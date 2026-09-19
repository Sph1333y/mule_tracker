"""
MuleTrace AI — ML Engine Package.

Exports Machine Learning models, feature engineering, and anomaly detection engines.
"""

from __future__ import annotations


from app.engines.ml.feature_engineering import FeatureEngineer
from app.engines.ml.isolation_forest import isolation_forest_detector
from app.engines.ml.graph import (
    GraphMLService,
    GraphSAGEMulService,
    graph_ml_service,
    graphsage_model_service,
)
from app.engines.ml.tabular import (
    AutoGluonModelService,
    TabularDatasetBuilder,
    TabularFeatureBuilder,
    TabularFeatures,
    XGBoostModelService,
    autogluon_model_service,
    tabular_dataset_builder,
    tabular_feature_builder,
    xgboost_model_service,
)
from app.engines.ml.xgboost_model import ml_engine

__all__ = [
    "AutoGluonModelService",
    "FeatureEngineer",
    "GraphMLService",
    "GraphSAGEMulService",
    "TabularDatasetBuilder",
    "TabularFeatureBuilder",
    "TabularFeatures",
    "XGBoostModelService",
    "autogluon_model_service",
    "graph_ml_service",
    "graphsage_model_service",
    "isolation_forest_detector",
    "ml_engine",
    "tabular_dataset_builder",
    "tabular_feature_builder",
    "xgboost_model_service",
]
