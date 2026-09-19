"""
MuleTrace AI — Graph Intelligence Fixture Tests (Fixtures A through T).

Validates all 20 canonical graph topology fixtures required by Milestone 7:
- Fixture A: Empty graph
- Fixture B: Single account (isolated node)
- Fixture C: Simple transfer (A -> B)
- Fixture D: Multiple outbound (A -> B, A -> C, A -> D)
- Fixture E: Multiple inbound (B -> A, C -> A, D -> A)
- Fixture F: Fan-in aggregation (hub)
- Fixture G: Fan-out dispersion (distributor)
- Fixture H: Two-node cycle (A -> B -> A)
- Fixture I: Three-node cycle (A -> B -> C -> A)
- Fixture J: Longer cycle (A -> B -> C -> D -> A)
- Fixture K: Shared device (A -> devX, B -> devX)
- Fixture L: Shared IP (A -> ipY, B -> ipY)
- Fixture M: Multiple transactions between same accounts (Multi-edge)
- Fixture N: Disconnected components
- Fixture O: Hop depth differences (0, 1, 2)
- Fixture P: Unsorted transaction input
- Fixture Q: Duplicate transaction IDs
- Fixture R: Missing optional device/IP data
- Fixture S: Mixed node types (Account, Device, IP)
- Fixture T: Large-but-reasonable graph (50 accounts)
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from app.domain.models import TransactionEvent
from app.engines.graph.intelligence import GraphIntelligenceEngine
from app.repositories.graph_nx import NetworkXGraphRepository


def _make_tx(
    tx_id: str,
    sender: str,
    receiver: str,
    amount: float = 1000.0,
    timestamp: datetime | None = None,
    channel: str = "UPI",
    device_id: str | None = None,
    ip_address: str | None = None,
) -> TransactionEvent:
    """Helper to create a canonical TransactionEvent."""
    return TransactionEvent(
        transaction_id=tx_id,
        timestamp=timestamp or datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc),
        amount=amount,
        sender_account=sender,
        receiver_account=receiver,
        channel=channel,
        device_id=device_id,
        ip_address=ip_address,
    )


# -----------------------------------------------------------------------------
# FIXTURE A — EMPTY GRAPH
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_a_empty_graph():
    """Empty graph query must return valid zero-initialized GraphFeatures without crashing."""
    repo = NetworkXGraphRepository()
    engine = GraphIntelligenceEngine(repository=repo)
    features = await engine.extract_features("ACC-EMPTY")

    assert features.account_id == "ACC-EMPTY"
    assert features.in_degree == 0
    assert features.out_degree == 0
    assert features.total_degree == 0
    assert features.unique_inbound_counterparties == 0
    assert features.unique_outbound_counterparties == 0
    assert features.inbound_volume_total == 0.0
    assert features.outbound_volume_total == 0.0
    assert features.has_cycle is False
    assert features.cycle_count == 0
    assert features.shared_device_count == 0
    assert features.shared_ip_count == 0
    assert features.subgraph_node_count == 0
    assert features.subgraph_edge_count == 0


# -----------------------------------------------------------------------------
# FIXTURE B — SINGLE ACCOUNT
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_b_single_account():
    """An isolated account node in the graph must return 0 degrees and 0 neighbors."""
    repo = NetworkXGraphRepository()
    # Explicitly add isolated node
    repo.graph.add_node("account:ACC-ISO", type="account", account_number="ACC-ISO")
    engine = GraphIntelligenceEngine(repository=repo)

    features = await engine.extract_features("ACC-ISO")
    assert features.account_id == "ACC-ISO"
    assert features.in_degree == 0
    assert features.out_degree == 0
    assert features.total_degree == 0
    assert features.neighboring_accounts_count == 0
    assert features.reachable_node_count == 0
    assert features.subgraph_node_count == 1
    assert features.subgraph_edge_count == 0


# -----------------------------------------------------------------------------
# FIXTURE C — SIMPLE TRANSFER (A -> B)
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_c_simple_transfer():
    """Directionality test: A -> B must show out_degree=1 for A and in_degree=1 for B."""
    repo = NetworkXGraphRepository()
    tx = _make_tx("TX-001", "ACC-A", "ACC-B", amount=5000.0)
    await repo.add_transaction(tx)
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A")
    assert f_a.out_degree == 1
    assert f_a.in_degree == 0
    assert f_a.unique_outbound_counterparties == 1
    assert f_a.unique_inbound_counterparties == 0
    assert f_a.outbound_volume_total == 5000.0
    assert f_a.inbound_volume_total == 0.0
    assert f_a.downstream_accounts == ["ACC-B"]
    assert f_a.upstream_accounts == []

    f_b = await engine.extract_features("ACC-B")
    assert f_b.in_degree == 1
    assert f_b.out_degree == 0
    assert f_b.unique_inbound_counterparties == 1
    assert f_b.unique_outbound_counterparties == 0
    assert f_b.inbound_volume_total == 5000.0
    assert f_b.outbound_volume_total == 0.0
    assert f_b.downstream_accounts == []
    assert f_b.upstream_accounts == ["ACC-A"]


# -----------------------------------------------------------------------------
# FIXTURE D — MULTIPLE OUTBOUND
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_d_multiple_outbound():
    """A -> B, A -> C, A -> D must reflect out_degree=3 and unique_outbound=3 for A."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_make_tx("TX-D1", "ACC-A", "ACC-B", amount=1000.0))
    await repo.add_transaction(_make_tx("TX-D2", "ACC-A", "ACC-C", amount=2000.0))
    await repo.add_transaction(_make_tx("TX-D3", "ACC-A", "ACC-D", amount=3000.0))
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A")
    assert f_a.out_degree == 3
    assert f_a.in_degree == 0
    assert f_a.unique_outbound_counterparties == 3
    assert f_a.outbound_volume_total == 6000.0
    assert sorted(f_a.downstream_accounts) == ["ACC-B", "ACC-C", "ACC-D"]


# -----------------------------------------------------------------------------
# FIXTURE E — MULTIPLE INBOUND
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_e_multiple_inbound():
    """B -> A, C -> A, D -> A must reflect in_degree=3 and unique_inbound=3 for A."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_make_tx("TX-E1", "ACC-B", "ACC-A", amount=1000.0))
    await repo.add_transaction(_make_tx("TX-E2", "ACC-C", "ACC-A", amount=2000.0))
    await repo.add_transaction(_make_tx("TX-E3", "ACC-D", "ACC-A", amount=3000.0))
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A")
    assert f_a.in_degree == 3
    assert f_a.out_degree == 0
    assert f_a.unique_inbound_counterparties == 3
    assert f_a.inbound_volume_total == 6000.0
    assert sorted(f_a.upstream_accounts) == ["ACC-B", "ACC-C", "ACC-D"]


# -----------------------------------------------------------------------------
# FIXTURE F — FAN-IN AGGREGATION
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_f_fan_in():
    """Multiple unique senders aggregating funds into a single account triggers HIGH_FAN_IN signal."""
    repo = NetworkXGraphRepository()
    for i in range(1, 6):
        await repo.add_transaction(
            _make_tx(f"TX-F{i}", f"ACC-SENDER-{i}", "ACC-COLLECTOR", amount=10000.0)
        )
    engine = GraphIntelligenceEngine(repository=repo)

    f = await engine.extract_features("ACC-COLLECTOR")
    assert f.unique_senders_count == 5
    assert f.inbound_tx_count == 5
    assert f.fan_in_ratio == 1.0
    assert f.inbound_volume_total == 50000.0
    assert any("HIGH_FAN_IN" in sig for sig in f.evidence_signals)


# -----------------------------------------------------------------------------
# FIXTURE G — FAN-OUT DISPERSION
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_g_fan_out():
    """Single distributor dispersing funds to many receivers triggers HIGH_FAN_OUT signal."""
    repo = NetworkXGraphRepository()
    for i in range(1, 6):
        await repo.add_transaction(
            _make_tx(f"TX-G{i}", "ACC-DISTRIBUTOR", f"ACC-RECEIVER-{i}", amount=5000.0)
        )
    engine = GraphIntelligenceEngine(repository=repo)

    f = await engine.extract_features("ACC-DISTRIBUTOR")
    assert f.unique_receivers_count == 5
    assert f.outbound_tx_count == 5
    assert f.fan_out_ratio == 1.0
    assert f.outbound_volume_total == 25000.0
    assert any("HIGH_FAN_OUT" in sig for sig in f.evidence_signals)


# -----------------------------------------------------------------------------
# FIXTURE H — TWO-NODE CYCLE (A -> B -> A)
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_h_two_node_cycle():
    """Circular ping-pong transfer A -> B -> A is detected as a cycle of length 2."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_make_tx("TX-H1", "ACC-A", "ACC-B", amount=5000.0))
    await repo.add_transaction(_make_tx("TX-H2", "ACC-B", "ACC-A", amount=4800.0))
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A")
    assert f_a.has_cycle is True
    assert f_a.cycle_count == 1
    assert 2 in f_a.cycle_lengths
    assert sorted(f_a.contributing_cycle_nodes) == ["ACC-A", "ACC-B"]
    assert any("CYCLE_DETECTED" in s for s in f_a.evidence_signals)


# -----------------------------------------------------------------------------
# FIXTURE I — THREE-NODE CYCLE (A -> B -> C -> A)
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_i_three_node_cycle():
    """Circular layering loop A -> B -> C -> A is detected as a cycle of length 3."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_make_tx("TX-I1", "ACC-A", "ACC-B", amount=10000.0))
    await repo.add_transaction(_make_tx("TX-I2", "ACC-B", "ACC-C", amount=9500.0))
    await repo.add_transaction(_make_tx("TX-I3", "ACC-C", "ACC-A", amount=9000.0))
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A")
    assert f_a.has_cycle is True
    assert f_a.cycle_count == 1
    assert 3 in f_a.cycle_lengths
    assert sorted(f_a.contributing_cycle_nodes) == ["ACC-A", "ACC-B", "ACC-C"]


# -----------------------------------------------------------------------------
# FIXTURE J — LONGER CYCLE (A -> B -> C -> D -> A)
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_j_longer_cycle():
    """4-node circular routing loop A -> B -> C -> D -> A is detected."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_make_tx("TX-J1", "ACC-A", "ACC-B", amount=10000.0))
    await repo.add_transaction(_make_tx("TX-J2", "ACC-B", "ACC-C", amount=9000.0))
    await repo.add_transaction(_make_tx("TX-J3", "ACC-C", "ACC-D", amount=8000.0))
    await repo.add_transaction(_make_tx("TX-J4", "ACC-D", "ACC-A", amount=7000.0))
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A", max_depth=5)
    assert f_a.has_cycle is True
    assert 4 in f_a.cycle_lengths
    assert sorted(f_a.contributing_cycle_nodes) == ["ACC-A", "ACC-B", "ACC-C", "ACC-D"]


# -----------------------------------------------------------------------------
# FIXTURE K — SHARED DEVICE
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_k_shared_device():
    """Multiple accounts operating from the same hardware device are flagged."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(
        _make_tx("TX-K1", "ACC-A", "ACC-MERCHANT", device_id="DEV-SHARED-1")
    )
    await repo.add_transaction(
        _make_tx("TX-K2", "ACC-B", "ACC-MERCHANT", device_id="DEV-SHARED-1")
    )
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A", hops=2)
    assert f_a.shared_device_count == 1
    assert f_a.accounts_per_shared_device.get("DEV-SHARED-1") == 2
    assert "DEV-SHARED-1" in f_a.associated_devices
    assert any("SHARED_DEVICE" in s for s in f_a.evidence_signals)


# -----------------------------------------------------------------------------
# FIXTURE L — SHARED IP
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_l_shared_ip():
    """Multiple accounts originating transactions from the same IP are flagged."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(
        _make_tx("TX-L1", "ACC-A", "ACC-MERCHANT", ip_address="192.168.1.100")
    )
    await repo.add_transaction(
        _make_tx("TX-L2", "ACC-B", "ACC-MERCHANT", ip_address="192.168.1.100")
    )
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A", hops=2)
    assert f_a.shared_ip_count == 1
    assert f_a.accounts_per_shared_ip.get("192.168.1.100") == 2
    assert "192.168.1.100" in f_a.associated_ips
    assert any("SHARED_IP" in s for s in f_a.evidence_signals)


# -----------------------------------------------------------------------------
# FIXTURE M — MULTIPLE TRANSACTIONS BETWEEN SAME ACCOUNTS (MULTI-EDGE)
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_m_multi_edge_preservation():
    """Three transactions between A and B must give out_degree=3, but unique_outbound=1."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_make_tx("TX-M1", "ACC-A", "ACC-B", amount=100.0))
    await repo.add_transaction(_make_tx("TX-M2", "ACC-A", "ACC-B", amount=200.0))
    await repo.add_transaction(_make_tx("TX-M3", "ACC-A", "ACC-B", amount=300.0))
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A")
    assert f_a.out_degree == 3
    assert f_a.outbound_tx_count == 3
    assert f_a.unique_outbound_counterparties == 1
    assert f_a.unique_receivers_count == 1
    assert f_a.outbound_volume_total == 600.0
    assert f_a.contributing_transaction_ids == ["TX-M1", "TX-M2", "TX-M3"]


# -----------------------------------------------------------------------------
# FIXTURE N — DISCONNECTED COMPONENTS
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_n_disconnected_components():
    """Transactions in an unrelated component must not bleed into focal account subgraph."""
    repo = NetworkXGraphRepository()
    # Component 1
    await repo.add_transaction(_make_tx("TX-N1", "ACC-A", "ACC-B", amount=1000.0))
    # Component 2
    await repo.add_transaction(_make_tx("TX-N2", "ACC-X", "ACC-Y", amount=9999.0))
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A", hops=2)
    assert f_a.neighboring_accounts_count == 1
    assert f_a.downstream_accounts == ["ACC-B"]
    assert "account:ACC-X" not in f_a.contributing_node_ids
    assert "account:ACC-Y" not in f_a.contributing_node_ids
    assert "TX-N2" not in f_a.contributing_transaction_ids


# -----------------------------------------------------------------------------
# FIXTURE O — HOP DEPTH DIFFERENCES
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_o_hop_depth_differences():
    """Chain A -> B -> C -> D: hop 0 sees only A, hop 1 sees B, hop 2 sees B and C."""
    repo = NetworkXGraphRepository()
    await repo.add_transaction(_make_tx("TX-O1", "ACC-A", "ACC-B"))
    await repo.add_transaction(_make_tx("TX-O2", "ACC-B", "ACC-C"))
    await repo.add_transaction(_make_tx("TX-O3", "ACC-C", "ACC-D"))
    engine = GraphIntelligenceEngine(repository=repo)

    f_h0 = await engine.extract_features("ACC-A", hops=0)
    assert f_h0.neighboring_accounts_count == 0

    f_h1 = await engine.extract_features("ACC-A", hops=1)
    assert f_h1.neighboring_accounts_count == 1

    f_h2 = await engine.extract_features("ACC-A", hops=2)
    assert f_h2.neighboring_accounts_count == 2
    assert "ACC-B" in f_h2.downstream_accounts
    assert "ACC-C" in f_h2.downstream_accounts


# -----------------------------------------------------------------------------
# FIXTURE P — UNSORTED TRANSACTION INPUT
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_p_unsorted_transaction_input():
    """Ingesting transactions out of order yields identical final graph intelligence features."""
    repo1 = NetworkXGraphRepository()
    repo2 = NetworkXGraphRepository()

    tx1 = _make_tx("TX-P1", "ACC-A", "ACC-B", amount=100.0)
    tx2 = _make_tx("TX-P2", "ACC-B", "ACC-C", amount=200.0)
    tx3 = _make_tx("TX-P3", "ACC-C", "ACC-A", amount=300.0)

    # Ingestion Order 1
    await repo1.add_transaction(tx1)
    await repo1.add_transaction(tx2)
    await repo1.add_transaction(tx3)

    # Ingestion Order 2
    await repo2.add_transaction(tx3)
    await repo2.add_transaction(tx1)
    await repo2.add_transaction(tx2)

    eng1 = GraphIntelligenceEngine(repository=repo1)
    eng2 = GraphIntelligenceEngine(repository=repo2)

    f1 = await eng1.extract_features("ACC-A")
    f2 = await eng2.extract_features("ACC-A")

    assert f1.total_degree == f2.total_degree
    assert f1.has_cycle == f2.has_cycle
    assert f1.cycle_count == f2.cycle_count
    assert f1.contributing_transaction_ids == f2.contributing_transaction_ids


# -----------------------------------------------------------------------------
# FIXTURE Q — DUPLICATE TRANSACTION IDS
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_q_duplicate_transaction_ids():
    """Duplicate transaction ID ingestion is idempotent and does not corrupt degree counts."""
    repo = NetworkXGraphRepository()
    tx = _make_tx("TX-DUP-1", "ACC-A", "ACC-B", amount=5000.0)
    await repo.add_transaction(tx)
    await repo.add_transaction(tx)  # Idempotent re-add
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A")
    assert f_a.out_degree == 1
    assert f_a.outbound_volume_total == 5000.0
    assert f_a.contributing_transaction_ids == ["TX-DUP-1"]


# -----------------------------------------------------------------------------
# FIXTURE R — MISSING OPTIONAL DEVICE / IP DATA
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_r_missing_optional_data():
    """Transactions without device_id or ip_address execute cleanly with zero device/ip counts."""
    repo = NetworkXGraphRepository()
    tx = _make_tx("TX-R1", "ACC-A", "ACC-B", amount=2500.0, device_id=None, ip_address=None)
    await repo.add_transaction(tx)
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A")
    assert f_a.neighboring_devices_count == 0
    assert f_a.neighboring_ips_count == 0
    assert f_a.shared_device_count == 0
    assert f_a.shared_ip_count == 0
    assert f_a.associated_devices == []
    assert f_a.associated_ips == []


# -----------------------------------------------------------------------------
# FIXTURE S — MIXED NODE TYPES
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_s_mixed_node_types():
    """Graph with accounts, devices, and IPs partitions node types cleanly."""
    repo = NetworkXGraphRepository()
    tx = _make_tx(
        "TX-S1",
        "ACC-A",
        "ACC-B",
        amount=1000.0,
        device_id="DEV-MIXED-1",
        ip_address="10.0.0.1",
    )
    await repo.add_transaction(tx)
    engine = GraphIntelligenceEngine(repository=repo)

    f_a = await engine.extract_features("ACC-A", hops=2)
    assert f_a.unique_node_count_by_type.get("account") == 2
    assert f_a.unique_node_count_by_type.get("device") == 1
    assert f_a.unique_node_count_by_type.get("ip") == 1
    assert f_a.neighboring_devices_count == 1
    assert f_a.neighboring_ips_count == 1


# -----------------------------------------------------------------------------
# FIXTURE T — LARGE-BUT-REASONABLE GRAPH
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_fixture_t_large_graph():
    """Topology with 50 accounts completes deterministically without timeout or performance degradation."""
    repo = NetworkXGraphRepository()
    # 50 accounts transferring sequentially: ACC-0 -> ACC-1 -> ACC-2 ...
    for i in range(49):
        await repo.add_transaction(
            _make_tx(f"TX-T{i}", f"ACC-{i}", f"ACC-{i+1}", amount=float((i + 1) * 100))
        )
    engine = GraphIntelligenceEngine(repository=repo)

    # ACC-0 at hop 2 can see ACC-1 and ACC-2
    f0 = await engine.extract_features("ACC-0", hops=2, max_depth=10)
    assert f0.out_degree == 1
    assert f0.neighboring_accounts_count == 2
    assert f0.reachable_node_count == 2
    assert f0.downstream_accounts == ["ACC-1", "ACC-2"]
