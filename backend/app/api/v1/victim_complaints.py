"""
MuleTrace AI — Victim Complaints Public API.

Public, unauthenticated endpoints for the external User Portal to submit
victim complaints and check basic status.
"""

from __future__ import annotations


from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response

from app.api.dependencies import get_victim_complaint_service
from app.schemas.victim_complaint import VictimComplaintSubmit, VictimComplaintResponse
from app.services.victim_complaint_service import VictimComplaintService

router = APIRouter(prefix="/complaints", tags=["Victim Complaints"])


@router.post(
    "/public/submit",
    response_model=VictimComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new victim complaint from the Public User Portal",
)
async def submit_victim_complaint(
    payload: VictimComplaintSubmit,
    service: VictimComplaintService = Depends(get_victim_complaint_service),
) -> VictimComplaintResponse:
    """
    Submit a victim complaint. This is intended to be called by the standalone
    User Portal. The complaint is stored as a Report (type VICTIM_COMPLAINT)
    and becomes immediately visible in the Admin Reports dashboard.
    """
    return await service.submit_complaint(payload)


@router.get(
    "/public/status/{complaint_number}",
    summary="Check status of a submitted complaint",
)
async def check_complaint_status(
    complaint_number: str,
    service: VictimComplaintService = Depends(get_victim_complaint_service),
) -> dict[str, Any]:
    """
    Allows victims to check the basic status of their submitted complaint
    using their tracking ID.
    """
    result = await service.get_complaint_status(complaint_number)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "Complaint not found"),
        )
    return result


@router.get(
    "/public/list",
    summary="List all complaints submitted by a victim email address",
)
async def list_complaints_by_email(
    response: Response,
    email: str = Query(..., description="The victim's email address"),
    service: VictimComplaintService = Depends(get_victim_complaint_service),
) -> list[dict[str, Any]]:
    """
    Returns all VICTIM_COMPLAINT records submitted from the User Portal
    matching the given email address. Used to populate the 'My Complaints'
    history page on the User Portal.
    """
    response.headers["Cache-Control"] = "private, max-age=60"
    return await service.list_complaints_by_email(email)
