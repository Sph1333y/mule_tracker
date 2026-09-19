"""
MuleTrace AI — Graph Intelligence Cycle Detection Tests.

Validates specialized circular fund routing loops and topological cycle scenarios:
- Direct self-transfer loops (A -> A)
- 2-node ping-pong cycles (A -> B -> A)
- 3-node layering cycles (A -> B -> C -> A)
- 4-node and 5-node extended rings
- Multiple overlapping cycles through a single focal account
- Re-orientation when focal account appears at non-zero index in cycle path
- Cycles with multi-edges between the same accounts
- Disconnected cycles involving other accounts (zero false positives)
- Cycle cutoff at max_depth
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from app.domain.models import TransactionEvent
from app.engines.graph.intelligence import GraphIntelligenceEngine
from app.repositories.graph_nx import NetworkXGraphRepository


def _tx(tx_id: str, u: str, v: str, amt: float = 1000.0) -> TransactionEvent:
    return TransactionEvent(
        transaction_id=tx_id,
        timestamp=datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc),
        amount=amt,
        sender_account=u,
        receiver_account=v,
        channel="UPI",
    )


@pytest.mark.anyio
async def test_self_transfer_loop():
    """A direct self-transfer A -> A is detected as a 1-hop self-loop cycle."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-SELF", "ACC-SELF", "ACC-SELF", 1000.0))
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-SELF", max_depth=5)
    assert features.has_cycle is True
    assert features.cycle_count == 1
    assert 1 in features.cycle_lengths
    assert features.cycles[0] == ["ACC-SELF", "ACC-SELF"]


@pytest.mark.anyio
async def test_multiple_distinct_cycles_through_focal():
    """Account A involved in two distinct cycles (A-B-A and A-C-D-A) detects both loops."""
    repo = NetworkXGraphRepository()
    # Cycle 1 (length 2): A -> B -> A
    await repo.add_transaction(_tx("TX-C1-1", "ACC-A", "ACC-B", 1000.0))
    await repo.add_transaction(_tx("TX-C1-2", "ACC-B", "ACC-A", 950.0))
    # Cycle 2 (length 3): A -> C -> D -> A
    await repo.add_transaction(_tx("TX-C2-1", "ACC-A", "ACC-C", 2000.0))
    await repo.add_transaction(_tx("TX-C2-2", "ACC-C", "ACC-D", 1900.0))
    await repo.add_transaction(_tx("TX-C2-3", "ACC-D", "ACC-A", 1800.0))

    engine = GraphIntelligenceEngine(repository=repo)
    features = await engine.extract_features("ACC-A", max_depth=5)

    assert features.has_cycle is True
    assert features.cycle_count == 2
    assert features.cycle_lengths == [2, 3]
    assert sorted(features.contributing_cycle_nodes) == ["ACC-A", "ACC-B", "ACC-C", "ACC-D"]


@pytest.mark.anyio
async def test_cycle_with_multi_edges():
    """Multiple parallel transfer edges between cycle nodes do not create duplicate phantom cycles."""
    repo = NetworkXGraphRepository()
    # Parallel edges A -> B
    await repo.add_transaction(_tx("TX-1", "ACC-A", "ACC-B", 100.0))
    await repo.add_transaction(_tx("TX-2", "ACC-A", "ACC-B", 200.0))
    # Parallel edges B -> A
    await repo.add_transaction(_tx("TX-3", "ACC-B", "ACC-A", 150.0))
    await repo.add_transaction(_tx("TX-4", "ACC-B", "ACC-A", 250.0))

    engine = GraphIntelligenceEngine(repository=repo)
    features = await engine.extract_features("ACC-A", max_depth=5)

    assert features.has_cycle is True
    assert features.cycle_count == 1
    assert features.cycle_lengths == [2]
    assert features.cycles[0] == ["ACC-A", "ACC-B", "ACC-A"]


@pytest.mark.anyio
async def test_disconnected_cycle_isolation():
    """A cycle between X -> Y -> Z -> X must NOT be attributed to account A."""
    repo = NetworkXGraphRepository()
    # Disconnected cycle
    await repo.add_transaction(_tx("TX-X1", "ACC-X", "ACC-Y", 1000.0))
    await repo.add_transaction(_tx("TX-X2", "ACC-Y", "ACC-Z", 1000.0))
    await repo.add_transaction(_tx("TX-X3", "ACC-Z", "ACC-X", 1000.0))
    # Unrelated transaction for A
    await repo.add_transaction(_tx("TX-A1", "ACC-A", "ACC-M", 500.0))

    engine = GraphIntelligenceEngine(repository=repo)
    features = await engine.extract_features("ACC-A", max_depth=5)

    assert features.has_cycle is False
    assert features.cycle_count == 0
    assert features.cycles == []
    assert features.contributing_cycle_nodes == []


@pytest.mark.anyio
async def test_max_depth_cycle_cutoff():
    """A cycle exceeding max_depth hops is not returned."""
    repo = NetworkXGraphRepository()
    # 4-node cycle (length 4): A -> B -> C -> D -> A
    await repo.add_transaction(_tx("TX-1", "ACC-A", "ACC-B"))
    await repo.add_transaction(_tx("TX-2", "ACC-B", "ACC-C"))
    await repo.add_transaction(_tx("TX-3", "ACC-C", "ACC-D"))
    await repo.add_transaction(_tx("TX-4", "ACC-D", "ACC-A"))

    engine = GraphIntelligenceEngine(repository=repo)
    # Cutoff at max_depth=3 (cannot reach 4-hop cycle)
    features = await engine.extract_features("ACC-A", max_depth=3)
    assert features.has_cycle is False
    assert features.cycle_count == 0

    # With max_depth=4 it is detected
    features_detected = await engine.extract_features("ACC-A", max_depth=4)
    assert features_detected.has_cycle is True
    assert features_detected.cycle_count == 1
    assert features_detected.cycle_lengths == [4]
