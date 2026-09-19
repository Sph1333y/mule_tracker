"""
MuleTrace AI — Domain Interfaces / Ports.

Defines cloud-agnostic, infrastructure-free abstract contracts (ports) for:
1. GraphRepository: Graph topological operations (subgraphs, paths, cycles, device links)
2. TransactionRepository: Transaction persistence and retrieval
3. AlertRepository: Fraud alert creation, query, and status lifecycle
4. ModelService: Machine learning inference and risk prediction
5. InvestigationCopilot: Investigation assistance and narrative synthesis

Architectural Boundary:
- Zero infrastructure dependencies (no SQLAlchemy, Neo4j, NetworkX, Torch, Bedrock, boto3).
- Uses only Python standard library and domain types (TransactionEvent).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from app.domain.models import TransactionEvent


# ── Domain Result Types ───────────────────────────────────────────────


@dataclass(frozen=True)
class ModelPrediction:
    """Domain model representing machine learning inference results.

    Attributes:
        risk_score: Normalized risk score between 0 and 100.
        fraud_probability: Estimated probability of fraud between 0.0 and 1.0.
        is_fraud: Binary classification whether transaction is predicted fraudulent.
        model_version: Identifier of the model version that generated the prediction.
        details: Optional supplementary metadata (e.g., feature contributions, SHAP values).
    """

    risk_score: int
    fraud_probability: float
    is_fraud: bool
    model_version: str = "1.0.0"
    details: Optional[dict[str, Any]] = None


# ── 1. GraphRepository Port ───────────────────────────────────────────


class GraphRepository(ABC):
    """Port for graph network storage and topological intelligence queries.

    Encapsulates operations for storing account-transaction topologies, detecting
    mule layering chains, tracing multi-hop fund flows, and identifying shared
    hardware/device clusters.

    Implementations:
        - NetworkXGraphRepository (Local in-memory / Build It phase)
        - Neo4jGraphRepository (Existing Neo4j cluster)
        - NeptuneGraphRepository (Amazon Neptune / Ship It phase)
    """

    @abstractmethod
    async def add_transaction(self, event: TransactionEvent) -> None:
        """Ingest a canonical transaction event into the graph topology.

        Creates or updates sender and receiver account nodes and establishes
        a directed transfer edge between them with transaction attributes.

        Args:
            event: Canonical transaction event to record.
        """
        pass

    @abstractmethod
    async def get_subgraph(self, account_id: str, hops: int = 2) -> dict[str, Any]:
        """Retrieve the local neighborhood graph centered on an account.

        Args:
            account_id: Target account identifier.
            hops: Maximum traversal distance from the root account (default: 2).

        Returns:
            Dictionary containing 'nodes' and 'edges' lists representing
            the topological subgraph around the specified account.
        """
        pass

    @abstractmethod
    async def trace_transaction_path(
        self, transaction_id: str, max_depth: int = 5
    ) -> dict[str, Any]:
        """Trace the multi-hop fund flow path associated with a transaction.

        Traverses consecutive fund transfers to trace layering chains
        where funds pass through intermediary mule accounts.

        Args:
            transaction_id: Unique transaction reference / ID.
            max_depth: Maximum path traversal depth in hops (default: 5).

        Returns:
            Dictionary with 'nodes', 'edges', and 'path_summary' describing
            the layering chain.
        """
        pass

    @abstractmethod
    async def find_circular_paths(
        self, start_account: str, max_depth: int = 5
    ) -> list[list[str]]:
        """Detect circular fund routing loops originating from an account.

        Identifies mule cycles where funds loop back to the originator
        or a coordinated cluster of intermediary accounts.

        Args:
            start_account: Account identifier to start cycle detection from.
            max_depth: Maximum cycle length in hops (default: 5).

        Returns:
            List of detected cycles, each represented as an ordered list
            of account identifiers forming the loop.
        """
        pass

    @abstractmethod
    async def link_account_device(self, account_id: str, device_id: str) -> None:
        """Establish a relationship between an account and a device fingerprint.

        Links an account node to a device entity to detect shared device
        mule rings and hardware-level account syndicates.

        Args:
            account_id: Unique account identifier.
            device_id: Hardware fingerprint or device identifier.
        """
        pass


# ── 2. TransactionRepository Port ─────────────────────────────────────


class TransactionRepository(ABC):
    """Port for transactional data persistence and retrieval.

    Provides domain-level data access operations for storing and querying
    canonical TransactionEvent entities without exposing database-specific
    ORM models, sessions, or drivers.

    Implementations:
        - PostgreSQLTransactionRepository (Local PostgreSQL via SQLAlchemy)
        - RDSTransactionRepository (Amazon Aurora / RDS PostgreSQL)
        - In-memory / FakeTransactionRepository (Testing)
    """

    @abstractmethod
    async def save(self, event: TransactionEvent) -> TransactionEvent:
        """Persist a canonical transaction event to durable storage.

        Args:
            event: Canonical TransactionEvent to persist.

        Returns:
            Persisted TransactionEvent with any storage-assigned metadata.
        """
        pass

    @abstractmethod
    async def get_by_id(self, transaction_id: str) -> Optional[TransactionEvent]:
        """Retrieve a single transaction event by its unique ID or reference.

        Args:
            transaction_id: Unique transaction ID or reference UTR.

        Returns:
            TransactionEvent if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_by_account(
        self, account_id: str, limit: int = 50
    ) -> list[TransactionEvent]:
        """Retrieve recent transactions associated with a given account.

        Fetches transactions where the account acts as sender or receiver,
        ordered by timestamp descending.

        Args:
            account_id: Account identifier to query.
            limit: Maximum number of transactions to return (default: 50).

        Returns:
            List of matching TransactionEvent entities.
        """
        pass

    @abstractmethod
    async def get_recent(self, limit: int = 20) -> list[TransactionEvent]:
        """Retrieve the most recent transactions across the system.

        Args:
            limit: Maximum number of transactions to return (default: 20).

        Returns:
            List of recent TransactionEvent entities ordered by timestamp descending.
        """
        pass


# ── 3. AlertRepository Port ───────────────────────────────────────────


class AlertRepository(ABC):
    """Port for fraud alert persistence, retrieval, and lifecycle management.

    Handles recording fraud alerts triggered by rules or ML engines,
    retrieving alerts by triage status and severity, and updating alert status.

    Implementations:
        - PostgreSQLAlertRepository (Local PostgreSQL via SQLAlchemy)
        - RDSAlertRepository (Amazon Aurora / RDS PostgreSQL)
        - In-memory / FakeAlertRepository (Testing)
    """

    @abstractmethod
    async def create_alert(self, alert_data: dict[str, Any]) -> dict[str, Any]:
        """Persist a new fraud alert record.

        Args:
            alert_data: Dictionary containing alert attributes (e.g. alert_number,
                account_id, rule_code, severity, risk_score, pattern_type).

        Returns:
            Dictionary representing the created alert record.
        """
        pass

    @abstractmethod
    async def get_by_id(self, alert_id: str) -> Optional[dict[str, Any]]:
        """Retrieve an alert by its unique identifier or alert number.

        Args:
            alert_id: UUID string or human-readable alert number.

        Returns:
            Dictionary representing the alert if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_alerts(
        self,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve alerts filtered by severity and/or triage lifecycle status.

        Args:
            severity: Optional severity filter (LOW, MEDIUM, HIGH, CRITICAL).
            status: Optional status filter (OPEN, IN_PROGRESS, ESCALATED, RESOLVED, FALSE_POSITIVE).
            limit: Maximum number of alerts to return (default: 50).

        Returns:
            List of matching alert dictionaries ordered by creation time descending.
        """
        pass

    @abstractmethod
    async def update_status(
        self, alert_id: str, status: str
    ) -> Optional[dict[str, Any]]:
        """Update the triage lifecycle status of an alert.

        Args:
            alert_id: Unique alert identifier or alert number.
            status: New status (e.g., IN_PROGRESS, RESOLVED, FALSE_POSITIVE).

        Returns:
            Updated alert dictionary if found and updated, None otherwise.
        """
        pass


# ── 4. ModelService Port ──────────────────────────────────────────────


class ModelService(ABC):
    """Port for machine learning inference and fraud risk prediction.

    Provides a model-agnostic contract for generating fraud scores and
    predictions from canonical transaction events.

    Implementations:
        - LocalMLEngine (RandomForest / XGBoost pipelines via joblib)
        - AutoGluonModelService (AutoGluon Tabular predictor / Build It)
        - SageMakerModelService (Amazon SageMaker Serverless / Ship It)
    """

    @abstractmethod
    def predict_risk(self, event: TransactionEvent) -> ModelPrediction:
        """Compute fraud risk score and classification for a transaction.

        Args:
            event: Canonical TransactionEvent to evaluate.

        Returns:
            ModelPrediction containing risk_score (0-100), fraud_probability,
            is_fraud boolean, and model_version.
        """
        pass


# ── 5. InvestigationCopilot Port ──────────────────────────────────────


class InvestigationCopilot(ABC):
    """Port for AI-powered fraud investigation assistance and narrative synthesis.

    Provides a provider-agnostic interface for synthesizing structured evidence,
    topological paths, and rule violations into human-readable executive narratives
    and recommended action steps for AML compliance officers.

    Implementations:
        - LocalCopilot (Local LLM via Ollama / Build It)
        - BedrockCopilot (Amazon Bedrock Claude 3.5 Sonnet / Ship It)
        - TemplateCopilot (Deterministic heuristic fallback)
    """

    @abstractmethod
    async def generate_narrative(self, evidence: dict[str, Any]) -> str:
        """Synthesize structured case evidence into an AML executive narrative.

        Args:
            evidence: Dictionary containing transaction details, rule matches,
                graph traversal hops, and behavioral anomalies.

        Returns:
            Human-readable natural language narrative explaining the suspicious pattern.
        """
        pass

    @abstractmethod
    async def suggest_next_steps(self, evidence: dict[str, Any]) -> list[str]:
        """Generate prioritized investigative recommendations based on evidence.

        Args:
            evidence: Structured case and alert evidence.

        Returns:
            List of recommended actionable steps (e.g., 'Freeze beneficiary account',
            'Submit SAR/STR to FIU-IND', 'Request biometric re-verification').
        """
        pass
