<p align="center">
  <img src="docs/images/muletrace-banner.png" alt="MuleTrace AI Banner" width="100%" />
</p>

<h1 align="center">MuleTrace AI</h1>

<h3 align="center">Cross-Channel Mule Account Detection & Financial Crime Investigation Platform</h3>

<p align="center">
  <em>Multi-Modal Intelligence · Graph Analytics · Deterministic Explainability · AWS Prototype Deployed</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0--alpha-blue?style=for-the-badge" alt="Version" />
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-16+-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/AWS-Amplify%20%2B%20EC2%20%2B%20RDS-FF9900?style=for-the-badge&logo=amazon-web-services&logoColor=white" alt="AWS Deployed" />
  <img src="https://img.shields.io/badge/Neo4j-AuraDB-008CC1?style=for-the-badge&logo=neo4j&logoColor=white" alt="Neo4j" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Tests-471%20passed-brightgreen?style=flat-square" alt="Tests" />
  <img src="https://img.shields.io/badge/Milestones-M1--M14%20Complete-blue?style=flat-square" alt="Milestones" />
  <img src="https://img.shields.io/badge/Architecture-Hexagonal%20Ports%20%26%20Adapters-orange?style=flat-square" alt="Architecture" />
  <img src="https://img.shields.io/badge/Copilot-Deterministic%20(Zero%20LLM)-purple?style=flat-square" alt="Copilot" />
</p>

---

## 🎯 Executive Summary

| Dimension | Specification |
|---|---|
| **WHAT** | An end-to-end mule account detection and financial crime investigation platform that synthesizes five independent detection modalities into a single explainable, auditable risk score. |
| **WHY** | Mule accounts — bank accounts used to funnel illicit funds — are the backbone of digital financial crime. Traditional rule-based systems detect fewer than 2% of mule accounts and generate over 95% false positives across high-velocity digital payment rails. |
| **HOW** | 14 deterministic fraud rules (M5) + multi-window temporal velocity analysis (M6) + topological graph intelligence (M7) + 57-feature XGBoost tabular ML (M8) + 2-layer GraphSAGE inductive graph neural network (M9) → deterministic multi-modal risk fusion (M10) → SHA-256 tamper-evident evidence engine (M11) → template-driven deterministic investigation copilot (M12) → SOC analyst workspace (M13). |
| **UNIQUE** | Fully deterministic explainability pipeline (zero LLM dependency; zero hallucination risk), multi-modal risk fusion with configurable weights and dynamic missing-signal renormalization, and hexagonal ports-and-adapters architecture ensuring 100% cloud-agnostic business logic. |
| **DEPLOYED** | AWS Amplify Hosting (Next.js frontend) → Amazon EC2 (FastAPI backend + ML/graph inference) → Amazon RDS PostgreSQL (relational application data) + Neo4j AuraDB (managed transaction graph). |

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
- [SHIP IT — AWS Prototype Deployment](#️-ship-it--aws-prototype-deployment)
- [Technology Stack](#-technology-stack)
- [Key Features](#-key-features)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Validation](#-validation)
- [Security & Deployment Notes](#-security--deployment-notes)
- [Current Limitations](#️-current-limitations)
- [Future Production Evolution](#-future-production-evolution)
- [Team Cipher Unit](#-team-cipher-unit)
- [Acknowledgements](#-acknowledgements)

---

## 🚨 Problem

India's digital payment ecosystem processes billions of retail transactions monthly across UPI, IMPS, NEFT, and RTGS. While driving unprecedented financial inclusion, this velocity has created a massive attack surface for cybercriminals.

**Mule accounts** — bank accounts opened or compromised to funnel, layer, and withdraw stolen funds — are the backbone of modern digital financial crime:

| Threat Vector | Operational Reality | Investigation Bottleneck |
|:---|:---|:---|
| **Layering Velocity** | Stolen funds traverse 5–15 intermediary accounts within minutes. | Manual investigation takes 30–90 days per incident dossier. |
| **Cross-Bank Networks** | Fraud rings spread hops across disparate public, private, and cooperative banks. | Siloed institution data defeats isolated perimeter detection rules. |
| **Recruitment Volume** | Criminal syndicates recruit thousands of student, rural, or dormant accounts simultaneously. | High volume overwhelms bank compliance and fraud operations teams. |
| **False-Positive Drag** | Primitive threshold rules generate upwards of 95% false-positive alerts. | Legitimate customer transactions are disrupted while real syndicates evade capture. |
| **Explainability Deficit** | Black-box predictive models fail to provide auditable evidence for regulatory filings. | Compliance officers cannot submit Suspicious Activity Reports without evidentiary provenance. |

---

## 💡 Solution

**MuleTrace AI** resolves these operational deficits through a unified, multi-modal intelligence and investigation platform:

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULETRACE AI CAPABILITIES                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅  Multi-Modal Mule Detection (Rules + ML + Temporal + Graph) │
│  ✅  Cross-Channel Correlation (UPI / NEFT / IMPS / RTGS)       │
│  ✅  Dynamic Graph Topology & Cycle Detection (NetworkX/Neo4j)  │
│  ✅  14 Deterministic Fraud Pattern Rules (R001–R014)           │
│  ✅  57-Feature Tabular ML Pipeline (XGBoost + AutoGluon)       │
│  ✅  Inductive GraphSAGE Neural Network (PyTorch, 16→32→16)     │
│  ✅  Deterministic Risk Fusion Engine (0–100 Normalized Score)  │
│  ✅  Tamper-Evident SHA-256 Evidence Engine with Deduplication  │
│  ✅  Deterministic Investigation Copilot (Zero LLM, Auditable)  │
│  ✅  SOC Analyst Workbench with Complete Intelligence Dossier   │
│  ✅  Geospatial Risk Mapping with Impossible Travel Detection   │
│  ✅  Hexagonal Architecture: Cloud-Agnostic BUILD → AWS SHIP    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Detect → Understand → Trace → Explain → Investigate

The investigative lifecycle transforms raw transactional events into actionable, auditable forensic intelligence:

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

1. **Detect**: Real-time evaluation against 14 domain rules, temporal window velocity, and graph topology.
2. **Understand**: Independent scoring across tabular feature distributions and structural neighborhood embeddings.
3. **Trace**: Graph path analysis and cycle traversal revealing circular laundering and multi-hop mule chains.
4. **Explain**: Deterministic fusion computing exact modality contributions and assigning cryptographic evidence hashes.
5. **Investigate**: Template-driven copilot generating executive narratives, verified findings, and prioritized actions for SOC analysts.

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

### Core Architectural Principle

> **BUSINESS LOGIC = CLOUD AGNOSTIC · INFRASTRUCTURE = REPLACEABLE THROUGH ADAPTERS**

MuleTrace AI enforces strict hexagonal architecture (ports and adapters):
- **Domain Layer ([`backend/app/domain/`](backend/app/domain/))**: Contains pure Python models and abstract interfaces with zero framework or cloud dependencies.
- **Engines ([`backend/app/engines/`](backend/app/engines/))**: Encapsulate pure detection logic (rules, temporal windows, topology metrics, ML inference, fusion, evidence, copilot).
- **Adapters & Repositories ([`backend/app/repositories/`](backend/app/repositories/))**: Pluggable implementations. Local development utilizes an in-memory NetworkX directed multigraph adapter ([`graph_nx.py`](backend/app/repositories/graph_nx.py)), while production connects via the Neo4j Cypher adapter ([`graph_neo4j.py`](backend/app/repositories/graph_neo4j.py)).

---

## 🧠 Intelligence Pipeline

The intelligence pipeline processes transactional events through five independent detection modalities before synthesizing composite risk:

| Milestone | Subsystem | Implementation Location | Output Representation |
|:---:|:---|:---|:---|
| **M5** | [Rules Engine](backend/app/engines/rules/) | 14 deterministic fraud pattern rules (R001–R014) | Match flags, rule severity, score contribution |
| **M6** | [Temporal Engine](backend/app/engines/temporal/) | Multi-window velocity (5m, 15m, 1h, 24h), burst, pass-through | Temporal risk signal $\in [0.0, 1.0]$ |
| **M7** | [Graph Intelligence](backend/app/engines/graph/intelligence/) | NetworkX / Neo4j topology: cycles, fan-in/out, shared device/IP | Topological risk signal $\in [0.0, 1.0]$ |
| **M8** | [Tabular ML](backend/app/engines/ml/tabular/) | XGBoost classifier on 57 engineered features | Calibrated fraud probability $\in [0.0, 1.0]$ |
| **M9** | [Graph ML](backend/app/engines/ml/graph/) | 2-layer GraphSAGE inductive graph neural network | Structural node fraud probability $\in [0.0, 1.0]$ |
| **M10** | [Risk Fusion](backend/app/engines/risk_fusion/) | Weighted synthesis with dynamic renormalization | Composite risk score $\in [0.0, 100.0]$ + tier |
| **M11** | [Evidence Engine](backend/app/engines/evidence/) | SHA-256 hashing, deduplication, multi-factor ranking | Ranked forensic evidence package |
| **M12** | [Investigation Copilot](backend/app/engines/ai/) | Deterministic template-driven narrative and action generator | Structured dossier (narrative, actions, findings) |
| **M13** | [SOC Integration](backend/app/services/soc_integration_service.py) | Service orchestration + FastAPI REST endpoints | Unified SOC case intelligence payload |

---

## ⚙️ M1–M14 Engineering Implementation

### M1 — Canonical Transaction Layer
- Implements the immutable [`TransactionEvent`](backend/app/domain/models.py) domain entity across UPI, NEFT, IMPS, and RTGS payment channels.
- Provides bidirectional, deterministic conversion via [`TransactionMapper`](backend/app/domain/transaction_mapper.py) to insulate core business logic from legacy data structures.

### M2 — Domain Interfaces / Ports
Pure Python abstract base classes in [`backend/app/domain/interfaces.py`](backend/app/domain/interfaces.py):
- `GraphRepository`: Transaction path tracing, circular path detection, subgraph extraction, entity linking.
- `TransactionRepository`: Transaction event persistence and query interfaces.
- `AlertRepository`: Alert lifecycle state machine (NEW, ESCALATED, RESOLVED, FALSE_POSITIVE).
- `ModelService`: Abstract ML inference port (`predict_risk(event) -> ModelPrediction`).
- `InvestigationCopilot`: Abstract copilot narrative and action synthesis interface.

### M3 — Local NetworkX Graph Adapter
- In-memory directed multigraph adapter ([`graph_nx.py`](backend/app/repositories/graph_nx.py)) implementing `GraphRepository`.
- Enables full graph traversal, cycle detection, and neighbor analysis locally with zero cloud or external database dependency.

### M4 — Graph Adapter Validation
- Exhaustive test suite verifying behavioral parity between the local NetworkX adapter and the production Neo4j Cypher adapter against identical contract suites.

### M5 — 14 Deterministic Fraud Rules
Independent, auditable rule modules located in [`backend/app/engines/rules/`](backend/app/engines/rules/):

| Rule | Name | Target Pattern | Module |
|:---:|:---|:---|:---|
| **R001** | High Velocity | Rapid transaction burst within short time window | [`r001.py`](backend/app/engines/rules/r001.py) |
| **R002** | Fan-In | Multiple disparate senders funneling into one account | [`r002.py`](backend/app/engines/rules/r002.py) |
| **R003** | Fan-Out | Single collector account dispersing funds to many recipients | [`r003.py`](backend/app/engines/rules/r003.py) |
| **R004** | Mule Chain | Sequential pass-through hops with minimal retention | [`r004.py`](backend/app/engines/rules/r004.py) |
| **R005** | Smurfing / Structuring | Repeated amounts structured just below mandatory reporting thresholds | [`r005.py`](backend/app/engines/rules/r005.py) |
| **R006** | Shared Device | Multiple unrelated accounts operating from identical hardware fingerprints | [`r006.py`](backend/app/engines/rules/r006.py) |
| **R007** | Dormant Activation | Abrupt high-volume activity following extended inactivity (>90 days) | [`r007.py`](backend/app/engines/rules/r007.py) |
| **R008** | New Account Abuse | High-velocity turnover on newly opened accounts (<7 days) | [`r008.py`](backend/app/engines/rules/r008.py) |
| **R009** | Cross-Channel Evasion | Rapid switching across UPI → NEFT → IMPS within 1 hour | [`r009.py`](backend/app/engines/rules/r009.py) |
| **R010** | Shared IP | Disparate accounts originating from identical public IP addresses | [`r010.py`](backend/app/engines/rules/r010.py) |
| **R011** | Impossible Travel | Sequential transactions spanning impossible geographic velocity (>500 km/h) | [`r011.py`](backend/app/engines/rules/r011.py) |
| **R012** | Night Activity | Unusual transaction concentration during high-risk night windows (12 AM–5 AM) | [`r012.py`](backend/app/engines/rules/r012.py) |
| **R013** | Shared Beneficiary | Multiple unrelated source accounts adding an identical beneficiary | [`r013.py`](backend/app/engines/rules/r013.py) |
| **R014** | Circular Flow | Topological fund routing that loops back to an originator | [`r014.py`](backend/app/engines/rules/r014.py) |

### M6 — Temporal Intelligence
Implemented in [`backend/app/engines/temporal/`](backend/app/engines/temporal/):
- Aggregates activity across standard sliding windows: **5 minutes**, **15 minutes**, **1 hour**, and **24 hours**.
- Detects transaction bursts ($>3\sigma$ standard deviation from rolling mean).
- Quantifies rapid pass-through ratios ($T_{in} \to T_{out}$ within $<300$ seconds).
- Measures activity change velocity between historical and current operational windows.

### M7 — Graph Intelligence
Implemented in [`backend/app/engines/graph/intelligence/`](backend/app/engines/graph/intelligence/):
- Analyzes heterogeneous relationship graphs connecting accounts, devices, and IP addresses.
- Detects directed circular routing ($A \to B \to \dots \to A$) for cycle lengths 2 to 5.
- Computes degree metrics (in-degree, out-degree, unique counterparty fan-in/fan-out ratios).
- Evaluates structural centrality (PageRank, betweenness centrality, clustering coefficients).

### M8 — Tabular ML + AutoGluon Challenger
Implemented in [`backend/app/engines/ml/tabular/`](backend/app/engines/ml/tabular/):
- **57 engineered features** across 4 canonical groups:
  - 14 Transaction-native features (amount, log-amount, direction, channel flags, day/hour cyclic encoding)
  - 14 Device and risk telemetry features (device trust, IP density, churn, rooted/emulator indicators)
  - 12 Temporal features from M6 (window transaction counts, velocity sums, interval averages, burst flags)
  - 17 Graph topological features from M7 (degrees, unique counterparties, cycle presence, shared device/IP counts)
- **Chronological 70/15/15 split** enforcing strict time-ordered validation with zero data leakage.
- **Primary model:** XGBoost gradient boosting classifier wrapped in scikit-learn pipeline ([`xgboost_adapter.py`](backend/app/engines/ml/tabular/xgboost_adapter.py)).
- **Challenger model:** AutoGluon integration ([`autogluon_adapter.py`](backend/app/engines/ml/tabular/autogluon_adapter.py)) providing automated benchmarking without hard runtime dependency.
- **Architectural invariant:** Zero post-prediction heuristic manipulation of model output probabilities.
- Model artifacts preserved in [`backend/app/engines/ml/artifacts/`](backend/app/engines/ml/artifacts/) with zero startup training.

### M9 — GraphSAGE Graph ML
Implemented in [`backend/app/engines/ml/graph/`](backend/app/engines/ml/graph/):
- Inductive graph neural network using native PyTorch ([`graphsage_model.py`](backend/app/engines/ml/graph/graphsage_model.py)).
- Operates on a heterogeneous relationship graph with a **16-dimensional account feature representation** ([`graph_schema.py`](backend/app/engines/ml/graph/graph_schema.py)).
- **Architecture:** `16 → 32 → 16 → Sigmoid`
  - Layer 1: Mean neighborhood aggregation ($16 \to 32$) + ReLU + Dropout (0.1) + $\ell_2$ normalization.
  - Layer 2: Neighborhood projection ($32 \to 16$) + ReLU + Dropout (0.1) + $\ell_2$ normalization.
  - Classification head: Linear projection ($16 \to 1$) + Sigmoid.
- **Loss function:** Weighted binary cross-entropy with positive-class weighting (`pos_weight = 4.0`) to handle fraud class imbalance.
- **Inference safety:** Safe fallback returning default score (0.50) when trained artifacts are uninitialized; zero startup training.

### M10 — Deterministic Risk Fusion
Composite risk fusion engine ([`backend/app/engines/risk_fusion/`](backend/app/engines/risk_fusion/)) synthesizing all 5 modalities into a normalized continuous score $[0.0, 100.0]$ and discrete risk tiers. See [Multi-Modal Risk Fusion](#-multi-modal-risk-fusion).

### M11 — Deterministic Evidence Engine
Forensic evidence collection, provenance hashing, deduplication, and ranking engine ([`backend/app/engines/evidence/`](backend/app/engines/evidence/)). See [Evidence & Investigation](#-evidence--investigation).

### M12 — Deterministic Investigation Copilot
Deterministic, template-driven investigation narrative and action synthesizer ([`backend/app/engines/ai/`](backend/app/engines/ai/)). Zero LLM dependency. See [Evidence & Investigation](#-evidence--investigation).

### M13 — SOC Integration
Full-service orchestration layer ([`soc_integration_service.py`](backend/app/services/soc_integration_service.py)) and REST API ([`investigations.py`](backend/app/api/v1/investigations.py)) powering the frontend SOC investigation dossier. See [SOC Investigation Workflow](#️-soc-investigation-workflow).

### M14 — BUILD IT Release / Hardening
Production build validation, test suite verification (471 passing tests), TypeScript strict compliance, ESLint verification, and milestone audit reporting ([`docs/reports/`](docs/reports/)).

---

## 🎯 Multi-Modal Risk Fusion

Implemented in [`backend/app/engines/risk_fusion/`](backend/app/engines/risk_fusion/):

The composite risk score $S \in [0.0, 100.0]$ is computed via weighted synthesis of five normalized signals:

$$S = 100.0 \times \sum_{m \in \mathcal{M}} \left(w_m^{\text{eff}} \cdot s_m\right)$$

### Modality Weight Allocation

| Modality | Baseline Weight ($w_m$) | Signal Interpretation | Normalization Method |
|:---|:---:|:---|:---|
| **Rules Engine (M5)** | **25%** | Forensic heuristics & deterministic patterns (R001–R014) | Severity-weighted match floor; Critical=0.90, High=0.70, Med=0.40 |
| **Tabular ML (M8)** | **25%** | 57-feature XGBoost gradient-boosted decision boundary | Clamped calibrated fraud probability $[0.0, 1.0]$ |
| **Graph Intelligence (M7)** | **20%** | Cycles, shared device/IP clusters, counterparty fan ratios | Composite heuristic: $0.40 \cdot \mathbf{1}_{\text{cycle}} + 0.25 \cdot \min(N_{\text{dev}}/3, 1) + \dots$ |
| **Temporal Intelligence (M6)** | **15%** | Multi-window velocity bursts & rapid pass-through | Composite heuristic: $0.40 \cdot r_{\text{in\_out}} + 0.35 \cdot \mathbf{1}_{\text{burst}} + 0.25 \cdot \text{vel}$ |
| **Graph ML / GraphSAGE (M9)** | **15%** | Inductive 2-layer GNN neighborhood representation | Clamped sigmoid output probability $[0.0, 1.0]$ |
| **Total** | **100%** | Strictly validated finite, non-negative, unit sum | Monotonically normalized |

### Operational Risk Tiers

Scores are mapped into operational triage bands ([`thresholds.py`](backend/app/engines/risk_fusion/thresholds.py)):

| Risk Tier | Score Boundary | Operational Protocol |
|:---|:---:|:---|
| 🟢 **LOW** | $0.0 \le S \le 30.0$ | Routine monitoring; standard clearing |
| 🟡 **MEDIUM** | $30.0 < S \le 65.0$ | Enhanced monitoring; secondary verification |
| 🟠 **HIGH** | $65.0 < S \le 85.0$ | Priority alert; analyst review within 4 hours; counterparty hold |
| 🔴 **CRITICAL** | $85.0 < S \le 100.0$ | Immediate escalation; automated debit freeze recommendation; STR filing |

### Missing-Modality Policies

When a detection modality is unavailable (e.g., cold start, missing graph connectivity, or uninitialized ML artifacts):

1. **`RENORMALIZE_AVAILABLE` (Default):** Dynamically rescales the weights of active modalities so their effective sum equals 1.0 ($w_m^{\text{eff}} = w_m / \sum_{a \in \mathcal{A}} w_a$). Rules and graph heuristics maintain full sensitivity even if ML models are offline.
2. **`ZERO_CONTRIBUTION`:** Retains original configured weights; missing modalities contribute 0.0, resulting in score dampening.
3. **`PENALTY_BASELINE`:** Missing modalities contribute an uninformative neutral risk baseline score of 0.20.

### Explainability Attributes

Every fusion output includes:
- Exact continuous composite risk score and categorical risk tier.
- Individual score contributions and applied effective weights per modality.
- **Primary Driver Identification**: Automatically identifies the single modality contributing the largest weighted signal.
- Full missing-modality audit trail and policy log.

---

## 🔎 Evidence & Investigation

### M11 — Deterministic Evidence Engine
Implemented in [`backend/app/engines/evidence/`](backend/app/engines/evidence/):

- **Deterministic SHA-256 Provenance:** Evidence IDs are generated using reproducible SHA-256 digests over source, reference, category, and sorted entity references:
  $$\text{EVD-}\{\text{SOURCE}\}\text{-}\{\text{REF\_SLUG}\}\text{-}\{\text{SHA256}(\dots)[:12]\}$$
- **Deduplication:** Merges identical findings across overlapping modalities, preserving the highest severity tier, union of entity references, and first-occurrence insertion order ([`deduplication.py`](backend/app/engines/evidence/deduplication.py)).
- **Multi-Factor Ranking:** Sorts evidence items deterministically by:
  $$\text{SortKey} = (-\text{SeverityWeight}, -\text{SourcePriority}, -\text{SignalStrength}, \text{EvidenceID})$$
- **Factual Summaries:** Renders objective text summaries derived exclusively from verified transaction metrics ([`renderer.py`](backend/app/engines/evidence/renderer.py)).
- **M10 Score Invariant:** M11 operates as an evidentiary downstream consumer; it never alters, modulates, or recalculates the composite risk score.

### M12 — Deterministic Investigation Copilot
Implemented in [`backend/app/engines/ai/`](backend/app/engines/ai/):

> **CRITICAL ARCHITECTURAL DECISION: ZERO LLM DEPENDENCY**

The investigation copilot is **strictly deterministic and template-driven** ([`copilot.py`](backend/app/engines/ai/copilot.py), [`templates.py`](backend/app/engines/ai/templates.py)). It does **NOT** use Large Language Models, generative AI APIs (OpenAI, Gemini, Bedrock, Claude), or external network calls.

**Why Deterministic?**
- **100% Reproducibility:** Identical transaction inputs and evidence packages always produce identical investigation text.
- **Auditability & Provenance:** Every statement directly cites verified M11 evidence IDs (`EVD-...`); zero hallucinated accounts, amounts, or findings.
- **Regulatory Defensibility:** Investigation narratives satisfy strict compliance audit standards without probabilistic variation.
- **Zero Token Costs & Latency:** Operates entirely in-memory with sub-millisecond execution times and zero cloud API failure modes.

**Synthesized Outputs:**
- **Executive Narrative:** Case-level summary highlighting focal accounts, total volume, and primary risk drivers.
- **Key Forensic Findings:** Structured observations cross-referenced to upstream M11 evidence IDs.
- **Prioritized Recommended Actions:** Tiered next steps (`IMMEDIATE`, `HIGH`, `MEDIUM`, `LOW`), such as temporary account freezing, hardware cluster isolation, or STR filing.
- **Investigator Follow-Up Questions:** Specific interview questions for suspect or victim debriefing.
- **Audit Limitations Disclosure:** Clear documentation of missing modalities or temporal data boundaries.

---

## 🖥️ SOC Investigation Workflow

### M13 — SOC Integration & API Layer

The SOC Integration service ([`soc_integration_service.py`](backend/app/services/soc_integration_service.py)) coordinates the end-to-end intelligence pipeline and exposes case management endpoints through FastAPI ([`investigations.py`](backend/app/api/v1/investigations.py)):

| Method | Endpoint | Description |
|:---:|:---|:---|
| `GET` | `/api/v1/investigations` | Lists active SOC cases with focal accounts, priority, and status |
| `GET` | `/api/v1/investigations/{case_number}` | Case overview metadata (priority, assigned analyst, transaction volume) |
| `PATCH` | `/api/v1/investigations/{case_number}` | Updates case status (`OPEN`, `IN_PROGRESS`, `CLOSED`), priority, or assignment |
| `GET` | `/api/v1/investigations/{case_number}/intelligence` | **Unified Intelligence Dossier:** Executes M5→M12 pipeline for complete case context |
| `POST` | `/api/v1/investigations/enrich` | Ad-hoc multi-modal intelligence synthesis on arbitrary transaction payloads |
| `POST` | `/api/v1/investigations/copilot` | Standalone copilot narrative and action synthesis on custom evidence |

### Frontend Investigation Intelligence Panel

The frontend ([`frontend/src/app/investigations/page.tsx`](frontend/src/app/investigations/page.tsx)) provides an interactive, SOC-ready analyst workbench:

1. **Top Metric Bar:** Composite risk gauge, risk tier badge, evidence item counter, and recommended action count.
2. **5-Modality Contribution Grid:** Visual progress bars displaying raw scores, effective weights, and point contributions for Rules, Tabular ML, Graph Intelligence, Temporal Intelligence, and GraphSAGE.
3. **Copilot Intelligence Workspace:**
   - Executive Narrative with primary driver callout.
   - Key Forensic Findings referencing linked entity badges.
   - Recommended Next Steps categorized by operational urgency.
4. **Forensic Evidence Dossier:** Tamper-evident evidence table displaying SHA-256 evidence IDs, category badges, severity levels, timestamps, and linked entities.

---

## 🛠️ BUILD IT — Cloud-Agnostic Architecture

The BUILD IT environment represents the fully functional, open-source, local development architecture. All core business logic runs with zero external cloud dependencies:

```
┌─────────────────────────────────────────────────────────────────┐
│                    BUILD IT — LOCAL DEVELOPMENT                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Frontend (Next.js 14 / React 18 / TypeScript 5)               │
│       ├── Cytoscape.js + fcose layout (Graph visualization)     │
│       ├── React Leaflet + Leaflet (Geospatial maps)             │
│       ├── Recharts (Analytical distributions & metrics)         │
│       └── Framer Motion + Tailwind CSS (SOC interface)          │
│                                                                 │
│   Backend (FastAPI / Uvicorn / Python 3.11+)                    │
│       ├── Domain Layer (Pure Python ports & canonical models)   │
│       ├── Modular Rule Engine (14 deterministic rules)          │
│       ├── Temporal Engine (Multi-window sliding velocity)       │
│       ├── Graph Intelligence (NetworkX directed multigraph)     │
│       ├── ML Inference (XGBoost tabular + PyTorch GraphSAGE)    │
│       ├── Risk Fusion Engine (Deterministic multi-modal synthesis)│
│       ├── Evidence Engine (SHA-256 provenance & ranking)        │
│       └── Deterministic Copilot (Template-driven narratives)    │
│                                                                 │
│   Persistence Layer                                             │
│       ├── PostgreSQL 16 + SQLAlchemy 2.0 (asyncpg) + Alembic    │
│       └── NetworkX In-Memory Multigraph (Zero cloud dependency) │
│                                                                 │
│   Validation Suite                                              │
│       └── pytest (474 tests, 471 passing, 0 regressions)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ☁️ SHIP IT — AWS Prototype Deployment

The SHIP IT environment deploys the cloud-agnostic application onto Amazon Web Services infrastructure using managed cloud primitives:

```
                      User Browser
                           │
                           ▼
              ┌─────────────────────────┐
              │   AWS Amplify Hosting   │  ← Next.js 14 Frontend
              │   (Global Edge / CDN)   │
              └────────────┬────────────┘
                           │ HTTPS (REST API)
                           ▼
              ┌─────────────────────────┐
              │       Amazon EC2        │  ← FastAPI Application
              │   (Ubuntu / Uvicorn)    │    ML Inference (XGBoost + GraphSAGE)
              │   Persistent EBS Vol.   │    Graph Processing
              └────────────┬────────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
┌─────────────────────────┐ ┌─────────────────────────┐
│ Amazon RDS (PostgreSQL) │ │     Neo4j AuraDB        │
│   Relational Schema     │ │ Managed Cloud Graph DB  │
│   VPC Subnet Isolation  │ │ Cypher Traversal Engine │
└─────────────────────────┘ └─────────────────────────┘
```

### AWS Cloud Infrastructure

| AWS Service | Architecture Function | Operational Role |
|:---|:---|:---|
| **AWS Amplify Hosting** | Frontend Hosting & Edge Delivery | Automated Git-driven builds, global CDN distribution, and SSR hosting for Next.js 14. |
| **Amazon EC2** | Application Compute Layer | Hosts containerized FastAPI service, PyTorch GraphSAGE inference, and API routing. |
| **Amazon EBS** | Persistent Block Storage | High-performance GP3 root and data volumes for EC2 application persistence. |
| **Amazon RDS for PostgreSQL** | Managed Relational Database | Multi-AZ ready PostgreSQL 16 hosting transactions, accounts, alerts, and cases. |
| **Amazon VPC** | Network Boundary Isolation | Isolated public/private subnets separating edge compute from internal databases. |
| **Security Groups** | Stateful Firewall Enforcement | Strict ingress/egress policies (EC2 limited to ports 80/443; RDS restricted to EC2 SG). |
| **AWS IAM** | Identity & Access Management | Least-privilege instance profiles and service execution roles. |

### External Managed Cloud Service

| Cloud Service | Architecture Function | Operational Role |
|:---|:---|:---|
| **Neo4j AuraDB** | Managed Cloud Graph Database | Fully managed cloud graph database executing Cypher queries for large-scale traversal. |

---

## 🧰 Technology Stack

### BUILD IT — Local Development Stack

| Category | Technology | Purpose in Platform |
|:---|:---|:---|
| **Frontend Framework** | Next.js 14 (`14.2.35`) | React framework with App Router, SSR, and API routing |
| **UI Library & Language** | React 18 / TypeScript 5 | Component lifecycle, strict static typing, and state safety |
| **Styling & Layout** | Tailwind CSS 3 / Lucide React | Modern SOC-grade utility-first styling and iconography |
| **Graph Visualization** | Cytoscape.js (`^3.34.0`) + fcose (`^2.2.0`) | Interactive topology canvas, compound spring embedder layout |
| **Geospatial Mapping** | React Leaflet (`^4.2.1`) + Leaflet (`^1.9.4`) | Interactive map rendering, impossible travel arc polylines |
| **Charts & Animation** | Recharts (`^3.10.0`) / Framer Motion (`^12.42.2`) | Alert metrics, volume trends, and smooth panel transitions |
| **State Management** | Zustand (`^5.0.14`) | Lightweight client state for graph and filter parameters |
| **Backend Framework** | FastAPI (`0.115.6`) / Uvicorn (`0.34.0`) | High-performance asynchronous Python REST API server |
| **Data Validation** | Pydantic v2 (`2.10.4`) | Strict request/response payload schemas and runtime validation |
| **Relational Database** | PostgreSQL 16 + SQLAlchemy 2.0 | Transaction and case metadata persistence via asyncpg |
| **Database Migrations** | Alembic (`1.14.1`) | Versioned relational database schema management |
| **In-Memory Graph** | NetworkX | Local graph construction, multigraph traversal, and cycle detection |
| **Tabular ML** | scikit-learn (`1.6.0`) + XGBoost (`2.1.3`) | 57-feature tabular pipeline and gradient boosting classification |
| **Challenger ML** | AutoGluon | Automated model benchmarking and challenger validation |
| **Graph Neural Network** | PyTorch + GraphSAGE | 2-layer inductive graph representation learning |
| **Testing Suite** | pytest (`8.3.4`) + pytest-asyncio (`0.25.0`) | Comprehensive test automation (474 test cases) |

### SHIP IT — AWS Prototype Deployment Stack

| AWS Service / Component | Purpose in Deployment |
|:---|:---|
| **AWS Amplify Hosting** | Next.js 14 frontend deployment, CI/CD pipeline, and edge caching |
| **Amazon EC2** | Application server hosting FastAPI backend and ML inference |
| **Amazon RDS for PostgreSQL** | Managed relational database for transaction and alert persistence |
| **Amazon EBS** | Persistent block storage attached to EC2 instance |
| **AWS IAM** | Role-based least-privilege security policies |
| **Amazon VPC** | Network isolation with dedicated public and private subnets |
| **Security Groups** | Port-level firewall rules restricting database access to EC2 |
| **Neo4j AuraDB** | Managed cloud graph database for distributed topology queries |

---

## 📊 Key Features

### 🔗 Graph Intelligence
- Heterogeneous transaction graph modeling accounts, physical devices, and IP addresses.
- Circular fund routing detection identifying layering cycles of length 2 to 5.
- Centrality metric calculation (PageRank, betweenness centrality, and neighborhood density).
- Interactive Cytoscape.js canvas with `fcose` layout, node pinning, and multi-hop expansion.

### 🤖 Machine Learning
- **Tabular ML:** 57-feature XGBoost classifier trained on strict chronological 70/15/15 split.
- **Graph ML:** 2-layer GraphSAGE inductive neural network operating on 16-D node embeddings.
- **Model Governance:** Zero post-prediction heuristic manipulation; models output pure probabilities.
- **Inference Stability:** Pre-trained model artifacts loaded at startup with safe fallback modes.

### ⏱️ Temporal Intelligence
- Multi-window activity aggregation across 5-minute, 15-minute, 1-hour, and 24-hour windows.
- Transaction velocity burst detection identifying sudden abnormal spikes.
- Rapid pass-through analysis identifying immediate fund forward-routing ($<300$ seconds).

### 📋 Rule-Based Detection
- 14 independently evaluable forensic fraud rules (R001–R014).
- Coverage across velocity, structuring/smurfing, hardware sharing, and dormancy activation.
- Fully configurable thresholds validated for strict monotonicity.

### 🗺️ Geospatial Intelligence
- Interactive Leaflet-powered geospatial analysis across major financial centers.
- Impossible travel vector detection calculating required transit velocity between sequential logins.

### 🔎 SOC Investigation Workbench
- Comprehensive case management lifecycle with real-time priority and status updates.
- Visual 5-modality risk contribution breakdown with effective weight attribution.
- Deterministic, tamper-evident SHA-256 evidence dossiers.
- Template-driven investigation copilot generating actionable executive narratives.

---

## 📁 Project Structure

```
D:\Team_Cipher_Unit/
│
├── README.md                              # Definitive project documentation
├── REPORT.md                              # Engineering source-of-truth and architecture audit
├── REPORT_AWS_PROTOTYPE_READINESS.md      # AWS cloud migration readiness report
├── .env.example                           # Root environment variable template
│
├── backend/                               # FastAPI Application Core
│   ├── requirements.txt                   # Python runtime dependencies
│   ├── pyproject.toml                     # Tool configurations (pytest, black, ruff)
│   ├── alembic.ini                        # Alembic migration configuration
│   ├── app/
│   │   ├── main.py                        # FastAPI application entry point & lifespan
│   │   ├── api/v1/                        # REST API v1 routing endpoints
│   │   │   ├── accounts.py                # Account profile endpoints
│   │   │   ├── alerts.py                  # Alert queue & triage endpoints
│   │   │   ├── analytics.py               # Aggregated analytics endpoints
│   │   │   ├── dashboard.py               # SOC dashboard summary endpoints
│   │   │   ├── geo.py                     # Geospatial risk endpoints
│   │   │   ├── graph.py                   # Graph query & traversal endpoints
│   │   │   ├── health.py                  # System health check endpoints
│   │   │   ├── investigations.py          # M13: SOC investigation & intelligence endpoints
│   │   │   ├── reports.py                 # SAR / compliance report endpoints
│   │   │   └── transactions.py            # Transaction query & scoring endpoints
│   │   ├── domain/                        # M1–M2: Pure domain layer (ports & canonical models)
│   │   │   ├── interfaces.py             # Abstract ports (GraphRepository, ModelService, etc.)
│   │   │   ├── models.py                 # Canonical TransactionEvent and domain entities
│   │   │   └── transaction_mapper.py     # Deterministic bidirectional mapper
│   │   ├── engines/                       # Intelligence detection engines
│   │   │   ├── rules/                    # M5: 14 modular fraud pattern rules (r001–r014)
│   │   │   ├── temporal/                 # M6: Multi-window temporal intelligence engine
│   │   │   ├── graph/                    # M7: Topological graph intelligence engine
│   │   │   │   └── intelligence/         # Graph metrics, models, and traversal engine
│   │   │   ├── ml/                       # M8–M9: Machine learning inference engines
│   │   │   │   ├── tabular/             # XGBoost & AutoGluon model adapters (57 features)
│   │   │   │   ├── graph/               # GraphSAGE PyTorch model & adapter (16-D features)
│   │   │   │   └── artifacts/           # Serialized pre-trained model artifacts
│   │   │   ├── risk_fusion/              # M10: Multi-modal risk fusion engine
│   │   │   ├── evidence/                 # M11: SHA-256 evidence engine & ranking
│   │   │   └── ai/                       # M12: Deterministic investigation copilot
│   │   ├── repositories/                  # Infrastructure adapters
│   │   │   ├── graph_nx.py               # M3: NetworkX local in-memory graph adapter
│   │   │   └── graph_neo4j.py            # Neo4j Cypher cloud graph adapter
│   │   ├── services/                      # Application service orchestration
│   │   │   └── soc_integration_service.py # M13: Case intelligence orchestration service
│   │   ├── models/                        # SQLAlchemy relational models
│   │   ├── schemas/                       # Pydantic validation schemas
│   │   ├── database/                      # PostgreSQL and Neo4j session managers
│   │   ├── middleware/                    # CORS, structured logging, request ID tracking
│   │   └── config/                        # Application settings and constant definitions
│   └── tests/                             # Pytest automated test suite (70 test files)
│
├── frontend/                              # Next.js 14 App Router Frontend
│   ├── package.json                       # Dependencies (Next 14, React 18, Cytoscape, Leaflet)
│   ├── next.config.mjs                    # Next.js build configuration
│   ├── tsconfig.json                      # Strict TypeScript compiler options
│   ├── tailwind.config.ts                 # Tailwind styling tokens
│   └── src/
│       ├── app/                           # App Router page routes
│       │   ├── page.tsx                   # Landing redirect to /dashboard
│       │   ├── dashboard/page.tsx         # SOC Overview KPI Dashboard
│       │   ├── transactions/page.tsx      # Transaction Ledger & Risk Explorer
│       │   ├── graph/page.tsx             # Interactive Cytoscape.js Graph Canvas
│       │   ├── geo/page.tsx               # Geospatial Leaflet Impossible Travel Map
│       │   ├── alerts/page.tsx            # Alert Triage Queue & Actions
│       │   ├── investigations/page.tsx    # SOC Investigation Dossier & Copilot Panel
│       │   └── reports/page.tsx           # Regulatory SAR / Compliance Reports
│       ├── components/                    # Reusable UI components (AppShell, Header, Sidebar)
│       ├── hooks/                         # Custom data-fetching hooks
│       └── lib/                           # API client, state stores, and type definitions
│
├── ml/                                    # Standalone Training Pipelines
│   ├── train_models.py                   # Baseline training pipeline
│   ├── transaction_fraud_detection.py    # XGBoost and Random Forest training script
│   └── transactions.csv                  # Reference training dataset
│
├── docs/                                  # Architectural Documentation & Reports
│   ├── architecture/                     # Detailed architectural specifications
│   ├── reports/                          # Milestone audit reports (M1–M14)
│   └── images/                           # System banners and architecture diagrams
│
└── scripts/                               # Maintenance and seed scripts
```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Minimum Version | Reference |
|:---|:---:|:---|
| **Python** | 3.11+ | [python.org](https://python.org) |
| **Node.js** | 18.x+ | [nodejs.org](https://nodejs.org) |
| **PostgreSQL** | 16.x | [postgresql.org](https://postgresql.org) |
| **Git** | 2.40+ | [git-scm.com](https://git-scm.com) |

### 1. Repository Setup

```bash
git clone https://github.com/Sph1333y/mule_tracker.git
cd mule_tracker

# Copy environment template
cp .env.example .env
# Configure your PostgreSQL connection strings in .env
```

### 2. Backend Setup (FastAPI)

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# Install backend dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
# API:         http://localhost:8000
# Swagger UI:  http://localhost:8000/docs
```

### 3. Frontend Setup (Next.js 14)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Dashboard:   http://localhost:3000
```

### 4. Run Automated Tests

```bash
cd backend
pytest -v
```

---

## 🧪 Validation

### Backend Test Suite (pytest)

The backend test suite verifies domain invariants, engine isolation, deterministic reproducibility, and adapter contracts:

| Verification Metric | Result | Engineering Status |
|:---|:---:|:---|
| **Total Automated Tests** | **474** | Complete test suite execution |
| **Passed Tests** | **471** | All core domain, engine, and adapter tests pass |
| **Skipped Tests** | **1** | Optional AutoGluon dependency verification |
| **Pre-Existing Baseline Failures** | **2** | Documented baseline items (preserved without regression) |
| **Regressions Introduced** | **0** | Zero regressions across M1–M14 implementation |

#### Breakdown by Architectural Milestone

| Milestone | Subsystem Tested | Passing Tests |
|:---|:---|:---:|
| **M1 / M2** | Canonical Domain Layer & Repository Interfaces | 21 |
| **M5** | 14 Modular Deterministic Fraud Rules | 35 |
| **M6** | Multi-Window Temporal Intelligence Engine | 30 |
| **M7** | Graph Intelligence & Topological Cycle Traversal | 42 |
| **M8** | Tabular ML XGBoost Adapter (57 Features) | 33 |
| **M9** | GraphSAGE GNN PyTorch Implementation (16-D Features) | 31 |
| **M10** | Multi-Modal Risk Fusion & Invariant Verification | 45 |
| **M11** | Tamper-Evident Evidence Engine & Deduplication | 44 |
| **M12** | Deterministic Investigation Copilot Templates | 43 |
| **M13** | SOC Integration Service & API Payloads | 11 |
| **M14** | Automated Release Hardening & E2E Verification | 2 |
| **Core** | Repositories, Adapters, and Middleware | 134 |

> **Transparency Note:** The two documented baseline failures (`test_postgres_dsn_computation` and `test_get_dashboard_overview`) represent pre-existing environment-specific configuration items that have been tracked since early development milestones. In accordance with strict release engineering protocols, these baseline items were preserved without masking or regressive alterations.

### Frontend Validation

| Verification Check | Standard | Result |
|:---|:---|:---:|
| **TypeScript Compilation** | `tsc --noEmit` (strict mode) | ✅ Zero errors |
| **ESLint Static Analysis** | Next.js core Web Vitals & ESLint rules | ✅ Passed |
| **Production Build** | `next build` (clean standalone build) | ✅ Successful |

---

## 🔐 Security & Deployment Notes

- **Secret Isolation:** All database credentials, secrets, and API endpoints are managed strictly through `.env` configuration; zero hardcoded secrets exist in source code.
- **Authentication & Authorization:** JWT-based stateless authentication with role-based access control (RBAC) separating viewer, investigator, and administrator personas.
- **Network Isolation:** In AWS deployment, backend compute (EC2) and database storage (RDS) reside within dedicated VPC private subnets; external ingress is limited strictly to HTTP/HTTPS.
- **Least Privilege (IAM):** AWS EC2 instances utilize IAM instance roles with scoped policies; root account credentials are never deployed.
- **Audit Logging:** Structured JSON logging across all backend endpoints with automated request ID tracking for complete forensic auditability.

---

## ⚠️ Current Limitations

- **Prototype Scope:** MuleTrace AI is currently implemented as an engineering prototype for hackathon demonstration and technical validation; it is not yet certified for statutory banking production operations.
- **Batch / Request-Driven Ingestion:** Ingestion operates via HTTP REST endpoints and batch pipelines; real-time event streaming via distributed commit logs (e.g., Apache Kafka) is planned for future phases.
- **Synthetic Evaluation Data:** Machine learning and graph neural network models were evaluated on simulated and anonymized financial transaction datasets rather than live proprietary banking core feeds.
- **Non-Regulatory Thresholds:** Risk tier thresholds (30, 65, 85) represent operational heuristics for analyst triage rather than statutory regulatory parameters.

---

## 🔮 Future Production Evolution

| Roadmap Phase | Target Capability | Architectural Description |
|:---|:---|:---|
| **Phase 2** | Real-Time Event Streaming | Apache Kafka / AWS MSK integration for microsecond transaction event processing. |
| **Phase 3** | Cross-Bank Federation | Privacy-preserving federated analytics across multiple financial institutions. |
| **Phase 4** | Advanced Graph Attention | Graph Attention Networks (GAT) with edge features for richer structural embeddings. |
| **Phase 5** | Regulatory API Adapters | Automated secure connectors to RBI Central Payments Fraud Information Registry (CPFIR). |
| **Phase 6** | Field Investigator Mobile App | React Native companion application for field agent verification and document intake. |

---

## 👥 Team Cipher Unit

Team Cipher Unit is a cross-functional engineering team combining cloud infrastructure, security, backend systems, machine learning, graph intelligence, data pipelines, and product design to build MuleTrace AI end to end.

### Engineering Contribution Matrix

| Member | Professional Role | Primary Ownership | Project Contribution |
|:---|:---|:---|:---|
| **Sakthi Prakash S** | **Team Lead**<br/>• DevOps<br/>• Cloud Security Engineer<br/>• Machine Learning Engineer | Deployment Architecture & Cloud Security | Spearheaded overall technical leadership, AWS deployment architecture (Amplify, EC2, RDS, VPC), infrastructure reliability, cloud security posture, and machine learning engineering contributions including model training pipelines and containerized integration. |
| **Sanjay B** | • Frontend Engineer<br/>• Graph Development Engineer<br/>• Machine Learning Engineer | SOC Frontend & Graph Visualization | Led the development of the Next.js 14 SOC investigation workbench, interactive Cytoscape.js graph canvas with `fcose` layout algorithms, geospatial Leaflet integration, and graph ML integration (GraphSAGE inference and feature mapping). |
| **Athishwar K** | • Backend Engineer<br/>• Pipeline Architect | Core Backend & Intelligence Orchestration | Designed and implemented the FastAPI core services, hexagonal ports-and-adapters architecture, database repositories, RESTful API endpoints, and end-to-end intelligence pipeline orchestration (M1–M13 synthesis). |
| **Karmugilan R** | • Pipeline Architect<br/>• UI/UX Designer | Pipeline Architecture & Product Experience | Guided end-to-end data pipeline architecture, dataflow specifications across detection modalities, and user experience design for the SOC analyst alert triage, investigation dossier, and compliance workflows. |

### Architecture & Capability Mapping

The technical execution of MuleTrace AI maps directly across team engineering capabilities:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     TEAM CAPABILITY & ARCHITECTURE MAPPING                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Cloud Infrastructure & Security       →  Sakthi Prakash S                  │
│  (AWS Amplify, EC2, RDS, VPC, IAM)                                          │
│                                                                             │
│  SOC Frontend & Graph Visualization     →  Sanjay B                          │
│  (Next.js 14, Cytoscape.js, Leaflet)                                        │
│                                                                             │
│  Backend Core & REST Services           →  Athishwar K                       │
│  (FastAPI, Domain Ports, Repositories)                                      │
│                                                                             │
│  Pipeline Architecture & Product UX     →  Karmugilan R                      │
│  (Dataflow Design, SOC Analyst UX)                                          │
│                                                                             │
│  Machine Learning & Graph Analytics     →  Sakthi Prakash S & Sanjay B       │
│  (XGBoost, GraphSAGE GNN, PyTorch)                                          │
│                                                                             │
│  Domain Logic & Intelligence Engines    →  Athishwar K & Karmugilan R        │
│  (Rules Engine, Temporal, Risk Fusion)                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **Cross-Functional Collaboration:** Technical ownership across Team Cipher Unit is deeply collaborative. All team members actively participated in cross-cutting architecture discussions, peer code reviews, integration testing, and documentation hardening across all 14 project milestones.

---

## 🙏 Acknowledgements

- **Reserve Bank of India (RBI)** — For published AML/CFT guidelines and regulatory compliance frameworks.
- **Financial Intelligence Unit - India (FIU-IND)** — For Suspicious Transaction Report (STR) standards.
- **Indian Cyber Crime Coordination Centre (I4C)** — For cybercrime investigation taxonomies and mule ring operational patterns.
- **National Payments Corporation of India (NPCI)** — For documentation on retail payment architectures (UPI, IMPS).
- **Neo4j** — For graph database engine and graph data science reference algorithms.
- **FastAPI & Next.js Communities** — For high-performance open-source frameworks powering our backend and frontend tiers.
- **PyTorch & Geometric Deep Learning Researchers** — For foundational GraphSAGE research enabling inductive representation learning on financial graphs.

---

<p align="center">
  <strong>MuleTrace AI</strong> — Defending India's Financial Ecosystem with Multi-Modal Intelligence
</p>

<p align="center">
  Built with technical rigor by <strong>Team Cipher Unit</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20in-India-orange?style=for-the-badge&logo=flag-india" alt="Made in India" />
</p>
