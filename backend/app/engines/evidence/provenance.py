"""
MuleTrace AI — Evidence Provenance & Identification.

Provides deterministic evidence ID hashing, source reference normalization,
and provenance validation routines using SHA-256.

Architectural Boundary:
- Strictly deterministic: uses hashlib.sha256 (never Python's process-randomized hash()).
- Cloud-agnostic (pure Python standard library).
"""

from __future__ import annotations

import hashlib
from typing import Sequence

from app.engines.evidence.models import EvidenceCategory, EvidenceSource


def generate_evidence_id(
    source: EvidenceSource,
    source_reference: str,
    category: EvidenceCategory,
    account_ids: Sequence[str] = (),
    transaction_ids: Sequence[str] = (),
) -> str:
    """Generate a stable, deterministic evidence identifier using SHA-256.

    The ID incorporates source, reference, category, and sorted entity references
    to ensure identical facts across different runs always receive the exact same ID.

    Format:
        EVD-{SOURCE}-{REF_SLUG}-{SHA256[:12]}
    """
    sorted_accounts = ",".join(sorted(account_ids))
    sorted_txns = ",".join(sorted(transaction_ids))
    ref_slug = source_reference.replace(":", "-").replace("_", "-").upper()[:16]

    raw_payload = f"{source.value}:{source_reference}:{category.value}:{sorted_accounts}:{sorted_txns}"
    digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()[:12]

    return f"EVD-{source.value}-{ref_slug}-{digest}"


def generate_case_id(
    transaction_id: str | None = None,
    subject_id: str | None = None,
) -> str:
    """Generate a deterministic case identifier if none is provided.

    Format:
        CASE-{IDENTIFIER_SLUG} or CASE-SHA256[:10]
    """
    if transaction_id:
        clean_tx = transaction_id.replace(" ", "_")[:32]
        return f"CASE-{clean_tx}"
    if subject_id:
        clean_sub = subject_id.replace(" ", "_")[:32]
        return f"CASE-{clean_sub}"

    fallback_digest = hashlib.sha256(b"anonymous_case").hexdigest()[:10]
    return f"CASE-ANON-{fallback_digest}"


def validate_provenance(
    source: EvidenceSource,
    source_reference: str,
) -> bool:
    """Validate that an evidence item has a valid, non-empty source and reference."""
    if not isinstance(source, EvidenceSource):
        return False
    if not source_reference or not isinstance(source_reference, str) or len(source_reference.strip()) == 0:
        return False
    return True
