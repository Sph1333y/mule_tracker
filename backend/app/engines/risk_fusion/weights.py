"""
MuleTrace AI — Risk Fusion Weight Configuration & Validation.

Provides configurable, validated weights for multi-modal risk signal synthesis.

Architectural Notice:
- The default weight allocations represent an operational heuristic baseline configuration.
- These weights are NOT claims of statistical optimality, regulatory validation, or statutory compliance.
- Modality weights are fully configurable and strictly validated before application.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.engines.risk_fusion.models import SignalModality


@dataclass
class FusionWeights:
    """Configurable weights controlling the contribution of each detection modality.

    Default Baseline Configuration:
        rules_weight: 0.25      (Forensic heuristics, deterministic patterns)
        temporal_weight: 0.15   (Velocity bursts, rapid pass-through sequences)
        graph_weight: 0.20      (Topological cycles, shared device/IP clusters, fan-in/out)
        tabular_ml_weight: 0.25 (Gradient-boosted tabular decision boundaries)
        graph_ml_weight: 0.15   (Inductive GraphSAGE structural node representations)
    """

    rules_weight: float = 0.25
    temporal_weight: float = 0.15
    graph_weight: float = 0.20
    tabular_ml_weight: float = 0.25
    graph_ml_weight: float = 0.15

    def __post_init__(self) -> None:
        """Validate weight attributes upon instantiation."""
        self.validate()

    def validate(self) -> None:
        """Strict validation of weight numerical values.

        Raises:
            ValueError: If any weight is negative, non-finite (NaN/Inf), or total sum is zero/invalid.
        """
        weights_map = self.to_dict()
        for modality_name, val in weights_map.items():
            if val is None or not isinstance(val, (int, float)):
                raise ValueError(f"Weight for '{modality_name}' must be a numeric float, got {val!r}")
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Weight for '{modality_name}' must be finite, got {val}")
            if val < 0.0:
                raise ValueError(f"Weight for '{modality_name}' cannot be negative, got {val}")

        total = sum(weights_map.values())
        if total <= 0.0:
            raise ValueError(f"Sum of fusion weights must be strictly positive, got {total}")

    def to_dict(self) -> dict[str, float]:
        """Convert weights to dictionary keyed by modality string."""
        return {
            SignalModality.RULES.value: float(self.rules_weight),
            SignalModality.TEMPORAL.value: float(self.temporal_weight),
            SignalModality.GRAPH.value: float(self.graph_weight),
            SignalModality.TABULAR_ML.value: float(self.tabular_ml_weight),
            SignalModality.GRAPH_ML.value: float(self.graph_ml_weight),
        }

    def normalized_weights(self) -> dict[str, float]:
        """Return weights mathematically normalized to sum to exactly 1.0."""
        self.validate()
        raw = self.to_dict()
        total = sum(raw.values())
        return {k: v / total for k, v in raw.items()}

    def get_weight(self, modality: SignalModality | str) -> float:
        """Retrieve configured weight for a specific modality."""
        key = modality.value if isinstance(modality, SignalModality) else str(modality)
        weights_dict = self.to_dict()
        if key not in weights_dict:
            raise KeyError(f"Unknown signal modality '{key}'. Supported: {list(weights_dict.keys())}")
        return weights_dict[key]


# Default baseline configuration singleton
DEFAULT_FUSION_WEIGHTS = FusionWeights()
