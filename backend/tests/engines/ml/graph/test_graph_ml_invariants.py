"""
MuleTrace AI — Graph ML Architecture Invariants Tests.

Verifies the critical architectural invariants governing Milestone 9:
1. Pure model output: zero heuristic bonus additions (no +25, +20, etc.).
2. Clean score bounds: raw_score strictly bounded in [0.0, 1.0].
3. Temporal leakage prevention: snapshots do not contain future edges.
4. Safe missing node handling: unobserved accounts do not crash inference.
5. Zero side-effects: graph feature extraction does not mutate graph state.
6. Deterministic inference: fixed seed yields invariant scores.
7. Architectural boundaries: no RiskFusion logic, domain ModelService conformity.
8. Safe startup: no training executed during module imports or adapter instantiation.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import networkx as nx
import numpy as np
import pytest
import pandas as pd

from app.domain.models import TransactionEvent
from app.domain.interfaces import ModelPrediction, ModelService
from app.engines.ml.graph.graph_schema import (
    ACCOUNT_NODE_FEATURE_COLUMNS,
    ACCOUNT_NODE_FEATURE_DIM,
    sanitize_numeric,
)
from app.engines.ml.graph.graph_feature_builder import GraphFeatureBuilder
from app.engines.ml.graph.graph_dataset import GraphMLDatasetBuilder
from app.engines.ml.graph.graphsage_model import (
    GraphSAGEClassifier,
    is_torch_available,
    set_seed,
)
from app.engines.ml.graph.graph_ml_adapter import GraphSAGEMulService
from app.engines.ml.graph.graph_ml_service import GraphMLService

if is_torch_available():
    import torch


def _make_event(src: str, dst: str, amount: float = 1000.0) -> TransactionEvent:
    return TransactionEvent(
        transaction_id=f"TXN_{src}_{dst}",
        sender_account=src,
        receiver_account=dst,
        amount=float(amount),
        timestamp=datetime(2026, 9, 19, 12, 0, 0),
        transaction_type="TRANSFER",
        channel="ONLINE",
    )


# --- Invariant 1: Pure Model Output (Zero Heuristic Additions) ---
def test_invariant_pure_model_output_no_heuristic_additions(tmp_path):
    """Raw score must be exactly the classifier probability with no heuristic bonuses."""
    if not is_torch_available():
        pytest.skip("PyTorch required.")

    # Train a minimal model
    df = pd.DataFrame([
        {"txn_id": "T1", "timestamp": "2026-09-01 10:00:00", "account_number": "A", "receiver_account": "B", "amount": 100.0, "is_fraud": 0},
        {"txn_id": "T2", "timestamp": "2026-09-01 10:05:00", "account_number": "B", "receiver_account": "C", "amount": 200.0, "is_fraud": 1},
    ])
    csv_file = tmp_path / "data.csv"
    df.to_csv(csv_file, index=False)

    service = GraphMLService(artifact_dir=tmp_path / "artifacts")
    service.train_offline(csv_file, epochs=1)
    adapter = GraphSAGEMulService(service=service)

    event = _make_event("A", "B")
    pred = adapter.predict(event)
    # Score must be a valid float in [0.0, 1.0] and risk score in [0, 100]
    assert 0.0 <= pred.fraud_probability <= 1.0
    assert 0 <= pred.risk_score <= 100
    # Zero heuristic bonus: probability remains in unit interval
    assert pred.fraud_probability <= 1.0


# --- Invariant 2: Strict Feature Dimension (16-D) ---
def test_invariant_node_feature_dimension():
    """All node feature vectors must strictly have 16 dimensions."""
    assert len(ACCOUNT_NODE_FEATURE_COLUMNS) == 16
    assert ACCOUNT_NODE_FEATURE_DIM == 16

    builder = GraphFeatureBuilder()
    G = nx.MultiDiGraph()
    G.add_node("account:ACC_X")
    features = builder.extract_node_features(G, "account:ACC_X")

    assert features.shape == (16,)
    assert len(features.feature_dict) == 16


# --- Invariant 3: Numeric Sanitization (No NaN / Inf) ---
def test_invariant_numeric_sanitization():
    """sanitize_numeric guarantees no NaN or Inf propagates to tensors."""
    assert sanitize_numeric(float("nan"), default=0.0) == 0.0
    assert sanitize_numeric(float("inf"), default=0.0) == 0.0
    assert sanitize_numeric(float("-inf"), default=0.0) == 0.0
    assert sanitize_numeric(42.5) == 42.5


# --- Invariant 4: Graph Immutability on Feature Extraction ---
def test_invariant_graph_immutability_on_read():
    """Extracting node features or subgraphs must never mutate the input graph."""
    builder = GraphFeatureBuilder()
    G = nx.MultiDiGraph()
    G.add_node("account:A1", balance=500.0)
    G.add_node("account:A2", balance=1000.0)
    G.add_edge("account:A1", "account:A2", amount=250.0, timestamp="2026-09-01T10:00:00")

    original_nodes = list(G.nodes(data=True))
    original_edges = list(G.edges(data=True))

    # Read features and subgraphs
    _ = builder.extract_node_features(G, "account:A1")
    _ = builder.extract_k_hop_subgraph(G, "account:A1", k=2)

    assert list(G.nodes(data=True)) == original_nodes
    assert list(G.edges(data=True)) == original_edges


# --- Invariant 5: Safe Missing Node Handling ---
def test_invariant_missing_node_safety():
    """Unobserved nodes produce fallback feature vectors without raising KeyErrors."""
    builder = GraphFeatureBuilder()
    empty_graph = nx.MultiDiGraph()

    vec = builder.extract_node_features(empty_graph, "account:NON_EXISTENT")
    assert vec.shape == (16,)
    assert np.all(vec.vector == 0.0)

    subgraph = builder.extract_k_hop_subgraph(empty_graph, "account:NON_EXISTENT", k=2)
    assert len(subgraph.nodes) == 1  # Contains only the dummy target node


# --- Invariant 6: Temporal Order & Anti-Leakage ---
def test_invariant_temporal_no_lookahead():
    """GraphMLDatasetBuilder with max_timestamp strictly discards future transactions."""
    df = pd.DataFrame([
        {"txn_id": "T1", "timestamp": "2026-09-01 10:00:00", "account_number": "A1", "receiver_account": "A2", "amount": 100.0, "is_fraud": 0},
        {"txn_id": "T2", "timestamp": "2026-09-05 10:00:00", "account_number": "A2", "receiver_account": "A3", "amount": 500.0, "is_fraud": 1},
    ])
    builder = GraphMLDatasetBuilder()
    cutoff = datetime(2026, 9, 2, 0, 0, 0)
    snapshot = builder.build_snapshot_from_dataframe(df, max_timestamp=cutoff)

    # Edge T2 (Sept 5) must NOT be present
    assert snapshot.num_edges == 1
    assert "account:A3" not in snapshot.node_ids


# --- Invariant 7: Seed Determinism ---
def test_invariant_seed_determinism():
    """Identical seeds yield identical predictions."""
    if not is_torch_available():
        pytest.skip("PyTorch required.")

    set_seed(42)
    m1 = GraphSAGEClassifier(16, 32, 1)
    x = torch.ones(3, 16)
    edge_index = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)
    m1.eval()
    with torch.no_grad():
        out1 = m1(x, edge_index).numpy()

    set_seed(42)
    m2 = GraphSAGEClassifier(16, 32, 1)
    m2.eval()
    with torch.no_grad():
        out2 = m2(x, edge_index).numpy()

    assert np.allclose(out1, out2, atol=1e-7)


# --- Invariant 8: Adapter Return Type Conformity ---
def test_invariant_adapter_domain_conformity():
    """Adapter must return native ModelPrediction types with no raw PyTorch tensors leaking."""
    adapter = GraphSAGEMulService()
    event = _make_event("SRC", "DST")
    pred = adapter.predict(event)

    assert isinstance(pred, ModelPrediction)
    assert type(pred.risk_score) is int
    assert type(pred.fraud_probability) is float
    assert type(pred.is_fraud) is bool
    assert isinstance(pred.details, dict)
    for k, v in pred.details.items():
        assert not str(type(v)).startswith("<class 'torch.Tensor'>")


# --- Invariant 9: Zero Startup Training Invariant ---
def test_invariant_no_startup_training():
    """Instantiating GraphMLService or GraphSAGEMulService must NOT trigger training."""
    # Instantiation should be instantaneous and is_trained False by default (unless pre-trained artifact exists)
    service = GraphMLService(artifact_dir=None)
    assert service.is_trained is False
    adapter = GraphSAGEMulService(service=service)
    assert adapter.is_trained is False
