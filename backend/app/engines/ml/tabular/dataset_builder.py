"""
MuleTrace AI — Tabular Dataset Builder & Splitting Pipeline.

Loads, transforms, and chronologically partitions transaction records for supervised
tabular model training and evaluation without temporal feature leakage.

Features:
- Chronological train / validation / test partitioning.
- Evaluates class imbalance metrics (Precision, Recall, F1, PR-AUC, ROC-AUC).
- Strictly preserves the 34-column TransactionMapper data integrity contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional, Union
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from app.domain.transaction_mapper import TransactionMapper
from app.engines.ml.tabular.feature_builder import TabularFeatureBuilder
from app.engines.ml.tabular.feature_schema import TABULAR_FEATURE_COLUMNS


@dataclass
class DatasetSplit:
    """Container holding feature matrices and target labels for partitioned data."""

    X_train: pd.DataFrame
    y_train: pd.Series
    X_val: pd.DataFrame
    y_val: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series
    target_name: str
    feature_names: list[str]


@dataclass
class EvaluationMetrics:
    """Comprehensive evaluation metrics for classification and regression."""

    target_type: Literal["classification", "regression"]
    sample_count: int
    positive_rate: float
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    roc_auc: Optional[float] = None
    pr_auc: Optional[float] = None
    confusion_matrix: Optional[list[list[int]]] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to clean serializable dictionary."""
        d: dict[str, Any] = {
            "target_type": self.target_type,
            "sample_count": self.sample_count,
            "positive_rate": round(self.positive_rate, 4),
        }
        if self.target_type == "classification":
            d.update({
                "precision": round(self.precision, 4) if self.precision is not None else None,
                "recall": round(self.recall, 4) if self.recall is not None else None,
                "f1": round(self.f1, 4) if self.f1 is not None else None,
                "roc_auc": round(self.roc_auc, 4) if self.roc_auc is not None else None,
                "pr_auc": round(self.pr_auc, 4) if self.pr_auc is not None else None,
                "confusion_matrix": self.confusion_matrix,
            })
        else:
            d.update({
                "mae": round(self.mae, 4) if self.mae is not None else None,
                "rmse": round(self.rmse, 4) if self.rmse is not None else None,
            })
        return d


class TabularDatasetBuilder:
    """Builder for constructing leak-free tabular datasets and chronological splits."""

    def __init__(self, builder: Optional[TabularFeatureBuilder] = None) -> None:
        self.builder = builder or TabularFeatureBuilder()

    def build_dataset_from_dataframe(
        self,
        df: pd.DataFrame,
        target_col: str = "is_fraud",
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Convert raw transaction DataFrame into TabularFeatures DataFrame and target series.

        Args:
            df: Raw DataFrame containing transaction records.
            target_col: Name of target column ('is_fraud' or 'risk_score').

        Returns:
            Tuple of (X: DataFrame with TABULAR_FEATURE_COLUMNS, y: target Series).
        """
        if df.empty:
            empty_x = pd.DataFrame(columns=list(TABULAR_FEATURE_COLUMNS))
            empty_y = pd.Series(dtype=float, name=target_col)
            return empty_x, empty_y

        # Chronological sorting guarantees temporal ordering
        if "timestamp" in df.columns:
            df_sorted = df.sort_values("timestamp").reset_index(drop=True)
        else:
            df_sorted = df.reset_index(drop=True)

        feature_records: list[dict[str, float]] = []
        for _, row in df_sorted.iterrows():
            row_dict = row.to_dict()
            tab_feat = self.builder.build_from_dict(row_dict)
            feature_records.append(tab_feat.to_dict())

        X = pd.DataFrame(feature_records, columns=list(TABULAR_FEATURE_COLUMNS))
        y = (
            df_sorted[target_col].astype(float)
            if target_col in df_sorted.columns
            else pd.Series([0.0] * len(df_sorted), name=target_col)
        )

        return X, y

    def split_chronological(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> DatasetSplit:
        """Partition data chronologically to prevent look-ahead temporal leakage.

        Args:
            X: Ordered feature matrix.
            y: Aligned target labels.
            train_ratio: Fraction for training (default: 0.70).
            val_ratio: Fraction for validation (default: 0.15).
            test_ratio: Fraction for testing (default: 0.15).

        Returns:
            DatasetSplit containing partitioned matrices.
        """
        n = len(X)
        if n == 0:
            return DatasetSplit(
                X_train=X, y_train=y,
                X_val=X, y_val=y,
                X_test=X, y_test=y,
                target_name=str(y.name or "target"),
                feature_names=list(TABULAR_FEATURE_COLUMNS),
            )

        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
        X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
        X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]

        return DatasetSplit(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
            target_name=str(y.name or "target"),
            feature_names=list(TABULAR_FEATURE_COLUMNS),
        )

    @staticmethod
    def evaluate_classification(
        y_true: Union[pd.Series, np.ndarray, list[float]],
        y_pred: Union[pd.Series, np.ndarray, list[float]],
        y_proba: Optional[Union[pd.Series, np.ndarray, list[float]]] = None,
    ) -> EvaluationMetrics:
        """Compute rigorous classification metrics focused on fraud class imbalance."""
        yt = np.array(y_true).astype(int)
        yp = np.array(y_pred).astype(int)
        n_samples = len(yt)
        pos_rate = float(np.mean(yt)) if n_samples > 0 else 0.0

        prec = float(precision_score(yt, yp, zero_division=0))
        rec = float(recall_score(yt, yp, zero_division=0))
        f1 = float(f1_score(yt, yp, zero_division=0))
        cm = confusion_matrix(yt, yp).tolist() if n_samples > 0 else [[0, 0], [0, 0]]

        roc = None
        pr_auc = None
        if y_proba is not None and len(np.unique(yt)) > 1:
            yp_prob = np.array(y_proba).astype(float)
            try:
                roc = float(roc_auc_score(yt, yp_prob))
                pr_auc = float(average_precision_score(yt, yp_prob))
            except ValueError:
                pass

        return EvaluationMetrics(
            target_type="classification",
            sample_count=n_samples,
            positive_rate=pos_rate,
            precision=prec,
            recall=rec,
            f1=f1,
            roc_auc=roc,
            pr_auc=pr_auc,
            confusion_matrix=cm,
        )


# Singleton instance
tabular_dataset_builder = TabularDatasetBuilder()
