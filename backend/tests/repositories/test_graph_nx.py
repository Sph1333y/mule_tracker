"""
MuleTrace AI — NetworkX Graph Repository Tests & Invariant Verification.

Comprehensive test suite verifying:
- Adapter initialization and empty graph behavior
- Heterogeneous node creation (Account, Device, IP)
- Directed multi-edge transaction preservation
- Subgraph querying and multi-hop traversal
- Layering transaction path tracing
- Circular cycle detection (mule loops)
- Duplicate idempotency
- The 7 Graph Invariants (collision prevention, instance isolation, immutability on read)
- Golden transaction integration
- Strict dependency boundary isolation
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

import pytest

from app.domain.interfaces import GraphRepository
from app.domain.models import TransactionEvent
from app.domain.transaction_mapper import TransactionMapper
from app.repositories.graph_nx import NetworkXGraphRepository


@pytest.fixture
def repo() -> NetworkXGraphRepository:
    """Create a fresh, isolated in-memory NetworkXGraphRepository instance."""
    return NetworkXGraphRepository()


@pytest.fixture
def sample_event() -> TransactionEvent:
    """Create a canonical sample TransactionEvent."""
    return TransactionEvent(
        transaction_id="TXN-NX-001",
        timestamp=datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
        sender_account="ACC-101",
        receiver_account="ACC-102",
        amount=25000.0,
        currency="INR",
        channel="UPI",
        sender_bank="State Bank of India",
        receiver_bank="HDFC Bank",
        device_id="DEV-FINGERPRINT-101",
        ip_address="192.168.1.15",
        narration="Test peer-to-peer transfer",
    )


# ── 1. Basic Adapter Lifecycle & Contract Compliance ──────────────────


def test_repository_initialization(repo: NetworkXGraphRepository):
    """Verify initialization and GraphRepository inheritance."""
    assert isinstance(repo, GraphRepository)
    assert repo.graph.number_of_nodes() == 0
    assert repo.graph.number_of_edges() == 0


@pytest.mark.asyncio
async def test_empty_graph_behavior(repo: NetworkXGraphRepository):
    """Verify empty graph query behavior does not raise errors."""
    subgraph = await repo.get_subgraph("ACC-NONEXISTENT")
    assert subgraph["nodes"] == []
    assert subgraph["edges"] == []
    assert subgraph["account_id"] == "ACC-NONEXISTENT"

    path = await repo.trace_transaction_path("TXN-NONEXISTENT")
    assert path["nodes"] == []
    assert path["edges"] == []
    assert "not found" in path["path_summary"]

    cycles = await repo.find_circular_paths("ACC-NONEXISTENT")
    assert cycles == []


# ── 2. add_transaction & Heterogeneous Representation ─────────────────


@pytest.mark.asyncio
async def test_add_transaction_and_node_creation(
    repo: NetworkXGraphRepository, sample_event: TransactionEvent
):
    """Verify node and edge creation from TransactionEvent."""
    await repo.add_transaction(sample_event)

    # Verify sender and receiver nodes exist with correct attributes
    s_node = "account:ACC-101"
    r_node = "account:ACC-102"
    assert s_node in repo.graph
    assert r_node in repo.graph

    assert repo.graph.nodes[s_node]["type"] == "account"
    assert repo.graph.nodes[s_node]["account_number"] == "ACC-101"
    assert repo.graph.nodes[s_node]["bank_name"] == "State Bank of India"

    assert repo.graph.nodes[r_node]["type"] == "account"
    assert repo.graph.nodes[r_node]["account_number"] == "ACC-102"
    assert repo.graph.nodes[r_node]["bank_name"] == "HDFC Bank"

    # Verify directed edge exists with transaction attributes
    assert repo.graph.has_edge(s_node, r_node, key="TXN-NX-001")
    edge_data = repo.graph.get_edge_data(s_node, r_node, key="TXN-NX-001")
    assert edge_data["amount"] == 25000.0
    assert edge_data["channel"] == "UPI"
    assert edge_data["relationship"] == "TRANSFERRED_FUNDS"
    assert edge_data["ref"] == "TXN-NX-001"

    # Verify device and IP linkages
    d_node = "device:DEV-FINGERPRINT-101"
    ip_node = "ip:192.168.1.15"
    assert d_node in repo.graph
    assert ip_node in repo.graph
    assert repo.graph.has_edge(
        s_node, d_node, key="link:account:ACC-101->device:DEV-FINGERPRINT-101"
    )
    assert repo.graph.has_edge(
        s_node, ip_node, key="ip_link:account:ACC-101->ip:192.168.1.15"
    )


@pytest.mark.asyncio
async def test_duplicate_transaction_idempotency(
    repo: NetworkXGraphRepository, sample_event: TransactionEvent
):
    """Verify adding the exact same transaction twice is strictly idempotent."""
    await repo.add_transaction(sample_event)
    initial_nodes = repo.graph.number_of_nodes()
    initial_edges = repo.graph.number_of_edges()

    # Re-insert the identical event
    await repo.add_transaction(sample_event)

    assert repo.graph.number_of_nodes() == initial_nodes
    assert repo.graph.number_of_edges() == initial_edges
    assert repo.graph.has_edge(
        "account:ACC-101", "account:ACC-102", key="TXN-NX-001"
    )


@pytest.mark.asyncio
async def test_multiple_transactions_between_same_accounts_preserved(
    repo: NetworkXGraphRepository,
):
    """Verify multiple distinct transactions between the same pair are preserved (MultiDiGraph)."""
    tx1 = TransactionEvent(
        transaction_id="TXN-MULTI-1",
        timestamp=datetime(2025, 3, 1, 10, 0, tzinfo=timezone.utc),
        sender_account="ACC-A",
        receiver_account="ACC-B",
        amount=100.0,
    )
    tx2 = TransactionEvent(
        transaction_id="TXN-MULTI-2",
        timestamp=datetime(2025, 3, 1, 10, 15, tzinfo=timezone.utc),
        sender_account="ACC-A",
        receiver_account="ACC-B",
        amount=500.0,
    )

    await repo.add_transaction(tx1)
    await repo.add_transaction(tx2)

    s_node = "account:ACC-A"
    r_node = "account:ACC-B"

    # Both edges must coexist
    edges_between = repo.graph.get_edge_data(s_node, r_node)
    assert len(edges_between) == 2
    assert "TXN-MULTI-1" in edges_between
    assert "TXN-MULTI-2" in edges_between
    assert edges_between["TXN-MULTI-1"]["amount"] == 100.0
    assert edges_between["TXN-MULTI-2"]["amount"] == 500.0


# ── 3. Subgraph Extraction ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_subgraph_hop_traversal(repo: NetworkXGraphRepository):
    """Verify neighborhood retrieval at varying hop distances."""
    # Build a 3-hop chain: ACC-1 -> ACC-2 -> ACC-3 -> ACC-4
    for i in range(1, 4):
        await repo.add_transaction(
            TransactionEvent(
                transaction_id=f"TXN-CHAIN-{i}",
                timestamp=datetime(2025, 3, 1, 10 + i, 0, tzinfo=timezone.utc),
                sender_account=f"ACC-{i}",
                receiver_account=f"ACC-{i + 1}",
                amount=1000.0 * i,
            )
        )

    # 1 hop from ACC-1: should see ACC-1, ACC-2
    sub1 = await repo.get_subgraph("ACC-1", hops=1)
    sub1_ids = {n["id"] for n in sub1["nodes"]}
    assert sub1_ids == {"account:ACC-1", "account:ACC-2"}
    assert len(sub1["edges"]) == 1

    # 2 hops from ACC-1: should see ACC-1, ACC-2, ACC-3
    sub2 = await repo.get_subgraph("ACC-1", hops=2)
    sub2_ids = {n["id"] for n in sub2["nodes"]}
    assert sub2_ids == {"account:ACC-1", "account:ACC-2", "account:ACC-3"}
    assert len(sub2["edges"]) == 2

    # 3 hops from ACC-1: should see all 4 accounts
    sub3 = await repo.get_subgraph("ACC-1", hops=3)
    sub3_ids = {n["id"] for n in sub3["nodes"]}
    assert sub3_ids == {
        "account:ACC-1",
        "account:ACC-2",
        "account:ACC-3",
        "account:ACC-4",
    }
    assert len(sub3["edges"]) == 3


# ── 4. Transaction Path Tracing ───────────────────────────────────────


@pytest.mark.asyncio
async def test_trace_transaction_path(repo: NetworkXGraphRepository):
    """Verify multi-hop layering path tracing from transaction ID."""
    # Construct a layering sequence: Victim -> Mule1 -> Mule2 -> Cashout
    await repo.add_transaction(
        TransactionEvent(
            transaction_id="TXN-INCEPTION",
            timestamp=datetime(2025, 3, 1, 10, 0, tzinfo=timezone.utc),
            sender_account="ACC-VICTIM",
            receiver_account="ACC-MULE-1",
            amount=100000.0,
        )
    )
    await repo.add_transaction(
        TransactionEvent(
            transaction_id="TXN-HOP-2",
            timestamp=datetime(2025, 3, 1, 10, 10, tzinfo=timezone.utc),
            sender_account="ACC-MULE-1",
            receiver_account="ACC-MULE-2",
            amount=98000.0,
        )
    )
    await repo.add_transaction(
        TransactionEvent(
            transaction_id="TXN-HOP-3",
            timestamp=datetime(2025, 3, 1, 10, 20, tzinfo=timezone.utc),
            sender_account="ACC-MULE-2",
            receiver_account="ACC-CASHOUT",
            amount=95000.0,
        )
    )

    trace = await repo.trace_transaction_path("TXN-INCEPTION", max_depth=5)
    assert len(trace["edges"]) == 3
    assert "Funds were traced across 3 hops" in trace["path_summary"]
    assert "Layering detected" in trace["path_summary"]

    # Test max_depth constraint
    trace_depth1 = await repo.trace_transaction_path("TXN-INCEPTION", max_depth=1)
    assert len(trace_depth1["edges"]) == 1


# ── 5. Circular Path / Mule Loop Detection ────────────────────────────


@pytest.mark.asyncio
async def test_find_circular_paths_and_no_false_positives(
    repo: NetworkXGraphRepository,
):
    """Verify circular cycle detection detects true cycles and rejects linear paths."""
    # 1. Linear path (A -> B -> C): NOT a cycle
    await repo.add_transaction(
        TransactionEvent(
            transaction_id="TXN-L1",
            timestamp=datetime.now(timezone.utc),
            sender_account="ACC-X",
            receiver_account="ACC-Y",
            amount=100.0,
        )
    )
    await repo.add_transaction(
        TransactionEvent(
            transaction_id="TXN-L2",
            timestamp=datetime.now(timezone.utc),
            sender_account="ACC-Y",
            receiver_account="ACC-Z",
            amount=100.0,
        )
    )
    linear_cycles = await repo.find_circular_paths("ACC-X")
    assert linear_cycles == [], "Linear path must NOT be reported as a cycle"

    # 2. Complete circular loop: C -> A
    await repo.add_transaction(
        TransactionEvent(
            transaction_id="TXN-L3",
            timestamp=datetime.now(timezone.utc),
            sender_account="ACC-Z",
            receiver_account="ACC-X",
            amount=90.0,
        )
    )

    detected = await repo.find_circular_paths("ACC-X", max_depth=5)
    assert len(detected) == 1
    assert detected[0] == ["ACC-X", "ACC-Y", "ACC-Z", "ACC-X"]

    # 3. Verify max_depth constraint on cycle detection
    detected_short = await repo.find_circular_paths("ACC-X", max_depth=2)
    assert detected_short == [], "Cycle of length 3 must not exceed max_depth=2"


# ── 6. Device Linkage ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_link_account_device_idempotency(repo: NetworkXGraphRepository):
    """Verify device-account link creation and idempotency."""
    await repo.link_account_device("ACC-MULE-99", "DEV-IMEI-8888")
    assert "account:ACC-MULE-99" in repo.graph
    assert "device:DEV-IMEI-8888" in repo.graph

    edge = repo.graph.get_edge_data(
        "account:ACC-MULE-99",
        "device:DEV-IMEI-8888",
        key="link:account:ACC-MULE-99->device:DEV-IMEI-8888",
    )
    assert edge["relationship"] == "USED_DEVICE"

    # Duplicate call should not create duplicate edge
    await repo.link_account_device("ACC-MULE-99", "DEV-IMEI-8888")
    edges_between = repo.graph.get_edge_data(
        "account:ACC-MULE-99", "device:DEV-IMEI-8888"
    )
    assert len(edges_between) == 1


# ── 7. Graph Invariant Tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_invariant_1_transaction_ids_unique(repo: NetworkXGraphRepository):
    """INVARIANT 1: Transaction IDs remain unique and distinct."""
    tx1 = TransactionEvent(
        transaction_id="TXN-ID-01",
        timestamp=datetime.now(timezone.utc),
        sender_account="ACC-1",
        receiver_account="ACC-2",
        amount=100.0,
    )
    tx2 = TransactionEvent(
        transaction_id="TXN-ID-02",
        timestamp=datetime.now(timezone.utc),
        sender_account="ACC-1",
        receiver_account="ACC-2",
        amount=200.0,
    )
    await repo.add_transaction(tx1)
    await repo.add_transaction(tx2)

    edge1 = repo.graph.get_edge_data("account:ACC-1", "account:ACC-2", key="TXN-ID-01")
    edge2 = repo.graph.get_edge_data("account:ACC-1", "account:ACC-2", key="TXN-ID-02")
    assert edge1["transaction_id"] != edge2["transaction_id"]


@pytest.mark.asyncio
async def test_invariant_2_entity_type_collision_prevention(
    repo: NetworkXGraphRepository,
):
    """INVARIANT 2: Different entity types with identical raw IDs cannot collide."""
    # Account with ID '123' and Device with ID '123'
    await repo.link_account_device("123", "123")

    acc_node = "account:123"
    dev_node = "device:123"

    assert acc_node != dev_node
    assert repo.graph.nodes[acc_node]["type"] == "account"
    assert repo.graph.nodes[dev_node]["type"] == "device"
    assert repo.graph.number_of_nodes() == 2


@pytest.mark.asyncio
async def test_invariant_3_multiple_transactions_preserve_all_data(
    repo: NetworkXGraphRepository,
):
    """INVARIANT 3: Multiple transactions between same accounts do not overwrite."""
    amounts = [100.0, 200.0, 300.0]
    for idx, amt in enumerate(amounts):
        await repo.add_transaction(
            TransactionEvent(
                transaction_id=f"TXN-AMT-{idx}",
                timestamp=datetime.now(timezone.utc),
                sender_account="ACC-SRC",
                receiver_account="ACC-DST",
                amount=amt,
            )
        )

    edges = repo.graph.get_edge_data("account:ACC-SRC", "account:ACC-DST")
    assert len(edges) == 3
    retrieved_amts = [d["amount"] for d in edges.values()]
    assert sorted(retrieved_amts) == amounts


@pytest.mark.asyncio
async def test_invariant_4_duplicate_insertion_idempotency(
    repo: NetworkXGraphRepository, sample_event: TransactionEvent
):
    """INVARIANT 4: Adding the same transaction twice does not corrupt the graph."""
    await repo.add_transaction(sample_event)
    await repo.add_transaction(sample_event)
    await repo.add_transaction(sample_event)

    assert repo.graph.number_of_nodes() == 4  # 2 accounts + 1 device + 1 IP
    assert repo.graph.number_of_edges() == 3  # 1 transfer + 1 device link + 1 IP link


@pytest.mark.asyncio
async def test_invariant_5_read_operations_do_not_mutate_state(
    repo: NetworkXGraphRepository, sample_event: TransactionEvent
):
    """INVARIANT 5: Read operations (subgraph, trace, cycle) do not mutate graph state."""
    await repo.add_transaction(sample_event)

    nodes_before = list(repo.graph.nodes(data=True))
    edges_before = list(repo.graph.edges(keys=True, data=True))

    # Execute read operations
    sub = await repo.get_subgraph("ACC-101", hops=2)
    trace = await repo.trace_transaction_path("TXN-NX-001")
    cycles = await repo.find_circular_paths("ACC-101")

    # Mutating returned dictionary must not affect internal graph
    sub["nodes"].clear()
    trace["edges"].clear()

    nodes_after = list(repo.graph.nodes(data=True))
    edges_after = list(repo.graph.edges(keys=True, data=True))

    assert nodes_before == nodes_after
    assert edges_before == edges_after


@pytest.mark.asyncio
async def test_invariant_6_cycle_only_returned_when_cycle_exists(
    repo: NetworkXGraphRepository,
):
    """INVARIANT 6: Cycles are strictly returned only when genuine directed loops exist."""
    # Tree structure: Root -> Child1, Root -> Child2
    await repo.add_transaction(
        TransactionEvent(
            transaction_id="TXN-T1",
            timestamp=datetime.now(timezone.utc),
            sender_account="ACC-ROOT",
            receiver_account="ACC-C1",
            amount=50.0,
        )
    )
    await repo.add_transaction(
        TransactionEvent(
            transaction_id="TXN-T2",
            timestamp=datetime.now(timezone.utc),
            sender_account="ACC-ROOT",
            receiver_account="ACC-C2",
            amount=50.0,
        )
    )

    assert await repo.find_circular_paths("ACC-ROOT") == []
    assert await repo.find_circular_paths("ACC-C1") == []


def test_invariant_7_repository_instance_isolation():
    """INVARIANT 7: One repository instance does not leak state into another instance."""
    repo1 = NetworkXGraphRepository()
    repo2 = NetworkXGraphRepository()

    repo1.graph.add_node("account:LEAK-TEST")
    assert "account:LEAK-TEST" in repo1.graph
    assert "account:LEAK-TEST" not in repo2.graph
    assert repo2.graph.number_of_nodes() == 0


# ── 8. Golden Transaction Verification ────────────────────────────────


@pytest.mark.asyncio
async def test_golden_transaction_representation(repo: NetworkXGraphRepository):
    """Verify the canonical golden transaction maps into NetworkXGraphRepository."""
    golden_record = {
        "transaction_id": "TXN-GOLDEN-M3",
        "timestamp": "2025-02-15T08:30:00+00:00",
        "sender_account": "ACC-GOLDEN-SRC",
        "receiver_account": "ACC-GOLDEN-DEST",
        "amount": 99500.0,
        "currency": "INR",
        "channel": "IMPS",
        "sender_bank": "State Bank of India",
        "receiver_bank": "ICICI Bank",
        "device_id": "DEV-GOLDEN-HW-99",
        "ip_address": "10.0.0.1",
        "narration": "Mule chain hop verification",
    }

    event = TransactionMapper.from_dict(golden_record)
    await repo.add_transaction(event)

    # Verify representation
    subgraph = await repo.get_subgraph("ACC-GOLDEN-SRC", hops=1)
    node_ids = {n["id"] for n in subgraph["nodes"]}
    assert "account:ACC-GOLDEN-SRC" in node_ids
    assert "account:ACC-GOLDEN-DEST" in node_ids
    assert "device:DEV-GOLDEN-HW-99" in node_ids

    trace = await repo.trace_transaction_path("TXN-GOLDEN-M3")
    assert len(trace["edges"]) == 1
    assert trace["edges"][0]["amount"] == 99500.0


# ── 9. Import Boundary Verification ───────────────────────────────────


def test_networkx_adapter_import_boundary():
    """Verify NetworkXGraphRepository does NOT import forbidden infrastructure.

    Forbidden: neo4j, sqlalchemy, fastapi, boto3, botocore, torch, dgl, ollama.
    Verifies via AST parsing and isolated module loading (bypassing eager package __init__).
    """
    import ast
    from pathlib import Path

    graph_nx_path = (
        Path(__file__).resolve().parent.parent.parent
        / "app"
        / "repositories"
        / "graph_nx.py"
    )
    assert graph_nx_path.exists()

    # 1. AST-level static inspection of all imports in graph_nx.py
    tree = ast.parse(graph_nx_path.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_names.add(node.module.split(".")[0])

    forbidden = {
        "neo4j",
        "sqlalchemy",
        "fastapi",
        "boto3",
        "botocore",
        "torch",
        "dgl",
        "ollama",
    }
    violated = imported_names.intersection(forbidden)
    assert not violated, f"graph_nx.py directly imports forbidden infrastructure: {violated}"

    # 2. Runtime execution of graph_nx module in clean isolated subprocess
    verification_script = f"""
import sys
import importlib.util
from pathlib import Path

target_file = Path(r'{graph_nx_path}')
spec = importlib.util.spec_from_file_location('graph_nx_isolated', target_file)
module = importlib.util.module_from_spec(spec)
sys.modules['graph_nx_isolated'] = module
spec.loader.exec_module(module)

forbidden = [
    'neo4j',
    'sqlalchemy',
    'fastapi',
    'boto3',
    'botocore',
    'torch',
    'dgl',
    'ollama',
]

imported = [m for m in forbidden if m in sys.modules]
if imported:
    print(f"FORBIDDEN_IMPORTED: {{','.join(imported)}}")
    sys.exit(1)
else:
    print("BOUNDARY_CLEAN")
    sys.exit(0)
"""
    result = subprocess.run(
        [sys.executable, "-c", verification_script],
        capture_output=True,
        text=True,
        cwd="D:\\Team_Cipher_Unit\\backend",
    )
    assert result.returncode == 0, f"Import boundary violated: {result.stdout} {result.stderr}"
    assert "BOUNDARY_CLEAN" in result.stdout

