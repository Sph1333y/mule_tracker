# MuleTrace AI — Temporal Intelligence Engine

> **Milestone 6 Architecture & Behavioral Specification**
>
> "M6 introduces an isolated, deterministic, explainable Temporal Intelligence layer built on canonical TransactionEvents without modifying R001–R014, graph repositories, or ML inference."

---

## 1. Milestone Objective

The objective of **Milestone 6 (M6)** is to establish a dedicated, modular, and deterministic **Temporal Intelligence Engine** for MuleTrace AI.

Unlike static rule triggers, the Temporal Engine operates across sliding time windows and transaction sequences to compute fine-grained velocity rates, micro-bursts, rapid pass-through layering, and activity-change ratios. It produces explainable `TemporalFeatures` without modifying the existing 14 modular fraud rules (R001–R014), without database schema alterations, and without external dependencies on AWS, ML models, or graph repositories.

---

## 2. Temporal Architecture

```
                  Canonical TransactionEvent(s)
                                │
                                ▼
                         TemporalEngine
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        Time Windows         Velocity          Sequences
       (5m, 15m, 1h, 24h)   (Intervals, Burst) (Pass-Through, Conc.)
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                         TemporalFeatures
                                │
                     ┌──────────┴──────────┐
                     │                     │
                     ▼                     ▼
             Future RiskFusion     Future Tabular/GNN ML
             (Later Milestones)    (Later Milestones)
```

---

## 3. Input Contract & Canonical Integration

The engine accepts either:
1. A sequence of canonical `TransactionEvent` domain models.
2. A sequence of raw transaction dictionaries (automatically converted via `TransactionMapper.from_dict`).

### Deduplication Policy
Transactions with identical `transaction_id` are explicitly deduplicated, retaining the first chronological occurrence to avoid artificial inflation of velocity metrics.

---

## 4. Timestamp & Timezone Safety

- **Normalization**: Every timestamp is normalized to timezone-aware UTC via `ensure_utc()`.
  - Offset-naive datetimes are treated as UTC (`dt.replace(tzinfo=timezone.utc)`).
  - Offset-aware datetimes are converted to UTC (`dt.astimezone(timezone.utc)`).
  - ISO-8601 strings and SQL datetimes are parsed safely with timezone alignment.
- **Reference Time Determinism**: The evaluation method accepts an explicit `reference_time: Optional[datetime]`. If omitted, the engine deterministically defaults to the maximum timestamp among the provided events, ensuring tests and historical replays never depend on `datetime.now()`.

---

## 5. Temporal Windows & Feature Inventory

The engine computes 4 canonical rolling windows defined in `STANDARD_WINDOWS`:
- **5 minutes** (300 seconds)
- **15 minutes** (900 seconds)
- **1 hour** (3,600 seconds)
- **24 hours** (86,400 seconds)

### Feature Inventory Table

| Feature | Definition | Window / Scope | Input | Output Type |
|---|---|---|---|---|
| `transaction_count_5m` | Count of transactions in `[ref - 5m, ref]` | 5 minutes | `timestamp` | `int` |
| `transaction_count_15m` | Count of transactions in `[ref - 15m, ref]` | 15 minutes | `timestamp` | `int` |
| `transaction_count_1h` | Count of transactions in `[ref - 1h, ref]` | 1 hour | `timestamp` | `int` |
| `transaction_count_24h` | Count of transactions in `[ref - 24h, ref]` | 24 hours | `timestamp` | `int` |
| `amount_sum_5m` | Aggregate monetary volume in `[ref - 5m, ref]` | 5 minutes | `amount`, `timestamp` | `float` |
| `amount_sum_15m` | Aggregate monetary volume in `[ref - 15m, ref]` | 15 minutes | `amount`, `timestamp` | `float` |
| `amount_sum_1h` | Aggregate monetary volume in `[ref - 1h, ref]` | 1 hour | `amount`, `timestamp` | `float` |
| `amount_sum_24h` | Aggregate monetary volume in `[ref - 24h, ref]` | 24 hours | `amount`, `timestamp` | `float` |
| `average_interval_seconds` | Mean time interval between consecutive sorted events | Full sequence | `timestamp` | `Optional[float]` |
| `minimum_interval_seconds` | Minimum time interval between consecutive sorted events | Full sequence | `timestamp` | `Optional[float]` |
| `maximum_interval_seconds` | Maximum time interval between consecutive sorted events | Full sequence | `timestamp` | `Optional[float]` |
| `burst_detected` | Flag indicating ≥5 transactions in any contiguous 5-minute slice | 5-minute sliding slice | `timestamp` | `bool` |
| `burst_count` | Maximum number of transactions in any contiguous 5-minute slice | 5-minute sliding slice | `timestamp` | `int` |
| `rapid_in_out_detected` | Flag indicating fund pass-through within 15 minutes | 15 minutes | `sender`, `receiver`, `amount` | `bool` |
| `rapid_in_out_delay_seconds` | Transit latency between incoming and outgoing legs | 15 minutes | `timestamp` | `Optional[float]` |
| `rapid_in_out_ratio` | Ratio of outgoing funds to incoming funds | 15 minutes | `amount` | `float` |
| `sequence_duration_seconds` | Total timespan between first and last events in sequence | Full sequence | `timestamp` | `float` |
| `temporal_concentration` | Fraction of total events occurring in the peak 5-minute slice | 5-minute slice | `timestamp` | `float` |
| `activity_change_ratio` | Current 1h count divided by previous 1h count | Trailing 2 hours | `timestamp` | `float` |

---

## 6. Velocity & Burst Analysis

### Sliding Window Burst Detection
A burst is formally defined as:
$$\text{count} \ge 5 \quad \text{within any continuous} \quad \Delta t \le 300\text{ seconds}$$
Implemented using an $O(N)$ two-pointer sliding window over chronologically sorted events. Unlike threshold rules, burst signals return factual counts and contributing transaction IDs rather than subjective fraud classifications.

---

## 7. Rapid In/Out Pass-Through Analysis

Identifies intermediate account behavior where:
$$\text{Account } X \text{ receives funds at } t_{\text{in}} \quad \text{and transfers out at } t_{\text{out}}$$
$$\text{such that } 0 \le (t_{\text{out}} - t_{\text{in}}) \le 900\text{ seconds (15 minutes)}$$
Records `PassThroughEvent` capturing exact timestamps, delay in seconds, leg amounts, and forwarded ratio.

---

## 8. Activity Change Dynamics

Measures surge against historical baseline:
- Current Window: $[t_{\text{ref}} - 3600\text{s}, t_{\text{ref}}]$
- Previous Window: $[t_{\text{ref}} - 7200\text{s}, t_{\text{ref}} - 3600\text{s}]$

$$\text{ratio} = \begin{cases}
0.0 & \text{if } \text{prev} = 0 \text{ and } \text{curr} = 0 \\
\text{float}(\text{curr}) & \text{if } \text{prev} = 0 \text{ and } \text{curr} > 0 \\
\frac{\text{curr}}{\text{prev}} & \text{if } \text{prev} > 0
\end{cases}$$

---

## 9. Explainability & Auditability

Every feature calculation in `TemporalFeatures` retains an audit trail:
- Contributing transaction IDs are stored inside each `WindowAggregation`.
- Burst transactions record `burst_transaction_ids`.
- Rapid pass-through instances record `incoming_transaction_id` and `outgoing_transaction_id`.
- Serializes cleanly to JSON via `to_dict()`.

---

## 10. Canonical Invariants Verified

1. **Non-negativity**: All counts, amounts, and intervals are $\ge 0$.
2. **Count Boundedness**: Window counts $\le$ total input events.
3. **Monotonicity**: Events are chronologically sorted prior to evaluation.
4. **Determinism**: Identical inputs and reference time produce bit-for-bit identical feature vectors.
5. **Window Shift**: Advancing `reference_time` predictably slides window membership.
6. **Null Safety**: Empty events list returns 0 metrics without exceptions.
7. **Telemetry Robustness**: Missing device, IP, or location attributes do not disrupt temporal calculations.
8. **Window Isolation**: Events outside $[t_{\text{ref}} - \Delta, t_{\text{ref}}]$ have zero effect on that window.
9. **Window Sensitivity**: Events within $[t_{\text{ref}} - \Delta, t_{\text{ref}}]$ strictly increment window count and volume.
10. **Permutation Invariance**: The input sequence order does not alter output results.

---

## 11. Confirmation of Rule Preservation

Existing rules R001 through R014 and the modular registry from Milestone 5 remain 100% untouched. No rules were replaced, no thresholds modified, and no alert logic altered.
