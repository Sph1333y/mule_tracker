"""
MuleTrace AI — Graph ML & GraphSAGE Schema Contracts.

Defines canonical node types, edge types, node feature dimensions,
and graph data structures for GraphSAGE representation learning.

Architectural Boundary:
- Cloud-agnostic and framework-safe.
- Pure graph ML data contracts with zero dependency on FastAPI, SQLAlchemy, or AWS.
- NaN / Inf immune: all numeric features guaranteed finite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Optional
import numpy as np
import pandas as pd

# Safe PyTorch import
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore
    TORCH_AVAILABLE = False


# ── Entity & Relation Constants ──────────────────────────────────────────────
NODE_TYPE_ACCOUNT = "account"
NODE_TYPE_DEVICE = "device"
NODE_TYPE_IP = "ip"

EDGE_TYPE_TRANSFER = "TRANSFERRED_FUNDS"
EDGE_TYPE_DEVICE = "USES_DEVICE"
EDGE_TYPE_IP = "USES_IP"


# ── Canonical Node Feature Column Ordering ───────────────────────────────────
# Fixed 16-dimensional node feature representation for GraphSAGE input.
ACCOUNT_NODE_FEATURE_COLUMNS: tuple[str, ...] = (
    "in_degree",
    "out_degree",
    "total_degree",
    "unique_inbound_counterparties",
    "unique_outbound_counterparties",
    "inbound_volume",
    "outbound_volume",
    "fan_in_ratio",
    "fan_out_ratio",
    "account_age_days",
    "velocity_l6h",
    "temporal_burst_detected",
    "temporal_tx_count_1h",
    "shared_device_count",
    "shared_ip_count",
    "neighborhood_density",
)

NODE_FEATURE_DIM: int = len(ACCOUNT_NODE_FEATURE_COLUMNS)  # 16
ACCOUNT_NODE_FEATURE_DIM: int = NODE_FEATURE_DIM


def sanitize_numeric(val: Any, default: float = 0.0) -> float:
    """Sanitize any numeric value, guaranteeing a finite real float."""
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default


@dataclass
class NodeFeatureVector:
    """Strongly typed feature representation for a single graph node."""

    node_id: str
    node_type: str = NODE_TYPE_ACCOUNT
    features: list[float] = field(default_factory=list)
    dim: int = NODE_FEATURE_DIM

    @property
    def vector(self) -> np.ndarray:
        return np.array(self.features, dtype=np.float32)

    @property
    def shape(self) -> tuple[int, ...]:
        return (len(self.features),)

    @property
    def feature_dict(self) -> dict[str, float]:
        return {
            col: (self.features[i] if i < len(self.features) else 0.0)
            for i, col in enumerate(ACCOUNT_NODE_FEATURE_COLUMNS)
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "features": self.features,
            "dim": self.dim,
        }


@dataclass
class NodeEmbedding:
    """Learned dense representation vector produced by GraphSAGE."""

    node_id: str
    vector: list[float]
    dim: int = 16
    model_version: str = "graphsage_v1.0"
    node_type: str = NODE_TYPE_ACCOUNT

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "dim": self.dim,
            "model_version": self.model_version,
            "node_type": self.node_type,
            "vector": [round(float(v), 6) for v in self.vector],
        }


@dataclass
class GraphDataSnapshot:
    """Tensor-backed or array-backed graph container for GraphSAGE operations.

    Maintains bidirectional node-to-index mappings, feature matrices,
    and directed edge connection indices.
    """

    node_ids: list[str]
    node_to_idx: dict[str, int]
    node_type_map: dict[str, str]
    # Tensor of shape [N, NODE_FEATURE_DIM]
    x: Any
    # Tensor of shape [2, E]
    edge_index: Any
    # Optional target labels [N]
    y: Optional[Any] = None
    # Optional edge attributes [E, D_edge]
    edge_attr: Optional[Any] = None
    # Train / Val / Test boolean masks
    train_mask: Optional[Any] = None
    val_mask: Optional[Any] = None
    test_mask: Optional[Any] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def num_nodes(self) -> int:
        return len(self.node_ids)

    @property
    def num_edges(self) -> int:
        if self.edge_index is None:
            return 0
        if hasattr(self.edge_index, "shape"):
            return int(self.edge_index.shape[1]) if len(self.edge_index.shape) > 1 else 0
        if isinstance(self.edge_index, list):
            return len(self.edge_index[0]) if len(self.edge_index) > 0 else 0
        return 0

    def get_node_index(self, node_id: str) -> Optional[int]:
        """Look up the contiguous tensor index of a node ID."""
        return self.node_to_idx.get(node_id)
