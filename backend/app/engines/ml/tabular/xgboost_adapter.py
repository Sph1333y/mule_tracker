"""
MuleTrace AI — XGBoost / Scikit-Learn Tabular Model Service Adapter.

Integrates the existing trained Random Forest & XGBoost pipelines into the domain
ModelService port contract, preserving existing ML behavior while outputting
standardized ModelPrediction domain models.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
import numpy as np
import pandas as pd

from app.engines.ml.tabular.model_adapter import BaseModelAdapter
from app.engines.ml.xgboost_model import ml_engine, MLEngine

logger = logging.getLogger("app.engines.ml.tabular.xgboost_adapter")


class XGBoostModelService(BaseModelAdapter):
    """Production tabular ML service implementing ModelService via XGBoost / RandomForest."""

    def __init__(
        self,
        engine: Optional[MLEngine] = None,
        model_name: str = "xgboost_random_forest",
        model_version: str = "v1.0",
    ) -> None:
        super().__init__(model_name=model_name, model_version=model_version)
        self.engine: MLEngine = engine or ml_engine

    def _predict_scores(
        self, X: pd.DataFrame
    ) -> tuple[int, float, bool, dict[str, Any]]:
        """Bridge tabular DataFrame row to existing ML pipeline and return standard tuple."""
        row_dict = X.iloc[0].to_dict() if not X.empty else {}
        amt = float(row_dict.get("amount", 0.0))

        # Reconstruct transaction dict compatible with existing MLEngine pipeline
        tx_dict = {
            "amount": amt,
            "account_type": "savings",
            "channel": "UPI" if row_dict.get("channel_upi") else "NEFT" if row_dict.get("channel_neft") else "RTGS" if row_dict.get("channel_rtgs") else "IMPS",
            "account_age_days": row_dict.get("account_age_days", 180),
            "velocity_l6h": row_dict.get("velocity_l6h", 1),
            "churn_rate": row_dict.get("churn_rate", 0.01),
            "ip_account_density": row_dict.get("ip_account_density", 1),
            "amount_deviation_ratio": row_dict.get("amount_deviation_ratio", 1.0),
            "daily_limit_fraction": row_dict.get("daily_limit_fraction", 0.1),
            "user_risk_score": row_dict.get("user_risk_score", 15.0),
            "device_trust_score": row_dict.get("device_trust_score", 85.0),
            "is_rooted_or_emulator": int(row_dict.get("is_rooted_or_emulator", 0)),
            "device_risk_score": row_dict.get("device_risk_score", 10.0),
            "merchant_chargeback_rate": row_dict.get("merchant_chargeback_rate", 0.0),
            "merchant_risk_score": row_dict.get("merchant_risk_score", 5.0),
            "is_vpn_or_proxy": int(row_dict.get("is_vpn_or_proxy", 0)),
            "network_risk_score": row_dict.get("network_risk_score", 15.0),
        }

        # Leverage existing MLEngine
        res = self.engine.predict_transaction_risk(tx_dict)

        details = {
            "underlying_model": res.model_version,
            "raw_predicted_score": res.predicted_risk_score,
            "raw_fraud_probability": res.fraud_probability,
        }

        # Model output preservation — ZERO post-prediction score modulation
        risk_score = res.predicted_risk_score
        proba = res.fraud_probability
        is_fraud = res.is_fraud_predicted

        return risk_score, proba, is_fraud, details


# Default singleton instance
xgboost_model_service = XGBoostModelService()
