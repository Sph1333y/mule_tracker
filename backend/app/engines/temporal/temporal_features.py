"""
MuleTrace AI — Temporal Velocity, Burst, Pass-Through, & Sequence Extractors.

Provides deterministic calculations for inter-transaction intervals, sliding-window
burst detection, rapid in/out pass-through analysis, and activity-change metrics.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timedelta
from typing import Optional

from app.domain.models import TransactionEvent
from app.engines.temporal.temporal_models import PassThroughEvent
from app.engines.temporal.temporal_windows import ensure_utc, filter_events_in_range


def compute_intervals(
    sorted_events: list[TransactionEvent],
) -> tuple[Optional[float], Optional[float], Optional[float], list[float]]:
    """Compute average, minimum, maximum, and full list of inter-transaction intervals.

    Args:
        sorted_events: Chronologically sorted list of TransactionEvents.

    Returns:
        tuple of (avg_interval_sec, min_interval_sec, max_interval_sec, all_intervals)
    """
    if len(sorted_events) <= 1:
        return None, None, None, []

    intervals: list[float] = []
    for i in range(len(sorted_events) - 1):
        t1 = ensure_utc(sorted_events[i].timestamp)
        t2 = ensure_utc(sorted_events[i + 1].timestamp)
        delta_sec = max(0.0, (t2 - t1).total_seconds())
        intervals.append(delta_sec)

    if not intervals:
        return None, None, None, []

    avg_sec = statistics.mean(intervals)
    min_sec = min(intervals)
    max_sec = max(intervals)
    return avg_sec, min_sec, max_sec, intervals


def detect_burst(
    sorted_events: list[TransactionEvent],
    burst_window_seconds: int = 300,
    burst_threshold_count: int = 5,
) -> tuple[bool, int, list[str]]:
    """Detect high-frequency bursts within a sliding time window.

    A burst occurs when >= burst_threshold_count events occur within any continuous
    sliding slice of burst_window_seconds duration (default: 5 txns in 5 mins).

    Args:
        sorted_events: Chronologically sorted list of TransactionEvents.
        burst_window_seconds: Window duration in seconds (default 300s / 5 min).
        burst_threshold_count: Minimum transaction count to constitute a burst.

    Returns:
        tuple of (burst_detected, peak_burst_count, contributing_transaction_ids)
    """
    if len(sorted_events) < burst_threshold_count:
        return False, len(sorted_events), []

    left = 0
    max_burst_count = 0
    burst_tx_ids: list[str] = []

    for right in range(len(sorted_events)):
        t_right = ensure_utc(sorted_events[right].timestamp)
        while left < right:
            t_left = ensure_utc(sorted_events[left].timestamp)
            if (t_right - t_left).total_seconds() > burst_window_seconds:
                left += 1
            else:
                break

        current_count = right - left + 1
        if current_count > max_burst_count:
            max_burst_count = current_count
            if current_count >= burst_threshold_count:
                burst_tx_ids = [sorted_events[i].transaction_id for i in range(left, right + 1)]

    detected = max_burst_count >= burst_threshold_count
    return detected, max_burst_count, burst_tx_ids if detected else []


def detect_rapid_pass_through(
    sorted_events: list[TransactionEvent],
    max_delay_seconds: int = 900,
    focal_account: Optional[str] = None,
) -> list[PassThroughEvent]:
    """Detect rapid in/out pass-through movement for intermediate accounts.

    Identifies sequences where an account receives funds and随后 disperses funds
    within max_delay_seconds (default: 15 minutes / 900 seconds).

    Args:
        sorted_events: Chronologically sorted list of TransactionEvents.
        max_delay_seconds: Maximum allowable delay between in and out legs (default 900s).
        focal_account: Optional specific account to analyze. If None, analyzes all accounts.

    Returns:
        List of identified PassThroughEvent occurrences.
    """
    if len(sorted_events) < 2:
        return []

    # Map candidate intermediate accounts
    accounts_to_check: set[str] = set()
    if focal_account:
        accounts_to_check.add(focal_account)
    else:
        # Accounts that appear as both receiver and sender
        receivers = {e.receiver_account for e in sorted_events if e.receiver_account}
        senders = {e.sender_account for e in sorted_events if e.sender_account}
        accounts_to_check = receivers.intersection(senders)

    results: list[PassThroughEvent] = []

    for acc in accounts_to_check:
        incomings = [e for e in sorted_events if e.receiver_account == acc]
        outgoings = [e for e in sorted_events if e.sender_account == acc]

        for in_tx in incomings:
            in_time = ensure_utc(in_tx.timestamp)
            for out_tx in outgoings:
                out_time = ensure_utc(out_tx.timestamp)
                delay = (out_time - in_time).total_seconds()

                if 0.0 <= delay <= max_delay_seconds:
                    ratio = (out_tx.amount / in_tx.amount) if in_tx.amount > 0 else 0.0
                    results.append(
                        PassThroughEvent(
                            account_id=acc,
                            incoming_transaction_id=in_tx.transaction_id,
                            outgoing_transaction_id=out_tx.transaction_id,
                            incoming_time=in_time,
                            outgoing_time=out_time,
                            delay_seconds=delay,
                            incoming_amount=in_tx.amount,
                            outgoing_amount=out_tx.amount,
                            pass_through_ratio=ratio,
                        )
                    )

    return results


def compute_temporal_concentration(
    sorted_events: list[TransactionEvent],
    slice_seconds: int = 300,
) -> float:
    """Compute the temporal concentration ratio of the event sequence.

    Definition: The maximum fraction of total events occurring within any continuous
    slice_seconds interval (default 300s / 5 min).
    """
    total = len(sorted_events)
    if total <= 1:
        return 1.0 if total == 1 else 0.0

    left = 0
    max_in_slice = 0

    for right in range(total):
        t_right = ensure_utc(sorted_events[right].timestamp)
        while left < right:
            t_left = ensure_utc(sorted_events[left].timestamp)
            if (t_right - t_left).total_seconds() > slice_seconds:
                left += 1
            else:
                break
        count = right - left + 1
        if count > max_in_slice:
            max_in_slice = count

    return max_in_slice / total


def compute_activity_change(
    sorted_events: list[TransactionEvent],
    reference_time: datetime,
    window_seconds: int = 3600,
) -> tuple[float, int, int]:
    """Compute relative activity change between current and previous time windows.

    Current Window: [reference_time - window_seconds, reference_time]
    Previous Window: [reference_time - 2 * window_seconds, reference_time - window_seconds]

    Returns:
        tuple of (activity_change_ratio, current_count, previous_count)
    """
    ref_utc = ensure_utc(reference_time)
    curr_start = ref_utc - timedelta(seconds=window_seconds)
    prev_start = ref_utc - timedelta(seconds=2 * window_seconds)

    curr_events = filter_events_in_range(sorted_events, curr_start, ref_utc)
    prev_events = filter_events_in_range(sorted_events, prev_start, curr_start)

    curr_count = len(curr_events)
    prev_count = len(prev_events)

    if prev_count == 0 and curr_count == 0:
        ratio = 0.0
    elif prev_count == 0 and curr_count > 0:
        ratio = float(curr_count)  # Full surge from inactive baseline
    else:
        ratio = curr_count / prev_count

    return ratio, curr_count, prev_count
