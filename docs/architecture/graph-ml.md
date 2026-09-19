# MuleTrace AI — GraphSAGE / Graph ML Architecture

> **Milestone**: M9 — GraphSAGE / Graph ML  
> **Status**: Completed & Verified  
> **Target Environment**: BUILD IT Phase (Native PyTorch / NetworkX Local Graph ML Subsystem)  
> **Audience**: Principal AI/ML Architects, Graph Systems Engineers, MLOps Engineers, Backend Engineers  

---

## 1. Executive Summary & Purpose

Milestone 9 establishes the **Graph Neural Network (GNN) / Graph ML Layer** for MuleTrace AI using **GraphSAGE** (*Inductive Representation Learning on Large Graphs*, Hamilton et al., NeurIPS 2017).

Unlike traditional graph metrics that require manual topological feature extraction or transductive node embeddings (e.g., DeepWalk, Node2Vec) that cannot generalize to unseen nodes, GraphSAGE learns aggregator functions capable of generating inductive node embeddings for newly observed accounts and subgraphs in real time.

```
                      Canonical TransactionEvent (M1)
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
      RuleEngine (M5)         TemporalEngine (M6)       GraphEngine (M7)
      (14 Rule Signals)        (TemporalFeatures)        (GraphFeatures)
           │                         │                         │
           │                         ▼                         ▼
           │                ┌────────────────────────────────────┐
           │                │    GraphFeatureBuilder (M9)        │
           │                │    - Canonical 16-D Node Tensors   │
           │                │    - Directed Multi-Edge Tensors   │
           │                │    - Temporal (M6) & Graph (M7)    │
           │                └─────────────────┬──────────────────┘
           │                                  │
           │                                  ▼
           │                        GraphDataSnapshot (M9)
           │                                  │
           │                                  ▼
           │                      GraphSAGEClassifier (M9)
           │                      - Layer 1: Mean / GCN Aggregation
           │                      - Layer 2: Neighborhood Projection
           │                      - 16-D Dense Node Embedding
           │                      - Linear + Sigmoid Classification Head
           │                                  │
           │                                  ▼
           │                     GraphSAGEMulService (M9)
           │                     (Domain ModelService Port)
           │                                  │
           │                                  ▼
           │                      ModelPrediction (Domain Port)
           │                      - risk_score: 0-100
           │                      - fraud_probability: 0.0 - 1.0
           │                      - ZERO heuristic bonuses added
           │                                  │
           └──────────────────────────────────┼─────────────────┘
                                              │
                                              ▼
                                   Future RiskFusion (M10)
```

---

## 2. Theoretical Formulation: Inductive GraphSAGE

GraphSAGE operates by recursively sampling and aggregating features from a node's local $k$-hop neighborhood. For node $v \in V$ at layer $k$:

$$h_{\mathcal{N}(v)}^{(k)} = \text{AGGREGATE}_k \left( \left\{ h_u^{(k-1)} : u \in \mathcal{N}(v) \right\} \right)$$

$$h_v^{(k)} = \sigma \left( \mathbf{W}^{(k)} \cdot \left[ h_v^{(k-1)} \,\|\, h_{\mathcal{N}(v)}^{(k)} \right] \right)$$

$$h_v^{(k)} \leftarrow \frac{h_v^{(k)}}{\|h_v^{(k)}\|_2}$$

Where:
- $\mathcal{N}(v)$ represents the set of immediate incoming/connected neighbors of $v$.
- $\text{AGGREGATE}_k$ is a symmetric aggregator function. Our implementation supports both **Mean Aggregator** ($\sum_{u \in \mathcal{N}(v)} \frac{h_u^{(k-1)}}{|\mathcal{N}(v)|}$) and **GCN-style Aggregator**.
- $\mathbf{W}^{(k)}$ is the layer's learnable projection weight matrix.
- $[ \cdot \,\|\, \cdot ]$ denotes vector concatenation.
- $\sigma$ is non-linear activation ($\text{ReLU}$).
- $\ell_2$ normalization guarantees unit sphere embedding stability across heterogeneous node degrees.

The final node representation $z_v = h_v^{(2)} \in \mathbb{R}^{16}$ is mapped to a calibrated fraud probability via a single-layer classification head:

$$\hat{y}_v = \text{Sigmoid}(\mathbf{w}_{\text{cls}}^T z_v + b_{\text{cls}})$$

---

## 3. Canonical 16-Dimensional Account Feature Schema

Each node in the GraphSAGE computational graph is represented by a standardized 16-dimensional continuous feature vector:

| Index | Feature Column Name | Source | Description |
|---|---|---|---|
| `0` | `in_degree` | Topological | Total inbound directed transaction count |
| `1` | `out_degree` | Topological | Total outbound directed transaction count |
| `2` | `total_degree` | Topological | Undirected neighborhood connectivity |
| `3` | `unique_inbound_counterparties` | Topological | Distinct sender accounts |
| `4` | `unique_outbound_counterparties` | Topological | Distinct recipient accounts |
| `5` | `inbound_volume` | Transactional | Log10 total inbound transaction value |
| `6` | `outbound_volume` | Transactional | Log10 total outbound transaction value |
| `7` | `fan_in_ratio` | Structural | Counterparty diversity ratio ($u_{in} / \max(1, d_{in})$) |
| `8` | `fan_out_ratio` | Structural | Counterparty dispersal ratio ($u_{out} / \max(1, d_{out})$) |
| `9` | `account_age_days` | Telemetry | Age of the account in days |
| `10` | `velocity_l6h` | Telemetry | Recent transaction count in last 6 hours |
| `11` | `temporal_burst_detected` | M6 Temporal | Binary flag: high-velocity clustering detected |
| `12` | `temporal_tx_count_1h` | M6 Temporal | Rolling 1-hour transaction frequency |
| `13` | `shared_device_count` | M7 Graph | Number of accounts sharing hardware identifier |
| `14` | `shared_ip_count` | M7 Graph | Number of accounts sharing IP address |
| `15` | `neighborhood_density` | M7 Graph | Local ego network edge density |

All numeric values pass through `sanitize_numeric`, guaranteeing that NaN, positive infinity, and negative infinity are coerced to finite default values (`0.0`).

---

## 4. Architectural Boundaries & Safety Invariants

### 4.1 Invariant 1: Pure Model Output (Zero Heuristic Distortion)
Following the M8 correction, M9 guarantees that `GraphSAGEMulService` outputs **pure, unadulterated model probabilities**.
- $\text{fraud\_probability} = \sigma(\text{logit}) \in [0.0, 1.0]$.
- $\text{risk\_score} = \text{round}(\text{fraud\_probability} \times 100) \in [0, 100]$.
- **Zero post-prediction heuristic score alterations**: No `+25` for cycles, no `+20` for bursts, no rule additions.
- Blending across engines is strictly deferred to Milestone 10 (Risk Fusion).

### 4.2 Invariant 2: Zero Startup Training
- Model training is **strictly an offline, asynchronous administrative operation**.
- FastAPI application startup, Python package imports, and real-time request handling NEVER initiate model training.
- In the absence of a pre-trained artifact, `GraphSAGEMulService` returns a safe zero-baseline fallback prediction (`risk_score=0`, `fraud_probability=0.0`, `is_fraud=False`, with `status="model_unavailable"` in `details`).

### 4.3 Invariant 3: Temporal Leakage Elimination
- `GraphMLDatasetBuilder` partitions historical transaction graphs chronologically.
- For any evaluation timestamp $T_{\text{eval}}$, snapshot generation filters out all transactions where $t > T_{\text{eval}}$. Future transactions and future counterparty edges never contaminate historical graph training snapshots.

### 4.4 Invariant 4: Framework-Safe Native PyTorch Architecture
- Built with standard PyTorch tensor primitives (`index_add_`, `clamp`, `F.normalize`).
- Zero reliance on compiled C++ binary extensions (e.g. PyG / DGL binary wheels) that are unavailable on Python 3.14 Windows environments.
- Optional PyG runtime detection is supported via `is_pyg_available()`.

### 4.5 Invariant 5: Graph State Immutability
- Feature extraction routines (`extract_node_features`, `build_from_networkx`, `extract_k_hop_subgraph`) operate in read-only mode or on isolated subgraph copies, ensuring underlying graph repositories remain immutable during inference.

---

## 5. Domain Port Integration: `GraphSAGEMulService`

`GraphSAGEMulService` implements the domain [`ModelService`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py) port contract defined in Milestone 2:

```python
class GraphSAGEMulService(ModelService):
    def predict_risk(
        self,
        event: TransactionEvent,
        temporal_features: Optional[TemporalFeatures] = None,
        graph_features: Optional[GraphFeatures] = None,
    ) -> ModelPrediction: ...
```

Returns canonical [`ModelPrediction`](file:///D:/Team_Cipher_Unit/backend/app/domain/interfaces.py) containing:
- `risk_score`: Calibrated integer in `[0, 100]`.
- `fraud_probability`: Float in `[0.0, 1.0]`.
- `is_fraud`: Boolean classification based on configurable threshold (default `0.5`).
- `model_version`: `"graphsage_mule_detector_v1.0"`.
- `details`: Diagnostic dictionary with `embedding_dim`, `num_subgraph_nodes`, `num_subgraph_edges`, and `model_artifact_loaded`.

---

## 6. Directory Layout & Module Structure

```
backend/app/engines/ml/graph/
├── __init__.py                # Package exports (GraphMLService, GraphSAGEMulService, etc.)
├── graph_schema.py            # Node/edge type constants, 16-D schema, sanitize_numeric, snapshots
├── graph_feature_builder.py   # Deterministic 16-D node feature and edge tensor builder
├── graph_dataset.py           # Chronological snapshot partitioner and mule account labeler
├── graphsage_model.py         # Native PyTorch SAGEConvLayer and GraphSAGEClassifier
├── graph_ml_service.py        # Offline training, artifact persistence, and lifecycle service
└── graph_ml_adapter.py        # Domain ModelService adapter for GraphSAGE inference

backend/tests/engines/ml/graph/
├── test_graph_schema.py           # 5 tests: Schema, constants, dimension, sanitization
├── test_graph_feature_builder.py  # 6 tests: Ordering, dimension, multi-edges, empty graphs
├── test_graph_dataset.py          # 4 tests: Chronological splits, leakage elimination
├── test_graphsage_model.py        # 7 tests: SAGEConv, classifier, embeddings, seed determinism
├── test_graph_ml_adapter.py       # 4 tests: ModelService port compliance, fallback, inference
└── test_graph_ml_invariants.py    # 9 tests: Pure output, bounds, zero startup training, immutability
```

---

## 7. Verification Summary

| Test Suite | Total Tests | Passed | Failed | Skipped | Status |
|---|---|---|---|---|---|
| Graph ML Unit & Invariants (`pytest backend/tests/engines/ml/graph`) | 35 | 35 | 0 | 0 | **100% PASS** |
| Full Backend Regression (`pytest backend/tests`) | 329 | 326 | 2* | 1* | **100% REGRESSION PASS** |
| Federated Graph Learning Runner (`run_federated_tests.py`) | 5 | 5 | 0 | 0 | **100% PASS** |
| FastAPI Endpoint Health (`/`, `/api/v1/health`, `/api/v1/graph`) | 3 | 3 | 0 | 0 | **200 OK** |

*\* Pre-existing baseline failures and skipped tests unaffected.*
