"""
MuleTrace AI — Domain Interfaces & Boundary Tests.

Tests:
1. Domain interfaces import cleanly.
2. Abstract base classes enforce implementation of all abstract methods.
3. Minimal fake implementations satisfy the interface contracts.
4. Import boundary test: importing app.domain.interfaces does not load
   infrastructure dependencies (neo4j, sqlalchemy, fastapi, boto3, networkx, torch, dgl, ollama).
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Optional

import pytest

from app.domain.interfaces import (
    AlertRepository,
    GraphRepository,
    InvestigationCopilot,
    ModelPrediction,
    ModelService,
    TransactionRepository,
)
from app.domain.models import TransactionEvent


# ── Minimal Fake Implementations for Contract Verification ────────────


class FakeGraphRepository(GraphRepository):
    """Test-only in-memory fake satisfying GraphRepository contract."""

    def __init__(self) -> None:
        self.transactions: list[TransactionEvent] = []
        self.device_links: dict[str, str] = {}

    async def add_transaction(self, event: TransactionEvent) -> None:
        self.transactions.append(event)

    async def get_subgraph(self, account_id: str, hops: int = 2) -> dict[str, Any]:
        return {
            "nodes": [{"id": account_id, "type": "account"}],
            "edges": [],
        }

    async def trace_transaction_path(
        self, transaction_id: str, max_depth: int = 5
    ) -> dict[str, Any]:
        return {
            "nodes": [{"id": "acc-1"}, {"id": "acc-2"}],
            "edges": [{"source": "acc-1", "target": "acc-2", "ref": transaction_id}],
            "path_summary": "1 hop transfer observed",
        }

    async def find_circular_paths(
        self, start_account: str, max_depth: int = 5
    ) -> list[list[str]]:
        return [[start_account, "acc-temp", start_account]]

    async def link_account_device(self, account_id: str, device_id: str) -> None:
        self.device_links[account_id] = device_id


class FakeTransactionRepository(TransactionRepository):
    """Test-only in-memory fake satisfying TransactionRepository contract."""

    def __init__(self) -> None:
        self._storage: dict[str, TransactionEvent] = {}

    async def save(self, event: TransactionEvent) -> TransactionEvent:
        self._storage[event.transaction_id] = event
        return event

    async def get_by_id(self, transaction_id: str) -> Optional[TransactionEvent]:
        return self._storage.get(transaction_id)

    async def get_by_account(
        self, account_id: str, limit: int = 50
    ) -> list[TransactionEvent]:
        results = [
            tx
            for tx in self._storage.values()
            if tx.sender_account == account_id or tx.receiver_account == account_id
        ]
        return results[:limit]

    async def get_recent(self, limit: int = 20) -> list[TransactionEvent]:
        sorted_txs = sorted(
            self._storage.values(), key=lambda x: x.timestamp, reverse=True
        )
        return sorted_txs[:limit]


class FakeAlertRepository(AlertRepository):
    """Test-only in-memory fake satisfying AlertRepository contract."""

    def __init__(self) -> None:
        self._alerts: dict[str, dict[str, Any]] = {}

    async def create_alert(self, alert_data: dict[str, Any]) -> dict[str, Any]:
        alert_id = str(alert_data.get("id", f"ALT-{len(self._alerts) + 1}"))
        record = {**alert_data, "id": alert_id}
        self._alerts[alert_id] = record
        return record

    async def get_by_id(self, alert_id: str) -> Optional[dict[str, Any]]:
        return self._alerts.get(alert_id)

    async def get_alerts(
        self,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        results = list(self._alerts.values())
        if severity:
            results = [a for a in results if a.get("severity") == severity]
        if status:
            results = [a for a in results if a.get("status") == status]
        return results[:limit]

    async def update_status(
        self, alert_id: str, status: str
    ) -> Optional[dict[str, Any]]:
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        alert["status"] = status
        return alert


class FakeModelService(ModelService):
    """Test-only fake satisfying ModelService contract."""

    def predict_risk(self, event: TransactionEvent) -> ModelPrediction:
        score = 85 if event.amount > 100000.0 else 20
        return ModelPrediction(
            risk_score=score,
            fraud_probability=score / 100.0,
            is_fraud=score >= 70,
            model_version="test_fake_v1.0",
            details={"evaluation": "rule_based_mock"},
        )


class FakeInvestigationCopilot(InvestigationCopilot):
    """Test-only fake satisfying InvestigationCopilot contract."""

    async def generate_narrative(self, evidence: dict[str, Any]) -> str:
        tx_count = len(evidence.get("transactions", []))
        return f"Investigation identified a suspected mule pattern across {tx_count} transactions."

    async def suggest_next_steps(self, evidence: dict[str, Any]) -> list[str]:
        return [
            "Freeze receiver account pending KYC review",
            "Generate Suspicious Transaction Report (STR)",
        ]


# ── Test Cases ────────────────────────────────────────────────────────


def test_interfaces_can_be_imported():
    """Verify all 5 domain ports and ModelPrediction are importable."""
    from app.domain import (
        AlertRepository as DomainAlertRepo,
        GraphRepository as DomainGraphRepo,
        InvestigationCopilot as DomainCopilot,
        ModelPrediction as DomainPrediction,
        ModelService as DomainModelSvc,
        TransactionRepository as DomainTxRepo,
    )

    assert DomainGraphRepo is GraphRepository
    assert DomainTxRepo is TransactionRepository
    assert DomainAlertRepo is AlertRepository
    assert DomainModelSvc is ModelService
    assert DomainCopilot is InvestigationCopilot
    assert DomainPrediction is ModelPrediction


def test_cannot_instantiate_abstract_interfaces():
    """Verify ABCs raise TypeError if instantiated directly."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        GraphRepository()  # type: ignore[abstract]

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        TransactionRepository()  # type: ignore[abstract]

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        AlertRepository()  # type: ignore[abstract]

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        ModelService()  # type: ignore[abstract]

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        InvestigationCopilot()  # type: ignore[abstract]


def test_incomplete_subclass_cannot_be_instantiated():
    """Verify that a subclass omitting an abstract method raises TypeError."""

    class IncompleteGraphRepo(GraphRepository):
        async def add_transaction(self, event: TransactionEvent) -> None:
            pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteGraphRepo()  # type: ignore[abstract]


@pytest.mark.asyncio
async def test_fake_graph_repository_contract():
    """Verify FakeGraphRepository satisfies all GraphRepository methods."""
    repo = FakeGraphRepository()
    event = TransactionEvent(
        transaction_id="TXN-GRAPH-001",
        timestamp=datetime.now(timezone.utc),
        sender_account="ACC-SENDER",
        receiver_account="ACC-RECEIVER",
        amount=50000.0,
    )

    # 1. add_transaction
    await repo.add_transaction(event)
    assert len(repo.transactions) == 1

    # 2. get_subgraph
    subgraph = await repo.get_subgraph("ACC-SENDER", hops=2)
    assert "nodes" in subgraph and "edges" in subgraph
    assert subgraph["nodes"][0]["id"] == "ACC-SENDER"

    # 3. trace_transaction_path
    path = await repo.trace_transaction_path("TXN-GRAPH-001", max_depth=3)
    assert "path_summary" in path
    assert len(path["edges"]) == 1

    # 4. find_circular_paths
    cycles = await repo.find_circular_paths("ACC-SENDER")
    assert len(cycles) == 1
    assert cycles[0][0] == "ACC-SENDER"

    # 5. link_account_device
    await repo.link_account_device("ACC-SENDER", "DEV-FP-999")
    assert repo.device_links["ACC-SENDER"] == "DEV-FP-999"


@pytest.mark.asyncio
async def test_fake_transaction_repository_contract():
    """Verify FakeTransactionRepository satisfies all TransactionRepository methods."""
    repo = FakeTransactionRepository()
    event1 = TransactionEvent(
        transaction_id="TXN-T1",
        timestamp=datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
        sender_account="ACC-1",
        receiver_account="ACC-2",
        amount=1000.0,
    )
    event2 = TransactionEvent(
        transaction_id="TXN-T2",
        timestamp=datetime(2025, 1, 1, 11, 0, tzinfo=timezone.utc),
        sender_account="ACC-2",
        receiver_account="ACC-3",
        amount=950.0,
    )

    # 1. save
    saved1 = await repo.save(event1)
    saved2 = await repo.save(event2)
    assert saved1.transaction_id == "TXN-T1"
    assert saved2.transaction_id == "TXN-T2"

    # 2. get_by_id
    retrieved = await repo.get_by_id("TXN-T1")
    assert retrieved is not None
    assert retrieved.amount == 1000.0

    missing = await repo.get_by_id("NONEXISTENT")
    assert missing is None

    # 3. get_by_account
    acc2_txs = await repo.get_by_account("ACC-2")
    assert len(acc2_txs) == 2

    # 4. get_recent
    recent = await repo.get_recent(limit=1)
    assert len(recent) == 1
    assert recent[0].transaction_id == "TXN-T2"


@pytest.mark.asyncio
async def test_fake_alert_repository_contract():
    """Verify FakeAlertRepository satisfies all AlertRepository methods."""
    repo = FakeAlertRepository()

    # 1. create_alert
    alert = await repo.create_alert(
        {
            "id": "ALT-1001",
            "account_id": "ACC-MULE-1",
            "rule_code": "HIGH_VELOCITY",
            "severity": "CRITICAL",
            "risk_score": 95,
            "status": "OPEN",
        }
    )
    assert alert["id"] == "ALT-1001"

    # 2. get_by_id
    found = await repo.get_by_id("ALT-1001")
    assert found is not None
    assert found["severity"] == "CRITICAL"

    # 3. get_alerts with filtering
    critical_alerts = await repo.get_alerts(severity="CRITICAL")
    assert len(critical_alerts) == 1
    low_alerts = await repo.get_alerts(severity="LOW")
    assert len(low_alerts) == 0

    # 4. update_status
    updated = await repo.update_status("ALT-1001", "IN_PROGRESS")
    assert updated is not None
    assert updated["status"] == "IN_PROGRESS"


def test_fake_model_service_contract():
    """Verify FakeModelService satisfies ModelService contract and ModelPrediction."""
    svc = FakeModelService()
    low_event = TransactionEvent(
        transaction_id="TXN-LOW",
        timestamp=datetime.now(timezone.utc),
        sender_account="ACC-A",
        receiver_account="ACC-B",
        amount=500.0,
    )
    pred_low = svc.predict_risk(low_event)
    assert isinstance(pred_low, ModelPrediction)
    assert pred_low.risk_score == 20
    assert not pred_low.is_fraud

    high_event = TransactionEvent(
        transaction_id="TXN-HIGH",
        timestamp=datetime.now(timezone.utc),
        sender_account="ACC-A",
        receiver_account="ACC-B",
        amount=150000.0,
    )
    pred_high = svc.predict_risk(high_event)
    assert pred_high.risk_score == 85
    assert pred_high.fraud_probability == 0.85
    assert pred_high.is_fraud
    assert pred_high.model_version == "test_fake_v1.0"


@pytest.mark.asyncio
async def test_fake_investigation_copilot_contract():
    """Verify FakeInvestigationCopilot satisfies InvestigationCopilot contract."""
    copilot = FakeInvestigationCopilot()
    evidence = {
        "case_id": "CASE-9001",
        "transactions": [{"ref": "TXN-1"}, {"ref": "TXN-2"}],
    }

    # 1. generate_narrative
    narrative = await copilot.generate_narrative(evidence)
    assert isinstance(narrative, str)
    assert "suspected mule pattern across 2 transactions" in narrative

    # 2. suggest_next_steps
    steps = await copilot.suggest_next_steps(evidence)
    assert isinstance(steps, list)
    assert len(steps) == 2
    assert "Freeze receiver account pending KYC review" in steps[0]


def test_import_boundary_isolation():
    """Verify that importing app.domain.interfaces loads ZERO infrastructure libraries.

    Runs an isolated Python subprocess to inspect sys.modules upon importing
    app.domain.interfaces.
    """
    verification_script = """
import sys
import app.domain.interfaces

forbidden_modules = [
    "neo4j",
    "sqlalchemy",
    "fastapi",
    "boto3",
    "botocore",
    "networkx",
    "torch",
    "dgl",
    "ollama",
]

imported = [m for m in forbidden_modules if m in sys.modules]
if imported:
    print(f"FORBIDDEN_IMPORTED: {','.join(imported)}")
    sys.exit(1)
else:
    print("BOUNDARY_CLEAN")
    sys.exit(0)
"""
    result = subprocess.run(
        [sys.executable, "-c", verification_script],
        capture_output=True,
        text=True,
        cwd="D:\\Team_Cipher_Unit\\backend",
    )
    assert result.returncode == 0, f"Import boundary violated: {result.stdout} {result.stderr}"
    assert "BOUNDARY_CLEAN" in result.stdout
