"""
Pydantic models for HiveForge Agent Discovery Service.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SettlementRail(str, Enum):
    usdc = "usdc"
    usdcx = "usdcx"
    usad = "usad"
    aleo = "aleo"


class AgentStatus(str, Enum):
    active = "active"
    idle = "idle"
    busy = "busy"


# ---------------------------------------------------------------------------
# Core capability taxonomy (mirrors /v1/discovery/capabilities)
# ---------------------------------------------------------------------------

CAPABILITY_TAXONOMY: Dict[str, List[str]] = {
    "legal": [
        "dispute_filing",
        "contract_review",
        "compliance_audit",
        "arbitration",
    ],
    "financial": [
        "settlement",
        "escrow",
        "payroll",
        "tax_calculation",
        "invoice_processing",
    ],
    "identity": [
        "did_resolution",
        "credential_issuance",
        "trust_scoring",
        "kyc",
    ],
    "compute": [
        "code_execution",
        "data_analysis",
        "ml_inference",
        "batch_processing",
    ],
    "logistics": [
        "routing",
        "scheduling",
        "inventory_management",
        "procurement",
    ],
    "creative": [
        "content_generation",
        "translation",
        "summarization",
        "classification",
    ],
    "security": [
        "threat_detection",
        "audit_logging",
        "access_control",
        "attestation",
    ],
    "memory": [
        "knowledge_storage",
        "retrieval",
        "indexing",
        "vector_search",
    ],
}

# Flat set for fast validation
ALL_CAPABILITIES: set = {cap for caps in CAPABILITY_TAXONOMY.values() for cap in caps}


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------

class Pricing(BaseModel):
    """Per-call or per-unit pricing in USDC."""
    currency: str = Field(default="USDC", description="Always USDC for now.")
    per_call: Optional[float] = Field(None, ge=0, description="Flat fee per API call in USDC.")
    per_minute: Optional[float] = Field(None, ge=0, description="Hourly rate in USDC (for long-running jobs).")
    per_token: Optional[float] = Field(None, ge=0, description="Per-token price for LLM-backed agents.")
    minimum_charge: Optional[float] = Field(None, ge=0, description="Minimum charge per invocation.")
    notes: Optional[str] = Field(None, max_length=256)


# ---------------------------------------------------------------------------
# Agent profile
# ---------------------------------------------------------------------------

class AgentProfile(BaseModel):
    """Full agent profile stored in the registry."""
    did: str = Field(..., description="Decentralised identifier, e.g. did:hive:xxxx-xxxx")
    description: str = Field(..., max_length=1024)
    capabilities: List[str] = Field(..., min_length=1, max_length=20)
    settlement_rails: List[SettlementRail] = Field(..., min_length=1)
    pricing: Pricing
    endpoint_url: str = Field(..., description="Base URL the agent exposes for invocations.")
    status: AgentStatus = Field(default=AgentStatus.active)
    trust_score: Optional[int] = Field(
        None, ge=0, le=100, description="Cached trust score from HiveTrust (0-100)."
    )
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class RegistrationRequest(BaseModel):
    """Payload for POST /v1/discovery/agents/register."""
    did: str = Field(..., description="Agent DID.")
    capabilities: List[str] = Field(..., min_length=1, max_length=20)
    settlement_rails: List[SettlementRail] = Field(..., min_length=1)
    pricing: Pricing
    description: str = Field(..., max_length=1024)
    endpoint_url: str = Field(..., description="Reachable endpoint of the agent.")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RegistrationResponse(BaseModel):
    did: str
    message: str
    registered_at: datetime
    last_seen: datetime


class PingResponse(BaseModel):
    did: str
    last_seen: datetime
    status: AgentStatus


class DiscoveryQuery(BaseModel):
    """Internal representation of query params for GET /v1/discovery/agents."""
    capability: Optional[str] = None
    trust_min: Optional[int] = Field(None, ge=0, le=100)
    trust_max: Optional[int] = Field(None, ge=0, le=100)
    rail: Optional[SettlementRail] = None
    status: Optional[AgentStatus] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedAgents(BaseModel):
    total: int
    limit: int
    offset: int
    agents: List[AgentProfile]


class CapabilityTaxonomy(BaseModel):
    categories: Dict[str, List[str]]


class SearchResult(BaseModel):
    total: int
    query: str
    agents: List[AgentProfile]


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "hive-discovery"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
