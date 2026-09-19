"""
MuleTrace AI — GraphSAGE Neural Architecture Unit Tests.

Validates the native PyTorch GraphSAGE layer (SAGEConvLayer), GraphSAGEClassifier,
embedding extraction, deterministic seed setting, and edge case handling.
"""

from __future__ import annotations

import pytest
import numpy as np

from app.engines.ml.graph.graphsage_model import (
    GraphSAGEClassifier,
    SAGEConvLayer,
    is_torch_available,
    set_seed,
)

if is_torch_available():
    import torch
else:
    torch = None


@pytest.fixture(autouse=True)
def skip_if_no_torch():
    if not is_torch_available():
        pytest.skip("PyTorch is required for GraphSAGE model tests.")


def test_torch_available():
    """Confirms PyTorch runtime is detected."""
    assert is_torch_available() is True


def test_sage_conv_layer_forward():
    """Validates SAGEConvLayer single-hop neighborhood aggregation and projection."""
    set_seed(42)
    in_dim = 16
    out_dim = 32

    conv = SAGEConvLayer(in_features=in_dim, out_features=out_dim, aggr="mean", normalize=True)
    conv.eval()

    # 4 nodes, 3 directed edges: 0->1, 1->2, 2->3 (node 0 has no incoming edges)
    x = torch.randn(4, in_dim)
    edge_index = torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long)

    with torch.no_grad():
        out = conv(x, edge_index)

    assert out.shape == (4, out_dim)
    # Check L2 normalization: each row norm should be ~1.0
    norms = torch.norm(out, p=2, dim=1)
    for n in norms:
        assert torch.isclose(n, torch.tensor(1.0), atol=1e-3)


def test_sage_conv_layer_gcn_aggregation():
    """Validates GCN aggregation option in SAGEConvLayer."""
    conv = SAGEConvLayer(in_features=8, out_features=16, aggr="gcn", normalize=False)
    conv.eval()

    x = torch.randn(3, 8)
    edge_index = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)

    with torch.no_grad():
        out = conv(x, edge_index)

    assert out.shape == (3, 16)


def test_graphsage_classifier_forward_pass():
    """Validates 2-layer GraphSAGE classifier outputs valid probabilities in [0, 1]."""
    set_seed(123)
    num_nodes = 5
    in_dim = 16
    hidden_dim = 32

    model = GraphSAGEClassifier(
        in_features=in_dim,
        hidden_features=hidden_dim,
        num_classes=1,
        dropout=0.0,
    )
    model.eval()

    x = torch.randn(num_nodes, in_dim)
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)

    with torch.no_grad():
        probs = model(x, edge_index)

    assert probs.shape == (num_nodes,)
    probs_np = probs.numpy()
    assert np.all(probs_np >= 0.0)
    assert np.all(probs_np <= 1.0)


def test_graphsage_classifier_get_embeddings():
    """Validates node embedding extraction from penultimate layer."""
    set_seed(123)
    num_nodes = 4
    in_dim = 16
    hidden_dim = 32

    model = GraphSAGEClassifier(
        in_features=in_dim,
        hidden_features=hidden_dim,
        num_classes=1,
    )
    model.eval()

    x = torch.randn(num_nodes, in_dim)
    edge_index = torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long)

    with torch.no_grad():
        emb = model.get_embeddings(x, edge_index)

    assert emb.shape == (num_nodes, hidden_dim)
    assert not torch.isnan(emb).any()


def test_seed_determinism():
    """Ensures identical seeds yield identical initializations and predictions."""
    in_dim = 16
    hidden_dim = 24
    x = torch.randn(4, in_dim)
    edge_index = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)

    set_seed(999)
    m1 = GraphSAGEClassifier(in_dim, hidden_dim, 1)
    m1.eval()
    with torch.no_grad():
        p1 = m1(x, edge_index)

    set_seed(999)
    m2 = GraphSAGEClassifier(in_dim, hidden_dim, 1)
    m2.eval()
    with torch.no_grad():
        p2 = m2(x, edge_index)

    assert torch.allclose(p1, p2, atol=1e-6)


def test_isolated_nodes_and_empty_edges():
    """Ensures model handles disconnected graphs and empty edges without exceptions."""
    model = GraphSAGEClassifier(in_features=16, hidden_features=16, num_classes=1)
    model.eval()

    # Graph with 3 nodes, 0 edges
    x = torch.randn(3, 16)
    edge_index = torch.empty((2, 0), dtype=torch.long)

    with torch.no_grad():
        probs = model(x, edge_index)
        emb = model.get_embeddings(x, edge_index)

    assert probs.shape == (3,)
    assert emb.shape == (3, 16)
    assert not torch.isnan(probs).any()
    assert not torch.isnan(emb).any()
