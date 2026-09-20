<p align="center">
  <img src="docs/images/muletrace-banner.png" alt="MuleTrace AI Banner" width="100%" />
</p>

<h1 align="center">MuleTrace AI</h1>

<h3 align="center">Cross-Channel Mule Account Detection & Financial Crime Investigation Platform</h3>

<p align="center">
  <em>AI-Powered Graph Intelligence for Banking Fraud Investigation</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0--alpha-blue?style=for-the-badge" alt="Version" />
  <img src="https://img.shields.io/badge/license-AGPL--3.0-green?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-14+-black?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-16+-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Netlify-Deployed-00C7B7?style=for-the-badge&logo=netlify&logoColor=white" alt="Netlify" />
  <img src="https://img.shields.io/badge/Render-Backend-46E3B7?style=for-the-badge&logo=render&logoColor=white" alt="Render" />
  <img src="https://img.shields.io/badge/Federated%20Learning-Privacy%20Preserving-purple?style=for-the-badge" alt="Federated Learning" />
  <img src="https://img.shields.io/badge/status-In%20Development-orange?style=for-the-badge" alt="Status" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome" />
  <img src="https://img.shields.io/badge/made%20with-❤️-red?style=flat-square" alt="Made with Love" />
  <img src="https://img.shields.io/badge/RBI-Compliant-darkgreen?style=flat-square" alt="RBI Compliant" />
  <img src="https://img.shields.io/badge/AML-Ready-darkred?style=flat-square" alt="AML Ready" />
  <img src="https://img.shields.io/badge/Differential%20Privacy-%20(ε,%20δ)-blueviolet?style=flat-square" alt="Differential Privacy" />
</p>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Why Mule Accounts Are Dangerous](#-why-mule-accounts-are-dangerous)
- [Current Banking Challenges](#-current-banking-challenges)
- [Our Solution](#-our-solution)
- [Objectives](#-objectives)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Workflow Architecture](#-workflow-architecture)
- [Fraud Detection Pipeline](#-fraud-detection-pipeline)
- [Graph Intelligence](#-graph-intelligence)
- [Machine Learning Pipeline](#-machine-learning-pipeline)
- [Rule Engine](#-rule-engine)
- [Explainable AI (XAI)](#-explainable-ai-xai)
- [Fraud Patterns Detected](#-fraud-patterns-detected)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Project Modules](#-project-modules)
- [Installation Guide](#-installation-guide)
- [Development Setup](#-development-setup)
- [Git Workflow & Branch Strategy](#-git-workflow--branch-strategy)
- [Pages Overview](#-pages-overview)
- [API Modules](#-api-modules)
- [Graph Engine](#-graph-engine-1)
- [ML Engine](#-ml-engine-1)
- [Screenshots](#-screenshots)
- [Coding Standards](#-coding-standards)
- [Future Scope](#-future-scope)
- [Contributors](#-contributors)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)

---

## 🔍 Overview

**MuleTrace AI** is an enterprise-grade, AI-powered financial crime investigation platform purpose-built for detecting cross-channel mule account networks in the Indian banking ecosystem.

The platform combines **Graph Intelligence**, **Machine Learning**, **Rule-Based Detection**, and **Explainable AI** to identify, trace, and investigate mule account chains used in cyber fraud, money laundering, and terror financing.

> Built for **Banks**, **RBI**, **Financial Intelligence Units (FIU-IND)**, **Cyber Crime Investigation Teams**, **AML Compliance Officers**, and **Fraud Analysts**.

---

## 🚨 Problem Statement

India's digital payment ecosystem processes **over 13 billion UPI transactions monthly**. While this drives financial inclusion, it has simultaneously created a massive attack surface for cybercriminals.

**Mule accounts** — bank accounts opened or compromised to funnel illicit funds — are the backbone of nearly every digital financial crime:

- **Cyber fraud victims** lose money that is instantly layered through 5-15 mule accounts across multiple banks
- **Traditional rule-based systems** catch less than 2% of mule accounts
- **Investigations are manual**, taking 30-90 days per case
- **Cross-bank coordination** is almost non-existent
- There is **no unified intelligence platform** available to investigators

**The gap is clear:** Banks and law enforcement need an AI-powered platform that can detect mule networks in real-time, trace money flows across channels, and generate investigation-ready evidence.

---

## ⚠️ Why Mule Accounts Are Dangerous

| Threat Vector | Impact |
|:---|:---|
| **Layering Speed** | Stolen funds traverse 5-15 accounts within minutes, making recovery nearly impossible |
| **Cross-Bank Chains** | Mule networks span multiple banks, defeating single-bank detection systems |
| **Volume** | A single fraud ring may operate 500-2,000 mule accounts simultaneously |
| **Recruitment** | Mule recruiters target students, rural populations, and unemployed youth |
| **Regulatory Risk** | Banks face RBI penalties, license risk, and reputational damage for harboring mule accounts |
| **National Security** | Mule networks are linked to terror financing, drug trafficking, and hawala operations |
| **Investigation Overload** | Law enforcement receives 50,000+ complaints/month with limited forensic tools |

---

## 🏦 Current Banking Challenges

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT STATE OF DETECTION                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❌  Rule-based systems generate 95%+ false positives           │
│  ❌  No cross-channel correlation (UPI + NEFT + IMPS)           │
│  ❌  Manual investigation takes 30-90 days per case             │
│  ❌  No graph-based relationship analysis                       │
│  ❌  No device/IP/geolocation intelligence                      │
│  ❌  Investigators lack visual forensic tools                   │
│  ❌  No explainability — "why was this flagged?" is unanswered  │
│  ❌  Siloed data across departments and banks                   │
│  ❌  No real-time alerting or prioritization                    │
│  ❌  Compliance reports are manually generated                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💡 Our Solution

**MuleTrace AI** addresses every gap with a unified, intelligent investigation platform:

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULETRACE AI CAPABILITIES                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅  AI-powered mule account detection (Graph + ML + Rules)     │
│  ✅  Cross-channel transaction correlation                      │
│  ✅  Real-time graph construction & visualization               │
│  ✅  14+ fraud pattern detection algorithms                     │
│  ✅  Device, IP, and geolocation intelligence                   │
│  ✅  Visual investigation workspace                             │
│  ✅  SHAP-based explainability for every alert                  │
│  ✅  Automated STR/CTR report generation                        │
│  ✅  Role-based access for banks, RBI, and law enforcement      │
│  ✅  LLM-powered investigation summaries                        │
│  ✅  Real-time risk scoring engine                              │
│  ✅  Production-ready deployment (Netlify + Render)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Objectives

1. **Detect** mule account networks using graph intelligence and machine learning
2. **Trace** money flows across UPI, NEFT, IMPS, and RTGS channels in real-time
3. **Investigate** suspicious accounts through an interactive visual workspace
4. **Explain** every risk score and alert with SHAP-based explainability
5. **Report** automatically generate RBI/FIU-compliant STR and CTR reports
6. **Scale** to process millions of transactions per day across multiple banks
7. **Empower** investigators with AI-assisted analysis and LLM-generated summaries

---

## ✨ Key Features

### 🔗 Graph Intelligence
- Real-time transaction graph construction using Neo4j
- Community detection (Louvain, Label Propagation)
- Centrality analysis (PageRank, Betweenness, Degree)
- Shortest path tracing between suspicious accounts
- Subgraph extraction for investigation

### 🤖 Machine Learning
- Isolation Forest for anomaly detection
- XGBoost/GraphSAGE for mule classification
- Real-time feature engineering pipeline
- Model versioning and retraining workflows

### 📊 Risk Score Engine
- Multi-signal risk fusion (Graph + ML + Rules)
- Dynamic risk scoring with configurable weights
- Historical risk trend analysis
- Account-level and network-level scoring

### 🧠 Explainable AI
- SHAP (SHapley Additive exPlanations) integration
- Feature importance visualization per alert
- Natural language explanations via LLM
- Audit-ready explanation logs

### 📋 Rule Engine
- 14+ configurable fraud pattern rules
- Threshold-based and behavior-based rules
- Real-time rule evaluation
- Custom rule builder for investigators

### 🗺️ Geo Intelligence
- Impossible travel detection
- Device-location correlation
- IP geolocation mapping
- Heat map visualization

### 📈 Investigation Workspace
- Interactive graph explorer
- Timeline-based transaction analysis
- Multi-account comparison view
- Evidence collection and case management

### 📄 Compliance & Reporting
- Automated STR (Suspicious Transaction Report) generation
- CTR (Cash Transaction Report) generation
- RBI/FIU-IND compliant report formats
- Exportable investigation summaries

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MULETRACE AI — SYSTEM ARCHITECTURE               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐               │
│   │   Frontend    │     │   Backend    │     │  Database    │               │
│   │  (Next.js)    │────▶│  (FastAPI)   │────▶│ (PostgreSQL) │               │
│   │  Port: 3000   │     │  Port: 8000  │     │  Port: 5432  │               │
│   └──────────────┘     └──────┬───────┘     └──────────────┘               │
│                               │                                             │
│              ┌────────────────┼────────────────┐                            │
│              ▼                ▼                ▼                             │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│   │ Graph Engine  │  │  ML Engine   │  │ Rule Engine   │                    │
│   │ (Neo4j)       │  │ (Scikit/XGB) │  │ (Custom)      │                    │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                     │
│          │                 │                  │                              │
│          └─────────────────┼──────────────────┘                             │
│                            ▼                                                │
│                  ┌──────────────────┐                                       │
│                  │  Risk Score      │                                       │
│                  │  Fusion Engine   │                                       │
│                  └────────┬─────────┘                                       │
│                           ▼                                                 │
│              ┌──────────────────────┐                                       │
│              │  Explainable AI      │                                       │
│              │  (SHAP + LLM)        │                                       │
│              └──────────┬───────────┘                                       │
│                         ▼                                                   │
│              ┌──────────────────────┐                                       │
│              │  Dashboard &         │                                       │
│              │  Investigation UI    │                                       │
│              └──────────────────────┘                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Workflow Architecture

<p align="center">
  <img src="docs/images/workflow-architecture.jpeg" alt="MuleTrace AI — Workflow Architecture" width="100%" />
</p>

<p align="center"><em>MuleTrace AI — End-to-End Fraud Detection Pipeline</em></p>

### Pipeline Stages

| Stage | Component | Description |
|:---:|:---|:---|
| **1** | **Raw Banking Transactions** | Ingest transaction data from CBS, UPI, NEFT, IMPS, RTGS feeds |
| **2** | **Data Cleaning** | Normalize, deduplicate, validate, and enrich raw transaction data |
| **3** | **Feature Engineering** | Extract 50+ behavioral, temporal, and statistical features per account |
| **4** | **Rule Engine** | Apply 14+ configurable fraud pattern rules for initial flagging |
| **5** | **Graph Construction** | Build dynamic transaction graphs (accounts → nodes, transactions → edges) |
| **6** | **Graph Algorithms** | Run community detection, centrality analysis, cycle detection |
| **7** | **Isolation Forest** | Unsupervised anomaly detection to identify statistical outliers |
| **8** | **XGBoost / GraphSAGE** | Supervised classification for mule account probability scoring |
| **9** | **SHAP Explainability** | Generate feature-level explanations for every prediction |
| **10** | **Risk Score Engine** | Fuse graph, ML, and rule signals into a unified risk score (0-100) |
| **11** | **LLM Report Generation** | Generate natural language investigation summaries and case narratives |
| **12** | **Admin Dashboard** | Present alerts, graphs, reports, and investigation tools to analysts |

---

## 🕸️ Fraud Detection Pipeline

```
                    ┌─────────────────────────────┐
                    │    TRANSACTION DATA FEED     │
                    │  (UPI / NEFT / IMPS / RTGS)  │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     DATA PREPROCESSING      │
                    │  Clean → Validate → Enrich  │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │    FEATURE ENGINEERING       │
                    │  50+ Features per Account    │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
   ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
   │   RULE ENGINE    │ │  GRAPH ENGINE    │ │   ML ENGINE      │
   │                  │ │                  │ │                  │
   │ • 14+ Patterns   │ │ • Community Det. │ │ • Isolation For. │
   │ • Threshold      │ │ • Centrality     │ │ • XGBoost        │
   │ • Velocity       │ │ • Cycle Detect.  │ │ • GraphSAGE      │
   │ • Cross-Channel  │ │ • Path Analysis  │ │ • Scoring        │
   └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 ▼
                    ┌──────────────────────┐
                    │    RISK FUSION       │
                    │   Score: 0 — 100     │
                    │  Graph + ML + Rules  │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │  EXPLAINABLE AI      │
                    │  SHAP + LLM Narr.    │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │  ALERTS & REPORTS    │
                    │  Dashboard + STR     │
                    └──────────────────────┘
```

---

## 🕸️ Graph Intelligence

The Graph Engine is the core differentiator of MuleTrace AI. While traditional AML systems analyze individual transactions in isolation, MuleTrace AI constructs a **living transaction graph** that reveals hidden relationships and mule networks.

### Graph Construction
```
Account A ──₹50K──▶ Account B ──₹49K──▶ Account C ──₹48K──▶ Account D
    │                   │                    │
    │              Shared Device         Shared IP
    │                   │                    │
Account E ◀──₹30K──── Account F ──₹29K──▶ Account G
```

### Graph Algorithms Used

| Algorithm | Purpose | Application |
|:---|:---|:---|
| **Louvain Community Detection** | Find clusters of tightly connected accounts | Identify mule networks operating as a group |
| **Label Propagation** | Fast community detection | Real-time network identification |
| **PageRank** | Identify influential nodes | Find controller accounts in mule chains |
| **Betweenness Centrality** | Find bridge accounts | Detect accounts connecting mule clusters |
| **Degree Centrality** | Find highly connected accounts | Identify hub accounts receiving/sending to many |
| **Cycle Detection** | Find circular money flows | Detect layering and circular laundering |
| **Shortest Path** | Trace money flow routes | Investigation path from victim to cash-out |
| **Connected Components** | Identify isolated networks | Group related mule accounts |

---

## 🤖 Machine Learning Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                     ML PIPELINE ARCHITECTURE                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐                                              │
│  │ Raw Features   │                                              │
│  │ (50+ signals)  │                                              │
│  └───────┬────────┘                                              │
│          ▼                                                       │
│  ┌────────────────┐     ┌────────────────┐                       │
│  │ Isolation      │     │ Graph Features │                       │
│  │ Forest         │     │ (Neo4j)        │                       │
│  │ (Anomaly Det.) │     │ • PageRank     │                       │
│  └───────┬────────┘     │ • Centrality   │                       │
│          │              │ • Community ID │                       │
│          │              └───────┬────────┘                       │
│          │                      │                                │
│          └──────────┬───────────┘                                │
│                     ▼                                            │
│          ┌────────────────────┐                                   │
│          │  Feature Matrix    │                                   │
│          │  (Combined)        │                                   │
│          └─────────┬──────────┘                                   │
│                    ▼                                              │
│          ┌────────────────────┐                                   │
│          │  XGBoost /         │                                   │
│          │  GraphSAGE         │                                   │
│          │  (Classification)  │                                   │
│          └─────────┬──────────┘                                   │
│                    ▼                                              │
│          ┌────────────────────┐                                   │
│          │  SHAP              │                                   │
│          │  Explainability    │                                   │
│          └─────────┬──────────┘                                   │
│                    ▼                                              │
│          ┌────────────────────┐                                   │
│          │  Risk Score        │                                   │
│          │  (0 — 100)         │                                   │
│          └────────────────────┘                                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Feature Categories

| Category | Examples | Count |
|:---|:---|:---:|
| **Transaction Velocity** | Txn count per hour/day/week, burst detection | 8 |
| **Amount Distribution** | Mean, std, skewness, round-amount ratio | 7 |
| **Temporal Patterns** | Night-hour ratio, weekend ratio, time-gap entropy | 6 |
| **Channel Diversity** | UPI/NEFT/IMPS ratio, channel switching frequency | 5 |
| **Counterparty Analysis** | Unique senders/receivers, fan-in/fan-out ratio | 6 |
| **Account Behavior** | Account age, dormancy periods, activation patterns | 5 |
| **Device/IP Signals** | Unique devices, shared device count, IP diversity | 6 |
| **Geolocation** | Unique cities, impossible travel flag, geo-spread | 5 |
| **Graph Features** | PageRank, betweenness, community ID, clustering coeff. | 6 |

---

## ⚙️ Rule Engine

The Rule Engine applies deterministic, configurable rules that encode domain expertise from AML investigators and RBI guidelines.

```
┌──────────────────────────────────────────────────────────┐
│                    RULE ENGINE FLOW                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   Transaction ──▶ Rule Matcher ──▶ Pattern Detected?     │
│                                         │                │
│                               ┌─────────┴──────────┐     │
│                               ▼                    ▼     │
│                          YES: Flag            NO: Pass    │
│                          + Score              to Next     │
│                          + Evidence                      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Rule Categories

| Rule ID | Pattern | Description | Default Threshold |
|:---:|:---|:---|:---|
| R001 | High Velocity | > N transactions in T hours | 20 txns / 1 hour |
| R002 | Fan-In | > N unique senders to one account | 10 senders / 24h |
| R003 | Fan-Out | > N unique receivers from one account | 10 receivers / 24h |
| R004 | Circular Flow | Funds return to origin within N hops | 5 hops |
| R005 | Near-Equal Amounts | Send ≈ Receive (layering indicator) | 95% pass-through |
| R006 | Dormant Activation | Account dormant > N days, sudden activity | 90 days |
| R007 | New Account Abuse | High volume within N days of opening | 7 days |
| R008 | Cross-Channel | Rapid channel switching (UPI → NEFT → IMPS) | 3 channels / 1h |
| R009 | Smurfing | Multiple small transactions just below threshold | ₹49,000 pattern |
| R010 | Shared Device | Multiple accounts accessed from same device | 3+ accounts |
| R011 | Shared IP | Multiple accounts from same IP address | 5+ accounts |
| R012 | Impossible Travel | Transactions from distant locations in short time | 500km / 1h |
| R013 | Night Activity | High transaction volume during 12AM-5AM | 60%+ night ratio |
| R014 | Shared Beneficiary | Multiple accounts sharing same beneficiary | 5+ accounts |

---

## 🧠 Explainable AI (XAI)

Every alert in MuleTrace AI comes with a **human-readable explanation** powered by SHAP and LLM.

### Why Explainability Matters

- **Investigators** need to understand why an account was flagged before taking action
- **Compliance teams** need audit-ready justifications for regulatory reporting
- **Legal proceedings** require evidence-grade explanations, not black-box scores
- **RBI/FIU** mandates require documented reasoning for suspicious activity reports

### Explainability Stack

```
┌─────────────────────────────────────────────────────┐
│              EXPLAINABILITY ARCHITECTURE             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Model Prediction ──▶ SHAP Analysis                 │
│                          │                          │
│                          ▼                          │
│                  Feature Importance                  │
│                  (Top 5 factors)                     │
│                          │                          │
│                          ▼                          │
│                  LLM Narrative Generation            │
│                  (Human-readable summary)            │
│                          │                          │
│                          ▼                          │
│                  Investigation Report               │
│                  (Auditable + Exportable)            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Sample Explanation Output

```json
{
  "account_id": "XXXX1234",
  "risk_score": 87,
  "risk_level": "CRITICAL",
  "top_factors": [
    { "feature": "fan_in_count_24h", "value": 23, "impact": "+18.5" },
    { "feature": "night_txn_ratio", "value": 0.78, "impact": "+14.2" },
    { "feature": "account_age_days", "value": 5, "impact": "+12.8" },
    { "feature": "pagerank_score", "value": 0.034, "impact": "+10.1" },
    { "feature": "amount_passthrough_ratio", "value": 0.96, "impact": "+9.7" }
  ],
  "narrative": "Account XXXX1234 was flagged as CRITICAL risk (87/100). The account received funds from 23 unique senders in the last 24 hours (Fan-In pattern), with 78% of transactions occurring between 12AM-5AM. The account was opened only 5 days ago and passes through 96% of received funds to downstream accounts, consistent with mule account behavior. The account holds a significant position in the transaction network (PageRank: 0.034), suggesting it serves as a hub in a potential mule chain."
}
```

---

## 🔎 Fraud Patterns Detected

MuleTrace AI detects **14 distinct fraud patterns** across transaction, behavioral, device, and network dimensions.

### 1. 🔗 Mule Chain
**Definition:** A sequence of accounts that rapidly pass funds from source to destination with minimal retention.
```
Victim ──₹1L──▶ Mule A ──₹99K──▶ Mule B ──₹98K──▶ Mule C ──₹97K──▶ Cash-out
                 (2 min)          (3 min)          (2 min)
```
**Indicators:** Near-equal send/receive amounts, short holding time, sequential flow.

---

### 2. 📱 Shared Device
**Definition:** Multiple bank accounts operated from the same physical device (phone/laptop).
```
Device: Samsung A54 (IMEI: 3534XXXX)
    ├── Account A (Bank 1)
    ├── Account B (Bank 2)
    └── Account C (Bank 3)
```
**Indicators:** Same device fingerprint across 3+ accounts from different individuals.

---

### 3. 🌐 Shared IP
**Definition:** Multiple unrelated accounts transacting from the same IP address.
```
IP: 103.21.XX.XX
    ├── Account A — ₹4.9L sent
    ├── Account B — ₹4.8L sent
    ├── Account C — ₹4.7L sent
    └── Account D — ₹4.9L sent
```
**Indicators:** 5+ accounts sharing IP within 24h window, not an institutional IP.

---

### 4. ⚡ High Velocity
**Definition:** Abnormally high transaction frequency within a short time window.
```
Account X: 47 transactions in 2 hours
           Average: 3 transactions/day (historical)
```
**Indicators:** Txn count > 3σ from historical mean, burst pattern detection.

---

### 5. 🔀 Cross-Channel
**Definition:** Rapid switching between payment channels to evade channel-specific monitoring.
```
10:01 — UPI (₹49K) → Account B
10:03 — NEFT (₹48K) → Account C
10:05 — IMPS (₹47K) → Account D
10:08 — RTGS (₹2L) → Account E
```
**Indicators:** 3+ channels used within 1 hour, amounts just below reporting thresholds.

---

### 6. 📥 Fan-In
**Definition:** Multiple accounts sending funds to a single collector account.
```
Account A ──₹50K──┐
Account B ──₹48K──┤
Account C ──₹52K──├──▶ Collector Account
Account D ──₹49K──┤
Account E ──₹51K──┘
```
**Indicators:** 10+ unique senders in 24h to a single account, inconsistent with account profile.

---

### 7. 📤 Fan-Out
**Definition:** Single account distributing funds to multiple recipient accounts.
```
                    ┌──▶ Account A (₹49K)
                    ├──▶ Account B (₹48K)
Distributor ────────├──▶ Account C (₹50K)
                    ├──▶ Account D (₹47K)
                    └──▶ Account E (₹49K)
```
**Indicators:** 10+ unique receivers in 24h, near-equal distribution amounts.

---

### 8. 🔄 Circular Loop
**Definition:** Funds flowing through a chain of accounts and returning to the origin.
```
Account A ──▶ Account B ──▶ Account C ──▶ Account D ──▶ Account A
   ₹1L           ₹99K          ₹98K          ₹97K
```
**Indicators:** Cycle detected in transaction graph within N hops, fund retention < 5%.

---

### 9. 💸 Smurfing (Structuring)
**Definition:** Breaking large amounts into multiple smaller transactions to avoid reporting thresholds.
```
Instead of: ₹5,00,000 (triggers CTR)
Actual:     ₹49,000 + ₹48,500 + ₹49,200 + ₹48,800 + ₹49,100 + ...
            (10 transactions × ~₹49K = ₹4.9L — below threshold)
```
**Indicators:** Multiple transactions just below ₹50,000 threshold, total exceeds ₹10L in 24h.

---

### 10. 💤 Dormant Account Activation
**Definition:** Account with no activity for extended period suddenly becomes highly active.
```
Jan - Aug:  0 transactions (dormant for 8 months)
Sep 1-3:   147 transactions, ₹23L turnover
```
**Indicators:** Dormancy > 90 days followed by high-velocity activity within 72h.

---

### 11. ✈️ Impossible Travel
**Definition:** Transactions originating from geographically distant locations in impossibly short timeframes.
```
10:00 AM — Transaction from Mumbai (₹50K)
10:15 AM — Transaction from Delhi (₹48K)
           Distance: 1,400 km — Travel time: minimum 2 hours
```
**Indicators:** Distance/time ratio exceeding 500 km/hour between consecutive transactions.

---

### 12. 📲 Device Switching
**Definition:** Single account accessed from multiple devices in rapid succession.
```
Account X accessed from:
  09:00 — iPhone 15 (Delhi)
  09:05 — Samsung S24 (Delhi)
  09:12 — Redmi Note 13 (Mumbai)
  09:18 — OnePlus 12 (Chennai)
```
**Indicators:** 3+ unique devices within 1 hour, especially combined with location changes.

---

### 13. 👥 Shared Beneficiary
**Definition:** Multiple unrelated accounts adding the same beneficiary account.
```
Account A ──added──▶ Beneficiary X
Account B ──added──▶ Beneficiary X
Account C ──added──▶ Beneficiary X
Account D ──added──▶ Beneficiary X
           (all within 48 hours)
```
**Indicators:** 5+ accounts adding same beneficiary within 48h, beneficiary is a new account.

---

### 14. 🆕 New Account Abuse
**Definition:** Recently opened account showing unusually high transaction volumes.
```
Account opened: Day 0
Day 1: 23 transactions, ₹8.5L inflow
Day 2: 31 transactions, ₹12.3L outflow
Day 3: 28 transactions, ₹9.7L inflow
           (Typical new account: 2-3 txns/week)
```
**Indicators:** Account age < 7 days with velocity/volume > 95th percentile.

---

## 🛠️ Technology Stack

### Frontend
| Technology | Purpose | Version |
|:---|:---|:---:|
| **Next.js** | React framework (App Router) | 14.x |
| **TypeScript** | Type safety | 5.x |
| **Tailwind CSS** | Utility-first styling | 3.x |
| **shadcn/ui** | Component library | Latest |
| **Recharts** | Data visualization / Charts | 2.x |
| **React Flow** | Graph visualization | 11.x |
| **Leaflet** | Geospatial maps | 1.9.x |
| **Framer Motion** | Animations | 11.x |
| **Zustand** | State management | 4.x |
| **React Query** | API state management | 5.x |

### Backend
| Technology | Purpose | Version |
|:---|:---|:---:|
| **FastAPI** | REST API framework | 0.110+ |
| **Python** | Backend language | 3.11+ |
| **SQLAlchemy** | ORM | 2.x |
| **Alembic** | Database migrations | 1.13+ |
| **Pydantic** | Data validation | 2.x |
| **Celery** | Async task queue | 5.x |
| **Redis** | Caching / Message broker | 7.x |

### Graph Engine
| Technology | Purpose | Version |
|:---|:---|:---:|
| **Neo4j** | Graph database, construction & algorithms | 5.x |
| **Neo4j Python Driver** | Python connectivity to Neo4j | 5.x |
| **Neo4j GDS** | Graph Data Science (community detection, centrality, pathfinding) | 2.x |
| **GraphSAGE (PyG)** | Graph neural networks | 2.x |

### ML Engine
| Technology | Purpose | Version |
|:---|:---|:---:|
| **Scikit-learn** | Isolation Forest, preprocessing | 1.4+ |
| **XGBoost** | Gradient boosting classifier | 2.x |
| **SHAP** | Model explainability | 0.44+ |
| **Pandas** | Data manipulation | 2.x |
| **NumPy** | Numerical computation | 1.26+ |

### Database & Infrastructure
| Technology | Purpose | Version |
|:---|:---|:---:|
| **PostgreSQL** | Primary database (Render managed) | 16.x |
| **Redis** | Caching & pub/sub (Render managed) | 7.x |
| **Netlify** | Frontend hosting, CDN, CI/CD | — |
| **Render** | Backend hosting, managed services | — |
| **GitHub Actions** | CI/CD pipelines, code quality | — |

---

## 📁 Project Structure

```
TEAM-CIPHERUNIT/
│
├── 📄 README.md                          # Project documentation (this file)
├── 📄 LICENSE                            # AGPL-3.0 License
├── 📄 CONTRIBUTING.md                    # Contribution guidelines
├── 📄 CODE_OF_CONDUCT.md                # Community standards
├── 📄 CHANGELOG.md                       # Version history
├── 📄 SECURITY.md                        # Security policy
├── 📄 .gitignore                         # Git ignore rules
├── 📄 .env.example                       # Environment variable template
├── 📄 netlify.toml                       # Netlify deployment config
├── 📄 render.yaml                        # Render deployment blueprint
├── 📄 Makefile                           # Development shortcuts
│
├── 📂 docs/                              # Documentation
│   ├── 📂 images/                        # README & doc images
│   │   ├── muletrace-banner.png
│   │   └── workflow-architecture.jpeg
│   ├── 📄 Architecture.md
│   ├── 📄 ProblemStatement.md
│   ├── 📄 Workflow.md
│   ├── 📄 FraudPatterns.md
│   ├── 📄 API.md
│   ├── 📄 Database.md
│   ├── 📄 UIGuidelines.md
│   ├── 📄 Deployment.md
│   ├── 📄 CodingStandards.md
│   └── 📄 Presentation.md
│
├── 📂 frontend/                          # Next.js Application
│   ├── 📄 package.json
│   ├── 📄 tsconfig.json
│   ├── 📄 next.config.js
│   ├── 📄 tailwind.config.ts
│   ├── 📂 public/
│   │   ├── 📂 icons/
│   │   └── 📂 images/
│   ├── 📂 src/
│   │   ├── 📂 app/                       # Next.js App Router pages
│   │   │   ├── 📄 layout.tsx
│   │   │   ├── 📄 page.tsx               # Home / Landing
│   │   │   ├── 📂 dashboard/
│   │   │   ├── 📂 transactions/
│   │   │   ├── 📂 graph-intelligence/
│   │   │   ├── 📂 geo-intelligence/
│   │   │   ├── 📂 investigation/
│   │   │   ├── 📂 pattern-analysis/
│   │   │   ├── 📂 alerts/
│   │   │   ├── 📂 reports/
│   │   │   ├── 📂 ai-assistant/
│   │   │   ├── 📂 settings/
│   │   │   └── 📂 auth/
│   │   ├── 📂 components/
│   │   │   ├── 📂 layouts/
│   │   │   ├── 📂 charts/
│   │   │   ├── 📂 maps/
│   │   │   ├── 📂 graphs/
│   │   │   ├── 📂 timeline/
│   │   │   ├── 📂 cards/
│   │   │   ├── 📂 forms/
│   │   │   ├── 📂 dialogs/
│   │   │   ├── 📂 tables/
│   │   │   └── 📂 ui/
│   │   ├── 📂 hooks/
│   │   ├── 📂 utils/
│   │   ├── 📂 types/
│   │   ├── 📂 lib/
│   │   ├── 📂 services/
│   │   └── 📂 theme/
│   └── 📂 tests/
│
├── 📂 backend/                           # FastAPI Application
│   ├── 📄 requirements.txt
│   ├── 📄 Dockerfile
│   ├── 📂 app/
│   │   ├── 📄 main.py
│   │   ├── 📂 api/
│   │   │   ├── 📂 v1/
│   │   │   │   ├── 📂 endpoints/
│   │   │   │   └── 📄 router.py
│   │   │   └── 📄 deps.py
│   │   ├── 📂 controllers/
│   │   ├── 📂 services/
│   │   ├── 📂 repositories/
│   │   ├── 📂 models/
│   │   ├── 📂 schemas/
│   │   ├── 📂 database/
│   │   ├── 📂 auth/
│   │   ├── 📂 middleware/
│   │   ├── 📂 utils/
│   │   ├── 📂 config/
│   │   └── 📂 jobs/
│   └── 📂 tests/
│
├── 📂 graph-engine/                      # Graph Intelligence Engine
│   ├── 📄 requirements.txt
│   ├── 📂 src/
│   │   ├── 📂 builder/
│   │   ├── 📂 algorithms/
│   │   ├── 📂 patterns/
│   │   ├── 📂 analytics/
│   │   ├── 📂 relationships/
│   │   └── 📂 visualization/
│   └── 📂 tests/
│
├── 📂 ml-engine/                         # Machine Learning Engine
│   ├── 📄 requirements.txt
│   ├── 📂 src/
│   │   ├── 📂 features/
│   │   ├── 📂 models/
│   │   │   ├── 📂 isolation_forest/
│   │   │   └── 📂 xgboost/
│   │   ├── 📂 risk_fusion/
│   │   ├── 📂 prediction/
│   │   ├── 📂 training/
│   │   └── 📂 explainability/
│   └── 📂 tests/
│
├── 📂 rule-engine/                       # Rule-Based Detection Engine
│   ├── 📄 requirements.txt
│   ├── 📂 src/
│   │   ├── 📂 rules/
│   │   ├── 📂 evaluator/
│   │   └── 📂 config/
│   └── 📂 tests/
│
├── 📂 shared/                            # Shared Modules
│   ├── 📂 constants/
│   ├── 📂 exceptions/
│   ├── 📂 schemas/
│   └── 📂 utils/
│
├── 📂 database/                          # Database Management
│   ├── 📂 schemas/
│   ├── 📂 migrations/
│   ├── 📂 seeds/
│   └── 📂 sql/
│
├── 📂 deployment/                        # Deployment Configuration
│   ├── 📂 netlify/                      # Netlify config & redirects
│   ├── 📂 render/                       # Render service config
│   ├── 📂 scripts/
│   └── 📂 environments/
│
├── 📂 tests/                             # Integration & E2E Tests
│   ├── 📂 integration/
│   ├── 📂 e2e/
│   └── 📂 fixtures/
│
├── 📂 scripts/                           # Development Scripts
│   ├── 📄 setup.sh
│   ├── 📄 setup.ps1
│   ├── 📄 seed-db.sh
│   └── 📄 run-tests.sh
│
├── 📂 .github/                           # GitHub Configuration
│   ├── 📂 ISSUE_TEMPLATE/
│   │   ├── 📄 bug_report.md
│   │   ├── 📄 feature_request.md
│   │   └── 📄 investigation_module.md
│   ├── 📄 PULL_REQUEST_TEMPLATE.md
│   └── 📂 workflows/
│       ├── 📄 ci.yml
│       ├── 📄 cd.yml
│       └── 📄 codeql.yml
│
└── 📂 .vscode/                           # VS Code Configuration
    ├── 📄 settings.json
    ├── 📄 extensions.json
    └── 📄 launch.json
```

---

## 📦 Project Modules

| Module | Description | Tech Stack | Owner |
|:---|:---|:---|:---|
| **Frontend** | SOC-style dashboard, investigation workspace, graph visualization | Next.js, TypeScript, React Flow | Frontend Team |
| **Backend** | REST API, authentication, business logic orchestration | FastAPI, SQLAlchemy, Pydantic | Backend Team |
| **Graph Engine** | Transaction graph construction, community detection, path analysis | Neo4j, Neo4j GDS | Graph Team |
| **ML Engine** | Anomaly detection, classification, feature engineering | Scikit-learn, XGBoost, SHAP | ML Team |
| **Rule Engine** | Deterministic fraud pattern rules, threshold evaluation | Python, configurable YAML/JSON | Backend Team |
| **Risk Engine** | Multi-signal risk score fusion (Graph + ML + Rules) | Python | Backend Team |
| **Explainable AI** | SHAP analysis, LLM narrative generation | SHAP, LLM API | ML Team |
| **Reports** | STR/CTR generation, PDF export, compliance reports | ReportLab, Jinja2 | Backend Team |
| **Authentication** | JWT-based auth, RBAC, session management | FastAPI, JWT, bcrypt | Backend Team |
| **Deployment** | Cloud hosting, CI/CD, environment management | Netlify, Render, GitHub Actions | DevOps |

---

## 🚀 Installation Guide

### Prerequisites

| Tool | Version | Installation |
|:---|:---|:---|
| **Node.js** | 18.x+ | [nodejs.org](https://nodejs.org) |
| **Python** | 3.11+ | [python.org](https://python.org) |
| **PostgreSQL** | 16.x | [postgresql.org](https://www.postgresql.org) or Render managed |
| **Git** | 2.40+ | [git-scm.com](https://git-scm.com) |
| **Netlify CLI** | Latest | `npm install -g netlify-cli` |
| **Render Account** | — | [render.com](https://render.com) |

### Quick Start (Cloud Deployment)

```bash
# Clone the repository
git clone https://github.com/athishwarkannan-del/TEAM-CIPHERUNIT.git
cd TEAM-CIPHERUNIT

# Copy environment variables
cp .env.example .env
# Edit .env with your Render database URL, API keys, etc.
```

#### Deploy Frontend to Netlify
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Build and deploy frontend
cd frontend
npm install
npm run build
netlify deploy --prod

# Or connect your GitHub repo on https://app.netlify.com
# Netlify auto-deploys on every push to main
```

#### Deploy Backend to Render
```bash
# Option 1: Connect GitHub repo at https://dashboard.render.com
# Render auto-deploys from render.yaml blueprint

# Option 2: Use Render CLI
# Create a Web Service pointing to /backend
# Build Command:  pip install -r requirements.txt
# Start Command:  uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### Access the Application
```
# Frontend:  https://muletrace-ai.netlify.app  (or your custom domain)
# Backend:   https://muletrace-api.onrender.com
# API Docs:  https://muletrace-api.onrender.com/docs
# Database:  Render managed PostgreSQL
```

### Manual Setup

#### 1. Clone & Configure

```bash
git clone https://github.com/athishwarkannan-del/TEAM-CIPHERUNIT.git
cd TEAM-CIPHERUNIT
cp .env.example .env
# Edit .env with your database credentials and API keys
```

#### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

#### 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs (Swagger UI)
```

#### 4. Graph Engine Setup

```bash
cd graph-engine
pip install -r requirements.txt
```

#### 5. ML Engine Setup

```bash
cd ml-engine
pip install -r requirements.txt
```

#### 6. Database Setup

```bash
# Create PostgreSQL database
createdb muletrace_db

# Run migrations
cd backend
alembic upgrade head

# Seed sample data
cd ../scripts
bash seed-db.sh
```

---

## 💻 Development Setup

### VS Code Extensions (Recommended)

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-azuretools.vscode-docker",
    "github.copilot",
    "eamodio.gitlens"
  ]
}
```

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/muletrace_db

# Backend
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 🌿 Git Workflow & Branch Strategy

### Branch Structure

```
main                          ← Production-ready code (protected)
  │
  └── develop                 ← Integration branch (protected)
        │
        ├── feature/frontend-ui
        ├── feature/dashboard
        ├── feature/backend
        ├── feature/graph-engine
        ├── feature/ml-engine
        └── feature/integration
```

### Branch Rules

| Branch | Purpose | Protection |
|:---|:---|:---|
| `main` | Production releases only | 🔒 No direct pushes. Requires PR + 2 approvals |
| `develop` | Integration and testing | 🔒 No direct pushes. Requires PR + 1 approval |
| `feature/*` | Individual feature development | Open for assigned developers |
| `bugfix/*` | Bug fixes | Open, requires PR to develop |
| `hotfix/*` | Critical production fixes | Requires PR to main + develop |

### Workflow

```
1. Create feature branch from develop
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature

2. Develop and commit
   git add .
   git commit -m "feat(module): description"

3. Push and create PR
   git push origin feature/your-feature
   # Create PR → develop

4. Code review and merge
   # At least 1 reviewer approves
   # CI passes
   # Merge to develop

5. Release
   # develop → main (via release PR)
   # Tag version
```

### Commit Message Convention

```
<type>(<scope>): <description>

Types:
  feat     — New feature
  fix      — Bug fix
  docs     — Documentation
  style    — Formatting (no code change)
  refactor — Code restructuring
  test     — Adding tests
  chore    — Maintenance tasks
  perf     — Performance improvement
  ci       — CI/CD changes

Examples:
  feat(dashboard): add real-time alert panel
  fix(graph-engine): resolve cycle detection memory leak
  docs(api): update transaction endpoint documentation
  test(ml-engine): add isolation forest unit tests
```

---

## 📄 Pages Overview

| Page | Route | Description |
|:---|:---|:---|
| **Home** | `/` | Landing page with platform overview and login |
| **Dashboard** | `/dashboard` | SOC-style overview with KPIs, alerts, risk distribution |
| **Transactions** | `/transactions` | Transaction explorer with filtering, search, timeline |
| **Graph Intelligence** | `/graph-intelligence` | Interactive graph visualization, network exploration |
| **Geo Intelligence** | `/geo-intelligence` | Map-based analysis, impossible travel, heat maps |
| **Investigation** | `/investigation` | Case workspace, evidence collection, account deep-dive |
| **Pattern Analysis** | `/pattern-analysis` | Detected fraud patterns, rule hits, trend analysis |
| **Alerts** | `/alerts` | Alert queue, triage, assignment, status tracking |
| **Reports** | `/reports` | STR/CTR generation, export, compliance reporting |
| **AI Assistant** | `/ai-assistant` | LLM-powered investigation assistant, query interface |
| **Settings** | `/settings` | User profile, system config, rule thresholds |
| **Authentication** | `/auth/login` | Login, registration, password reset |

---

## 🔌 API Modules

### Backend API Structure (FastAPI)

| Module | Endpoint Prefix | Description |
|:---|:---|:---|
| **Auth** | `/api/v1/auth` | Login, register, refresh token, logout |
| **Users** | `/api/v1/users` | User management, roles, permissions |
| **Transactions** | `/api/v1/transactions` | CRUD, search, filter, bulk upload |
| **Accounts** | `/api/v1/accounts` | Account profiles, risk history, associations |
| **Alerts** | `/api/v1/alerts` | Alert queue, triage, status updates |
| **Graph** | `/api/v1/graph` | Graph queries, subgraph extraction, algorithms |
| **ML** | `/api/v1/ml` | Predictions, model status, retraining triggers |
| **Rules** | `/api/v1/rules` | Rule CRUD, threshold configuration |
| **Risk** | `/api/v1/risk` | Risk scores, fusion weights, history |
| **Reports** | `/api/v1/reports` | STR/CTR generation, export |
| **Investigations** | `/api/v1/investigations` | Case management, evidence, notes |
| **Analytics** | `/api/v1/analytics` | Dashboard KPIs, trends, statistics |

---

## 🕸️ Graph Engine

### Module Structure

| Module | Responsibility |
|:---|:---|
| **Graph Builder** | Construct transaction graphs in Neo4j (accounts → nodes, transactions → relationships) |
| **Graph Algorithms** | Run PageRank, Betweenness, Louvain, Label Propagation via Neo4j GDS |
| **Pattern Detection** | Detect cycles, fan-in, fan-out, mule chains, circular flows |
| **Graph Analytics** | Network-level statistics, density, diameter, clustering coefficients |
| **Relationship Engine** | Map account-device, account-IP, account-beneficiary relationships |
| **Visualization** | Generate graph layouts, export visualization data for React Flow |

---

## 🤖 ML Engine

### Module Structure

| Module | Responsibility |
|:---|:---|
| **Feature Engineering** | Extract 50+ features from transaction, device, and graph data |
| **Isolation Forest** | Unsupervised anomaly detection for statistical outlier identification |
| **XGBoost** | Supervised mule account classification |
| **Risk Fusion** | Combine graph, ML, and rule scores into unified risk score |
| **Prediction** | Real-time inference pipeline for incoming transactions |
| **Training** | Model training, validation, hyperparameter tuning workflows |
| **Explainability** | SHAP value computation, feature importance ranking |

---

## 📸 Screenshots

> 🚧 **Screenshots will be added as the UI is implemented.**
>
> Expected screenshots include:
> - SOC-style Dashboard
> - Transaction Explorer
> - Graph Intelligence Visualization
> - Investigation Workspace
> - Geo Intelligence Map
> - Alert Triage Panel
> - Pattern Analysis View
> - SHAP Explainability View
> - Report Generation
> - AI Assistant Interface

---

## 📏 Coding Standards

### General

| Standard | Convention |
|:---|:---|
| **Indentation** | 2 spaces (Frontend), 4 spaces (Backend) |
| **Line Length** | Max 100 characters |
| **File Naming** | `kebab-case` for files, `PascalCase` for components |
| **Folder Naming** | `kebab-case` (all lowercase, hyphen-separated) |

### Frontend (TypeScript / Next.js)

| Standard | Convention |
|:---|:---|
| **Components** | PascalCase (`TransactionTable.tsx`) |
| **Hooks** | camelCase with `use` prefix (`useTransactions.ts`) |
| **Utils** | camelCase (`formatCurrency.ts`) |
| **Types** | PascalCase with `.types.ts` suffix |
| **Constants** | UPPER_SNAKE_CASE |
| **CSS Classes** | Tailwind utility classes |

### Backend (Python / FastAPI)

| Standard | Convention |
|:---|:---|
| **Modules** | snake_case (`transaction_service.py`) |
| **Classes** | PascalCase (`TransactionService`) |
| **Functions** | snake_case (`get_transactions()`) |
| **Variables** | snake_case (`account_id`) |
| **Constants** | UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`) |
| **API Routes** | kebab-case (`/api/v1/risk-scores`) |

### API Naming

| Resource | GET (list) | GET (one) | POST | PUT | DELETE |
|:---|:---|:---|:---|:---|:---|
| Transactions | `/transactions` | `/transactions/{id}` | `/transactions` | `/transactions/{id}` | `/transactions/{id}` |
| Alerts | `/alerts` | `/alerts/{id}` | `/alerts` | `/alerts/{id}` | `/alerts/{id}` |
| Investigations | `/investigations` | `/investigations/{id}` | `/investigations` | `/investigations/{id}` | `/investigations/{id}` |

---

## 🔮 Future Scope

| Phase | Feature | Description |
|:---:|:---|:---|
| **Phase 2** | Real-Time Streaming | Apache Kafka integration for live transaction processing |
| **Phase 2** | Multi-Bank Federation | Cross-bank mule network detection with privacy-preserving analytics |
| **Phase 2** | Mobile App | React Native companion app for field investigators |
| **Phase 3** | NLP Document Analysis | Parse FIRs, bank statements, and KYC documents using NLP |
| **Phase 3** | GNN (Graph Neural Networks) | Replace heuristic graph algorithms with learned representations |
| **Phase 3** | Federated Learning | Train models across banks without sharing raw data |
| **Phase 4** | Blockchain Forensics | Extend to cryptocurrency and blockchain transaction tracing |
| **Phase 4** | Dark Web Intelligence | Monitor dark web forums for mule recruitment activities |
| **Phase 4** | Regulatory API | Direct integration with RBI/FIU-IND reporting systems |

---

## 👥 Contributors

<table>
  <tr>
    <td align="center">
      <strong>Team CipherUnit</strong><br/>
      <em>MuleTrace AI Development Team</em>
    </td>
  </tr>
</table>

> **Want to contribute?** Read our [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

---

## 📜 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

See [LICENSE](LICENSE) for the full license text.

```
MuleTrace AI — Cross-Channel Mule Account Detection & Financial Crime Investigation Platform
Copyright (C) 2025 Team CipherUnit

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
```

---

## 🙏 Acknowledgements

- **Reserve Bank of India (RBI)** — For AML/CFT guidelines and regulatory frameworks
- **Financial Intelligence Unit - India (FIU-IND)** — For STR/CTR reporting standards
- **Indian Cyber Crime Coordination Centre (I4C)** — For cybercrime investigation frameworks
- **NPCI** — For UPI transaction ecosystem documentation
- **Neo4j** — For graph database and graph data science capabilities
- **SHAP** — For model explainability
- **FastAPI** — For high-performance API framework
- **Next.js** — For production-grade React framework

---

<p align="center">
  <strong>MuleTrace AI</strong> — Defending India's Financial Ecosystem with AI-Powered Intelligence
</p>

<p align="center">
  Built with ❤️ by <strong>Team CipherUnit</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20in-India-orange?style=for-the-badge&logo=flag-india" alt="Made in India" />
</p>

## 👥 Team Members

```text
┌──────────────────────────────────────────────────────────────┐
│ 👤 Athishwar K     → Backend                                 │
│ 👤 Karmugilan R    → Graph Intelligence                      │
│ 👤 Sanjay B        → Frontend & Machine Learning             │
│ 👤 Sakthi Prakash  → Frontend                                │
└──────────────────────────────────────────────────────────────┘
```
