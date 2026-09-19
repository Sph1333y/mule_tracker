"""
MuleTrace AI — Graph Intelligence Invariant Verification Tests.

Validates the 12 non-negotiable architectural invariants required by Milestone 7:
- Invariant 1: Determinism (Same graph + inputs -> identical GraphFeatures)
- Invariant 2: Directionality (A -> B does not imply B -> A)
- Invariant 3: Unique-counterparty correctness (Multiple transactions to same counterparty do not inflate unique count)
- Invariant 4: Transaction-count correctness (Multiple transactions counted individually)
- Invariant 5: Hop boundedness (Monotonicity: higher hops >= lower hops reachable accounts)
- Invariant 6: Empty graph safety (Valid zeroed output without exceptions)
- Invariant 7: No false cycle (A -> B -> C directed path does NOT trigger cycle)
- Invariant 8: Real cycle detection (A -> B -> C -> A strictly detected)
- Invariant 9: Duplicate safety (Idempotency preserves integrity)
- Invariant 10: Input-order invariance (Reordering transactions yields identical feature payload)
- Invariant 11: Stable serialization (to_dict() produces identical JSON-compatible output)
- Invariant 12: No graph mutation from read operations (extract_features leaves graph untouched)
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from app.domain.models import TransactionEvent
from app.engines.graph.intelligence import GraphIntelligenceEngine
from app.repositories.graph_nx import NetworkXGraphRepository


def _tx(tx_id: str, u: str, v: str, amt: float = 1000.0, **kwargs) -> TransactionEvent:
    return TransactionEvent(
        transaction_id=tx_id,
        timestamp=datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc),
        amount=amt,
        sender_account=u,
        receiver_account=v,
        channel="UPI",
        **kwargs,
    )


# -----------------------------------------------------------------------------
# INVARIANT 1: DETERMINISM
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_1_determinism():
    """Extracting features repeatedly on identical graph state produces identical outputs."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-1", "ACC-A", "ACC-B", 500.0))
    await repo.add_transaction(_tx("TX-2", "ACC-B", "ACC-C", 400.0))
    await repo.add_transaction(_tx("TX-3", "ACC-C", "ACC-A", 300.0))
    engine = GraphIntelligenceEngine(repository=repo)

    f1 = await engine.extract_features("ACC-A")
    f2 = await engine.extract_features("ACC-A")

    assert f1.to_dict() == f2.to_dict()


# -----------------------------------------------------------------------------
# INVARIANT 2: DIRECTIONALITY
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_2_directionality():
    """A -> B strictly provides out_degree=1 for A, in_degree=0 for A, and vice versa for B."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-DIR", "ACC-SRC", "ACC-DST", 1000.0))
    engine = GraphIntelligenceEngine(repository=repo)

    src_f = await engine.extract_features("ACC-SRC")
    dst_f = await engine.extract_features("ACC-DST")

    assert src_f.out_degree == 1
    assert src_f.in_degree == 0
    assert src_f.unique_outbound_counterparties == 1
    assert src_f.unique_inbound_counterparties == 0

    assert dst_f.in_degree == 1
    assert dst_f.out_degree == 0
    assert dst_f.unique_inbound_counterparties == 1
    assert dst_f.unique_outbound_counterparties == 0


# -----------------------------------------------------------------------------
# INVARIANT 3: UNIQUE-COUNTERPARTY CORRECTNESS
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_3_unique_counterparties_not_inflated():
    """10 transfers from A to B must result in unique_outbound_counterparties == 1."""
    repo = NetworkXGraphRepository()
    for i in range(10):
        await repo.add_transaction(_tx(f"TX-{i}", "ACC-A", "ACC-B", 100.0))
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-A")
    assert features.unique_outbound_counterparties == 1
    assert features.unique_receivers_count == 1


# -----------------------------------------------------------------------------
# INVARIANT 4: TRANSACTION-COUNT CORRECTNESS
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_4_transaction_counts_preserved():
    """10 transfers from A to B must result in out_degree == 10 and outbound_tx_count == 10."""
    repo = NetworkXGraphRepository()
    for i in range(10):
        await repo.add_transaction(_tx(f"TX-{i}", "ACC-A", "ACC-B", 100.0))
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-A")
    assert features.out_degree == 10
    assert features.outbound_tx_count == 10
    assert features.outbound_volume_total == 1000.0


# -----------------------------------------------------------------------------
# INVARIANT 5: HOP BOUNDEDNESS (MONOTONICITY)
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_5_hop_boundedness():
    """Higher hop depth neighborhood must contain >= nodes than lower hop depth."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-1", "ACC-A", "ACC-B"))
    await repo.add_transaction(_tx("TX-2", "ACC-B", "ACC-C"))
    await repo.add_transaction(_tx("TX-3", "ACC-C", "ACC-D"))
    engine = GraphIntelligenceEngine(repository=repo)

    f_hop0 = await engine.extract_features("ACC-A", hops=0)
    f_hop1 = await engine.extract_features("ACC-A", hops=1)
    f_hop2 = await engine.extract_features("ACC-A", hops=2)
    f_hop3 = await engine.extract_features("ACC-A", hops=3)

    assert f_hop0.subgraph_node_count <= f_hop1.subgraph_node_count
    assert f_hop1.subgraph_node_count <= f_hop2.subgraph_node_count
    assert f_hop2.subgraph_node_count <= f_hop3.subgraph_node_count


# -----------------------------------------------------------------------------
# INVARIANT 6: EMPTY GRAPH SAFETY
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_6_empty_graph_safety():
    """Empty graph and unseen account queries produce valid zeroed data without crashing."""
    repo = NetworkXGraphRepository()
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("NON-EXISTENT")
    assert features.account_id == "NON-EXISTENT"
    assert features.in_degree == 0
    assert features.out_degree == 0
    assert features.has_cycle is False
    assert features.evidence_signals == []
    assert features.to_dict() is not None


# -----------------------------------------------------------------------------
# INVARIANT 7: NO FALSE CYCLES
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_7_no_false_cycle():
    """A strictly linear directed chain A -> B -> C -> D has zero cycles."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-1", "ACC-A", "ACC-B"))
    await repo.add_transaction(_tx("TX-2", "ACC-B", "ACC-C"))
    await repo.add_transaction(_tx("TX-3", "ACC-C", "ACC-D"))
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-A", max_depth=5)
    assert features.has_cycle is False
    assert features.cycle_count == 0
    assert features.cycles == []
    assert features.contributing_cycle_nodes == []


# -----------------------------------------------------------------------------
# INVARIANT 8: REAL CYCLE DETECTION
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_8_real_cycle_detection():
    """A true circular flow A -> B -> C -> A is detected with exact length 3."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-1", "ACC-A", "ACC-B"))
    await repo.add_transaction(_tx("TX-2", "ACC-B", "ACC-C"))
    await repo.add_transaction(_tx("TX-3", "ACC-C", "ACC-A"))
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-A", max_depth=5)
    assert features.has_cycle is True
    assert features.cycle_count == 1
    assert features.cycle_lengths == [3]
    assert features.cycles[0] == ["ACC-A", "ACC-B", "ACC-C", "ACC-A"]


# -----------------------------------------------------------------------------
# INVARIANT 9: DUPLICATE SAFETY (IDEMPOTENCY)
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_9_duplicate_safety():
    """Re-ingesting the exact same transaction ID updates/maintains identical topological state."""
    repo = NetworkXGraphRepository()
    tx = _tx("TX-IDEMPOTENT", "ACC-A", "ACC-B", 2500.0)
    await repo.add_transaction(tx)
    engine = GraphIntelligenceEngine(repository=repo)
    f1 = await engine.extract_features("ACC-A")

    await repo.add_transaction(tx)
    f2 = await engine.extract_features("ACC-A")

    assert f1.out_degree == f2.out_degree
    assert f1.outbound_volume_total == f2.outbound_volume_total
    assert f1.to_dict() == f2.to_dict()


# -----------------------------------------------------------------------------
# INVARIANT 10: INPUT-ORDER INVARIANCE
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_10_input_order_invariance():
    """Reversing transaction insertion order results in identical extracted features."""
    txs = [
        _tx("TX-1", "ACC-A", "ACC-B", 100.0),
        _tx("TX-2", "ACC-A", "ACC-C", 200.0),
        _tx("TX-3", "ACC-B", "ACC-A", 50.0),
    ]

    repo_forward = NetworkXGraphRepository()
    for t in txs:
        await repo_forward.add_transaction(t)

    repo_reverse = NetworkXGraphRepository()
    for t in reversed(txs):
        await repo_reverse.add_transaction(t)

    eng_forward = GraphIntelligenceEngine(repository=repo_forward)
    eng_reverse = GraphIntelligenceEngine(repository=repo_reverse)

    f_fwd = await eng_forward.extract_features("ACC-A")
    f_rev = await eng_reverse.extract_features("ACC-A")

    # Audit timestamps may differ, so compare topological payload
    d_fwd = f_fwd.to_dict()
    d_rev = f_rev.to_dict()
    d_fwd["reference_timestamp"] = None
    d_rev["reference_timestamp"] = None
    assert d_fwd == d_rev


# -----------------------------------------------------------------------------
# INVARIANT 11: STABLE SERIALIZATION
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_11_stable_serialization():
    """to_dict() returns stable, JSON-compatible nested dictionaries."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-1", "ACC-A", "ACC-B", 1000.0))
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-A")
    d = features.to_dict()

    assert isinstance(d, dict)
    assert d["account_id"] == "ACC-A"
    assert "degrees" in d
    assert "fan_in_out" in d
    assert "neighborhood" in d
    assert "connectivity" in d
    assert "cycles" in d
    assert "shared_entities" in d
    assert "audit" in d
    assert d["degrees"]["out_degree"] == 1


# -----------------------------------------------------------------------------
# INVARIANT 12: NO GRAPH MUTATION FROM READ OPERATIONS
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_invariant_12_no_graph_mutation_on_read():
    """Extracting features must NOT modify node or edge counts of the repository graph."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-1", "ACC-A", "ACC-B", 1000.0))
    engine = GraphIntelligenceEngine(repository=repo)

    initial_nodes = repo.graph.number_of_nodes()
    initial_edges = repo.graph.number_of_edges()

    # Repeated reads across accounts
    await engine.extract_features("ACC-A", hops=2)
    await engine.extract_features("ACC-B", hops=2)
    await engine.extract_features("ACC-UNKNOWN", hops=2)

    assert repo.graph.number_of_nodes() == initial_nodes
    assert repo.graph.number_of_edges() == initial_edges
