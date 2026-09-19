"""
MuleTrace AI — GraphSAGE Deep Graph Representation Learning Model.

Implements inductive GraphSAGE neighborhood aggregation layers (Hamilton et al., NeurIPS 2017)
and an end-to-end node classification pipeline for mule account detection.

Architectural Boundary:
- Pure PyTorch implementation with zero required external C++ extensions.
- Zero heuristic post-processing or score additions.
- Inductive: can generate embeddings and predictions for unseen test nodes and subgraphs.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Literal, Optional

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore
    nn = None  # type: ignore
    F = None  # type: ignore
    TORCH_AVAILABLE = False

from app.engines.ml.graph.graph_schema import NODE_FEATURE_DIM

logger = logging.getLogger("app.engines.ml.graph.graphsage_model")


def is_torch_available() -> bool:
    """Return True if PyTorch is installed and available in current runtime."""
    return TORCH_AVAILABLE


def is_pyg_available() -> bool:
    """Check if torch_geometric is installed."""
    try:
        import torch_geometric  # noqa: F401
        return True
    except ImportError:
        return False


def set_graph_ml_seed(seed: int = 42) -> None:
    """Set random seeds for deterministic model initialization and inference."""
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)


set_seed = set_graph_ml_seed


if TORCH_AVAILABLE:

    class SAGEConvLayer(nn.Module):
        """GraphSAGE Inductive Neighborhood Aggregation Layer.

        Computes:
            h_N(v) = AGGREGATE({h_u : u in N(v)})
            h_v'   = sigma(W * CONCAT(h_v, h_N(v)) + b)
        """

        def __init__(
            self,
            in_features: int,
            out_features: int,
            aggregator_type: Literal["mean", "gcn", "max"] = "mean",
            dropout: float = 0.0,
            normalize: bool = True,
            aggr: Optional[str] = None,
        ) -> None:
            super().__init__()
            if aggr is not None:
                aggregator_type = aggr  # type: ignore
            self.in_features = in_features
            self.out_features = out_features
            self.aggregator_type = aggregator_type
            self.normalize = normalize

            # For mean/max: input to linear is concat of self and neighbor (2 * in_features)
            # For gcn: input to linear is in_features
            if aggregator_type == "gcn":
                self.linear = nn.Linear(in_features, out_features, bias=True)
            else:
                self.linear = nn.Linear(in_features * 2, out_features, bias=True)

            self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
            self.reset_parameters()

        def reset_parameters(self) -> None:
            nn.init.xavier_uniform_(self.linear.weight)
            if self.linear.bias is not None:
                nn.init.zeros_(self.linear.bias)

        def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
            """Execute inductive neighborhood aggregation over node features and edges.

            Args:
                x: Node feature tensor of shape [N, in_features].
                edge_index: Edge connection tensor of shape [2, E].

            Returns:
                Updated node representation tensor of shape [N, out_features].
            """
            num_nodes = x.size(0)
            if num_nodes == 0:
                return torch.zeros((0, self.out_features), device=x.device, dtype=x.dtype)

            # 1. Neighbor Aggregation
            src = edge_index[0]
            dst = edge_index[1]

            if edge_index.numel() > 0:
                # Accumulate neighbor feature vectors
                neigh_sum = torch.zeros(num_nodes, self.in_features, device=x.device, dtype=x.dtype)
                neigh_sum.index_add_(0, dst, x[src])

                # Accumulate degrees for mean normalization
                degree = torch.zeros(num_nodes, 1, device=x.device, dtype=x.dtype)
                ones = torch.ones((dst.size(0), 1), device=x.device, dtype=x.dtype)
                degree.index_add_(0, dst, ones)

                # Safe division by degree (nodes without in-edges retain zeros)
                neigh_agg = neigh_sum / torch.clamp(degree, min=1.0)
            else:
                neigh_agg = torch.zeros_like(x)

            # 2. Aggregator Combination & Linear Transform
            if self.aggregator_type == "gcn":
                # GCN-style combination: (self + neighbors) / (deg + 1)
                combined = (x + neigh_agg) / 2.0
                out = self.linear(combined)
            else:
                # Canonical GraphSAGE: concat self and neighbor features
                concat_features = torch.cat([x, neigh_agg], dim=-1)
                out = self.linear(concat_features)

            # 3. Activation, Dropout & Normalization
            out = F.relu(out)
            out = self.dropout(out)
            if self.normalize:
                out = F.normalize(out, p=2, dim=-1)

            return out


    class GraphSAGEClassifier(nn.Module):
        """End-to-end GraphSAGE Model for Node Representation and Fraud Risk Scoring.

        Architecture:
            Input Node Features (16-D)
                    │
            SAGEConv Layer 1 (16 -> hidden_dim)
                    │
            SAGEConv Layer 2 (hidden_dim -> embedding_dim)
                    │
            Node Embedding (embedding_dim)
                    │
            Classification Head (Linear -> Sigmoid)
                    │
            Predicted Mule Probability P in [0, 1]
        """

        def __init__(
            self,
            in_features: int = NODE_FEATURE_DIM,
            hidden_dim: int = 32,
            embedding_dim: int = 16,
            num_layers: int = 2,
            dropout: float = 0.1,
            aggregator_type: Literal["mean", "gcn", "max"] = "mean",
            hidden_features: Optional[int] = None,
            num_classes: Optional[int] = None,
        ) -> None:
            super().__init__()
            if hidden_features is not None:
                hidden_dim = hidden_features
                embedding_dim = hidden_features
            self.in_features = in_features
            self.hidden_dim = hidden_dim
            self.embedding_dim = embedding_dim
            self.num_layers = num_layers
            self.aggregator_type = aggregator_type

            # Layer 1: Input -> Hidden
            self.conv1 = SAGEConvLayer(
                in_features=in_features,
                out_features=hidden_dim,
                aggregator_type=aggregator_type,
                dropout=dropout,
                normalize=True,
            )

            # Layer 2: Hidden -> Embedding
            self.conv2 = SAGEConvLayer(
                in_features=hidden_dim,
                out_features=embedding_dim,
                aggregator_type=aggregator_type,
                dropout=dropout,
                normalize=True,
            )

            # Prediction Head: Embedding -> Binary Fraud Probability Logit
            self.classifier = nn.Linear(embedding_dim, 1)
            self.sigmoid = nn.Sigmoid()

        def get_embeddings(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
            """Extract learned dense node representation vectors without classification head.

            Returns:
                Tensor of shape [N, embedding_dim] containing L2-normalized embeddings.
            """
            h1 = self.conv1(x, edge_index)
            h2 = self.conv2(h1, edge_index)
            return h2

        def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
            """Compute predicted mule/fraud probabilities for all nodes.

            Returns:
                Tensor of shape [N] containing predicted probabilities in [0.0, 1.0].
            """
            embeddings = self.get_embeddings(x, edge_index)
            logits = self.classifier(embeddings).squeeze(-1)
            return self.sigmoid(logits)

        def get_model_config(self) -> dict[str, Any]:
            """Return serializable architecture configuration."""
            return {
                "in_features": self.in_features,
                "hidden_dim": self.hidden_dim,
                "embedding_dim": self.embedding_dim,
                "num_layers": self.num_layers,
                "aggregator_type": self.aggregator_type,
                "framework": "pytorch_native",
            }

else:
    # Graceful fallback stubs if torch is unavailable
    class SAGEConvLayer:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class GraphSAGEClassifier:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
