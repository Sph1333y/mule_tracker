"""
MuleTrace AI — GraphFeatures Model Unit Tests.

Tests the GraphFeatures domain model, serialization, immutability,
and field structure.
"""

from __future__ import annotations

import json
import pytest

from app.engines.graph.intelligence import GraphFeatures


def test_graph_features_defaults():
    """GraphFeatures default initialization provides zeroed topological metrics."""
    f = GraphFeatures(account_id="ACC-001")

    assert f.account_id == "ACC-001"
    assert f.node_type == "account"
    assert f.hop_depth == 2
    assert f.in_degree == 0
    assert f.out_degree == 0
    assert f.total_degree == 0
    assert f.has_cycle is False
    assert f.shared_device_count == 0
    assert f.shared_ip_count == 0
    assert f.evidence_signals == []
    assert f.explanations == []


def test_graph_features_json_serializable():
    """to_dict() output must be 100% compliant with json.dumps()."""
    f = GraphFeatures(
        account_id="ACC-002",
        in_degree=5,
        out_degree=3,
        total_degree=8,
        unique_inbound_counterparties=4,
        unique_outbound_counterparties=2,
        inbound_volume_total=50000.55,
        outbound_volume_total=45000.12,
        fan_in_ratio=0.8,
        fan_out_ratio=0.6667,
        neighboring_accounts_count=6,
        neighboring_devices_count=1,
        neighboring_ips_count=1,
        unique_node_count_by_type={"account": 7, "device": 1, "ip": 1},
        neighborhood_density=0.1905,
        reachable_node_count=2,
        downstream_accounts=["ACC-003", "ACC-004"],
        upstream_accounts=["ACC-005", "ACC-006", "ACC-007", "ACC-008"],
        max_downstream_path_length=2,
        path_summary="Account ACC-002 can reach 2 downstream accounts.",
        has_cycle=True,
        cycle_count=1,
        cycle_lengths=[3],
        cycles=[["ACC-002", "ACC-003", "ACC-004", "ACC-002"]],
        contributing_cycle_nodes=["ACC-002", "ACC-003", "ACC-004"],
        shared_device_count=1,
        shared_ip_count=1,
        accounts_per_shared_device={"DEV-1": 3},
        accounts_per_shared_ip={"10.0.0.1": 2},
        associated_devices=["DEV-1"],
        associated_ips=["10.0.0.1"],
        subgraph_node_count=9,
        subgraph_edge_count=10,
        contributing_node_ids=["account:ACC-002", "account:ACC-003"],
        contributing_transaction_ids=["TX-100", "TX-101"],
        evidence_signals=["CYCLE_DETECTED: 1 loop(s)", "SHARED_DEVICE: DEV-1"],
        explanations=["Account recorded transfers."],
        reference_timestamp="2026-09-19T12:00:00+00:00",
    )

    data = f.to_dict()
    serialized = json.dumps(data)
    deserialized = json.loads(serialized)

    assert deserialized["account_id"] == "ACC-002"
    assert deserialized["degrees"]["in_degree"] == 5
    assert deserialized["cycles"]["has_cycle"] is True
    assert deserialized["shared_entities"]["shared_device_count"] == 1
    assert deserialized["audit"]["subgraph_node_count"] == 9
