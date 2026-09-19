"""
MuleTrace AI — Report Repository.

Handles database operations for compliance Report entities.
"""

from __future__ import annotations


import uuid
from typing import Optional, Sequence
from sqlalchemy import func, select, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

from app.models.report import Report


class ReportRepository:
    """Repository managing Report database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, report_id: uuid.UUID) -> Optional[Report]:
        """Fetch report by UUID."""
        stmt = select(Report).where(Report.id == report_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_number(self, report_number: str) -> Optional[Report]:
        """Fetch report by report reference number."""
        stmt = select(Report).where(Report.report_number == report_number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 20,
        report_type: Optional[str] = None,
        case_id: Optional[uuid.UUID] = None,
    ) -> Sequence[Report]:
        """Fetch paginated reports."""
        stmt = select(Report)

        if report_type:
            stmt = stmt.where(Report.report_type == report_type)
        if case_id:
            stmt = stmt.where(Report.case_id == case_id)

        stmt = stmt.offset(skip).limit(limit).order_by(Report.generated_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        report_type: Optional[str] = None,
        case_id: Optional[uuid.UUID] = None,
    ) -> int:
        """Count total reports."""
        stmt = select(func.count(Report.id))

        if report_type:
            stmt = stmt.where(Report.report_type == report_type)
        if case_id:
            stmt = stmt.where(Report.case_id == case_id)

        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def create(self, report: Report) -> Report:
        """Persist a new report."""
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_victim_complaints_by_email(self, email: str) -> Sequence[Report]:
        """Fetch all VICTIM_COMPLAINT reports for a given victim email.

        Filters by report_type and searches summary_text (stored JSON)
        for the victim_email field matching the provided address.
        """
        stmt = (
            select(Report)
            .where(Report.report_type == "VICTIM_COMPLAINT")
            .where(Report.summary_text.like(f'%"{email}"%'))
            .where(
                cast(Report.summary_text, JSONB)["victim_email"].astext == email
            )
            .order_by(Report.generated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
