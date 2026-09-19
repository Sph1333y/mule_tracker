# MuleTrace AI — Modular 14-Rule Fraud Detection Engine

> **Milestone 5 Architecture & Behavioral Parity Specification**
>
> "M5 modularizes the existing 14-rule engine without intentionally changing its detection behavior."

---

## 1. Milestone Objective

The objective of **Milestone 5 (M5)** is to safely refactor the forensic fraud detection implementation into a modular, independently testable, decoupled rule architecture without altering the system's fraud-detection behavior, thresholds, severity ratings, or API contracts.

Prior to M5, rule evaluation was executed inside a monolithic class (`RuleEngine`) where rule checks were coupled as internal methods. M5 extracts every rule into an independent module adhering to a standard `BaseRule` contract, registered deterministically in `ModularRuleEngine`, while maintaining `RuleEngine` as a 100% backward-compatible facade.

---

## 2. Existing vs. Modular Rule Architecture

### 2.1 Before M5 (Monolithic)
```
API / TransactionService
          │
          ▼
   RuleEngine (monolithic)
   ├── _check_high_velocity (R001)
   ├── _check_fan_in        (R002)
   ├── _check_fan_out       (R003)
   ├── _check_mule_chain    (R004)
   ├── _check_smurfing      (R005)
   └── _check_shared_device (R006)
          │
          ▼
   EvaluationResult
```

### 2.2 After M5 (Modular Architecture with Compatibility Facade)
```
                 Existing Application (Next.js / FastAPI / TransactionService)
                                        │
                                        ▼
                             Existing RuleEngine
                                        │
                             (Compatibility Boundary)
                                        │
                                        ▼
                                ModularRuleEngine
                                        │
             ┌───────┬───────┬───────┬──┴────┬───────┬───────┬───────┐
             │       │       │       │       │       │       │       │
             ▼       ▼       ▼       ▼       ▼       ▼       ▼       ▼
           R001    R002    R003    R004    R005    R006    ...     R014
             │       │       │       │       │       │       │       │
             └───────┴───────┴───────┼───────┴───────┴───────┴───────┘
                                     │
                                     ▼
                              RuleMatchResult
                                     │
                                     ▼
                              EvaluationResult
                                     │
                                     ▼
                           Existing Alert Flow
```

---

## 3. The 14 Forensic Rules Inventory

| Rule ID | Canonical Rule Name | Pattern Name | Inputs Evaluated | Threshold Parameters | Score Contribution | Severity |
|:---:|:---|:---|:---|:---|:---:|:---:|
| **R001** | High Velocity Transactions | High Velocity | `recent_transactions` timestamps | >20 txns in 1 hour | +25 | HIGH |
| **R002** | Fan-In Aggregation | Fan In | `receiver_account_id`, `recent_transactions` | ≥10 unique senders in 24h | +30 | HIGH |
| **R003** | Fan-Out Dispersion | Fan Out | `sender_account_id`, `recent_transactions` | ≥10 unique receivers in 24h | +30 | HIGH |
| **R004** | Mule Chain Rapid Pass-Through | Mule Chain | `amount`, `timestamp`, `recent_transactions` | ≥90% forwarded within 15 min | +40 | CRITICAL |
| **R005** | Smurfing / Structuring | Smurfing | `amount` | ₹48,000 ≤ amount ≤ ₹49,999 | +35 | HIGH |
| **R006** | Shared Hardware Device | Shared Device | `linked_devices_count` | >3 accounts per device | +35 | HIGH |
| **R007** | Dormant Account Reactivation | Dormant Reactivation | `sender_account` (`dormant_days`, `is_dormant`) | Dormancy >90 days | +30 | HIGH |
| **R008** | New Account Abuse | New Account Abuse | `sender_account.opened_at`, `recent_transactions` | Account age <7 days, >15 txns | +25 | HIGH |
| **R009** | Cross-Channel Hopping | Cross-Channel Hopping | `channel`, `recent_transactions.channel` | ≥3 payment rails in 1 hour | +25 | MEDIUM |
| **R010** | Shared IP Address Clustering | Shared IP | `linked_ips_count` | >5 accounts per public IP | +30 | HIGH |
| **R011** | Impossible Travel Velocity | Impossible Travel | `travel_speed_kmh`, `impossible_travel` | Implied speed >500 km/h | +35 | HIGH |
| **R012** | Night Activity Anomalies | Night Activity | `timestamp.hour`, `amount` | 12 AM - 5 AM and amount ≥ ₹50K | +20 | MEDIUM |
| **R013** | Shared Beneficiary Convergence | Shared Beneficiary | `beneficiary_linked_accounts_count` | ≥5 accounts to same beneficiary | +30 | HIGH |
| **R014** | Circular Flow / Wash Laundering | Circular Flow | `sender_account_id`, `cycle_path` | Funds return to originator | +40 | CRITICAL |

---

## 4. Modular Rule Contract

The base abstraction is implemented in `app.engines.rules.base`:

```python
class BaseRule(ABC):
    rule_code: str
    rule_name: str
    pattern_name: str
    score_contribution: int
    severity: str
    description: str

    @abstractmethod
    def evaluate(self, context: RuleContext) -> RuleMatchResult: ...
```

### Context & Result Payloads
- **`RuleContext`**: Encapsulates `transaction`, `sender_account`, `recent_transactions`, `linked_devices_count`, and `linked_ips_count`.
- **`RuleMatchResult`**: Returns `rule_code`, `rule_name`, `pattern_name`, `matched`, `score_contribution`, `severity`, and `narrative`.
- **`EvaluationResult`**: Aggregates all matched rules, calculates `total_risk_score_delta`, deduplicates `flagged_patterns`, and computes the strict `highest_severity` rating (`CRITICAL` > `HIGH` > `MEDIUM` > `LOW`).

---

## 5. Rule Registry

The rule registry (`app.engines.rules.engine.ModularRuleEngine`) maintains a deterministic sequence of all 14 rule classes:
- Explicit ordering: R001 through R014.
- Direct lookup via `get_rule(rule_code: str) -> BaseRule | None`.
- Full collection via `list_rules() -> list[BaseRule]`.
- Isolated single-rule execution via `evaluate_rule(rule_code: str, context: RuleContext) -> RuleMatchResult | None`.
- Full or filtered multi-rule execution via `evaluate(...)`.

---

## 6. Backward Compatibility Layer

To prevent any breaking change across existing callers (`TransactionService`, `test_transaction_event.py`, etc.):
- `app.engines.rules.rule_engine.RuleEngine` retains identical public method signatures (`evaluate`, `_check_high_velocity`, `_check_fan_in`, `_check_fan_out`, `_check_mule_chain`, `_check_smurfing`, `_check_shared_device`).
- The global singleton instance `rule_engine = RuleEngine()` remains available at `app.engines.rules.rule_engine`.
- Public imports (`from app.engines.rules.rule_engine import rule_engine, RuleEngine, RuleMatchResult, EvaluationResult`) continue to function without modification.

---

## 7. Behavioral Parity & Verification Results

Deterministic tests in `backend/tests/engines/rules/` confirm:
1. **Rule Parity (`test_rule_parity.py`)**: Exact parity between legacy helper methods and modular rule classes for R001 through R006.
2. **Rule Contract (`test_rule_contract.py`)**: All 14 rules independently pass positive and negative trigger cases.
3. **Registry Completeness (`test_rule_registry.py`)**: Exactly 14 rules registered with unique codes R001–R014.
4. **Interactions (`test_rule_interactions.py`)**: Multi-rule triggers aggregate risk scores additively and resolve severities strictly by hierarchy.
5. **Full Regression**: Full pytest suite passes with 107 passed tests (44 new M5 tests), exactly 0 new regressions.

---

## 8. Threshold Preservation

All 14 rule thresholds remain strictly preserved:
- R001: 20 transactions / 1 hour
- R002: 10 senders / 24 hours
- R003: 10 receivers / 24 hours
- R004: ≥90% forwarded within 15 minutes
- R005: ₹48,000 to ₹49,999
- R006: >3 accounts per device
- R007: >90 days dormancy
- R008: <7 days account age with >15 transactions
- R009: ≥3 payment rails in 1 hour
- R010: >5 accounts per IP
- R011: >500 km/h transit velocity
- R012: 12 AM - 5 AM and amount ≥ ₹50,000
- R013: ≥5 accounts per beneficiary
- R014: Intermediate hops returning to originator (≤5 hops)

---

## 9. Known Limitations

1. **Pre-existing test_config DSN test failure**: `test_config.py::test_postgres_dsn_computation` fails due to live Supabase URL format in `.env`. Untouched per safety invariants.
2. **Pre-existing test_dashboard ASGITransport failure**: `test_dashboard.py` fails when run with httpx ASGITransport without FastAPI lifespan database initialization. Untouched per safety invariants.
3. **Pre-existing frontend lint warning**: `frontend/src/lib/api.ts` ESLint rule flags explicit `any` on lines 229, 233. Untouched per safety invariants.

---

## 10. Future Extension Path

- **Milestone 6 (Temporal Intelligence)**: Integrate temporal sequence tracking and velocity graph windows without altering the rule contract.
- **Milestone 7 (Graph Intelligence)**: Feed graph topology metrics (cycles, centrality, Louvain communities) directly into rule contexts.
- **Milestone 10 (Risk Fusion)**: Combine rule engine outputs with tabular ML predictions and graph neural network embeddings.
