# MuleTrace AI — Domain Interfaces & Ports Specification

## 1. Architectural Purpose

In Hexagonal / Ports & Adapters Architecture, the **Domain Layer** represents the core business capabilities, entities, rules, and invariants. It must remain strictly independent of infrastructure, persistence mechanisms, cloud providers, and transport protocols.

**Milestone 2 establishes this architectural boundary** by introducing domain-level interfaces (ports). These abstract base classes (`ABC`) define *what* operations the MuleTrace AI fraud detection platform requires from infrastructure, without dictating *how* those operations are executed or what underlying database, graph engine, or ML service is used.

```
                         ┌─────────────────────────────┐
                         │        DOMAIN LAYER         │
                         │                             │
                         │  TransactionEvent (M1)      │
                         │  ModelPrediction (M2)       │
                         │                             │
                         │       DOMAIN PORTS          │
                         │  - GraphRepository          │
                         │  - TransactionRepository    │
                         │  - AlertRepository          │
                         │  - ModelService             │
                         │  - InvestigationCopilot     │
                         └──────────────┬──────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           │ (BUILD IT: Open-Source)    │                            │ (SHIP IT: AWS Cloud)
           ▼                            ▼                            ▼
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│  In-Memory / Local   │    │ Existing Monolith    │    │ AWS Managed Services │
│                      │    │                      │    │                      │
│ NetworkXGraphRepo    │    │ Neo4j Driver         │    │ Amazon Neptune       │
│ SQLite / Local PG    │    │ SQLAlchemy + AsyncPG │    │ Amazon Aurora RDS    │
│ Scikit/XGBoost/AG    │    │ Local Joblib Models  │    │ Amazon SageMaker     │
│ Local Ollama LLM     │    │ Python Rule Engine   │    │ Amazon Bedrock       │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

> **Critical Principle**:
> `BUSINESS LOGIC = CLOUD AGNOSTIC`
> `INFRASTRUCTURE = REPLACEABLE THROUGH ADAPTERS`

---

## 2. Interface / Port Inventory

The 5 domain ports defined in [`backend/app/domain/interfaces.py`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py) are:

| Port Interface | Category | Core Responsibility | Current Consumer |
| :--- | :--- | :--- | :--- |
| [`GraphRepository`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py#L42-L125) | Topology & Relationships | Ingest transactions into graph, query subgraphs, trace multi-hop layering paths, detect cycles, link devices | `app/api/v1/graph.py`, `path_analysis.py`, `relationship_engine.py` |
| [`TransactionRepository`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py#L128-L191) | Persistence & Retrieval | Store canonical transactions, retrieve by ID, query by account, retrieve recent streams | `app/api/v1/transactions.py`, `transaction_service.py`, `rule_engine.py` |
| [`AlertRepository`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py#L194-L263) | Alert Lifecycle & Triage | Persist fraud alerts, query by severity/status, update triage state | `app/api/v1/alerts.py`, `alert_service.py`, `alert_correlator.py` |
| [`ModelService`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py#L266-L289) | ML Inference | Generate risk scores, fraud probabilities, and binary classification from transactions | `app/api/v1/ml.py`, `xgboost_model.py`, `transaction_service.py` |
| [`InvestigationCopilot`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py#L292-L330) | AI Narrative Assistance | Synthesize structured evidence into AML narratives, suggest actionable investigative next steps | SOC Dashboard, STR Report Generation, `app/models/report.py` |

---

## 3. Detailed Port Responsibilities & Contracts

### 3.1 `GraphRepository`

- **Purpose**: Provides graph topological storage and relationship traversal for money-mule detection.
- **Methods**:
  - `add_transaction(event: TransactionEvent) -> None`: Ingests a transaction into the network topology, creating/updating account nodes and establishing a directed transfer edge.
  - `get_subgraph(account_id: str, hops: int = 2) -> dict[str, Any]`: Retrieves the local neighborhood graph centered on `account_id` up to `hops` traversal distance (`nodes` and `edges`).
  - `trace_transaction_path(transaction_id: str, max_depth: int = 5) -> dict[str, Any]`: Follows consecutive transfer hops to trace layering flows where illicit funds pass through intermediary mule accounts.
  - `find_circular_paths(start_account: str, max_depth: int = 5) -> list[list[str]]`: Identifies cyclical fund routing loops originating from or returning to `start_account`.
  - `link_account_device(account_id: str, device_id: str) -> None`: Connects account nodes to hardware fingerprints to detect shared device mule rings.
- **Domain Dependencies**: [`TransactionEvent`](file:///D:/Team_Cipher_Unit/backend/app/domain/models.py), standard primitives (`dict`, `list`, `str`, `int`).
- **Infrastructure Dependencies**: **ZERO**. Does not import or expose Neo4j drivers, Cypher query strings, sessions, NetworkX graph objects, or Gremlin query syntax.

### 3.2 `TransactionRepository`

- **Purpose**: Provides durable storage and retrieval of financial transactions.
- **Methods**:
  - `save(event: TransactionEvent) -> TransactionEvent`: Persists a canonical transaction event.
  - `get_by_id(transaction_id: str) -> Optional[TransactionEvent]`: Fetches a single transaction by its unique reference UTR or ID.
  - `get_by_account(account_id: str, limit: int = 50) -> list[TransactionEvent]`: Fetches chronological transactions involving `account_id` as sender or receiver.
  - `get_recent(limit: int = 20) -> list[TransactionEvent]`: Fetches the latest system-wide transactions.
- **Domain Dependencies**: [`TransactionEvent`](file:///D:/Team_Cipher_Unit/backend/app/domain/models.py), `Optional`, `list`.
- **Infrastructure Dependencies**: **ZERO**. Does not expose SQLAlchemy `Session`, `Query`, `mapped_column`, database engine connections, or PostgreSQL dialects.

### 3.3 `AlertRepository`

- **Purpose**: Manages persistence, query filtering, and status updates for fraud alerts.
- **Methods**:
  - `create_alert(alert_data: dict[str, Any]) -> dict[str, Any]`: Persists a newly triggered alert.
  - `get_by_id(alert_id: str) -> Optional[dict[str, Any]]`: Fetches an alert by ID or human-readable alert number.
  - `get_alerts(severity: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]`: Queries alerts filtered by severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and/or lifecycle status (`OPEN`, `IN_PROGRESS`, `ESCALATED`, `RESOLVED`, `FALSE_POSITIVE`).
  - `update_status(alert_id: str, status: str) -> Optional[dict[str, Any]]`: Updates an alert's triage status.
- **Domain Dependencies**: Standard Python types (`dict`, `str`, `Optional`, `list`).
- **Infrastructure Dependencies**: **ZERO**. Does not expose database sessions, tables, or ORM instances.

### 3.4 `ModelService`

- **Purpose**: Model-agnostic port for computing ML fraud risk scores and classifications.
- **Methods**:
  - `predict_risk(event: TransactionEvent) -> ModelPrediction`: Generates risk score (0-100), fraud probability (0.0-1.0), binary fraud flag, and model metadata from a canonical transaction.
- **Domain Dependencies**: [`TransactionEvent`](file:///D:/Team_Cipher_Unit/backend/app/domain/models.py), [`ModelPrediction`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py#L25-L39).
- **Infrastructure Dependencies**: **ZERO**. Does not import Scikit-learn, XGBoost, PyTorch, AutoGluon, or SageMaker.

### 3.5 `InvestigationCopilot`

- **Purpose**: Provider-agnostic port for AI-assisted AML investigation narrative synthesis.
- **Methods**:
  - `generate_narrative(evidence: dict[str, Any]) -> str`: Translates multi-source evidence (rule flags, layering hops, velocity anomalies) into an executive summary for compliance officers.
  - `suggest_next_steps(evidence: dict[str, Any]) -> list[str]`: Produces recommended investigative actions (e.g., account freeze, SAR submission).
- **Domain Dependencies**: Standard Python types (`dict`, `str`, `list`).
- **Infrastructure Dependencies**: **ZERO**. Does not import Ollama, OpenAI, Amazon Bedrock, LangChain, or HTTP clients.

---

## 4. What Each Interface Intentionally Does NOT Know

1. **`GraphRepository` does NOT know**:
   - Whether graph data is stored in memory as an adjacency list, in a Neo4j graph database, in an Amazon Neptune cluster, or in a PostgreSQL recursive CTE.
   - Any query language (Cypher, Gremlin, openCypher, SPARQL).
   - Any driver connection pooling, session lifecycle, or socket errors.

2. **`TransactionRepository` does NOT know**:
   - Whether storage is PostgreSQL, SQLite, DynamoDB, Amazon Aurora, or an in-memory dictionary.
   - Database schema migrations, table names, primary key generators, foreign keys, or ACID transaction isolation levels.

3. **`AlertRepository` does NOT know**:
   - The underlying relational ORM model or index configuration.
   - How status changes trigger external webhooks or notification emails.

4. **`ModelService` does NOT know**:
   - Whether inference is performed locally by RandomForest / XGBoost in-process, by an AutoGluon Tabular predictor, or via an HTTP REST endpoint hosted on Amazon SageMaker Serverless.
   - Hardware acceleration (CPU, CUDA GPU, AWS Inferentia).

5. **`InvestigationCopilot` does NOT know**:
   - Whether the LLM is running locally via Ollama (Llama 3 / Mistral), in the cloud via Amazon Bedrock (Anthropic Claude 3.5 Sonnet), or using a deterministic rule template fallback.
   - Prompt engineering templates, token budgets, or model temperature settings.

---

## 5. Current Implementations That Remain Unchanged

In accordance with the **Absolute Safety Requirement** of Milestone 2:
- Existing implementations continue to run untouched.
- No existing class has been forced to inherit from these interfaces yet.
- No dependency injection or FastAPI router wiring was modified.
- Production services remain 100% operational:
  - `backend/app/repositories/transaction_repository.py` (SQLAlchemy Transaction repository)
  - `backend/app/repositories/alert_repository.py` (SQLAlchemy Alert repository)
  - `backend/app/database/neo4j.py` & `app/engines/graph/path_analysis.py` (Neo4j driver & Cypher queries)
  - `backend/app/engines/ml/xgboost_model.py` (MLEngine RandomForest + XGBoost pipeline)
  - `backend/app/engines/rules/rule_engine.py` (14 fraud rules)
  - `backend/app/main.py` & `app/api/v1/*` (FastAPI routers and startup lifespan)

---

## 6. Future Adapter Mapping (Hackathon Dual-Phase)

The domain interfaces created in Milestone 2 provide the exact substitution contracts required for both the **BUILD IT** (Open-Source / Local) and **SHIP IT** (AWS Cloud) phases:

```
┌────────────────────────┬─────────────────────────────┬──────────────────────────────┐
│ Domain Interface / Port│ BUILD IT Phase (Local / OSS)│ SHIP IT Phase (AWS Managed)  │
├────────────────────────┼─────────────────────────────┼──────────────────────────────┤
│ GraphRepository        │ NetworkXGraphRepository (M3)│ NeptuneGraphRepository (M19) │
│ TransactionRepository  │ PostgreSQLTransactionRepo   │ RDSTransactionRepository     │
│ AlertRepository        │ PostgreSQLAlertRepo         │ RDSAlertRepository           │
│ ModelService           │ LocalMLEngine / AutoGluon   │ SageMakerModelService        │
│ InvestigationCopilot   │ LocalCopilot (Ollama / M7)  │ BedrockCopilot (Claude 3.5)  │
└────────────────────────┴─────────────────────────────┴──────────────────────────────┘
```

> **Note**: These adapters will be constructed incrementally in subsequent milestones (M3 for NetworkX, M4 for Repositories, M6 for ML, M7 for Copilot, M19 for Neptune, M20 for Bedrock). None of these adapters were implemented in Milestone 2.
