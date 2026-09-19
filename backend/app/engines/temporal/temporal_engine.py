"""
MuleTrace AI — Temporal Intelligence Engine.

Processes canonical TransactionEvents to extract deterministic, explainable
rolling window metrics, velocity rates, burst signals, and pass-through sequences.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional, Sequence, Union

from app.domain.models import TransactionEvent
from app.domain.transaction_mapper import TransactionMapper
from app.engines.temporal.temporal_features import (
    compute_activity_change,
    compute_intervals,
    compute_temporal_concentration,
    detect_burst,
    detect_rapid_pass_through,
)
from app.engines.temporal.temporal_models import TemporalFeatures, WindowAggregation
from app.engines.temporal.temporal_windows import (
    STANDARD_WINDOWS,
    compute_window_aggregation,
    ensure_utc,
    parse_timestamp,
)

logger = logging.getLogger("app.engines.temporal.temporal_engine")


class TemporalEngine:
    """Core deterministic temporal intelligence evaluation engine."""

    def evaluate(
        self,
        events: Sequence[Union[TransactionEvent, dict[str, Any]]],
        reference_time: Optional[datetime] = None,
        focal_account: Optional[str] = None,
    ) -> TemporalFeatures:
        """Evaluate a sequence of transactions and return comprehensive temporal features.

        Args:
            events: Sequence of TransactionEvent domain objects or raw dictionaries.
            reference_time: Optional reference anchor time. If omitted, defaults to the
                timestamp of the latest event in the sequence to ensure 100% determinism.
            focal_account: Optional account number to focus rapid in/out pass-through analysis.

        Returns:
            TemporalFeatures containing rolling metrics, velocity, burst, and explainability map.
        """
        # 1. Handle Empty History
        if not events:
            ref_dt = ensure_utc(reference_time) if reference_time else datetime.now(timezone.utc)
            return TemporalFeatures(
                reference_time=ref_dt,
                total_events_evaluated=0,
                windows={
                    name: WindowAggregation(
                        window_name=name,
                        window_seconds=secs,
                        start_time=ref_dt,
                        end_time=ref_dt,
                        transaction_count=0,
                        amount_sum=0.0,
                        contributing_transaction_ids=[],
                    )
                    for name, secs in STANDARD_WINDOWS.items()
                },
            )

        # 2. Normalize and Deduplicate Input Events
        normalized_events: list[TransactionEvent] = []
        seen_tx_ids: set[str] = set()

        for item in events:
            if isinstance(item, TransactionEvent):
                event = item
            elif isinstance(item, dict):
                event = TransactionMapper.from_dict(item)
            else:
                continue

            # Explicit deduplication: preserve first occurrence deterministically
            if event.transaction_id in seen_tx_ids:
                continue
            seen_tx_ids.add(event.transaction_id)
            normalized_events.append(event)

        # 3. Deterministic Chronological Sorting
        sorted_events = sorted(
            normalized_events,
            key=lambda e: ensure_utc(e.timestamp),
        )

        # 4. Resolve Reference Time (Deterministic to latest event if None)
        if reference_time is not None:
            ref_dt = ensure_utc(reference_time)
        else:
            ref_dt = ensure_utc(sorted_events[-1].timestamp)

        # 5. Compute Standard Rolling Windows (5m, 15m, 1h, 24h)
        window_aggs: dict[str, WindowAggregation] = {}
        for name, secs in STANDARD_WINDOWS.items():
            agg = compute_window_aggregation(
                events=sorted_events,
                window_name=name,
                window_seconds=secs,
                reference_time=ref_dt,
            )
            window_aggs[name] = agg

        # 6. Compute Velocity & Intervals
        avg_int, min_int, max_int, _ = compute_intervals(sorted_events)

        # 7. Compute Burst Activity
        burst_hit, burst_cnt, burst_ids = detect_burst(
            sorted_events=sorted_events,
            burst_window_seconds=STANDARD_WINDOWS["5m"],
            burst_threshold_count=5,
        )

        # 8. Compute Rapid In/Out Pass-Through
        pass_throughs = detect_rapid_pass_through(
            sorted_events=sorted_events,
            max_delay_seconds=STANDARD_WINDOWS["15m"],
            focal_account=focal_account,
        )
        rapid_detected = len(pass_throughs) > 0
        rapid_delay = pass_throughs[0].delay_seconds if rapid_detected else None
        rapid_ratio = pass_throughs[0].pass_through_ratio if rapid_detected else 0.0

        # 9. Compute Sequence Metrics & Temporal Concentration
        first_time = ensure_utc(sorted_events[0].timestamp)
        last_time = ensure_utc(sorted_events[-1].timestamp)
        seq_duration = max(0.0, (last_time - first_time).total_seconds())
        concentration = compute_temporal_concentration(sorted_events, slice_seconds=STANDARD_WINDOWS["5m"])

        # 10. Compute Activity Change (Current 1h vs Previous 1h)
        act_ratio, curr_cnt, prev_cnt = compute_activity_change(
            sorted_events=sorted_events,
            reference_time=ref_dt,
            window_seconds=STANDARD_WINDOWS["1h"],
        )

        return TemporalFeatures(
            reference_time=ref_dt,
            total_events_evaluated=len(sorted_events),
            # Rolling Counts
            transaction_count_5m=window_aggs["5m"].transaction_count,
            transaction_count_15m=window_aggs["15m"].transaction_count,
            transaction_count_1h=window_aggs["1h"].transaction_count,
            transaction_count_24h=window_aggs["24h"].transaction_count,
            # Rolling Volumes
            amount_sum_5m=window_aggs["5m"].amount_sum,
            amount_sum_15m=window_aggs["15m"].amount_sum,
            amount_sum_1h=window_aggs["1h"].amount_sum,
            amount_sum_24h=window_aggs["24h"].amount_sum,
            # Intervals
            average_interval_seconds=avg_int,
            minimum_interval_seconds=min_int,
            maximum_interval_seconds=max_int,
            # Burst
            burst_detected=burst_hit,
            burst_count=burst_cnt,
            burst_transaction_ids=burst_ids,
            # Rapid In/Out Pass-Through
            rapid_in_out_detected=rapid_detected,
            rapid_in_out_delay_seconds=rapid_delay,
            rapid_in_out_ratio=rapid_ratio,
            rapid_in_out_events=pass_throughs,
            # Sequence
            sequence_duration_seconds=seq_duration,
            temporal_concentration=concentration,
            # Activity Dynamics
            activity_change_ratio=act_ratio,
            current_window_count=curr_cnt,
            previous_window_count=prev_cnt,
            # Explainability
            windows=window_aggs,
        )


# Singleton engine instance
temporal_engine = TemporalEngine()
