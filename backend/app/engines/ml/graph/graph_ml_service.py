"""
MuleTrace AI — Graph ML Training & Artifact Service.

Manages offline GraphSAGE model training, validation, artifact persistence,
and lifecycle diagnostics.

Architectural Invariant (INV-9):
- ZERO startup model training.
- Training is strictly an explicit offline operation.
- Application startup and import never trigger model training.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore
    nn = None  # type: ignore
    optim = None  # type: ignore
    TORCH_AVAILABLE = False

from app.engines.ml.graph.graph_schema import NODE_FEATURE_DIM, GraphDataSnapshot
from app.engines.ml.graph.graphsage_model import (
    GraphSAGEClassifier,
    is_pyg_available,
    is_torch_available,
    set_graph_ml_seed,
)

logger = logging.getLogger("app.engines.ml.graph.graph_ml_service")
DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


class GraphMLService:
    """Manages GraphSAGE training routines, artifact persistence, and model lifecycle."""

    def __init__(
        self,
        artifacts_dir: Optional[Path] = None,
        model: Optional[GraphSAGEClassifier] = None,
        artifact_dir: Optional[Path] = None,
    ) -> None:
        self.artifacts_dir = artifacts_dir or artifact_dir or DEFAULT_ARTIFACTS_DIR
        self.model_path = self.artifacts_dir / "graphsage_model.pt"
        self.meta_path = self.artifacts_dir / "graphsage_meta.json"
        self.model: Optional[GraphSAGEClassifier] = model
        self.is_loaded: bool = False

        # Attempt safe loading of existing pre-trained artifact (NO training on init)
        if self.model is None:
            self._load_artifact_if_exists()
        else:
            self.is_loaded = True

    def _load_artifact_if_exists(self) -> bool:
        """Safely load model artifact if it exists on disk without crashing if absent."""
        if not TORCH_AVAILABLE:
            return False

        if self.model_path.exists():
            try:
                # Load metadata
                meta = {}
                if self.meta_path.exists():
                    with open(self.meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)

                in_feat = meta.get("in_features", NODE_FEATURE_DIM)
                hidden_dim = meta.get("hidden_dim", 32)
                embed_dim = meta.get("embedding_dim", 16)
                agg_type = meta.get("aggregator_type", "mean")

                # Instantiate model and load state_dict
                model = GraphSAGEClassifier(
                    in_features=in_feat,
                    hidden_dim=hidden_dim,
                    embedding_dim=embed_dim,
                    aggregator_type=agg_type,
                )
                state_dict = torch.load(self.model_path, map_location="cpu")
                model.load_state_dict(state_dict)
                model.eval()

                self.model = model
                self.is_loaded = True
                logger.info("GraphSAGE model loaded successfully from %s", self.model_path)
                return True
            except Exception as e:
                logger.warning("Failed to load GraphSAGE artifact from %s: %s", self.model_path, e)
                return False
        return False

    def get_status(self) -> dict[str, Any]:
        """Return diagnostic health and availability status of the Graph ML subsystem."""
        return {
            "torch_available": is_torch_available(),
            "pyg_available": is_pyg_available(),
            "model_trained": self.is_loaded,
            "artifact_exists": self.model_path.exists(),
            "model_path": str(self.model_path),
            "model_name": "graphsage_v1.0",
            "framework": "pytorch_native",
            "in_features": NODE_FEATURE_DIM,
            "mode": "live_inference" if self.is_loaded else "model_unavailable",
        }

    @property
    def is_trained(self) -> bool:
        """Return True if model weights are loaded in memory."""
        return self.model is not None and self.is_loaded

    def train_offline(
        self,
        snapshot: Optional[Any] = None,
        epochs: int = 25,
        lr: float = 0.01,
        weight_decay: float = 1e-4,
        pos_weight: float = 4.0,
        seed: int = 42,
        save_artifact: bool = True,
        transactions_csv_path: Optional[str | Path] = None,
        hidden_dim: int = 32,
    ) -> dict[str, Any]:
        """Explicit offline training procedure for GraphSAGE.

        NEVER called automatically by application startup or API requests.

        Args:
            snapshot: GraphDataSnapshot, DataFrame, or CSV path with data.
            epochs: Training epochs (default: 25).
            lr: Learning rate (default: 0.01).
            weight_decay: L2 regularization penalty.
            pos_weight: Loss weight multiplier for minority positive (fraud) class.
            seed: Deterministic random seed.
            save_artifact: Whether to persist weights to disk.
            transactions_csv_path: Optional CSV path if snapshot is omitted.
            hidden_dim: Hidden dimension for GraphSAGE layers.

        Returns:
            Dictionary containing training history and loss convergence stats.
        """
        if not TORCH_AVAILABLE:
            return {
                "trained": False,
                "reason": "PyTorch is not available in current runtime.",
            }

        if snapshot is None and transactions_csv_path is not None:
            snapshot = transactions_csv_path

        if isinstance(snapshot, (str, Path)):
            import pandas as pd
            from app.engines.ml.graph.graph_dataset import graph_ml_dataset_builder
            df = pd.read_csv(snapshot)
            snapshot = graph_ml_dataset_builder.build_snapshot_from_dataframe(df)
        elif hasattr(snapshot, "columns"):  # DataFrame
            from app.engines.ml.graph.graph_dataset import graph_ml_dataset_builder
            snapshot = graph_ml_dataset_builder.build_snapshot_from_dataframe(snapshot)

        set_graph_ml_seed(seed)

        x = snapshot.x
        edge_index = snapshot.edge_index
        y = snapshot.y

        if y is None or x.size(0) == 0:
            return {"trained": False, "reason": "No labeled nodes present for supervised training."}

        # Filter nodes with valid binary labels (0.0 or 1.0; -1 indicates unlabeled)
        labeled_mask = (y >= 0.0)
        if labeled_mask.sum() == 0:
            return {"trained": False, "reason": "Zero labeled account nodes available."}

        # Instantiate fresh model
        model = GraphSAGEClassifier(
            in_features=x.size(1),
            hidden_dim=32,
            embedding_dim=16,
            dropout=0.1,
            aggregator_type="mean",
        )
        model.train()

        # Weighted BCE Loss to handle fraud imbalance
        loss_weight = torch.tensor([pos_weight], dtype=torch.float32)
        criterion = nn.BCELoss(weight=loss_weight)
        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

        loss_history: list[float] = []

        for epoch in range(epochs):
            optimizer.zero_grad()
            probas = model(x, edge_index)

            # Compute loss only on labeled nodes
            loss = criterion(probas[labeled_mask], y[labeled_mask])
            loss.backward()
            optimizer.step()

            loss_val = float(loss.item())
            loss_history.append(round(loss_val, 5))

        model.eval()
        self.model = model
        self.is_loaded = True

        # Persist weights and metadata if requested
        if save_artifact:
            self.artifacts_dir.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), self.model_path)
            meta = model.get_model_config()
            meta.update({
                "epochs": epochs,
                "final_loss": loss_history[-1] if loss_history else None,
                "labeled_nodes": int(labeled_mask.sum().item()),
                "total_nodes": int(x.size(0)),
                "num_edges": snapshot.num_edges,
            })
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

        return {
            "trained": True,
            "train_nodes": int(x.size(0)),
            "labeled_nodes": int(labeled_mask.sum().item()),
            "epochs": epochs,
            "final_loss": loss_history[-1] if loss_history else None,
            "loss_history": loss_history,
            "artifact_saved": save_artifact,
        }


# Singleton instance
graph_ml_service = GraphMLService()
