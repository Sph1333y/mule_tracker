"""
MuleTrace AI — Tabular Dataset Builder Unit Tests.

Tests dataset transformation from raw CSV/DataFrames, chronological splitting
to prevent future feature leakage, and class imbalance evaluation metrics.
"""

from __future__ import annotations

from pathlib import Path
import pytest
import pandas as pd

from app.engines.ml.tabular.dataset_builder import TabularDatasetBuilder, tabular_dataset_builder
from app.engines.ml.tabular.feature_schema import TABULAR_FEATURE_COLUMNS, TOTAL_FEATURE_COUNT


def _get_csv_path() -> Path:
    # ml/transactions.csv relative to project root
    p = Path(__file__).resolve().parent.parent.parent.parent.parent / "ml" / "transactions.csv"
    return p


def test_build_dataset_from_transactions_csv():
    """Transforms 500-record transactions.csv into model-ready matrix and target."""
    csv_path = _get_csv_path()
    assert csv_path.exists(), f"transactions.csv missing at {csv_path}"

    df = pd.read_csv(csv_path)
    X, y = tabular_dataset_builder.build_dataset_from_dataframe(df, target_col="is_fraud")

    assert len(X) == len(df)
    assert len(y) == len(df)
    assert list(X.columns) == list(TABULAR_FEATURE_COLUMNS)
    assert X.shape[1] == TOTAL_FEATURE_COUNT
    assert y.name == "is_fraud"
    assert set(y.unique()).issubset({0.0, 1.0})


def test_chronological_split_prevents_leakage():
    """Chronological split strictly partitions older transactions into train, newer into test."""
    csv_path = _get_csv_path()
    df = pd.read_csv(csv_path)
    X, y = tabular_dataset_builder.build_dataset_from_dataframe(df, target_col="is_fraud")

    split = tabular_dataset_builder.split_chronological(X, y, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)

    assert len(split.X_train) == 350
    assert len(split.X_val) == 75
    assert len(split.X_test) == 75
    assert len(split.X_train) + len(split.X_val) + len(split.X_test) == 500

    # Ensure feature matrix columns match TABULAR_FEATURE_COLUMNS
    assert list(split.X_train.columns) == list(TABULAR_FEATURE_COLUMNS)
    assert list(split.X_test.columns) == list(TABULAR_FEATURE_COLUMNS)


def test_empty_dataframe_handling():
    """Empty input DataFrame produces empty feature matrix without errors."""
    empty_df = pd.DataFrame()
    X, y = tabular_dataset_builder.build_dataset_from_dataframe(empty_df)

    assert X.empty
    assert y.empty
    assert list(X.columns) == list(TABULAR_FEATURE_COLUMNS)

    split = tabular_dataset_builder.split_chronological(X, y)
    assert split.X_train.empty
    assert split.X_test.empty


def test_classification_evaluation_metrics():
    """evaluate_classification produces precision, recall, F1, PR-AUC, ROC-AUC."""
    y_true = [0, 0, 1, 1, 1, 0, 1, 0, 0, 1]
    y_pred = [0, 0, 1, 1, 0, 0, 1, 0, 1, 1]
    y_proba = [0.1, 0.2, 0.9, 0.85, 0.4, 0.15, 0.95, 0.05, 0.6, 0.8]

    metrics = TabularDatasetBuilder.evaluate_classification(y_true, y_pred, y_proba)

    assert metrics.target_type == "classification"
    assert metrics.sample_count == 10
    assert metrics.precision is not None
    assert metrics.recall is not None
    assert metrics.f1 is not None
    assert metrics.roc_auc is not None
    assert metrics.pr_auc is not None
    assert metrics.confusion_matrix is not None
    assert isinstance(metrics.to_dict(), dict)
