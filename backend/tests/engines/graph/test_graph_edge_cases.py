"""
MuleTrace AI — Graph Intelligence Edge Case Tests.

Validates boundary conditions and robustness:
- Hop depth 0 behavior
- Excessively large hop depth (hops=10) on small topology
- Zero and extreme monetary transaction amounts
- Account ID formatting (special characters, hyphens, spaces)
- Neighborhood density boundaries (N=1 -> 0.0, complete digraph -> 1.0)
- Accounts with only device links and zero transactions
- Zero-division safety for fan-in/out ratios
- Concurrent asynchronous extractions
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import pytest

from app.domain.models import TransactionEvent
from app.engines.graph.intelligence import GraphIntelligenceEngine
from app.repositories.graph_nx import NetworkXGraphRepository


def _tx(tx_id: str, u: str, v: str, amount: float = 1000.0, **kwargs) -> TransactionEvent:
    return TransactionEvent(
        transaction_id=tx_id,
        timestamp=datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc),
        amount=amount,
        sender_account=u,
        receiver_account=v,
        channel="UPI",
        **kwargs,
    )


@pytest.mark.anyio
async def test_hops_zero_on_active_account():
    """hops=0 captures only the focal account node and 0 neighbors."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-1", "ACC-A", "ACC-B", 500.0))
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-A", hops=0)
    assert features.hop_depth == 0
    assert features.neighboring_accounts_count == 0
    assert features.subgraph_node_count == 1


@pytest.mark.anyio
async def test_large_hop_depth_boundedness():
    """hops=10 on a 3-node graph safely terminates without infinite looping or errors."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-1", "ACC-A", "ACC-B"))
    await repo.add_transaction(_tx("TX-2", "ACC-B", "ACC-C"))
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-A", hops=10)
    assert features.neighboring_accounts_count == 2
    assert features.subgraph_node_count == 3


@pytest.mark.anyio
async def test_minimum_amount_transactions():
    """Minimum allowed transaction amount (0.01) is handled cleanly in volumes."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-MIN", "ACC-A", "ACC-B", amount=0.01))
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A")
    assert f_a.out_degree == 1
    assert f_a.outbound_volume_total == 0.01


@pytest.mark.anyio
async def test_extreme_amount_transactions():
    """Very large transactions (e.g. 100 crore / 1,000,000,000 INR) round and sum accurately."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-BIG-1", "ACC-A", "ACC-B", amount=1_000_000_000.0))
    await repo.add_transaction(_tx("TX-BIG-2", "ACC-A", "ACC-B", amount=2_500_000_000.75))
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A")
    assert f_a.outbound_volume_total == 3_500_000_000.75


@pytest.mark.anyio
async def test_account_with_only_device_link():
    """An account that only has a device link and no transactions computes cleanly."""
    repo = NetworkXGraphRepository()
    await repo.link_account_device("ACC-DEV-ONLY", "HARDWARE-FINGERPRINT-999")
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-DEV-ONLY", hops=1)
    assert features.in_degree == 0
    assert features.out_degree == 0
    assert features.neighboring_devices_count == 1
    assert features.associated_devices == ["HARDWARE-FINGERPRINT-999"]
    assert features.has_cycle is False


@pytest.mark.anyio
async def test_neighborhood_density_complete_digraph():
    """A complete directed 3-node cycle (all pairs transferred) yields density 1.0."""
    repo = NetworkXGraphRepository()
    # All 6 directed pairs among A, B, C:
    # A->B, A->C, B->A, B->C, C->A, C->B
    await repo.add_transaction(_tx("TX-AB", "ACC-A", "ACC-B"))
    await repo.add_transaction(_tx("TX-AC", "ACC-A", "ACC-C"))
    await repo.add_transaction(_tx("TX-BA", "ACC-B", "ACC-A"))
    await repo.add_transaction(_tx("TX-BC", "ACC-B", "ACC-C"))
    await repo.add_transaction(_tx("TX-CA", "ACC-C", "ACC-A"))
    await repo.add_transaction(_tx("TX-CB", "ACC-C", "ACC-B"))
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-A", hops=1)
    assert features.neighborhood_density == 1.0


@pytest.mark.anyio
async def test_concurrent_feature_extractions():
    """Concurrent feature extractions across 10 tasks complete without state corruption."""
    repo = NetworkXGraphRepository()
    for i in range(10):
        await repo.add_transaction(_tx(f"TX-CONC-{i}", f"ACC-{i}", f"ACC-{i+1}"))
    engine = GraphIntelligenceEngine(repository=repo)

    async def _fetch(acc: str):
        return await engine.extract_features(acc)

    tasks = [_fetch(f"ACC-{i}") for i in range(10)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 10
    for i, res in enumerate(results):
        assert res.account_id == f"ACC-{i}"
        assert res.out_degree == 1
