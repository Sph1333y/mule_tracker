"""
MuleTrace AI — GraphSAGEMulService Adapter Unit Tests.

Validates compliance with the domain ModelService port contract, inference behavior,
graceful un-trained fallback, and artifact generation.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import tempfile
import pytest

from app.domain.models import TransactionEvent
from app.domain.interfaces import ModelPrediction, ModelService
from app.engines.ml.graph.graph_ml_adapter import GraphSAGEMulService
from app.engines.ml.graph.graph_ml_service import GraphMLService
from app.engines.ml.graph.graphsage_model import is_torch_available


def _make_event(
    account_number: str = "ACC_SRC",
    receiver_account: str = "ACC_DST",
    amount: float = 5000.0,
    timestamp: datetime | None = None,
) -> TransactionEvent:
    if timestamp is None:
        timestamp = datetime(2026, 9, 19, 12, 0, 0)
    return TransactionEvent(
        transaction_id="TXN_TEST_001",
        sender_account=account_number,
        receiver_account=receiver_account,
        amount=float(amount),
        timestamp=timestamp,
        transaction_type="TRANSFER",
        channel="ONLINE",
    )


def test_adapter_implements_domain_model_service():
    """GraphSAGEMulService must be a concrete implementation of ModelService port."""
    service = GraphSAGEMulService()
    assert isinstance(service, ModelService)
    assert service.model_name == "graphsage_mule_detector"
    assert service.model_version == "v1.0"


def test_untrained_fallback_prediction():
    """When model artifacts are missing, predict() returns a clean zero fallback without error."""
    service = GraphSAGEMulService()
    # Ensure model is not loaded
    service.service.model = None

    event = _make_event()
    prediction = service.predict(event)

    assert isinstance(prediction, ModelPrediction)
    assert prediction.risk_score == 0
    assert prediction.fraud_probability == 0.0
    assert prediction.is_fraud is False
    assert "fallback" in prediction.model_version
    assert isinstance(prediction.details, dict)
    assert prediction.details["model_artifact_loaded"] is False


def test_untrained_fallback_predict_batch():
    """Batch prediction on un-trained model produces list of fallback predictions."""
    service = GraphSAGEMulService()
    service.service.model = None

    events = [_make_event(account_number=f"ACC_{i}") for i in range(3)]
    predictions = service.predict_batch(events)

    assert len(predictions) == 3
    for p in predictions:
        assert isinstance(p, ModelPrediction)
        assert p.risk_score == 0
        assert p.fraud_probability == 0.0


@pytest.mark.skipif(not is_torch_available(), reason="PyTorch required for training test")
def test_offline_training_and_inference(tmp_path):
    """Offline training builds artifacts, updates state, and generates real inference."""
    import pandas as pd

    # Create synthetic transactions CSV
    df = pd.DataFrame([
        {"txn_id": f"T{i}", "timestamp": f"2026-09-01 10:{i:02d}:00", "account_number": f"A{i}", "receiver_account": f"A{i+1}", "amount": 1000.0 * (i + 1), "is_fraud": i % 2}
        for i in range(10)
    ])
    csv_file = tmp_path / "transactions.csv"
    df.to_csv(csv_file, index=False)

    artifact_dir = tmp_path / "artifacts"
    ml_service = GraphMLService(artifact_dir=artifact_dir)

    metrics = ml_service.train_offline(
        transactions_csv_path=csv_file,
        epochs=3,
        hidden_dim=16,
    )

    assert metrics["train_nodes"] > 0
    assert (artifact_dir / "graphsage_model.pt").exists()
    assert (artifact_dir / "graphsage_meta.json").exists()
    assert ml_service.is_trained is True

    # Mount trained service into adapter
    adapter = GraphSAGEMulService(service=ml_service)
    assert adapter.is_trained is True

    event = _make_event(account_number="A1", receiver_account="A2")
    pred = adapter.predict(event)

    assert isinstance(pred, ModelPrediction)
    assert 0.0 <= pred.fraud_probability <= 1.0
    assert 0 <= pred.risk_score <= 100
    assert pred.details is not None
    assert "embedding_dim" in pred.details
    assert "num_subgraph_nodes" in pred.details
