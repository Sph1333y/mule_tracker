"""
MuleTrace AI — Transaction Mapper.

Factory and conversion layer mapping raw dictionaries, dataset rows,
and existing ORM/Pydantic models to and from the canonical TransactionEvent model.
Deterministic, side-effect free, and preserves all raw source attributes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel

from app.domain.models import TransactionEvent


class TransactionMapper:
    """Deterministic mapper converting between legacy transaction formats and TransactionEvent."""

    # Set of keys directly ingested into canonical fields (not relegated to metadata)
    CANONICAL_SOURCE_KEYS: set[str] = {
        "transaction_id",
        "transaction_ref",
        "txn_id",
        "tx_ref",
        "id",
        "timestamp",
        "created_at",
        "date",
        "sender_account",
        "sender_account_number",
        "account_number",
        "sender_account_id",
        "receiver_account",
        "receiver_account_number",
        "receiver_account_id",
        "amount",
        "currency",
        "channel",
        "trans_type",
        "sender_bank",
        "bank_name",
        "receiver_bank",
        "sender_name",
        "name",
        "receiver_name",
        "device_id",
        "device_fingerprint",
        "device",
        "ip_address",
        "ip_address_str",
        "wallet_id",
        "beneficiary_id",
        "location_city",
        "city",
        "location_state",
        "state",
        "latitude",
        "longitude",
        "narration",
        "narrative",
        "description",
        "metadata",
    }

    @staticmethod
    def _parse_timestamp(raw_val: Any) -> datetime:
        """Parse various timestamp representations into a datetime object."""
        if isinstance(raw_val, datetime):
            return raw_val
        if isinstance(raw_val, str):
            clean_str = raw_val.strip()
            # Fast-path ISO format
            try:
                return datetime.fromisoformat(clean_str)
            except ValueError:
                pass
            # Common dataset format: "2025-07-01 15:20:38"
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S"):
                try:
                    return datetime.strptime(clean_str, fmt)
                except ValueError:
                    continue
        # Fallback to current time if unparseable or absent
        return datetime.utcnow()

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> TransactionEvent:
        """Convert a raw dictionary (e.g. from CSV, API body, or message) into TransactionEvent.

        Deterministic: preserves all unmapped fields in the metadata dictionary.
        """
        # Resolve Transaction Identifier
        tx_id = (
            raw.get("transaction_id")
            or raw.get("transaction_ref")
            or raw.get("txn_id")
            or raw.get("tx_ref")
            or (str(raw.get("id")) if raw.get("id") is not None else None)
        )
        if not tx_id:
            msg = "Missing required transaction identifier (transaction_id/transaction_ref/txn_id)"
            raise ValueError(msg)

        # Resolve Execution Timestamp
        raw_ts = raw.get("timestamp") or raw.get("created_at") or raw.get("date")
        timestamp = cls._parse_timestamp(raw_ts)

        # Resolve Accounts
        sender_acc = (
            raw.get("sender_account")
            or raw.get("sender_account_number")
            or raw.get("account_number")
            or (str(raw.get("sender_account_id")) if raw.get("sender_account_id") else None)
        )
        if not sender_acc:
            msg = "Missing required sender account identifier"
            raise ValueError(msg)

        receiver_acc = (
            raw.get("receiver_account")
            or raw.get("receiver_account_number")
            or (str(raw.get("receiver_account_id")) if raw.get("receiver_account_id") else None)
        )
        if not receiver_acc:
            msg = "Missing required receiver account identifier"
            raise ValueError(msg)

        # Resolve Amount
        try:
            amount = float(raw.get("amount", 0.0))
        except (ValueError, TypeError) as e:
            msg = f"Invalid transaction amount: {raw.get('amount')}"
            raise ValueError(msg) from e

        if amount <= 0.0:
            msg = f"Transaction amount must be strictly positive, got: {amount}"
            raise ValueError(msg)

        # Resolve Currency & Channel
        currency = str(raw.get("currency") or "INR")
        channel = str(raw.get("channel") or raw.get("trans_type") or "UPI")

        # Resolve Optional Attributes
        sender_bank = raw.get("sender_bank") or raw.get("bank_name")
        receiver_bank = raw.get("receiver_bank")
        sender_name = raw.get("sender_name") or raw.get("name")
        receiver_name = raw.get("receiver_name")

        device_id = raw.get("device_id") or raw.get("device_fingerprint") or raw.get("device")
        ip_address = raw.get("ip_address") or raw.get("ip_address_str")
        wallet_id = raw.get("wallet_id")
        beneficiary_id = raw.get("beneficiary_id")

        location_city = raw.get("location_city") or raw.get("city")
        location_state = raw.get("location_state") or raw.get("state")

        def _to_float_opt(val: Any) -> Optional[float]:
            if val is None or str(val).strip() == "":
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        latitude = _to_float_opt(raw.get("latitude"))
        longitude = _to_float_opt(raw.get("longitude"))

        narration = raw.get("narration") or raw.get("narrative") or raw.get("description")

        # Preserve all extra fields in metadata
        metadata = dict(raw.get("metadata", {})) if isinstance(raw.get("metadata"), dict) else {}
        for key, val in raw.items():
            if key not in cls.CANONICAL_SOURCE_KEYS and key not in metadata:
                metadata[key] = val

        return TransactionEvent(
            transaction_id=str(tx_id),
            timestamp=timestamp,
            sender_account=str(sender_acc),
            receiver_account=str(receiver_acc),
            amount=amount,
            currency=currency,
            channel=channel,
            sender_bank=str(sender_bank) if sender_bank is not None else None,
            receiver_bank=str(receiver_bank) if receiver_bank is not None else None,
            sender_name=str(sender_name) if sender_name is not None else None,
            receiver_name=str(receiver_name) if receiver_name is not None else None,
            device_id=str(device_id) if device_id is not None else None,
            ip_address=str(ip_address) if ip_address is not None else None,
            wallet_id=str(wallet_id) if wallet_id is not None else None,
            beneficiary_id=str(beneficiary_id) if beneficiary_id is not None else None,
            location_city=str(location_city) if location_city is not None else None,
            location_state=str(location_state) if location_state is not None else None,
            latitude=latitude,
            longitude=longitude,
            narration=str(narration) if narration is not None else None,
            metadata=metadata,
        )

    @classmethod
    def from_existing_model(cls, model: Any) -> TransactionEvent:
        """Convert a Pydantic or ORM model instance into TransactionEvent."""
        if isinstance(model, BaseModel):
            return cls.from_dict(model.model_dump())
        if hasattr(model, "__dict__"):
            d = {k: v for k, v in model.__dict__.items() if not k.startswith("_")}
            return cls.from_dict(d)
        msg = f"Unsupported model type: {type(model)}"
        raise TypeError(msg)

    @classmethod
    def to_legacy_dict(cls, event: TransactionEvent) -> dict[str, Any]:
        """Convert TransactionEvent back to a legacy dictionary with aliased keys.

        Guarantees that downstream legacy components (rules, ML, Neo4j) receive
        the exact dictionary keys they expect without data loss.
        """
        legacy = {
            # Canonical & Aliases for Identifier
            "transaction_id": event.transaction_id,
            "transaction_ref": event.transaction_id,
            "txn_id": event.transaction_id,
            # Timestamp
            "timestamp": event.timestamp,
            # Accounts
            "sender_account": event.sender_account,
            "sender_account_number": event.sender_account,
            "receiver_account": event.receiver_account,
            "receiver_account_number": event.receiver_account,
            # Flow details
            "amount": event.amount,
            "currency": event.currency,
            "channel": event.channel,
            "trans_type": event.channel,
            # Institution
            "sender_bank": event.sender_bank,
            "bank_name": event.sender_bank,
            "receiver_bank": event.receiver_bank,
            "sender_name": event.sender_name,
            "name": event.sender_name,
            "receiver_name": event.receiver_name,
            # Telemetry
            "device_id": event.device_id,
            "device_fingerprint": event.device_id,
            "device": event.device_id,
            "ip_address": event.ip_address,
            "ip_address_str": event.ip_address,
            "wallet_id": event.wallet_id,
            "beneficiary_id": event.beneficiary_id,
            # Geo
            "location_city": event.location_city,
            "city": event.location_city,
            "location_state": event.location_state,
            "state": event.location_state,
            "latitude": event.latitude,
            "longitude": event.longitude,
            # Narration
            "narration": event.narration,
            "narrative": event.narration,
            "description": event.narration,
        }
        # Unpack preserved metadata
        if event.metadata:
            for k, v in event.metadata.items():
                if k not in legacy:
                    legacy[k] = v

        return legacy
