"""
MuleTrace AI — Unit Tests for ML Evidence Extraction (M8 & M9).
"""

from app.domain.interfaces import ModelPrediction
from app.engines.evidence.collectors import collect_ml_evidence
from app.engines.evidence.models import EvidenceCategory, EvidenceSeverity, EvidenceSource


def test_collect_ml_tabular_trained_positive() -> None:
    """Verify active tabular ML model prediction generates structured evidence."""
    pred = ModelPrediction(
        risk_score=88,
        fraud_probability=0.88,
        is_fraud=True,
        model_version="xgboost_v1.0.0",
        details={"status": "model_trained", "model_artifact_loaded": True},
    )

    items = collect_ml_evidence(tabular_prediction=pred, graph_ml_prediction=None)
    assert len(items) == 1
    item = items[0]

    assert item.source == EvidenceSource.TABULAR_ML
    assert item.source_reference == "TABULAR_ML:xgboost_v1.0.0"
    assert item.category == EvidenceCategory.MODEL_PREDICTION
    assert item.severity == EvidenceSeverity.CRITICAL  # >= 0.85
    assert item.metrics["risk_score"] == 88
    assert item.metrics["fraud_probability"] == 0.88
    assert "Supervised gradient-boosted tabular model" in item.description


def test_collect_ml_graph_sage_trained_positive() -> None:
    """Verify active GraphSAGE model prediction generates structured evidence."""
    pred = ModelPrediction(
        risk_score=72,
        fraud_probability=0.72,
        is_fraud=True,
        model_version="graphsage_v1.0.0",
        details={"status": "model_trained", "model_artifact_loaded": True},
    )

    items = collect_ml_evidence(tabular_prediction=None, graph_ml_prediction=pred)
    assert len(items) == 1
    item = items[0]

    assert item.source == EvidenceSource.GRAPH_ML
    assert item.source_reference == "GRAPH_ML:graphsage_v1.0.0"
    assert item.category == EvidenceCategory.MODEL_PREDICTION
    assert item.severity == EvidenceSeverity.HIGH  # 0.65 <= p < 0.85
    assert item.metrics["risk_score"] == 72
    assert item.metrics["fraud_probability"] == 0.72
    assert "GraphSAGE" in item.description


def test_unavailable_model_does_not_fabricate_evidence() -> None:
    """Verify unavailable or fallback models do NOT create fake evidence items."""
    fallback_tab = ModelPrediction(
        risk_score=0,
        fraud_probability=0.0,
        is_fraud=False,
        model_version="xgboost_fallback_v0.1",
        details={"status": "model_unavailable", "model_artifact_loaded": False},
    )
    fallback_gnn = ModelPrediction(
        risk_score=0,
        fraud_probability=0.0,
        is_fraud=False,
        model_version="graphsage_untrained_fallback",
        details={"status": "model_unavailable", "model_artifact_loaded": False},
    )

    items = collect_ml_evidence(tabular_prediction=fallback_tab, graph_ml_prediction=fallback_gnn)
    assert len(items) == 0


def test_low_risk_model_does_not_create_suspicious_evidence() -> None:
    """Verify clean, low-risk predictions do not generate suspicious evidence items."""
    clean_tab = ModelPrediction(
        risk_score=10,
        fraud_probability=0.10,
        is_fraud=False,
        model_version="xgboost_v1.0.0",
        details={"status": "model_trained", "model_artifact_loaded": True},
    )

    items = collect_ml_evidence(tabular_prediction=clean_tab, graph_ml_prediction=None)
    assert len(items) == 0
