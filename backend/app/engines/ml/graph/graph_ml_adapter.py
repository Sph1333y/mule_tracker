"""
MuleTrace AI — GraphSAGE Model Service Adapter.

Implements the domain ModelService port contract from M2 using inductive GraphSAGE
graph neural networks. Evaluates account-level graph topologies, generates learned
node embeddings, and outputs standardized ModelPrediction domain models.

Architectural Boundary:
- Implements: app.domain.interfaces.ModelService
- Output contract: app.domain.interfaces.ModelPrediction
- Cloud-agnostic: operates over GraphRepository port (M2/M3/M4/M7).
- STRICT SEPARATION: Zero heuristic score adjustments. Pure GraphSAGE model output.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional
import networkx as nx

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore
    TORCH_AVAILABLE = False

from app.domain.interfaces import ModelPrediction, ModelService
from app.domain.models import TransactionEvent
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.engines.ml.graph.graph_feature_builder import GraphFeatureBuilder, graph_feature_builder
from app.engines.ml.graph.graph_ml_service import GraphMLService, graph_ml_service
from app.engines.ml.graph.graph_schema import (
    NODE_FEATURE_DIM,
    NODE_TYPE_ACCOUNT,
    GraphDataSnapshot,
    NodeEmbedding,
    sanitize_numeric,
)
from app.engines.ml.graph.graphsage_model import GraphSAGEClassifier
from app.engines.temporal.temporal_models import TemporalFeatures
from app.repositories.graph_factory import get_graph_repository

logger = logging.getLogger("app.engines.ml.graph.graph_ml_adapter")


class GraphSAGEMulService(ModelService):
    """Production Graph ML service implementing ModelService via GraphSAGE."""

    def __init__(
        self,
        model: Optional[GraphSAGEClassifier] = None,
        service: Optional[GraphMLService] = None,
        feature_builder: Optional[GraphFeatureBuilder] = None,
        model_name: str = "graphsage_mule_detector",
        model_version: str = "v1.0",
        threshold: float = 0.5,
    ) -> None:
        self.model_name = model_name
        self.model_version = model_version
        self.threshold = threshold
        self.service = service or graph_ml_service
        self.feature_builder = feature_builder or graph_feature_builder
        self._model: Optional[GraphSAGEClassifier] = model or self.service.model

    @property
    def model(self) -> Optional[GraphSAGEClassifier]:
        """Lazy-access model from service if loaded."""
        if self._model is None and self.service is not None:
            self._model = self.service.model
        return self._model

    @property
    def is_trained(self) -> bool:
        """Return True if model is initialized and ready for inference."""
        return self.model is not None

    def predict(
        self,
        event: TransactionEvent,
        temporal_features: Optional[TemporalFeatures] = None,
        graph_features: Optional[GraphFeatures] = None,
    ) -> ModelPrediction:
        """Alias for predict_risk to conform to standard ML predictor conventions."""
        return self.predict_risk(event=event, temporal_features=temporal_features, graph_features=graph_features)

    def predict_batch(
        self,
        events: list[TransactionEvent],
    ) -> list[ModelPrediction]:
        """Run batch inference for a collection of transaction events."""
        return [self.predict_risk(e) for e in events]

    def predict_risk(
        self,
        event: TransactionEvent,
        temporal_features: Optional[TemporalFeatures] = None,
        graph_features: Optional[GraphFeatures] = None,
    ) -> ModelPrediction:
        """Compute fraud risk score and classification for a canonical TransactionEvent.

        Args:
            event: Canonical TransactionEvent to evaluate.
            temporal_features: Optional contextual temporal features (M6).
            graph_features: Optional contextual graph features (M7).

        Returns:
            ModelPrediction containing risk_score (0-100), fraud_probability,
            is_fraud boolean, model_version, and feature details.
        """
        sender_acc = str(event.sender_account).strip()
        norm_node_id = f"account:{sender_acc}"

        # 1. Build local graph representation around sender account
        snapshot = self._build_event_subgraph(
            event=event,
            temporal_features=temporal_features,
            graph_features=graph_features,
        )

        # 2. Run GraphSAGE inference over the snapshot
        return self.predict_snapshot(snapshot=snapshot, target_node_id=norm_node_id)

    def predict_snapshot(
        self,
        snapshot: GraphDataSnapshot,
        target_node_id: str,
    ) -> ModelPrediction:
        """Evaluate inference directly over a pre-constructed GraphDataSnapshot."""
        norm_target = target_node_id if target_node_id.startswith("account:") else f"account:{target_node_id}"

        # Check if target exists in snapshot
        target_idx = snapshot.get_node_index(norm_target)

        # If model is not loaded or PyTorch is unavailable, return safe un-trained baseline
        current_model = self.model
        if current_model is None or not TORCH_AVAILABLE:
            return self._fallback_prediction(
                target_node_id=norm_target,
                reason="GraphSAGE model artifact not trained or runtime unavailable",
                num_neighbors=snapshot.num_edges,
            )

        if target_idx is None or snapshot.x.size(0) == 0:
            return self._fallback_prediction(
                target_node_id=norm_target,
                reason="Target node not found in graph topology",
                num_neighbors=0,
            )

        try:
            current_model.eval()
            with torch.no_grad():
                probas = current_model(snapshot.x, snapshot.edge_index)
                prob_val = float(probas[target_idx].item())

            # Mathematical calibration to domain range
            prob = max(0.0, min(1.0, prob_val))
            risk_score = max(0, min(100, int(round(prob * 100))))
            is_fraud = bool(prob >= self.threshold)

            details = {
                "model_name": self.model_name,
                "framework": "pytorch_native",
                "target_node_id": norm_target,
                "embedding_dim": current_model.embedding_dim,
                "num_subgraph_nodes": snapshot.num_nodes,
                "num_subgraph_edges": snapshot.num_edges,
                "raw_predicted_score": risk_score,
                "raw_fraud_probability": round(prob, 4),
                "model_artifact_loaded": True,
            }

            return ModelPrediction(
                risk_score=risk_score,
                fraud_probability=round(prob, 4),
                is_fraud=is_fraud,
                model_version=f"{self.model_name}_{self.model_version}",
                details=details,
            )
        except Exception as e:
            logger.warning("Error during GraphSAGE inference: %s", e)
            return self._fallback_prediction(
                target_node_id=norm_target,
                reason=f"Inference exception: {e}",
                num_neighbors=snapshot.num_edges,
            )

    def get_node_embedding(
        self,
        snapshot: GraphDataSnapshot,
        target_node_id: str,
    ) -> Optional[NodeEmbedding]:
        """Extract the 16-D learned dense representation vector for a target node."""
        norm_target = target_node_id if target_node_id.startswith("account:") else f"account:{target_node_id}"
        target_idx = snapshot.get_node_index(norm_target)

        current_model = self.model
        if current_model is None or not TORCH_AVAILABLE or target_idx is None:
            return None

        try:
            current_model.eval()
            with torch.no_grad():
                embeddings = current_model.get_embeddings(snapshot.x, snapshot.edge_index)
                vec = embeddings[target_idx].cpu().numpy().tolist()

            return NodeEmbedding(
                node_id=norm_target,
                vector=[float(v) for v in vec],
                dim=len(vec),
                model_version=f"{self.model_name}_{self.model_version}",
            )
        except Exception as e:
            logger.warning("Failed to extract node embedding: %s", e)
            return None

    def _build_event_subgraph(
        self,
        event: TransactionEvent,
        temporal_features: Optional[TemporalFeatures] = None,
        graph_features: Optional[GraphFeatures] = None,
    ) -> GraphDataSnapshot:
        """Construct local subgraph around event parties without blocking event loops."""
        repo = get_graph_repository()
        sender_id = f"account:{event.sender_account}"
        receiver_id = f"account:{event.receiver_account}"

        # If repo has an accessible NetworkX graph, extract directly in-memory
        if hasattr(repo, "graph") and isinstance(getattr(repo, "graph"), nx.MultiDiGraph):
            G_source: nx.MultiDiGraph = getattr(repo, "graph")
            sub_nodes = set()
            if sender_id in G_source:
                sub_nodes.add(sender_id)
                sub_nodes.update(G_source.successors(sender_id))
                sub_nodes.update(G_source.predecessors(sender_id))
            if receiver_id in G_source:
                sub_nodes.add(receiver_id)
                sub_nodes.update(G_source.successors(receiver_id))
                sub_nodes.update(G_source.predecessors(receiver_id))

            # Include current event parties
            sub_nodes.add(sender_id)
            sub_nodes.add(receiver_id)

            sub_G = G_source.subgraph(sub_nodes).copy()
            # Ensure transfer edge between current event parties is represented
            edge_key = str(event.transaction_id)
            sub_G.add_edge(
                sender_id,
                receiver_id,
                key=edge_key,
                relationship="TRANSFERRED_FUNDS",
                amount=float(event.amount),
            )
            return self.feature_builder.build_from_networkx(
                G=sub_G,
                temporal_context={sender_id: temporal_features} if temporal_features else None,
                graph_context={sender_id: graph_features} if graph_features else None,
            )

        # Fallback minimal 2-node graph for the immediate transaction
        G_min = nx.MultiDiGraph()
        G_min.add_node(sender_id, type=NODE_TYPE_ACCOUNT, account_number=event.sender_account)
        G_min.add_node(receiver_id, type=NODE_TYPE_ACCOUNT, account_number=event.receiver_account)
        G_min.add_edge(
            sender_id,
            receiver_id,
            key=str(event.transaction_id),
            relationship="TRANSFERRED_FUNDS",
            amount=float(event.amount),
        )
        return self.feature_builder.build_from_networkx(
            G=G_min,
            temporal_context={sender_id: temporal_features} if temporal_features else None,
            graph_context={sender_id: graph_features} if graph_features else None,
        )

    def _fallback_prediction(
        self,
        target_node_id: str,
        reason: str,
        num_neighbors: int,
    ) -> ModelPrediction:
        """Explicit safe fallback when model artifact is absent or node is unobserved."""
        return ModelPrediction(
            risk_score=0,
            fraud_probability=0.0,
            is_fraud=False,
            model_version=f"{self.model_name}_{self.model_version}_fallback",
            details={
                "model_name": self.model_name,
                "status": "model_unavailable",
                "reason": reason,
                "target_node_id": target_node_id,
                "num_subgraph_edges": num_neighbors,
                "model_artifact_loaded": False,
                "framework": "pytorch_native" if TORCH_AVAILABLE else "none",
            },
        )


# Default singleton instance
graphsage_model_service = GraphSAGEMulService()
