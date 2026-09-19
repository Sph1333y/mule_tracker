"""
MuleTrace AI — Unit Tests for Graph Evidence Extraction (M7).
"""

from app.engines.evidence.collectors import collect_graph_evidence
from app.engines.evidence.models import EvidenceCategory, EvidenceSeverity, EvidenceSource
from app.engines.graph.intelligence.graph_models import GraphFeatures


def test_collect_graph_circular_routing() -> None:
    """Verify circular routing extracts cycle nodes, path representation, and CRITICAL severity."""
    gf = GraphFeatures(
        account_id="ACC_RING_A",
        has_cycle=True,
        cycle_count=1,
        cycle_lengths=[3],
        cycles=[["ACC_RING_A", "ACC_RING_B", "ACC_RING_C", "ACC_RING_A"]],
        contributing_cycle_nodes=["ACC_RING_A", "ACC_RING_B", "ACC_RING_C"],
    )

    items = collect_graph_evidence(gf)
    assert len(items) == 1
    item = items[0]

    assert item.source == EvidenceSource.GRAPH
    assert item.source_reference == "GRAPH:circular_routing"
    assert item.category == EvidenceCategory.CIRCULAR_ROUTING
    assert item.severity == EvidenceSeverity.CRITICAL
    assert "ACC_RING_A" in item.account_ids
    assert "ACC_RING_B" in item.account_ids
    assert "ACC_RING_C" in item.account_ids
    assert item.metrics["cycle_count"] == 1


def test_collect_graph_shared_infrastructure() -> None:
    """Verify shared devices and IPs generate distinct evidence items with correct severities."""
    gf = GraphFeatures(
        account_id="ACC_SYNDICATE_01",
        shared_device_count=3,
        associated_devices=["DEV_01", "DEV_02", "DEV_03"],
        accounts_per_shared_device={"DEV_01": 4, "DEV_02": 3, "DEV_03": 2},
        shared_ip_count=2,
        associated_ips=["10.0.0.1", "10.0.0.2"],
        accounts_per_shared_ip={"10.0.0.1": 5, "10.0.0.2": 2},
    )

    items = collect_graph_evidence(gf)
    assert len(items) == 2

    refs = [i.source_reference for i in items]
    assert "GRAPH:shared_device" in refs
    assert "GRAPH:shared_ip" in refs

    dev_item = next(i for i in items if i.source_reference == "GRAPH:shared_device")
    assert dev_item.category == EvidenceCategory.SHARED_INFRASTRUCTURE
    assert dev_item.severity == EvidenceSeverity.CRITICAL  # >= 3 devices
    assert "DEV_01" in dev_item.device_ids
    assert "DEV_02" in dev_item.device_ids

    ip_item = next(i for i in items if i.source_reference == "GRAPH:shared_ip")
    assert ip_item.category == EvidenceCategory.SHARED_INFRASTRUCTURE
    assert ip_item.severity == EvidenceSeverity.MEDIUM  # < 3 IPs
    assert "10.0.0.1" in ip_item.ip_addresses


def test_collect_graph_fan_ratio_and_downstream_layering() -> None:
    """Verify fan dispersion and multi-hop layering are extracted properly."""
    gf = GraphFeatures(
        account_id="ACC_HUB_01",
        fan_in_ratio=6.5,
        unique_senders_count=26,
        unique_receivers_count=4,
        max_downstream_path_length=4,
        downstream_accounts=["ACC_LAYER_1", "ACC_LAYER_2", "ACC_CASHOUT"],
        path_summary="ACC_HUB_01 -> ACC_LAYER_1 -> ACC_LAYER_2 -> ACC_CASHOUT",
    )

    items = collect_graph_evidence(gf)
    assert len(items) == 2

    refs = [i.source_reference for i in items]
    assert "GRAPH:fan_ratio" in refs
    assert "GRAPH:downstream_layering" in refs

    fan_item = next(i for i in items if i.source_reference == "GRAPH:fan_ratio")
    assert fan_item.severity == EvidenceSeverity.HIGH  # max ratio >= 5.0
    assert fan_item.metrics["fan_in_ratio"] == 6.5

    layer_item = next(i for i in items if i.source_reference == "GRAPH:downstream_layering")
    assert layer_item.severity == EvidenceSeverity.HIGH
    assert layer_item.metrics["max_downstream_hops"] == 4
    assert "ACC_LAYER_1" in layer_item.account_ids


def test_collect_graph_empty_and_none() -> None:
    """Verify empty or None graph features safely produce zero evidence items."""
    assert collect_graph_evidence(None) == []

    clean_gf = GraphFeatures(account_id="ACC_CLEAN_01")
    assert collect_graph_evidence(clean_gf) == []


def test_graph_path_direction_and_hop_count() -> None:
    """Verify directed downstream path preserves direction, hop counts, and account ordering."""
    ordered_path = ["ACC_ORIGIN", "ACC_MULE_1", "ACC_MULE_2", "ACC_DEST"]
    gf = GraphFeatures(
        account_id="ACC_ORIGIN",
        max_downstream_path_length=3,
        downstream_accounts=["ACC_MULE_1", "ACC_MULE_2", "ACC_DEST"],
        path_summary=" -> ".join(ordered_path),
    )

    items = collect_graph_evidence(gf)
    assert len(items) == 1
    item = items[0]

    assert item.metrics["max_downstream_hops"] == 3
    assert item.metrics["downstream_accounts_count"] == 3
    assert item.metrics["path_summary"] == "ACC_ORIGIN -> ACC_MULE_1 -> ACC_MULE_2 -> ACC_DEST"
    # Ensure root account is first in account_ids
    assert item.account_ids[0] == "ACC_ORIGIN"
    assert item.account_ids[1] == "ACC_MULE_1"
    assert item.account_ids[2] == "ACC_MULE_2"
