"""
MuleTrace AI — Tabular Feature Builder Unit Tests.

Tests extraction of TabularFeatures from TransactionEvent, integration
with M6 TemporalFeatures, M7 GraphFeatures, and dictionary-based extraction.
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from app.domain.models import TransactionEvent
from app.engines.ml.tabular.feature_builder import TabularFeatureBuilder, tabular_feature_builder
from app.engines.temporal.temporal_models import TemporalFeatures
from app.engines.graph.intelligence.graph_models import GraphFeatures


def _make_event(
    amount: float = 25000.0,
    channel: str = "UPI",
    sender_bank: str = "State Bank of India",
    receiver_bank: str = "HDFC Bank",
    hour: int = 14,
    weekday: int = 2,  # Wednesday
    **kwargs,
) -> TransactionEvent:
    # 2026-09-16 was a Wednesday
    dt = datetime(2026, 9, 16, hour, 30, 0, tzinfo=timezone.utc)
    return TransactionEvent(
        transaction_id="TX-TEST-001",
        timestamp=dt,
        amount=amount,
        sender_account="ACC-SENDER",
        receiver_account="ACC-RECEIVER",
        channel=channel,
        sender_bank=sender_bank,
        receiver_bank=receiver_bank,
        device_id="DEV-101",
        ip_address="192.168.1.1",
        metadata={
            "account_age_days": 120,
            "velocity_l6h": 5,
            "user_risk_score": 45.0,
            "is_vpn_or_proxy": 1,
            **kwargs,
        },
    )


def test_build_features_from_event_basic():
    """Extracts transaction-native features, channel one-hot, and interbank flag."""
    event = _make_event(amount=10000.0, channel="NEFT")
    builder = TabularFeatureBuilder()
    features = builder.build_features(event)

    assert features.amount == 10000.0
    assert features.log_amount == pytest.approx(4.0000, abs=1e-3)  # log10(10001)
    assert features.channel_neft == 1.0
    assert features.channel_upi == 0.0
    assert features.is_interbank == 1.0  # SBI != HDFC
    assert features.has_device_id == 1.0
    assert features.has_ip_address == 1.0
    assert features.account_age_days == 120.0
    assert features.velocity_l6h == 5.0
    assert features.is_vpn_or_proxy == 1.0


def test_build_features_with_temporal_context():
    """Integrates M6 TemporalFeatures into TabularFeatures."""
    event = _make_event()
    temp_feat = TemporalFeatures(
        reference_time=datetime.now(timezone.utc),
        transaction_count_5m=4,
        transaction_count_1h=18,
        amount_sum_5m=45000.0,
        amount_sum_1h=90000.0,
        average_interval_seconds=15.5,
        burst_detected=True,
        burst_count=6,
        rapid_in_out_detected=True,
        rapid_in_out_ratio=0.95,
        activity_change_ratio=2.5,
    )

    builder = TabularFeatureBuilder()
    features = builder.build_features(event, temporal_features=temp_feat)

    assert features.temporal_tx_count_5m == 4.0
    assert features.temporal_tx_count_1h == 18.0
    assert features.temporal_amount_sum_5m == 45000.0
    assert features.temporal_avg_interval_seconds == 15.5
    assert features.temporal_burst_detected == 1.0
    assert features.temporal_burst_count == 6.0
    assert features.temporal_rapid_in_out_detected == 1.0
    assert features.temporal_rapid_in_out_ratio == 0.95
    assert features.temporal_activity_change_ratio == 2.5


def test_build_features_with_graph_context():
    """Integrates M7 GraphFeatures into TabularFeatures."""
    event = _make_event()
    graph_feat = GraphFeatures(
        account_id="ACC-SENDER",
        in_degree=10,
        out_degree=8,
        total_degree=18,
        unique_inbound_counterparties=9,
        unique_outbound_counterparties=7,
        fan_in_ratio=0.90,
        fan_out_ratio=0.875,
        neighboring_accounts_count=16,
        neighborhood_density=0.12,
        reachable_node_count=5,
        has_cycle=True,
        cycle_count=1,
        shared_device_count=2,
        shared_ip_count=1,
    )

    builder = TabularFeatureBuilder()
    features = builder.build_features(event, graph_features=graph_feat)

    assert features.graph_in_degree == 10.0
    assert features.graph_out_degree == 8.0
    assert features.graph_total_degree == 18.0
    assert features.graph_unique_inbound_counterparties == 9.0
    assert features.graph_fan_in_ratio == 0.90
    assert features.graph_has_cycle == 1.0
    assert features.graph_cycle_count == 1.0
    assert features.graph_shared_device_count == 2.0
    assert features.graph_shared_ip_count == 1.0


def test_build_features_from_dict_row():
    """build_from_dict accurately parses raw dictionary rows matching CSV schema."""
    row = {
        "txn_id": "TXN-CSV-99",
        "timestamp": "2025-07-01 10:40:36",
        "account_number": "ACC-SRC-1",
        "receiver_account": "ACC-DST-2",
        "amount": 44532.52,
        "trans_type": "UPI",
        "bank_name": "State Bank of India",
        "receiver_bank": "State Bank of India",
        "account_age_days": 7,
        "velocity_l6h": 13,
        "user_risk_score": 60.9,
        "is_vpn_or_proxy": 1,
    }
    feat = tabular_feature_builder.build_from_dict(row)

    assert feat.amount == 44532.52
    assert feat.channel_upi == 1.0
    assert feat.is_interbank == 0.0  # Same bank
    assert feat.account_age_days == 7.0
    assert feat.velocity_l6h == 13.0
    assert feat.user_risk_score == 60.9
    assert feat.is_vpn_or_proxy == 1.0
