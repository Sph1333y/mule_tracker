# MuleTrace AI — Risk Fusion Architecture

> **Milestone**: M10 — Risk Fusion  
> **Status**: Completed & Verified  
> **Target Environment**: BUILD IT Phase (Cloud-Agnostic Python Backend Subsystem)  
> **Audience**: Principal AI/ML Architects, Fraud Systems Engineers, Risk Modelers, Backend Engineers  

---

## 1. Executive Summary & Architectural Purpose

Milestone 10 establishes the **Risk Fusion Subsystem** for MuleTrace AI.

The core objective of Risk Fusion is to synthesize independent, multi-modal fraud detection signals into a unified, deterministic, explainable composite risk assessment. In the MuleTrace AI platform, fraud indicators originate from five distinct analytical paradigms:

1. **Deterministic Expert Rules (M5)**: High-precision domain heuristics detecting regulatory, threshold, and structuring patterns.
2. **Temporal Intelligence (M6)**: Sliding-window velocity, burst frequency, and rapid pass-through dynamics.
3. **Graph Intelligence (M7)**: Topological structures, circular routing, shared telemetry entities, and synthetic fan ratios.
4. **Tabular Machine Learning (M8)**: Supervised gradient-boosted decision trees (XGBoost) trained on 57-dimensional feature vectors.
5. **Inductive Graph Machine Learning (M9)**: Inductive GraphSAGE graph neural networks operating over dynamic transaction graphs.

Risk Fusion is the central convergence point that ingests these heterogenous signals, normalizes them into continuous bounded intervals $[0.0, 1.0]$, applies validated weighting schemes, enforces strict missing-signal policies, computes a deterministic composite risk score $[0.0, 100.0]$, and categorizes the transaction into actionable risk tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

```
                    ┌─────────────────────────┐
                    │ Canonical Transaction   │
                    │      Event (M1)         │
                    └───────────┬─────────────┘
                                │
       ┌────────────────────────┼────────────────────────┐
       ▼                        ▼                        ▼
 ┌───────────┐            ┌───────────┐            ┌───────────┐
 │ 14 Rules  │            │ Temporal  │            │   Graph   │
 │   (M5)    │            │Engine (M6)│            │Engine (M7)│
 └─────┬─────┘            └─────┬─────┘            └─────┬─────┘
       │                        │                        │
       │                        ▼                        ▼
       │                  ┌───────────┐            ┌───────────┐
       │                  │Tabular ML │            │ Graph ML  │
       │                  │XGBoost(M8)│            │GraphSAGE  │
       │                  └─────┬─────┘            │   (M9)    │
       │                        │                  └─────┬─────┘
       │                        │                        │
       ▼                        ▼                        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                Risk Fusion Subsystem (M10)                  │
 │                                                             │
 │  ┌───────────────────────────────────────────────────────┐  │
 │  │ 1. Signal Normalizer: Map each modality to [0.0, 1.0] │  │
 │  └───────────────────────────┬───────────────────────────┘  │
 │                              ▼                              │
 │  ┌───────────────────────────────────────────────────────┐  │
 │  │ 2. Missing Signal Handler: RENORMALIZE / ZERO / PEN   │  │
 │  └───────────────────────────┬───────────────────────────┘  │
 │                              ▼                              │
 │  ┌───────────────────────────────────────────────────────┐  │
 │  │ 3. Weighted Fusion: S_composite = 100 * SUM(w_i * s_i)│  │
 │  └───────────────────────────┬───────────────────────────┘  │
 │                              ▼                              │
 │  ┌───────────────────────────────────────────────────────┐  │
 │  │ 4. Threshold Classifier: LOW / MEDIUM / HIGH / CRIT   │  │
 │  └───────────────────────────┬───────────────────────────┘  │
 │                              ▼                              │
 │  ┌───────────────────────────────────────────────────────┐  │
 │  │ 5. Contribution Attribution & Explainability          │  │
 │  └───────────────────────────────────────────────────────┘  │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
                       FusionResult (M10)
                                │
                                ▼
                   Evidence Engine (Future M11)
```

---

## 2. Architectural Boundary: M10 vs. M11

A foundational design requirement of the MuleTrace AI architecture is the strict separation of concerns between **Signal Synthesis (M10)** and **Evidence / Narrative Generation (M11)**:

| Responsibility Domain | Milestone 10 (Risk Fusion) | Milestone 11 (Evidence Engine) |
| :--- | :--- | :--- |
| **Signal Collection & Ingestion** | **OWNED**: Accepts M5, M6, M7, M8, M9 outputs. | Read-only consumer of `FusionResult`. |
| **Normalization & Scaling** | **OWNED**: Maps all raw outputs to continuous $[0.0, 1.0]$. | Does not perform signal normalization. |
| **Weighting & Policy Enforcement** | **OWNED**: Re-scaling, missing signal fallback policies. | None. |
| **Composite Score & Tier** | **OWNED**: Calculates $[0.0, 100.0]$ score and RiskLevel. | Reads composite score and tier. |
| **Mathematical Contribution** | **OWNED**: Absolute points and percentage per modality. | Formats contribution for visual reports. |
| **Natural Language Explanations** | **NOT OWNED**: Mathematical narrative only. | **OWNED**: Comprehensive SAR-ready narrative. |
| **Graph Path Walk & Visualization** | **NOT OWNED**: Only consumes numeric graph features. | **OWNED**: Visual subgraphs, shortest paths, flow trails. |
| **Investigator Recommendations** | **NOT OWNED**: Zero action prescriptions. | **OWNED**: Freeze account, trigger KYC, submit SAR. |
| **Audit Trails & Regulatory Filing** | **NOT OWNED**: Ephemeral / stateless computation. | **OWNED**: Persistent audit logs, SAR XML export. |

---

## 3. Signal Contracts & Ingestion Audits

Risk Fusion interfaces directly with the standardized domain objects and outputs established across Milestones 5 through 9:

### 3.1 Rule Engine (M5)
- **Input Object**: `RuleEvaluationResult` ([backend/app/engines/rules/base.py](file:///D:/Team_Cipher_Unit/backend/app/engines/rules/base.py))
- **Payload Attributes**:
  - `total_score_delta`: Cumulative heuristic risk delta (typically $[0, 100]$).
  - `matches`: List of triggered `RuleMatch` objects with `severity` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and `score_delta`.
- **Contract Characteristics**: High-precision, zero false-positive tolerance for compliance rules.

### 3.2 Temporal Intelligence Engine (M6)
- **Input Object**: `TemporalFeatures` ([backend/app/engines/temporal/feature_extractor.py](file:///D:/Team_Cipher_Unit/backend/app/engines/temporal/feature_extractor.py))
- **Payload Attributes**:
  - `rapid_in_out_ratio`: Ratio of outbound volume to recent inbound volume $[0.0, 1.0]$.
  - `burst_detected`: Boolean indicator of burst activity within window.
  - `velocity_score`: Continuous aggregate velocity metric.
  - `tx_count_1h`, `tx_count_24h`, `dormancy_prior_days`.
- **Contract Characteristics**: Temporal dynamics indicating rapid pass-through and structuring.

### 3.3 Graph Intelligence Engine (M7)
- **Input Object**: `GraphFeatures` ([backend/app/engines/graph/intelligence/feature_extractor.py](file:///D:/Team_Cipher_Unit/backend/app/engines/graph/intelligence/feature_extractor.py))
- **Payload Attributes**:
  - `cycle_detected`: Boolean flag for circular transaction loops ($A \to B \to \dots \to A$).
  - `shared_device_count`, `shared_ip_count`: Multi-account entity co-occurrence counts.
  - `fan_in_ratio`, `fan_out_ratio`: Ratio of unique counterparties to volume.
  - `neighborhood_density`: Local clustering density.
- **Contract Characteristics**: Topological and syndicate collusion detection.

### 3.4 Tabular ML Engine (M8)
- **Input Object**: `ModelPrediction` ([backend/app/domain/interfaces.py](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py))
- **Payload Attributes**:
  - `risk_score`: Score scaled $[0.0, 100.0]$.
  - `fraud_probability`: Continuous sigmoid probability $[0.0, 1.0]$.
  - `model_version`: Identifier string (e.g. `xgboost_v1.0.0` or `xgboost_v1.0.0_fallback`).
  - `details`: Metadata dictionary indicating model training status (`model_artifact_loaded: bool`, `status: str`).
- **Contract Characteristics**: Statistical supervised classification over historical transaction profiles.

### 3.5 Graph ML Engine (M9)
- **Input Object**: `ModelPrediction` ([backend/app/domain/interfaces.py](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py))
- **Payload Attributes**:
  - `risk_score`: Score scaled $[0.0, 100.0]$.
  - `fraud_probability`: Continuous raw sigmoid probability $[0.0, 1.0]$.
  - `model_version`: Identifier string (e.g. `graphsage_v1.0.0` or `graphsage_untrained_fallback`).
  - `details`: GNN configuration and training availability metadata.
- **Contract Characteristics**: Inductive neighborhood representation learning.

---

## 4. Signal Normalization Architecture

To ensure that no single modality dominates simply due to arbitrary scale conventions, the `SignalNormalizer` converts each raw signal into a bounded, finite continuous value $s_i \in [0.0, 1.0]$:

### 4.1 Rule Normalization Formula
The rule engine output is normalized using a combination of linear score delta scaling and rule severity floor enforcement:

$$s_{rules} = \max\left(\min\left(\frac{\Delta_{score}}{100.0}, 1.0\right), \text{Floor}(\text{matches})\right)$$

Where severity floors guarantee that critical rule violations are not diluted by a low cumulative delta:
- Any `CRITICAL` rule match: Floor = $0.90$
- Any `HIGH` rule match: Floor = $0.70$
- Any `MEDIUM` rule match: Floor = $0.40$
- `LOW` matches only: Floor = $0.20$
- No matches: Floor = $0.00$

### 4.2 Temporal Normalization Formula
Temporal features are synthesized through a weighted component combination:

$$s_{temporal} = \text{clamp}\left(0.40 \cdot r_{in\_out} + 0.35 \cdot \mathbf{1}_{\text{burst}} + 0.25 \cdot \min\left(\frac{v_{velocity}}{100.0}, 1.0\right), 0.0, 1.0\right)$$

- Rapid In/Out ratio directly reflects classic mule pass-through velocity.
- Burst detection accounts for short-term transaction clustering.
- Velocity score captures aggregate cadence relative to historical baselines.

### 4.3 Graph Intelligence Normalization Formula
Graph topological features capture syndicates and ring patterns:

$$s_{graph} = \text{clamp}\left(0.40 \cdot \mathbf{1}_{\text{cycle}} + 0.25 \cdot \min\left(\frac{N_{dev}}{3.0}, 1.0\right) + 0.20 \cdot \min\left(\frac{N_{ip}}{3.0}, 1.0\right) + 0.15 \cdot \rho_{density}, 0.0, 1.0\right)$$

- Circular routing ($\mathbf{1}_{\text{cycle}} = 1.0$) carries the heaviest single structural weight.
- Shared device / IP infrastructure is scaled to saturation at 3 shared entities.
- Neighborhood density provides local clustering context.

### 4.4 Tabular & Graph Machine Learning Normalization
Both M8 and M9 outputs provide a direct continuous probability:

$$s_{ml} = \begin{cases} \text{clamp}(P(\text{fraud}), 0.0, 1.0) & \text{if active and trained} \\ 0.0 \ (\text{with } \text{is\_available} = \text{False}) & \text{if model unavailable / fallback} \end{cases}$$

---

## 5. Weighting Scheme & Missing Signal Policies

### 5.1 Baseline Weight Configuration
The default baseline weights represent a balanced allocation across detection paradigms:

| Modality | Default Weight ($w_i$) | Rationale |
| :--- | :---: | :--- |
| **Rules Engine (M5)** | **0.25** | Authoritative compliance and explicit fraud pattern detection. |
| **Tabular ML (M8)** | **0.25** | Statistical model across 57 engineered account/transaction features. |
| **Graph Intelligence (M7)**| **0.20** | Explicit structural topology (cycles, shared device rings). |
| **Temporal Intelligence (M6)**| **0.15** | Velocity and rapid structuring dynamics. |
| **Graph ML / GraphSAGE (M9)**| **0.15** | Inductive representation learning over multi-hop neighborhoods. |
| **Total** | **1.00** | Strictly normalized to unit sum. |

### 5.2 Missing Signal Policies

In real-world deployment, certain intelligence engines may be temporarily disabled, uninitialized, or failing to evaluate:

1. **`RENORMALIZE_AVAILABLE` (Default)**:
   Weights of unavailable modalities are redistributed proportionally among available modalities:
   
   $$w_i^{eff} = \frac{w_i}{\sum_{j \in \mathcal{A}} w_j} \quad \forall i \in \mathcal{A}$$
   
   Where $\mathcal{A}$ is the set of available modalities. If an ML model is un-trained or offline, active deterministic rules and graph intelligence seamlessly maintain full 0–100 sensitivity without artificial suppression.

2. **`ZERO_CONTRIBUTION`**:
   The original static weights are retained without modification. Missing signals contribute $0.0$ to the risk sum ($w_i^{eff} = w_i$, but $s_i = 0.0$). This is conservative and produces lower composite scores when engines are missing.

3. **`PENALTY_BASELINE`**:
   Missing signals assume a neutral, cautious baseline risk score (default $0.30$) with effective weights renormalized among all modalities.

### 5.3 Distinguishing Model Unavailability from Genuine Zero Risk
A critical architectural requirement implemented in M10 is distinguishing between:
- A trained model actively evaluating an account as safe ($P(\text{fraud}) = 0.0 \implies \text{is\_available}=\text{True}, s=0.0$).
- A model being offline, un-trained, or using a fallback placeholder ($\text{is\_available}=\text{False}$).

Under `RENORMALIZE_AVAILABLE`, genuine safe evaluations actively lower the composite score, whereas unavailable models are excluded from the denominator so they neither increase nor decrease the score artificially.

---

## 6. Composite Score & Risk Classification

### 6.1 Composite Score Formulation
The final composite risk score $S \in [0.0, 100.0]$ is computed as:

$$S = 100.0 \times \sum_{i \in \mathcal{M}} \left(w_i^{eff} \cdot s_i\right)$$

Where:
- $\mathcal{M}$ is the set of evaluated modalities.
- $w_i^{eff}$ is the effective weight satisfying $\sum_{i \in \mathcal{M}} w_i^{eff} = 1.0$ (when at least one modality is available).
- $s_i \in [0.0, 1.0]$ is the normalized risk signal.

### 6.2 Deterministic Risk Tiers
Tiers are assigned monotonically via configurable `RiskThresholds`:

| Risk Tier | Score Range | Operational Meaning |
| :--- | :---: | :--- |
| **`LOW`** | $[0.0, 30.0]$ | Normal account behavior; auto-cleared without SOC alert. |
| **`MEDIUM`** | $(30.0, 65.0]$ | Anomalous behavior; eligible for batch review or soft friction. |
| **`HIGH`** | $(65.0, 85.0]$ | Strong fraud indicators; immediate investigator review required. |
| **`CRITICAL`** | $(85.0, 100.0]$ | Severe multi-modal collusion/mule activity; immediate transaction hold. |

---

## 7. Double-Counting Analysis & Calibration Disclaimer

### 7.1 Double-Counting Analysis
Because the Tabular ML model (M8) and Graph ML model (M9) ingest features derived from Temporal (M6) and Graph (M7) pipelines, their predictions are not statistically orthogonal. 

- The Risk Fusion weighting scheme represents an **operational heuristic allocation**, not an assumption of statistical independence or naive Bayes conditional independence.
- Modality contributions are explicitly displayed as separate decomposition terms, giving investigators full visibility into both the raw heuristic drivers and the predictive model outputs.

### 7.2 Calibration Limitations
- The composite risk score $S$ is a **heuristic risk index**, not a statistically calibrated Bayesian posterior probability of default or criminal culpability.
- The score does not constitute statutory or regulatory clearance under FCRA or BSA/AML rules. Threshold adjustments must be validated against institutional risk tolerance and back-tested against labeled audit cohorts.

---

## 8. Invariants and Architectural Guarantees

Milestone 10 enforces sixteen formal architectural invariants (`INV-1` through `INV-16`), verified continuously by automated unit and property tests:

- **`INV-1`**: Composite risk score is strictly bounded in $[0.0, 100.0]$.
- **`INV-2`**: Output is fully deterministic given identical inputs and configuration.
- **`INV-3`**: Normalization maps all modalities strictly into $[0.0, 1.0]$.
- **`INV-4`**: Configured fusion weights strictly sum to $1.0 \pm 10^{-6}$.
- **`INV-5`**: Rejection of negative, NaN, infinite, or all-zero weights.
- **`INV-6`**: Monotonic risk classification (`low_max < medium_max < high_max`).
- **`INV-7`**: Signal contributions sum exactly to the composite risk score.
- **`INV-8`**: Handled missing signals gracefully without exceptions.
- **`INV-9`**: Distinction between genuine 0.0 prediction and unavailable model.
- **`INV-10`**: Immutable inputs and outputs (dataclasses `frozen=True`).
- **`INV-11`**: Additive-only integration; zero modifications to M1–M9 contracts.
- **`INV-12`**: Modality outputs (M5–M9) preserved exactly as passed.
- **`INV-13`**: No duplicate domain business logic reimplemented in M10.
- **`INV-14`**: Strict boundary: no M11 evidence narrative or path traversal in M10.
- **`INV-15`**: Zero AWS cloud dependencies (`boto3`, Lambda, Neptune, etc.).
- **`INV-16`**: Full backward compatibility with existing application routes.
