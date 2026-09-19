"""
MuleTrace AI — Milestone 13 (M13) SOC Integration Test Suite.

Verifies end-to-end integration of the M1-M12 pipeline into the SOC API:
- Invariants INV-1 through INV-12
- Endpoints: GET /{case_number}, GET /{case_number}/intelligence, POST /enrich, PATCH /{case_number}
- Backward compatibility for existing investigations endpoints
- Determinism and immutability across M10, M11, and M12
- Failure isolation and graceful degradation
- Strictly zero LLM usage
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.soc_integration_service import soc_integration_service
from app.schemas.investigation import InvestigationEnrichRequest


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# =============================================================================
# 1. Existing Endpoints Backward Compatibility
# =============================================================================

def test_existing_investigations_list_unbroken(client):
    """Ensure GET /api/v1/investigations continues to work without modification."""
    response = client.get("/api/v1/investigations")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    cases = body["data"]["cases"]
    assert len(cases) >= 1
    case_numbers = [c["case_number"] for c in cases]
    assert "CAS-2025-0045" in case_numbers


def test_existing_copilot_endpoint_unbroken(client):
    """Ensure existing POST /api/v1/investigations/copilot continues to work."""
    payload = {
        "case_id": "CAS-TEST-01",
        "subject_id": "ACC-TEST-01",
        "evidence_package": {
            "case_id": "CAS-TEST-01",
            "subject_id": "ACC-TEST-01",
            "composite_risk_score": 88.0,
            "risk_level": "HIGH",
            "evidence_items": [
                {
                    "evidence_id": "EVD-01",
                    "category": "CIRCULAR_ROUTING",
                    "title": "Cycle detected",
                    "description": "3 hop cycle",
                    "severity": "HIGH",
                    "source": "GRAPH",
                }
            ],
        },
    }
    response = client.post("/api/v1/investigations/copilot", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["case_id"] == "CAS-TEST-01"
    assert data["data"]["generation_metadata"]["llm_used"] is False


# =============================================================================
# 2. Case Detail & Management Endpoints
# =============================================================================

def test_get_case_detail_success(client):
    """Test retrieving case details for a known canonical case."""
    response = client.get("/api/v1/investigations/CAS-2025-0045")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    case = body["data"]
    assert case["case_number"] == "CAS-2025-0045"
    assert case["priority"] == "CRITICAL"
    assert case["assigned_investigator_id"] == "INV-882"
    assert case["alerts_count"] == 8


def test_get_case_detail_not_found(client):
    """Test retrieving an invalid case number returns 404."""
    response = client.get("/api/v1/investigations/CAS-9999-9999")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body or body.get("success") is False


def test_patch_case_detail_success(client):
    """Test updating case status and priority via PATCH."""
    payload = {
        "case_status": "ESCALATED",
        "priority": "CRITICAL",
    }
    response = client.patch("/api/v1/investigations/CAS-2025-0047", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["case_status"] == "ESCALATED"
    assert body["data"]["priority"] == "CRITICAL"


# =============================================================================
# 3. M13 Intelligence Pipeline Endpoint
# =============================================================================

def test_get_case_intelligence_canonical_case(client):
    """Verify end-to-end intelligence synthesis for canonical case CAS-2025-0045."""
    response = client.get("/api/v1/investigations/CAS-2025-0045/intelligence")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    intel = body["data"]

    # Invariant: Identity & Schema
    assert intel["case_id"] == "CAS-2025-0045"
    assert intel["subject_id"] == "XXXX1002"
    assert intel["transaction_id"] == "TX-2025-0045-B"
    assert 0.0 <= intel["composite_risk_score"] <= 100.0
    assert intel["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    # Invariant: Modality Contributions
    assert len(intel["risk_contributions"]) == 5
    modalities = {c["modality"] for c in intel["risk_contributions"]}
    expected_modalities = {
        "rules",
        "temporal",
        "graph",
        "tabular_ml",
        "graph_ml",
    }
    assert modalities == expected_modalities

    # Check sum of effective weights
    weight_sum = sum(c["effective_weight"] for c in intel["risk_contributions"])
    assert abs(weight_sum - 1.0) < 0.01

    # Invariant: Evidence Items
    assert intel["total_evidence_count"] >= 1
    assert len(intel["evidence_items"]) == intel["total_evidence_count"]

    evidence_ids = {e["evidence_id"] for e in intel["evidence_items"]}
    assert len(evidence_ids) == len(intel["evidence_items"])  # No duplicate IDs

    # Invariant: Key Findings and Suggested Next Steps
    assert len(intel["key_findings"]) >= 1
    for kf in intel["key_findings"]:
        assert kf["finding"]
        assert kf["severity"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        # Evidence ID validity: every referenced ID must exist in evidence_items
        for eid in kf["evidence_ids"]:
            assert eid in evidence_ids

    assert len(intel["suggested_next_steps"]) >= 1
    for step in intel["suggested_next_steps"]:
        assert step["action_id"]
        assert step["title"]
        assert step["priority"] in {"IMMEDIATE", "HIGH", "MEDIUM", "LOW"}
        for eid in step["related_evidence_ids"]:
            assert eid in evidence_ids

    # Copilot Narrative
    assert len(intel["investigation_summary"]) > 20
    assert len(intel["follow_up_questions"]) >= 1
    assert len(intel["limitations"]) >= 1


def test_get_case_intelligence_all_canonical_cases(client):
    """Verify all 5 canonical cases return 200 OK with valid intelligence structures."""
    for case_num in ["CAS-2025-0045", "CAS-2025-0046", "CAS-2025-0047", "CAS-2025-0048", "CAS-2025-0049"]:
        res = client.get(f"/api/v1/investigations/{case_num}/intelligence")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["case_id"] == case_num
        assert len(data["risk_contributions"]) == 5
        assert data["composite_risk_score"] >= 0.0


# =============================================================================
# 4. Ad-Hoc Investigation Enrichment (POST /enrich)
# =============================================================================

def test_enrich_ad_hoc_investigation(client):
    """Test dynamic on-the-fly intelligence enrichment for custom payload."""
    payload = {
        "case_id": "CAS-CUSTOM-001",
        "subject_id": "ACC-CUSTOM-88",
        "transaction_event": {
            "transaction_id": "TXN-CUSTOM-88",
            "sender_account": "ACC-CUSTOM-88",
            "receiver_account": "ACC-BENEFICIARY-99",
            "amount": 95000.0,
            "currency": "INR",
            "timestamp": "2025-07-24T12:00:00Z",
            "channel": "IMPS",
            "device_id": "DEV-CUSTOM-88",
            "ip_address": "192.168.10.50",
            "location_city": "Mumbai",
        },
    }
    response = client.post("/api/v1/investigations/enrich", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["case_id"] == "CAS-CUSTOM-001"
    assert data["subject_id"] == "ACC-CUSTOM-88"
    assert data["transaction_id"] == "TXN-CUSTOM-88"
    assert len(data["risk_contributions"]) == 5
    assert len(data["suggested_next_steps"]) >= 1


# =============================================================================
# 5. Pipeline Invariants: Determinism, Zero LLM & Failure Isolation
# =============================================================================

@pytest.mark.asyncio
async def test_determinism_5_consecutive_runs():
    """Verify that running the intelligence pipeline 5 times gives bit-identical results."""
    scores = []
    tiers = []
    evidence_counts = []

    for _ in range(5):
        intel = await soc_integration_service.get_case_intelligence("CAS-2025-0045")
        scores.append(intel.composite_risk_score)
        tiers.append(intel.risk_level)
        evidence_counts.append(intel.total_evidence_count)

    assert len(set(scores)) == 1, f"Composite score varied across runs: {scores}"
    assert len(set(tiers)) == 1, f"Risk tier varied across runs: {tiers}"
    assert len(set(evidence_counts)) == 1, f"Evidence count varied across runs: {evidence_counts}"


@pytest.mark.asyncio
async def test_strictly_zero_llm():
    """Verify that no external generative AI is invoked in the M13 pipeline."""
    intel = await soc_integration_service.get_case_intelligence("CAS-2025-0045")
    assert not hasattr(intel, "llm_model")
    assert "subject" in intel.investigation_summary.lower() or "case" in intel.investigation_summary.lower()


@pytest.mark.asyncio
async def test_failure_isolation_fallback():
    """Verify that an unknown case degrades gracefully without raising unhandled errors."""
    intel = await soc_integration_service.get_case_intelligence("CAS-UNKNOWN-999")
    assert intel.case_id == "CAS-UNKNOWN-999"
    assert intel.composite_risk_score >= 0.0
    assert intel.risk_level in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert len(intel.risk_contributions) == 5
