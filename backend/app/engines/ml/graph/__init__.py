"""
MuleTrace AI — Graph ML & GraphSAGE Module.

Provides inductive graph representation learning, node embeddings,
and graph-based fraud/mule-account classification.

Components:
- graph_schema: Node and edge schemas, deterministic 16-D feature column ordering, GraphDataSnapshot.
- graph_feature_builder: Deterministic extraction from NetworkX graphs and subgraphs into tensors.
- graph_dataset: Chronological graph snapshots and temporal leakage elimination.
- graphsage_model: SAGEConvLayer and GraphSAGEClassifier architectures.
- graph_ml_service: Offline training routines, model weights persistence, and diagnostics.
- graph_ml_adapter: GraphSAGEMulService implementing domain ModelService port contract.
"""

from __future__ import annotations

from app.engines.ml.graph.graph_dataset import (
    ChronologicalGraphSplit,
    GraphMLDatasetBuilder,
    graph_ml_dataset_builder,
)
from app.engines.ml.graph.graph_feature_builder import (
    GraphFeatureBuilder,
    graph_feature_builder,
)
from app.engines.ml.graph.graph_ml_adapter import (
    GraphSAGEMulService,
    graphsage_model_service,
)
from app.engines.ml.graph.graph_ml_service import (
    GraphMLService,
    graph_ml_service,
)
from app.engines.ml.graph.graph_schema import (
    ACCOUNT_NODE_FEATURE_COLUMNS,
    EDGE_TYPE_DEVICE,
    EDGE_TYPE_IP,
    EDGE_TYPE_TRANSFER,
    NODE_FEATURE_DIM,
    NODE_TYPE_ACCOUNT,
    NODE_TYPE_DEVICE,
    NODE_TYPE_IP,
    GraphDataSnapshot,
    NodeEmbedding,
    NodeFeatureVector,
    sanitize_numeric,
)
from app.engines.ml.graph.graphsage_model import (
    GraphSAGEClassifier,
    SAGEConvLayer,
    is_pyg_available,
    is_torch_available,
    set_graph_ml_seed,
)

__all__ = [
    "ACCOUNT_NODE_FEATURE_COLUMNS",
    "ChronologicalGraphSplit",
    "EDGE_TYPE_DEVICE",
    "EDGE_TYPE_IP",
    "EDGE_TYPE_TRANSFER",
    "GraphDataSnapshot",
    "GraphFeatureBuilder",
    "GraphMLDatasetBuilder",
    "GraphMLService",
    "GraphSAGEClassifier",
    "GraphSAGEMulService",
    "NODE_FEATURE_DIM",
    "NODE_TYPE_ACCOUNT",
    "NODE_TYPE_DEVICE",
    "NODE_TYPE_IP",
    "NodeEmbedding",
    "NodeFeatureVector",
    "SAGEConvLayer",
    "graph_feature_builder",
    "graph_ml_dataset_builder",
    "graph_ml_service",
    "graphsage_model_service",
    "is_pyg_available",
    "is_torch_available",
    "sanitize_numeric",
    "set_graph_ml_seed",
]
