"""
MuleTrace AI — Common Graph Repository Contract & Parity Test Suite.

Validates concrete implementations of the domain GraphRepository port:
- NetworkXGraphRepository (BUILD IT phase / local in-memory)
- Neo4jGraphRepository (Existing production wrapper)
- Controlled Graph Repository Factory (get_graph_repository)

Uses deterministic fixtures A through G to test:
- Simple transfer (A -> B)
- Multiple parallel transactions between same accounts
- Multi-hop layering chains (A -> B -> C -> D)
- Circular mule cycles (A -> B -> C -> A) vs linear chains
- Device and IP relationships
- Idempotency, read immutability, and instance isolation
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import pytest

from app.database.neo4j import neo4j_manager
from app.domain.interfaces import GraphRepository
from app.domain.models import TransactionEvent
from app.repositories.graph_factory import DEFAULT_GRAPH_BACKEND, get_graph_repository
from app.repositories.graph_neo4j import Neo4jGraphRepository
from app.repositories.graph_nx import NetworkXGraphRepository


# ── Deterministic Fixture Definitions ──────────────────────────────────


@pytest.fixture
def nx_repo() -> NetworkXGraphRepository:
    """Provide a clean, isolated NetworkXGraphRepository instance."""
    return NetworkXGraphRepository()


@pytest.fixture
def neo4j_repo() -> Neo4jGraphRepository:
    """Provide a Neo4jGraphRepository instance."""
    return Neo4jGraphRepository()


@pytest.fixture
def fixture_a_simple_transfer() -> TransactionEvent:
    """FIXTURE A: Simple transfer A -> B."""
    return TransactionEvent(
        transaction_id="TX-A-B-001",
        timestamp=datetime(2025, 4, 1, 10, 0, 0, tzinfo=timezone.utc),
        sender_account="ACC-A",
        receiver_account="ACC-B",
        amount=1000.0,
        currency="INR",
        channel="UPI",
        sender_bank="State Bank of India",
        receiver_bank="HDFC Bank",
    )


@pytest.fixture
def fixture_b_multiple_transactions() -> list[TransactionEvent]:
    """FIXTURE B: Multiple transactions A -> B."""
    return [
        TransactionEvent(
            transaction_id="TX-A-B-001",
            timestamp=datetime(2025, 4, 1, 10, 0, 0, tzinfo=timezone.utc),
            sender_account="ACC-A",
            receiver_account="ACC-B",
            amount=1000.0,
        ),
        TransactionEvent(
            transaction_id="TX-A-B-002",
            timestamp=datetime(2025, 4, 1, 10, 15, 0, tzinfo=timezone.utc),
            sender_account="ACC-A",
            receiver_account="ACC-B",
            amount=2500.0,
        ),
        TransactionEvent(
            transaction_id="TX-A-B-003",
            timestamp=datetime(2025, 4, 1, 10, 30, 0, tzinfo=timezone.utc),
            sender_account="ACC-A",
            receiver_account="ACC-B",
            amount=49000.0,
        ),
    ]


@pytest.fixture
def fixture_c_chain() -> list[TransactionEvent]:
    """FIXTURE C: Multi-hop chain A -> B -> C -> D."""
    return [
        TransactionEvent(
            transaction_id="TX-CHAIN-1",
            timestamp=datetime(2025, 4, 1, 11, 0, 0, tzinfo=timezone.utc),
            sender_account="ACC-A",
            receiver_account="ACC-B",
            amount=100000.0,
        ),
        TransactionEvent(
            transaction_id="TX-CHAIN-2",
            timestamp=datetime(2025, 4, 1, 11, 10, 0, tzinfo=timezone.utc),
            sender_account="ACC-B",
            receiver_account="ACC-C",
            amount=98000.0,
        ),
        TransactionEvent(
            transaction_id="TX-CHAIN-3",
            timestamp=datetime(2025, 4, 1, 11, 20, 0, tzinfo=timezone.utc),
            sender_account="ACC-C",
            receiver_account="ACC-D",
            amount=95000.0,
        ),
    ]


# ── Common Contract Tests against NetworkXGraphRepository ─────────────


@pytest.mark.asyncio
async def test_contract_empty_repository(nx_repo: NetworkXGraphRepository):
    """Contract: Empty repository queries return empty, non-null structures."""
    subgraph = await nx_repo.get_subgraph("NONEXISTENT_ACC")
    assert isinstance(subgraph, dict)
    assert subgraph["nodes"] == []
    assert subgraph["edges"] == []

    trace = await nx_repo.trace_transaction_path("NONEXISTENT_TX")
    assert isinstance(trace, dict)
    assert trace["nodes"] == []
    assert trace["edges"] == []
    assert "not found" in trace["path_summary"]

    cycles = await nx_repo.find_circular_paths("NONEXISTENT_ACC")
    assert isinstance(cycles, list)
    assert cycles == []


@pytest.mark.asyncio
async def test_contract_fixture_a_simple_transfer(
    nx_repo: NetworkXGraphRepository, fixture_a_simple_transfer: TransactionEvent
):
    """Contract Fixture A: Adding a simple transfer creates accounts, edge, and preserves ID."""
    await nx_repo.add_transaction(fixture_a_simple_transfer)

    # Subgraph centered on ACC-A should include ACC-A and ACC-B
    subgraph = await nx_repo.get_subgraph("ACC-A", hops=1)
    node_labels = {n["label"] for n in subgraph["nodes"]}
    assert "ACC-A" in node_labels
    assert "ACC-B" in node_labels

    # Verify edge attributes and directionality
    assert len(subgraph["edges"]) == 1
    edge = subgraph["edges"][0]
    assert edge["source"] == "account:ACC-A"
    assert edge["target"] == "account:ACC-B"
    assert edge["transaction_id"] == "TX-A-B-001"
    assert edge["amount"] == 1000.0
    assert edge["relationship"] == "TRANSFERRED_FUNDS"


@pytest.mark.asyncio
async def test_contract_fixture_b_multiple_transactions_preserve_distinction(
    nx_repo: NetworkXGraphRepository,
    fixture_b_multiple_transactions: list[TransactionEvent],
):
    """Contract Fixture B: Multiple transactions between same accounts do not collapse."""
    for tx in fixture_b_multiple_transactions:
        await nx_repo.add_transaction(tx)

    subgraph = await nx_repo.get_subgraph("ACC-A", hops=1)
    assert len(subgraph["edges"]) == 3

    edge_ids = {e["transaction_id"] for e in subgraph["edges"]}
    assert edge_ids == {"TX-A-B-001", "TX-A-B-002", "TX-A-B-003"}

    amounts = sorted([e["amount"] for e in subgraph["edges"]])
    assert amounts == [1000.0, 2500.0, 49000.0]


@pytest.mark.asyncio
async def test_contract_duplicate_insertion_idempotency(
    nx_repo: NetworkXGraphRepository, fixture_a_simple_transfer: TransactionEvent
):
    """Contract: Duplicate insertion of the same transaction preserves exact graph counts."""
    await nx_repo.add_transaction(fixture_a_simple_transfer)
    await nx_repo.add_transaction(fixture_a_simple_transfer)

    subgraph = await nx_repo.get_subgraph("ACC-A", hops=1)
    assert len(subgraph["nodes"]) == 2
    assert len(subgraph["edges"]) == 1


@pytest.mark.asyncio
async def test_contract_fixture_c_chain_path_and_subgraph(
    nx_repo: NetworkXGraphRepository, fixture_c_chain: list[TransactionEvent]
):
    """Contract Fixture C: Layering chain traversal and path tracing across hops."""
    for tx in fixture_c_chain:
        await nx_repo.add_transaction(tx)

    # 1. Subgraph expansion by hop distance
    sub_hop1 = await nx_repo.get_subgraph("ACC-A", hops=1)
    assert len(sub_hop1["nodes"]) == 2

    sub_hop2 = await nx_repo.get_subgraph("ACC-A", hops=2)
    assert len(sub_hop2["nodes"]) == 3

    sub_hop3 = await nx_repo.get_subgraph("ACC-A", hops=3)
    assert len(sub_hop3["nodes"]) == 4

    # 2. Transaction path tracing from the first transaction
    trace = await nx_repo.trace_transaction_path("TX-CHAIN-1", max_depth=5)
    assert len(trace["edges"]) == 3
    assert "3 hops" in trace["path_summary"]
    assert "Layering detected" in trace["path_summary"]


@pytest.mark.asyncio
async def test_contract_fixture_d_cycle_detection(
    nx_repo: NetworkXGraphRepository,
):
    """Contract Fixture D: Genuine circular cycles detected; linear paths rejected."""
    # 1. Linear sequence: A -> B -> C (NOT a cycle)
    await nx_repo.add_transaction(
        TransactionEvent(
            transaction_id="TX-L1",
            timestamp=datetime.now(timezone.utc),
            sender_account="ACC-U",
            receiver_account="ACC-V",
            amount=500.0,
        )
    )
    await nx_repo.add_transaction(
        TransactionEvent(
            transaction_id="TX-L2",
            timestamp=datetime.now(timezone.utc),
            sender_account="ACC-V",
            receiver_account="ACC-W",
            amount=500.0,
        )
    )
    assert await nx_repo.find_circular_paths("ACC-U") == []

    # 2. Complete the cycle: W -> U
    await nx_repo.add_transaction(
        TransactionEvent(
            transaction_id="TX-L3",
            timestamp=datetime.now(timezone.utc),
            sender_account="ACC-W",
            receiver_account="ACC-U",
            amount=480.0,
        )
    )
    cycles = await nx_repo.find_circular_paths("ACC-U", max_depth=5)
    assert len(cycles) == 1
    assert cycles[0] == ["ACC-U", "ACC-V", "ACC-W", "ACC-U"]


@pytest.mark.asyncio
async def test_contract_fixture_e_device_linkage(
    nx_repo: NetworkXGraphRepository,
):
    """Contract Fixture E: Account to Device linkage representation and idempotency."""
    await nx_repo.link_account_device("ACC-MULE-1", "DEV-FP-ALPHA")
    subgraph = await nx_repo.get_subgraph("ACC-MULE-1", hops=1)

    node_types = {n["type"] for n in subgraph["nodes"]}
    assert "account" in node_types
    assert "device" in node_types

    edge_rels = {e["relationship"] for e in subgraph["edges"]}
    assert "USED_DEVICE" in edge_rels

    # Duplicate call is idempotent
    await nx_repo.link_account_device("ACC-MULE-1", "DEV-FP-ALPHA")
    subgraph_dup = await nx_repo.get_subgraph("ACC-MULE-1", hops=1)
    assert len(subgraph_dup["edges"]) == 1


@pytest.mark.asyncio
async def test_contract_fixture_f_ip_linkage(
    nx_repo: NetworkXGraphRepository,
):
    """Contract Fixture F: Account to IP linkage representation when provided on event."""
    event = TransactionEvent(
        transaction_id="TX-IP-001",
        timestamp=datetime.now(timezone.utc),
        sender_account="ACC-IP-TEST",
        receiver_account="ACC-DST",
        amount=5000.0,
        ip_address="203.0.113.195",
    )
    await nx_repo.add_transaction(event)

    subgraph = await nx_repo.get_subgraph("ACC-IP-TEST", hops=1)
    node_types = {n["type"] for n in subgraph["nodes"]}
    assert "ip" in node_types

    edge_rels = {e["relationship"] for e in subgraph["edges"]}
    assert "USES_IP" in edge_rels


@pytest.mark.asyncio
async def test_contract_read_immutability(
    nx_repo: NetworkXGraphRepository, fixture_a_simple_transfer: TransactionEvent
):
    """Contract: Read queries must not mutate internal graph state."""
    await nx_repo.add_transaction(fixture_a_simple_transfer)
    node_count_before = nx_repo.graph.number_of_nodes()
    edge_count_before = nx_repo.graph.number_of_edges()

    # Execute multiple read calls
    _ = await nx_repo.get_subgraph("ACC-A", hops=2)
    _ = await nx_repo.trace_transaction_path("TX-A-B-001")
    _ = await nx_repo.find_circular_paths("ACC-A")

    assert nx_repo.graph.number_of_nodes() == node_count_before
    assert nx_repo.graph.number_of_edges() == edge_count_before


# ── Controlled Adapter Selection Tests ────────────────────────────────


def test_factory_default_backend():
    """Verify factory defaults to 'neo4j', strictly preserving production flow."""
    # Ensure GRAPH_BACKEND is unset or default
    current_env = os.environ.get("GRAPH_BACKEND")
    try:
        if "GRAPH_BACKEND" in os.environ:
            del os.environ["GRAPH_BACKEND"]
        repo = get_graph_repository()
        assert isinstance(repo, Neo4jGraphRepository)
        assert DEFAULT_GRAPH_BACKEND == "neo4j"
    finally:
        if current_env is not None:
            os.environ["GRAPH_BACKEND"] = current_env


def test_factory_explicit_selection():
    """Verify factory returns appropriate adapter when explicitly passed."""
    repo_nx = get_graph_repository(backend="networkx")
    assert isinstance(repo_nx, NetworkXGraphRepository)

    repo_neo = get_graph_repository(backend="neo4j")
    assert isinstance(repo_neo, Neo4jGraphRepository)


def test_factory_env_selection(monkeypatch: pytest.MonkeyPatch):
    """Verify factory respects GRAPH_BACKEND environment variable."""
    monkeypatch.setenv("GRAPH_BACKEND", "networkx")
    repo = get_graph_repository()
    assert isinstance(repo, NetworkXGraphRepository)

    monkeypatch.setenv("GRAPH_BACKEND", "neo4j")
    repo_neo = get_graph_repository()
    assert isinstance(repo_neo, Neo4jGraphRepository)


def test_factory_invalid_backend_raises_error():
    """Verify factory raises ValueError on unsupported backend."""
    with pytest.raises(ValueError, match="Unsupported GRAPH_BACKEND 'invalid_backend'"):
        get_graph_repository(backend="invalid_backend")


# ── Neo4j Adapter Offline / Disconnected Behavior Tests ───────────────


@pytest.mark.asyncio
async def test_neo4j_adapter_offline_graceful_fallback(
    neo4j_repo: Neo4jGraphRepository,
    fixture_a_simple_transfer: TransactionEvent,
):
    """Verify Neo4j adapter degrades gracefully and does not throw if daemon is offline."""
    if not neo4j_repo.is_connected:
        # In disconnected state, methods must safely return empty structures without crashing
        await neo4j_repo.add_transaction(fixture_a_simple_transfer)
        subgraph = await neo4j_repo.get_subgraph("ACC-A")
        assert subgraph["nodes"] == []
        assert subgraph["edges"] == []

        trace = await neo4j_repo.trace_transaction_path("TX-A-B-001")
        assert "not be established" in trace["path_summary"]

        cycles = await neo4j_repo.find_circular_paths("ACC-A")
        assert cycles == []


@pytest.mark.skipif(
    not neo4j_manager.is_connected,
    reason="Neo4j daemon not connected in test environment",
)
@pytest.mark.asyncio
async def test_neo4j_live_contract_simple_transfer(
    neo4j_repo: Neo4jGraphRepository,
    fixture_a_simple_transfer: TransactionEvent,
):
    """Live Neo4j test: Executed only when a live Neo4j daemon is actively connected."""
    await neo4j_repo.add_transaction(fixture_a_simple_transfer)
    trace = await neo4j_repo.trace_transaction_path(
        fixture_a_simple_transfer.transaction_id
    )
    assert len(trace["edges"]) >= 1
