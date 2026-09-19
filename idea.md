# MuleTrace AI — Enterprise Architectural Blueprint & System Specification
**Document Version:** 1.0.0  
**Role / Author:** Senior Engineering Manager & Lead Architect  
**Classification:** Proprietary / Financial Crime Intelligence Platform  
**Target Audience:** Engineering Leadership, Regulatory Auditors (RBI/FIU-IND), AML Officers, Core Dev Team  

---

## Executive Summary

**MuleTrace AI** is an enterprise-grade, real-time financial crime intelligence and cross-channel mule account detection platform designed specifically for the high-velocity Indian banking ecosystem (UPI, IMPS, NEFT, RTGS). 

India processes over 13+ billion digital payment transactions every month. Cybercrime syndicates systematically exploit this volume through sophisticated layering tactics—rapidly routing illicit funds through 5 to 15 intermediary "mule" bank accounts within minutes before cashing out via ATMs or crypto ramps. Traditional AML/CFT rule engines generate over 95% false positives and fail to detect distributed, cross-bank collusion.

MuleTrace AI bridges this systemic vulnerability by fusing **Graph Data Science (Neo4j)**, **Machine Learning (RandomForest / XGBoost / Isolation Forest)**, **Deterministic Rule Engines (14 Forensic Patterns)**, **Geospatial Velocity Intelligence**, **Explainable AI (SHAP + LLM Copilot)**, and **Privacy-Preserving Federated Learning** into a single cohesive Security Operations Center (SOC) investigation platform.

---

## 1. System Architecture & Topology

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    MULETRACE AI SYSTEM TOPOLOGY                                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│   ┌──────────────────────────────────┐             ┌─────────────────────────────────────────┐   │
│   │       CLIENT / PUBLIC LAYER      │             │         ANALYST / SOC ADMIN PORTAL      │   │
│   │  • Victim Fraud Intake Portal    │             │  • Next.js 14 App Router (Port 3000)    │   │
│   │  • Transaction Dispute Web App   │             │  • Cytoscape / Recharts / Leaflet Map   │   │
│   └────────────────┬─────────────────┘             └────────────────────▲────────────────────┘   │
│                    │                                                    │                        │
│                    │ HTTPS REST (JSON)                                  │ Next.js API / Client   │
│                    ▼                                                    ▼                        │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                          FASTAPI APPLICATION LAYER (Port 8000)                           │   │
│   │  • Lifespan & Middleware: CORS, RequestID, Structured JSON Logging, Global Error Handler │   │
│   │  • API v1 Master Router: /dashboard, /accounts, /transactions, /alerts, /graph, /geo,   │   │
│   │                          /investigations, /reports, /complaints, /federated             │   │
│   └──────┬───────────────────────┬──────────────────────────┬────────────────────────┬───────┘   │
│          │                       │                          │                        │           │
│          ▼                       ▼                          ▼                        ▼           │
│   ┌──────────────┐        ┌──────────────┐           ┌──────────────┐         ┌──────────────┐   │
│   │ RULE ENGINE  │        │ GRAPH ENGINE │           │  ML ENGINE   │         │ GEO / TRAVEL │   │
│   │ • 14 Patterns│        │ • Neo4j GDS  │           │ • RF / XGB   │         │ • Velocity   │   │
│   │ • Velocity   │        │ • PageRank   │           │ • IsolationF │         │ • GreatCircle│   │
│   │ • Smurfing   │        │ • Louvain    │           │ • SHAP XAI   │         │ • Density    │   │
│   └──────┬───────┘        └──────┬───────┘           └──────┬───────┘         └──────┬───────┘   │
│          │                       │                          │                        │           │
│          └───────────────────────┼──────────────────────────┴────────────────────────┘           │
│                                  ▼                                                               │
│                   ┌─────────────────────────────┐                                                │
│                   │      MULTI-SIGNAL FUSION    │                                                │
│                   │  Normalized Risk Score 0-100│                                                │
│                   └──────────────┬──────────────┘                                                │
│                                  │                                                               │
│         ┌────────────────────────┴────────────────────────┐                                      │
│         ▼                                                 ▼                                      │
│  ┌───────────────────────────────────┐     ┌───────────────────────────────────┐                 │
│  │    RELATIONAL PERSISTENCE LAYER   │     │      GRAPH DATABASE LAYER         │                 │
│  │  • PostgreSQL 16 (Supabase/Render)│     │  • Neo4j 5.x Graph Database       │                 │
│  │  • SQLAlchemy 2.0 Async / asyncpg │     │  • Cypher Graph Engine            │                 │
│  │  • Alembic Schema Migrations      │     │  • Account Nodes & Txn Edges      │                 │
│  └───────────────────────────────────┘     └───────────────────────────────────┘                 │
│                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                    CROSS-BANK FEDERATED LEARNING SUBSYSTEM (Phase 1)                     │   │
│  │  • Central Coordinator (FedAvg)           • Local Bank Trainer (PyTorch/Sklearn)          │   │
│  │  • (ε, δ) Differential Privacy Engine     • Secure Cryptographic Weight Aggregation       │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Complete Technology Stack & Tooling

### 2.1 Frontend Engineering
* **Framework:** Next.js 14.2.35 (React 18, React DOM 18) utilizing App Router (`src/app/`).
* **Language & Type System:** TypeScript 5.x.
* **Styling & UI Architecture:** Tailwind CSS 3.4.1, PostCSS, Custom Obsidian Dark SOC Glassmorphism theme, `clsx`, `tailwind-merge`.
* **Icons & Visual Language:** `lucide-react` (1.26.0).
* **Graph Visualization Engine:**
  * `cytoscape` (3.34.0) with `cytoscape-fcose` (Fast Compound Spring Embedder physics layout) for multi-hop graph clusters.
  * `@xyflow/react` (12.11.2) / `react-force-graph-2d` (1.29.1) for forensic node-link diagram rendering.
* **Charts & Analytics:** `recharts` (3.10.0) for velocity spikes, risk distribution donuts, and channel volume bar charts.
* **Geospatial Mapping:** `leaflet` (1.9.4) and `react-leaflet` (4.2.1) using Carto Dark Basemaps for fraud heatmaps and impossible travel flightpaths.
* **Micro-interactions & State:** `framer-motion` (12.42.2) for smooth drawer transitions, `zustand` (5.0.14) for global graph filters (hop counts, risk slider, bank toggles).
* **Forensic Document Export:** `jspdf` (4.2.1) for client-side generation of Suspicious Transaction Reports (STR/CTR).

### 2.2 Backend Engineering
* **Framework:** FastAPI 0.115.6 with `uvicorn[standard]` (0.34.0) ASGI server.
* **Runtime & Type Annotations:** Python 3.11+ with future annotations, Pydantic v2.10.4, Pydantic Settings 2.7.1 for strict environment configuration.
* **Relational Database & ORM:** SQLAlchemy 2.0.36 (`asyncio` mode), `asyncpg` 0.30.0 for async database pooling, `psycopg2-binary` 2.9.12 for synchronous Alembic migrations.
* **Database Migrations:** Alembic 1.14.1 for versioned schema management.
* **Graph Engine Client:** `neo4j` 5.27.0 Python driver for asynchronous Cypher execution.
* **Quality Assurance & Testing:** `pytest` 8.3.4, `pytest-asyncio` 0.25.0, `httpx` 0.28.1, `black`, `ruff`, `isort`.

### 2.3 Machine Learning, AI & Data Science
* **Tabular Models:** `scikit-learn` 1.6.0 (RandomForestRegressor, RandomForestClassifier, IsolationForest, OneHotEncoder, StandardScaler, ColumnTransformer).
* **Gradient Boosting:** `xgboost` 2.1.3 for non-linear mule pattern classification.
* **Model Serialization:** `joblib` 1.4.2 storing compiled pipelines (`rf_regressor_pipeline.pkl`, `rf_classifier_pipeline.pkl`, `freq_encodings.pkl`).
* **Data Wrangling:** `pandas` 2.2.3, `numpy` 1.26+.
* **Explainable AI (XAI):** `SHAP` for Shapley value computation + LLM Investigation Narrative Copilot (`app/engines/ai/copilot.py`).
* **Federated Learning:** Custom FedAvg Coordinator with Laplace differential privacy noise injection ($(\epsilon, \delta)$-DP).

---

## 3. Dataset Architecture & Feature Engineering

### 3.1 Primary Forensic Dataset (`data_set/transactions_data_set.csv`)
The core forensic training and simulation dataset consists of rich multi-bank transaction logs with 34 forensic columns:

| Field Name | Data Type | Forensic Description & Purpose |
|:---|:---|:---|
| `timestamp` | `datetime` | Exact ISO transaction timestamp for velocity and night-time analysis |
| `txn_id` | `string` | Unique bank transaction reference / UTR number |
| `name` / `receiver_name` | `string` | Remitter and beneficiary KYC names |
| `account_number` / `receiver_account` | `string` | Remitter and beneficiary account identifiers |
| `bank_name` / `receiver_bank` | `string` | Originating and target institutions (SBI, HDFC, ICICI, Axis, YES Bank, PNB) |
| `trans_type` / `narration` | `string` | Payment rail (`UPI`, `NEFT`, `IMPS`, `RTGS`) and transfer intent |
| `amount` | `float` | Monetary value in INR |
| `ip_address` | `string` | Source IP address for proxy, VPN, and CIDR clustering |
| `device` | `string` | Device model and operating system fingerprint |
| `is_fraud` / `fraud_type` | `int` / `string` | Ground truth target (0: Normal, 1: Mule Chain, Smurfing, Fan-In, etc.) |
| `account_age_days` | `int` | Days since KYC account creation (new account abuse detection) |
| `velocity_l6h` | `int` | Transaction count recorded in the trailing 6 hours |
| `churn_rate` | `float` | Inflow vs. outflow turnover velocity |
| `ip_account_density` | `int` | Total number of distinct accounts accessing the system from this IP |
| `amount_deviation_ratio` | `float` | Deviation multiplier compared to remitter's historical 90-day baseline |
| `daily_limit_fraction` | `float` | Proportion of RBI regulatory daily transaction limit consumed |
| `user_risk_score` | `float` | Historical behavioral risk baseline of the remitter (0-100) |
| `device_trust_score` | `float` | Hardware integrity score (0-100) |
| `is_rooted_or_emulator` | `int (0/1)` | Binary flag for modified OS, jailbreaks, or virtual emulator execution |
| `device_risk_score` | `float` | Aggregate device risk score |
| `is_vpn_or_proxy` | `int (0/1)` | Anonymization network detection flag |
| `network_risk_score` | `float` | Telecom / ISP risk coefficient |
| `risk_score` | `float` | Ground truth synthetic risk index |

---

## 4. Detection Engines & Analytical Methodology

```
                   ┌────────────────────────────────────────┐
                   │    INCOMING TRANSACTION DATA FEED      │
                   └───────────────────┬────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
 ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
 │     RULE ENGINE     │    │    GRAPH ENGINE     │    │      ML ENGINE      │
 │   (Deterministic)   │    │  (Network Topology) │    │  (Stat/Probabilistic)│
 ├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
 │ • 14 Fraud Rules    │    │ • Neo4j GDS Graph   │    │ • Isolation Forest  │
 │ • Velocity Spikes   │    │ • Louvain Clustering│    │ • RF/XGB Regressor  │
 │ • Smurfing (<₹50K)  │    │ • PageRank Hops     │    │ • RF/XGB Classifier │
 │ • Pass-Through Rate │    │ • Cycle Tracing     │    │ • Feature Scaling   │
 └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       ▼
                        ┌─────────────────────────────┐
                        │      RISK SCORE FUSION      │
                        │    Multi-Signal Weighting   │
                        │    Final Risk: 0 — 100      │
                        └──────────────┬──────────────┘
                                       ▼
                        ┌─────────────────────────────┐
                        │    EXPLAINABLE AI (XAI)     │
                        │  • SHAP Top 5 Contributors  │
                        │  • Copilot Narrative Gen    │
                        └─────────────────────────────┘
```

### 4.1 The 14 Forensic Rule Patterns (`app/engines/rules/rule_engine.py`)
1. **R001 — High Velocity:** $>20$ transactions originating from a single account within a 60-minute window.
2. **R002 — Fan-In (Collector Account):** $>10$ distinct remitters depositing funds into a single account within 24 hours.
3. **R003 — Fan-Out (Distributor Account):** A single remitter dispersing funds to $>10$ distinct beneficiary accounts within 24 hours.
4. **R004 — Mule Chain Rapid Pass-Through:** $>90\%$ of received funds transferred out to a subsequent node within 15 minutes.
5. **R005 — Smurfing / Structuring:** Repeated transactions clustered between ₹48,000 and ₹49,999 to evade the mandatory ₹50,000 PAN/CTR reporting threshold.
6. **R006 — Dormant Account Activation:** Sudden high-velocity activity on an account with zero transactions over the preceding 90 days.
7. **R007 — New Account Abuse:** Unusually high transaction frequency ($>15$ txns) on accounts created $<7$ days ago.
8. **R008 — Cross-Channel Hopping:** Rapid cycling across payment rails (UPI $\rightarrow$ NEFT $\rightarrow$ IMPS $\rightarrow$ RTGS) within 1 hour.
9. **R009 — Shared Device Fingerprint:** $>3$ distinct customer bank accounts operated from the exact same IMEI/Device ID.
10. **R010 — Shared IP Address Clustering:** $>5$ unrelated accounts transacting from the same non-institutional public IP.
11. **R011 — Impossible Travel Velocity:** Successive transactions from distinct cities with implied physical transit speeds exceeding $500\text{ km/h}$.
12. **R012 — Night Activity Anomalies:** $>60\%$ of high-value transactions occurring between 12:00 AM and 05:00 AM.
13. **R013 — Shared Beneficiary Convergence:** $>5$ unrelated accounts adding and transferring to the identical newly registered beneficiary.
14. **R014 — Circular Flow / Wash Laundering:** Directed cycles where funds traverse intermediate accounts and return to the originator.

### 4.2 Graph Intelligence Engine (`app/engines/graph/`)
* **Cypher Construction:** Accounts are mapped as `(:Account)` nodes and transactions as `[:TRANSFERRED_FUNDS]` directed edges storing amounts, channels, and timestamps.
* **Louvain Community Detection:** Identifies densely connected clusters of accounts acting as coordinated syndicates across disparate banks.
* **PageRank & Centrality:** Computes node influence to isolate syndicate controllers (high PageRank) vs. expendable mules (high betweenness, low retention).
* **Path Tracing (`/api/v1/graph/trace/{txRef}`):** Computes all downstream flow paths from the victim's initial debited transaction to the cash-out sink node.

### 4.3 Machine Learning Pipeline (`app/engines/ml/`)
* **Task 1 — Risk Score Regression:** Predicts continuous risk score ($0.0 - 100.0$) via tuned RandomForestRegressor and XGBoost models.
* **Task 2 — Binary Fraud Classification:** Computes fraud probability ($P(\text{mule})$) using balanced class weights to address rare-event skew.
* **Anomaly Detection:** Scikit-learn `IsolationForest` identifies multi-dimensional outliers in feature space without labeled supervision.

---

## 5. API Reference & Communication Protocols

All endpoints are hosted under the `/api/v1` namespace with structured Pydantic response wrappers (`BaseResponse[T]` and `PaginatedResponse[T]`):

```
┌───────────────────┬──────────────────────────────────────────┬────────────────────────────────────────────────────────┐
│ Module            │ Endpoint                                 │ Description & Payload                                  │
├───────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ Health            │ GET /api/v1/health                       │ System readiness, PostgreSQL & Neo4j ping check        │
│ Dashboard         │ GET /api/v1/dashboard                    │ SOC KPIs, active alerts count, 24h risk distribution   │
│ Accounts          │ GET /api/v1/accounts                     │ Paginated accounts, filter by risk level & mule flag   │
│                   │ GET /api/v1/accounts/{account_number}    │ Detailed account profile, risk trajectory & links      │
│ Transactions      │ GET /api/v1/transactions                 │ Paginated transactions, filter by rail, amount, status │
│                   │ POST /api/v1/transactions                │ Real-time transaction ingestion & tri-engine evaluation│
│ Alerts            │ GET /api/v1/alerts                       │ Alert queue with severity filtering                    │
│                   │ PATCH /api/v1/alerts/{id}/triage         │ Update status (ACKNOWLEDGED, ESCALATED, RESOLVED)      │
│ Analytics         │ GET /api/v1/analytics                    │ Macro statistics, fraud typology distribution, volume  │
│ Graph             │ GET /api/v1/graph                        │ Global transaction topology for Cytoscape renderer     │
│                   │ GET /api/v1/graph/trace/{txRef}          │ Multi-hop path tracing from origin transaction         │
│ Geo               │ GET /api/v1/geo                          │ City clusters, state density, impossible travel alerts │
│ Investigations    │ GET /api/v1/investigations               │ Active cases (`CAS-YYYY-XXXX`), evidence dockets       │
│                   │ GET /api/v1/investigations/{case_number} │ Deep case view, linked accounts, activity timeline     │
│                   │ PATCH /api/v1/investigations/{case_num}  │ Update priority, investigator assignment, case status  │
│ Reports           │ GET /api/v1/reports                      │ Suspicious Transaction Reports & Cybercrime summaries  │
│                   │ POST /api/v1/reports                     │ Generate FIU-IND compliant STR/CTR report              │
│ Victim Intake     │ POST /api/v1/complaints/public/submit    │ Public intake API bridging victim portal to Admin view │
│                   │ GET /api/v1/complaints/public/status/{id}│ Public tracking of victim complaint resolution status  │
│ Federated Learn   │ POST /api/v1/federated/banks/register    │ Register bank node, issue authentication token         │
│                   │ POST /api/v1/federated/rounds/initiate   │ Central trigger for distributed training round         │
│                   │ POST /api/v1/federated/models/weights    │ Bank upload of encrypted/DP-noised model gradients     │
│                   │ GET /api/v1/federated/models/global      │ Fetch aggregated global model weights                  │
└───────────────────┴──────────────────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 6. End-to-End Operational Workflow (Session by Session)

### Session 1: Public Intake & Citizen Complaint Ingestion
1. A citizen victimized by cyber fraud (e.g., Digital Arrest, Phishing, Fake Job Scam) submits a dispute via the external User Portal.
2. The User Portal makes a single `POST` request to `/api/v1/complaints/public/submit` with transaction UTR, victim details, loss amount, and narrative.
3. The backend validates the request, generates an immutable tracking identifier (`CMP-YYYY-XXXXX`), and stores the record in PostgreSQL with `report_type = "VICTIM_COMPLAINT"`.
4. The complaint immediately surfaces in the Admin Platform's Reports & Investigations queue without requiring manual batch transfers.

### Session 2: Real-Time Stream Ingestion & Multi-Engine Evaluation
1. Live CBS / Switch transaction feeds (UPI, NEFT, IMPS, RTGS) are ingested via `POST /api/v1/transactions`.
2. The transaction is simultaneously broadcast to three parallel detection engines:
   * **Rule Engine:** Evaluates velocity, smurfing limits, dormant activation, and channel switching.
   * **ML Engine:** Computes non-linear risk score and anomaly probabilities via RandomForest/XGBoost.
   * **Graph Engine:** Merges `(:Account)` nodes and writes the directed `[:TRANSFERRED_FUNDS]` edge in Neo4j.

### Session 3: Multi-Signal Risk Score Fusion
1. The signals are normalized into a unified $0 - 100$ scale:
   $$\text{Final Risk} = w_r \cdot \text{RuleScore} + w_m \cdot \text{MLScore} + w_g \cdot \text{GraphScore} + w_a \cdot \text{AnomalyScore}$$
2. Risk levels are dynamically categorized:
   * **$0 - 39$:** `LOW` (Normal operations)
   * **$40 - 69$:** `MEDIUM` (Flagged for automated monitoring)
   * **$70 - 84$:** `HIGH` (Queued for analyst review)
   * **$85 - 100$:** `CRITICAL` (Immediate account freeze & alert escalation)

### Session 4: SOC Dashboard & Real-Time Alert Triage
1. SOC Tier-1 analysts monitor the Dashboard overview (`/dashboard`), observing KPI cards, real-time alert streams, and regional distribution charts.
2. High-priority alerts are opened in the Alert Triage drawer (`/alerts`), displaying the top 5 SHAP contributing factors and the LLM-generated narrative.
3. The analyst can update status to `IN_PROGRESS`, `ESCALATED`, or `RESOLVED`, recording notes and linking them to active investigation dockets.

### Session 5: Interactive Visual Graph Forensics
1. Navigating to the Graph Intelligence explorer (`/graph`), investigators view the live topology rendered via Cytoscape with fcose physics.
2. Analysts apply multi-attribute filters (hop count, risk score range, bank institution, minimum transferred amount).
3. Clicking a flagged node displays connected counter-parties, shared IP/device clusters, and runs real-time shortest path tracing to identify the cash-out sink node.

### Session 6: Geo Intelligence & Impossible Travel Detection
1. The Geospatial module (`/geo`) renders a high-contrast Carto Dark map of India showing regional fraud densities.
2. The system flags impossible travel arcs between geographically distant cities (e.g., ATM withdrawal in Mumbai followed by UPI transfer from Delhi 15 minutes later).

### Session 7: Case Management & Regulatory Reporting (STR / CTR)
1. Flagged accounts and suspicious transaction clusters are compiled into an official investigation case (`/investigations`).
2. Analysts click **Generate Report** (`/reports`), triggering automated synthesis of an RBI/FIU-IND compliant Suspicious Transaction Report.
3. The system generates exportable JSON and branded forensic PDF dockets using `jspdf`, embedding evidence timelines and graph topologies.

### Session 8: Privacy-Preserving Cross-Bank Federated Learning
1. Multiple participating banks (e.g., SBI, HDFC, ICICI) register with the central `FederatedCoordinator`.
2. The coordinator initiates training rounds. Each bank trains a local graph/tabular model on its private on-premises transaction database.
3. Banks inject $(\epsilon, \delta)$ differential privacy noise into their weight updates and submit them to the coordinator.
4. The coordinator executes FedAvg aggregation to produce an updated global model that detects cross-bank mule patterns without any bank sharing confidential customer PII.

---

## 7. Database Entities & Relational Schema

```
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│            ACCOUNTS             │           │          TRANSACTIONS           │
├─────────────────────────────────┤           ├─────────────────────────────────┤
│ id (UUID, PK)                   │1         *│ id (UUID, PK)                   │
│ account_number (VARCHAR, UQ)    ├───────────┤ sender_account_id (UUID, FK)    │
│ customer_name (VARCHAR)         │           │ receiver_account_id (UUID, FK)  │
│ bank_name (VARCHAR)             │           │ transaction_ref (VARCHAR, UQ)   │
│ account_type (VARCHAR)          │           │ amount (NUMERIC)                │
│ risk_score (INTEGER)            │           │ channel (UPI/NEFT/IMPS/RTGS)    │
│ risk_level (VARCHAR)            │           │ trans_type (DEBIT/CREDIT)       │
│ is_flagged_mule (BOOLEAN)       │           │ timestamp (TIMESTAMPTZ)         │
│ created_at (TIMESTAMPTZ)        │           │ risk_score (INTEGER)            │
└────────────────┬────────────────┘           │ is_suspicious (BOOLEAN)         │
                 │                            └─────────────────────────────────┘
                 │1
                 │
                 │*
┌────────────────┴────────────────┐           ┌─────────────────────────────────┐
│             ALERTS              │           │             REPORTS             │
├─────────────────────────────────┤           ├─────────────────────────────────┤
│ id (UUID, PK)                   │           │ id (UUID, PK)                   │
│ account_id (UUID, FK)           │           │ report_number (VARCHAR, UQ)     │
│ alert_type (VARCHAR)            │           │ report_type (STR/CTR/COMPLAINT) │
│ severity (LOW/MED/HIGH/CRIT)    │           │ title (VARCHAR)                 │
│ risk_score (INTEGER)            │           │ summary_text (TEXT / JSON)      │
│ alert_status (OPEN/ESC/RES)     │           │ status (DRAFT/SUBMITTED)        │
│ rule_code (VARCHAR)             │           │ case_id (UUID, FK, Optional)    │
│ ai_narrative (TEXT)             │           │ generated_at (TIMESTAMPTZ)      │
│ triggered_at (TIMESTAMPTZ)      │           └─────────────────────────────────┘
└─────────────────────────────────┘
```

---

## 8. Deployment Architecture & Operational Blueprint

* **Frontend Hosting:** Netlify / Vercel Edge CDN with automated CI/CD builds from the `main` branch.
* **Backend Hosting:** Render Web Service (FastAPI running on Linux containers with automated health check probes on `/api/v1/health`).
* **Relational Storage:** Managed PostgreSQL 16 (Render / Supabase) with SSL encryption and async connection pooling.
* **Graph Storage:** Neo4j 5.x Enterprise / AuraDB instance accessible over encrypted Bolt protocol (`bolt+s://`).
* **Environment Isolation:** Zero hardcoded secrets; strict adherence to 12-factor configuration via `.env` and Pydantic Settings.

---

## 9. Conclusion & Strategic Roadmap

MuleTrace AI represents a generational shift in financial crime detection. By replacing siloed, heuristic rules with unified graph intelligence, explainable ML, and privacy-preserving federated collaboration, the platform equips Indian banking institutions and law enforcement agencies with the forensic velocity required to dismantle mule syndicates in real time.
