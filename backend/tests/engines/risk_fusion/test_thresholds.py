"""
MuleTrace AI — Risk Classification Thresholds Unit Tests.

Validates threshold bounds, monotonicity, deterministic categorization, and error handling (Milestone 10).
"""

from __future__ import annotations

import pytest
from app.engines.risk_fusion.models import RiskLevel
from app.engines.risk_fusion.thresholds import DEFAULT_RISK_THRESHOLDS, RiskThresholds


def test_default_threshold_monotonicity():
    """Default baseline thresholds are strictly increasing in (0, 100)."""
    t = DEFAULT_RISK_THRESHOLDS
    assert 0.0 < t.low_max < t.medium_max < t.high_max < 100.0
    assert t.low_max == 30.0
    assert t.medium_max == 65.0
    assert t.high_max == 85.0


def test_deterministic_classification_spectrum():
    """Maps entire score spectrum deterministically into appropriate risk bands."""
    t = DEFAULT_RISK_THRESHOLDS

    # LOW tier (< 30.0)
    assert t.classify(0.0) == RiskLevel.LOW
    assert t.classify(15.5) == RiskLevel.LOW
    assert t.classify(29.99) == RiskLevel.LOW

    # MEDIUM tier (30.0 <= s < 65.0)
    assert t.classify(30.0) == RiskLevel.MEDIUM
    assert t.classify(45.0) == RiskLevel.MEDIUM
    assert t.classify(64.99) == RiskLevel.MEDIUM

    # HIGH tier (65.0 <= s < 85.0)
    assert t.classify(65.0) == RiskLevel.HIGH
    assert t.classify(75.0) == RiskLevel.HIGH
    assert t.classify(84.99) == RiskLevel.HIGH

    # CRITICAL tier (>= 85.0)
    assert t.classify(85.0) == RiskLevel.CRITICAL
    assert t.classify(95.0) == RiskLevel.CRITICAL
    assert t.classify(100.0) == RiskLevel.CRITICAL


def test_out_of_bounds_score_handling():
    """Negative scores clamp to LOW, scores > 100 clamp to CRITICAL."""
    t = DEFAULT_RISK_THRESHOLDS
    assert t.classify(-10.0) == RiskLevel.LOW
    assert t.classify(150.0) == RiskLevel.CRITICAL
    assert t.classify(float("nan")) == RiskLevel.LOW


def test_rejection_of_non_monotonic_thresholds():
    """Non-monotonic or invalid threshold bounds trigger ValueError."""
    with pytest.raises(ValueError, match="strictly monotonic"):
        RiskThresholds(low_max=50.0, medium_max=40.0, high_max=80.0)

    with pytest.raises(ValueError, match="strictly monotonic"):
        RiskThresholds(low_max=30.0, medium_max=70.0, high_max=65.0)


def test_rejection_of_out_of_range_thresholds():
    """Thresholds outside (0, 100) trigger ValueError."""
    with pytest.raises(ValueError, match="must be in"):
        RiskThresholds(low_max=-5.0)

    with pytest.raises(ValueError, match="must be in"):
        RiskThresholds(high_max=105.0)
