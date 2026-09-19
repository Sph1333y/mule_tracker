"""
MuleTrace AI — Graph Intelligence Engine Integration Tests.

Validates end-to-end GraphIntelligenceEngine workflows:
- extract_for_event with transaction ingestion
- analyze_account interface
- extract_features_sync synchronous invocation
- Negative and out-of-range hop depth clamping
- Automatic repository factory fallback
- Prefix resilience ('account:ACC-1' vs 'ACC-1')
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from app.domain.models import TransactionEvent
from app.engines.graph.intelligence import (
    GraphFeatures,
    GraphIntelligenceEngine,
    graph_intelligence_engine,
)
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
async def test_extract_for_event_with_ingestion():
    """extract_for_event ingests the transaction and computes features for both endpoints."""
    repo = NetworkXGraphRepository()
    engine = GraphIntelligenceEngine(repository=repo)
    tx = _tx("TX-EVENT-1", "ACC-SENDER", "ACC-RECEIVER", 7500.0)

    res = await engine.extract_for_event(tx, ingest=True)

    assert "sender" in res
    assert "receiver" in res

    f_sender = res["sender"]
    f_receiver = res["receiver"]

    assert f_sender.account_id == "ACC-SENDER"
    assert f_sender.out_degree == 1
    assert f_sender.outbound_volume_total == 7500.0

    assert f_receiver.account_id == "ACC-RECEIVER"
    assert f_receiver.in_degree == 1
    assert f_receiver.inbound_volume_total == 7500.0


@pytest.mark.anyio
async def test_analyze_account_alias():
    """analyze_account serves as an exact alias to extract_features."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-AL-1", "ACC-A", "ACC-B", 2000.0))
    engine = GraphIntelligenceEngine(repository=repo)

    f1 = await engine.extract_features("ACC-A")
    f2 = await engine.analyze_account("ACC-A")

    assert f1.to_dict() == f2.to_dict()


def test_extract_features_sync_wrapper():
    """extract_features_sync executes synchronously without active loop error."""
    repo = NetworkXGraphRepository()
    # Populate directly
    import asyncio
    asyncio.run(repo.add_transaction(_tx("TX-SYNC-1", "ACC-SYNC-A", "ACC-SYNC-B", 3000.0)))

    engine = GraphIntelligenceEngine(repository=repo)
    features = engine.extract_features_sync("ACC-SYNC-A")

    assert isinstance(features, GraphFeatures)
    assert features.out_degree == 1
    assert features.outbound_volume_total == 3000.0


@pytest.mark.anyio
async def test_negative_hop_depth_clamping():
    """Negative hop depth is safely clamped to 0 without raising exceptions."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-NEG-1", "ACC-A", "ACC-B", 1000.0))
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-A", hops=-5)
    assert features.hop_depth == 0
    assert features.neighboring_accounts_count == 0


@pytest.mark.anyio
async def test_account_prefix_resilience():
    """extract_features seamlessly accepts both 'account:ACC-99' and 'ACC-99'."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_tx("TX-PRE-1", "ACC-99", "ACC-100", 500.0))
    engine = GraphIntelligenceEngine(repository=repo)

    f_raw = await engine.extract_features("ACC-99")
    f_prefixed = await engine.extract_features("account:ACC-99")

    assert f_raw.account_id == "ACC-99"
    assert f_prefixed.account_id == "ACC-99"
    assert f_raw.out_degree == f_prefixed.out_degree
    assert f_raw.outbound_volume_total == f_prefixed.outbound_volume_total


def test_singleton_engine_exists():
    """The default singleton instance is initialized and accessible."""
    assert graph_intelligence_engine is not None
    assert isinstance(graph_intelligence_engine, GraphIntelligenceEngine)
