"""
MuleTrace AI — Temporal Intelligence Package.

Provides deterministic temporal sequence analysis, rolling window calculations,
burst detection, rapid pass-through tracking, and explainable temporal features.
"""

from __future__ import annotations

from app.engines.temporal.temporal_engine import TemporalEngine, temporal_engine
from app.engines.temporal.temporal_features import (
    compute_activity_change,
    compute_intervals,
    compute_temporal_concentration,
    detect_burst,
    detect_rapid_pass_through,
)
from app.engines.temporal.temporal_models import (
    PassThroughEvent,
    TemporalFeatures,
    WindowAggregation,
)
from app.engines.temporal.temporal_windows import (
    STANDARD_WINDOWS,
    compute_window_aggregation,
    ensure_utc,
    filter_events_in_range,
    parse_timestamp,
)

__all__ = [
    # Engine & Singleton
    "TemporalEngine",
    "temporal_engine",
    # Models & Features
    "TemporalFeatures",
    "WindowAggregation",
    "PassThroughEvent",
    # Windows & Helpers
    "STANDARD_WINDOWS",
    "ensure_utc",
    "parse_timestamp",
    "filter_events_in_range",
    "compute_window_aggregation",
    # Feature Calculations
    "compute_intervals",
    "detect_burst",
    "detect_rapid_pass_through",
    "compute_temporal_concentration",
    "compute_activity_change",
]
