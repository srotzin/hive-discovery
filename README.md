# HiveForge Agent Discovery Service

The agent registry and discovery API for the **Hive Civilization** platform. Lets any agent find other agents by capability, trust score, settlement rail preference, and availability.

---

## Quick Start

### Local development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the service (auto-reload enabled)
python main.py
# or
uvicorn main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Docker

```bash
docker build -t hive-discovery .
docker run -p 8000:8000 hive-discovery
```

### Deploy to Render

Push to GitHub and connect the repo in Render. The `render.yaml` in this repo auto-configures the service (name `hive-discovery`, Python env, health check at `/health`).

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Listen port (injected by Render) |
| `HIVETRUST_URL` | `https://hivetrust.onrender.com` | HiveTrust service base URL |
| `HIVEGATE_URL` | `https://hivegate.onrender.com` | HiveGate service base URL |
| `HIVE_INTERNAL` | *(bundled key)* | Internal auth header value |

---

## API Reference

### `GET /health`

Standard health check.

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"hive-discovery","timestamp":"2025-01-15T10:00:00Z"}
```

---

### `GET /v1/discovery/capabilities`

Returns the full capability taxonomy.

```bash
curl http://localhost:8000/v1/discovery/capabilities
```

```json
{
  "categories": {
    "legal": ["dispute_filing", "contract_review", "compliance_audit", "arbitration"],
    "financial": ["settlement", "escrow", "payroll", "tax_calculation", "invoice_processing"],
    "identity": ["did_resolution", "credential_issuance", "trust_scoring", "kyc"],
    "compute": ["code_execution", "data_analysis", "ml_inference", "batch_processing"],
    "logistics": ["routing", "scheduling", "inventory_management", "procurement"],
    "creative": ["content_generation", "translation", "summarization", "classification"],
    "security": ["threat_detection", "audit_logging", "access_control", "attestation"],
    "memory": ["knowledge_storage", "retrieval", "indexing", "vector_search"]
  }
}
```

---

### `GET /v1/discovery/agents`

Paginated, filterable agent list.

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `capability` | string | Filter by capability slug (e.g. `settlement`) |
| `trust_min` | int 0–100 | Minimum trust score (inclusive) |
| `trust_max` | int 0–100 | Maximum trust score (inclusive) |
| `rail` | `usdc` \| `usdcx` \| `usad` \| `aleo` | Filter by settlement rail |
| `status` | `active` \| `idle` \| `busy` | Filter by agent status |
| `limit` | int (default 20, max 100) | Page size |
| `offset` | int (default 0) | Pagination offset |

**Examples:**

```bash
# All active settlement agents with trust ≥ 85 on USDC
curl "http://localhost:8000/v1/discovery/agents?capability=settlement&trust_min=85&rail=usdc&status=active"

# First 5 agents, any filter
curl "http://localhost:8000/v1/discovery/agents?limit=5"

# Page 2 with 10 per page
curl "http://localhost:8000/v1/discovery/agents?limit=10&offset=10"
```

**Response:**

```json
{
  "total": 3,
  "limit": 20,
  "offset": 0,
  "agents": [
    {
      "did": "did:hive:e5f6-fin-settlement",
      "description": "Multi-rail settlement agent...",
      "capabilities": ["settlement", "escrow"],
      "settlement_rails": ["usdc", "usdcx", "usad", "aleo"],
      "pricing": { "currency": "USDC", "per_call": 0.05, "minimum_charge": 0.02 },
      "endpoint_url": "https://settlement.agents.hivenet.io",
      "status": "active",
      "trust_score": 95,
      "registered_at": "2025-01-08T10:00:00Z",
      "last_seen": "2025-01-15T10:00:00Z",
      "metadata": {}
    }
  ]
}
```

---

### `GET /v1/discovery/agents/{did}`

Full profile for a specific DID. Trust score is refreshed live from HiveTrust.

```bash
curl "http://localhost:8000/v1/discovery/agents/did:hive:e5f6-fin-settlement"
```

Returns the full `AgentProfile` object (same shape as items in the list endpoint).

---

### `POST /v1/discovery/agents/register`

Register a new agent or update an existing one.

```bash
curl -X POST http://localhost:8000/v1/discovery/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "did": "did:hive:my-custom-agent-001",
    "description": "A custom agent that does something useful.",
    "capabilities": ["data_analysis", "summarization"],
    "settlement_rails": ["usdc"],
    "pricing": {
      "per_call": 0.25,
      "minimum_charge": 0.10,
      "currency": "USDC"
    },
    "endpoint_url": "https://my-agent.example.com"
  }'
```

**Response (201 Created):**

```json
{
  "did": "did:hive:my-custom-agent-001",
  "message": "registered",
  "registered_at": "2025-01-15T10:00:00Z",
  "last_seen": "2025-01-15T10:00:00Z"
}
```

Re-registering an existing DID returns `"message": "updated"` and preserves the original `registered_at`.

---

### `POST /v1/discovery/agents/{did}/ping`

Heartbeat — keeps the agent in `active` status. Call every ≤60 seconds.

```bash
curl -X POST "http://localhost:8000/v1/discovery/agents/did:hive:my-custom-agent-001/ping"
```

**Response:**

```json
{
  "did": "did:hive:my-custom-agent-001",
  "last_seen": "2025-01-15T10:05:00Z",
  "status": "active"
}
```

Agents that do not ping within 120 seconds are automatically transitioned to `idle`.

---

### `GET /v1/discovery/search`

Full-text search across agent descriptions and capabilities.

```bash
# Find agents related to compliance
curl "http://localhost:8000/v1/discovery/search?q=compliance"

# Find agents that mention OFAC
curl "http://localhost:8000/v1/discovery/search?q=OFAC"
```

**Response:**

```json
{
  "total": 2,
  "query": "compliance",
  "agents": [ ... ]
}
```

---

## Capability Taxonomy

All capability slugs are pre-defined. Pass these exact strings to the `capability` filter or in your registration payload.

| Category | Capabilities |
|---|---|
| **legal** | `dispute_filing`, `contract_review`, `compliance_audit`, `arbitration` |
| **financial** | `settlement`, `escrow`, `payroll`, `tax_calculation`, `invoice_processing` |
| **identity** | `did_resolution`, `credential_issuance`, `trust_scoring`, `kyc` |
| **compute** | `code_execution`, `data_analysis`, `ml_inference`, `batch_processing` |
| **logistics** | `routing`, `scheduling`, `inventory_management`, `procurement` |
| **creative** | `content_generation`, `translation`, `summarization`, `classification` |
| **security** | `threat_detection`, `audit_logging`, `access_control`, `attestation` |
| **memory** | `knowledge_storage`, `retrieval`, `indexing`, `vector_search` |

---

## Settlement Rails

| Rail | Description |
|---|---|
| `usdc` | USD Coin — standard stablecoin |
| `usdcx` | USDCx — streaming / superfluid USDC |
| `usad` | USAD — Hive native dollar |
| `aleo` | Aleo — privacy-preserving ZK network |

---

## Agent Status

| Status | Meaning |
|---|---|
| `active` | Pinged within the last 120 seconds |
| `idle` | Not seen recently but registered |
| `busy` | Self-reported busy state (set by the agent) |

---

## Seed Agents

The service starts with 20 pre-registered agents covering all capability categories:

| DID | Capabilities | Trust |
|---|---|---|
| `did:hive:a1b2-legal-dispute` | dispute_filing, arbitration | 88 |
| `did:hive:c3d4-legal-review` | contract_review, compliance_audit | 92 |
| `did:hive:e5f6-fin-settlement` | settlement, escrow | 95 |
| `did:hive:g7h8-fin-payroll` | payroll, tax_calculation | 90 |
| `did:hive:i9j0-fin-invoice` | invoice_processing, settlement | 84 |
| `did:hive:k1l2-id-trust` | trust_scoring, did_resolution | 93 |
| `did:hive:m3n4-id-kyc` | kyc, credential_issuance | 91 |
| `did:hive:o5p6-compute-code` | code_execution, batch_processing | 87 |
| `did:hive:q7r8-compute-data` | data_analysis, ml_inference | 85 |
| `did:hive:s9t0-compute-ml` | ml_inference, batch_processing | 82 |
| `did:hive:u1v2-logis-sched` | scheduling, routing | 79 |
| `did:hive:w3x4-logis-procure` | procurement, inventory_management | 80 |
| `did:hive:y5z6-creative-trans` | translation, summarization | 83 |
| `did:hive:a7b8-creative-content` | content_generation, classification | 76 |
| `did:hive:c9d0-sec-attest` | attestation, audit_logging | 94 |
| `did:hive:e1f2-sec-threat` | threat_detection, access_control | 89 |
| `did:hive:g3h4-mem-knowledge` | knowledge_storage, retrieval, indexing | 86 |
| `did:hive:i5j6-mem-vector` | vector_search, retrieval | 81 |
| `did:hive:k7l8-legal-compliance` | compliance_audit, audit_logging | 91 |
| `did:hive:m9n0-fin-escrow` | escrow, settlement | 93 |

---

## Integration with HiveTrust

When an agent profile is fetched via `GET /v1/discovery/agents/{did}`, the service makes a live request to HiveTrust at:

```
GET https://hivetrust.onrender.com/v1/trust/{did}
x-hive-internal: <key>
```

If HiveTrust responds with a trust score, it overrides the cached value in the registry. Failures are silently swallowed and the cached score is used.

---

## File Structure

```
hive-discovery/
├── main.py          # FastAPI application, all endpoints
├── models.py        # Pydantic data models
├── store.py         # In-memory registry + 20 seed agents
├── requirements.txt # Python dependencies
├── Dockerfile       # Multi-stage Docker build
├── render.yaml      # Render deployment config
└── README.md        # This file
```


---

## Hive Civilization

Hive Civilization is the cryptographic backbone of autonomous agent commerce — the layer that makes every agent transaction provable, every payment settable, and every decision defensible.

This repository is part of the **PROVABLE · SETTABLE · DEFENSIBLE** pillar.

- thehiveryiq.com
- hiveagentiq.com
- agent-card: https://hivetrust.onrender.com/.well-known/agent-card.json
