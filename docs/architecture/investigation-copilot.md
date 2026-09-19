# MuleTrace AI — M12 Deterministic Investigation Copilot Architecture

## 1. Executive Overview & Purpose

Milestone 12 (M12) establishes the **Deterministic Investigation Copilot** for the MuleTrace AI platform.
The copilot is an additive, transparent, and audit-compliant synthesis engine designed to assist AML compliance investigators and fraud analysts.

### Core Architectural Guarantees
- **STRICTLY ZERO LLM**: M12 contains zero integrations with generative AI or LLM services (no OpenAI, Gemini, Bedrock, Ollama, Claude, Llama, or Mistral).
- **Zero API Keys & Offline Operation**: Requires no cloud credentials, external network connectivity, or runtime inference services.
- **Deterministic Rendering**: Executive summaries, risk posture evaluations, key findings, suggested next steps, follow-up questions, and governance disclosures are generated via rule-governed templates with stable sorting.
- **M10 Source of Truth for Risk**: Consumes upstream M10 `FusionResult` and strictly preserves `composite_risk_score` and `risk_level` without recalculation or scoring drift.
- **M11 Source of Truth for Evidence**: Consumes upstream M11 `EvidencePackage` and references 100% verified, valid `evidence_id`s. Zero hallucinated or fabricated evidence items.
- **Non-Punitive Investigative Guidance**: Recommends technical data audits and review steps, avoiding automated account blocking or unsupported legal/regulatory assertions.
- **Application Preservation**: Does not alter existing backend endpoints, database schemas, or frontend interfaces. Existing systems operate with full fidelity regardless of M12 availability.

---

## 2. Subsystem Architecture

```
                  ┌──────────────────────────────┐
                  │    Canonical Transaction     │
                  └──────────────┬───────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
     ┌───────────┐         ┌───────────┐         ┌───────────┐
     │ M5 Rules  │         │M6 Temporal│         │ M7 Graph  │
     └─────┬─────┘         └─────┬─────┘         └─────┬─────┘
           │                     │                     │
           └──────────────┬──────┴─────────────────────┘
                          │
                  ┌───────┴───────┐
                  ▼               ▼
            ┌───────────┐   ┌───────────┐
            │ M8 Tabular│   │ M9 Graph  │
            │    ML     │   │    ML     │
            └─────┬─────┘   └─────┬─────┘
                  │               │
                  └───────┬───────┘
                          │
                          ▼
            ┌───────────────────────────┐
            │     M10 Risk Fusion       │ ◄── Source of Truth for Risk
            └─────────────┬─────────────┘
                          │
                          ▼
            ┌───────────────────────────┐
            │    M11 Evidence Engine    │ ◄── Source of Truth for Evidence
            └─────────────┬─────────────┘
                          │
                          ▼
    ═════════════════════════════════════════════════════════════
    ║        M12 DETERMINISTIC INVESTIGATION COPILOT            ║
    ║                                                           ║
    ║   ┌───────────────────────────────────────────────────┐   ║
    ║   │               InvestigationContext                │   ║
    ║   └─────────────────────────┬─────────────────────────┘   ║
    ║                             ▼                             ║
    ║   ┌───────────────────────────────────────────────────┐   ║
    ║   │       DeterministicInvestigationCopilot           │   ║
    ║   │   - Preserves M10 composite_risk_score & tier     │   ║
    ║   │   - Extracts KeyFindings from M11 EvidenceItems   │   ║
    ║   │   - Synthesizes Executive Narrative & Risk Summary│   ║
    ║   │   - Emits Prioritized Investigative Next Steps    │   ║
    ║   │   - Generates Targeted Follow-Up Questions        │   ║
    ║   │   - Emits Deterministic Limitations Disclosures   │   ║
    ║   └─────────────────────────┬─────────────────────────┘   ║
    ║                             ▼                             ║
    ║   ┌───────────────────────────────────────────────────┐   ║
    ║   │          InvestigationCopilotResponse             │   ║
    ║   └───────────────────────────────────────────────────┘   ║
    ═════════════════════════════════════════════════════════════
                          │
                          ▼
            ┌───────────────────────────┐
            │  FastAPI API v1 Endpoint  │
            │ POST /investigations/     │
            │          copilot          │
            └───────────────────────────┘
```

---

## 3. Domain Port Compliance

M12 implements the domain port defined in [`backend/app/domain/interfaces.py`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py):

```python
class InvestigationCopilot(ABC):
    @abstractmethod
    async def generate_narrative(self, evidence: dict[str, Any]) -> str:
        """Synthesize structured case evidence into an AML executive narrative."""
        pass

    @abstractmethod
    async def suggest_next_steps(self, evidence: dict[str, Any]) -> list[str]:
        """Generate prioritized investigative recommendations based on evidence."""
        pass
```

The concrete implementation `DeterministicInvestigationCopilot` in [`backend/app/engines/ai/copilot.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/ai/copilot.py) implements both methods asynchronously and provides comprehensive typed synthesis via `investigate(context) -> InvestigationCopilotResponse`.

---

## 4. Input & Output Contracts

### Input: `InvestigationContext`
- `case_id: Optional[str]`: Unique case tracking reference.
- `subject_id: Optional[str]`: Target account or entity identifier.
- `transaction_id: Optional[str]`: Primary transaction reference.
- `fusion_result: Optional[FusionResult]`: Upstream M10 risk assessment (read-only).
- `evidence_package: Optional[EvidencePackage]`: Upstream M11 evidence package (read-only).
- `investigator_query: Optional[str]`: Optional inquiry string.
- `metadata: dict[str, Any]`: Contextual execution metadata.

### Output: `InvestigationCopilotResponse`
- `case_id: Optional[str]`
- `subject_id: Optional[str]`
- `transaction_id: Optional[str]`
- `composite_risk_score: float`: Exactly inherited from M10 ([0.0, 100.0]).
- `risk_level: str`: Exactly inherited from M10 (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- `risk_summary: str`: Deterministic summary of risk score and driver modalities.
- `investigation_summary: str`: Factual executive narrative synthesizing observed signals.
- `key_findings: tuple[KeyFinding, ...]`: Structured findings referencing valid M11 evidence IDs.
- `evidence_references: tuple[str, ...]`: Stable, ordered list of referenced M11 evidence IDs.
- `suggested_next_steps: tuple[SuggestedAction, ...]`: Non-punitive investigative recommendations.
- `follow_up_questions: tuple[str, ...]`: Targeted forensic inquiries based on evidence.
- `limitations: tuple[str, ...]`: Transparent audit and coverage disclosures.
- `generation_metadata: dict[str, Any]`: Diagnostic audit block confirming deterministic generation.

---

## 5. Deterministic Template Architecture

All output text is rendered through pure functions in [`backend/app/engines/ai/templates.py`](file:///D:/Team_Cipher_Unit/backend/app/engines/ai/templates.py):

1. **Risk Summary (`render_risk_summary`)**:
   - Synthesizes composite risk score, risk level, and active driver modalities sorted deterministically by weighted contribution.
2. **Executive Narrative (`render_investigation_summary`)**:
   - Compiles detected patterns (circular routing, rapid pass-through, shared hardware/network infrastructure, transaction velocity bursts, high in/out degree concentration, and ML anomalies) into a coherent, non-speculative factual summary.
3. **Key Findings (`extract_key_findings`)**:
   - Maps each ranked M11 `EvidenceItem` directly to a `KeyFinding`, retaining the exact `evidence_id`, title, description, category, severity, source, and metrics.
4. **Investigative Next Steps (`generate_investigation_actions`)**:
   - Produces prioritized `SuggestedAction` items categorized by investigative archetype (`TOPOLOGY_ANALYSIS`, `TEMPORAL_AUDIT`, `DEVICE_VERIFICATION`, `COUNTERPARTY_VERIFICATION`, `MODEL_ANOMALY_REVIEW`).
   - Prioritized deterministically: `CRITICAL` -> `HIGH` -> `MEDIUM` -> `LOW`.
   - Never issues automated account closures, freezes, or criminal accusations.
5. **Follow-Up Questions (`generate_follow_up_questions`)**:
   - Emits specific investigative inquiries strictly triggered by present evidence items.
6. **Governance Limitations (`generate_audit_limitations`)**:
   - Discloses zero-LLM architecture, M10 score inheritance, M11 evidence provenance, and any missing/unavailable modalities.

---

## 6. Safety & Failure Isolation

- **Zero LLM Dependency**: Completely offline; no OpenAI/Gemini/Bedrock SDKs, keys, or external AI network calls.
- **Preservation of Upstream Artifacts**: M10 scores and M11 evidence items are frozen and never mutated.
- **Safe Degradation**: If empty or malformed inputs are provided, `DeterministicInvestigationCopilot` safely degrades to baseline account audits and transparent limitation notices without crashing.
- **API Isolation**: Endpoint `POST /api/v1/investigations/copilot` catches and encapsulates all exceptions, returning standard error responses without crashing the server or disturbing existing routes.
