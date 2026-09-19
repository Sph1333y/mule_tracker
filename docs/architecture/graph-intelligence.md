# MuleTrace AI — Graph Intelligence Architecture

> **Milestone**: M7 — Graph Intelligence  
> **Status**: Completed  
> **Target Environment**: BUILD IT Phase (Local NetworkX & Port Abstraction)  
> **Audience**: Principal Architects, Graph ML Engineers, Security Operations Center (SOC) Developers

---

## 1. Executive Summary & Purpose

Milestone 7 introduces the **Graph Intelligence Layer** to MuleTrace AI. Building directly upon the canonical domain interfaces established in M2, the local in-memory graph repository in M3, the adapter factory in M4, the modular 14 fraud rules in M5, and the temporal intelligence engine in M6, M7 extracts deterministic, multi-hop topological features from transaction networks.

The primary purpose of M7 is to convert raw account topologies and transaction flows into structured, explainable, strongly typed **`GraphFeatures`** without requiring external graph infrastructure or modifying the existing production application flow.

```
                  Canonical TransactionEvent
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
        RuleEngine       TemporalEngine   Graph Intelligence
        (14 Rules)       (Time Windows)       (M7 Engine)
             │                │                │
             ▼                ▼                ▼
        Rule Signals     TemporalFeatures  GraphFeatures
             │                │                │
             └────────────────┼────────────────┘
                              │
                       Future RiskFusion (M10)
                              │
                       Future Graph ML (M9)
```

> [!IMPORTANT]
> **Production Boundary Guarantee:**
> - M7 does **NOT** replace the existing Neo4j production flow.
> - M7 is an **additive**, non-disruptive graph intelligence capability.
> - The existing Next.js frontend, FastAPI backend, PostgreSQL database, and Neo4j queries continue functioning identically.
> - `GraphFeatures` are topological signals for future Risk Fusion (M10) and Graph ML (M9) consumers; M7 does not issue subjective fraud verdicts (`fraud=true` or `mule=true`).

---

## 2. Architectural Principles & Boundaries

### 2.1 Cloud-Agnostic Core
The core computation engine in [`GraphIntelligenceEngine`](file:///D:/Team_Cipher_Unit/backend/app/engines/graph/intelligence/graph_engine.py) has **zero cloud or database dependencies**. It operates strictly through the domain [`GraphRepository`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py) port abstraction:

```
  GraphIntelligenceEngine
             │
             ▼
      GraphRepository (Port)
       ├── NetworkXGraphRepository (Local BUILD IT Adapter)
       ├── Neo4jGraphRepository (Live Production Adapter)
       └── NeptuneGraphRepository (Future SHIP IT Adapter - M15+)
```

### 2.2 Multi-Edge Safety
Financial transaction graphs are multigraphs where multiple fund transfers occur between the same sender-receiver pair. M7 preserves multi-edge semantics:
- **Transaction Counts & Degrees:** Each transfer edge increments `out_degree` / `in_degree` and `outbound_tx_count` / `inbound_tx_count`.
- **Counterparty Sets:** Multiple transfers between Account A and Account B collapse into 1 unique counterparty.
- **Audit Integrity:** All contributing transaction references (`transaction_id`) are preserved individually in `contributing_transaction_ids`.

### 2.3 Strict Directionality
Directionality is enforced across all metric extractors:
- $A \to B$ indicates an outbound transfer from $A$ and an inbound transfer to $B$.
- Senders to $A$ (`unique_senders_count`) and receivers from $A$ (`unique_receivers_count`) are never conflated.
- Pass-through and reachability tracing strictly follow edge orientations.

### 2.4 Strict Determinism
The Graph Intelligence Layer is 100% deterministic:
- Node and edge collections are processed and returned in canonical sorted orders.
- No reliance on system clocks, unordered hash iterations, or stochastic traversals.
- Output serialization via `to_dict()` is bitwise consistent across repeated executions.

---

## 3. Graph Feature Inventory (`GraphFeatures`)

The [`GraphFeatures`](file:///D:/Team_Cipher_Unit/backend/app/engines/graph/intelligence/graph_models.py) container exposes 7 distinct metric dimensions:

| Feature Category | Field Names | Description & Mathematical Formula |
| :--- | :--- | :--- |
| **A. Degree Metrics** | `in_degree`<br>`out_degree`<br>`total_degree`<br>`unique_inbound_counterparties`<br>`unique_outbound_counterparties` | Multi-edge safe counts of incoming/outgoing transfers and unique counterparties. |
| **B. Fan-In / Fan-Out** | `unique_senders_count`<br>`unique_receivers_count`<br>`inbound_tx_count`<br>`outbound_tx_count`<br>`inbound_volume_total`<br>`outbound_volume_total`<br>`fan_in_ratio`<br>`fan_out_ratio` | Dispersion ratios representing aggregation or distribution patterns.<br>$\text{fan\_in\_ratio} = \frac{|S_{\text{senders}}|}{\max(1, N_{\text{inbound}})}$<br>$\text{fan\_out\_ratio} = \frac{|R_{\text{receivers}}|}{\max(1, N_{\text{outbound}})}$ |
| **C. Neighborhood Structure** | `neighboring_accounts_count`<br>`neighboring_devices_count`<br>`neighboring_ips_count`<br>`unique_node_count_by_type`<br>`neighborhood_density` | Heterogeneous node counts within hop cutoff $H$.<br>Density: $\min\left(1.0, \frac{\|E_{\text{unique directed pairs}}\|}{N_{\text{accounts}}(N_{\text{accounts}} - 1)}\right)$ |
| **D & E. Reachability & Paths** | `reachable_node_count`<br>`downstream_accounts`<br>`upstream_accounts`<br>`max_downstream_path_length`<br>`path_summary` | Directed BFS reachability tracing downstream layering routes and upstream fund origins up to `max_depth`. |
| **F. Circular Flow Cycles** | `has_cycle`<br>`cycle_count`<br>`cycle_lengths`<br>`cycles`<br>`contributing_cycle_nodes` | Detection of closed fund-routing loops ($A \to B \to C \to A$) returning to the focal account. |
| **G & H. Shared Entity Syndicates** | `shared_device_count`<br>`shared_ip_count`<br>`accounts_per_shared_device`<br>`accounts_per_shared_ip`<br>`associated_devices`<br>`associated_ips` | Clustering accounts that authenticate from identical hardware fingerprints or IP addresses. |
| **Explainability & Audit** | `subgraph_node_count`<br>`subgraph_edge_count`<br>`contributing_node_ids`<br>`contributing_transaction_ids`<br>`evidence_signals`<br>`explanations` | Non-subjective factual audit trails detailing transaction references, cycle nodes, and topological signals. |

---

## 4. Subgraph & Traversal Semantics

### 4.1 Configurable Hop Depth (`hops`)
- **`hops = 0`**: Evaluates only the isolated focal entity node without expanding neighbors.
- **`hops = 1`**: Evaluates immediate 1-hop counterparties, directly linked devices, and IPs.
- **`hops = 2`** *(Default)*: Expands to 2-hop counterparties and multi-account syndicates sharing identical hardware or IP addresses (e.g. Account $A \to \text{Device } D \leftarrow \text{Account } B$).
- **Boundedness**: Out-of-bounds hop parameters are clamped safely ($H \ge 0$) without infinite traversal.

### 4.2 Circular Routing Loops
- Detection traverses directed `TRANSFERRED_FUNDS` edges up to `max_depth` (default: 5).
- Cycles are normalized to start and end at the focal account (`["ACC-A", "ACC-B", "ACC-C", "ACC-A"]`).
- Multiple parallel transactions between the same accounts do not generate duplicate phantom cycles.
- Disconnected cycles in unrelated network partitions are strictly isolated and never attributed to the focal account.

---

## 5. File Structure & Component Map

The M7 implementation resides entirely under `backend/app/engines/graph/intelligence/` and `backend/tests/engines/graph/`:

```
backend/
├── app/
│   └── engines/
│       └── graph/
│           ├── __init__.py                          # Re-exports GraphIntelligenceEngine & GraphFeatures
│           ├── graph_builder.py                     # Existing Neo4j builder (UNTOUCHED)
│           ├── path_analysis.py                     # Existing Neo4j path analysis (UNTOUCHED)
│           ├── relationship_engine.py               # Existing Neo4j relationship engine (UNTOUCHED)
│           └── intelligence/                        # [M7 Package]
│               ├── __init__.py                      # Package entry point
│               ├── graph_models.py                  # GraphFeatures dataclass & serialization
│               ├── graph_metrics.py                 # Pure deterministic graph metric extractors
│               └── graph_engine.py                  # GraphIntelligenceEngine orchestrator
└── tests/
    └── engines/
        └── graph/                                   # [M7 Test Suite]
            ├── __init__.py
            ├── test_graph_fixtures.py               # Fixtures A through T (20 test scenarios)
            ├── test_graph_invariants.py             # Architectural Invariants 1 through 12
            ├── test_graph_features.py               # Model structure & JSON serialization
            ├── test_graph_cycles.py                 # Advanced cycle detection & isolation
            ├── test_graph_edge_cases.py             # Extreme amounts, bounds, concurrency
            └── test_graph_intelligence.py           # Integration workflows & factory fallback
```

---

## 6. Test Suite & Invariant Verification

Milestone 7 includes 100 dedicated automated tests validating all specified fixtures, invariants, and edge cases:

### 6.1 Test Fixtures (A through T)
- **Fixture A**: Empty graph returns zero metrics gracefully.
- **Fixture B**: Single isolated account returns 0 degrees and 0 neighbors.
- **Fixture C**: Directionality test ($A \to B$ produces $out=1$ for $A$ and $in=1$ for $B$).
- **Fixture D & E**: Multiple outbound and inbound transfer counts.
- **Fixture F & G**: Fan-in aggregation and fan-out dispersion ratios and signals.
- **Fixture H, I, J**: 2-node, 3-node, and 4-node circular loops.
- **Fixture K & L**: Shared hardware device and IP address syndicates.
- **Fixture M**: Multi-edge preservation (3 transactions between $A$ and $B \implies out\_deg=3, unique=1$).
- **Fixture N**: Disconnected components remain fully isolated.
- **Fixture O**: Hop depth progression ($0 \to 1 \to 2$ monotonicity).
- **Fixture P**: Input permutation invariance (out-of-order transaction ingestion).
- **Fixture Q**: Idempotent duplicate transaction ingestion.
- **Fixture R**: Missing optional device/IP fields handled cleanly.
- **Fixture S**: Heterogeneous graph node type partitioning.
- **Fixture T**: 50-node topology stress test executes in $<100\text{ms}$.

### 6.2 The 12 Non-Negotiable Invariants
1. **Determinism**: Identical graph state + inputs $\implies$ identical `GraphFeatures`.
2. **Directionality**: $A \to B \centernot\implies B \to A$.
3. **Unique-Counterparty Correctness**: Multi-edges do not inflate unique counterparties.
4. **Transaction-Count Correctness**: Transactions are counted individually.
5. **Hop Boundedness**: Subgraph node count increases monotonically with hop depth.
6. **Empty Graph Safety**: Non-existent entities return safe defaults without exceptions.
7. **No False Cycles**: Linear chains ($A \to B \to C$) never report circular loops.
8. **Real Cycle Detection**: True cycles ($A \to B \to C \to A$) detected with exact length.
9. **Duplicate Safety**: Duplicate transaction ingestion is idempotent.
10. **Input-Order Invariance**: Transaction arrival sequence does not alter topological metrics.
11. **Stable Serialization**: `to_dict()` outputs stable, JSON-compliant schemas.
12. **No Graph Mutation on Read**: Feature extraction does not alter nodes or edges.

---

## 7. Future Consumers

The `GraphFeatures` contract is specifically designed for downstream consumption in:
- **Milestone 8 (Tabular ML + AutoGluon)**: Graph metrics concatenated with tabular transaction features.
- **Milestone 9 (Graph ML / GraphSAGE)**: Node embedding generation and structural neighborhood pooling.
- **Milestone 10 (Risk Fusion)**: Synthesis of Rule Engine signals, Temporal Features (M6), and Graph Features (M7).
- **Milestone 12 (Investigation Copilot)**: Automated executive narrative generation for AML analysts based on topological evidence signals.
- **Milestone 15+ (Ship It / Amazon Neptune)**: Replacing `NetworkXGraphRepository` with `NeptuneGraphRepository` without changing a single line of business logic in `GraphIntelligenceEngine`.
