# Milestone 13 — SOC Integration Architecture

## 1. Overview & Architectural Role

Milestone 13 (M13) is the **SOC Integration Layer** of MuleTrace AI. Its purpose is to safely and seamlessly expose the end-to-end multi-modal intelligence pipeline (M1 through M12) to the Security Operations Center (SOC) investigation workflow across both the backend REST APIs and the Next.js investigator dashboard.

Prior to M13, each intelligence milestone operated as an independently validated, deterministic engine:
- **M1**: Canonical TransactionEvent domain contract
- **M2**: Domain interfaces & abstraction boundaries
- **M3/M4**: Graph repository adapters (NetworkX & Neo4j)
- **M5**: 14-rule modular heuristic detection engine
- **M6**: Temporal velocity & rapid pass-through detection
- **M7**: Graph topological centrality & community detection
- **M8**: Deterministic tabular ML (XGBoost / Random Forest)
- **M9**: Graph ML / GNN embeddings (GraphSAGE)
- **M10**: Multi-modal Risk Fusion engine (Source of Truth for composite risk)
- **M11**: Deterministic Evidence Engine (Source of Truth for auditable facts)
- **M12**: Deterministic Investigation Copilot (Source of Truth for investigative narrative)

**M13 bridges these intelligence capabilities directly into the investigator's hands without altering any detection logic, recalculating any risk scores, or breaking existing application flows.**

---

## 2. End-to-End Pipeline Data Flow

The full pipeline executes deterministically from raw transaction event to investigator UI:

```
Transaction Ingestion
       ↓
[M1] Canonical TransactionEvent
       ↓
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ [M5] Modular Rules   │ [M6] Temporal Engine │ [M7] Graph Engine    │
│ Heuristic Violations │ Velocity & Timing    │ Topology & Rings     │
└──────────┬───────────┴──────────┬───────────┴──────────┬───────────┘
           │                      │                      │
           └──────────────┬───────┴──────────────────────┘
                          ↓
           ┌──────────────────────────────┐
           │ [M8] Tabular ML (XGBoost)    │
           │ [M9] Graph ML (GraphSAGE)    │
           └──────────────┬───────────────┘
                          ↓
           [M10] Multi-Modal Risk Fusion
           - Weighted combination (5 modalities)
           - Dynamic renormalization
           - Composite Risk Score & Level
                          ↓
           [M11] Deterministic Evidence Engine
           - Immutable, self-contained EvidencePackage
           - Verified evidence IDs & entity links
                          ↓
           [M12] Deterministic Investigation Copilot
           - Template-governed executive narrative
           - Key forensic findings & recommended actions
           - Audit boundaries & follow-up questions
                          ↓
       [M13] SOC Integration Service & API
       - Canonical Case Index & Detail API
       - On-the-fly intelligence enrichment API
                          ↓
       [M13] Next.js Investigator Dashboard
       - Risk Gauge & Tier Badges
       - 5-Modality Contribution Breakdown
       - Copilot Narrative & Recommended Actions
       - Auditable Evidence Dossier Table
```

---

## 3. Core Architectural Principles

### 3.1 Unalterable Upstream Sources of Truth
- **M10 is the sole authority on Risk**: M13 strictly passes through `composite_risk_score`, `risk_level`, and `risk_contributions`. No score adjustments, threshold overrides, or weights are applied in M13.
- **M11 is the sole authority on Evidence**: Every evidence item in M13 is mapped directly from an upstream `EvidenceItem`. No evidence IDs are invented or altered.
- **M12 is the sole authority on Copilot Synthesis**: All narratives, key findings, suggested next steps, and follow-up questions originate from M12 deterministic templates.

### 3.2 Strictly Zero LLM
No external LLMs (OpenAI, Gemini, Bedrock, Anthropic) or local LLMs (Ollama, Mistral) are invoked anywhere in M13. 100% of intelligence outputs are deterministic, reproducible, auditable, and offline-capable.

### 3.3 Strict Failure Isolation & Graceful Degradation
Subsystem exceptions (such as temporary Neo4j disconnects or missing history) do not propagate into 500 internal server errors. The `SOCIntegrationService` catches errors, tags the response with `is_degraded=True`, and returns a safe fallback package so the investigator can continue their review.

### 3.4 Zero AWS Cloud Migration (BUILD IT vs. SHIP IT)
M13 runs completely on local infrastructure (FastAPI, Next.js, in-memory NetworkX/scikit-learn/XGBoost). Cloud infrastructure (AWS Lambda, Amplify, Neptune Analytics, S3) remains reserved for later deployment milestones.

---

## 4. Backend Implementation Architecture

### 4.1 Schemas (`app/schemas/investigation.py`)
- `ModalityContributionRead`: Represents individual signal contributions from the 5 modalities (`rules`, `temporal`, `graph`, `tabular_ml`, `graph_ml`).
- `EvidenceItemRead`: Serialized, immutable forensic evidence records with entity references and category metadata.
- `KeyFindingRead`: Structured findings linking back to verified `evidence_ids`.
- `SuggestedActionRead`: Actionable investigation steps with priority (`IMMEDIATE`, `HIGH`, `MEDIUM`, `LOW`) and action types (`RESTRICT_ACCOUNT`, `FILE_SAR`, etc.).
- `InvestigationIntelligenceData`: Comprehensive unified intelligence package combining M10, M11, and M12 outputs.
- `CaseDetailRead`: Case overview metadata including case status, priority, and assigned investigator.
- `InvestigationEnrichRequest`: Request body for on-the-fly intelligence synthesis on custom transaction payloads.

### 4.2 Service Layer (`app/services/soc_integration_service.py`)
The `SOCIntegrationService` coordinates:
1. **Canonical Case Retrieval**: Pre-indexes realistic canonical investigation cases (`CAS-2025-0045` through `CAS-2025-0049`) representing distinct mule typology benchmarks (rapid pass-through, fan-in collector, cross-channel layering, shared hardware cluster, dormant account reactivation).
2. **Orchestrated Evaluation**: For any case or ad-hoc payload, constructs canonical `TransactionEvent` streams, evaluates M5 rules, M6 temporal features, M7 graph topology, M8 tabular ML, M9 graph ML, executes M10 risk fusion, gathers M11 evidence, and invokes M12 copilot synthesis.
3. **Failsafe Degradation**: Ensures that if any feature extraction encounters an issue, the pipeline falls back gracefully.

### 4.3 API Routes (`app/api/v1/investigations.py`)
- `GET /api/v1/investigations`: Lists active cases (unmodified backward-compatible contract).
- `POST /api/v1/investigations/copilot`: Standalone copilot synthesis on custom evidence packages (unmodified backward-compatible contract).
- `GET /api/v1/investigations/{case_number}`: Retrieves case metadata (returns 200 for valid cases, 404 for non-existent cases).
- `PATCH /api/v1/investigations/{case_number}`: Updates case priority, status, or assignee.
- `GET /api/v1/investigations/{case_number}/intelligence`: Returns full deterministic M1–M12 intelligence dossier for the specified case.
- `POST /api/v1/investigations/enrich`: Accepts custom transaction context and performs real-time intelligence synthesis.

---

## 5. Frontend Integration Architecture

### 5.1 Client API Layer (`frontend/src/lib/api.ts`)
- `fetchCaseIntelligence(caseNumber: string)`: Calls `GET /api/v1/investigations/{case_number}/intelligence` with an automatic fallback to `getMockInvestigationIntelligence()` if running in mock/demo mode or if the backend is temporarily offline.
- Guarantees that frontend components will never break or crash due to network unavailability.

### 5.2 UI Presentation (`frontend/src/app/investigations/page.tsx`)
The `InvestigationIntelligencePanel` component renders dynamically whenever an investigator selects a case card:
1. **Header Banner**: Case context, subject account reference, pipeline status badge (`M1–M12 Pipeline`), and degraded mode indicator.
2. **Top Metric Row**:
   - M10 Composite Risk Score percentage gauge and Risk Level badge (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
   - M11 Auditable Evidence count and severity pills.
   - M12 Copilot recommended action count.
3. **Multi-Modal Signal Contributions Grid**:
   - 5 independent visual cards for `Modular Rules (M5)`, `Temporal Intelligence (M6)`, `Graph Intelligence (M7)`, `Tabular ML (M8)`, and `Graph ML / GNN (M9)`.
   - Score progress bars, effective weights, weighted risk points, and explanatory text.
4. **Deterministic Copilot Insights (M12)**:
   - Executive Narrative prose.
   - Key Forensic Findings with verified evidence badges.
   - Step-by-Step Suggested Actions with priority tags (`IMMEDIATE`, `HIGH`, `MEDIUM`).
5. **Auditable Evidence Dossier (M11)**:
   - Grid of verified forensic records displaying evidence IDs, categories, descriptions, severity, and associated entity linkages.
6. **Audit Boundaries & Follow-Up Questions**:
   - Recommended investigator interview questions.
   - Transparent disclaimer on algorithmic scope and data ingestion window limitations.
