"""
HiveForge Agent Discovery Service
==================================
FastAPI application exposing the agent registry and discovery API.

Environment variables:
  HIVETRUST_URL   — HiveTrust base URL  (default: https://hivetrust.onrender.com)
  HIVEGATE_URL    — HiveGate base URL   (default: https://hivegate.onrender.com)
  HIVE_INTERNAL   — Internal key value  (optional override)
  PORT            — Listen port         (default: 8000)
"""

from __future__ import annotations

import asyncio
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import store
from models import (
    CAPABILITY_TAXONOMY,
    AgentProfile,
    AgentStatus,
    CapabilityTaxonomy,
    DiscoveryQuery,
    HealthResponse,
    PaginatedAgents,
    PingResponse,
    RegistrationRequest,
    RegistrationResponse,
    SearchResult,
    SettlementRail,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HIVETRUST_URL: str = os.getenv("HIVETRUST_URL", "https://hivetrust.onrender.com")
HIVEGATE_URL: str = os.getenv("HIVEGATE_URL", "https://hivegate.onrender.com")
HIVE_INTERNAL_KEY: str = os.getenv(
    "HIVE_INTERNAL",
    "hive_internal_125e04e071e8829be631ea0216dd4a0c9b707975fcecaf8c62c6a2ab43327d46",
)

INTERNAL_HEADERS = {"x-hive-internal": HIVE_INTERNAL_KEY}


# ---------------------------------------------------------------------------
# x402 payment gate
# ---------------------------------------------------------------------------

def x402_gate(price_usd: float, description: str):
    """Returns a FastAPI dependency that enforces x402 payment or internal key bypass."""
    async def dependency(
        request: Request,
        x_payment: str = Header(None),
        x_hive_internal: str = Header(None),
        x_api_key: str = Header(None)
    ):
        # Internal bypass
        if x_hive_internal == HIVE_INTERNAL_KEY or x_api_key == HIVE_INTERNAL_KEY:
            return {"bypassed": True, "amount": 0}
        # Payment present — accept (in production, verify cryptographically)
        if x_payment:
            return {"verified": True, "amount": price_usd}
        # No payment — return 402
        raise HTTPException(
            status_code=402,
            detail={
                "error": "payment_required",
                "x402": {
                    "version": "1.0",
                    "amount_usdc": price_usd,
                    "description": description,
                    "payment_methods": ["x402-usdc", "x402-aleo"],
                    "headers_required": ["X-Payment"],
                    "settlement_wallet": "0x78B3B3C356E89b5a69C488c6032509Ef4260B6bf",
                    "network": "base"
                }
            }
        )
    return dependency

# Agents not seen within this window are marked idle
ACTIVE_WINDOW_SECONDS = 120

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hive-discovery")


# ---------------------------------------------------------------------------
# Background task: expire stale agents
# ---------------------------------------------------------------------------

async def _stale_agent_sweeper() -> None:
    """Mark agents as idle if they haven't pinged recently."""
    while True:
        await asyncio.sleep(30)
        cutoff = datetime.utcnow() - timedelta(seconds=ACTIVE_WINDOW_SECONDS)
        for agent in store.get_all():
            if agent.status == AgentStatus.active and agent.last_seen < cutoff:
                agent.status = AgentStatus.idle
                logger.info("Agent %s marked idle (last seen %s)", agent.did, agent.last_seen)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_stale_agent_sweeper())
    logger.info("HiveForge Discovery Service started. Registry size: %d agents", store.count())
    yield
    task.cancel()
    logger.info("HiveForge Discovery Service shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="HiveForge Agent Discovery",
    description=(
        "Registry and discovery API for the Hive Civilization agent network. "
        "Find agents by capability, trust score, settlement rail, and availability."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_status(agent: AgentProfile) -> AgentStatus:
    """Derive live status based on last_seen timestamp."""
    cutoff = datetime.utcnow() - timedelta(seconds=ACTIVE_WINDOW_SECONDS)
    if agent.last_seen < cutoff and agent.status == AgentStatus.active:
        return AgentStatus.idle
    return agent.status


async def _fetch_trust_score(did: str) -> Optional[int]:
    """Attempt to fetch the latest trust score from HiveTrust."""
    url = f"{HIVETRUST_URL}/v1/trust/{did}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=INTERNAL_HEADERS)
            if resp.status_code == 200:
                data = resp.json()
                score = data.get("trust_score") or data.get("score")
                if isinstance(score, (int, float)):
                    return int(score)
    except Exception as exc:
        logger.debug("HiveTrust fetch failed for %s: %s", did, exc)
    return None


def _filter_agents(query: DiscoveryQuery) -> List[AgentProfile]:
    agents = store.get_all()

    if query.capability:
        agents = [a for a in agents if query.capability in a.capabilities]

    if query.rail:
        agents = [a for a in agents if query.rail in a.settlement_rails]

    if query.status:
        agents = [a for a in agents if _compute_status(a) == query.status]

    if query.trust_min is not None:
        agents = [a for a in agents if a.trust_score is not None and a.trust_score >= query.trust_min]

    if query.trust_max is not None:
        agents = [a for a in agents if a.trust_score is not None and a.trust_score <= query.trust_max]

    # Sort: active first, then by trust score descending
    agents.sort(key=lambda a: (a.status != AgentStatus.active, -(a.trust_score or 0)))

    return agents


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["Meta"])
async def health_check():
    """Service health check."""
    return HealthResponse()


@app.get(
    "/v1/discovery/capabilities",
    response_model=CapabilityTaxonomy,
    tags=["Discovery"],
    summary="Get capability taxonomy",
)
async def get_capabilities():
    """Return the full taxonomy of agent capabilities."""
    return CapabilityTaxonomy(categories=CAPABILITY_TAXONOMY)


@app.get(
    "/v1/discovery/agents",
    response_model=PaginatedAgents,
    tags=["Discovery"],
    summary="List and filter agents",
)
async def list_agents(
    capability: Optional[str] = Query(None, description="Filter by a single capability slug."),
    trust_min: Optional[int] = Query(None, ge=0, le=100, description="Minimum trust score."),
    trust_max: Optional[int] = Query(None, ge=0, le=100, description="Maximum trust score."),
    rail: Optional[SettlementRail] = Query(None, description="Filter by settlement rail."),
    status: Optional[AgentStatus] = Query(None, description="Filter by agent status."),
    limit: int = Query(20, ge=1, le=100, description="Page size."),
    offset: int = Query(0, ge=0, description="Pagination offset."),
    _payment=Depends(x402_gate(0.01, "Agent discovery search — $0.01 per query")),
):
    """
    Return a paginated, filtered list of registered agents.

    All filters are optional and combinable. Results are sorted active-first,
    then by trust score descending.
    """
    query = DiscoveryQuery(
        capability=capability,
        trust_min=trust_min,
        trust_max=trust_max,
        rail=rail,
        status=status,
        limit=limit,
        offset=offset,
    )
    filtered = _filter_agents(query)
    total = len(filtered)
    page = filtered[offset: offset + limit]

    # Ensure computed status is reflected
    for agent in page:
        agent.status = _compute_status(agent)

    return PaginatedAgents(total=total, limit=limit, offset=offset, agents=page)


@app.get(
    "/v1/discovery/agents/{did:path}",
    response_model=AgentProfile,
    tags=["Discovery"],
    summary="Get agent profile by DID",
)
async def get_agent(
    did: str = Path(..., description="Agent DID (e.g. did:hive:xxxx-xxxx)"),
    _payment=Depends(x402_gate(0.01, "Agent discovery search — $0.01 per query")),
):
    """
    Return the full profile for a specific agent DID.

    Trust score is refreshed live from HiveTrust if available;
    falls back to the cached value in the registry.
    """
    agent = store.get_by_did(did)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{did}' not found in registry.")

    # Refresh trust score from HiveTrust
    live_score = await _fetch_trust_score(did)
    if live_score is not None:
        agent.trust_score = live_score

    agent.status = _compute_status(agent)
    return agent


@app.post(
    "/v1/discovery/agents/register",
    response_model=RegistrationResponse,
    status_code=201,
    tags=["Registry"],
    summary="Register or update an agent",
)
async def register_agent(body: RegistrationRequest):
    """
    Register a new agent or update an existing one.

    The `did` field is the primary key. Re-registering with an existing DID
    updates the profile in-place and resets `last_seen` to now.
    """
    existing = store.get_by_did(body.did)
    now = datetime.utcnow()

    profile = AgentProfile(
        did=body.did,
        description=body.description,
        capabilities=body.capabilities,
        settlement_rails=body.settlement_rails,
        pricing=body.pricing,
        endpoint_url=body.endpoint_url,
        metadata=body.metadata,
        status=AgentStatus.active,
        registered_at=existing.registered_at if existing else now,
        last_seen=now,
        trust_score=existing.trust_score if existing else None,
    )

    # Fire-and-forget trust score fetch
    live_score = await _fetch_trust_score(body.did)
    if live_score is not None:
        profile.trust_score = live_score

    store.upsert(profile)
    logger.info("Agent %s %s.", body.did, "updated" if existing else "registered")

    return RegistrationResponse(
        did=profile.did,
        message="updated" if existing else "registered",
        registered_at=profile.registered_at,
        last_seen=profile.last_seen,
    )


@app.post(
    "/v1/discovery/agents/{did:path}/ping",
    response_model=PingResponse,
    tags=["Registry"],
    summary="Heartbeat ping — keeps agent active",
)
async def ping_agent(
    did: str = Path(..., description="Agent DID to ping."),
):
    """
    Update the agent's `last_seen` timestamp.

    Agents should call this every ≤60 seconds to remain in `active` status.
    A 404 is returned if the DID is not registered.
    """
    agent = store.ping(did)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{did}' not found. Register before pinging.",
        )
    return PingResponse(did=agent.did, last_seen=agent.last_seen, status=agent.status)


@app.get(
    "/v1/discovery/search",
    response_model=SearchResult,
    tags=["Discovery"],
    summary="Full-text search across agents",
)
async def search_agents(
    q: str = Query(..., min_length=2, description="Search query string."),
    _payment=Depends(x402_gate(0.01, "Agent discovery search — $0.01 per query")),
):
    """
    Full-text search across agent descriptions and capabilities.

    Case-insensitive substring match. Results ordered by trust score descending.
    """
    q_lower = q.lower()
    results = []
    for agent in store.get_all():
        hit = (
            q_lower in agent.description.lower()
            or any(q_lower in cap.lower() for cap in agent.capabilities)
            or q_lower in agent.did.lower()
        )
        if hit:
            agent.status = _compute_status(agent)
            results.append(agent)

    results.sort(key=lambda a: -(a.trust_score or 0))
    return SearchResult(total=len(results), query=q, agents=results)


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# ---------------------------------------------------------------------------
# Entry point (for local development)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
