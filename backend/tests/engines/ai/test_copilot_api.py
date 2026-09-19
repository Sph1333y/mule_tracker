"""
MuleTrace AI — API Integration & Failure Isolation Tests for M12 Copilot Endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_existing_investigations_endpoint_unaffected(client):
    """Verify that existing GET /api/v1/investigations continues to work unmodified."""
    response = client.get("/api/v1/investigations")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "cases" in data["data"]
    assert len(data["data"]["cases"]) >= 1
    assert data["data"]["cases"][0]["case_number"] == "CAS-2025-0045"


def test_copilot_endpoint_success(client):
    """Verify successful execution of POST /api/v1/investigations/copilot."""
    payload = {
        "case_id": "CAS-API-01",
        "subject_id": "ACC-API-99",
        "evidence_package": {
            "case_id": "CAS-API-01",
            "subject_id": "ACC-API-99",
            "composite_risk_score": 91.2,
            "risk_level": "CRITICAL",
            "evidence_items": [
                {
                    "evidence_id": "EVD-API-001",
                    "category": "CIRCULAR_ROUTING",
                    "title": "Circular Transaction Ring",
                    "description": "3-hop fund cycle detected",
                    "severity": "CRITICAL",
                    "source": "RULE",
                    "source_reference": "RULE:R004",
                }
            ],
        },
    }

    response = client.post("/api/v1/investigations/copilot", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Investigation copilot synthesis generated successfully"

    data = body["data"]
    assert data["case_id"] == "CAS-API-01"
    assert data["subject_id"] == "ACC-API-99"
    assert data["composite_risk_score"] == 91.2
    assert data["risk_level"] == "CRITICAL"
    assert len(data["key_findings"]) == 1
    assert data["evidence_references"] == ["EVD-API-001"]
    assert data["generation_metadata"]["llm_used"] is False


def test_copilot_endpoint_empty_payload(client):
    """Verify copilot handles empty payload gracefully without error."""
    response = client.post("/api/v1/investigations/copilot", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["composite_risk_score"] == 0.0
    assert data["risk_level"] == "LOW"
    assert len(data["key_findings"]) == 0
    assert len(data["suggested_next_steps"]) >= 1


def test_copilot_endpoint_malformed_evidence(client):
    """Verify copilot handles malformed evidence fields safely with failure isolation."""
    payload = {
        "evidence_package": {
            "evidence_items": [
                {"invalid": 123},
                {"evidence_id": "EVD-VALID", "title": "Valid Item", "category": "INVALID_CAT"},
            ]
        }
    }
    response = client.post("/api/v1/investigations/copilot", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    # Coercion recovered the valid item with fallback category
    assert "EVD-VALID" in data["evidence_references"]
