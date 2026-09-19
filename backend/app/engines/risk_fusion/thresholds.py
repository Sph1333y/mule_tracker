"""
MuleTrace AI — Risk Classification & Threshold Configuration.

Provides configurable, validated thresholds for mapping continuous composite risk
scores [0.0, 100.0] into discrete operational risk tiers (LOW, MEDIUM, HIGH, CRITICAL).

Architectural Notice:
- These thresholds are operational engineering defaults for fraud analyst prioritization.
- They are NOT regulatory thresholds (e.g., RBI, FIU-IND, FinCEN) and carry no statutory certification.
- Threshold values are fully configurable and validated for strict monotonicity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.engines.risk_fusion.models import RiskLevel


@dataclass
class RiskThresholds:
    """Configurable boundaries dividing the continuous composite risk spectrum into risk bands.

    Default Baseline Configuration:
        low_max: 30.0       (Scores < 30.0 -> LOW)
        medium_max: 65.0    (Scores 30.0 <= s < 65.0 -> MEDIUM)
        high_max: 85.0      (Scores 65.0 <= s < 85.0 -> HIGH, >= 85.0 -> CRITICAL)
    """

    low_max: float = 30.0
    medium_max: float = 65.0
    high_max: float = 85.0

    def __post_init__(self) -> None:
        """Validate thresholds upon instantiation."""
        self.validate()

    def validate(self) -> None:
        """Enforce finite values and strictly increasing monotonic ordering.

        Raises:
            ValueError: If thresholds are non-finite, out of [0, 100], or non-monotonic.
        """
        for name, val in [("low_max", self.low_max), ("medium_max", self.medium_max), ("high_max", self.high_max)]:
            if val is None or not isinstance(val, (int, float)):
                raise ValueError(f"Threshold '{name}' must be numeric, got {val!r}")
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Threshold '{name}' must be finite, got {val}")
            if not (0.0 < val < 100.0):
                raise ValueError(f"Threshold '{name}' must be in (0.0, 100.0), got {val}")

        if not (self.low_max < self.medium_max < self.high_max):
            raise ValueError(
                f"Thresholds must be strictly monotonic: low_max ({self.low_max}) "
                f"< medium_max ({self.medium_max}) < high_max ({self.high_max})"
            )

    def classify(self, score: float) -> RiskLevel:
        """Deterministically map a continuous composite risk score into an operational RiskLevel.

        Args:
            score: Composite risk score in [0.0, 100.0].

        Returns:
            RiskLevel enum (LOW, MEDIUM, HIGH, CRITICAL).
        """
        if math.isnan(score) or math.isinf(score):
            return RiskLevel.LOW

        bounded_score = max(0.0, min(100.0, float(score)))

        if bounded_score < self.low_max:
            return RiskLevel.LOW
        elif bounded_score < self.medium_max:
            return RiskLevel.MEDIUM
        elif bounded_score < self.high_max:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def to_dict(self) -> dict[str, float]:
        """Convert thresholds to dictionary."""
        return {
            "low_max": float(self.low_max),
            "medium_max": float(self.medium_max),
            "high_max": float(self.high_max),
        }


# Default baseline configuration singleton
DEFAULT_RISK_THRESHOLDS = RiskThresholds()
