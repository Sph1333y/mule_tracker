# MuleTrace AI — Milestone 10 Execution Report
## Risk Fusion Subsystem

> **Project**: MuleTrace AI — AWS First Commit Hackathon  
> **Milestone**: M10 — Risk Fusion  
> **Status**: COMPLETED & VERIFIED  
> **Lead Architect**: Principal AI/ML Architect, Senior Fraud-Detection Engineer & Senior Backend Engineer  
> **Date**: September 19, 2026  

---

## 1. Status

- **Milestone Code**: `M10`
- **Milestone Title**: `Risk Fusion Subsystem`
- **Subsystem Path**: [`backend/app/engines/risk_fusion/`](file:///D:/Team_Cipher_Unit/backend/app/engines/risk_fusion/)
- **Test Suite Path**: [`backend/tests/engines/risk_fusion/`](file:///D:/Team_Cipher_Unit/backend/tests/engines/risk_fusion/)
- **Execution State**: **PASSED 100% (45 / 45 tests passing)**
- **System Regression State**: **ZERO REGRESSIONS (371 passed, 2 failed baseline, 1 skipped)**
- **Baseline Integrity**: M1–M9 contracts, databases, dependencies, and application flows fully preserved.

---

## 2. Baseline Before M10

Before starting Milestone 10, the complete system test suite and application endpoints were measured to establish the immutable baseline:

- **Pytest Suite Baseline**:
  - `326 passed`
  - `2 failed` (Pre-existing baseline failures: `backend/tests/test_config.py::test_postgres_dsn_computation` due to local test URL format; `backend/tests/test_dashboard.py::test_get_dashboard_overview` due to uninitialized mock DB session)
  - `1 skipped`
  - Total test count: `329 tests`
- **Federated Test Runner**:
  - `python backend/tests/run_federated_tests.py`: **5 / 5 passed (100% clean)**
- **FastAPI Endpoints**:
  - `GET /`: `200 OK`
  - `GET /api/v1/health`: `200 OK`
  - `GET /api/v1/graph`: `200 OK`
- **Frontend State**:
  - Next.js build clean with 4 pre-existing TypeScript/ESLint warnings in `src/lib/api.ts`.

---

## 3. Repository Audit

Prior to implementation, all existing engine directories and domain interfaces were audited:

- `backend/app/domain/interfaces.py`: Defines core domain ports (`GraphRepository`, `RuleEngineService`, `FeatureExtractorService`, `ModelService`, `ExplanationService`, `AlertService`) and transfer models (`TransactionEvent`, `ModelPrediction`).
- `backend/app/engines/rules/`: Modular 14-rule engine (`RuleEngine`, `RuleEvaluationResult`, `RuleMatch`).
- `backend/app/engines/temporal/`: Temporal sliding-window engine (`TemporalEngine`, `TemporalFeatures`).
- `backend/app/engines/graph/intelligence/`: Topological graph features (`GraphIntelligenceEngine`, `GraphFeatures`).
- `backend/app/engines/ml/tabular/`: XGBoost/AutoGluon tabular service (`TabularMLService`, `ModelPrediction`).
- `backend/app/engines/ml/graph/`: Inductive GraphSAGE GNN service (`GraphSAGEMulService`, `ModelPrediction`).

All five intelligence modules operate deterministically and return rich structured outputs ready for fusion.

---

## 4. M10 Objective

The objective of Milestone 10 is to implement a modular, cloud-agnostic, deterministic **Risk Fusion Subsystem** that synthesizes the independent fraud signals from M5, M6, M7, M8, and M9 into a composite risk score $[0.0, 100.0]$ and an actionable risk tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), accompanied by mathematical contribution attribution.

Key non-negotiables:
- Pure Python and NumPy/standard library algorithms.
- Zero external cloud SDKs or AWS dependencies (`boto3`, Lambda, Neptune, etc.).
- Zero database schema migrations or state mutations.
- Zero frontend modifications.
- Zero post-processing heuristic corruption of underlying M5–M9 outputs.
- Distinction between an unavailable model and a genuine 0.0 risk prediction.
- Strict isolation from M11 (no evidence graph walking, no SAR generation, no investigator copilot).

---

## 5. Signal Contract Audit (M5, M6, M7, M8, M9)

The signal contracts consumed by Risk Fusion are:

1. **M5 (14 Rules)**:
   - Contract: `RuleEvaluationResult`
   - Key Fields: `total_score_delta: float`, `matches: List[RuleMatch]`
   - Nature: Deterministic compliance, structuring, threshold detection.
2. **M6 (Temporal Intelligence)**:
   - Contract: `TemporalFeatures`
   - Key Fields: `rapid_in_out_ratio: float`, `burst_detected: bool`, `velocity_score: float`, `tx_count_1h: int`
   - Nature: Flow velocity, pass-through speed, burst frequency.
3. **M7 (Graph Intelligence)**:
   - Contract: `GraphFeatures`
   - Key Fields: `cycle_detected: bool`, `shared_device_count: int`, `shared_ip_count: int`, `fan_in_ratio: float`, `fan_out_ratio: float`, `neighborhood_density: float`
   - Nature: Topological cycles, shared infrastructure, syndicate clustering.
4. **M8 (Tabular ML / XGBoost)**:
   - Contract: `ModelPrediction`
   - Key Fields: `risk_score: float`, `fraud_probability: float`, `model_version: str`, `details: Dict[str, Any]`
   - Nature: Supervised gradient boosting over 57-dimensional account/transaction feature schema.
5. **M9 (Graph ML / GraphSAGE)**:
   - Contract: `ModelPrediction`
   - Key Fields: `risk_score: float`, `fraud_probability: float`, `model_version: str`, `details: Dict[str, Any]`
   - Nature: Inductive neighborhood representation learning over dynamic transaction graphs.

---

## 6. Fusion Input Model

Implemented in [`backend/app/engines/risk_fusion/models.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/risk_fusion/models.py):

```python
@dataclass(frozen=True)
class FusionInput:
    transaction_id: str
    rules_result: Optional[RuleEvaluationResult] = None
    temporal_features: Optional[TemporalFeatures] = None
    graph_features: Optional[GraphFeatures] = None
    tabular_prediction: Optional[ModelPrediction] = None
    graph_prediction: Optional[ModelPrediction] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

- **Immutability**: `frozen=True` guarantees that input objects cannot be accidentally mutated during fusion.
- **Graceful Optionality**: Every modality is optional (`None` by default), permitting partial or staggered evaluations.
- **Auditing**: `active_modalities` property provides immediate inspection of present signals.

---

## 7. Signal Normalization

Implemented in [`backend/app/engines/risk_fusion/normalizers.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/risk_fusion/normalizers.py):

The `SignalNormalizer` maps each heterogeneous modality into a bounded, finite continuous value $s_i \in [0.0, 1.0]$:

- **Rules Normalizer**:
  - $s_{rules} = \max\left(\min\left(\frac{\Delta_{score}}{100.0}, 1.0\right), \text{Floor}(\text{matches})\right)$
  - Severity Floors: `CRITICAL` $\implies 0.90$, `HIGH` $\implies 0.70$, `MEDIUM` $\implies 0.40$, `LOW` $\implies 0.20$, No matches $\implies 0.00$.
- **Temporal Normalizer**:
  - $s_{temporal} = \text{clamp}(0.40 \cdot r_{in\_out} + 0.35 \cdot \mathbf{1}_{burst} + 0.25 \cdot \min(v_{vel}/100.0, 1.0), 0.0, 1.0)$
- **Graph Intelligence Normalizer**:
  - $s_{graph} = \text{clamp}(0.40 \cdot \mathbf{1}_{cycle} + 0.25 \cdot \min(N_{dev}/3.0, 1.0) + 0.20 \cdot \min(N_{ip}/3.0, 1.0) + 0.15 \cdot \rho_{density}, 0.0, 1.0)$
- **Tabular ML & Graph ML Normalizers**:
  - $s_{ml} = \text{clamp}(P(\text{fraud}), 0.0, 1.0)$ when model is active and trained.
  - Returns `is_available=False` if `model_version` contains `_fallback` or `details["status"] == "model_unavailable"`.
- **Sanitization**: All calculations pass through `_sanitize_float()` ensuring no `NaN` or `Inf` can ever escape.

---

## 8. Fusion Weights

Implemented in [`backend/app/engines/risk_fusion/weights.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/risk_fusion/weights.py):

- **Baseline Allocation**:
  - `rules`: **0.25**
  - `tabular_ml`: **0.25**
  - `graph`: **0.20**
  - `temporal`: **0.15**
  - `graph_ml`: **0.15**
- **Strict Validation**:
  - Rejects negative weights (`ValueError`).
  - Rejects `NaN` and `Inf` weights (`ValueError`).
  - Rejects all-zero weights (`ValueError`).
  - Auto-normalizes custom weights to ensure $\sum w_i = 1.0$.

---

## 9. Missing Signal Policy

Implemented in [`backend/app/engines/risk_fusion/fusion_engine.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/risk_fusion/fusion_engine.py):

Supported policies via `MissingSignalPolicy`:
1. **`RENORMALIZE_AVAILABLE` (Default)**:
   - Calculates total configured weight of available signals: $W_{avail} = \sum_{j \in \mathcal{A}} w_j$.
   - Effective weights: $w_i^{eff} = w_i / W_{avail}$.
   - Unavailable signals receive $w_k^{eff} = 0.0$.
   - Preserves dynamic 0–100 sensitivity even when ML models are offline.
2. **`ZERO_CONTRIBUTION`**:
   - Effective weights equal configured weights ($w_i^{eff} = w_i$).
   - Unavailable signals contribute 0.0 risk points.
3. **`PENALTY_BASELINE`**:
   - Unavailable signals are assigned a default cautious baseline risk ($0.30$) and evaluated alongside available modalities.

### Distinguishing Missing vs. Zero Risk:
- If an ML model predicts $0.0$ fraud probability while active:
  - `is_available = True`, `normalized_score = 0.0`.
  - The zero risk prediction actively lowers the composite score.
- If an ML model is offline/untrained:
  - `is_available = False`.
  - The model is excluded from the normalization denominator under `RENORMALIZE_AVAILABLE`, preventing dilution.

---

## 10. Fusion Formula

The composite risk score $S \in [0.0, 100.0]$ is computed as:

$$S = 100.0 \times \sum_{i \in \mathcal{M}} \left(w_i^{eff} \cdot s_i\right)$$

Where:
- $s_i \in [0.0, 1.0]$ is the normalized risk signal for modality $i$.
- $w_i^{eff}$ is the normalized effective weight satisfying $\sum_{i \in \mathcal{M}} w_i^{eff} = 1.0$.
- In the edge case where all modalities are unavailable or missing, $S = 0.0$.
- The score is strictly clamped to $[0.0, 100.0]$ and rounded to 4 decimal places.

---

## 11. Risk Classification

Implemented in [`backend/app/engines/risk_fusion/thresholds.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/risk_fusion/thresholds.py):

- **Monotonic Boundary Invariant**:
  $$0.0 < \text{low\_max} < \text{medium\_max} < \text{high\_max} < 100.0$$
- **Default Thresholds**:
  - `low_max`: `30.0`
  - `medium_max`: `65.0`
  - `high_max`: `85.0`
- **Classification Spectrum**:
  - $[0.0, 30.0] \implies$ **`RiskLevel.LOW`**
  - $(30.0, 65.0] \implies$ **`RiskLevel.MEDIUM`**
  - $(65.0, 85.0] \implies$ **`RiskLevel.HIGH`**
  - $(85.0, 100.0] \implies$ **`RiskLevel.CRITICAL`**

---

## 12. Double-Counting Analysis

Because Tabular ML (M8) and Graph ML (M9) ingest features derived in part from Temporal (M6) and Graph (M7) engineering:
- The fusion weights represent an **operational heuristic allocation**, not an assumption of statistical independence.
- The `RiskFusionEngine` does not claim orthogonal Bayesian independence.
- Modality contributions are explicitly disaggregated in `FusionResult.contributions`, allowing compliance officers and fraud analysts to view the exact contribution of each component without opacity.

---

## 13. Calibration Limitations

- The composite risk score is a deterministic **decision-support heuristic index**, not a statistically calibrated Bayesian posterior probability.
- The score does not constitute formal statutory or regulatory clearance under FCRA or BSA/AML rules.
- Production deployment should calibrate operational thresholds against institutional ground-truth fraud cohorts using precision-recall optimization.

---

## 14. FusionResult

Defined in [`backend/app/engines/risk_fusion/models.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/risk_fusion/models.py):

```python
@dataclass(frozen=True)
class FusionResult:
    transaction_id: str
    composite_risk_score: float          # [0.0, 100.0]
    risk_level: RiskLevel                 # LOW, MEDIUM, HIGH, CRITICAL
    policy_applied: MissingSignalPolicy
    contributions: Dict[SignalModality, SignalContribution]
    primary_risk_driver: Optional[SignalModality]
    raw_signals: Dict[SignalModality, NormalizedSignal]
    available_signals_count: int
    missing_signals_count: int
    narrative_summary: str
    metadata: Dict[str, Any]
```

- Immutable, self-contained, and serializable.
- Contains both granular mathematical attribution and normalized raw inputs.

---

## 15. Explainability

Risk Fusion provides mathematical explainability for every evaluation:
- `primary_risk_driver`: The modality that contributed the highest absolute points to the composite score.
- `contributions`: Detailed map for each modality containing:
  - `raw_score`: Original un-normalized metric.
  - `normalized_score`: Value in $[0.0, 1.0]$.
  - `effective_weight`: Scaled weight after missing signal redistribution.
  - `contribution_points`: Absolute score points added ($w_i^{eff} \cdot s_i \times 100$).
  - `contribution_percentage`: Percentage of the composite score explained by this modality.
- `narrative_summary`: Deterministic breakdown string (e.g. `Composite risk score 78.50/100 (HIGH). Primary driver: RULES (25.0 pts, 31.8%).`).

---

## 16. M5 Preservation

- The 14-rule fraud engine (`backend/app/engines/rules/`) was untouched during M10.
- All 14 rule classes (`R001` through `R014`) execute identically.
- `RuleEvaluationResult` and `RuleMatch` objects are ingested read-only.
- All 44 rule-specific tests pass cleanly.

---

## 17. M6 Preservation

- The temporal intelligence engine (`backend/app/engines/temporal/`) was untouched during M10.
- `TemporalEngine` and `TemporalFeatures` data structures remain completely unmodified.
- All 35 temporal tests pass cleanly.

---

## 18. M7 Preservation

- The graph intelligence engine (`backend/app/engines/graph/intelligence/`) was untouched during M10.
- Cycle detection, shared entity counters, and structural metrics continue to operate with 100% fidelity.
- All 41 graph intelligence tests pass cleanly.

---

## 19. M8 Preservation

- Tabular ML pipeline (`backend/app/engines/ml/tabular/`) was untouched during M10.
- 57-dimensional feature extraction, XGBoost adapter, and AutoGluon fallback remain intact.
- All 86 tabular ML tests pass cleanly.

---

## 20. M9 Preservation

- Graph ML pipeline (`backend/app/engines/ml/graph/`) was untouched during M10.
- Native PyTorch GraphSAGE classifier and inductive embedding extractor remain unmodified.
- All 57 Graph ML tests pass cleanly.

---

## 21. M10 Invariants (INV-1 through INV-16)

All sixteen architectural invariants are codified and enforced in [`backend/tests/engines/risk_fusion/test_fusion_invariants.py`](file:///D:/Team_Cipher_Unit/backend/tests/engines/risk_fusion/test_fusion_invariants.py):

| Invariant | Description | Verification Method | Status |
| :--- | :--- | :--- | :---: |
| **`INV-1`** | Composite score bounded in $[0.0, 100.0]$ | Boundary sweep across all permutations | **PASS** |
| **`INV-2`** | 100% deterministic reproducibility | Multiple sequential evaluations on same inputs | **PASS** |
| **`INV-3`** | Normalized signals bounded in $[0.0, 1.0]$ | Extreme input checks (NaN, Inf, negative, huge) | **PASS** |
| **`INV-4`** | Configured weights sum to $1.0 \pm 10^{-6}$ | Unit sum assertion on default & custom weights | **PASS** |
| **`INV-5`** | Non-negative, finite weights only | Rejection tests for negative, NaN, Inf, all-zero | **PASS** |
| **`INV-6`** | Monotonic risk thresholds | Threshold validation tests | **PASS** |
| **`INV-7`** | Contributions sum to composite score | Mathematical equality test ($\pm 0.001$) | **PASS** |
| **`INV-8`** | Graceful handling of missing signals | Empty and partial `FusionInput` tests | **PASS** |
| **`INV-9`** | Distinction between 0.0 and unavailable | Direct test comparing safe prediction vs offline | **PASS** |
| **`INV-10`** | Immutability of inputs and results | `FrozenInstanceError` verification | **PASS** |
| **`INV-11`** | Additive-only integration | Zero schema or existing engine file changes | **PASS** |
| **`INV-12`** | Original outputs preserved | Verification of input objects post-fusion | **PASS** |
| **`INV-13`** | No duplicated domain logic | Architecture AST and code audits | **PASS** |
| **`INV-14`** | No M11 evidence generation in M10 | Code scan for evidence engine logic | **PASS** |
| **`INV-15`** | Zero AWS dependencies | Import scan ensuring no `boto3`, etc. | **PASS** |
| **`INV-16`** | Existing application flow unaffected | Full regression & endpoint verification | **PASS** |

---

## 22. M10 Test Suite

The dedicated M10 test suite comprises 45 tests across 7 test files:

1. [`test_models.py`](file:///D:/Team_Cipher_Unit/backend/tests/engines/risk_fusion/test_models.py): **5 tests** (enums, `NormalizedSignal`, `SignalContribution`, `FusionInput`, `FusionResult` immutability).
2. [`test_weights.py`](file:///D:/Team_Cipher_Unit/backend/tests/engines/risk_fusion/test_weights.py): **6 tests** (defaults, normalization, negative/NaN/Inf/all-zero rejection, lookup).
3. [`test_thresholds.py`](file:///D:/Team_Cipher_Unit/backend/tests/engines/risk_fusion/test_thresholds.py): **5 tests** (monotonicity, deterministic classification, clamp safety, invalid threshold rejection).
4. [`test_normalizers.py`](file:///D:/Team_Cipher_Unit/backend/tests/engines/risk_fusion/test_normalizers.py): **8 tests** (all modality normalizers, severity floors, edge cases, fallback detection).
5. [`test_fusion_engine.py`](file:///D:/Team_Cipher_Unit/backend/tests/engines/risk_fusion/test_fusion_engine.py): **5 tests** (end-to-end evaluation, deterministic score, contribution attribution, singleton).
6. [`test_missing_signals.py`](file:///D:/Team_Cipher_Unit/backend/tests/engines/risk_fusion/test_missing_signals.py): **5 tests** (`RENORMALIZE_AVAILABLE`, `ZERO_CONTRIBUTION`, `PENALTY_BASELINE`, genuine 0.0 vs unavailable, all missing).
7. [`test_fusion_invariants.py`](file:///D:/Team_Cipher_Unit/backend/tests/engines/risk_fusion/test_fusion_invariants.py): **11 tests** (exhaustive automated verification of INV-1 through INV-16).

**Result**: **45 passed, 0 failed in 0.18s**.

---

## 23. Existing Application Verification

1. **Federated Graph Learning Suite**:
   ```
   python backend/tests/run_federated_tests.py
   ALL 5 FEDERATED GRAPH LEARNING TESTS PASSED 100% CLEANLY!
   ```
2. **FastAPI Route Verification**:
   - `GET /` $\implies$ `200 OK`
   - `GET /api/v1/health` $\implies$ `200 OK`
   - `GET /api/v1/graph` $\implies$ `200 OK`

---

## 24. Regression Results

Full pytest regression suite across the entire repository:

- **Baseline (Pre-M10)**: `326 passed, 2 failed, 1 skipped` (329 total)
- **Current (Post-M10)**: `371 passed, 2 failed, 1 skipped` (374 total)
- **Net Change**: **+45 tests passed**
- **New Failures**: **0 (ZERO NEW FAILURES)**
- **Baseline Failures**: Exactly the 2 pre-existing configuration/mock DB tests.

---

## 25. Git Safety Audit

A complete audit of `git status` confirms zero unauthorized modifications:
- Only additive files in `backend/app/engines/risk_fusion/` and `backend/tests/engines/risk_fusion/`.
- Pre-existing modified files in git status (`__init__.py` files in rules, ml, graph) date from earlier approved milestones M5–M9.
- No database migrations, settings alterations, or package configuration modifications were performed.

---

## 26. Known Limitations

1. **Static Default Weights**: Default weights are calibrated based on domain heuristics; production deployments should refine weights via supervised meta-learning (e.g. logistic regression or stacking) on verified fraud datasets.
2. **Synchronous Stateless Computation**: The current fusion engine operates in-memory; high-throughput streaming architectures will benefit from asynchronous batching.
3. **Double-Counting Residuals**: While contributions are cleanly separated, features shared between M6/M7 and M8/M9 naturally exhibit statistical collinearity.

---

## 27. Cloud-Agnostic Architecture

The Risk Fusion subsystem is 100% cloud-agnostic:
- **Build It Phase**: Runs seamlessly on local developer environments, GitHub Actions, Docker, or bare metal without any cloud dependencies.
- **Ship It Phase (AWS Ready)**: Designed for zero-overhead migration into AWS Lambda, Amazon ECS, or Amazon SageMaker Inference endpoints without refactoring business logic.

---

## 28. M10/M11 Boundary

The architectural boundary between Milestone 10 (Risk Fusion) and Milestone 11 (Evidence Engine) is strictly respected:
- **M10 Owns**: Signal ingestion, normalization, weighting, composite scoring, tier classification, and mathematical attribution.
- **M11 Owns**: Natural language SAR synthesis, visual transaction path graph extraction, investigator decision copilot recommendations, and audit storage.
- Milestone 10 contains zero evidence-generation logic, zero LLM prompts, zero graph path traversal routines, and zero investigator workflow state.

---

## 29. Final Decision

All objectives, architectural invariants, code quality standards, and regression thresholds for Milestone 10 have been met.

```
============================================================
FINAL DECISION:
MILESTONE 10 IS READY FOR REVIEW.
============================================================
```
