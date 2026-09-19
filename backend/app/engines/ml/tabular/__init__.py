"""
MuleTrace AI — Tabular ML Package.

Exports feature schemas, feature builders, dataset splitters, and model adapters
for tabular machine learning.
"""

from __future__ import annotations

from app.engines.ml.tabular.autogluon_adapter import (
    AutoGluonModelService,
    autogluon_model_service,
    is_autogluon_available,
)
from app.engines.ml.tabular.dataset_builder import (
    DatasetSplit,
    EvaluationMetrics,
    TabularDatasetBuilder,
    tabular_dataset_builder,
)
from app.engines.ml.tabular.feature_builder import (
    TabularFeatureBuilder,
    tabular_feature_builder,
)
from app.engines.ml.tabular.feature_schema import (
    TABULAR_FEATURE_COLUMNS,
    TOTAL_FEATURE_COUNT,
    TabularFeatures,
)
from app.engines.ml.tabular.model_adapter import BaseModelAdapter
from app.engines.ml.tabular.xgboost_adapter import (
    XGBoostModelService,
    xgboost_model_service,
)

__all__ = [
    "AutoGluonModelService",
    "BaseModelAdapter",
    "DatasetSplit",
    "EvaluationMetrics",
    "TABULAR_FEATURE_COLUMNS",
    "TOTAL_FEATURE_COUNT",
    "TabularDatasetBuilder",
    "TabularFeatureBuilder",
    "TabularFeatures",
    "XGBoostModelService",
    "autogluon_model_service",
    "is_autogluon_available",
    "tabular_dataset_builder",
    "tabular_feature_builder",
    "xgboost_model_service",
]
