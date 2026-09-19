"""
MuleTrace AI — Tabular Feature Schema & Model Contracts.

Defines the canonical, strongly typed feature vector schema for tabular machine learning,
combining transaction-native attributes, device/network telemetry, M6 TemporalFeatures,
and M7 GraphFeatures.

Architectural Boundary:
- Pure tabular representation: zero dependencies on FastAPI, SQLAlchemy, Neo4j, or AWS.
- Fully deterministic: column order is fixed by TABULAR_FEATURE_COLUMNS.
- NaN / Infinite safe: all values are guaranteed finite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Optional
import numpy as np
import pandas as pd


# ── Canonical Deterministic Feature Column Order ─────────────────────────────
# This fixed tuple guarantees 100% deterministic column ordering across
# training, evaluation, and inference.
TABULAR_FEATURE_COLUMNS: tuple[str, ...] = (
    # ── 1. Transaction-Native Features (12) ──
    "amount",
    "log_amount",
    "channel_upi",
    "channel_neft",
    "channel_rtgs",
    "channel_imps",
    "channel_other",
    "is_interbank",
    "has_device_id",
    "has_ip_address",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_night",
    # ── 2. Device & Risk Telemetry Features (14) ──
    "account_age_days",
    "velocity_l6h",
    "churn_rate",
    "ip_account_density",
    "amount_deviation_ratio",
    "daily_limit_fraction",
    "user_risk_score",
    "device_trust_score",
    "is_rooted_or_emulator",
    "device_risk_score",
    "merchant_chargeback_rate",
    "merchant_risk_score",
    "is_vpn_or_proxy",
    "network_risk_score",
    # ── 3. M6 Temporal Intelligence Features (12) ──
    "temporal_tx_count_5m",
    "temporal_tx_count_15m",
    "temporal_tx_count_1h",
    "temporal_tx_count_24h",
    "temporal_amount_sum_5m",
    "temporal_amount_sum_1h",
    "temporal_avg_interval_seconds",
    "temporal_burst_detected",
    "temporal_burst_count",
    "temporal_rapid_in_out_detected",
    "temporal_rapid_in_out_ratio",
    "temporal_activity_change_ratio",
    # ── 4. M7 Graph Intelligence Features (16) ──
    "graph_in_degree",
    "graph_out_degree",
    "graph_total_degree",
    "graph_unique_inbound_counterparties",
    "graph_unique_outbound_counterparties",
    "graph_fan_in_ratio",
    "graph_fan_out_ratio",
    "graph_neighboring_accounts_count",
    "graph_neighboring_devices_count",
    "graph_neighboring_ips_count",
    "graph_neighborhood_density",
    "graph_reachable_node_count",
    "graph_max_downstream_path_length",
    "graph_has_cycle",
    "graph_cycle_count",
    "graph_shared_device_count",
    "graph_shared_ip_count",
)

TOTAL_FEATURE_COUNT = len(TABULAR_FEATURE_COLUMNS)


@dataclass
class TabularFeatures:
    """Strongly typed feature vector for ML inference and model training."""

    # ── 1. Transaction-Native ───────────────────────────────────────────
    amount: float = 0.0
    log_amount: float = 0.0
    channel_upi: float = 0.0
    channel_neft: float = 0.0
    channel_rtgs: float = 0.0
    channel_imps: float = 0.0
    channel_other: float = 0.0
    is_interbank: float = 0.0
    has_device_id: float = 0.0
    has_ip_address: float = 0.0
    hour_of_day: float = 0.0
    day_of_week: float = 0.0
    is_weekend: float = 0.0
    is_night: float = 0.0

    # ── 2. Device & Risk Telemetry ──────────────────────────────────────
    account_age_days: float = 180.0
    velocity_l6h: float = 1.0
    churn_rate: float = 0.01
    ip_account_density: float = 1.0
    amount_deviation_ratio: float = 1.0
    daily_limit_fraction: float = 0.1
    user_risk_score: float = 15.0
    device_trust_score: float = 85.0
    is_rooted_or_emulator: float = 0.0
    device_risk_score: float = 10.0
    merchant_chargeback_rate: float = 0.0
    merchant_risk_score: float = 5.0
    is_vpn_or_proxy: float = 0.0
    network_risk_score: float = 15.0

    # ── 3. M6 Temporal Features ─────────────────────────────────────────
    temporal_tx_count_5m: float = 0.0
    temporal_tx_count_15m: float = 0.0
    temporal_tx_count_1h: float = 0.0
    temporal_tx_count_24h: float = 0.0
    temporal_amount_sum_5m: float = 0.0
    temporal_amount_sum_1h: float = 0.0
    temporal_avg_interval_seconds: float = 0.0
    temporal_burst_detected: float = 0.0
    temporal_burst_count: float = 0.0
    temporal_rapid_in_out_detected: float = 0.0
    temporal_rapid_in_out_ratio: float = 0.0
    temporal_activity_change_ratio: float = 0.0

    # ── 4. M7 Graph Features ────────────────────────────────────────────
    graph_in_degree: float = 0.0
    graph_out_degree: float = 0.0
    graph_total_degree: float = 0.0
    graph_unique_inbound_counterparties: float = 0.0
    graph_unique_outbound_counterparties: float = 0.0
    graph_fan_in_ratio: float = 0.0
    graph_fan_out_ratio: float = 0.0
    graph_neighboring_accounts_count: float = 0.0
    graph_neighboring_devices_count: float = 0.0
    graph_neighboring_ips_count: float = 0.0
    graph_neighborhood_density: float = 0.0
    graph_reachable_node_count: float = 0.0
    graph_max_downstream_path_length: float = 0.0
    graph_has_cycle: float = 0.0
    graph_cycle_count: float = 0.0
    graph_shared_device_count: float = 0.0
    graph_shared_ip_count: float = 0.0

    # ── Metadata Context (Non-modeling) ─────────────────────────────────
    transaction_id: Optional[str] = None
    account_id: Optional[str] = None

    def to_dict(self) -> dict[str, float]:
        """Return deterministic dictionary ordered strictly by TABULAR_FEATURE_COLUMNS."""
        res: dict[str, float] = {}
        for col in TABULAR_FEATURE_COLUMNS:
            val = getattr(self, col, 0.0)
            if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                val = 0.0
            res[col] = float(val)
        return res

    def to_vector(self) -> list[float]:
        """Return ordered float list aligned with TABULAR_FEATURE_COLUMNS."""
        d = self.to_dict()
        return [d[col] for col in TABULAR_FEATURE_COLUMNS]

    def to_dataframe(self) -> pd.DataFrame:
        """Return single-row DataFrame strictly aligned with feature schema."""
        return pd.DataFrame([self.to_dict()], columns=list(TABULAR_FEATURE_COLUMNS))


def sanitize_numeric(val: Any, default: float = 0.0) -> float:
    """Ensure a value is converted to a finite float, preventing NaN/Inf propagation."""
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default
