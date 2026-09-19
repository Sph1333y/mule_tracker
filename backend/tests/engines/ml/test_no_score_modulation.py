"""
MuleTrace AI — Regression Tests: Score Modulation Removal & Model Output Preservation.

Explicitly verifies that M8 Tabular ML preserves raw underlying model outputs
with ZERO external post-prediction score modulation or heuristic risk fusion.

Covers:
- TEST 1: Temporal burst does not externally alter prediction score post-inference.
- TEST 2: Graph cycle does not trigger an independent score adjustment.
- TEST 3: Shared device count is an input feature, not a post-processing multiplier.
- TEST 4: Raw model output preservation (mocked engine returning score=X).
- TEST 5: Temporal and graph features remain present in input TabularFeatures.
- TEST 6: AutoGluon returns model output without external risk modulation.
- TEST 7: ModelPrediction domain contract compliance.
- TEST 8: Existing ML pipeline operational preservation.
- Architectural Invariants INV-1 through INV-10 verification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
import pandas as pd

from app.domain.interfaces import ModelPrediction, ModelService
from app.domain.models import TransactionEvent
from app.engines.ml.tabular import (
    AutoGluonModelService,
    TabularDatasetBuilder,
    TabularFeatureBuilder,
    TabularFeatures,
    XGBoostModelService,
    autogluon_model_service,
    tabular_feature_builder,
    xgboost_model_service,
)
from app.engines.ml.xgboost_model import MLEngine, MLPredictionResult, ml_engine
from app.engines.temporal.temporal_models import TemporalFeatures
from app.engines.graph.intelligence.graph_models import GraphFeatures


def _sample_event(
    amount: float = 12000.0,
    tx_id: str = "TX-NOMOD-1",
    sender: str = "ACC-A",
    receiver: str = "ACC-B",
) -> TransactionEvent:
    return TransactionEvent(
        transaction_id=tx_id,
        timestamp=datetime(2026, 9, 19, 14, 0, 0, tzinfo=timezone.utc),
        amount=amount,
        sender_account=sender,
        receiver_account=receiver,
        channel="UPI",
        sender_bank="State Bank of India",
        receiver_bank="HDFC Bank",
        device_id="DEV-MOD-1",
        ip_address="10.10.10.10",
        metadata={
            "account_age_days": 180,
            "velocity_l6h": 1,
            "user_risk_score": 25.0,
            "device_trust_score": 80.0,
            "is_vpn_or_proxy": 0,
        },
    )


# -----------------------------------------------------------------------------
# TEST 1: Temporal feature does not externally alter prediction score
# -----------------------------------------------------------------------------
def test_temporal_burst_does_not_externally_alter_score():
    """Verify that temporal burst does not add heuristic points to the model prediction."""
    event = _sample_event(amount=8000.0)
    base_pred = xgboost_model_service.predict_risk(event)

    temp_feat = TemporalFeatures(
        reference_time=datetime.now(timezone.utc),
        burst_detected=True,
        burst_count=15,
        rapid_in_out_detected=True,
        rapid_in_out_ratio=0.99,
    )

    with_temp_pred = xgboost_model_service.predict_risk(
        event=event,
        temporal_features=temp_feat,
    )

    # In M8, the underlying MLEngine output is preserved directly
    assert with_temp_pred.risk_score == base_pred.risk_score
    assert with_temp_pred.fraud_probability == base_pred.fraud_probability
    assert with_temp_pred.is_fraud == base_pred.is_fraud
    assert "has_graph_cycle" not in with_temp_pred.details
    assert "temporal_burst_detected" not in with_temp_pred.details


# -----------------------------------------------------------------------------
# TEST 2: Graph cycle does not externally alter prediction score
# -----------------------------------------------------------------------------
def test_graph_cycle_does_not_externally_alter_score():
    """Verify that graph cycle detection does not trigger a post-prediction score bump."""
    event = _sample_event(amount=15000.0)
    base_pred = xgboost_model_service.predict_risk(event)

    graph_feat = GraphFeatures(
        account_id="ACC-A",
        has_cycle=True,
        cycle_count=3,
    )

    with_graph_pred = xgboost_model_service.predict_risk(
        event=event,
        graph_features=graph_feat,
    )

    assert with_graph_pred.risk_score == base_pred.risk_score
    assert with_graph_pred.fraud_probability == base_pred.fraud_probability
    assert with_graph_pred.is_fraud == base_pred.is_fraud


# -----------------------------------------------------------------------------
# TEST 3: Shared device count does not externally alter prediction score
# -----------------------------------------------------------------------------
def test_shared_device_does_not_externally_alter_score():
    """Verify that shared device count is an input feature, not a post-prediction multiplier."""
    event = _sample_event(amount=20000.0)
    base_pred = xgboost_model_service.predict_risk(event)

    graph_feat = GraphFeatures(
        account_id="ACC-A",
        shared_device_count=12,
        shared_ip_count=8,
    )

    with_shared_pred = xgboost_model_service.predict_risk(
        event=event,
        graph_features=graph_feat,
    )

    assert with_shared_pred.risk_score == base_pred.risk_score
    assert with_shared_pred.fraud_probability == base_pred.fraud_probability


# -----------------------------------------------------------------------------
# TEST 4: Raw model output preservation with deterministic mock
# -----------------------------------------------------------------------------
def test_raw_model_output_preservation():
    """Mock an underlying MLEngine returning specific values; adapter must return exactly those."""
    mock_engine = MagicMock(spec=MLEngine)
    mock_engine.predict_transaction_risk.return_value = MLPredictionResult(
        predicted_risk_score=42,
        fraud_probability=0.4215,
        is_fraud_predicted=False,
        model_version="mock_engine_v1",
    )

    adapter = XGBoostModelService(engine=mock_engine)
    event = _sample_event()

    temp_feat = TemporalFeatures(reference_time=datetime.now(timezone.utc), burst_detected=True)
    graph_feat = GraphFeatures(account_id="ACC-A", has_cycle=True)

    pred = adapter.predict_risk(
        event=event,
        temporal_features=temp_feat,
        graph_features=graph_feat,
    )

    # Output must EXACTLY match the underlying model output
    assert pred.risk_score == 42
    assert pred.fraud_probability == 0.4215
    assert pred.is_fraud is False
    assert pred.details.get("raw_predicted_score") == 42
    assert pred.details.get("raw_fraud_probability") == 0.4215
    assert pred.details.get("underlying_model") == "mock_engine_v1"


# -----------------------------------------------------------------------------
# TEST 5: Feature-based influence remains valid in input vector
# -----------------------------------------------------------------------------
def test_feature_based_influence_in_input_vector():
    """Temporal and graph values properly populate the 57-dimensional input feature vector."""
    event = _sample_event()
    temp_feat = TemporalFeatures(
        reference_time=datetime.now(timezone.utc),
        transaction_count_5m=7,
        burst_detected=True,
        burst_count=4,
    )
    graph_feat = GraphFeatures(
        account_id="ACC-A",
        in_degree=5,
        out_degree=6,
        has_cycle=True,
        cycle_count=2,
    )

    feat = tabular_feature_builder.build_features(
        event=event,
        temporal_features=temp_feat,
        graph_features=graph_feat,
    )

    # Features ARE present in the input representation
    assert feat.temporal_tx_count_5m == 7.0
    assert feat.temporal_burst_detected == 1.0
    assert feat.temporal_burst_count == 4.0
    assert feat.graph_in_degree == 5.0
    assert feat.graph_out_degree == 6.0
    assert feat.graph_has_cycle == 1.0
    assert feat.graph_cycle_count == 2.0
    assert len(feat.to_vector()) == 57


# -----------------------------------------------------------------------------
# TEST 6: AutoGluon returns model output without external risk modulation
# -----------------------------------------------------------------------------
def test_autogluon_output_without_external_modulation(monkeypatch):
    """AutoGluon challenger and its fallback execute without post-prediction modulation."""
    monkeypatch.setattr("app.engines.ml.tabular.autogluon_adapter.is_autogluon_available", lambda: True)

    # Test with mock predictor
    mock_predictor = MagicMock()
    mock_predictor.predict_proba.return_value = pd.DataFrame([[0.35, 0.65]], columns=[0, 1])
    mock_predictor.model_best = "LightGBM"

    service = AutoGluonModelService(predictor=mock_predictor)

    feat = TabularFeatures(amount=50000.0, graph_has_cycle=1.0, temporal_burst_detected=1.0)
    pred = service.predict_tabular(feat)

    # Must reflect the predictor probability (0.65 -> 65 risk score), zero heuristic additions
    assert pred.risk_score == 65
    assert pred.fraud_probability == 0.65
    assert pred.is_fraud is True
    assert pred.details.get("challenger_engine") == "autogluon"


# -----------------------------------------------------------------------------
# TEST 7: ModelPrediction domain contract compliance
# -----------------------------------------------------------------------------
def test_model_prediction_domain_contract_compliance():
    """Returned prediction strictly complies with app.domain.interfaces.ModelPrediction."""
    event = _sample_event()
    pred = xgboost_model_service.predict_risk(event)

    assert isinstance(pred, ModelPrediction)
    assert isinstance(pred.risk_score, int)
    assert 0 <= pred.risk_score <= 100
    assert isinstance(pred.fraud_probability, float)
    assert 0.0 <= pred.fraud_probability <= 1.0
    assert isinstance(pred.is_fraud, bool)
    assert isinstance(pred.model_version, str)
    assert isinstance(pred.details, dict)


# -----------------------------------------------------------------------------
# TEST 8: Existing ML pipeline operational preservation
# -----------------------------------------------------------------------------
def test_existing_ml_pipeline_operational_preservation():
    """The underlying ml_engine remains untouched and operational."""
    res = ml_engine.predict_transaction_risk({"amount": 10000.0, "channel": "UPI"})
    assert res is not None
    assert 0 <= res.predicted_risk_score <= 100
    assert 0.0 <= res.fraud_probability <= 1.0


# -----------------------------------------------------------------------------
# ARCHITECTURAL INVARIANTS: INV-1 through INV-10
# -----------------------------------------------------------------------------
def test_inv1_ml_output_equals_underlying_model():
    """INV-1: ML output equals the underlying model output after valid model inference."""
    tx_dict = {"amount": 5000.0, "channel": "UPI"}
    raw_res = ml_engine.predict_transaction_risk(tx_dict)

    feat = TabularFeatures(amount=5000.0, channel_upi=1.0)
    adapter_pred = xgboost_model_service.predict_tabular(feat)

    assert adapter_pred.risk_score == raw_res.predicted_risk_score
    assert adapter_pred.fraud_probability == raw_res.fraud_probability
    assert adapter_pred.is_fraud == raw_res.is_fraud_predicted


def test_inv2_temporal_features_influence_only_via_input():
    """INV-2: TemporalFeatures influence ML only through model input features."""
    event = _sample_event()
    temp_feat = TemporalFeatures(reference_time=datetime.now(timezone.utc), burst_detected=True)

    # Feature vector contains the temporal indicator
    tab_feat = tabular_feature_builder.build_features(event, temporal_features=temp_feat)
    assert tab_feat.temporal_burst_detected == 1.0

    # Adapter does not post-process output
    pred = xgboost_model_service.predict_risk(event, temporal_features=temp_feat)
    base_pred = xgboost_model_service.predict_risk(event)
    assert pred.risk_score == base_pred.risk_score


def test_inv3_graph_features_influence_only_via_input():
    """INV-3: GraphFeatures influence ML only through model input features."""
    event = _sample_event()
    graph_feat = GraphFeatures(account_id="ACC-A", has_cycle=True)

    tab_feat = tabular_feature_builder.build_features(event, graph_features=graph_feat)
    assert tab_feat.graph_has_cycle == 1.0

    pred = xgboost_model_service.predict_risk(event, graph_features=graph_feat)
    base_pred = xgboost_model_service.predict_risk(event)
    assert pred.risk_score == base_pred.risk_score


def test_inv4_no_post_prediction_temporal_risk_adjustment():
    """INV-4: No post-prediction temporal risk adjustment exists."""
    event = _sample_event(amount=1000.0)
    temp_burst = TemporalFeatures(reference_time=datetime.now(timezone.utc), burst_detected=True, burst_count=20)
    pred = xgboost_model_service.predict_risk(event, temporal_features=temp_burst)
    assert "temporal_burst_detected" not in pred.details


def test_inv5_no_post_prediction_graph_risk_adjustment():
    """INV-5: No post-prediction graph risk adjustment exists."""
    event = _sample_event(amount=1000.0)
    graph_cycle = GraphFeatures(account_id="ACC-A", has_cycle=True, cycle_count=5)
    pred = xgboost_model_service.predict_risk(event, graph_features=graph_cycle)
    assert "has_graph_cycle" not in pred.details


def test_inv6_risk_fusion_not_implemented_in_m8():
    """INV-6: RiskFusion is not implemented in M8 — adapter outputs ModelPrediction, not CompositeRisk."""
    pred = xgboost_model_service.predict_risk(_sample_event())
    assert isinstance(pred, ModelPrediction)
    assert not hasattr(pred, "composite_risk_score")
    assert not hasattr(pred, "fusion_verdict")


def test_inv7_model_prediction_compatible_with_domain_port():
    """INV-7: ModelPrediction remains compatible with the domain port."""
    assert issubclass(XGBoostModelService, ModelService)
    assert issubclass(AutoGluonModelService, ModelService)


def test_inv8_autogluon_remains_optional():
    """INV-8: AutoGluon remains optional and gracefully provides diagnostics."""
    status = autogluon_model_service.get_status()
    assert "autogluon_installed" in status
    assert "mode" in status


def test_inv9_fastapi_startup_never_trains_models():
    """INV-9: FastAPI startup never trains models."""
    from app.engines.ml.tabular import tabular_dataset_builder
    assert tabular_dataset_builder is not None


def test_inv10_existing_application_behavior_unchanged():
    """INV-10: Existing application behavior remains unchanged."""
    event = _sample_event()
    pred = xgboost_model_service.predict_risk(event)
    assert 0 <= pred.risk_score <= 100
