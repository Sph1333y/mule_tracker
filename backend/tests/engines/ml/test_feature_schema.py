"""
MuleTrace AI — Tabular Feature Schema Tests.

Validates TABULAR_FEATURE_COLUMNS schema definition, ordering stability,
TabularFeatures conversion methods, and NaN/Inf prevention.
"""

from __future__ import annotations

import math
import pytest
import pandas as pd

from app.engines.ml.tabular.feature_schema import (
    TABULAR_FEATURE_COLUMNS,
    TOTAL_FEATURE_COUNT,
    TabularFeatures,
    sanitize_numeric,
)


def test_tabular_feature_columns_schema():
    """TABULAR_FEATURE_COLUMNS must have unique, non-empty string column names."""
    assert len(TABULAR_FEATURE_COLUMNS) == TOTAL_FEATURE_COUNT
    assert len(TABULAR_FEATURE_COLUMNS) == len(set(TABULAR_FEATURE_COLUMNS))
    for col in TABULAR_FEATURE_COLUMNS:
        assert isinstance(col, str)
        assert len(col) > 0


def test_tabular_features_default_initialization():
    """Default TabularFeatures instance must be populated with finite numeric defaults."""
    feat = TabularFeatures()
    d = feat.to_dict()

    assert len(d) == TOTAL_FEATURE_COUNT
    assert list(d.keys()) == list(TABULAR_FEATURE_COLUMNS)

    for k, v in d.items():
        assert isinstance(v, float)
        assert not math.isnan(v)
        assert not math.isinf(v)


def test_tabular_features_vector_and_dataframe_alignment():
    """to_vector() and to_dataframe() must strictly align with TABULAR_FEATURE_COLUMNS order."""
    feat = TabularFeatures(
        amount=50000.0,
        log_amount=4.699,
        channel_upi=1.0,
        graph_in_degree=5.0,
        temporal_tx_count_1h=12.0,
    )

    vec = feat.to_vector()
    assert len(vec) == TOTAL_FEATURE_COUNT
    assert vec[0] == 50000.0  # amount is first column

    df = feat.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == list(TABULAR_FEATURE_COLUMNS)
    assert df.shape == (1, TOTAL_FEATURE_COUNT)
    assert df["amount"].iloc[0] == 50000.0


def test_sanitize_numeric_prevents_nan_and_inf():
    """sanitize_numeric safely intercepts NaN, Inf, and incompatible types."""
    assert sanitize_numeric(float("nan"), default=0.0) == 0.0
    assert sanitize_numeric(float("inf"), default=0.0) == 0.0
    assert sanitize_numeric(float("-inf"), default=0.0) == 0.0
    assert sanitize_numeric(None, default=5.0) == 5.0
    assert sanitize_numeric("invalid", default=10.0) == 10.0
    assert sanitize_numeric("123.45", default=0.0) == 123.45
    assert sanitize_numeric(42, default=0.0) == 42.0
