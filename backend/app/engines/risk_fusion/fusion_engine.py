"""
MuleTrace AI — Risk Fusion Engine.

Synthesizes multi-modal detection signals (Rules, Temporal, Graph, Tabular ML, Graph ML)
into a deterministic, explainable composite risk assessment.

Architectural Notice:
- M10 is the FIRST milestone permitted to combine outputs from multiple detection modalities.
- M10 strictly consumes M5, M6, M7, M8, and M9 outputs without mutating them.
- Composite risk calculation is deterministic, bounded, and explainable.
- Does NOT implement evidence narratives, graph traversal chains, or investigator actions (owned by M11).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.engines.risk_fusion.models import (
    FusionInput,
    FusionResult,
    MissingSignalPolicy,
    NormalizedSignal,
    RiskLevel,
    SignalContribution,
    SignalModality,
)
from app.engines.risk_fusion.normalizers import SignalNormalizer, signal_normalizer
from app.engines.risk_fusion.thresholds import DEFAULT_RISK_THRESHOLDS, RiskThresholds
from app.engines.risk_fusion.weights import DEFAULT_FUSION_WEIGHTS, FusionWeights

logger = logging.getLogger("app.engines.risk_fusion.fusion_engine")

# Canonical deterministic execution sequence
CANONICAL_MODALITY_ORDER: list[SignalModality] = [
    SignalModality.RULES,
    SignalModality.TEMPORAL,
    SignalModality.GRAPH,
    SignalModality.TABULAR_ML,
    SignalModality.GRAPH_ML,
]


class RiskFusionEngine:
    """Core synthesis engine computing composite fraud risk across all detection modalities."""

    def __init__(
        self,
        weights: Optional[FusionWeights] = None,
        thresholds: Optional[RiskThresholds] = None,
        missing_policy: MissingSignalPolicy = MissingSignalPolicy.RENORMALIZE_AVAILABLE,
        normalizer: Optional[SignalNormalizer] = None,
    ) -> None:
        """Initialize the fusion engine with verified configurations.

        Args:
            weights: Configurable modality weights (defaults to DEFAULT_FUSION_WEIGHTS).
            thresholds: Categorical risk tier thresholds (defaults to DEFAULT_RISK_THRESHOLDS).
            missing_policy: Policy governing handling of absent signals (defaults to RENORMALIZE_AVAILABLE).
            normalizer: Signal normalizer instance.
        """
        self.weights = weights or DEFAULT_FUSION_WEIGHTS
        self.weights.validate()
        self.thresholds = thresholds or DEFAULT_RISK_THRESHOLDS
        self.thresholds.validate()
        self.missing_policy = missing_policy
        self.normalizer = normalizer or signal_normalizer

    def extract_signals(self, fusion_input: FusionInput) -> dict[SignalModality, NormalizedSignal]:
        """Extract and normalize all modality signals from a unified FusionInput."""
        return {
            SignalModality.RULES: self.normalizer.normalize_rules(fusion_input.rule_signals),
            SignalModality.TEMPORAL: self.normalizer.normalize_temporal(fusion_input.temporal_features),
            SignalModality.GRAPH: self.normalizer.normalize_graph(fusion_input.graph_features),
            SignalModality.TABULAR_ML: self.normalizer.normalize_tabular_ml(fusion_input.tabular_prediction),
            SignalModality.GRAPH_ML: self.normalizer.normalize_graph_ml(fusion_input.graph_ml_prediction),
        }

    def calculate_effective_weights(
        self,
        signals: dict[SignalModality, NormalizedSignal],
    ) -> tuple[dict[SignalModality, float], list[str], list[str]]:
        """Compute effective weights according to the configured missing signal policy.

        Returns:
            Tuple of (effective_weights_map, available_modalities_list, unavailable_modalities_list).
        """
        raw_normalized_weights = self.weights.normalized_weights()

        available_modalities: list[str] = []
        unavailable_modalities: list[str] = []
        effective_weights: dict[SignalModality, float] = {}

        for mod in CANONICAL_MODALITY_ORDER:
            sig = signals[mod]
            if sig.is_available:
                available_modalities.append(mod.value)
            else:
                unavailable_modalities.append(mod.value)

        if self.missing_policy == MissingSignalPolicy.RENORMALIZE_AVAILABLE:
            total_available_weight = sum(
                raw_normalized_weights[mod.value]
                for mod in CANONICAL_MODALITY_ORDER
                if signals[mod].is_available
            )

            for mod in CANONICAL_MODALITY_ORDER:
                if signals[mod].is_available and total_available_weight > 0.0:
                    effective_weights[mod] = raw_normalized_weights[mod.value] / total_available_weight
                else:
                    effective_weights[mod] = 0.0

        elif self.missing_policy in (MissingSignalPolicy.ZERO_CONTRIBUTION, MissingSignalPolicy.PENALTY_BASELINE):
            for mod in CANONICAL_MODALITY_ORDER:
                effective_weights[mod] = raw_normalized_weights[mod.value]

        return effective_weights, available_modalities, unavailable_modalities

    def fuse(self, fusion_input: FusionInput) -> FusionResult:
        """Execute deterministic risk fusion over all available detection signals.

        Mathematical Formulation:
            CompositeRisk = sum_{m in Modalities} (EffectiveWeight_m * NormalizedSignal_m)
            CompositeRiskScore = round(CompositeRisk * 100.0, 2)
            RiskTier = classify(CompositeRiskScore)

        Args:
            fusion_input: Multi-modal signals for the transaction.

        Returns:
            Immutable FusionResult containing composite scores, tiers, and mathematical breakdown.
        """
        # 1. Normalize all signals deterministically
        signals = self.extract_signals(fusion_input)

        # 2. Compute effective weights under missing-signal policy
        effective_weights, available, unavailable = self.calculate_effective_weights(signals)
        raw_normalized_weights = self.weights.normalized_weights()

        # 3. Compute weighted contributions and aggregate composite risk
        contributions: dict[str, SignalContribution] = {}
        composite_risk: float = 0.0

        for mod in CANONICAL_MODALITY_ORDER:
            sig = signals[mod]
            eff_w = effective_weights[mod]
            cfg_w = raw_normalized_weights[mod.value]

            if sig.is_available:
                mod_val = sig.value
                status_text = f"Evaluated ({sig.raw_summary})"
            else:
                if self.missing_policy == MissingSignalPolicy.PENALTY_BASELINE:
                    mod_val = 0.20  # Neutral uninformative baseline
                    status_text = f"Unavailable ({sig.status}) -> Neutral Baseline 0.20"
                else:
                    mod_val = 0.0
                    status_text = f"Unavailable ({sig.status}) -> Zero Contribution"

            contribution = eff_w * mod_val
            composite_risk += contribution

            explanation = (
                f"{mod.value.upper()}: normalized={mod_val:.4f}, effective_weight={eff_w:.4f} "
                f"(configured={cfg_w:.4f}) -> contribution={contribution:.4f}. Status: {status_text}"
            )

            contributions[mod.value] = SignalContribution(
                modality=mod,
                normalized_value=mod_val,
                configured_weight=cfg_w,
                effective_weight=eff_w,
                weighted_score=round(contribution, 6),
                is_available=sig.is_available,
                explanation=explanation,
            )

        # 4. Strict bounding to unit interval and scaling to [0, 100]
        normalized_risk = min(1.0, max(0.0, composite_risk))
        composite_risk_score = round(normalized_risk * 100.0, 2)

        # 5. Deterministic classification into risk tier
        risk_level = self.thresholds.classify(composite_risk_score)

        metadata: dict[str, Any] = {
            "transaction_id": fusion_input.event.transaction_id if fusion_input.event else None,
            "total_available_modalities": len(available),
            "total_unavailable_modalities": len(unavailable),
            "renormalized": len(unavailable) > 0 and self.missing_policy == MissingSignalPolicy.RENORMALIZE_AVAILABLE,
        }

        return FusionResult(
            composite_risk_score=composite_risk_score,
            normalized_risk=round(normalized_risk, 4),
            risk_level=risk_level,
            contributions=contributions,
            available_modalities=available,
            unavailable_modalities=unavailable,
            effective_weights={mod.value: effective_weights[mod] for mod in CANONICAL_MODALITY_ORDER},
            missing_signal_policy=self.missing_policy,
            metadata=metadata,
            fusion_version="v1.0",
        )


# Singleton fusion engine instance with baseline configuration
risk_fusion_engine = RiskFusionEngine()
