"""
MuleTrace AI — Tabular ML Edge Case Tests.

Tests boundary conditions, extreme values, unknown channels,
and stress scenarios for tabular machine learning feature generation and inference.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
import pytest
import pandas as pd

from app.domain.models import TransactionEvent
from app.engines.ml.tabular import (
    TABULAR_FEATURE_COLUMNS,
    TabularFeatureBuilder,
    TabularFeatures,
    xgboost_model_service,
)
from app.engines.temporal.temporal_models import TemporalFeatures
from app.engines.graph.intelligence.graph_models import GraphFeatures


def _tx(amt: float = 1000.0, channel: str = "UPI", **kwargs) -> TransactionEvent:
    return TransactionEvent(
        transaction_id="TX-EDGE-1",
        timestamp=datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc),
        amount=amt,
        sender_account="ACC-EDGE-A",
        receiver_account="ACC-EDGE-B",
        channel=channel,
        **kwargs,
    )


def test_extreme_amount_log_scaling():
    """Very large amount (1,000,000,000 INR) computes log_amount smoothly without overflow."""
    event = _tx(amt=1_000_000_000.0)
    builder = TabularFeatureBuilder()
    feat = builder.build_features(event)

    assert feat.amount == 1_000_000_000.0
    assert feat.log_amount == pytest.approx(9.0, abs=1e-2)


def test_sub_rupee_minimum_amount():
    """Minimal amount (0.01 INR) computes log_amount cleanly without division by zero."""
    event = _tx(amt=0.01)
    feat = TabularFeatureBuilder.build_features(event)

    assert feat.amount == 0.01
    assert feat.log_amount >= 0.0


def test_unknown_channel_encoding():
    """Non-standard channels (e.g. 'CRYPTO', 'QR_CODE') fall back to channel_other = 1.0."""
    event = _tx(amt=500.0, channel="CRYPTO")
    feat = TabularFeatureBuilder.build_features(event)

    assert feat.channel_upi == 0.0
    assert feat.channel_neft == 0.0
    assert feat.channel_rtgs == 0.0
    assert feat.channel_imps == 0.0
    assert feat.channel_other == 1.0


def test_corrupted_metadata_resilience():
    """Non-numeric, None, or string metadata values are sanitized to default finite floats."""
    event = _tx(
        amt=1000.0,
        metadata={
            "account_age_days": "invalid_string",
            "velocity_l6h": None,
            "churn_rate": float("nan"),
            "user_risk_score": float("inf"),
        },
    )
    feat = TabularFeatureBuilder.build_features(event)
    vec = feat.to_vector()

    for v in vec:
        assert isinstance(v, (int, float))
        assert not pd.isna(v)
        assert abs(v) != float("inf")


def test_high_intensity_temporal_and_graph_extremes():
    """Massive temporal bursts and high-degree graph features process without overflow."""
    event = _tx(amt=500000.0)
    temp_feat = TemporalFeatures(
        reference_time=datetime.now(timezone.utc),
        transaction_count_1h=5000,
        amount_sum_1h=50_000_000.0,
        burst_count=100,
        activity_change_ratio=99.9,
    )
    graph_feat = GraphFeatures(
        account_id="ACC-EDGE-A",
        in_degree=1500,
        out_degree=2000,
        total_degree=3500,
        cycle_count=25,
        shared_device_count=50,
    )

    feat = TabularFeatureBuilder.build_features(event, temporal_features=temp_feat, graph_features=graph_feat)
    pred = xgboost_model_service.predict_tabular(feat)

    # Validates numerical stability and bounds without artificial score inflation
    assert 0 <= pred.risk_score <= 100
    assert 0.0 <= pred.fraud_probability <= 1.0
    assert isinstance(pred.is_fraud, bool)
