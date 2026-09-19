"""
MuleTrace AI — AutoGluon Challenger Model Service Adapter.

Provides an optional, isolated benchmark/challenger tabular model adapter
implementing the domain ModelService contract.

Architectural Boundary:
- AutoGluon is an optional dependency: never imports autogluon at top level without try/except.
- If AutoGluon is not installed in the environment (e.g., on Python 3.14+ where binary wheels
  are not yet published), the adapter operates in graceful fallback/benchmark mode.
- Does NOT replace the existing production XGBoost / Random Forest pipeline.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
import pandas as pd

from app.domain.interfaces import ModelPrediction
from app.engines.ml.tabular.model_adapter import BaseModelAdapter
from app.engines.ml.tabular.xgboost_adapter import XGBoostModelService

logger = logging.getLogger("app.engines.ml.tabular.autogluon_adapter")


def is_autogluon_available() -> bool:
    """Check if autogluon.tabular is safely installed in current Python runtime."""
    try:
        import autogluon.tabular  # noqa: F401
        return True
    except (ImportError, ModuleNotFoundError):
        return False


class AutoGluonModelService(BaseModelAdapter):
    """Optional AutoGluon Tabular predictor adapter acting as an AutoML challenger."""

    def __init__(
        self,
        predictor: Optional[Any] = None,
        fallback_service: Optional[BaseModelAdapter] = None,
        model_name: str = "autogluon_challenger",
        model_version: str = "v1.0",
    ) -> None:
        super().__init__(model_name=model_name, model_version=model_version)
        self.predictor = predictor
        self.fallback_service = fallback_service or XGBoostModelService()
        self._available = is_autogluon_available()

    @property
    def is_available(self) -> bool:
        """Indicate whether AutoGluon runtime is available in current environment."""
        return self._available and (self.predictor is not None or is_autogluon_available())

    def get_status(self) -> dict[str, Any]:
        """Return diagnostic status regarding AutoGluon challenger availability."""
        return {
            "name": self.model_name,
            "version": self.model_version,
            "autogluon_installed": self._available,
            "has_trained_predictor": self.predictor is not None,
            "mode": "live_autogluon" if (self._available and self.predictor is not None) else "challenger_fallback",
            "environment_note": "AutoGluon is an optional challenger. On Python 3.14+, fallback adapter is engaged automatically.",
        }

    def train_challenger(
        self,
        train_data: pd.DataFrame,
        target_column: str = "is_fraud",
        time_limit_seconds: int = 60,
        presets: str = "medium_quality",
    ) -> dict[str, Any]:
        """Train an AutoGluon TabularPredictor on tabular dataset if available."""
        if not is_autogluon_available():
            logger.info("AutoGluon is not installed. Challenger training skipped gracefully.")
            return {
                "trained": False,
                "reason": "AutoGluon not installed in current Python runtime.",
            }

        try:
            from autogluon.tabular import TabularPredictor
            self.predictor = TabularPredictor(
                label=target_column,
                eval_metric="roc_auc" if target_column == "is_fraud" else "root_mean_squared_error",
            ).fit(
                train_data=train_data,
                time_limit=time_limit_seconds,
                presets=presets,
            )
            return {
                "trained": True,
                "leaderboard": self.predictor.leaderboard(silent=True).to_dict(orient="records"),
            }
        except Exception as e:
            logger.warning("Error during AutoGluon training: %s", e)
            return {"trained": False, "error": str(e)}

    def _predict_scores(
        self, X: pd.DataFrame
    ) -> tuple[int, float, bool, dict[str, Any]]:
        """Perform prediction via AutoGluon predictor if available, otherwise delegate to fallback."""
        if self.predictor is not None and is_autogluon_available():
            try:
                # Use AutoGluon TabularPredictor
                probas = self.predictor.predict_proba(X)
                # Handle probability output format
                if hasattr(probas, "iloc"):
                    prob = float(probas.iloc[0, 1] if probas.shape[1] > 1 else probas.iloc[0, 0])
                else:
                    prob = float(probas[0])

                is_fraud = bool(prob >= 0.5)
                risk_score = max(0, min(100, int(round(prob * 100))))
                details = {
                    "challenger_engine": "autogluon",
                    "best_model": getattr(self.predictor, "model_best", "ensemble"),
                }
                return risk_score, prob, is_fraud, details
            except Exception as e:
                logger.warning("AutoGluon inference error: %s. Falling back to primary ML service.", e)

        # Graceful fallback to primary XGBoost / RandomForest service
        if self.fallback_service:
            score, prob, is_f, details = self.fallback_service._predict_scores(X)
            details["challenger_engine"] = "fallback_baseline"
            details["autogluon_available"] = False
            details["reason"] = "AutoGluon runtime not installed or predictor not trained"
            return score, prob, is_f, details

        # Extreme fallback
        return (
            25,
            0.25,
            False,
            {
                "challenger_engine": "heuristic_fallback",
                "autogluon_available": False,
            },
        )


# Default singleton instance
autogluon_model_service = AutoGluonModelService()
