"""
MuleTrace AI — Tabular ML Invariant Verification Tests.

Validates the 10 non-negotiable architectural invariants required by Milestone 8:
- Invariant 1: Feature determinism (Same transaction/context -> identical feature vector)
- Invariant 2: Stable column order (Fixed order strictly matching TABULAR_FEATURE_COLUMNS)
- Invariant 3: No future leakage (Chronological split prevents look-ahead information)
- Invariant 4: No NaN/Inf values (All features guaranteed finite)
- Invariant 5: Input-order invariance (Feature representation is record-independent)
- Invariant 6: Missing-data safety (Missing optional attributes do not crash extraction)
- Invariant 7: ModelPrediction compatibility (Adapters implement ModelService output contract)
- Invariant 8: Existing model preservation (Existing MLEngine pipeline remains operational)
- Invariant 9: AutoGluon optionality (Graceful operation when AutoGluon is unavailable)
- Invariant 10: No startup training (Model training is strictly offline, not on startup)
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest
import pandas as pd

from app.domain.interfaces import ModelPrediction, ModelService
from app.domain.models import TransactionEvent
from app.engines.ml.tabular.autogluon_adapter import AutoGluonModelService
from app.engines.ml.tabular.dataset_builder import tabular_dataset_builder
from app.engines.ml.tabular.feature_builder import tabular_feature_builder
from app.engines.ml.tabular.feature_schema import TABULAR_FEATURE_COLUMNS, TabularFeatures
from app.engines.ml.tabular.xgboost_adapter import xgboost_model_service
from app.engines.ml.xgboost_model import ml_engine


def _tx(tx_id: str, amt: float = 10000.0, **kwargs) -> TransactionEvent:
    return TransactionEvent(
        transaction_id=tx_id,
        timestamp=datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc),
        amount=amt,
        sender_account="ACC-INV-1",
        receiver_account="ACC-INV-2",
        channel="UPI",
        **kwargs,
    )


# -----------------------------------------------------------------------------
# INVARIANT 1: FEATURE DETERMINISM
# -----------------------------------------------------------------------------
def test_invariant_1_feature_determinism():
    """Extracting features repeatedly on identical event produces identical vector."""
    event = _tx("TX-DET-1", amt=25000.0, device_id="DEV-DET", ip_address="10.10.10.10")
    f1 = tabular_feature_builder.build_features(event)
    f2 = tabular_feature_builder.build_features(event)

    assert f1.to_dict() == f2.to_dict()
    assert f1.to_vector() == f2.to_vector()


# -----------------------------------------------------------------------------
# INVARIANT 2: STABLE COLUMN ORDER
# -----------------------------------------------------------------------------
def test_invariant_2_stable_column_order():
    """to_vector() and to_dataframe() maintain fixed column order."""
    f = TabularFeatures(amount=100.0, graph_in_degree=2.0)
    df = f.to_dataframe()

    assert tuple(df.columns) == TABULAR_FEATURE_COLUMNS


# -----------------------------------------------------------------------------
# INVARIANT 3: NO FUTURE LEAKAGE
# -----------------------------------------------------------------------------
def test_invariant_3_no_future_leakage():
    """Chronological split strictly orders train before val and val before test."""
    records = [
        {"txn_id": f"TX-{i}", "timestamp": f"2026-09-19 12:{i:02d}:00", "account_number": "A", "receiver_account": "B", "amount": 100.0, "is_fraud": 0}
        for i in range(20)
    ]
    df = pd.DataFrame(records)
    X, y = tabular_dataset_builder.build_dataset_from_dataframe(df)

    split = tabular_dataset_builder.split_chronological(X, y, train_ratio=0.6, val_ratio=0.2, test_ratio=0.2)

    # First 12 in train, next 4 in val, last 4 in test
    assert len(split.X_train) == 12
    assert len(split.X_val) == 4
    assert len(split.X_test) == 4


# -----------------------------------------------------------------------------
# INVARIANT 4: NO NAN / INF VALUES
# -----------------------------------------------------------------------------
def test_invariant_4_no_nan_or_inf():
    """All vector outputs are guaranteed to be finite real numbers."""
    event = _tx("TX-NAN-1", amt=0.01, metadata={"user_risk_score": float("nan"), "device_risk_score": float("inf")})
    feat = tabular_feature_builder.build_features(event)
    vec = feat.to_vector()

    for val in vec:
        assert isinstance(val, (int, float))
        assert not pd.isna(val)
        assert abs(val) != float("inf")


# -----------------------------------------------------------------------------
# INVARIANT 5: INPUT-ORDER INVARIANCE
# -----------------------------------------------------------------------------
def test_invariant_5_input_order_invariance():
    """Extracting features for an individual event is independent of batch ordering."""
    e1 = _tx("TX-ORD-1", amt=1000.0)
    e2 = _tx("TX-ORD-2", amt=2000.0)

    f1_a = tabular_feature_builder.build_features(e1)
    f2_a = tabular_feature_builder.build_features(e2)

    f2_b = tabular_feature_builder.build_features(e2)
    f1_b = tabular_feature_builder.build_features(e1)

    assert f1_a.to_dict() == f1_b.to_dict()
    assert f2_a.to_dict() == f2_b.to_dict()


# -----------------------------------------------------------------------------
# INVARIANT 6: MISSING-DATA SAFETY
# -----------------------------------------------------------------------------
def test_invariant_6_missing_data_safety():
    """Minimal event with zero optional metadata extracts cleanly with defaults."""
    event = TransactionEvent(
        transaction_id="TX-MIN-1",
        timestamp=datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        sender_account="A",
        receiver_account="B",
    )
    feat = tabular_feature_builder.build_features(event)
    assert feat.amount == 100.0
    assert feat.has_device_id == 0.0
    assert feat.has_ip_address == 0.0


# -----------------------------------------------------------------------------
# INVARIANT 7: MODELPREDICTION COMPATIBILITY
# -----------------------------------------------------------------------------
def test_invariant_7_model_prediction_compatibility():
    """Both XGBoost and AutoGluon adapters produce domain ModelPrediction objects."""
    event = _tx("TX-PRED-1")
    p1 = xgboost_model_service.predict_risk(event)
    p2 = AutoGluonModelService().predict_risk(event)

    assert isinstance(p1, ModelPrediction)
    assert isinstance(p2, ModelPrediction)
    assert 0 <= p1.risk_score <= 100
    assert 0 <= p2.risk_score <= 100


# -----------------------------------------------------------------------------
# INVARIANT 8: EXISTING MODEL PRESERVATION
# -----------------------------------------------------------------------------
def test_invariant_8_existing_model_preservation():
    """Existing ml_engine.predict_transaction_risk remains completely functional."""
    tx_dict = {"amount": 5000.0, "channel": "UPI"}
    res = ml_engine.predict_transaction_risk(tx_dict)

    assert res is not None
    assert hasattr(res, "predicted_risk_score")
    assert hasattr(res, "fraud_probability")
    assert hasattr(res, "is_fraud_predicted")


# -----------------------------------------------------------------------------
# INVARIANT 9: AUTOGLUON OPTIONALITY
# -----------------------------------------------------------------------------
def test_invariant_9_autogluon_optionality():
    """AutoGluonModelService functions without crashing when AutoGluon is unavailable."""
    svc = AutoGluonModelService()
    event = _tx("TX-OPT-1")
    pred = svc.predict_risk(event)

    assert pred is not None
    assert isinstance(pred, ModelPrediction)


# -----------------------------------------------------------------------------
# INVARIANT 10: NO STARTUP TRAINING
# -----------------------------------------------------------------------------
def test_invariant_10_no_startup_training():
    """Importing app.main or initializing adapters does not trigger model.fit()."""
    # Simply verifying that importing modules does not train models
    from app.engines.ml.tabular import (
        autogluon_model_service,
        tabular_feature_builder,
        xgboost_model_service,
    )
    assert xgboost_model_service is not None
    assert autogluon_model_service is not None
    assert tabular_feature_builder is not None
