"""
MuleTrace AI — Deterministic Investigation Copilot Package.

Public interface and exports for Milestone 12 (Deterministic Investigation Copilot).
"""

from __future__ import annotations

from app.engines.ai.copilot import DeterministicInvestigationCopilot
from app.engines.ai.models import (
    ActionPriority,
    ActionType,
    InvestigationContext,
    InvestigationCopilotResponse,
    KeyFinding,
    SuggestedAction,
)
from app.engines.ai.templates import (
    extract_key_findings,
    generate_audit_limitations,
    generate_follow_up_questions,
    generate_investigation_actions,
    render_investigation_summary,
    render_risk_summary,
)

__all__ = [
    "DeterministicInvestigationCopilot",
    "InvestigationContext",
    "InvestigationCopilotResponse",
    "KeyFinding",
    "SuggestedAction",
    "ActionPriority",
    "ActionType",
    "extract_key_findings",
    "generate_audit_limitations",
    "generate_follow_up_questions",
    "generate_investigation_actions",
    "render_investigation_summary",
    "render_risk_summary",
]
