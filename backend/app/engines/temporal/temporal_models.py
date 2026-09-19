"""
MuleTrace AI — Temporal Domain Models & Feature Contracts.

Defines deterministic data structures for temporal window aggregations,
pass-through sequences, and explainable temporal feature payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class WindowAggregation:
    """Deterministic summary for a specific rolling time window."""

    window_name: str
    window_seconds: int
    start_time: datetime
    end_time: datetime
    transaction_count: int
    amount_sum: float
    contributing_transaction_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_name": self.window_name,
            "window_seconds": self.window_seconds,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "transaction_count": self.transaction_count,
            "amount_sum": round(self.amount_sum, 2),
            "contributing_transaction_ids": self.contributing_transaction_ids,
        }


@dataclass(frozen=True)
class PassThroughEvent:
    """Details of a rapid in/out pass-through sequence for a specific account."""

    account_id: str
    incoming_transaction_id: str
    outgoing_transaction_id: str
    incoming_time: datetime
    outgoing_time: datetime
    delay_seconds: float
    incoming_amount: float
    outgoing_amount: float
    pass_through_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "incoming_transaction_id": self.incoming_transaction_id,
            "outgoing_transaction_id": self.outgoing_transaction_id,
            "incoming_time": self.incoming_time.isoformat(),
            "outgoing_time": self.outgoing_time.isoformat(),
            "delay_seconds": round(self.delay_seconds, 2),
            "incoming_amount": round(self.incoming_amount, 2),
            "outgoing_amount": round(self.outgoing_amount, 2),
            "pass_through_ratio": round(self.pass_through_ratio, 4),
        }


@dataclass
class TemporalFeatures:
    """Canonical explainable feature container produced by the Temporal Engine.

    Encapsulates rolling counts, volumes, velocity intervals, burst indicators,
    pass-through timings, and full explainability metadata.
    """

    reference_time: datetime

    # ── Rolling Window Counts ───────────────────────────────────────────
    transaction_count_5m: int = 0
    transaction_count_15m: int = 0
    transaction_count_1h: int = 0
    transaction_count_24h: int = 0

    # ── Rolling Window Monetary Volumes ─────────────────────────────────
    amount_sum_5m: float = 0.0
    amount_sum_15m: float = 0.0
    amount_sum_1h: float = 0.0
    amount_sum_24h: float = 0.0

    # ── Velocity & Inter-Transaction Intervals ──────────────────────────
    average_interval_seconds: Optional[float] = None
    minimum_interval_seconds: Optional[float] = None
    maximum_interval_seconds: Optional[float] = None

    # ── Burst Activity ──────────────────────────────────────────────────
    burst_detected: bool = False
    burst_count: int = 0
    burst_transaction_ids: list[str] = field(default_factory=list)

    # ── Rapid In/Out Pass-Through ────────────────────────────────────────
    rapid_in_out_detected: bool = False
    rapid_in_out_delay_seconds: Optional[float] = None
    rapid_in_out_ratio: float = 0.0
    rapid_in_out_events: list[PassThroughEvent] = field(default_factory=list)

    # ── Sequence & Concentration ────────────────────────────────────────
    sequence_duration_seconds: float = 0.0
    temporal_concentration: float = 0.0

    # ── Activity Change Dynamics ────────────────────────────────────────
    activity_change_ratio: float = 0.0
    current_window_count: int = 0
    previous_window_count: int = 0

    # ── Explainability Audit Map ────────────────────────────────────────
    windows: dict[str, WindowAggregation] = field(default_factory=dict)
    total_events_evaluated: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert features into a clean JSON-serializable dictionary."""
        return {
            "reference_time": self.reference_time.isoformat(),
            "total_events_evaluated": self.total_events_evaluated,
            "counts": {
                "5m": self.transaction_count_5m,
                "15m": self.transaction_count_15m,
                "1h": self.transaction_count_1h,
                "24h": self.transaction_count_24h,
            },
            "volumes": {
                "5m": round(self.amount_sum_5m, 2),
                "15m": round(self.amount_sum_15m, 2),
                "1h": round(self.amount_sum_1h, 2),
                "24h": round(self.amount_sum_24h, 2),
            },
            "intervals": {
                "average_seconds": (
                    round(self.average_interval_seconds, 2)
                    if self.average_interval_seconds is not None
                    else None
                ),
                "minimum_seconds": (
                    round(self.minimum_interval_seconds, 2)
                    if self.minimum_interval_seconds is not None
                    else None
                ),
                "maximum_seconds": (
                    round(self.maximum_interval_seconds, 2)
                    if self.maximum_interval_seconds is not None
                    else None
                ),
            },
            "burst": {
                "detected": self.burst_detected,
                "count": self.burst_count,
                "transaction_ids": self.burst_transaction_ids,
            },
            "rapid_pass_through": {
                "detected": self.rapid_in_out_detected,
                "delay_seconds": (
                    round(self.rapid_in_out_delay_seconds, 2)
                    if self.rapid_in_out_delay_seconds is not None
                    else None
                ),
                "ratio": round(self.rapid_in_out_ratio, 4),
                "events": [e.to_dict() for e in self.rapid_in_out_events],
            },
            "sequence": {
                "duration_seconds": round(self.sequence_duration_seconds, 2),
                "concentration": round(self.temporal_concentration, 4),
            },
            "activity_change": {
                "ratio": round(self.activity_change_ratio, 4),
                "current_window_count": self.current_window_count,
                "previous_window_count": self.previous_window_count,
            },
            "windows": {k: v.to_dict() for k, v in self.windows.items()},
        }
