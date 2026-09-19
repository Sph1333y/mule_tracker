# MuleTrace AI — Local NetworkX Graph Repository Adapter Specification

## 1. Purpose

`NetworkXGraphRepository` is a local, in-memory graph repository adapter implementing the canonical [`GraphRepository`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py#L42-L125) domain interface using NetworkX.

It enables local topology storage, community subgraphs, multi-hop layering traces, and circular mule cycle detection without requiring an external database cluster (such as Neo4j or Amazon Neptune).

> **Architectural Boundary Statement**:
> "NetworkXGraphRepository is introduced as a local BUILD IT adapter.
> The existing Neo4j implementation remains the current application
> graph implementation and is not replaced in Milestone 3."

---

## 2. Why NetworkX Exists in BUILD IT

In the hackathon **BUILD IT** phase:
- Development, developer environments, CI pipelines, and unit tests must run fully offline and locally without mandatory external database dependencies.
- NetworkX is a pure Python, high-performance graph algorithms library that runs entirely in-memory with zero network overhead and zero cloud cost.
- NetworkX provides standard implementations of shortest path algorithms, cycle detection, and topological subgraphs, perfectly matching the domain requirements of money-mule detection.

In the future **SHIP IT** phase:
- The exact same domain interface (`GraphRepository`) will be implemented by `NeptuneGraphRepository` to connect to Amazon Neptune.
- Business logic remains 100% cloud-agnostic.

---

## 3. Relationship to `GraphRepository`

`NetworkXGraphRepository` inherits directly from [`app.domain.interfaces.GraphRepository`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py#L42-L125) and satisfies all 5 abstract methods:

```
                  GraphRepository (Domain Port)
                               ▲
                               │ implements
                    NetworkXGraphRepository (M3 Adapter)
                               │ wraps
                      nx.MultiDiGraph (In-Memory)
```

Methods implemented:
1. `async def add_transaction(self, event: TransactionEvent) -> None`
2. `async def get_subgraph(self, account_id: str, hops: int = 2) -> dict[str, Any]`
3. `async def trace_transaction_path(self, transaction_id: str, max_depth: int = 5) -> dict[str, Any]`
4. `async def find_circular_paths(self, start_account: str, max_depth: int = 5) -> list[list[str]]`
5. `async def link_account_device(self, account_id: str, device_id: str) -> None`

---

## 4. Graph Type Selected: `nx.MultiDiGraph`

`NetworkXGraphRepository` uses `nx.MultiDiGraph` as its underlying data structure.

### Rationale:
1. **Directed (`DiGraph`)**: Financial transactions are directional flows of capital from a sender account to a receiver account ($A \rightarrow B$). Device linkages are also directional ($A \xrightarrow{\text{USED\_DEVICE}} D$).
2. **Multi-Edge Support (`MultiGraph`)**: Multiple financial transactions frequently occur between the same pair of accounts over time (e.g., structuring or smurfing). In a standard `nx.DiGraph`, adding a second transaction from $A$ to $B$ would overwrite the edge attributes of the previous transaction. `nx.MultiDiGraph` assigns a distinct key to each edge, enabling complete preservation of all individual transaction events.

---

## 5. Node ID Strategy (Typed Identifiers)

To prevent identifier collisions across heterogeneous entity types (INVARIANT 2), all node IDs use deterministic type prefixes:

| Entity Type | Prefix Format | Example |
| :--- | :--- | :--- |
| **Account** | `account:<account_number>` | `account:ACC-987654` |
| **Device** | `device:<fingerprint>` | `device:DEV-HW-ANDROID-01` |
| **IP Address** | `ip:<ip_address>` | `ip:192.168.1.15` |

Consumers receiving subgraph data receive both the qualified ID (`id: "account:123"`) and raw labels (`label: "123"`), preventing any breaking change in downstream visualization.

---

## 6. Node Types

1. **Account Node** (`type: "account"`):
   - `account_number`: String account identifier.
   - `bank_name`: Originating or beneficiary bank name.
   - `customer_name`: Account holder designation.
2. **Device Node** (`type: "device"`):
   - `fingerprint`: Hardware or browser fingerprint string.
   - `device_id`: Device identifier.
3. **IP Node** (`type: "ip"`):
   - `ip_address`: IPv4/IPv6 address string.

---

## 7. Edge Types

1. **`TRANSFERRED_FUNDS`** (Account $\rightarrow$ Account):
   - Key: `event.transaction_id`
   - Attributes: `amount`, `currency`, `channel`, `timestamp`, `ref`, `narration`.
2. **`USED_DEVICE`** (Account $\rightarrow$ Device):
   - Key: `link:account:<acc>->device:<dev>`
   - Attributes: `relationship`, `account_id`, `device_id`.
3. **`USES_IP`** (Account $\rightarrow$ IP):
   - Key: `ip_link:account:<acc>->ip:<ip>`
   - Attributes: `relationship`, `account_id`, `ip_address`.

---

## 8. Transaction Representation & Multi-Transaction Handling

Incoming transactions arrive as canonical [`TransactionEvent`](file:///D:/Team_Cipher_Unit/backend/app/domain/models.py) objects.
- Each transaction creates a directed edge whose key is strictly `event.transaction_id`.
- If 10 separate transactions occur between `ACC-A` and `ACC-B`, exactly 10 distinct edges are maintained under `repo.graph.get_edge_data("account:ACC-A", "account:ACC-B")`.
- Transaction amounts, timestamps, channels, and references are preserved without loss or aggregation.

---

## 9. Subgraph Behavior

`get_subgraph(account_id, hops=2)`:
- Locates the root account `account:<account_id>`.
- Generates an undirected view (`self.graph.to_undirected(as_view=True)`) to find all connected neighbors (transfers in, transfers out, linked devices, linked IPs) within `hops` distance using single-source shortest path traversal.
- Returns induced subgraph with formatted node and edge lists matching the existing SOC visualization format.
- Purely read-only; does not mutate internal graph state.

---

## 10. Path Behavior (Layering Trace)

`trace_transaction_path(transaction_id, max_depth=5)`:
- Finds the initiating edge matching `transaction_id`.
- Follows downstream `TRANSFERRED_FUNDS` transfers originating from the receiving account using breadth-first traversal up to `max_depth` hops.
- Produces a summary:
  `"Funds were traced across N hops involving M unique accounts. Layering detected."` (matching existing API format).

---

## 11. Cycle Behavior (Circular Mule Routing)

`find_circular_paths(start_account, max_depth=5)`:
- Builds a filtered directed graph containing strictly `TRANSFERRED_FUNDS` edges (excluding device/IP linkages).
- Uses `nx.all_simple_paths` from successors back to the root node with cutoff `max_depth - 1`.
- Identifies genuine circular money routes (e.g. $A \rightarrow B \rightarrow C \rightarrow A$).
- Linear paths (e.g. $A \rightarrow B \rightarrow C$) are strictly rejected (zero false positives).

---

## 12. Idempotency & Lifecycle

- **Idempotent Inserts**: Inserting the exact same `TransactionEvent` multiple times updates edge attributes in-place using the unique key. No duplicate edges or orphaned nodes are created.
- **Instance Isolation**: Every instance of `NetworkXGraphRepository` initializes its own private `self.graph`. There is zero global mutable state.

---

## 13. Current Neo4j Relationship & Why Neo4j Was NOT Removed

1. **Zero Production Flow Disruption**: The active application runtime (FastAPI routes in `app/api/v1/graph.py`, `graph_builder.py`, `path_analysis.py`) continues to use Neo4j directly.
2. **Backward Compatibility**: Production Docker containers, seed scripts, and existing dashboards remain fully functional.
3. **Decoupled Evolution**: NetworkX is an independent adapter ready to be wired into dependency injection in a future milestone when repository-based routing is established.

---

## 14. Future Neptune Adapter Mapping (Hackathon Dual-Phase)

| Capability | Local Adapter (BUILD IT) | Cloud Adapter (SHIP IT) |
| :--- | :--- | :--- |
| **Port** | `GraphRepository` | `GraphRepository` |
| **Implementation** | `NetworkXGraphRepository` | `NeptuneGraphRepository` |
| **Execution** | Local Python in-memory | Amazon Neptune Cluster (openCypher / Gremlin) |
| **Dependencies** | `networkx` | `boto3` / `gremlinpython` |
| **Storage** | Ephemeral RAM | AWS Managed NVMe Multi-AZ |
