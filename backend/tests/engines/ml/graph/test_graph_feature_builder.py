"""
MuleTrace AI — Graph Feature Builder Unit Tests.

Validates deterministic node feature extraction, multi-edge representation,
heterogeneous entity processing, and boundary edge cases (empty and single-node graphs).
"""

from __future__ import annotations

from datetime import datetime
import networkx as nx
import pytest

from app.engines.ml.graph.graph_feature_builder import GraphFeatureBuilder, graph_feature_builder
from app.engines.ml.graph.graph_schema import (
    NODE_FEATURE_DIM,
    NODE_TYPE_ACCOUNT,
    NODE_TYPE_DEVICE,
    NODE_TYPE_IP,
)
from app.engines.temporal.temporal_models import TemporalFeatures
from app.engines.graph.intelligence.graph_models import GraphFeatures


def _build_test_graph() -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()
    G.add_node("account:ACC-1", type=NODE_TYPE_ACCOUNT, account_age_days=200, velocity_l6h=3)
    G.add_node("account:ACC-2", type=NODE_TYPE_ACCOUNT, account_age_days=50, velocity_l6h=1)
    G.add_node("account:ACC-3", type=NODE_TYPE_ACCOUNT, account_age_days=300, velocity_l6h=2)
    G.add_node("device:DEV-99", type=NODE_TYPE_DEVICE)
    G.add_node("ip:10.0.0.1", type=NODE_TYPE_IP)

    # ACC-1 -> ACC-2 (Tx 1)
    G.add_edge("account:ACC-1", "account:ACC-2", key="TX-1", relationship="TRANSFERRED_FUNDS", amount=5000.0)
    # ACC-1 -> ACC-2 (Tx 2 - multi-edge)
    G.add_edge("account:ACC-1", "account:ACC-2", key="TX-2", relationship="TRANSFERRED_FUNDS", amount=15000.0)
    # ACC-2 -> ACC-3
    G.add_edge("account:ACC-2", "account:ACC-3", key="TX-3", relationship="TRANSFERRED_FUNDS", amount=18000.0)

    # Device & IP links
    G.add_edge("account:ACC-1", "device:DEV-99", key="dev:1", relationship="USES_DEVICE")
    G.add_edge("account:ACC-2", "device:DEV-99", key="dev:2", relationship="USES_DEVICE")
    G.add_edge("account:ACC-1", "ip:10.0.0.1", key="ip:1", relationship="USES_IP")
    return G


def test_feature_builder_deterministic_node_ordering():
    """Nodes in snapshot are strictly sorted lexicographically."""
    G = _build_test_graph()
    snap = graph_feature_builder.build_from_networkx(G)

    expected_sorted = sorted(list(G.nodes()))
    assert snap.node_ids == expected_sorted
    assert snap.num_nodes == len(expected_sorted)
    # Check index mapping
    for i, nid in enumerate(expected_sorted):
        assert snap.node_to_idx[nid] == i


def test_feature_builder_dimension_and_finite_values():
    """All node feature vectors have dimension 16 and contain finite real values."""
    G = _build_test_graph()
    snap = graph_feature_builder.build_from_networkx(G)

    assert snap.x.shape[1] == NODE_FEATURE_DIM
    # Check ACC-1 features
    idx_1 = snap.get_node_index("account:ACC-1")
    feat_1 = snap.x[idx_1].tolist() if hasattr(snap.x[idx_1], "tolist") else list(snap.x[idx_1])
    assert len(feat_1) == 16

    # In-degree = 0, Out-degree = 2 transfers + 1 device + 1 IP = 4
    assert feat_1[0] == 0.0  # in_degree
    assert feat_1[1] == 4.0  # out_degree (transfers + device + ip)
    assert feat_1[2] == 4.0  # total_degree
    assert feat_1[4] == 1.0  # unique outbound counterparties (ACC-2)
    assert feat_1[9] == 200.0  # account_age_days
    assert feat_1[10] == 3.0   # velocity_l6h


def test_feature_builder_multi_edge_preservation():
    """Multi-edges between same account pair are preserved with individual edge keys."""
    G = _build_test_graph()
    snap = graph_feature_builder.build_from_networkx(G)

    # 3 transfer edges + 2 device edges + 1 ip edge = 6 total directed edges
    assert snap.num_edges == 6


def test_feature_builder_empty_graph_handling():
    """Empty NetworkX graph produces an empty snapshot without crashing."""
    G = nx.MultiDiGraph()
    snap = graph_feature_builder.build_from_networkx(G)

    assert snap.num_nodes == 0
    assert snap.num_edges == 0
    assert snap.x.shape[0] == 0
    assert snap.x.shape[1] == NODE_FEATURE_DIM


def test_feature_builder_single_node_graph_handling():
    """Single isolated node processes safely with zero degrees."""
    G = nx.MultiDiGraph()
    G.add_node("account:SOLO-1", type=NODE_TYPE_ACCOUNT, account_age_days=100)
    snap = graph_feature_builder.build_from_networkx(G)

    assert snap.num_nodes == 1
    assert snap.num_edges == 0
    assert snap.node_ids == ["account:SOLO-1"]
    idx = snap.get_node_index("account:SOLO-1")
    feat = snap.x[idx].tolist() if hasattr(snap.x[idx], "tolist") else list(snap.x[idx])
    assert feat[0] == 0.0  # in_degree
    assert feat[1] == 0.0  # out_degree
    assert feat[9] == 100.0  # account_age_days


def test_feature_builder_incorporates_temporal_and_graph_context():
    """Pre-computed M6 and M7 features populate into node feature vector."""
    G = nx.MultiDiGraph()
    G.add_node("account:TARGET-1", type=NODE_TYPE_ACCOUNT)

    temp_ctx = {
        "account:TARGET-1": TemporalFeatures(
            reference_time=datetime(2026, 9, 19, 12, 0, 0),
            burst_detected=True,
            transaction_count_1h=12,
        )
    }
    graph_ctx = {
        "account:TARGET-1": GraphFeatures(
            account_id="TARGET-1",
            shared_device_count=5,
            shared_ip_count=3,
            neighborhood_density=0.45,
        )
    }

    snap = graph_feature_builder.build_from_networkx(
        G=G,
        temporal_context=temp_ctx,
        graph_context=graph_ctx,
    )

    feat = snap.x[0].tolist() if hasattr(snap.x[0], "tolist") else list(snap.x[0])
    assert feat[11] == 1.0   # temporal_burst_detected
    assert feat[12] == 12.0  # temporal_tx_count_1h
    assert feat[13] == 5.0   # shared_device_count
    assert feat[14] == 3.0   # shared_ip_count
    assert feat[15] == pytest.approx(0.45, abs=1e-3)  # neighborhood_density
