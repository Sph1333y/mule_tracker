"""
MuleTrace AI — Domain Models.

Contains the canonical TransactionEvent domain model representing immutable financial
transaction events across all banking channels (UPI, NEFT, IMPS, RTGS).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class TransactionEvent(BaseModel):
    """Canonical domain representation of a financial transaction event.

    Separates immutable transactional facts from derived risk metrics,
    features, graph properties, and ML scores.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    # ── Core Immutable Identifiers & Flow ───────────────────────────────
    transaction_id: str = Field(
        ...,
        min_length=1,
        description="Canonical unique transaction reference / UTR / identifier",
    )
    timestamp: datetime = Field(
        ...,
        description="Execution timestamp of the transaction event",
    )
    sender_account: str = Field(
        ...,
        min_length=1,
        description="Originating sender account number or identifier",
    )
    receiver_account: str = Field(
        ...,
        min_length=1,
        description="Receiving beneficiary account number or identifier",
    )
    amount: float = Field(
        ...,
        gt=0.0,
        description="Transaction monetary amount (must be positive)",
    )
    currency: str = Field(
        default="INR",
        max_length=5,
        description="ISO currency code (default: INR)",
    )
    channel: str = Field(
        default="UPI",
        description="Payment rail / channel (e.g. UPI, NEFT, IMPS, RTGS, CARD)",
    )

    # ── Institution & KYC Metadata ──────────────────────────────────────
    sender_bank: Optional[str] = Field(
        default=None,
        description="Originating bank or financial institution name",
    )
    receiver_bank: Optional[str] = Field(
        default=None,
        description="Beneficiary bank or financial institution name",
    )
    sender_name: Optional[str] = Field(
        default=None,
        description="Originating account holder / KYC name",
    )
    receiver_name: Optional[str] = Field(
        default=None,
        description="Beneficiary account holder / KYC name",
    )

    # ── Device & Network Telemetry ──────────────────────────────────────
    device_id: Optional[str] = Field(
        default=None,
        description="Originating device identifier or hardware fingerprint",
    )
    ip_address: Optional[str] = Field(
        default=None,
        description="Originating IP address string (IPv4/IPv6)",
    )
    wallet_id: Optional[str] = Field(
        default=None,
        description="Associated digital wallet identifier if applicable",
    )
    beneficiary_id: Optional[str] = Field(
        default=None,
        description="Pre-registered beneficiary profile identifier if applicable",
    )

    # ── Geospatial Context ──────────────────────────────────────────────
    location_city: Optional[str] = Field(
        default=None,
        description="Origination city location",
    )
    location_state: Optional[str] = Field(
        default=None,
        description="Origination state/province location",
    )
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Geographic latitude coordinate",
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Geographic longitude coordinate",
    )

    # ── Narration & Extension Payload ───────────────────────────────────
    narration: Optional[str] = Field(
        default=None,
        description="Transaction narrative, purpose description, or remarks",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Preserved raw source fields and non-domain extension attributes",
    )

    # ── Backward Compatibility Accessors ────────────────────────────────
    @property
    def txn_id(self) -> str:
        """Backward-compatibility property for dataset 'txn_id' alias."""
        return self.transaction_id

    @property
    def transaction_ref(self) -> str:
        """Backward-compatibility property for database/API 'transaction_ref' alias."""
        return self.transaction_id

    @property
    def trans_type(self) -> str:
        """Backward-compatibility property for dataset 'trans_type' alias."""
        return self.channel

    @property
    def device_fingerprint(self) -> Optional[str]:
        """Backward-compatibility property for database 'device_fingerprint' alias."""
        return self.device_id

    @property
    def ip_address_str(self) -> Optional[str]:
        """Backward-compatibility property for database 'ip_address_str' alias."""
        return self.ip_address

    def __repr__(self) -> str:
        return (
            f"<TransactionEvent(id={self.transaction_id}, "
            f"amount={self.amount} {self.currency}, "
            f"channel={self.channel}, "
            f"sender={self.sender_account} -> receiver={self.receiver_account})>"
        )
