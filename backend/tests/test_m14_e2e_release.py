"""
MuleTrace AI — Milestone 14 (M14) BUILD IT End-to-End Automated Release Test.

Validates the complete deterministic intelligence pipeline from raw transaction to SOC response:
    Transaction
    → M1 Canonical TransactionEvent
    → M5 Modular Rules
    → M6 Temporal Intelligence
    → M7 Graph Intelligence
    → M8 Tabular ML (XGBoost)
    → M9 Graph ML (GraphSAGE)
    → M10 Risk Fusion
    → M11 Evidence Engine
    → M12 Investigation Copilot
    → M13 SOC Integration API
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.domain import TransactionEvent
from app.services.soc_integration_service import soc_integration_service


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_m14_complete_e2e_pipeline_via_api(client):
    """Verify complete M1-M13 deterministic pipeline via POST /api/v1/investigations/enrich."""
    payload = {
        "case_id": "CAS-M14-RELEASE-01",
        "subject_id": "ACC-M14-SUBJECT-99",
        "transaction_event": {
            "transaction_id": "TX-M14-E2E-001",
            "sender_account": "ACC-M14-SENDER-01",
            "receiver_account": "ACC-M14-SUBJECT-99",
            "amount": 490000.0,
            "currency": "INR",
            "timestamp": "2025-07-24T14:30:00Z",
            "channel": "UPI",
            "device_id": "DEV-M14-9988",
            "ip_address": "192.168.1.150",
            "location_city": "Mumbai",
            "narration": "High value rapid transit",
        },
        "history": [
            {
                "transaction_id": "TX-M14-E2E-000",
                "sender_account": "ACC-M14-SENDER-01",
                "receiver_account": "ACC-M14-SUBJECT-99",
                "amount": 485000.0,
                "currency": "INR",
                "timestamp": "2025-07-24T14:28:00Z",
                "channel": "UPI",
                "device_id": "DEV-M14-9988",
                "ip_address": "192.168.1.150",
                "location_city": "Mumbai",
            },
            {
                "transaction_id": "TX-M14-E2E-001",
                "sender_account": "ACC-M14-SUBJECT-99",
                "receiver_account": "ACC-M14-BENEFICIARY-88",
                "amount": 480000.0,
                "currency": "INR",
                "timestamp": "2025-07-24T14:31:00Z",
                "channel": "IMPS",
                "device_id": "DEV-M14-9988",
                "ip_address": "192.168.1.150",
                "location_city": "Mumbai",
            }
        ]
    }

    response = client.post("/api/v1/investigations/enrich", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]

    # 1. Identity Verification
    assert data["case_id"] == "CAS-M14-RELEASE-01"
    assert data["subject_id"] == "ACC-M14-SUBJECT-99"
    assert data["transaction_id"] == "TX-M14-E2E-001"

    # 2. M10 Risk Fusion Verification
    assert 0.0 <= data["composite_risk_score"] <= 100.0
    assert data["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert len(data["risk_contributions"]) == 5

    modalities = {c["modality"] for c in data["risk_contributions"]}
    assert modalities == {"rules", "temporal", "graph", "tabular_ml", "graph_ml"}

    weight_sum = sum(c["effective_weight"] for c in data["risk_contributions"])
    assert abs(weight_sum - 1.0) < 0.01

    # 3. M11 Evidence Engine Verification
    assert data["total_evidence_count"] >= 1
    assert len(data["evidence_items"]) == data["total_evidence_count"]

    evidence_ids = {e["evidence_id"] for e in data["evidence_items"]}
    assert len(evidence_ids) == len(data["evidence_items"])  # Unique IDs

    # 4. M12 Investigation Copilot Verification
    assert len(data["investigation_summary"]) > 20
    assert len(data["key_findings"]) >= 1
    for kf in data["key_findings"]:
        assert kf["finding"]
        for eid in kf["evidence_ids"]:
            assert eid in evidence_ids

    assert len(data["suggested_next_steps"]) >= 1
    for act in data["suggested_next_steps"]:
        assert act["action_id"]
        assert act["priority"] in {"IMMEDIATE", "HIGH", "MEDIUM", "LOW"}
        for eid in act["related_evidence_ids"]:
            assert eid in evidence_ids

    assert len(data["follow_up_questions"]) >= 1
    assert len(data["limitations"]) >= 1

    # 5. Determinism Verification (Zero LLM)
    assert "generation_metadata" not in data or data.get("generation_metadata", {}).get("llm_used") is not True


@pytest.mark.asyncio
async def test_m14_pipeline_determinism_direct_service():
    """Verify that the M1-M13 orchestration service produces identical outputs across runs."""
    base_time = datetime(2025, 7, 24, 12, 0, 0, tzinfo=timezone.utc)
    anchor_tx = TransactionEvent(
        transaction_id="TX-M14-DET-01",
        sender_account="ACC-DET-SENDER",
        receiver_account="ACC-DET-TARGET",
        amount=350000.0,
        currency="INR",
        channel="IMPS",
        timestamp=base_time,
        device_id="DEV-DET-1",
        ip_address="10.0.0.1",
        location_city="Delhi",
    )

    results = []
    for _ in range(3):
        intel = await soc_integration_service.get_case_intelligence(
            case_number="CAS-M14-DET",
            subject_id="ACC-DET-TARGET",
            transaction_event=anchor_tx,
            history=[anchor_tx],
        )
        results.append((
            intel.composite_risk_score,
            intel.risk_level,
            intel.total_evidence_count,
            intel.investigation_summary,
        ))

    # All runs must be bit-for-bit identical
    assert results[0] == results[1] == results[2]
