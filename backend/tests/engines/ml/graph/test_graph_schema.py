"""
MuleTrace AI — Graph ML Schema Unit Tests.

Validates canonical constants, 16-D node feature catalog, NaN/Inf numeric sanitization,
and GraphDataSnapshot data structures.
"""

from __future__ import annotations

import math
import pytest
import numpy as np

from app.engines.ml.graph.graph_schema import (
    ACCOUNT_NODE_FEATURE_COLUMNS,
    EDGE_TYPE_DEVICE,
    EDGE_TYPE_IP,
    EDGE_TYPE_TRANSFER,
    NODE_FEATURE_DIM,
    NODE_TYPE_ACCOUNT,
    NODE_TYPE_DEVICE,
    NODE_TYPE_IP,
    GraphDataSnapshot,
    NodeEmbedding,
    NodeFeatureVector,
    sanitize_numeric,
)


def test_schema_constants():
    """Entity and relation types match domain ontology."""
    assert NODE_TYPE_ACCOUNT == "account"
    assert NODE_TYPE_DEVICE == "device"
    assert NODE_TYPE_IP == "ip"
    assert EDGE_TYPE_TRANSFER == "TRANSFERRED_FUNDS"
    assert EDGE_TYPE_DEVICE == "USES_DEVICE"
    assert EDGE_TYPE_IP == "USES_IP"


def test_account_node_feature_columns_dimension():
    """Canonical account node feature vector is strictly 16 dimensions."""
    assert len(ACCOUNT_NODE_FEATURE_COLUMNS) == 16
    assert NODE_FEATURE_DIM == 16
    # Fixed ordered columns
    assert ACCOUNT_NODE_FEATURE_COLUMNS[0] == "in_degree"
    assert ACCOUNT_NODE_FEATURE_COLUMNS[1] == "out_degree"
    assert ACCOUNT_NODE_FEATURE_COLUMNS[2] == "total_degree"
    assert "fan_in_ratio" in ACCOUNT_NODE_FEATURE_COLUMNS
    assert "fan_out_ratio" in ACCOUNT_NODE_FEATURE_COLUMNS
    assert "shared_device_count" in ACCOUNT_NODE_FEATURE_COLUMNS
    assert "shared_ip_count" in ACCOUNT_NODE_FEATURE_COLUMNS


def test_sanitize_numeric_prevents_nan_and_inf():
    """Sanitize numeric handles NaN, Inf, None, strings, and types safely."""
    assert sanitize_numeric(42.5) == 42.5
    assert sanitize_numeric(float("nan"), default=0.0) == 0.0
    assert sanitize_numeric(float("inf"), default=0.0) == 0.0
    assert sanitize_numeric(float("-inf"), default=-1.0) == -1.0
    assert sanitize_numeric(None, default=5.0) == 5.0
    assert sanitize_numeric("invalid", default=0.0) == 0.0


def test_node_feature_vector_and_embedding_models():
    """NodeFeatureVector and NodeEmbedding serialize to clean JSON dictionaries."""
    vec = NodeFeatureVector(
        node_id="account:ACC-001",
        features=[1.0] * 16,
    )
    d_vec = vec.to_dict()
    assert d_vec["node_id"] == "account:ACC-001"
    assert len(d_vec["features"]) == 16
    assert d_vec["dim"] == 16

    emb = NodeEmbedding(
        node_id="account:ACC-001",
        vector=[0.1234567, -0.9876543],
        dim=2,
    )
    d_emb = emb.to_dict()
    assert d_emb["node_id"] == "account:ACC-001"
    assert d_emb["dim"] == 2
    assert d_emb["vector"] == [0.123457, -0.987654]


def test_graph_data_snapshot_properties():
    """GraphDataSnapshot tracks node counts, edge counts, and index mappings."""
    snapshot = GraphDataSnapshot(
        node_ids=["account:A", "account:B", "device:D1"],
        node_to_idx={"account:A": 0, "account:B": 1, "device:D1": 2},
        node_type_map={"account:A": "account", "account:B": "account", "device:D1": "device"},
        x=np.zeros((3, 16)),
        edge_index=np.array([[0, 1], [1, 2]]),
    )

    assert snapshot.num_nodes == 3
    assert snapshot.num_edges == 2
    assert snapshot.get_node_index("account:A") == 0
    assert snapshot.get_node_index("account:B") == 1
    assert snapshot.get_node_index("unknown:X") is None
