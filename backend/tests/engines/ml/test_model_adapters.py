"""
MuleTrace AI — Tabular Model Adapter Unit Tests.

Validates ModelService interface compliance, ModelPrediction output contracts,
and integration with existing XGBoost / Random Forest engines.
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from app.domain.interfaces import ModelPrediction, ModelService
from app.domain.models import TransactionEvent
from app.engines.ml.tabular.feature_schema import TabularFeatures
from app.engines.ml.tabular.xgboost_adapter import XGBoostModelService, xgboost_model_service
from app.engines.temporal.temporal_models import TemporalFeatures
from app.engines.graph.intelligence.graph_models import GraphFeatures


def _sample_event(amount: float = 45000.0) -> TransactionEvent:
    return TransactionEvent(
        transaction_id="TX-ADAPT-1",
        timestamp=datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc),
        amount=amount,
        sender_account="ACC-TEST-1",
        receiver_account="ACC-TEST-2",
        channel="UPI",
        sender_bank="State Bank of India",
        receiver_bank="HDFC Bank",
        device_id="DEV-001",
        ip_address="10.0.0.1",
        metadata={
            "user_risk_score": 60.0,
            "device_risk_score": 50.0,
            "is_vpn_or_proxy": 1,
        },
    )


def test_xgboost_adapter_implements_model_service():
    """XGBoostModelService must be an instance of domain ModelService port."""
    adapter = XGBoostModelService()
    assert isinstance(adapter, ModelService)


def test_predict_risk_returns_valid_model_prediction():
    """predict_risk generates a compliant ModelPrediction contract."""
    event = _sample_event(amount=35000.0)
    pred = xgboost_model_service.predict_risk(event)

    assert isinstance(pred, ModelPrediction)
    assert 0 <= pred.risk_score <= 100
    assert 0.0 <= pred.fraud_probability <= 1.0
    assert isinstance(pred.is_fraud, bool)
    assert isinstance(pred.model_version, str)
    assert isinstance(pred.details, dict)
    assert "model_name" in pred.details


def test_predict_without_score_modulation():
    """Underlying model output is preserved directly without post-prediction score modulation."""
    event = _sample_event(amount=5000.0)

    # Baseline prediction without anomalies
    pred_base = xgboost_model_service.predict_risk(event)

    # Context with topological cycle (M7) and temporal burst (M6)
    temp_feat = TemporalFeatures(
        reference_time=datetime.now(timezone.utc),
        burst_detected=True,
        rapid_in_out_detected=True,
    )
    graph_feat = GraphFeatures(
        account_id="ACC-TEST-1",
        has_cycle=True,
        cycle_count=1,
    )

    pred_with_context = xgboost_model_service.predict_risk(
        event=event,
        temporal_features=temp_feat,
        graph_features=graph_feat,
    )

    # In M8, features enter via input vector; no post-prediction score additions occur
    assert pred_with_context.risk_score == pred_base.risk_score
    assert pred_with_context.fraud_probability == pred_base.fraud_probability
    assert pred_with_context.is_fraud == pred_base.is_fraud
    assert pred_with_context.details.get("raw_predicted_score") == pred_base.risk_score


def test_predict_tabular_direct_evaluation():
    """predict_tabular evaluates a pre-constructed TabularFeatures vector."""
    features = TabularFeatures(
        amount=75000.0,
        log_amount=4.875,
        channel_upi=1.0,
        user_risk_score=80.0,
        is_vpn_or_proxy=1.0,
    )
    pred = xgboost_model_service.predict_tabular(features)

    assert isinstance(pred, ModelPrediction)
    assert pred.risk_score >= 0
    assert pred.details.get("feature_count") == len(features.to_vector())
