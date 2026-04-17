"""
In-memory agent registry for HiveForge Discovery Service.
Populated with 20 diverse seed agents at startup.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from models import AgentProfile, AgentStatus, Pricing, SettlementRail


# ---------------------------------------------------------------------------
# Registry singleton
# ---------------------------------------------------------------------------

_registry: Dict[str, AgentProfile] = {}


def _make_did(suffix: str) -> str:
    return f"did:hive:{suffix}"


def _ts(minutes_ago: int = 0) -> datetime:
    return datetime.utcnow() - timedelta(minutes=minutes_ago)


# ---------------------------------------------------------------------------
# Seed data — 20 agents
# ---------------------------------------------------------------------------

_SEED_AGENTS: list[dict] = [
    # ---- Legal ----
    {
        "did": _make_did("a1b2-legal-dispute"),
        "description": (
            "Specialist dispute-filing agent. Prepares and submits on-chain dispute records "
            "referencing smart-contract evidence, generates structured claim packets for "
            "Hive arbitration panels, and tracks resolution status."
        ),
        "capabilities": ["dispute_filing", "arbitration"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usad],
        "pricing": Pricing(per_call=0.85, minimum_charge=0.50, notes="Complex disputes billed per hour"),
        "endpoint_url": "https://legal-dispute.agents.hivenet.io",
        "trust_score": 88,
        "status": AgentStatus.active,
        "registered_at": _ts(4320),
        "last_seen": _ts(1),
    },
    {
        "did": _make_did("c3d4-legal-review"),
        "description": (
            "Contract review agent powered by a fine-tuned legal LLM. Accepts contract text "
            "or PDF URL, returns structured analysis: risk clauses, missing provisions, "
            "jurisdiction flags, and recommended edits."
        ),
        "capabilities": ["contract_review", "compliance_audit"],
        "settlement_rails": [SettlementRail.usdc],
        "pricing": Pricing(per_call=1.20, per_token=0.000012, notes="Minimum 1000 tokens"),
        "endpoint_url": "https://contract-review.agents.hivenet.io",
        "trust_score": 92,
        "status": AgentStatus.active,
        "registered_at": _ts(8640),
        "last_seen": _ts(2),
    },
    # ---- Financial ----
    {
        "did": _make_did("e5f6-fin-settlement"),
        "description": (
            "Multi-rail settlement agent. Routes payments across USDC, USDCx, USAD, and Aleo "
            "networks. Handles automatic retries, fee optimisation, and on-chain settlement "
            "receipts. Supports batch disbursements up to 500 transactions."
        ),
        "capabilities": ["settlement", "escrow"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usdcx, SettlementRail.usad, SettlementRail.aleo],
        "pricing": Pricing(per_call=0.05, minimum_charge=0.02, notes="0.1% of transaction value, min $0.05"),
        "endpoint_url": "https://settlement.agents.hivenet.io",
        "trust_score": 95,
        "status": AgentStatus.active,
        "registered_at": _ts(10080),
        "last_seen": _ts(0),
    },
    {
        "did": _make_did("g7h8-fin-payroll"),
        "description": (
            "Automated payroll agent for DAOs and protocol teams. Reads contributor wallets "
            "from on-chain registries, calculates net pay after token vesting, executes "
            "recurring disbursements, and generates payroll attestations."
        ),
        "capabilities": ["payroll", "tax_calculation"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usdcx],
        "pricing": Pricing(per_call=0.30, minimum_charge=0.15),
        "endpoint_url": "https://payroll.agents.hivenet.io",
        "trust_score": 90,
        "status": AgentStatus.active,
        "registered_at": _ts(2880),
        "last_seen": _ts(3),
    },
    {
        "did": _make_did("i9j0-fin-invoice"),
        "description": (
            "Invoice processing agent. Parses PDF, CSV, and JSON invoices, validates line "
            "items against purchase orders, detects duplicate submissions, and triggers "
            "payment via any configured settlement rail."
        ),
        "capabilities": ["invoice_processing", "settlement"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usad],
        "pricing": Pricing(per_call=0.18, minimum_charge=0.10),
        "endpoint_url": "https://invoice.agents.hivenet.io",
        "trust_score": 84,
        "status": AgentStatus.active,
        "registered_at": _ts(5760),
        "last_seen": _ts(5),
    },
    # ---- Identity ----
    {
        "did": _make_did("k1l2-id-trust"),
        "description": (
            "Trust scoring agent backed by the HiveTrust oracle. Accepts a DID, aggregates "
            "on-chain history, credential depth, stake, and dispute record to produce a "
            "0-100 composite trust score with a confidence band."
        ),
        "capabilities": ["trust_scoring", "did_resolution"],
        "settlement_rails": [SettlementRail.usdc],
        "pricing": Pricing(per_call=0.10, minimum_charge=0.05),
        "endpoint_url": "https://trust-score.agents.hivenet.io",
        "trust_score": 93,
        "status": AgentStatus.active,
        "registered_at": _ts(14400),
        "last_seen": _ts(1),
    },
    {
        "did": _make_did("m3n4-id-kyc"),
        "description": (
            "KYC and credential issuance agent. Integrates with off-chain identity providers, "
            "performs liveness checks, and mints verifiable credentials on the Hive credential "
            "chain. GDPR-compliant data handling."
        ),
        "capabilities": ["kyc", "credential_issuance"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usad],
        "pricing": Pricing(per_call=2.50, minimum_charge=1.00, notes="Includes 3rd-party verification fee"),
        "endpoint_url": "https://kyc.agents.hivenet.io",
        "trust_score": 91,
        "status": AgentStatus.active,
        "registered_at": _ts(7200),
        "last_seen": _ts(4),
    },
    # ---- Compute ----
    {
        "did": _make_did("o5p6-compute-code"),
        "description": (
            "Sandboxed code execution agent. Runs Python, JavaScript, and Rust snippets in "
            "isolated WASM containers. Returns stdout, stderr, exit code, and resource usage. "
            "Supports up to 60-second execution windows."
        ),
        "capabilities": ["code_execution", "batch_processing"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.aleo],
        "pricing": Pricing(per_minute=0.06, minimum_charge=0.01),
        "endpoint_url": "https://code-exec.agents.hivenet.io",
        "trust_score": 87,
        "status": AgentStatus.active,
        "registered_at": _ts(3600),
        "last_seen": _ts(2),
    },
    {
        "did": _make_did("q7r8-compute-data"),
        "description": (
            "Data analysis agent. Accepts CSV, Parquet, or JSON datasets and a natural-language "
            "query. Returns computed statistics, charts (as base64 PNG), and a narrative "
            "summary. Powered by a fine-tuned code-generation model."
        ),
        "capabilities": ["data_analysis", "ml_inference"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usdcx],
        "pricing": Pricing(per_call=0.40, per_token=0.000008),
        "endpoint_url": "https://data-analysis.agents.hivenet.io",
        "trust_score": 85,
        "status": AgentStatus.active,
        "registered_at": _ts(1440),
        "last_seen": _ts(6),
    },
    {
        "did": _make_did("s9t0-compute-ml"),
        "description": (
            "General ML inference agent. Hosts fine-tuned models for classification, embedding, "
            "and regression. Accepts structured JSON payloads, returns predictions with "
            "probability scores. Supports async batch jobs."
        ),
        "capabilities": ["ml_inference", "batch_processing"],
        "settlement_rails": [SettlementRail.usdc],
        "pricing": Pricing(per_call=0.12, per_token=0.000005, notes="Batch jobs 30% discount"),
        "endpoint_url": "https://ml-inference.agents.hivenet.io",
        "trust_score": 82,
        "status": AgentStatus.active,
        "registered_at": _ts(2160),
        "last_seen": _ts(8),
    },
    # ---- Logistics ----
    {
        "did": _make_did("u1v2-logis-sched"),
        "description": (
            "Intelligent scheduling agent for multi-agent workflows. Accepts job graphs with "
            "dependencies, resource constraints, and deadlines. Outputs an optimal execution "
            "plan and monitors live progress via webhook callbacks."
        ),
        "capabilities": ["scheduling", "routing"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usad],
        "pricing": Pricing(per_call=0.22, minimum_charge=0.10),
        "endpoint_url": "https://scheduler.agents.hivenet.io",
        "trust_score": 79,
        "status": AgentStatus.active,
        "registered_at": _ts(720),
        "last_seen": _ts(10),
    },
    {
        "did": _make_did("w3x4-logis-procure"),
        "description": (
            "Procurement agent for on-chain and off-chain supply chains. Discovers vendors, "
            "negotiates quote requests, validates delivery attestations, and triggers escrow "
            "release upon confirmed fulfilment."
        ),
        "capabilities": ["procurement", "inventory_management"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usdcx],
        "pricing": Pricing(per_call=0.65, minimum_charge=0.30, notes="1% of PO value over $500"),
        "endpoint_url": "https://procurement.agents.hivenet.io",
        "trust_score": 80,
        "status": AgentStatus.active,
        "registered_at": _ts(4320),
        "last_seen": _ts(12),
    },
    # ---- Creative ----
    {
        "did": _make_did("y5z6-creative-trans"),
        "description": (
            "Professional translation agent supporting 40 language pairs. Preserves tone, "
            "formatting, and legal/technical terminology. Delivers translated documents with "
            "a confidence score and optional human-review flag."
        ),
        "capabilities": ["translation", "summarization"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usad],
        "pricing": Pricing(per_token=0.000020, minimum_charge=0.05),
        "endpoint_url": "https://translation.agents.hivenet.io",
        "trust_score": 83,
        "status": AgentStatus.active,
        "registered_at": _ts(5040),
        "last_seen": _ts(7),
    },
    {
        "did": _make_did("a7b8-creative-content"),
        "description": (
            "Content generation agent for technical documentation, marketing copy, and "
            "regulatory summaries. Accepts brand voice profiles. Outputs Markdown, HTML, "
            "or plain text. Integrates with Hive memory agents for context retrieval."
        ),
        "capabilities": ["content_generation", "classification"],
        "settlement_rails": [SettlementRail.usdc],
        "pricing": Pricing(per_token=0.000018, minimum_charge=0.08),
        "endpoint_url": "https://content-gen.agents.hivenet.io",
        "trust_score": 76,
        "status": AgentStatus.idle,
        "registered_at": _ts(8640),
        "last_seen": _ts(25),
    },
    # ---- Security ----
    {
        "did": _make_did("c9d0-sec-attest"),
        "description": (
            "Security attestation agent. Generates cryptographic attestations for agent "
            "outputs, smart-contract states, and data provenance. Attestations are anchored "
            "on-chain and verifiable by any Hive participant."
        ),
        "capabilities": ["attestation", "audit_logging"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.aleo],
        "pricing": Pricing(per_call=0.08, minimum_charge=0.04),
        "endpoint_url": "https://attestation.agents.hivenet.io",
        "trust_score": 94,
        "status": AgentStatus.active,
        "registered_at": _ts(11520),
        "last_seen": _ts(1),
    },
    {
        "did": _make_did("e1f2-sec-threat"),
        "description": (
            "Real-time threat detection agent. Monitors on-chain activity streams for "
            "anomalous patterns: rug-pull signals, abnormal fund flows, replay attacks, "
            "and Sybil behaviour. Emits structured alerts via webhook or on-chain event."
        ),
        "capabilities": ["threat_detection", "access_control"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usad],
        "pricing": Pricing(per_minute=0.15, minimum_charge=0.50, notes="Flat monthly plans available"),
        "endpoint_url": "https://threat-detection.agents.hivenet.io",
        "trust_score": 89,
        "status": AgentStatus.active,
        "registered_at": _ts(2880),
        "last_seen": _ts(3),
    },
    # ---- Memory ----
    {
        "did": _make_did("g3h4-mem-knowledge"),
        "description": (
            "Knowledge retrieval agent with hybrid dense-sparse search. Indexes documents, "
            "on-chain data, and structured tables. Returns cited passages ranked by relevance. "
            "Supports incremental indexing and access-controlled namespaces."
        ),
        "capabilities": ["knowledge_storage", "retrieval", "indexing"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usdcx],
        "pricing": Pricing(per_call=0.06, per_token=0.000004, notes="Storage $0.002 per MB/month"),
        "endpoint_url": "https://knowledge.agents.hivenet.io",
        "trust_score": 86,
        "status": AgentStatus.active,
        "registered_at": _ts(6480),
        "last_seen": _ts(5),
    },
    {
        "did": _make_did("i5j6-mem-vector"),
        "description": (
            "Vector search agent providing high-throughput ANN (approximate nearest neighbour) "
            "lookups over agent-managed embedding stores. Supports cosine and dot-product "
            "similarity. HNSW index with sub-10ms p99 latency."
        ),
        "capabilities": ["vector_search", "retrieval"],
        "settlement_rails": [SettlementRail.usdc],
        "pricing": Pricing(per_call=0.03, minimum_charge=0.01, notes="Index build billed separately"),
        "endpoint_url": "https://vector-search.agents.hivenet.io",
        "trust_score": 81,
        "status": AgentStatus.active,
        "registered_at": _ts(1800),
        "last_seen": _ts(9),
    },
    # ---- Compliance ----
    {
        "did": _make_did("k7l8-legal-compliance"),
        "description": (
            "Compliance audit agent for DeFi protocols and DAO treasuries. Cross-references "
            "transactions against OFAC/SDN lists, MiCA requirements, and configurable "
            "internal policy rules. Produces audit reports in PDF and machine-readable JSON."
        ),
        "capabilities": ["compliance_audit", "audit_logging"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usad],
        "pricing": Pricing(per_call=1.50, minimum_charge=0.75, notes="Full treasury audit: flat $50"),
        "endpoint_url": "https://compliance.agents.hivenet.io",
        "trust_score": 91,
        "status": AgentStatus.active,
        "registered_at": _ts(3240),
        "last_seen": _ts(6),
    },
    # ---- Escrow / financial hybrid ----
    {
        "did": _make_did("m9n0-fin-escrow"),
        "description": (
            "Programmable escrow agent. Locks funds in a smart-contract vault, monitors "
            "fulfilment conditions (off-chain attestations or on-chain events), and releases "
            "or refunds automatically. Supports multi-party and time-locked escrows."
        ),
        "capabilities": ["escrow", "settlement"],
        "settlement_rails": [SettlementRail.usdc, SettlementRail.usdcx, SettlementRail.aleo],
        "pricing": Pricing(per_call=0.20, minimum_charge=0.10, notes="0.05% of locked value"),
        "endpoint_url": "https://escrow.agents.hivenet.io",
        "trust_score": 93,
        "status": AgentStatus.active,
        "registered_at": _ts(9360),
        "last_seen": _ts(2),
    },
]


# ---------------------------------------------------------------------------
# Registry bootstrap
# ---------------------------------------------------------------------------

def _bootstrap() -> None:
    for agent_data in _SEED_AGENTS:
        profile = AgentProfile(**agent_data)
        _registry[profile.did] = profile


_bootstrap()


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def get_all() -> list[AgentProfile]:
    return list(_registry.values())


def get_by_did(did: str) -> Optional[AgentProfile]:
    return _registry.get(did)


def upsert(profile: AgentProfile) -> AgentProfile:
    _registry[profile.did] = profile
    return profile


def ping(did: str) -> Optional[AgentProfile]:
    profile = _registry.get(did)
    if profile is None:
        return None
    profile.last_seen = datetime.utcnow()
    profile.status = AgentStatus.active
    return profile


def count() -> int:
    return len(_registry)
