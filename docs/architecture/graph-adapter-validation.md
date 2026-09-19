# MuleTrace AI — Graph Adapter Validation & Controlled Integration

## 1. M4 Objective

The objective of Milestone 4 is to establish, validate, and test the graph adapter boundary without disturbing the active, working application.

Milestone 4 delivers:
1. Reusable, parameterized contract validation against the domain [`GraphRepository`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py#L42-L125) interface.
2. Full semantic validation of [`NetworkXGraphRepository`](file:///D:/Team_Cipher_Unit/backend/app/repositories/graph_nx.py) (the BUILD IT local adapter).
3. A non-invasive Neo4j adapter ([`Neo4jGraphRepository`](file:///D:/Team_Cipher_Unit/backend/app/repositories/graph_neo4j.py)) wrapping existing Neo4j Cypher operations.
4. A deterministic adapter-selection mechanism ([`get_graph_repository`](file:///D:/Team_Cipher_Unit/backend/app/repositories/graph_factory.py)) that defaults strictly to `neo4j`.
5. An empirical adapter parity matrix comparing NetworkX and Neo4j.
6. 100% preservation of the active production flow (`Next.js -> FastAPI -> Existing Graph Service -> Neo4j`).

---

## 2. Current Architecture

```
                                GraphRepository (Domain Port)
                                             ▲
                                             │
                        ┌────────────────────┴────────────────────┐
                        │                                         │
              NetworkXGraphRepository                   Neo4jGraphRepository
              (BUILD IT / In-Memory)                   (Existing Neo4j Driver)
                        │                                         │
                        ▼                                         ▼
                 nx.MultiDiGraph                          Neo4j Cypher Cluster
                        ▲                                         ▲
                        └────────────────────┬────────────────────┘
                                             │
                                    get_graph_repository()
                                    [GRAPH_BACKEND="neo4j" (DEFAULT)]
```

### Production Flow Guarantee:
```
[Frontend (Next.js / Cytoscape)]
           │
           ▼
     [FastAPI Routes]
           │
           ▼
[Existing Graph Service / Cypher Queries]  <── UNCHANGED
           │
           ▼
     [Neo4j Cluster]
```

NetworkX is NOT used by default in production. It is an isolated, independently testable adapter for local development and offline BUILD IT workloads.

---

## 3. GraphRepository Contract

The domain contract defined in [`backend/app/domain/interfaces.py`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py#L42-L125) specifies 5 mandatory asynchronous methods:

1. `async def add_transaction(self, event: TransactionEvent) -> None`
   - Ingests canonical transaction events.
   - Upserts sender/receiver account nodes.
   - Establishes a directed `TRANSFERRED_FUNDS` edge keyed by `transaction_id`.
   - Links device and IP entities where available.
2. `async def get_subgraph(self, account_id: str, hops: int = 2) -> dict[str, Any]`
   - Traverses neighborhood topology up to `hops` distance.
   - Returns structured `nodes` and `edges` without mutating graph state.
3. `async def trace_transaction_path(self, transaction_id: str, max_depth: int = 5) -> dict[str, Any]`
   - Traces downstream layering flows through intermediary accounts up to `max_depth` hops.
   - Formats human-readable `path_summary`.
4. `async def find_circular_paths(self, start_account: str, max_depth: int = 5) -> list[list[str]]`
   - Identifies directed cycles of `TRANSFERRED_FUNDS` edges returning to `start_account`.
   - Rejects non-cyclic linear chains (0 false positives).
5. `async def link_account_device(self, account_id: str, device_id: str) -> None`
   - Maps an account node to a device fingerprint via a directed `USED_DEVICE` edge.

---

## 4. Deterministic Fixtures (A through G)

The contract test suite in [`backend/tests/repositories/test_graph_repository_contract.py`](file:///D:/Team_Cipher_Unit/backend/tests/repositories/test_graph_repository_contract.py) evaluates both adapters against standardized, reproducible fixtures:

- **Fixture A (Simple Transfer)**: Single transfer $A \rightarrow B$ (`TX-A-B-001`, ₹1,000). Verifies node creation, directionality, and transaction attribute persistence.
- **Fixture B (Multiple Transactions)**: Three transfers $A \rightarrow B$ (`TX-A-B-001`, `TX-A-B-002`, `TX-A-B-003`). Verifies parallel edges are preserved without collapsing or attribute overwriting.
- **Fixture C (Multi-Hop Chain)**: Linear sequence $A \rightarrow B \rightarrow C \rightarrow D$ (`TX-CHAIN-1`, `TX-CHAIN-2`, `TX-CHAIN-3`). Verifies neighborhood hop expansion (1, 2, 3 hops) and downstream layering traces.
- **Fixture D (Circular Routing)**: Directed cycle $A \rightarrow B \rightarrow C \rightarrow A$. Verifies true cycle detection, hop limits, and rejection of linear paths ($A \rightarrow B \rightarrow C$).
- **Fixture E (Device Linkage)**: Account $A \rightarrow$ Device $D_1$. Verifies `USED_DEVICE` edge creation and deduplication.
- **Fixture F (IP Linkage)**: Account $A \rightarrow$ IP $X$. Verifies network entity tracking via `USES_IP`.
- **Fixture G (Invariants)**: Validates idempotency on duplicate insertion, read-only immutability, and instance isolation.

---

## 5. Adapter Parity Matrix

The following matrix documents verified behavior based on direct contract testing and code inspection:

| Behavior | NetworkX Adapter | Neo4j Adapter | Contract Compatible |
| :--- | :--- | :--- | :--- |
| **Account Identity** | `account:<number>` | `account_number` property | **YES** (Canonical account numbers match) |
| **Device Identity** | `device:<fingerprint>` | `fingerprint` property | **YES** |
| **IP Identity** | `ip:<address>` | Supported via `USES_IP` | **YES** (NetworkX runtime verified; Neo4j via Cypher) |
| **Transaction Identity** | Keyed by `transaction_id` | Edge attribute `ref` | **YES** |
| **Directionality** | Directed (`MultiDiGraph`) | Directed Cypher relationship | **YES** ($A \rightarrow B$) |
| **Multiple Transactions** | Discrete parallel edges | Multiple `:TRANSFERRED_FUNDS` rels | **YES** (No overwrite on either engine) |
| **Duplicate Insertion** | Idempotent (updates edge key) | Cypher `MERGE` on accounts | **YES** |
| **Subgraph Traversal** | BFS shortest path view | Variable length Cypher match `-[*1..hops]-` | **YES** (Returns `nodes` and `edges`) |
| **Transaction Path** | Downstream BFS queue | Cypher `-[*1..max_depth]->` with `WHERE ref` | **YES** (Identical summary text format) |
| **Cycle Detection** | Directed cycle DFS (`nx.all_simple_paths`) | Cypher `MATCH path = (s)-[*1..N]->(s)` | **YES** (Returns list of account chains) |
| **Device Linkage** | Directed `USED_DEVICE` edge | Cypher `(a)-[:USED_DEVICE]->(d)` | **YES** |
| **IP Linkage** | Directed `USES_IP` edge | Cypher `(a)-[:USES_IP]->(ip)` | **YES** |

---

## 6. Controlled Adapter Selection Mechanism

Implemented in [`backend/app/repositories/graph_factory.py`](file:///D:/Team_Cipher_Unit/backend/app/repositories/graph_factory.py):

```python
from app.repositories.graph_factory import get_graph_repository

# Default: returns Neo4jGraphRepository (production default)
repo = get_graph_repository()

# Explicit BUILD IT local override:
repo_local = get_graph_repository(backend="networkx")

# Environment variable override:
# export GRAPH_BACKEND="networkx"
```

### Safety Rules:
1. `DEFAULT_GRAPH_BACKEND = "neo4j"` ensures existing production configuration is never silently altered.
2. In-memory `NetworkXGraphRepository` is available on demand for tests and offline evaluation.

---

## 7. Verified Differences & Limitations

1. **Storage Persistence**:
   - `NetworkXGraphRepository` is purely in-memory (`RAM`). Graph state is cleared when the process exits.
   - `Neo4jGraphRepository` persists nodes and edges to disk in the Neo4j database.
2. **Environment Connectivity**:
   - In local development environments without an active Neo4j daemon, `Neo4jGraphRepository` detects `neo4j_manager.is_connected == False` and falls back gracefully to safe, empty responses without raising exceptions.
   - Live Neo4j contract tests are automatically skipped when the daemon is offline (`test_neo4j_live_contract_simple_transfer SKIPPED`).
3. **Graph Type Prefixing**:
   - NetworkX prefixes node IDs (`account:ACC-101`, `device:DEV-101`) to guarantee zero cross-type collision in a unified graph.
   - Neo4j separates entity types via native node labels (`:Account`, `:Device`).

---

## 8. Future Neptune Migration Path (SHIP IT)

In Milestone 19 (SHIP IT / AWS Phase), Amazon Neptune will be introduced as a third adapter:

```
GraphRepository (Domain Interface)
   ├── NetworkXGraphRepository (BUILD IT / Local / CI)
   ├── Neo4jGraphRepository    (Existing Legacy / Self-Hosted)
   └── NeptuneGraphRepository  (SHIP IT / Amazon Neptune Serverless)
```

The domain contract established and validated in M4 ensures that adding `NeptuneGraphRepository` requires **zero changes** to transaction models, fraud rules, or investigation engines.
