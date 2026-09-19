"""
MuleTrace AI — Graph ML Feature Builder.

Extracts, normalizes, and constructs deterministic node features and edge indices
from graph repositories, subgraphs, and transaction networks for GraphSAGE.

Architectural Boundary:
- Consumes GraphRepository (M2/M3/M4) and GraphFeatures (M7) as domain clients.
- 100% deterministic node ordering and edge indexing.
- Zero external heuristic score adjustments.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional
import networkx as nx
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore
    TORCH_AVAILABLE = False

from app.domain.interfaces import GraphRepository
from app.engines.ml.graph.graph_schema import (
    ACCOUNT_NODE_FEATURE_COLUMNS,
    EDGE_TYPE_DEVICE,
    EDGE_TYPE_IP,
    EDGE_TYPE_TRANSFER,
    NODE_FEATURE_DIM,
    NODE_TYPE_ACCOUNT,
    NODE_TYPE_DEVICE,
    NODE_TYPE_IP,
    GraphDataSnapshot,
    NodeFeatureVector,
    sanitize_numeric,
)
from app.engines.temporal.temporal_models import TemporalFeatures
from app.engines.graph.intelligence.graph_models import GraphFeatures

logger = logging.getLogger("app.engines.ml.graph.graph_feature_builder")


class GraphFeatureBuilder:
    """Deterministic extractor converting graph topologies into GraphSAGE input tensors."""

    @staticmethod
    def _normalize_node_id(node_id: str) -> str:
        """Format an account node ID with canonical prefix."""
        nid = str(node_id).strip()
        if nid.startswith("account:") or nid.startswith("device:") or nid.startswith("ip:"):
            return nid
        return f"account:{nid}"

    def build_from_networkx(
        self,
        G: nx.MultiDiGraph,
        temporal_context: Optional[dict[str, TemporalFeatures]] = None,
        graph_context: Optional[dict[str, GraphFeatures]] = None,
        node_labels: Optional[dict[str, float]] = None,
    ) -> GraphDataSnapshot:
        """Convert a NetworkX MultiDiGraph into a deterministic GraphDataSnapshot.

        Args:
            G: MultiDiGraph containing heterogeneous accounts, devices, and IPs.
            temporal_context: Optional map of account_id -> TemporalFeatures (M6).
            graph_context: Optional map of account_id -> GraphFeatures (M7).
            node_labels: Optional ground-truth fraud labels (account_id -> 0.0 or 1.0).

        Returns:
            GraphDataSnapshot with deterministic node indices, features, and edges.
        """
        temporal_context = temporal_context or {}
        graph_context = graph_context or {}
        node_labels = node_labels or {}

        # 1. Deterministic Node Ordering (Lexicographically sorted)
        sorted_nodes = sorted(list(G.nodes()))
        node_to_idx = {nid: i for i, nid in enumerate(sorted_nodes)}
        node_type_map = {}

        feature_matrix: list[list[float]] = []
        labels_list: list[float] = []

        for nid in sorted_nodes:
            attrs = G.nodes[nid]
            ntype = attrs.get("type", NODE_TYPE_ACCOUNT)
            if nid.startswith("device:"):
                ntype = NODE_TYPE_DEVICE
            elif nid.startswith("ip:"):
                ntype = NODE_TYPE_IP
            node_type_map[nid] = ntype

            # Extract 16-D feature vector based on node type
            if ntype == NODE_TYPE_ACCOUNT:
                feat = self._extract_account_node_features(
                    G=G,
                    node_id=nid,
                    node_attrs=attrs,
                    temp_feat=temporal_context.get(nid) or temporal_context.get(nid.replace("account:", "")),
                    m7_feat=graph_context.get(nid) or graph_context.get(nid.replace("account:", "")),
                )
            elif ntype == NODE_TYPE_DEVICE:
                feat = self._extract_device_node_features(G, nid)
            else:
                feat = self._extract_ip_node_features(G, nid)

            feature_matrix.append(feat)

            # Node label mapping (if available, e.g. for supervised classification)
            lbl = node_labels.get(nid, node_labels.get(nid.replace("account:", ""), -1.0))
            labels_list.append(float(lbl))

        # 2. Deterministic Directed Edge Index Construction
        sorted_edges = sorted(list(G.edges(keys=True, data=True)), key=lambda e: (str(e[0]), str(e[1]), str(e[2])))
        src_indices: list[int] = []
        dst_indices: list[int] = []
        edge_attr_list: list[list[float]] = []

        for u, v, k, data in sorted_edges:
            if u in node_to_idx and v in node_to_idx:
                src_indices.append(node_to_idx[u])
                dst_indices.append(node_to_idx[v])
                # Edge features: [log_amount, is_transfer, is_device, is_ip]
                amt = sanitize_numeric(data.get("amount", 0.0))
                log_amt = math.log10(amt + 1.0) if amt > 0 else 0.0
                rel = data.get("relationship", EDGE_TYPE_TRANSFER)
                is_trans = 1.0 if rel == EDGE_TYPE_TRANSFER else 0.0
                is_dev = 1.0 if rel == EDGE_TYPE_DEVICE else 0.0
                is_ip = 1.0 if rel == EDGE_TYPE_IP else 0.0
                edge_attr_list.append([round(log_amt, 4), is_trans, is_dev, is_ip])

        # Convert to PyTorch tensors if torch is available, else numpy arrays
        if TORCH_AVAILABLE:
            x_tensor = torch.tensor(feature_matrix, dtype=torch.float32) if feature_matrix else torch.zeros((0, NODE_FEATURE_DIM), dtype=torch.float32)
            edge_index_tensor = (
                torch.tensor([src_indices, dst_indices], dtype=torch.long)
                if src_indices
                else torch.zeros((2, 0), dtype=torch.long)
            )
            y_tensor = torch.tensor(labels_list, dtype=torch.float32) if labels_list else None
            edge_attr_tensor = torch.tensor(edge_attr_list, dtype=torch.float32) if edge_attr_list else None
        else:
            x_tensor = np.array(feature_matrix, dtype=np.float32) if feature_matrix else np.zeros((0, NODE_FEATURE_DIM), dtype=np.float32)
            edge_index_tensor = (
                np.array([src_indices, dst_indices], dtype=np.int64)
                if src_indices
                else np.zeros((2, 0), dtype=np.int64)
            )
            y_tensor = np.array(labels_list, dtype=np.float32) if labels_list else None
            edge_attr_tensor = np.array(edge_attr_list, dtype=np.float32) if edge_attr_list else None

        return GraphDataSnapshot(
            node_ids=sorted_nodes,
            node_to_idx=node_to_idx,
            node_type_map=node_type_map,
            x=x_tensor,
            edge_index=edge_index_tensor,
            y=y_tensor,
            edge_attr=edge_attr_tensor,
            metadata={
                "num_nodes": len(sorted_nodes),
                "num_edges": len(src_indices),
                "account_nodes": sum(1 for t in node_type_map.values() if t == NODE_TYPE_ACCOUNT),
                "device_nodes": sum(1 for t in node_type_map.values() if t == NODE_TYPE_DEVICE),
                "ip_nodes": sum(1 for t in node_type_map.values() if t == NODE_TYPE_IP),
            },
        )

    def _extract_account_node_features(
        self,
        G: nx.MultiDiGraph,
        node_id: str,
        node_attrs: dict[str, Any],
        temp_feat: Optional[TemporalFeatures] = None,
        m7_feat: Optional[GraphFeatures] = None,
    ) -> list[float]:
        """Extract canonical 16-dimensional node feature vector for an account."""
        in_deg = float(G.in_degree(node_id))
        out_deg = float(G.out_degree(node_id))
        tot_deg = in_deg + out_deg

        # Unique counterparties & volumes
        in_senders = set()
        in_vol = 0.0
        for u, _, data in G.in_edges(node_id, data=True):
            if data.get("relationship") == EDGE_TYPE_TRANSFER:
                in_senders.add(u)
                in_vol += sanitize_numeric(data.get("amount", 0.0))

        out_receivers = set()
        out_vol = 0.0
        shared_devices = 0.0
        shared_ips = 0.0
        for _, v, data in G.out_edges(node_id, data=True):
            rel = data.get("relationship", EDGE_TYPE_TRANSFER)
            if rel == EDGE_TYPE_TRANSFER:
                out_receivers.add(v)
                out_vol += sanitize_numeric(data.get("amount", 0.0))
            elif rel == EDGE_TYPE_DEVICE:
                shared_devices += 1.0
            elif rel == EDGE_TYPE_IP:
                shared_ips += 1.0

        u_in = float(len(in_senders))
        u_out = float(len(out_receivers))
        fan_in_r = u_in / max(1.0, in_deg)
        fan_out_r = u_out / max(1.0, out_deg)

        log_in_vol = math.log10(in_vol + 1.0) if in_vol > 0 else 0.0
        log_out_vol = math.log10(out_vol + 1.0) if out_vol > 0 else 0.0

        # Account telemetry attributes
        acc_age = sanitize_numeric(node_attrs.get("account_age_days"), default=180.0)
        velocity = sanitize_numeric(node_attrs.get("velocity_l6h"), default=1.0)

        # M6 Temporal features if available
        t_burst = 1.0 if (temp_feat and temp_feat.burst_detected) else 0.0
        t_cnt_1h = sanitize_numeric(temp_feat.transaction_count_1h) if temp_feat else 0.0

        # M7 Graph metrics if available
        if m7_feat:
            shared_devices = max(shared_devices, float(m7_feat.shared_device_count))
            shared_ips = max(shared_ips, float(m7_feat.shared_ip_count))
            density = sanitize_numeric(m7_feat.neighborhood_density)
        else:
            density = 0.0

        vec = [
            in_deg,
            out_deg,
            tot_deg,
            u_in,
            u_out,
            round(log_in_vol, 4),
            round(log_out_vol, 4),
            round(fan_in_r, 4),
            round(fan_out_r, 4),
            acc_age,
            velocity,
            t_burst,
            t_cnt_1h,
            shared_devices,
            shared_ips,
            round(density, 4),
        ]
        return [sanitize_numeric(v) for v in vec]

    def _extract_device_node_features(self, G: nx.MultiDiGraph, node_id: str) -> list[float]:
        """Project device node features to canonical 16-D space."""
        linked_accounts = float(G.in_degree(node_id))
        vec = [0.0] * NODE_FEATURE_DIM
        vec[0] = linked_accounts  # in_degree equivalent
        vec[13] = 1.0  # is_device flag at index 13
        return vec

    def _extract_ip_node_features(self, G: nx.MultiDiGraph, node_id: str) -> list[float]:
        """Project IP node features to canonical 16-D space."""
        linked_accounts = float(G.in_degree(node_id))
        vec = [0.0] * NODE_FEATURE_DIM
        vec[0] = linked_accounts  # in_degree equivalent
        vec[14] = 1.0  # is_ip flag at index 14
        return vec

    async def build_from_subgraph(
        self,
        account_id: str,
        repository: GraphRepository,
        hops: int = 2,
    ) -> GraphDataSnapshot:
        """Extract a k-hop neighborhood from GraphRepository and build a GraphDataSnapshot."""
        subgraph_dict = await repository.get_subgraph(account_id=account_id, hops=hops)
        G = nx.MultiDiGraph()

        for n in subgraph_dict.get("nodes", []):
            nid = n.get("id")
            if nid:
                G.add_node(nid, **n)

        for e in subgraph_dict.get("edges", []):
            src = e.get("source") or e.get("from")
            dst = e.get("target") or e.get("to")
            if src and dst:
                key = str(e.get("transaction_id") or e.get("id") or f"{src}->{dst}")
                G.add_edge(src, dst, key=key, **e)

        # Ensure root account is in graph even if isolated
        norm_acc = self._normalize_node_id(account_id)
        if norm_acc not in G:
            G.add_node(norm_acc, type=NODE_TYPE_ACCOUNT, account_number=account_id)

        return self.build_from_networkx(G)

    def extract_node_features(
        self,
        G: nx.MultiDiGraph,
        node_id: str,
        temp_feat: Optional[TemporalFeatures] = None,
        m7_feat: Optional[GraphFeatures] = None,
    ) -> NodeFeatureVector:
        """Extract strongly typed 16-D feature vector for a specific node in a graph."""
        norm_id = self._normalize_node_id(node_id)
        if norm_id not in G:
            zeros = [0.0] * NODE_FEATURE_DIM
            return NodeFeatureVector(
                node_id=norm_id,
                node_type=NODE_TYPE_ACCOUNT,
                features=zeros,
                dim=NODE_FEATURE_DIM,
            )

        node_attrs = dict(G.nodes[norm_id])
        node_type = node_attrs.get("type") or (
            NODE_TYPE_DEVICE if norm_id.startswith("device:") else (
                NODE_TYPE_IP if norm_id.startswith("ip:") else NODE_TYPE_ACCOUNT
            )
        )
        if node_type == NODE_TYPE_DEVICE:
            raw_vec = self._extract_device_node_features(G, norm_id)
        elif node_type == NODE_TYPE_IP:
            raw_vec = self._extract_ip_node_features(G, norm_id)
        else:
            raw_vec = self._extract_account_node_features(G, norm_id, node_attrs, temp_feat, m7_feat)

        return NodeFeatureVector(
            node_id=norm_id,
            node_type=node_type,
            features=raw_vec,
            dim=len(raw_vec),
        )

    def extract_k_hop_subgraph(
        self,
        G: nx.MultiDiGraph,
        center_node: str,
        k: int = 2,
    ) -> nx.MultiDiGraph:
        """Extract an undirected k-hop ego subgraph around center_node without mutating G."""
        norm_id = self._normalize_node_id(center_node)
        if norm_id not in G:
            sub = nx.MultiDiGraph()
            sub.add_node(norm_id, type=NODE_TYPE_ACCOUNT)
            return sub

        nodes = {norm_id}
        current_layer = {norm_id}
        undirected_view = G.to_undirected(as_view=True)
        for _ in range(k):
            next_layer = set()
            for node in current_layer:
                if node in undirected_view:
                    next_layer.update(undirected_view.neighbors(node))
            next_layer.difference_update(nodes)
            nodes.update(next_layer)
            current_layer = next_layer

        return G.subgraph(nodes).copy()


# Singleton instance
graph_feature_builder = GraphFeatureBuilder()
