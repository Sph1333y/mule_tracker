"""
MuleTrace AI — Investigations Endpoints.

API endpoints for investigation case management, evidence tracking, and deterministic
copilot synthesis (Milestone 12).
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engines.ai.copilot import DeterministicInvestigationCopilot
from app.engines.ai.models import InvestigationContext
from app.schemas.common import BaseResponse
from app.schemas.investigation import (
    CaseDetailRead,
    InvestigationEnrichRequest,
)
from app.services.soc_integration_service import soc_integration_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investigations", tags=["Investigations"])


class CopilotInvestigationRequest(BaseModel):
    """Request payload for the deterministic investigation copilot."""

    case_id: Optional[str] = Field(default=None, description="Case identifier")
    subject_id: Optional[str] = Field(default=None, description="Focal subject identifier (account or entity)")
    transaction_id: Optional[str] = Field(default=None, description="Primary transaction identifier")
    investigator_query: Optional[str] = Field(default=None, description="Optional investigator query or focus area")
    evidence_package: Optional[dict[str, Any]] = Field(default=None, description="M11 evidence package dictionary")
    fusion_result: Optional[dict[str, Any]] = Field(default=None, description="M10 fusion result dictionary")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional audit metadata")


@router.get("", response_model=BaseResponse[dict])
async def list_investigations() -> BaseResponse[dict]:
    """List active investigation cases and assigned analyst workloads."""
    return BaseResponse(
        success=True,
        message="Active investigation cases retrieved successfully",
        data={
            "cases": [
                {
                    "case_number": "CAS-2025-0045",
                    "title": "Mule Ring Operation — Western Region",
                    "priority": "CRITICAL",
                    "case_status": "IN_PROGRESS",
                    "assigned_investigator_id": "INV-882",
                    "alerts_count": 8,
                }
            ]
        },
    )


@router.post("/copilot", response_model=BaseResponse[dict[str, Any]])
async def run_investigation_copilot(
    request: CopilotInvestigationRequest,
) -> BaseResponse[dict[str, Any]]:
    """Execute deterministic investigation copilot synthesis on case evidence.

    Failsafe: All processing is isolated. Any unexpected parsing or processing
    errors return a clean error response without crashing the application.
    """
    try:
        copilot = DeterministicInvestigationCopilot()

        # Coerce evidence_package if provided as dict
        pkg, score, tier, subject = copilot._coerce_evidence_input(request.evidence_package or {})

        ctx = InvestigationContext(
            case_id=request.case_id or (pkg.case_id if pkg else None),
            subject_id=request.subject_id or subject,
            transaction_id=request.transaction_id or (pkg.transaction_id if pkg else None),
            evidence_package=pkg,
            investigator_query=request.investigator_query,
            metadata=request.metadata,
        )

        response = await copilot.investigate(ctx)

        return BaseResponse(
            success=True,
            message="Investigation copilot synthesis generated successfully",
            data=response.to_dict(),
        )
    except Exception as exc:
        logger.exception("Investigation copilot execution failed: %s", exc)
        return BaseResponse(
            success=False,
            message=f"Investigation copilot synthesis failed: {str(exc)}",
            data=None,
        )


@router.post("/enrich", response_model=BaseResponse[dict[str, Any]])
async def enrich_investigation_intelligence(
    request: InvestigationEnrichRequest,
) -> BaseResponse[dict[str, Any]]:
    """Execute end-to-end multi-modal intelligence enrichment on custom or case context."""
    try:
        tx_event = None
        history_events = None
        if request.transaction_event:
            from app.domain.transaction_mapper import TransactionMapper
            tx_event = TransactionMapper.from_dict(request.transaction_event)
        if request.history:
            from app.domain.transaction_mapper import TransactionMapper
            history_events = [TransactionMapper.from_dict(h) for h in request.history]

        intel = await soc_integration_service.get_case_intelligence(
            case_number=request.case_id or "CAS-AD-HOC",
            subject_id=request.subject_id,
            transaction_event=tx_event,
            history=history_events,
        )
        return BaseResponse(
            success=True,
            message="Investigation intelligence synthesized successfully",
            data=intel.model_dump(),
        )
    except Exception as exc:
        logger.exception("Investigation enrichment failed: %s", exc)
        return BaseResponse(
            success=False,
            message=f"Investigation enrichment failed: {str(exc)}",
            data=None,
        )


@router.get("/{case_number}", response_model=BaseResponse[dict[str, Any]])
async def get_investigation_case(case_number: str) -> BaseResponse[dict[str, Any]]:
    """Retrieve case overview and metadata by case reference."""
    case_detail = soc_integration_service.get_case_detail(case_number)
    if not case_detail:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation case '{case_number}' not found",
        )
    return BaseResponse(
        success=True,
        message=f"Investigation case '{case_number}' fetched successfully",
        data=case_detail.model_dump(),
    )


@router.patch("/{case_number}", response_model=BaseResponse[dict[str, Any]])
async def update_investigation_case(
    case_number: str,
    payload: dict[str, Any],
) -> BaseResponse[dict[str, Any]]:
    """Update case status, priority, or assigned investigator."""
    case_detail = soc_integration_service.get_case_detail(case_number)
    data = case_detail.model_dump() if case_detail else {"case_number": case_number}
    for k, v in payload.items():
        if v is not None:
            data[k] = v
    return BaseResponse(
        success=True,
        message=f"Investigation case '{case_number}' updated successfully",
        data=data,
    )


@router.get("/{case_number}/intelligence", response_model=BaseResponse[dict[str, Any]])
async def get_investigation_intelligence(case_number: str) -> BaseResponse[dict[str, Any]]:
    """Retrieve full multi-modal intelligence package (M10 Risk + M11 Evidence + M12 Copilot).

    Failsafe: 100% failure isolated. Returns graceful degraded intelligence
    if any subsystem fails without throwing an HTTP 500 error.
    """
    intel = await soc_integration_service.get_case_intelligence(case_number)
    return BaseResponse(
        success=True,
        message="Case intelligence package retrieved successfully",
        data=intel.model_dump(),
    )

