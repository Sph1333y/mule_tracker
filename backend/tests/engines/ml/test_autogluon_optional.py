"""
MuleTrace AI — AutoGluon Optional Challenger Unit Tests.

Validates that AutoGluon is purely an optional challenger component that:
1. Never crashes imports or execution when unavailable in the runtime.
2. Returns diagnostic status indicating environment availability.
3. Automatically delegates to the baseline model service when unavailable.
4. Correctly exercises TabularPredictor inference when a predictor is injected.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
import pandas as pd

from app.domain.interfaces import ModelPrediction, ModelService
from app.domain.models import TransactionEvent
from app.engines.ml.tabular.autogluon_adapter import (
    AutoGluonModelService,
    autogluon_model_service,
    is_autogluon_available,
)
from app.engines.ml.tabular.xgboost_adapter import XGBoostModelService


def _event() -> TransactionEvent:
    return TransactionEvent(
        transaction_id="TX-AG-1",
        timestamp=datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc),
        amount=15000.0,
        sender_account="ACC-AG-A",
        receiver_account="ACC-AG-B",
        channel="UPI",
    )


def test_autogluon_availability_check_non_crashing():
    """is_autogluon_available() safely returns boolean without raising exceptions."""
    avail = is_autogluon_available()
    assert isinstance(avail, bool)


def test_autogluon_service_initialization():
    """AutoGluonModelService instantiates and implements ModelService contract."""
    service = AutoGluonModelService()
    assert isinstance(service, ModelService)
    assert service.model_name == "autogluon_challenger"


def test_autogluon_status_diagnostics():
    """get_status() reports environment status, version, and diagnostic info."""
    status = autogluon_model_service.get_status()
    assert isinstance(status, dict)
    assert "autogluon_installed" in status
    assert "mode" in status
    assert "environment_note" in status


def test_autogluon_fallback_prediction_when_unavailable():
    """When AutoGluon is unavailable, predict_risk falls back to primary service."""
    service = AutoGluonModelService()
    event = _event()

    pred = service.predict_risk(event)

    assert isinstance(pred, ModelPrediction)
    assert 0 <= pred.risk_score <= 100
    assert 0.0 <= pred.fraud_probability <= 1.0
    assert pred.details.get("challenger_engine") in ("fallback_baseline", "heuristic_fallback")
    assert pred.details.get("autogluon_available") is False


def test_autogluon_inference_with_mock_predictor(monkeypatch):
    """When a trained predictor is present, AutoGluon evaluates inference successfully."""
    mock_predictor = MagicMock()
    # Mock predict_proba returning DataFrame with [P(0), P(1)]
    mock_predictor.predict_proba.return_value = pd.DataFrame([[0.15, 0.85]], columns=[0, 1])
    mock_predictor.model_best = "WeightedEnsemble_L2"

    # Monkeypatch is_autogluon_available to True
    monkeypatch.setattr("app.engines.ml.tabular.autogluon_adapter.is_autogluon_available", lambda: True)

    service = AutoGluonModelService(predictor=mock_predictor)
    assert service.is_available is True

    pred = service.predict_risk(_event())

    assert isinstance(pred, ModelPrediction)
    assert pred.risk_score == 85
    assert pred.fraud_probability == 0.85
    assert pred.is_fraud is True
    assert pred.details.get("challenger_engine") == "autogluon"
    assert pred.details.get("best_model") == "WeightedEnsemble_L2"
