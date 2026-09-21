<p align="center">
  <img src="docs/images/muletrace-banner.png" alt="MuleTrace AI Banner" width="100%" />
</p>

<h1 align="center">MuleTrace AI</h1>

<h3 align="center">Cross-Channel Mule Account Detection & Financial Crime Investigation Platform</h3>

<p align="center">
  <em>Multi-Modal Intelligence · Graph Analysis · Deterministic Explainability · AWS Deployed</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0--alpha-blue?style=for-the-badge" alt="Version" />
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-16+-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/AWS-Deployed-FF9900?style=for-the-badge&logo=amazon-web-services&logoColor=white" alt="AWS" />
  <img src="https://img.shields.io/badge/Neo4j-AuraDB-008CC1?style=for-the-badge&logo=neo4j&logoColor=white" alt="Neo4j" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Tests-471%20passed-brightgreen?style=flat-square" alt="Tests" />
  <img src="https://img.shields.io/badge/Milestones-M1--M14%20Complete-blue?style=flat-square" alt="Milestones" />
  <img src="https://img.shields.io/badge/made%20with-❤️-red?style=flat-square" alt="Made with Love" />
</p>

---

## 🎯 Executive Summary

| | |
|---|---|
| **WHAT** | End-to-end mule account detection and financial crime investigation platform that fuses five independent detection modalities into a single explainable risk score |
| **WHY** | Mule accounts — bank accounts used to funnel illicit funds — are the backbone of digital financial crime. Traditional rule-based systems detect fewer than 2% of mule accounts and generate 95%+ false positives |
| **HOW** | 14 deterministic fraud rules + temporal velocity analysis + graph topology intelligence + XGBoost tabular ML (57 features) + GraphSAGE inductive graph neural network → deterministic risk fusion → SHA-256 evidence engine → template-based investigation copilot → SOC analyst workspace |
| **UNIQUE** | Fully deterministic explainability pipeline (zero LLM dependency), multi-modal risk fusion with configurable weights and missing-modality policies, hexagonal ports-and-adapters architecture enabling cloud-agnostic business logic |
| **DEPLOYED** | AWS Amplify (frontend) → Amazon EC2 (backend + ML) → Amazon RDS PostgreSQL (data) + Neo4j AuraDB (graph) |

---

## 📑 Table of Contents

- [Problem](#-problem)
- [Solution](#-solution)
- [Detect → Understand → Trace → Explain → Investigate](#-detect--understand--trace--explain--investigate)
- [System Architecture](#️-system-architecture)
- [Intelligence Pipeline](#-intelligence-pipeline)
- [M1–M14 Engineering Implementation](#️-m1m14-engineering-implementation)
- [Multi-Modal Risk Fusion](#-multi-modal-risk-fusion)
- [Evidence & Investigation](#-evidence--investigation)
- [SOC Investigation Workflow](#️-soc-investigation-workflow)
- [BUILD IT — Cloud-Agnostic Architecture](#️-build-it--cloud-agnostic-architecture)
- [SHIP IT — AWS Deployment](#️-ship-it--aws-deployment)
- [Technology Stack](#-technology-stack)
- [Key Features](#-key-features)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Validation](#-validation)
- [Security & Deployment Notes](#-security--deployment-notes)
- [Current Limitations](#️-current-limitations)
- [Future Production Evolution](#-future-production-evolution)
- [Team](#-team)
- [Acknowledgements](#-acknowledgements)

---

## 🚨 Problem

India's digital payment ecosystem processes billions of UPI transactions monthly. While this drives financial inclusion, it has simultaneously created a massive attack surface for cybercriminals.

**Mule accounts** — bank accounts opened or compromised to funnel illicit funds — are the backbone of nearly every digital financial crime:

| Threat Vector | Impact |
|:---|:---|
| **Layering Speed** | Stolen funds traverse 5–15 accounts within minutes, making recovery nearly impossible |
| **Cross-Bank Chains** | Mule networks span multiple banks, defeating single-bank detection systems |
| **Volume** | A single fraud ring may operate hundreds to thousands of mule accounts simultaneously |
| **Investigation Overload** | Law enforcement faces massive complaint volumes with limited forensic tools |
| **Detection Gap** | Traditional rule-based systems generate 95%+ false positives |

---

## 💡 Solution

**MuleTrace AI** addresses these gaps with a unified, multi-modal intelligence platform:

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULETRACE AI CAPABILITIES                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅  Multi-modal mule account detection (Rules + ML + Graph)    │
│  ✅  Cross-channel transaction correlation (UPI/NEFT/IMPS/RTGS) │
│  ✅  Graph construction & interactive visualization             │
│  ✅  14 deterministic fraud pattern rules (R001–R014)           │
│  ✅  57-feature tabular ML with XGBoost + AutoGluon challenger  │
│  ✅  GraphSAGE inductive graph neural network (16→32→16)        │
│  ✅  5-modality deterministic risk fusion (0–100 score)         │
│  ✅  SHA-256 evidence engine with provenance & deduplication    │
│  ✅  Deterministic investigation copilot (zero LLM, auditable)  │
│  ✅  SOC analyst investigation workspace with intelligence API  │
│  ✅  Geospatial intelligence with impossible travel detection   │
│  ✅  AWS deployment (Amplify + EC2 + RDS + Neo4j AuraDB)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Detect → Understand → Trace → Explain → Investigate

```
  INGEST          ANALYZE           FUSE            EXPLAIN         INVESTIGATE
    │                │                │                │                │
    ▼                ▼                ▼                ▼                ▼
┌────────┐   ┌──────────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐
│ Trans- │   │ Rules (M5)   │   │ Risk     │   │ Evidence │   │ Copilot (M12)│
│ action │──▶│ Temporal (M6)│──▶│ Fusion   │──▶│ Engine   │──▶│ SOC Panel    │
│ Event  │   │ Graph   (M7) │   │ (M10)    │   │ (M11)    │   │ (M13)        │
│ (M1)   │   │ Tab ML  (M8) │   │ 0–100    │   │ SHA-256  │   │ Narrative +  │
│        │   │ GNN     (M9) │   │ Score    │   │ Ranked   │   │ Actions      │
└────────┘   └──────────────┘   └──────────┘   └──────────┘   └──────────────┘
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULETRACE AI — SYSTEM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐               │
│   │   Frontend    │     │   Backend    │     │  Database    │               │
│   │  (Next.js 14) │────▶│  (FastAPI)   │────▶│ (PostgreSQL) │               │
│   │  TypeScript   │     │  Uvicorn     │     │  SQLAlchemy  │               │
│   └──────────────┘     └──────┬───────┘     └──────────────┘               │
│                               │                                             │
│          ┌────────────────────┼────────────────────┐                        │
│          ▼                    ▼                    ▼                         │
│   ┌────────────┐    ┌──────────────┐    ┌────────────────┐                  │
│   │ Rules (M5) │    │ Graph Intel. │    │ ML Engines     │                  │
│   │ 14 Rules   │    │ NetworkX /   │    │ XGBoost (M8)   │                  │
│   │ R001–R014  │    │ Neo4j  (M7)  │    │ GraphSAGE (M9) │                  │
│   └─────┬──────┘    └──────┬───────┘    └───────┬────────┘                  │
│         │                  │                    │                            │
│         │    ┌─────────────┤                    │                            │
│         │    │ Temporal     │                    │                            │
│         │    │ Engine (M6)  │                    │                            │
│         │    └──────┬──────┘                    │                            │
│         │           │                           │                            │
│         └───────────┼───────────────────────────┘                            │
│                     ▼                                                        │
│           ┌──────────────────┐                                               │
│           │  Risk Fusion     │                                               │
│           │  Engine (M10)    │                                               │
│           │  Score: 0–100    │                                               │
│           └────────┬─────────┘                                               │
│                    ▼                                                         │
│           ┌──────────────────┐                                               │
│           │  Evidence Engine │                                               │
│           │  (M11) SHA-256   │                                               │
│           └────────┬─────────┘                                               │
│                    ▼                                                         │
│           ┌──────────────────┐                                               │
│           │  Investigation   │                                               │
│           │  Copilot (M12)   │                                               │
│           │  Deterministic   │                                               │
│           └────────┬─────────┘                                               │
│                    ▼                                                         │
│           ┌──────────────────┐                                               │
│           │  SOC Integration │                                               │
│           │  (M13) API +     │                                               │
│           │  Intelligence UI │                                               │
│           └──────────────────┘                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Core Architectural Principle:**

> **BUSINESS LOGIC = CLOUD AGNOSTIC** · **INFRASTRUCTURE = REPLACEABLE THROUGH ADAPTERS**

The domain layer ([`backend/app/domain/`](backend/app/domain/)) defines pure Python ports/interfaces. Infrastructure adapters (NetworkX, Neo4j, XGBoost, AutoGluon) implement these ports, enabling the same business logic to run locally or on any cloud provider.

---

## 🧠 Intelligence Pipeline

The intelligence pipeline processes transactions through five independent detection modalities before fusing their signals:

| Stage | Engine | Implementation | Output |
|:---:|:---|:---|:---|
| **M5** | [Rules Engine](backend/app/engines/rules/) | 14 deterministic fraud pattern rules (R001–R014) | Rule matches, severity, score contribution |
| **M6** | [Temporal Engine](backend/app/engines/temporal/) | Velocity bursts, rapid pass-through, activity windows (5m/15m/1h/24h) | Temporal risk signals |
| **M7** | [Graph Intelligence](backend/app/engines/graph/intelligence/) | NetworkX topology — cycles, fan-in/out, shared device/IP, centrality | Graph feature vector |
| **M8** | [Tabular ML](backend/app/engines/ml/tabular/) | XGBoost on 57 features, chronological 70/15/15 split | Fraud probability [0, 1] |
| **M9** | [GraphSAGE](backend/app/engines/ml/graph/) | 2-layer GNN (16→32→16→sigmoid), weighted BCE | Structural fraud probability |
| **M10** | [Risk Fusion](backend/app/engines/risk_fusion/) | Weighted combination, 5 modalities → composite score 0–100 | Risk score + level + driver |
| **M11** | [Evidence Engine](backend/app/engines/evidence/) | SHA-256 provenance, deduplication, severity ranking | Ranked evidence package |
| **M12** | [Investigation Copilot](backend/app/engines/ai/) | Deterministic templates, zero LLM | Narrative + actions + findings |
| **M13** | [SOC Integration](backend/app/services/soc_integration_service.py) | End-to-end pipeline orchestration, case management API | Intelligence dossier |

---

## ⚙️ M1–M14 Engineering Implementation

### M1 — Canonical Transaction Layer

Immutable domain model ([`TransactionEvent`](backend/app/domain/models.py)) representing cross-channel transactions (UPI, NEFT, IMPS, RTGS) with deterministic two-way mapping ([`TransactionMapper`](backend/app/domain/transaction_mapper.py)).

### M2 — Domain Interfaces / Ports

Pure Python abstract interfaces ([`backend/app/domain/interfaces.py`](backend/app/domain/interfaces.py)) defining infrastructure-agnostic contracts:
- `GraphRepository` — graph storage and query
- `TransactionRepository` — transaction persistence
- `AlertRepository` — alert lifecycle
- `ModelService` — ML model prediction
- `InvestigationCopilot` — investigation narrative generation

### M3 — Local NetworkX Graph Adapter

In-memory graph adapter ([`graph_nx.py`](backend/app/repositories/graph_nx.py)) implementing `GraphRepository` using NetworkX directed multigraph. Zero cloud dependency, fully local development support.

### M4 — Graph Adapter Validation

Comprehensive test suite validating graph adapter contract compliance. Both NetworkX (local) and Neo4j (production) adapters validated against identical interface contracts.

### M5 — 14 Deterministic Fraud Rules

Each rule implemented as an independent module in [`backend/app/engines/rules/`](backend/app/engines/rules/):

| Rule | Pattern | File |
|:---:|:---|:---|
| R001 | High Velocity | [`r001.py`](backend/app/engines/rules/r001.py) |
| R002 | Fan-In | [`r002.py`](backend/app/engines/rules/r002.py) |
| R003 | Fan-Out | [`r003.py`](backend/app/engines/rules/r003.py) |
| R004 | Mule Chain | [`r004.py`](backend/app/engines/rules/r004.py) |
| R005 | Smurfing / Structuring | [`r005.py`](backend/app/engines/rules/r005.py) |
| R006 | Shared Device | [`r006.py`](backend/app/engines/rules/r006.py) |
| R007 | Dormant Activation | [`r007.py`](backend/app/engines/rules/r007.py) |
| R008 | New Account Abuse | [`r008.py`](backend/app/engines/rules/r008.py) |
| R009 | Cross-Channel | [`r009.py`](backend/app/engines/rules/r009.py) |
| R010 | Shared IP | [`r010.py`](backend/app/engines/rules/r010.py) |
| R011 | Impossible Travel | [`r011.py`](backend/app/engines/rules/r011.py) |
| R012 | Night Activity | [`r012.py`](backend/app/engines/rules/r012.py) |
| R013 | Shared Beneficiary | [`r013.py`](backend/app/engines/rules/r013.py) |
| R014 | Circular Flow | [`r014.py`](backend/app/engines/rules/r014.py) |

### M6 — Temporal Intelligence

[`backend/app/engines/temporal/`](backend/app/engines/temporal/) extracts time-series behavioral signals:
- Multi-window velocity aggregation (5m, 15m, 1h, 24h)
- Burst detection (statistically anomalous transaction clusters)
- Rapid pass-through detection (funds received and immediately forwarded)
- Activity change ratio (dormancy-to-activity transitions)

### M7 — Graph Intelligence

[`backend/app/engines/graph/intelligence/`](backend/app/engines/graph/intelligence/) computes topological features from the transaction graph:
- Degree metrics (in/out/total, unique counterparties)
- Flow dynamics (inbound/outbound volume, pass-through ratio)
- Cycle detection (circular routing, lengths 2–5)
- Shared infrastructure (device/IP overlap)
- Centrality measures (PageRank, betweenness, clustering density)

### M8 — Tabular ML + AutoGluon Challenger

[`backend/app/engines/ml/tabular/`](backend/app/engines/ml/tabular/)

- **57 canonical features** across 4 categories:
  - 14 transaction-native features
  - 14 device & risk telemetry features
  - 12 temporal intelligence features (from M6)
  - 17 graph intelligence features (from M7)
- **Chronological 70/15/15 split** — no random shuffle, strict leakage prevention
- **Primary model:** scikit-learn pipeline + XGBoost classifier ([`xgboost_adapter.py`](backend/app/engines/ml/tabular/xgboost_adapter.py))
- **Challenger:** AutoGluon as optional benchmark ([`autogluon_adapter.py`](backend/app/engines/ml/tabular/autogluon_adapter.py))
- **Model artifacts preserved** to [`backend/app/engines/ml/artifacts/`](backend/app/engines/ml/artifacts/)
- Zero startup training — inference from pre-trained artifacts only

### M9 — GraphSAGE Graph ML

[`backend/app/engines/ml/graph/graphsage_model.py`](backend/app/engines/ml/graph/graphsage_model.py)

Pure PyTorch implementation of inductive GraphSAGE (Hamilton et al., NeurIPS 2017):

- **Heterogeneous graph:** account, device, and IP nodes
- **16-dimensional account feature representation** ([`graph_schema.py`](backend/app/engines/ml/graph/graph_schema.py)):
  - `in_degree`, `out_degree`, `total_degree`, `unique_inbound_counterparties`, `unique_outbound_counterparties`, `inbound_volume`, `outbound_volume`, `fan_in_ratio`, `fan_out_ratio`, `account_age_days`, `velocity_l6h`, `temporal_burst_detected`, `temporal_tx_count_1h`, `shared_device_count`, `shared_ip_count`, `neighborhood_density`
- **Architecture:** `16 → 32 → 16 → sigmoid`
  - SAGEConv Layer 1: 16 → 32 (mean aggregation, ReLU, dropout 0.1, L2 normalization)
  - SAGEConv Layer 2: 32 → 16 (mean aggregation, ReLU, dropout 0.1, L2 normalization)
  - Classification head: Linear(16 → 1) + Sigmoid
- **Weighted BCE loss** with positive-class weighting for class imbalance
- **Safe fallback:** returns default score (0.5) when trained artifacts are unavailable
- **Zero startup training** — uses pre-trained model artifacts

### M10 — Deterministic Risk Fusion

See [Multi-Modal Risk Fusion](#-multi-modal-risk-fusion) section below.

### M11 — Deterministic Evidence Engine

See [Evidence & Investigation](#-evidence--investigation) section below.

### M12 — Deterministic Investigation Copilot

See [Evidence & Investigation](#-evidence--investigation) section below.

### M13 — SOC Integration

See [SOC Investigation Workflow](#️-soc-investigation-workflow) section below.

### M14 — BUILD IT Release / Hardening

Final hardening milestone:
- 471 tests passing, 0 regressions
- TypeScript compilation clean
- ESLint passing
- Next.js production build successful
- Comprehensive milestone audit reports in [`docs/reports/`](docs/reports/)

---

## 🎯 Multi-Modal Risk Fusion

[`backend/app/engines/risk_fusion/`](backend/app/engines/risk_fusion/)

The risk fusion engine synthesizes five independent detection modalities into a single composite risk score.

### Modality Weights

| Modality | Weight | Description |
|:---|:---:|:---|
| **Rules Engine (M5)** | **25%** | Forensic heuristics, deterministic pattern matches |
| **Tabular ML (M8)** | **25%** | Gradient-boosted tabular decision boundaries |
| **Graph Intelligence (M7)** | **20%** | Topological cycles, shared device/IP clusters, fan-in/out |
| **Temporal Intelligence (M6)** | **15%** | Velocity bursts, rapid pass-through sequences |
| **Graph ML / GraphSAGE (M9)** | **15%** | Inductive GraphSAGE structural node representations |
| **Total** | **100%** | Strictly validated, non-negative, normalized to 1.0 |

### Risk Score & Levels

Composite risk score range: **0–100**

| Risk Level | Score Range |
|:---|:---|
| 🟢 **LOW** | ≤ 30 |
| 🟡 **MEDIUM** | > 30 to 65 |
| 🟠 **HIGH** | > 65 to 85 |
| 🔴 **CRITICAL** | > 85 |

### Missing Modality Policies

When a detection modality is unavailable (e.g., ML model not yet trained):

| Policy | Behavior |
|:---|:---|
| **`RENORMALIZE_AVAILABLE`** (default) | Redistributes missing weights proportionally among available modalities |
| **`ZERO_CONTRIBUTION`** | Missing modalities contribute 0.0; original weights preserved |
| **`PENALTY_BASELINE`** | Missing modalities assume neutral 0.20 baseline risk |

### Explainability

Every fusion result preserves:
- Individual modality contributions (exact score per modality)
- Effective weights applied (accounting for missing modality policy)
- **Primary driver** — the modality contributing the highest signal
- Missing modalities list and policy applied

---

## 🔎 Evidence & Investigation

### M11 — Deterministic Evidence Engine

[`backend/app/engines/evidence/`](backend/app/engines/evidence/)

The evidence engine sits downstream of risk fusion (M10) and produces verifiable, tamper-evident forensic artifacts:

- **Deterministic SHA-256 evidence IDs** — each evidence item receives a reproducible hash based on source, reference, category, and linked entities ([`provenance.py`](backend/app/engines/evidence/provenance.py))
- **Evidence deduplication** — identical findings from overlapping modalities are merged while preserving the highest severity and union of entity references ([`deduplication.py`](backend/app/engines/evidence/deduplication.py))
- **Multi-factor ranking** — evidence items ranked by severity weight → source authority priority → signal strength → deterministic tie-breaker ([`ranking.py`](backend/app/engines/evidence/ranking.py))
- **Factual summaries** — structured text descriptions generated from verified data only ([`renderer.py`](backend/app/engines/evidence/renderer.py))
- **M10 score preservation** — evidence engine never recomputes or alters composite risk scores

### M12 — Deterministic Investigation Copilot

[`backend/app/engines/ai/`](backend/app/engines/ai/)

The investigation copilot is **intentionally LLM-free and fully deterministic**:

| Attribute | Implementation |
|:---|:---|
| **LLM dependency** | **Zero** — no OpenAI, Gemini, Bedrock, Claude, or any generative AI |
| **Template engine** | [`templates.py`](backend/app/engines/ai/templates.py) — rule-governed deterministic text renderers |
| **Core class** | [`DeterministicInvestigationCopilot`](backend/app/engines/ai/copilot.py) |
| **Domain port** | Implements [`InvestigationCopilot`](backend/app/domain/interfaces.py) interface |

**Why deterministic?**
- **Reproducibility** — identical inputs always produce identical outputs
- **Auditability** — every statement traces to verified M11 evidence IDs
- **Traceability** — complete provenance chain from raw signal to narrative
- **Predictable output** — no hallucination risk, no prompt injection surface
- **Evidence integrity** — preserves exact M10 risk scores and M11 evidence without modification

**Outputs:**
- Executive investigation narrative
- Structured key forensic findings (linked to evidence IDs)
- Prioritized recommended investigator actions (IMMEDIATE / HIGH / MEDIUM / LOW)
- Suggested follow-up questions for suspect/victim interviews
- Transparent limitation disclosures regarding data freshness and scope

---

## 🖥️ SOC Investigation Workflow

### M13 — SOC Integration

Orchestrated by [`SOCIntegrationService`](backend/app/services/soc_integration_service.py) and exposed through the investigations API ([`backend/app/api/v1/investigations.py`](backend/app/api/v1/investigations.py)):

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/v1/investigations` | `GET` | List active SOC cases |
| `/api/v1/investigations/{case}` | `GET` | Case overview (priority, accounts, volume) |
| `/api/v1/investigations/{case}` | `PATCH` | Update status, priority, assignee |
| `/api/v1/investigations/{case}/intelligence` | `GET` | **Full intelligence dossier** (M5→M12 pipeline) |
| `/api/v1/investigations/enrich` | `POST` | Ad-hoc multi-modal enrichment |
| `/api/v1/investigations/copilot` | `POST` | Standalone copilot synthesis |

### Intelligence Dossier Pipeline

The `/intelligence` endpoint executes the complete pipeline:

```
Rules (M5) → Temporal (M6) → Graph (M7) → Tabular ML (M8) → Graph ML (M9)
    → Risk Fusion (M10) → Evidence (M11) → Copilot (M12)
```

**Returns:**
- Composite risk score and risk level
- Per-modality contributions with effective weights
- Primary risk driver identification
- Deduplicated, ranked evidence items with SHA-256 provenance
- Deterministic investigation narrative and recommended actions

### Frontend Intelligence Panel

The investigations page renders a multi-panel intelligence workspace:
- **Risk gauge** with score, level badge, and evidence/action counters
- **5-modality contribution grid** — individual cards for Rules, Temporal, Graph, Tabular ML, and GraphSAGE with progress bars and effective weights
- **Copilot insights** — executive narrative, key findings, and recommended actions
- **Evidence dossier** — forensic evidence table with entity linkages and evidence IDs

---

## 🛠️ BUILD IT — Cloud-Agnostic Architecture

The BUILD IT architecture is designed to be **infrastructure-independent**. Business logic has zero cloud provider coupling.

```
┌─────────────────────────────────────────────────────────────────┐
│                    BUILD IT — LOCAL DEVELOPMENT                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Frontend (Next.js 14 / React / TypeScript)                    │
│       ├── Cytoscape.js + fcose (graph visualization)            │
│       ├── React Leaflet (geospatial mapping)                    │
│       ├── Recharts (data visualization)                         │
│       └── Framer Motion (animations)                            │
│                                                                 │
│   Backend (FastAPI / Uvicorn / Python 3.11+)                    │
│       ├── Domain Layer (pure Python ports & interfaces)         │
│       ├── Engines (rules, temporal, graph, ML, fusion, evidence)│
│       ├── Repositories (graph_nx, graph_neo4j, transaction)     │
│       └── Services (SOC integration, alerts, analytics)         │
│                                                                 │
│   Data                                                          │
│       ├── PostgreSQL + SQLAlchemy + Alembic                     │
│       ├── NetworkX (local graph, zero cloud dependency)         │
│       └── Neo4j (production graph database)                     │
│                                                                 │
│   ML                                                            │
│       ├── scikit-learn + XGBoost (tabular ML)                   │
│       ├── AutoGluon (optional challenger)                       │
│       └── PyTorch + GraphSAGE (graph ML)                        │
│                                                                 │
│   Testing                                                       │
│       └── pytest (474 tests, 471 passing)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ☁️ SHIP IT — AWS Deployment

The production deployment uses AWS managed services:

```
    User (Browser)
         │
         ▼
    ┌──────────────────┐
    │  AWS Amplify      │  ← Next.js frontend hosting
    │  Hosting          │
    └────────┬─────────┘
             │ HTTPS
             ▼
    ┌──────────────────┐
    │  Amazon EC2       │  ← FastAPI backend + ML/graph processing
    │  (Uvicorn)        │
    └────────┬─────────┘
             │
      ┌──────┴──────┐
      │              │
      ▼              ▼
┌──────────┐   ┌──────────────┐
│ Amazon   │   │ Neo4j        │
│ RDS      │   │ AuraDB       │
│ Postgres │   │ (Graph DB)   │
└──────────┘   └──────────────┘
```

### AWS Services

| AWS Service | Purpose |
|:---|:---|
| **AWS Amplify Hosting** | Next.js frontend hosting, CI/CD, and deployment |
| **Amazon EC2** | FastAPI backend server, ML inference, graph processing |
| **Amazon RDS for PostgreSQL** | Managed relational application database |
| **Amazon EBS** | Persistent block storage for EC2 instance |
| **AWS IAM** | Identity and access management for service roles |
| **Amazon VPC** | Network isolation for backend and database tiers |
| **Security Groups** | Network access control (EC2 ↔ RDS, ingress rules) |

### External Managed Service

| Service | Purpose |
|:---|:---|
| **Neo4j AuraDB** | Managed graph database for production graph queries |

---

## 🧰 Technology Stack

### BUILD IT — Development Stack

| Category | Technology | Purpose |
|:---|:---|:---|
| **Frontend** | Next.js 14 | React framework (App Router) |
| | React 18 | UI library |
| | TypeScript 5 | Type safety |
| | Tailwind CSS | Utility-first styling |
| | Cytoscape.js + fcose | Interactive graph visualization |
| | React Leaflet / Leaflet | Geospatial mapping |
| | Recharts | Data visualization / charts |
| | Framer Motion | UI animations |
| | Zustand | State management |
| **Backend** | Python 3.11+ | Backend language |
| | FastAPI | REST API framework |
| | Uvicorn | ASGI server |
| | Pydantic | Data validation |
| **Data** | PostgreSQL 16 | Primary relational database |
| | SQLAlchemy | ORM |
| | Alembic | Database migrations |
| **Graph** | NetworkX | Local graph computation (zero cloud dependency) |
| | Neo4j | Production graph database |
| | Cytoscape.js + fcose | Frontend graph rendering |
| **ML** | scikit-learn | ML preprocessing and pipelines |
| | XGBoost | Gradient boosting classifier |
| | AutoGluon | Optional challenger / benchmark |
| | PyTorch | Deep learning framework |
| | GraphSAGE | Inductive graph neural network |
| **Geo** | Leaflet / React Leaflet | Geospatial maps and impossible travel visualization |
| **Testing** | pytest | Backend test framework (474 tests) |

### SHIP IT — AWS Deployment Stack

| Service | Purpose |
|:---|:---|
| **AWS Amplify Hosting** | Next.js frontend hosting and deployment |
| **Amazon EC2** | FastAPI backend and ML/graph processing |
| **Amazon RDS for PostgreSQL** | Managed relational application database |
| **Amazon EBS** | Persistent EC2 block storage |
| **AWS IAM** | Identity and access management |
| **Amazon VPC** | Network isolation |
| **Security Groups** | Network access control |
| **Neo4j AuraDB** | Managed graph database |

---

## 📊 Key Features

### 🔗 Graph Intelligence
- Transaction graph construction using NetworkX (local) and Neo4j (production)
- Community detection, centrality analysis (PageRank, betweenness)
- Cycle detection (circular money flows, lengths 2–5)
- Shared device and IP cluster identification
- Interactive Cytoscape.js visualization with fcose force-directed layout

### 🤖 Machine Learning
- **Tabular ML:** 57-feature XGBoost pipeline with chronological data splitting
- **Graph ML:** 2-layer GraphSAGE for inductive node classification
- **AutoGluon:** Optional challenger model for benchmark comparison
- Pre-trained artifact loading, zero startup training

### ⏱️ Temporal Intelligence
- Multi-window velocity analysis (5m, 15m, 1h, 24h)
- Burst detection and rapid pass-through identification
- Activity change ratio tracking

### 📋 Rule Engine
- 14 deterministic fraud pattern rules (R001–R014)
- High velocity, fan-in/out, smurfing, circular flow, impossible travel, etc.
- Configurable thresholds per rule

### 🗺️ Geo Intelligence
- Geospatial mapping with React Leaflet
- Impossible travel detection between transaction locations
- Risk density visualization

### 🔍 Investigation Workspace
- SOC-style case management with intelligence API
- 5-modality contribution dashboard
- Evidence dossier with SHA-256 provenance
- Deterministic investigation narrative

---

## 📁 Project Structure

```
D:\Team_Cipher_Unit/
│
├── README.md                              # This file
├── REPORT.md                              # Engineering source-of-truth
├── REPORT_AWS_PROTOTYPE_READINESS.md      # AWS deployment readiness report
├── .env.example                           # Environment variable template
│
├── backend/                               # FastAPI Application
│   ├── requirements.txt                   # Python dependencies
│   ├── pyproject.toml                     # Project configuration
│   ├── alembic.ini                        # Database migration config
│   ├── app/
│   │   ├── main.py                        # Application entry point
│   │   ├── api/v1/                        # REST API endpoints
│   │   │   ├── accounts.py
│   │   │   ├── alerts.py
│   │   │   ├── analytics.py
│   │   │   ├── dashboard.py
│   │   │   ├── geo.py
│   │   │   ├── graph.py
│   │   │   ├── health.py
│   │   │   ├── investigations.py          # SOC integration (M13)
│   │   │   ├── reports.py
│   │   │   └── transactions.py
│   │   ├── domain/                        # Domain ports & models (M1, M2)
│   │   │   ├── interfaces.py             # Abstract ports
│   │   │   ├── models.py                 # TransactionEvent, domain models
│   │   │   └── transaction_mapper.py     # Canonical mapping
│   │   ├── engines/                       # Intelligence engines
│   │   │   ├── rules/                    # M5: R001–R014
│   │   │   ├── temporal/                 # M6: Temporal intelligence
│   │   │   ├── graph/                    # M7: Graph intelligence
│   │   │   │   └── intelligence/         # Graph engine, metrics, models
│   │   │   ├── ml/                       # M8 + M9: ML engines
│   │   │   │   ├── tabular/             # XGBoost, AutoGluon adapters
│   │   │   │   ├── graph/               # GraphSAGE model, adapter
│   │   │   │   └── artifacts/           # Pre-trained model files
│   │   │   ├── risk_fusion/              # M10: Multi-modal fusion
│   │   │   ├── evidence/                 # M11: Evidence engine
│   │   │   └── ai/                       # M12: Deterministic copilot
│   │   ├── repositories/                  # Infrastructure adapters
│   │   │   ├── graph_nx.py               # M3: NetworkX adapter
│   │   │   └── graph_neo4j.py            # Neo4j adapter
│   │   ├── services/                      # Business service layer
│   │   │   └── soc_integration_service.py # M13: SOC orchestration
│   │   ├── models/                        # SQLAlchemy models
│   │   ├── schemas/                       # Pydantic schemas
│   │   ├── database/                      # DB connections
│   │   ├── middleware/                    # CORS, logging, error handling
│   │   └── config/                        # Settings, constants
│   └── tests/                             # 474 tests across all milestones
│
├── frontend/                              # Next.js 14 Application
│   ├── package.json
│   ├── next.config.mjs
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── src/
│       ├── app/                           # App Router pages
│       │   ├── dashboard/                # SOC overview
│       │   ├── transactions/             # Transaction ledger
│       │   ├── graph/                    # Cytoscape.js graph workspace
│       │   ├── geo/                      # Leaflet geospatial map
│       │   ├── alerts/                   # Alert triage queue
│       │   ├── investigations/           # Investigation + intelligence panel
│       │   └── reports/                  # Regulatory report generation
│       ├── components/                    # Shared UI components
│       ├── hooks/                         # Custom React hooks
│       └── lib/                           # Utilities, API client, types
│
├── ml/                                    # Standalone ML training
│   ├── train_models.py                   # Model training pipeline
│   ├── transaction_fraud_detection.py    # XGBoost + RandomForest training
│   └── transactions.csv                  # Training dataset
│
├── docs/                                  # Documentation
│   ├── architecture/                     # Architecture specifications
│   ├── reports/                          # Milestone audit reports
│   └── images/                           # Banner, architecture diagrams
│
└── scripts/                               # Development scripts
```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version |
|:---|:---|
| **Node.js** | 18.x+ |
| **Python** | 3.11+ |
| **PostgreSQL** | 16.x |
| **Git** | 2.40+ |

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/Sph1333y/mule_tracker.git
cd mule_tracker

# Copy environment variables
cp .env.example .env
# Edit .env with your database credentials
```

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
alembic upgrade head            # Run database migrations
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs (Swagger UI)
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

#### Run Tests

```bash
cd backend
pytest -v
```

---

## 🧪 Validation

### Backend Test Suite

| Metric | Result |
|:---|:---|
| **Total tests** | 474 |
| **Passed** | 471 |
| **Skipped** | 1 (AutoGluon optional dependency) |
| **Pre-existing baseline failures** | 2 (`test_postgres_dsn_computation`, `test_get_dashboard_overview`) |
| **Regressions introduced** | **0** |

**Milestone coverage:**

| Milestone | Tests |
|:---|:---:|
| M1/M2 Domain | 21 |
| M5 Rules Engine | 35 |
| M6 Temporal | 30 |
| M7 Graph Intelligence | 42 |
| M8 Tabular ML | 33 |
| M9 GraphSAGE | 31 |
| M10 Risk Fusion | 45 |
| M11 Evidence Engine | 44 |
| M12 Investigation Copilot | 43 |
| M13 SOC Integration | 11 |
| M14 Release | 2 |
| Repositories & Adapters | 29 |

### Frontend Validation

| Check | Status |
|:---|:---|
| TypeScript compilation | ✅ Passed |
| ESLint | ✅ Passed |
| Next.js production build | ✅ Passed |

> **Transparency note:** Two pre-existing baseline test failures (`test_postgres_dsn_computation` and `test_get_dashboard_overview`) are documented and preserved in the release protocol. These are known baseline items, not regressions.

---

## 🔐 Security & Deployment Notes

- Environment variables managed via `.env` (never committed)
- JWT-based authentication with role-based access control
- CORS middleware configured for frontend-backend communication
- Database credentials isolated in environment configuration
- VPC and Security Group network isolation on AWS
- IAM roles for service-level access control

---

## ⚠️ Current Limitations

- **Prototype scope:** This is a hackathon/prototype implementation, not a production-certified banking platform
- **No real-time streaming:** Transaction processing is batch/request-based, not event-streamed
- **Single-bank scope:** Current implementation operates within a single institution's data boundary
- **No regulatory certification:** Thresholds are engineering defaults, not RBI/FIU-IND certified values
- **Model training data:** ML models trained on synthetic/sample datasets, not production banking data
- **Two known baseline test failures:** Documented and tracked (`test_postgres_dsn_computation`, `test_get_dashboard_overview`)

---

## 🔮 Future Production Evolution

| Area | Evolution |
|:---|:---|
| **Real-Time Streaming** | Apache Kafka integration for live transaction processing |
| **Multi-Bank Federation** | Cross-bank mule network detection with privacy-preserving analytics |
| **LLM Copilot Upgrade** | Optional LLM integration for M12 copilot (maintaining deterministic as default) |
| **Advanced GNN** | Heterogeneous graph attention networks for richer structural learning |
| **Regulatory Integration** | Direct API integration with RBI/FIU-IND reporting systems |
| **Mobile Companion** | React Native app for field investigators |

---

## 👥 Team

```text
┌──────────────────────────────────────────────────────────────┐
│                     Team CipherUnit                           │
├──────────────────────────────────────────────────────────────┤
│ 👤 Athishwar K     → Backend                                 │
│ 👤 Karmugilan R    → Graph Intelligence                      │
│ 👤 Sanjay B        → Frontend & Machine Learning             │
│ 👤 Sakthi Prakash  → Frontend                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 🙏 Acknowledgements

- **Reserve Bank of India (RBI)** — For AML/CFT guidelines and regulatory frameworks
- **Financial Intelligence Unit - India (FIU-IND)** — For STR/CTR reporting standards
- **Indian Cyber Crime Coordination Centre (I4C)** — For cybercrime investigation frameworks
- **NPCI** — For UPI transaction ecosystem documentation
- **Neo4j** — For graph database and graph data science capabilities
- **FastAPI** — For high-performance API framework
- **Next.js** — For production-grade React framework
- **PyTorch** — For deep learning framework powering GraphSAGE

---

<p align="center">
  <strong>MuleTrace AI</strong> — Defending India's Financial Ecosystem with Multi-Modal Intelligence
</p>

<p align="center">
  Built with ❤️ by <strong>Team CipherUnit</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20in-India-orange?style=for-the-badge&logo=flag-india" alt="Made in India" />
</p>
