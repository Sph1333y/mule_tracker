"""
MuleTrace AI — Tabular Feature Builder.

Extracts, transforms, and synthesizes multi-modal tabular features from:
1. Canonical TransactionEvent domain models (M1)
2. Device and risk telemetry metadata
3. M6 TemporalFeatures (velocity, rolling counts, bursts, pass-throughs)
4. M7 GraphFeatures (degrees, fan ratios, cycles, shared entity syndicates)

Architectural Boundary:
- Consumes M1, M6, and M7 contracts as an uncoupled client.
- Modifies zero code in previous milestones.
- Strictly deterministic, leakage-free, and NaN/Inf safe.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from app.domain.models import TransactionEvent
from app.domain.transaction_mapper import TransactionMapper
from app.engines.ml.tabular.feature_schema import (
    TABULAR_FEATURE_COLUMNS,
    TabularFeatures,
    sanitize_numeric,
)
from app.engines.temporal.temporal_models import TemporalFeatures
from app.engines.graph.intelligence.graph_models import GraphFeatures


class TabularFeatureBuilder:
    """Deterministic feature extractor producing model-ready TabularFeatures."""

    @staticmethod
    def build_features(
        event: TransactionEvent,
        temporal_features: Optional[TemporalFeatures] = None,
        graph_features: Optional[GraphFeatures] = None,
    ) -> TabularFeatures:
        """Construct a standardized TabularFeatures instance from a canonical event.

        Args:
            event: Canonical TransactionEvent to extract features from.
            temporal_features: Optional pre-computed M6 TemporalFeatures for the event.
            graph_features: Optional pre-computed M7 GraphFeatures for the sender account.

        Returns:
            TabularFeatures instance strictly conforming to TABULAR_FEATURE_COLUMNS.
        """
        # ── 1. Transaction-Native Features ──────────────────────────────────
        amt = max(0.0, sanitize_numeric(event.amount))
        log_amt = math.log10(amt + 1.0) if amt > 0 else 0.0

        ch = (event.channel or "UPI").upper()
        ch_upi = 1.0 if ch == "UPI" else 0.0
        ch_neft = 1.0 if ch == "NEFT" else 0.0
        ch_rtgs = 1.0 if ch == "RTGS" else 0.0
        ch_imps = 1.0 if ch == "IMPS" else 0.0
        ch_other = 1.0 if ch not in ("UPI", "NEFT", "RTGS", "IMPS") else 0.0

        is_interbank = (
            1.0
            if (
                event.sender_bank
                and event.receiver_bank
                and event.sender_bank.strip().lower() != event.receiver_bank.strip().lower()
            )
            else 0.0
        )
        has_dev = 1.0 if event.device_id else 0.0
        has_ip = 1.0 if event.ip_address else 0.0

        ts = event.timestamp
        hour = float(ts.hour) if hasattr(ts, "hour") else 12.0
        dow = float(ts.weekday()) if hasattr(ts, "weekday") else 2.0
        is_wknd = 1.0 if dow in (5.0, 6.0) else 0.0
        is_night = 1.0 if (hour < 6.0 or hour >= 22.0) else 0.0

        # ── 2. Device & Risk Telemetry Context (from metadata or defaults) ───
        meta = event.metadata or {}

        acc_age = sanitize_numeric(meta.get("account_age_days"), default=180.0)
        vel_l6h = sanitize_numeric(meta.get("velocity_l6h"), default=1.0)
        churn = sanitize_numeric(meta.get("churn_rate"), default=0.01)
        ip_dens = sanitize_numeric(meta.get("ip_account_density"), default=1.0)
        amt_dev = sanitize_numeric(meta.get("amount_deviation_ratio"), default=1.0)
        lim_frac = sanitize_numeric(meta.get("daily_limit_fraction"), default=0.1)
        u_risk = sanitize_numeric(meta.get("user_risk_score"), default=15.0)
        dev_trust = sanitize_numeric(meta.get("device_trust_score"), default=85.0)
        rooted = 1.0 if meta.get("is_rooted_or_emulator") else 0.0
        dev_risk = sanitize_numeric(meta.get("device_risk_score"), default=10.0)
        m_cb = sanitize_numeric(meta.get("merchant_chargeback_rate"), default=0.0)
        m_risk = sanitize_numeric(meta.get("merchant_risk_score"), default=5.0)
        vpn = 1.0 if meta.get("is_vpn_or_proxy") else 0.0
        net_risk = sanitize_numeric(meta.get("network_risk_score"), default=15.0)

        # ── 3. M6 Temporal Features Integration ──────────────────────────────
        t_5m = sanitize_numeric(temporal_features.transaction_count_5m) if temporal_features else 0.0
        t_15m = sanitize_numeric(temporal_features.transaction_count_15m) if temporal_features else 0.0
        t_1h = sanitize_numeric(temporal_features.transaction_count_1h) if temporal_features else 0.0
        t_24h = sanitize_numeric(temporal_features.transaction_count_24h) if temporal_features else 0.0
        t_vol_5m = sanitize_numeric(temporal_features.amount_sum_5m) if temporal_features else 0.0
        t_vol_1h = sanitize_numeric(temporal_features.amount_sum_1h) if temporal_features else 0.0
        t_avg_int = sanitize_numeric(temporal_features.average_interval_seconds) if temporal_features else 0.0
        t_burst = 1.0 if (temporal_features and (temporal_features.burst_detected or (temporal_features.burst_count and temporal_features.burst_count > 0))) else 0.0
        t_burst_cnt = sanitize_numeric(temporal_features.burst_count) if temporal_features else 0.0
        t_rapid = 1.0 if (temporal_features and temporal_features.rapid_in_out_detected) else 0.0
        t_rapid_r = sanitize_numeric(temporal_features.rapid_in_out_ratio) if temporal_features else 0.0
        t_act_chg = sanitize_numeric(temporal_features.activity_change_ratio) if temporal_features else 0.0

        # ── 4. M7 Graph Features Integration ─────────────────────────────────
        g_in_deg = sanitize_numeric(graph_features.in_degree) if graph_features else 0.0
        g_out_deg = sanitize_numeric(graph_features.out_degree) if graph_features else 0.0
        g_tot_deg = sanitize_numeric(graph_features.total_degree) if graph_features else 0.0
        g_u_in = sanitize_numeric(graph_features.unique_inbound_counterparties) if graph_features else 0.0
        g_u_out = sanitize_numeric(graph_features.unique_outbound_counterparties) if graph_features else 0.0
        g_fan_in_r = sanitize_numeric(graph_features.fan_in_ratio) if graph_features else 0.0
        g_fan_out_r = sanitize_numeric(graph_features.fan_out_ratio) if graph_features else 0.0
        g_neigh_acc = sanitize_numeric(graph_features.neighboring_accounts_count) if graph_features else 0.0
        g_neigh_dev = sanitize_numeric(graph_features.neighboring_devices_count) if graph_features else 0.0
        g_neigh_ip = sanitize_numeric(graph_features.neighboring_ips_count) if graph_features else 0.0
        g_dens = sanitize_numeric(graph_features.neighborhood_density) if graph_features else 0.0
        g_reach = sanitize_numeric(graph_features.reachable_node_count) if graph_features else 0.0
        g_max_path = sanitize_numeric(graph_features.max_downstream_path_length) if graph_features else 0.0
        g_has_cyc = 1.0 if (graph_features and (graph_features.has_cycle or (graph_features.cycle_count and graph_features.cycle_count > 0))) else 0.0
        g_cyc_cnt = sanitize_numeric(graph_features.cycle_count) if graph_features else 0.0
        g_sh_dev = sanitize_numeric(graph_features.shared_device_count) if graph_features else 0.0
        g_sh_ip = sanitize_numeric(graph_features.shared_ip_count) if graph_features else 0.0

        return TabularFeatures(
            # Transaction-native
            amount=amt,
            log_amount=round(log_amt, 4),
            channel_upi=ch_upi,
            channel_neft=ch_neft,
            channel_rtgs=ch_rtgs,
            channel_imps=ch_imps,
            channel_other=ch_other,
            is_interbank=is_interbank,
            has_device_id=has_dev,
            has_ip_address=has_ip,
            hour_of_day=hour,
            day_of_week=dow,
            is_weekend=is_wknd,
            is_night=is_night,
            # Telemetry
            account_age_days=acc_age,
            velocity_l6h=vel_l6h,
            churn_rate=churn,
            ip_account_density=ip_dens,
            amount_deviation_ratio=amt_dev,
            daily_limit_fraction=lim_frac,
            user_risk_score=u_risk,
            device_trust_score=dev_trust,
            is_rooted_or_emulator=rooted,
            device_risk_score=dev_risk,
            merchant_chargeback_rate=m_cb,
            merchant_risk_score=m_risk,
            is_vpn_or_proxy=vpn,
            network_risk_score=net_risk,
            # Temporal
            temporal_tx_count_5m=t_5m,
            temporal_tx_count_15m=t_15m,
            temporal_tx_count_1h=t_1h,
            temporal_tx_count_24h=t_24h,
            temporal_amount_sum_5m=t_vol_5m,
            temporal_amount_sum_1h=t_vol_1h,
            temporal_avg_interval_seconds=t_avg_int,
            temporal_burst_detected=t_burst,
            temporal_burst_count=t_burst_cnt,
            temporal_rapid_in_out_detected=t_rapid,
            temporal_rapid_in_out_ratio=t_rapid_r,
            temporal_activity_change_ratio=t_act_chg,
            # Graph
            graph_in_degree=g_in_deg,
            graph_out_degree=g_out_deg,
            graph_total_degree=g_tot_deg,
            graph_unique_inbound_counterparties=g_u_in,
            graph_unique_outbound_counterparties=g_u_out,
            graph_fan_in_ratio=g_fan_in_r,
            graph_fan_out_ratio=g_fan_out_r,
            graph_neighboring_accounts_count=g_neigh_acc,
            graph_neighboring_devices_count=g_neigh_dev,
            graph_neighboring_ips_count=g_neigh_ip,
            graph_neighborhood_density=g_dens,
            graph_reachable_node_count=g_reach,
            graph_max_downstream_path_length=g_max_path,
            graph_has_cycle=g_has_cyc,
            graph_cycle_count=g_cyc_cnt,
            graph_shared_device_count=g_sh_dev,
            graph_shared_ip_count=g_sh_ip,
            # Identifiers
            transaction_id=event.transaction_id,
            account_id=event.sender_account,
        )

    @classmethod
    def build_from_dict(
        cls,
        row: dict[str, Any],
        temporal_features: Optional[TemporalFeatures] = None,
        graph_features: Optional[GraphFeatures] = None,
    ) -> TabularFeatures:
        """Convenience method converting a transaction dictionary to TabularFeatures."""
        event = TransactionMapper.from_dict(row)
        return cls.build_features(
            event=event,
            temporal_features=temporal_features,
            graph_features=graph_features,
        )


# Singleton instance
tabular_feature_builder = TabularFeatureBuilder()
