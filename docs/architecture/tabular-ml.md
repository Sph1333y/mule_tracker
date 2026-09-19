# MuleTrace AI — Tabular ML & AutoGluon Architecture

> **Milestone**: M8 — Tabular ML + AutoGluon  
> **Status**: Completed  
> **Target Environment**: BUILD IT Phase (Local Scikit-Learn/XGBoost & Optional AutoGluon Challenger)  
> **Audience**: Principal Architects, Machine Learning Engineers, MLOps Engineers, SOC Developers

---

## 1. Executive Summary & Purpose

Milestone 8 introduces the **Tabular Machine Learning Layer** to MuleTrace AI. Building upon the canonical domain foundation established across M1–M7, M8 synthesizes multi-modal signals into a deterministic, high-dimensional tabular feature representation and exposes model inference through the domain [`ModelService`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py) port.

```
                  Canonical TransactionEvent (M1)
                                │
       ┌────────────────────────┼────────────────────────┐
       ▼                        ▼                        ▼
  RuleEngine (M5)        TemporalEngine (M6)     GraphEngine (M7)
  (14 Rule Signals)       (TemporalFeatures)      (GraphFeatures)
       │                        │                        │
       │                        ▼                        ▼
       │              ┌────────────────────────────────────┐
       │              │    TabularFeatureBuilder (M8)      │
       │              │    - 14 Transaction-Native         │
       │              │    - 14 Telemetry & Risk           │
       │              │    - 12 Temporal Intelligence (M6) │
       │              │    - 17 Graph Intelligence (M7)    │
       │              └─────────────────┬──────────────────┘
       │                                │
       │                                ▼
       │                    TabularFeatures (57 dims)
       │                                │
       │                ┌───────────────┴───────────────┐
       │                ▼                               ▼
       │      XGBoostModelService             AutoGluonModelService
       │      (Baseline / Legacy Adapter)     (Optional Challenger)
       │                │                               │
       │                └───────────────┬───────────────┘
       │                                │
       │                                ▼
       │                    ModelPrediction (Domain Port)
       │                                │
       └────────────────────────────────┼────────────────┘
                                        │
                                        ▼
                             Future RiskFusion (M10)
```

### Key Capabilities Introduced in M8
1. **Multi-Source Feature Synthesis**: Unifies transaction primitives, client telemetry, temporal velocity/burst profiles (M6), and topological graph metrics (M7) into a 57-dimensional canonical schema.
2. **Temporal Leakage Elimination**: Strict chronological train/validation/test partitioning ensuring zero lookahead leakage during training and benchmark evaluation.
3. **Domain Port Compliance**: Fully satisfies the domain [`ModelService`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py) abstraction, outputting structured [`ModelPrediction`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py) domain objects.
4. **Preserved Production Baseline**: Wraps and serves the existing scikit-learn / XGBoost inference pipelines (`rf_classifier_pipeline.pkl`, `rf_regressor_pipeline.pkl`) without post-prediction distortion or disruption.
5. **Optional Challenger Architecture**: Provides an isolated `AutoGluonModelService` designed to benchmark AutoML performance without making AutoGluon a mandatory runtime dependency (critical for platforms such as Python 3.14 on Windows where AutoGluon binary wheels are unavailable).

---

## 2. Architectural Principles & Safety Invariants

### 2.1 Zero Startup Training
Model training must **NEVER** execute during application startup or within request handler lifecycles. All inference is strictly offline-trained or relies on pre-trained pipeline artifacts loaded safely from disk or default inference fallbacks.

### 2.2 Strict Chronological Splitting (No Temporal Leakage)
Financial transaction fraud detection suffers severely from temporal leakage if random K-fold splits are applied. In M8:
- All training and evaluation datasets are sorted strictly by `timestamp` ascending.
- Splits are sliced sequentially:
  $$\text{Train } (70\%) \longrightarrow \text{Validation } (15\%) \longrightarrow \text{Test } (15\%)$$
- Future transactions never inform historical feature scaling, imputation, or model tuning.

### 2.3 NaN and Inf Immunity
Production transaction payloads frequently contain missing values, division-by-zero risk ratios, or unobserved telemetry. M8 guarantees mathematical safety:
- All numeric features pass through `sanitize_numeric(val, default=0.0)`.
- Infinite values (`float('inf')`, `float('-inf')`) and `NaN` are scrubbed before reaching any inference engine or downstream consumer.

### 2.4 Additive & Non-Breaking Design
- The existing [`backend/app/engines/ml/xgboost_model.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/ml/xgboost_model.py) and [`MLEngine`](file:///D:/Team_Cipher_Unit/backend/app/engines/ml/xgboost_model.py) remain 100% untouched and functional.
- The existing Next.js frontend, FastAPI endpoints, and PostgreSQL schemas remain unaffected.

---

## 3. Canonical Tabular Feature Catalog

The canonical feature matrix defined in [`backend/app/engines/ml/tabular/feature_schema.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/ml/tabular/feature_schema.py) consists of **57 ordered features** across four distinct operational dimensions:

| Feature Category | Dim | Key Fields | Extraction Source |
| :--- | :---: | :--- | :--- |
| **1. Transaction-Native** | 14 | `amount`, `hour_of_day`, `day_of_week`, `is_weekend`, `log_amount`, `channel_web`, `channel_mobile`, `channel_atm`, `channel_pos`, `channel_upi`, `is_high_value`, `is_night_transaction`, `is_round_amount`, `is_cross_border` | `TransactionEvent` core fields and payload metadata |
| **2. Telemetry & Context** | 14 | `device_trust_score`, `location_risk_score`, `behavioral_anomaly_score`, `ip_reputation_score`, `sender_account_age_days`, `receiver_account_age_days`, `sender_balance_prior`, `receiver_balance_prior`, `balance_change_ratio`, `is_new_device`, `is_vpn_or_proxy`, `failed_logins_24h`, `distance_from_home_km`, `user_velocity_1h` | Client telemetry, device fingerprinting, user metadata |
| **3. Temporal Intelligence** | 12 | `burst_velocity`, `time_since_last_tx_sec`, `sender_velocity_1h`, `sender_velocity_24h`, `receiver_velocity_1h`, `receiver_velocity_24h`, `burst_flag`, `dormant_reactivation`, `frequency_surge_ratio`, `accelerated_drain`, `rapid_movement`, `flow_symmetry` | Milestone 6 `TemporalFeatures` container |
| **4. Graph Intelligence** | 17 | `in_degree`, `out_degree`, `total_degree`, `unique_senders_count`, `unique_receivers_count`, `fan_in_ratio`, `fan_out_ratio`, `neighborhood_density`, `has_cycle`, `cycle_count`, `shared_device_count`, `shared_ip_count`, `reachable_node_count`, `max_path_length`, `subgraph_node_count`, `subgraph_edge_count`, `inbound_to_outbound_ratio` | Milestone 7 `GraphFeatures` container |

### Feature Alignment & Vectorization
Every [`TabularFeatures`](file:///D:/Team_Cipher_Unit/backend/app/engines/ml/tabular/feature_schema.py) instance guarantees three interoperable views:
- **`to_dict()`**: Typed Python dictionary with 57 key-value pairs.
- **`to_vector()`**: 57-element floating-point list in strict schema order.
- **`to_dataframe()`**: Single-row Pandas `DataFrame` conforming to `TABULAR_FEATURE_COLUMNS`.

---

## 4. Dataset Building & Validation Strategy

The [`TabularDatasetBuilder`](file:///D:/Team_Cipher_Unit/backend/app/engines/ml/tabular/dataset_builder.py) manages training set preparation from historical tabular data (such as `ml/transactions.csv`):

```python
builder = TabularDatasetBuilder()
X_train, X_val, X_test, y_train, y_val, y_test = builder.split_chronological(
    df,
    target_column="is_fraud",
    train_ratio=0.70,
    val_ratio=0.15,
    test_ratio=0.15,
)
```

### Comprehensive Model Evaluation Metrics
Evaluation routines in `TabularDatasetBuilder.evaluate_classification` generate production-grade telemetry:
- **Classification**: Precision, Recall, F1-Score, PR-AUC (Average Precision), ROC-AUC, Brier Score, and Confusion Matrix ($TP, FP, TN, FN$).
- **Regression**: Mean Absolute Error (MAE), Mean Squared Error (MSE), Root Mean Squared Error (RMSE).

---

## 5. Model Adapters & ModelService Port

M8 introduces the [`backend/app/engines/ml/tabular/model_adapter.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/ml/tabular/model_adapter.py) hierarchy implementing the domain `ModelService` interface:

```
                  ModelService (Domain Port)
                              │
                      BaseModelAdapter
                              ├── XGBoostModelService
                              └── AutoGluonModelService
```

### 5.1 `XGBoostModelService`
- Integrates directly with existing production pipelines (`rf_classifier_pipeline.pkl` and `rf_regressor_pipeline.pkl`).
- Accepts raw `TransactionEvent` along with optional `TemporalFeatures` and `GraphFeatures`.
- **Pure Model Output Preservation**: Generates predictions from the underlying model pipeline and preserves raw model outputs with **ZERO** post-prediction score modulation or heuristic adjustments.
- Temporal and graph features influence inference exclusively as inputs into `TabularFeatures`, never via post-hoc score additions.
- Emits standard [`ModelPrediction`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py) objects containing:
  - `risk_score`: Raw model predicted score (0 to 100)
  - `fraud_probability`: Raw model predicted probability ($0.0 \dots 1.0$)
  - `is_fraud`: Raw model classification verdict
  - `model_version`: Model identifier string
  - `details`: Metadata including `raw_predicted_score`, `raw_fraud_probability`, and `underlying_model`

### 5.2 `AutoGluonModelService` (Challenger Adapter)
AutoGluon serves as an automated machine learning benchmark. Because AutoGluon binary wheels may be unavailable in specific deployment environments (e.g. Python 3.14 on Windows), M8 implements a robust **Optional Dependency Pattern**:
- **Environment Isolation**: No top-level `import autogluon` calls that could crash application startup.
- **Dynamic Probing**: `is_autogluon_available()` safely inspects module availability via `importlib.util.find_spec`.
- **Independent Inference**: Operates without external heuristic or risk fusion adjustments.
- **Automatic Fallback**: If AutoGluon is unavailable or un-trained, the challenger gracefully delegates inference to the baseline `XGBoostModelService`, annotating the prediction metadata with:
  ```json
  {
    "autogluon_available": false,
    "challenger_status": "fallback_to_xgboost"
  }
  ```

---

## 6. Architectural Invariants Compliance Checklist

The corrected M8 Tabular ML layer strictly enforces the 10 non-negotiable architectural invariants:

| Invariant | Description | Verification Test | Status |
| :---: | :--- | :--- | :---: |
| **INV-1** | ML output equals the underlying model output after valid model inference | `test_inv1_ml_output_equals_underlying_model` | ✅ Compliant |
| **INV-2** | TemporalFeatures influence ML only through model input features | `test_inv2_temporal_features_influence_only_via_input` | ✅ Compliant |
| **INV-3** | GraphFeatures influence ML only through model input features | `test_inv3_graph_features_influence_only_via_input` | ✅ Compliant |
| **INV-4** | No post-prediction temporal risk adjustment exists | `test_inv4_no_post_prediction_temporal_risk_adjustment` | ✅ Compliant |
| **INV-5** | No post-prediction graph risk adjustment exists | `test_inv5_no_post_prediction_graph_risk_adjustment` | ✅ Compliant |
| **INV-6** | RiskFusion is not implemented in M8 | `test_inv6_risk_fusion_not_implemented_in_m8` | ✅ Compliant |
| **INV-7** | ModelPrediction remains compatible with domain port | `test_inv7_model_prediction_compatible_with_domain_port` | ✅ Compliant |
| **INV-8** | AutoGluon remains optional | `test_inv8_autogluon_remains_optional` | ✅ Compliant |
| **INV-9** | FastAPI startup never trains models | `test_inv9_fastapi_startup_never_trains_models` | ✅ Compliant |
| **INV-10** | Existing application behavior remains unchanged | `test_inv10_existing_application_behavior_unchanged` | ✅ Compliant |

---

## 7. Explicit Boundary with Milestone 10 (Risk Fusion)

M8 maintains a strict separation of concerns from future Milestone 10:

```
┌─────────────────────────────────────────────────────────────┐
│                    MILESTONE 8 (Tabular ML)                 │
│                                                             │
│   Input Features (57-D) ───► Model Pipeline ───► ModelPrediction │
│   (Zero post-hoc heuristics, zero external score modulation)│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 MILESTONE 10 (Future Risk Fusion)           │
│                                                             │
│   Rule Signals (M5)                                         │
│   + Temporal Features (M6)                                  │
│   + Graph Features (M7)                                     │
│   + Tabular ML Prediction (M8)                              │
│   + Graph ML Prediction (M9)                                │
│   ───────────────────────────────────────────────────────── │
│   ===> Composite Risk Score & Fusion Verdict                │
└─────────────────────────────────────────────────────────────┘
```
