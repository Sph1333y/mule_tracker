"""
MuleTrace AI — Graph ML Dataset & Chronological Leakage Prevention.

Constructs training, validation, and testing graph data snapshots from transaction logs
with strict chronological windowing to eliminate look-ahead feature leakage.

Architectural Boundary:
- Cloud-agnostic and deterministic.
- Prevents future transaction edges from appearing in historical training graphs.
- Maps binary mule/fraud labels to account nodes without data fabrication.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
import networkx as nx
import pandas as pd

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore
    TORCH_AVAILABLE = False

from app.engines.ml.graph.graph_feature_builder import GraphFeatureBuilder
from app.engines.ml.graph.graph_schema import (
    EDGE_TYPE_TRANSFER,
    NODE_TYPE_ACCOUNT,
    NODE_TYPE_DEVICE,
    NODE_TYPE_IP,
    GraphDataSnapshot,
    sanitize_numeric,
)

logger = logging.getLogger("app.engines.ml.graph.graph_dataset")


@dataclass
class ChronologicalGraphSplit:
    """Container holding isolated chronological graph snapshots and masks."""

    train_snapshot: GraphDataSnapshot
    val_snapshot: GraphDataSnapshot
    test_snapshot: GraphDataSnapshot
    split_timestamps: dict[str, str]
    num_train_nodes: int
    num_val_nodes: int
    num_test_nodes: int
    num_train_fraud: int
    num_val_fraud: int
    num_test_fraud: int


class GraphMLDatasetBuilder:
    """Constructs leak-free graph snapshots and node labels from transaction histories."""

    def __init__(self, feature_builder: Optional[GraphFeatureBuilder] = None) -> None:
        self.feature_builder = feature_builder or GraphFeatureBuilder()

    def build_snapshot_from_dataframe(
        self,
        df: pd.DataFrame,
        max_timestamp: Optional[datetime] = None,
    ) -> GraphDataSnapshot:
        """Build a graph snapshot containing only transactions up to max_timestamp.

        Args:
            df: DataFrame containing transaction records (e.g., ml/transactions.csv).
            max_timestamp: Strict temporal cutoff. All records with timestamp > max_timestamp
                are excluded to prevent look-ahead feature and structural leakage.

        Returns:
            GraphDataSnapshot with deterministic node indices, features, and directed edges.
        """
        if df.empty:
            return self.feature_builder.build_from_networkx(nx.MultiDiGraph())

        # Ensure timestamp column is parsed
        df_work = df.copy()
        if "timestamp" in df_work.columns:
            df_work["parsed_dt"] = pd.to_datetime(df_work["timestamp"])
            if max_timestamp is not None:
                # Strict leakage prevention filter: historical graph only
                df_work = df_work[df_work["parsed_dt"] <= max_timestamp]

        G = nx.MultiDiGraph()
        node_labels: dict[str, float] = {}

        for _, row in df_work.iterrows():
            sender = str(row.get("account_number") or row.get("sender_account", "")).strip()
            receiver = str(row.get("receiver_account", "")).strip()
            if not sender or not receiver:
                continue

            sender_id = f"account:{sender}"
            receiver_id = f"account:{receiver}"
            amt = sanitize_numeric(row.get("amount", 0.0))
            is_fraud = float(row.get("is_fraud", 0.0))

            # Upsert nodes
            if sender_id not in G:
                G.add_node(
                    sender_id,
                    type=NODE_TYPE_ACCOUNT,
                    account_number=sender,
                    account_age_days=sanitize_numeric(row.get("account_age_days"), 180.0),
                    velocity_l6h=sanitize_numeric(row.get("velocity_l6h"), 1.0),
                )
            if receiver_id not in G:
                G.add_node(
                    receiver_id,
                    type=NODE_TYPE_ACCOUNT,
                    account_number=receiver,
                )

            # Assign account-level fraud label (sender account is marked mule if participating in fraud)
            if sender_id not in node_labels:
                node_labels[sender_id] = is_fraud
            else:
                node_labels[sender_id] = max(node_labels[sender_id], is_fraud)

            # Receivers start with label 0 unless also active as fraudulent senders
            if receiver_id not in node_labels:
                node_labels[receiver_id] = 0.0

            # Add Transfer edge
            tx_id = str(row.get("txn_id") or row.get("transaction_id", f"{sender}->{receiver}"))
            G.add_edge(
                sender_id,
                receiver_id,
                key=tx_id,
                relationship=EDGE_TYPE_TRANSFER,
                amount=amt,
                is_fraud=is_fraud,
                timestamp=str(row.get("timestamp", "")),
            )

            # Optional device & IP linkage if present
            dev = row.get("device")
            if dev and pd.notna(dev):
                dev_id = f"device:{str(dev).strip()}"
                if dev_id not in G:
                    G.add_node(dev_id, type=NODE_TYPE_DEVICE)
                G.add_edge(sender_id, dev_id, key=f"dev:{sender}->{dev_id}", relationship="USES_DEVICE")

            ip = row.get("ip_address")
            if ip and pd.notna(ip):
                ip_id = f"ip:{str(ip).strip()}"
                if ip_id not in G:
                    G.add_node(ip_id, type=NODE_TYPE_IP)
                G.add_edge(sender_id, ip_id, key=f"ip:{sender}->{ip_id}", relationship="USES_IP")

        return self.feature_builder.build_from_networkx(
            G=G,
            node_labels=node_labels,
        )

    def split_chronological_snapshots(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> ChronologicalGraphSplit:
        """Partition transaction data into 3 leak-free chronological graph snapshots.

        Slices:
        - Train Snapshot: constructed ONLY from transactions in [T_0, T_train].
        - Val Snapshot: constructed ONLY from transactions in [T_0, T_val].
        - Test Snapshot: constructed from transactions in [T_0, T_test].

        Args:
            df: Historical transaction DataFrame.
            train_ratio: Fraction of chronological timeline for training (default: 0.70).
            val_ratio: Fraction of chronological timeline for validation (default: 0.15).
            test_ratio: Fraction of chronological timeline for test (default: 0.15).

        Returns:
            ChronologicalGraphSplit containing the 3 isolated snapshots.
        """
        if df.empty:
            empty_snap = self.build_snapshot_from_dataframe(df)
            return ChronologicalGraphSplit(
                train_snapshot=empty_snap,
                val_snapshot=empty_snap,
                test_snapshot=empty_snap,
                split_timestamps={},
                num_train_nodes=0,
                num_val_nodes=0,
                num_test_nodes=0,
                num_train_fraud=0,
                num_val_fraud=0,
                num_test_fraud=0,
            )

        df_sorted = df.copy()
        df_sorted["parsed_dt"] = pd.to_datetime(df_sorted["timestamp"])
        df_sorted = df_sorted.sort_values("parsed_dt").reset_index(drop=True)

        n = len(df_sorted)
        train_idx = max(1, int(n * train_ratio))
        val_idx = max(train_idx + 1, int(n * (train_ratio + val_ratio)))

        t_train = df_sorted.iloc[train_idx - 1]["parsed_dt"]
        t_val = df_sorted.iloc[val_idx - 1]["parsed_dt"]
        t_test = df_sorted.iloc[-1]["parsed_dt"]

        # Build chronological snapshots without future structural leakage
        train_snap = self.build_snapshot_from_dataframe(df_sorted, max_timestamp=t_train)
        val_snap = self.build_snapshot_from_dataframe(df_sorted, max_timestamp=t_val)
        test_snap = self.build_snapshot_from_dataframe(df_sorted, max_timestamp=t_test)

        # Count account nodes and fraud instances in each snapshot
        def _fraud_count(snap: GraphDataSnapshot) -> int:
            if snap.y is None:
                return 0
            if hasattr(snap.y, "cpu"):
                return int((snap.y == 1.0).sum().item())
            return int((snap.y == 1.0).sum())

        return ChronologicalGraphSplit(
            train_snapshot=train_snap,
            val_snapshot=val_snap,
            test_snapshot=test_snap,
            split_timestamps={
                "train_cutoff": t_train.isoformat(),
                "val_cutoff": t_val.isoformat(),
                "test_cutoff": t_test.isoformat(),
            },
            num_train_nodes=train_snap.num_nodes,
            num_val_nodes=val_snap.num_nodes,
            num_test_nodes=test_snap.num_nodes,
            num_train_fraud=_fraud_count(train_snap),
            num_val_fraud=_fraud_count(val_snap),
            num_test_fraud=_fraud_count(test_snap),
        )


# Singleton instance
graph_ml_dataset_builder = GraphMLDatasetBuilder()
