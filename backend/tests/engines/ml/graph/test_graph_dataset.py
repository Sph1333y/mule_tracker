"""
MuleTrace AI — Graph Dataset & Leakage Prevention Unit Tests.

Validates graph snapshot construction from CSV data, strict chronological splitting,
and elimination of future temporal feature and structural leakage.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import pandas as pd
import pytest

from app.engines.ml.graph.graph_dataset import (
    ChronologicalGraphSplit,
    GraphMLDatasetBuilder,
    graph_ml_dataset_builder,
)

CSV_PATH = Path("ml/transactions.csv")


def _sample_df() -> pd.DataFrame:
    rows = [
        {"txn_id": "T1", "timestamp": "2026-09-01 10:00:00", "account_number": "A1", "receiver_account": "A2", "amount": 1000.0, "is_fraud": 0},
        {"txn_id": "T2", "timestamp": "2026-09-02 10:00:00", "account_number": "A2", "receiver_account": "A3", "amount": 900.0, "is_fraud": 0},
        {"txn_id": "T3", "timestamp": "2026-09-03 10:00:00", "account_number": "A3", "receiver_account": "A4", "amount": 50000.0, "is_fraud": 1},
        {"txn_id": "T4", "timestamp": "2026-09-04 10:00:00", "account_number": "A4", "receiver_account": "A5", "amount": 49000.0, "is_fraud": 1},
        {"txn_id": "T5", "timestamp": "2026-09-05 10:00:00", "account_number": "A5", "receiver_account": "A1", "amount": 100.0, "is_fraud": 0},
    ]
    return pd.DataFrame(rows)


def test_build_snapshot_from_transactions_csv():
    """Builds a valid GraphDataSnapshot from actual project CSV data if present."""
    if not CSV_PATH.exists():
        pytest.skip("ml/transactions.csv not found.")

    df = pd.read_csv(CSV_PATH)
    snapshot = graph_ml_dataset_builder.build_snapshot_from_dataframe(df)

    assert snapshot.num_nodes > 0
    assert snapshot.num_edges > 0
    assert snapshot.x.shape[1] == 16
    assert snapshot.y is not None


def test_chronological_leakage_prevention():
    """Transactions after max_timestamp do NOT enter the historical graph snapshot."""
    df = _sample_df()

    # Snapshot up to Sept 2: Should contain T1 and T2 only
    cutoff = datetime(2026, 9, 2, 23, 59, 59)
    snap = graph_ml_dataset_builder.build_snapshot_from_dataframe(df, max_timestamp=cutoff)

    assert snap.num_edges == 2
    # Only A1, A2, A3 should exist in this graph
    assert "account:A1" in snap.node_ids
    assert "account:A2" in snap.node_ids
    assert "account:A3" in snap.node_ids
    assert "account:A4" not in snap.node_ids  # A4 first appeared in T3 (Sept 3)
    assert "account:A5" not in snap.node_ids  # A5 first appeared in T4 (Sept 4)


def test_chronological_graph_splits():
    """Chronological split partitions data into 3 temporally monotonic snapshots."""
    df = _sample_df()
    split = graph_ml_dataset_builder.split_chronological_snapshots(
        df,
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
    )

    assert isinstance(split, ChronologicalGraphSplit)
    # Train snapshot has fewer edges than full test snapshot
    assert split.train_snapshot.num_edges <= split.val_snapshot.num_edges
    assert split.val_snapshot.num_edges <= split.test_snapshot.num_edges
    # Cutoffs are sorted
    t_train = split.split_timestamps["train_cutoff"]
    t_val = split.split_timestamps["val_cutoff"]
    t_test = split.split_timestamps["test_cutoff"]
    assert t_train <= t_val <= t_test


def test_empty_dataframe_handling():
    """Empty dataframe yields empty snapshots gracefully."""
    empty_df = pd.DataFrame()
    split = graph_ml_dataset_builder.split_chronological_snapshots(empty_df)

    assert split.num_train_nodes == 0
    assert split.num_val_nodes == 0
    assert split.num_test_nodes == 0
