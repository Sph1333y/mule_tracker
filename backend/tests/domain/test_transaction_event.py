"""
MuleTrace AI — TransactionEvent Domain Model Unit & Regression Tests.

Tests:
1. Valid transaction creation.
2. Required field validation.
3. Optional fields behavior.
4. Numeric amount handling (positive, int/float coercion, invalid amounts).
5. Timestamp parsing (ISO, space-separated, datetime instances).
6. Empty/null optional fields handling.
7. Invalid transaction ID handling.
8. Invalid amount constraint handling.
9. Mapping from legacy transaction dictionary.
10. Backward-compatibility properties (.txn_id, .transaction_ref, .trans_type, etc.).
11. Golden transaction test using real dataset record through existing Rule and ML engines.
12. Data preservation verification (zero unexplained data loss).
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.domain.models import TransactionEvent
from app.domain.transaction_mapper import TransactionMapper
from app.engines.rules.rule_engine import rule_engine
from app.engines.ml.xgboost_model import ml_engine


# -----------------------------------------------------------------------------
# 1. Valid Creation
# -----------------------------------------------------------------------------
def test_valid_transaction_creation():
    """Verify that TransactionEvent can be created with all standard fields."""
    now = datetime(2025, 7, 1, 10, 40, 36, tzinfo=timezone.utc)
    event = TransactionEvent(
        transaction_id="TXN-2025-001",
        timestamp=now,
        sender_account="SB00009199",
        receiver_account="SB41222178",
        amount=44532.52,
        currency="INR",
        channel="UPI",
        sender_bank="State Bank of India",
        receiver_bank="HDFC Bank",
        sender_name="Sakthi Prakash",
        receiver_name="Rakesh Agarwal",
        device_id="iPhone 14",
        ip_address="103.42.240.225",
        narration="Layered Transfer",
    )

    assert event.transaction_id == "TXN-2025-001"
    assert event.amount == 44532.52
    assert event.currency == "INR"
    assert event.channel == "UPI"
    assert event.sender_account == "SB00009199"
    assert event.receiver_account == "SB41222178"
    assert event.sender_bank == "State Bank of India"
    assert event.receiver_bank == "HDFC Bank"
    assert event.device_id == "iPhone 14"
    assert event.ip_address == "103.42.240.225"


# -----------------------------------------------------------------------------
# 2. Required Fields Validation
# -----------------------------------------------------------------------------
def test_required_field_validation():
    """Verify that omitting required fields raises ValidationError."""
    with pytest.raises(ValidationError):
        # Missing amount, sender_account, receiver_account
        TransactionEvent(
            transaction_id="TXN-001",
            timestamp=datetime.now(timezone.utc),
        )


# -----------------------------------------------------------------------------
# 3. Optional Fields Handling
# -----------------------------------------------------------------------------
def test_optional_fields():
    """Verify that optional fields default to None and metadata defaults to empty dict."""
    now = datetime.now(timezone.utc)
    event = TransactionEvent(
        transaction_id="TXN-OPT-001",
        timestamp=now,
        sender_account="ACC-001",
        receiver_account="ACC-002",
        amount=1000.0,
    )

    assert event.channel == "UPI"
    assert event.currency == "INR"
    assert event.sender_bank is None
    assert event.receiver_bank is None
    assert event.sender_name is None
    assert event.receiver_name is None
    assert event.device_id is None
    assert event.ip_address is None
    assert event.wallet_id is None
    assert event.beneficiary_id is None
    assert event.location_city is None
    assert event.latitude is None
    assert event.longitude is None
    assert event.narration is None
    assert event.metadata == {}


# -----------------------------------------------------------------------------
# 4. Numeric Amount Handling
# -----------------------------------------------------------------------------
def test_numeric_amount_handling():
    """Verify numeric amount conversions (int, float, string coercion)."""
    now = datetime.now(timezone.utc)

    # Int amount
    ev1 = TransactionMapper.from_dict({
        "transaction_id": "TXN-INT",
        "timestamp": now,
        "sender_account": "A1",
        "receiver_account": "A2",
        "amount": 5000,
    })
    assert ev1.amount == 5000.0
    assert isinstance(ev1.amount, float)

    # String amount
    ev2 = TransactionMapper.from_dict({
        "transaction_id": "TXN-STR",
        "timestamp": now,
        "sender_account": "A1",
        "receiver_account": "A2",
        "amount": "1234.56",
    })
    assert ev2.amount == 1234.56


# -----------------------------------------------------------------------------
# 5. Timestamp Parsing
# -----------------------------------------------------------------------------
def test_timestamp_parsing():
    """Verify ISO strings, space-separated datetime strings, and datetime objects."""
    # Datetime object
    dt = datetime(2025, 7, 1, 15, 20, 38)
    ev1 = TransactionMapper.from_dict({
        "txn_id": "T1", "timestamp": dt, "account_number": "A1", "receiver_account": "A2", "amount": 100,
    })
    assert ev1.timestamp == dt

    # Space-separated string (standard dataset format: 2025-07-01 15:20:38)
    ev2 = TransactionMapper.from_dict({
        "txn_id": "T2", "timestamp": "2025-07-01 15:20:38", "account_number": "A1", "receiver_account": "A2", "amount": 100,
    })
    assert ev2.timestamp.year == 2025
    assert ev2.timestamp.month == 7
    assert ev2.timestamp.day == 1
    assert ev2.timestamp.hour == 15

    # ISO string
    ev3 = TransactionMapper.from_dict({
        "txn_id": "T3", "timestamp": "2025-07-01T15:20:38Z", "account_number": "A1", "receiver_account": "A2", "amount": 100,
    })
    assert ev3.timestamp.year == 2025


# -----------------------------------------------------------------------------
# 6. Empty / Null Optional Fields
# -----------------------------------------------------------------------------
def test_empty_or_null_optional_fields():
    """Verify that null/empty optional values do not break mapping."""
    ev = TransactionMapper.from_dict({
        "transaction_id": "TXN-NULL",
        "timestamp": "2025-07-01 10:00:00",
        "sender_account": "A1",
        "receiver_account": "A2",
        "amount": 500,
        "sender_bank": None,
        "receiver_bank": "",
        "latitude": "",
        "longitude": None,
        "narration": None,
    })
    assert ev.sender_bank is None
    assert ev.latitude is None
    assert ev.longitude is None
    assert ev.narration is None


# -----------------------------------------------------------------------------
# 7. Invalid Transaction ID
# -----------------------------------------------------------------------------
def test_invalid_transaction_id():
    """Verify that missing or empty transaction identifier raises an error."""
    with pytest.raises(ValueError, match="Missing required transaction identifier"):
        TransactionMapper.from_dict({
            "timestamp": "2025-07-01 10:00:00",
            "sender_account": "A1",
            "receiver_account": "A2",
            "amount": 500,
        })


# -----------------------------------------------------------------------------
# 8. Invalid Amount Constraint
# -----------------------------------------------------------------------------
def test_invalid_amount_constraint():
    """Verify that zero or negative amount raises ValueError."""
    # Zero amount
    with pytest.raises(ValueError, match="strictly positive"):
        TransactionMapper.from_dict({
            "transaction_id": "TXN-0",
            "timestamp": "2025-07-01 10:00:00",
            "sender_account": "A1",
            "receiver_account": "A2",
            "amount": 0,
        })

    # Negative amount
    with pytest.raises(ValueError, match="strictly positive"):
        TransactionMapper.from_dict({
            "transaction_id": "TXN-NEG",
            "timestamp": "2025-07-01 10:00:00",
            "sender_account": "A1",
            "receiver_account": "A2",
            "amount": -500.0,
        })


# -----------------------------------------------------------------------------
# 9. Mapping from Legacy Dict
# -----------------------------------------------------------------------------
def test_mapping_from_legacy_dict():
    """Verify mapping from standard legacy transaction dictionary formats."""
    legacy = {
        "transaction_ref": "UTR2025MULECHAIN001",
        "channel": "UPI",
        "amount": 250000.0,
        "currency": "INR",
        "timestamp": "2025-07-01 12:00:00",
        "location_city": "Mumbai",
        "location_state": "Maharashtra",
        "sender_account_number": "ACC-MUM-01",
        "receiver_account_number": "ACC-MUM-02",
        "narrative": "Mule Chain Step 1",
    }
    event = TransactionMapper.from_dict(legacy)
    assert event.transaction_id == "UTR2025MULECHAIN001"
    assert event.channel == "UPI"
    assert event.amount == 250000.0
    assert event.sender_account == "ACC-MUM-01"
    assert event.receiver_account == "ACC-MUM-02"
    assert event.location_city == "Mumbai"
    assert event.narration == "Mule Chain Step 1"


# -----------------------------------------------------------------------------
# 10. Backward Compatibility Properties
# -----------------------------------------------------------------------------
def test_compatibility_properties():
    """Verify that read properties alias to expected names."""
    event = TransactionEvent(
        transaction_id="TXN-COMPAT-99",
        timestamp=datetime(2025, 7, 1, 12, 0, 0),
        sender_account="A1",
        receiver_account="A2",
        amount=100.0,
        channel="NEFT",
        device_id="DEV-1234",
        ip_address="192.168.1.1",
    )
    assert event.txn_id == "TXN-COMPAT-99"
    assert event.transaction_ref == "TXN-COMPAT-99"
    assert event.trans_type == "NEFT"
    assert event.device_fingerprint == "DEV-1234"
    assert event.ip_address_str == "192.168.1.1"


# -----------------------------------------------------------------------------
# 11. Golden Transaction Test (Real Dataset Sample -> Pipeline Compatibility)
# -----------------------------------------------------------------------------
def test_golden_transaction_dataset_record():
    """Test real transaction from transactions_data_set.csv through canonical mapping and legacy engines."""
    # Record from line 4 of transactions_data_set.csv (Sakthi Prakash, Mule Chain)
    golden_record = {
        "timestamp": "2025-07-01 10:40:36",
        "txn_id": "SB3000111",
        "name": "Sakthi Prakash",
        "account_number": "SB00009199",
        "account_type": "Current",
        "mobile_number": "9797801251",
        "pincode": "600001",
        "narration": "Layered Transfer",
        "trans_type": "UPI",
        "amount": 44532.52,
        "ip_address": "103.42.240.225",
        "device": "iPhone 14",
        "receiver_account": "SB41222178",
        "is_fraud": 1,
        "fraud_type": "Mule Chain",
        "account_age_days": 7,
        "receiver_name": "Rakesh Agarwal",
        "receiver_pincode": "380001",
        "velocity_l6h": 13,
        "churn_rate": 0.522,
        "ip_account_density": 9,
        "amount_deviation_ratio": 1.41,
        "daily_limit_fraction": 0.859,
        "user_risk_score": 60.9,
        "device_trust_score": 50,
        "is_rooted_or_emulator": 0,
        "device_risk_score": 89.6,
        "merchant_chargeback_rate": 0.358,
        "merchant_risk_score": 93.6,
        "is_vpn_or_proxy": 1,
        "network_risk_score": 84.7,
        "risk_score": 90.9,
        "bank_name": "State Bank of India",
        "receiver_bank": "State Bank of India",
    }

    # Step A: Convert to Canonical TransactionEvent
    event = TransactionMapper.from_dict(golden_record)

    assert event.transaction_id == "SB3000111"
    assert event.sender_account == "SB00009199"
    assert event.receiver_account == "SB41222178"
    assert event.amount == 44532.52
    assert event.channel == "UPI"
    assert event.sender_bank == "State Bank of India"
    assert event.sender_name == "Sakthi Prakash"
    assert event.receiver_name == "Rakesh Agarwal"
    assert event.device_id == "iPhone 14"
    assert event.ip_address == "103.42.240.225"
    assert event.narration == "Layered Transfer"

    # Verify that non-canonical dataset features are safely preserved in metadata
    assert event.metadata["velocity_l6h"] == 13
    assert event.metadata["is_fraud"] == 1
    assert event.metadata["fraud_type"] == "Mule Chain"
    assert event.metadata["account_age_days"] == 7
    assert event.metadata["risk_score"] == 90.9

    # Step B: Export back to legacy format
    legacy_dict = TransactionMapper.to_legacy_dict(event)

    # Step C: Evaluate legacy dict in Rule Engine
    rule_res = rule_engine.evaluate(
        transaction=legacy_dict,
        sender_account={},
        recent_transactions=[],
        linked_devices_count=1,
        linked_ips_count=1,
    )
    assert rule_res is not None
    assert isinstance(rule_res.total_risk_score_delta, int)

    # Step D: Evaluate legacy dict in ML Engine
    ml_res = ml_engine.predict_transaction_risk(legacy_dict)
    assert ml_res is not None
    assert 0 <= ml_res.predicted_risk_score <= 100
    assert 0.0 <= ml_res.fraud_probability <= 1.0


# -----------------------------------------------------------------------------
# 12. Data Preservation Verification
# -----------------------------------------------------------------------------
def test_data_preservation_verification():
    """Verify that NO field from the source dictionary is lost after roundtrip."""
    raw_source = {
        "txn_id": "TXN-PRESERVE-001",
        "timestamp": "2025-07-01 10:40:36",
        "account_number": "ACC-111",
        "receiver_account": "ACC-222",
        "amount": 49000.0,
        "trans_type": "NEFT",
        "bank_name": "State Bank of India",
        "receiver_bank": "HDFC Bank",
        "name": "John Doe",
        "receiver_name": "Jane Smith",
        "device": "Pixel 8",
        "ip_address": "192.168.1.50",
        "custom_tag": "vip_flagged",
        "analyst_id": "AN-99",
        "raw_score_xyz": 42.5,
    }

    event = TransactionMapper.from_dict(raw_source)
    legacy = TransactionMapper.to_legacy_dict(event)

    # Verify custom metadata is preserved
    assert legacy["custom_tag"] == "vip_flagged"
    assert legacy["analyst_id"] == "AN-99"
    assert legacy["raw_score_xyz"] == 42.5

    # Verify canonical data is preserved
    assert legacy["transaction_id"] == "TXN-PRESERVE-001"
    assert legacy["txn_id"] == "TXN-PRESERVE-001"
    assert legacy["transaction_ref"] == "TXN-PRESERVE-001"
    assert legacy["amount"] == 49000.0
    assert legacy["channel"] == "NEFT"
    assert legacy["trans_type"] == "NEFT"
    assert legacy["sender_account"] == "ACC-111"
    assert legacy["receiver_account"] == "ACC-222"
