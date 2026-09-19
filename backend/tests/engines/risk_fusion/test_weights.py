"""
MuleTrace AI — Risk Fusion Weights Configuration & Validation Unit Tests.

Validates weight sum validation, normalization, non-negativity, and rejection of invalid values (Milestone 10).
"""

from __future__ import annotations

import pytest
from app.engines.risk_fusion.models import SignalModality
from app.engines.risk_fusion.weights import DEFAULT_FUSION_WEIGHTS, FusionWeights


def test_default_weights_sum_to_one():
    """Default baseline weights sum to exactly 1.0."""
    w = DEFAULT_FUSION_WEIGHTS
    total = sum(w.to_dict().values())
    assert pytest.approx(total, abs=1e-6) == 1.0
    assert w.rules_weight == 0.25
    assert w.temporal_weight == 0.15
    assert w.graph_weight == 0.20
    assert w.tabular_ml_weight == 0.25
    assert w.graph_ml_weight == 0.15


def test_custom_weights_and_normalization():
    """Arbitrary positive weights normalize cleanly to sum to 1.0."""
    w = FusionWeights(
        rules_weight=2.0,
        temporal_weight=1.0,
        graph_weight=1.0,
        tabular_ml_weight=4.0,
        graph_ml_weight=2.0,
    )
    norm = w.normalized_weights()
    assert pytest.approx(sum(norm.values()), abs=1e-6) == 1.0
    assert norm["rules"] == 0.20
    assert norm["temporal"] == 0.10
    assert norm["graph"] == 0.10
    assert norm["tabular_ml"] == 0.40
    assert norm["graph_ml"] == 0.20


def test_rejection_of_negative_weights():
    """Negative weights must trigger ValueError."""
    with pytest.raises(ValueError, match="cannot be negative"):
        FusionWeights(rules_weight=-0.1)


def test_rejection_of_nan_and_inf_weights():
    """NaN and infinite weights must trigger ValueError."""
    with pytest.raises(ValueError, match="must be finite"):
        FusionWeights(graph_weight=float("nan"))

    with pytest.raises(ValueError, match="must be finite"):
        FusionWeights(temporal_weight=float("inf"))


def test_rejection_of_all_zero_weights():
    """All-zero weights produce zero sum and must trigger ValueError."""
    with pytest.raises(ValueError, match="strictly positive"):
        FusionWeights(
            rules_weight=0.0,
            temporal_weight=0.0,
            graph_weight=0.0,
            tabular_ml_weight=0.0,
            graph_ml_weight=0.0,
        )


def test_get_weight_lookup():
    """Retrieve weights by enum or string safely."""
    w = FusionWeights()
    assert w.get_weight(SignalModality.RULES) == 0.25
    assert w.get_weight("temporal") == 0.15

    with pytest.raises(KeyError):
        w.get_weight("unsupported_modality")
