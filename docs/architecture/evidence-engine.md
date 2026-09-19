# MuleTrace AI — Deterministic Evidence Engine Architecture

> **Milestone**: M11 — Deterministic Evidence Engine  
> **Status**: Completed & Verified  
> **Target Environment**: BUILD IT Phase (Cloud-Agnostic Python Backend Subsystem)  
> **Audience**: Principal AI/Fraud Architects, AML Systems Engineers, Compliance Officers, Backend Engineers  

---

## 1. Executive Summary & Architectural Purpose

Milestone 11 establishes the **Deterministic Evidence Engine** for the MuleTrace AI platform.

While Milestone 10 answered the quantitative question:
> *"How risky is this transaction/account based on available multi-modal signals?"*

Milestone 11 answers the forensic and investigative question:
> *"What concrete, verifiable, deterministic evidence explains and substantiates that risk assessment?"*

The Evidence Engine sits directly downstream of Risk Fusion (M10) and upstream of the future Investigation Copilot (M12). It extracts granular evidence from rules, temporal features, graph topologies, machine learning models, and risk fusion contributions. It normalizes, deduplicates, and ranks these items deterministically into an immutable, audit-ready **EvidencePackage**.

```
    M5 Rule Signals
          │
    M6 Temporal Signals
          │
    M7 Graph Signals
          │
    M8 Tabular ML Prediction
          │
    M9 Graph ML Prediction
          │
    M10 Composite Risk
          │
          ▼
    ┌─────────────────────────────┐
    │ M11 Evidence Engine         │
    │                             │
    │ deterministic evidence      │
    │ extraction + ranking        │
    │ + provenance + explanation  │
    └──────────────┬──────────────┘
                   │
                   ▼
             EvidencePackage
                   │
                   ▼
          Future M12 Copilot
```

---

## 2. Hard Invariant: Exact M10 Preservation

The most critical architectural constraint of Milestone 11 is that **M11 never calculates a competing risk score, never modifies the M10 composite risk score, and never alters the M10 risk level**.

$$\text{M11}(\text{Input}, \text{FusionResult}) \implies \begin{cases} \text{composite\_risk\_score} \equiv \text{FusionResult.composite\_risk\_score} \\ \text{risk\_level} \equiv \text{FusionResult.risk\_level} \end{cases}$$

If M10 produces `composite_risk_score = 86.75` and `risk_level = CRITICAL`, M11 preserves `86.75` and `CRITICAL` exactly down to the floating-point bit representation. M11 generates evidence *about* the assessment; it never re-evaluates the assessment.

---

## 3. Core Domain Contracts

### 3.1 `EvidenceInput`
An immutable, frozen container that aggregates all available upstream outputs:
- `transaction_event`: Optional canonical `TransactionEvent` (M1).
- `rule_signals`: Optional `EvaluationResult` or list of `RuleMatchResult` (M5).
- `temporal_features`: Optional `TemporalFeatures` (M6).
- `graph_features`: Optional `GraphFeatures` (M7).
- `tabular_prediction`: Optional `ModelPrediction` from XGBoost (M8).
- `graph_ml_prediction`: Optional `ModelPrediction` from GraphSAGE (M9).
- `fusion_result`: Optional `FusionResult` from Risk Fusion (M10).
- `case_id`: Optional pre-assigned or derived case identifier.
- `subject_id`: Optional focal subject (account or transaction) ID.
- `metadata`: Optional dictionary of pipeline telemetry.

All fields are optional, permitting graceful handling of partial or asynchronous pipelines.

### 3.2 `EvidenceItem`
A granular, verifiable forensic finding:
- `evidence_id`: Deterministic SHA-256 derived identifier (`EVD-{SOURCE}-{REF_SLUG}-{HASH[:12]}`).
- `category`: Categorical taxonomy (`RULE_VIOLATION`, `TEMPORAL_ANOMALY`, `TOPOLOGICAL_PATTERN`, `SHARED_INFRASTRUCTURE`, `CIRCULAR_ROUTING`, `MODEL_PREDICTION`, `RISK_FUSION_ASSESSMENT`, `TRANSACTION_CONTEXT`).
- `title`: Short human-readable title.
- `description`: Factual narrative describing the observed pattern.
- `severity`: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- `source`: `RULE`, `TEMPORAL`, `GRAPH`, `TABULAR_ML`, `GRAPH_ML`, `RISK_FUSION`, `TRANSACTION`.
- `source_reference`: Specific machine-readable reference (e.g. `RULE:R004`, `GRAPH:circular_routing`).
- `transaction_ids`, `account_ids`, `device_ids`, `ip_addresses`, `timestamps`: Linked entity tuples.
- `metrics`: Dictionary of raw numeric/boolean values from the originating engine.
- `rank`: Assigned priority integer (1 = highest priority).

### 3.3 `EvidencePackage`
The comprehensive, immutable result container:
- `case_id`, `subject_id`, `transaction_id`.
- `composite_risk_score`: Exactly preserved from M10.
- `risk_level`: Exactly preserved from M10.
- `evidence_items`: Ranked and deduplicated tuple of `EvidenceItem`.
- `evidence_summary`: Deterministic factual case narrative.
- `source_coverage`: Dictionary mapping each source to `AVAILABLE`, `PARTIAL`, `UNAVAILABLE`, or `MISSING`.
- `total_evidence_count`, `severity_counts`.
- `metadata`, `engine_version`.

---

## 4. Extraction & Modality Ingestion Architecture

### 4.1 Rule Evidence (M5)
Extracts triggered rules (`matched == True`) directly from `EvaluationResult.matches`:
- Preserves `rule_code` (e.g. `R004`), `rule_name`, `pattern_name`, and `narrative`.
- Preserves the rule's original severity directly (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- Preserves `score_contribution`.
- Associates sender and receiver accounts and transaction IDs.
- Zero rule re-evaluation: rules are never executed inside M11.

### 4.2 Temporal Evidence (M6)
Extracts temporal dynamics from `TemporalFeatures`:
- **Rapid In/Out Pass-Through**: Turns around funds with turnaround ratio and delay in seconds; captures incoming and outgoing transaction IDs from `PassThroughEvent`.
- **Burst Activity**: Flags transaction bursts with `burst_count` and `burst_transaction_ids`.
- **Velocity Spikes**: Flags elevated 1-hour transaction counts and monetary volumes.
- Zero temporal recalculation: rolling window calculations are never repeated.

### 4.3 Graph Evidence (M7)
Extracts topological patterns from `GraphFeatures`:
- **Circular Routing**: Detects directed loops ($A \to B \to C \to A$); preserves ordered node cycle path and assigns `CRITICAL` severity.
- **Shared Infrastructure**: Detects shared hardware devices and IP clusters across multiple accounts.
- **Topological Fan Ratios**: Detects synthetic dispersion and aggregation ratios.
- **Multi-Hop Downstream Chains**: Captures layering chains traversing $\ge 3$ hops.
- Zero graph traversal: graph database queries are never re-run inside M11.

### 4.4 Machine Learning Evidence (M8 & M9)
Extracts model-derived risk indicators from `ModelPrediction`:
- Identifies active, trained model predictions ($\text{fraud\_probability} \ge 0.50$ or $\text{risk\_score} \ge 50$).
- Factual compliance language: uses *"Model-derived risk indicator"*, strictly avoiding *"Confirmed fraud"*.
- Offline/unavailable models are detected via `details["status"] == "model_unavailable"` or fallback versions; they are marked `UNAVAILABLE` in source coverage and never generate fake low-risk evidence.

### 4.5 Risk Fusion Evidence (M10)
Extracts mathematical attribution from `FusionResult`:
- Creates a `RISK_FUSION_ASSESSMENT` item summarizing composite score and policy.
- Identifies dominant modality contributions ($\ge 15.0$ points to composite risk).
- Never recomputes weights or scores.

---

## 5. Deduplication & Ranking

### 5.1 Deterministic Deduplication
Evidence items are grouped by their stable analytical key:

$$\text{Key} = \text{source} \,\|\, \text{source\_reference} \,\|\, \text{category} \,\|\, \text{sorted}(\text{account\_ids})$$

When duplicate items are identified (e.g. identical rule triggered in multiple passes or overlapping transactions):
1. The **highest severity** is retained.
2. Entity references (`transaction_ids`, `account_ids`, `device_ids`, `ip_addresses`, `timestamps`) are unioned and sorted.
3. Metric dictionaries are merged.
4. The first stable occurrence order is preserved.

### 5.2 Deterministic Multi-Factor Ranking
Evidence items are sorted according to an explicit, tested hierarchy:
1. **Severity Tier**: `CRITICAL` (500) > `HIGH` (400) > `MEDIUM` (300) > `LOW` (200) > `INFO` (100).
2. **Source Authority**: `RULE` (70) > `GRAPH` (60) > `TEMPORAL` (50) > `GRAPH_ML` (40) = `TABULAR_ML` (40) > `RISK_FUSION` (30) > `TRANSACTION` (20).
3. **Signal Strength Magnitude**: Extracted continuous metric (e.g. score contribution, fraud probability, volume).
4. **Deterministic Tie-Breaker**: Lexicographical ascending order of `evidence_id`.

Assigned rank indices run sequentially $1, 2, \dots, N$.

---

## 6. Deterministic Summary Rendering

The `render_evidence_summary` module generates factual executive summaries without LLMs:
- Summarizes case ID, subject ID, composite risk score, and risk level.
- Reports total evidence count and severity breakdowns.
- Enumerates top 4 ranked forensic findings.
- Summarizes analytical source coverage.
- Purely deterministic template string generation; 100% reproducible and hallucination-free.

---

## 7. Security, Privacy & Compliance

- **No Credential Logging**: Passwords, secrets, and API keys are never ingested or written to evidence.
- **Entity Masking Compatibility**: Accounts and transaction references use identifiers, avoiding unencrypted PII exposure.
- **Audit-Ready Immutability**: All evidence objects are `frozen=True` dataclasses, ensuring tamper-evident preservation.
- **Defamation Safeguard**: Evidence items describe observed patterns and model predictions; they do not assert criminal guilt without legal adjudication.

---

## 8. Architectural Boundary: M11 vs. M12

| Functional Area | Milestone 11 (Evidence Engine) | Milestone 12 (Investigation Copilot) |
| :--- | :--- | :--- |
| **Evidence Extraction** | **OWNED**: Extracts and normalizes signals. | Consumes `EvidencePackage`. |
| **Deduplication & Ranking** | **OWNED**: Deterministic multi-factor ranking. | Reads ranked evidence items. |
| **Factual Case Summary** | **OWNED**: Deterministic template-based summary. | Reads summary for context. |
| **M10 Score Preservation** | **OWNED**: Strictly preserves M10 scores. | Displays M10 score. |
| **LLM Narrative Synthesis** | **NOT OWNED**: Zero LLM calls. | **OWNED**: Generative SAR narratives. |
| **Investigator Recommendations**| **NOT OWNED**: Zero action prescriptions. | **OWNED**: Suggests account freezes, KYC. |
| **Interactive Copilot Chat** | **NOT OWNED**: No conversational interface. | **OWNED**: Natural language Q&A. |
| **Decision Management** | **NOT OWNED**: No triage status changes. | **OWNED**: Escalation & closure workflows. |
