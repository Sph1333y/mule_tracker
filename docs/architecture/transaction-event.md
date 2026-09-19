# MuleTrace AI — Canonical TransactionEvent Architecture Specification

**Milestone:** 1 — Canonical Transaction Layer  
**Status:** Adopted / Active  
**Scope Notice:**  
> *"Milestone 1 establishes the canonical transaction representation. It does not migrate all existing engines to TransactionEvent."*

---

## 1. Executive Summary & Purpose

In the initial MuleTrace AI codebase, transaction payloads were passed across system components as unvalidated Python dictionaries (`dict[str, Any]`), varying Pydantic schemas (`TransactionBase`, `TransactionCreate`, `TransactionRead`), and raw dataset CSV rows. Over time, subtle naming divergences emerged across layers:

- **Identifiers:** `txn_id` (dataset / ML scripts) vs. `transaction_ref` (PostgreSQL / Alembic / API schemas) vs. `transaction_id` (Victim Portal / REST contract).
- **Payment Rails:** `trans_type` (dataset) vs. `channel` (PostgreSQL / API schemas).
- **Device Telemetry:** `device` (dataset) vs. `device_fingerprint` (PostgreSQL) vs. `device_id`.
- **IP Address:** `ip_address` (dataset) vs. `ip_address_str` (PostgreSQL).
- **Account Identification:** `account_number` / `receiver_account` (dataset) vs. `sender_account_id` / `receiver_account_id` (PostgreSQL UUIDs) vs. `sender_account_number` / `receiver_account_number` (Neo4j GraphBuilder).

`TransactionEvent` establishes a single, canonical, typed domain representation that decouples business logic from external ingestion formats, database models, and cloud infrastructure.

---

## 2. The Architectural Boundary: Canonical Facts vs. Derived Features

A critical architectural principle enforced in Milestone 1 is that **immutable transactional facts** must never be conflated with **derived features, model predictions, or risk scores**.

```
Raw Transaction Stream (CSV, REST, Switch)
                  │
                  ▼
   ┌──────────────────────────────┐
   │       TransactionEvent       │  <── Immutable Transactional Facts
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │     Feature Engineering      │  <── Behavioral, Temporal & Network Analytics
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │   Rules, Graph, ML Models    │  <── Downstream Detection Engines
   └──────────────────────────────┘
```

### A. Canonical Immutable Facts (`TransactionEvent`)
Represents the ground-truth financial event that occurred at an exact point in time:
- Transaction identity (`transaction_id`)
- Temporal timestamp (`timestamp`)
- Originating and destination accounts (`sender_account`, `receiver_account`)
- Monetary flow (`amount`, `currency`)
- Payment rail (`channel`)
- Institution information (`sender_bank`, `receiver_bank`)
- Counterparty identities (`sender_name`, `receiver_name`)
- Originating hardware & network telemetry (`device_id`, `ip_address`)
- Geospatial coordinates & city context (`location_city`, `location_state`, `latitude`, `longitude`)
- Remittance purpose (`narration`)

### B. Intentionally Excluded Derived Features
The following 18 fields from `transactions_data_set.csv` are **intentionally excluded** from the core `TransactionEvent` schema because they are calculated after the event occurs or represent model outputs:
1. `is_fraud` — Ground-truth classification label.
2. `fraud_type` — Ground-truth fraud typology categorization.
3. `risk_score` — Composite risk score (0-100).
4. `velocity_l6h` — Trailing 6-hour transaction velocity (calculated by temporal engines).
5. `churn_rate` — Turnover ratio (calculated by account analytics).
6. `ip_account_density` — Number of distinct accounts sharing an IP (calculated by relationship engines).
7. `amount_deviation_ratio` — Historical standard deviation multiple (calculated by feature engineering).
8. `daily_limit_fraction` — Fraction of daily regulatory threshold consumed.
9. `user_risk_score` — Behavioral risk profile baseline.
10. `device_trust_score` — Hardware integrity metric.
11. `is_rooted_or_emulator` — Security telemetry classification.
12. `device_risk_score` — Device-level risk sub-score.
13. `merchant_chargeback_rate` — Counterparty dispute history.
14. `merchant_risk_score` — Merchant category risk weight.
15. `is_vpn_or_proxy` — Network proxy classifier.
16. `network_risk_score` — Network anomaly score.
17. `account_age_days` — Account profile age feature.
18. `pincode` / `receiver_pincode` — Preserved in `metadata` rather than polluting core geo fields.

*Preservation Guarantee:* All excluded fields present in incoming payloads are preserved losslessly inside `TransactionEvent.metadata` via `TransactionMapper.from_dict()`.

---

## 3. Canonical Field Specifications

| Field Name | Type | Constraint | Description |
|:---|:---|:---|:---|
| `transaction_id` | `str` | Required, non-empty | Canonical unique reference (UTR / RRN) |
| `timestamp` | `datetime` | Required | Execution timestamp (timezone-aware supported) |
| `sender_account` | `str` | Required, non-empty | Remitter account number or identifier |
| `receiver_account` | `str` | Required, non-empty | Beneficiary account number or identifier |
| `amount` | `float` | Required, strictly $>0.0$ | Monetary value of the transfer |
| `currency` | `str` | Default `"INR"`, max 5 chars | ISO currency code |
| `channel` | `str` | Default `"UPI"` | Payment rail (`UPI`, `NEFT`, `IMPS`, `RTGS`, `CARD`) |
| `sender_bank` | `Optional[str]` | Optional, default `None` | Remitter bank name (e.g. State Bank of India) |
| `receiver_bank` | `Optional[str]` | Optional, default `None` | Beneficiary bank name (e.g. HDFC Bank) |
| `sender_name` | `Optional[str]` | Optional, default `None` | Remitter KYC customer name |
| `receiver_name` | `Optional[str]` | Optional, default `None` | Beneficiary KYC customer name |
| `device_id` | `Optional[str]` | Optional, default `None` | Hardware/browser fingerprint |
| `ip_address` | `Optional[str]` | Optional, default `None` | Originating IP address string |
| `wallet_id` | `Optional[str]` | Optional, default `None` | Digital wallet identifier |
| `beneficiary_id` | `Optional[str]` | Optional, default `None` | Registered beneficiary profile ID |
| `location_city` | `Optional[str]` | Optional, default `None` | Originating city name |
| `location_state` | `Optional[str]` | Optional, default `None` | Originating state name |
| `latitude` | `Optional[float]` | $-90.0 \le \text{lat} \le 90.0$ | Geographic latitude |
| `longitude` | `Optional[float]` | $-180.0 \le \text{lon} \le 180.0$ | Geographic longitude |
| `narration` | `Optional[str]` | Optional, default `None` | Remittance remarks or purpose |
| `metadata` | `dict[str, Any]` | Default `{}` | Lossless storage of non-domain extension fields |

---

## 4. Field Aliases & Backward Compatibility

To guarantee that legacy components can interact with `TransactionEvent` without code breaks, the class provides read properties:

| Compatibility Property | Canonical Field Mapped To | Original Legacy Source |
|:---|:---|:---|
| `event.txn_id` | `event.transaction_id` | `transactions_data_set.csv`, ML scripts |
| `event.transaction_ref` | `event.transaction_id` | SQLAlchemy `Transaction`, Alembic, API |
| `event.trans_type` | `event.channel` | `transactions_data_set.csv` |
| `event.device_fingerprint`| `event.device_id` | SQLAlchemy `Transaction` |
| `event.ip_address_str` | `event.ip_address` | SQLAlchemy `Transaction` |

---

## 5. Bidirectional Mapping & Factory Layer (`TransactionMapper`)

The `TransactionMapper` class (`backend/app/domain/transaction_mapper.py`) provides deterministic, side-effect-free conversion:

```
                  ┌─────────────────────────────────────────┐
                  │    Raw Source Payload / Dict / Model    │
                  └────────────────────┬────────────────────┘
                                       │
                                       │ TransactionMapper.from_dict(...)
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │       Canonical TransactionEvent        │
                  └────────────────────┬────────────────────┘
                                       │
                                       │ TransactionMapper.to_legacy_dict(...)
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │  Legacy Dict (All original keys intact) │
                  └─────────────────────────────────────────┘
```

1. **`from_dict(raw: dict[str, Any]) -> TransactionEvent`**
   - Automatically inspects all known identifier keys (`transaction_id`, `transaction_ref`, `txn_id`, `tx_ref`, `id`).
   - Parses diverse timestamp formats (ISO-8601, `%Y-%m-%d %H:%M:%S`, datetime instances).
   - Validates that amount is strictly positive.
   - Preserves all unmapped source keys losslessly in `.metadata`.

2. **`from_existing_model(model: Any) -> TransactionEvent`**
   - Ingests Pydantic schemas (`TransactionBase`, `TransactionCreate`, `TransactionRead`) via `model.model_dump()`.
   - Ingests SQLAlchemy ORM models via attribute extraction.

3. **`to_legacy_dict(event: TransactionEvent) -> dict[str, Any]`**
   - Re-emits both canonical and aliased keys simultaneously (`transaction_id`, `transaction_ref`, `txn_id`, `channel`, `trans_type`, `device`, `device_fingerprint`, etc.).
   - Unpacks all preserved `metadata` entries back into the dictionary.
   - Guarantees 100% roundtrip compatibility with legacy Rule and ML engines.

---

## 6. Real Example Transaction

### Raw CSV Row (Source: `data_set/transactions_data_set.csv` Row 4):
```json
{
  "timestamp": "2025-07-01 10:40:36",
  "txn_id": "SB3000111",
  "name": "Sakthi Prakash",
  "account_number": "SB00009199",
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
  "velocity_l6h": 13,
  "churn_rate": 0.522,
  "amount_deviation_ratio": 1.41,
  "risk_score": 90.9,
  "bank_name": "State Bank of India",
  "receiver_bank": "State Bank of India"
}
```

### Canonical `TransactionEvent` Representation:
```json
{
  "transaction_id": "SB3000111",
  "timestamp": "2025-07-01T10:40:36",
  "sender_account": "SB00009199",
  "receiver_account": "SB41222178",
  "amount": 44532.52,
  "currency": "INR",
  "channel": "UPI",
  "sender_bank": "State Bank of India",
  "receiver_bank": "State Bank of India",
  "sender_name": "Sakthi Prakash",
  "receiver_name": "Rakesh Agarwal",
  "device_id": "iPhone 14",
  "ip_address": "103.42.240.225",
  "narration": "Layered Transfer",
  "metadata": {
    "is_fraud": 1,
    "fraud_type": "Mule Chain",
    "account_age_days": 7,
    "velocity_l6h": 13,
    "churn_rate": 0.522,
    "amount_deviation_ratio": 1.41,
    "risk_score": 90.9
  }
}
```

---

## 7. Migration Strategy for Subsequent Milestones

- **Milestone 2 (Repository Interfaces):** `GraphRepository` and `TransactionRepository` interfaces will take `TransactionEvent` as their primary method arguments.
- **Milestone 3 (NetworkX Graph Adapter):** Ingests `TransactionEvent` to build heterogeneous node-link relationships (`Account`, `Device`, `IP`, `Customer`).
- **Milestone 4 (14 Modular Rules):** Each `BaseRule.evaluate(event: TransactionEvent, context)` receives the canonical event directly.
- **Milestone 5 (Temporal Engine):** Aggregates streams of `TransactionEvent` across configurable time windows (1m, 5m, 15m, 1h, 24h).
