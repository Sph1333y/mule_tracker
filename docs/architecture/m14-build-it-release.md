# Milestone 14 — BUILD IT Release / Hardening Architecture

## 1. Overview & Architectural Role

Milestone 14 (M14) is the **BUILD IT Release and Hardening Layer** of the MuleTrace AI project. It marks the completion of the local, cloud-agnostic implementation phase across Milestones 0 through 13.

The foundational principle of MuleTrace AI is:
```
BUSINESS LOGIC = CLOUD AGNOSTIC
INFRASTRUCTURE = REPLACEABLE THROUGH ADAPTERS
```

The BUILD IT phase focuses on delivering an end-to-end operational platform on local infrastructure before initiating any cloud deployment or managed service migration (SHIP IT).

---

## 2. Complete BUILD IT Intelligence Stack

MuleTrace AI processes suspicious transaction events through a strictly hierarchical, deterministic intelligence pipeline:

```
[Raw Transaction / Batch Ingestion]
                ↓
    [M1] Canonical Domain Mapping
    - TransactionEvent (immutable, validated Pydantic model)
    - Domain Value Objects (Currency, Channel, Entity IDs)
                ↓
    [M2] Domain Repository Interfaces
    - TransactionRepository, AlertRepository, GraphRepository
    - ModelService, InvestigationCopilot
                ↓
┌───────────────────────┬───────────────────────┬───────────────────────┐
│ [M5] Heuristic Rules  │ [M6] Temporal Engine  │ [M7] Graph Engine     │
│ 14 Modular Heuristics │ Velocity & Burst      │ Topological Centrality│
│ Rapid Pass-Through    │ In/Out Turnaround     │ Cycle / Ring Detection│
│ Structuring Patterns  │ Dormancy Bursts       │ Shared Infrastructure │
└───────────┬───────────┴───────────┬───────────┴───────────┬───────────┘
            │                       │                       │
            └───────────────┬───────┴───────────────────────┘
                            ↓
            ┌───────────────────────────────┐
            │ [M8] Tabular ML (XGBoost)     │
            │ 57-dim feature vector         │
            │ Supervised anomaly score      │
            ├───────────────────────────────┤
            │ [M9] Graph ML (GraphSAGE)     │
            │ Topological neighborhood      │
            │ Unsupervised node embeddings  │
            └───────────────┬───────────────┘
                            ↓
            [M10] Multi-Modal Risk Fusion
            - Source of truth for Risk
            - 5 Modalities: rules, temporal, graph, tabular_ml, graph_ml
            - Dynamic weight renormalization (renormalize_available)
            - Composite Risk Score [0.0 - 100.0] & Categorical Tier
                            ↓
            [M11] Deterministic Evidence Engine
            - Source of truth for Forensic Facts
            - EvidencePackage (immutable collection of EvidenceItems)
            - Deduplication, ranking, and verified entity linkages
                            ↓
            [M12] Deterministic Investigation Copilot
            - Source of truth for Executive Narrative
            - Zero external LLM / 100% deterministic template synthesis
            - Key Findings, Prioritized Actions, Audit Boundaries
                            ↓
            [M13] SOC Integration Layer
            - Canonical Case Repository (CAS-2025-0045 through 0049)
            - REST Endpoints: GET /intelligence, POST /enrich, GET /cases
            - Next.js Investigation Intelligence Dossier Panel
                            ↓
            [M14] BUILD IT Release & Hardening
            - Dual Verification: Automated Regression + Manual Testing
            - Failsafe Offline / Degraded Mode Safety Guarantees
            - Localhost runnability freeze
```

---

## 3. Core Hardening Principles

### 3.1 Unbroken Heritage from M1 through M13
All underlying algorithms, heuristics, feature builders, adapters, and schemas implemented in M1 through M13 remain 100% frozen. M14 introduces zero modifications to scoring, zero alterations to heuristics, and zero restructuring of domain interfaces.

### 3.2 Offline Runnability & Graceful Degradation
The application operates fully offline without requiring cloud connectivity:
- If external databases (e.g. Neo4j Aura or Supabase PostgreSQL) are unavailable, the system safely falls back to local in-memory NetworkX graphs and deterministic state.
- In offline mode, the frontend clearly displays amber `DEGRADED MODE` badges and explicit notices so simulated benchmark data is never misrepresented as live intelligence.

### 3.3 Strict Zero Generative AI Boundary
MuleTrace AI rejects non-deterministic generative models for compliance reasons. The Investigation Copilot operates with 100% auditable Python templates. No external LLM keys or network access are required.

### 3.4 Strict Localhost Deployment Boundary (BUILD IT vs. SHIP IT)
M14 explicitly defines the end of the BUILD IT phase:
- **BUILD IT (Complete in M14)**: FastAPI, Uvicorn, Next.js, NetworkX, scikit-learn, XGBoost, local storage.
- **SHIP IT (Deferred to later milestones)**: AWS Lambda, API Gateway, Amazon RDS, Amazon Neptune, Neptune Analytics, Amazon S3, AWS Amplify, AWS CDK.
