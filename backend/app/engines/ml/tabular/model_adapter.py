"""
MuleTrace AI — Tabular Model Service Adapter Contract.

Defines the base abstraction for tabular machine learning inference services,
implementing the domain ModelService port contract from M2.

Architectural Boundary:
- Implements: app.domain.interfaces.ModelService
- Output contract: app.domain.interfaces.ModelPrediction
- Zero dependency on FastAPI, SQLAlchemy, or AWS.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Optional
import pandas as pd

from app.domain.interfaces import ModelPrediction, ModelService
from app.domain.models import TransactionEvent
from app.engines.ml.tabular.feature_builder import TabularFeatureBuilder
from app.engines.ml.tabular.feature_schema import TabularFeatures
from app.engines.temporal.temporal_models import TemporalFeatures
from app.engines.graph.intelligence.graph_models import GraphFeatures


class BaseModelAdapter(ModelService):
    """Abstract base adapter implementing ModelService for tabular models."""

    def __init__(
        self,
        model_name: str = "base_model",
        model_version: str = "1.0.0",
        feature_builder: Optional[TabularFeatureBuilder] = None,
    ) -> None:
        self.model_name = model_name
        self.model_version = model_version
        self.feature_builder = feature_builder or TabularFeatureBuilder()

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
        tabular_feat = self.feature_builder.build_features(
            event=event,
            temporal_features=temporal_features,
            graph_features=graph_features,
        )
        return self.predict_tabular(tabular_feat)

    def predict_tabular(self, features: TabularFeatures) -> ModelPrediction:
        """Evaluate inference directly on a TabularFeatures vector."""
        df_row = features.to_dataframe()
        risk_score, proba, is_fraud, details = self._predict_scores(df_row)

        details["model_name"] = self.model_name
        details["feature_count"] = len(features.to_vector())

        return ModelPrediction(
            risk_score=max(0, min(100, int(round(risk_score)))),
            fraud_probability=round(float(proba), 4),
            is_fraud=bool(is_fraud),
            model_version=f"{self.model_name}_{self.model_version}",
            details=details,
        )

    @abstractmethod
    def _predict_scores(
        self, X: pd.DataFrame
    ) -> tuple[int, float, bool, dict[str, Any]]:
        """Subclass implementation returning (risk_score, fraud_probability, is_fraud, details)."""
        pass
