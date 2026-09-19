"""
MuleTrace AI — Local NetworkX Graph Repository Adapter.

Implements the domain GraphRepository port using an in-memory NetworkX MultiDiGraph.
Provides local graph intelligence, neighborhood subgraphs, multi-hop layering traces,
and circular mule cycle detection for the BUILD IT phase without requiring external
graph databases.

Architectural Boundary:
- Implements: app.domain.interfaces.GraphRepository
- Zero dependencies on Neo4j, SQLAlchemy, FastAPI, or AWS.
- Instance-isolated (no global mutable state).
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any, Optional

import networkx as nx

from app.domain.interfaces import GraphRepository
from app.domain.models import TransactionEvent

logger = logging.getLogger("app.repositories.graph_nx")


class NetworkXGraphRepository(GraphRepository):
    """In-memory graph repository implementing GraphRepository via NetworkX MultiDiGraph.

    Supports heterogeneous graph topology:
    - Node Types: Account ('account:<number>'), Device ('device:<fingerprint>'), IP ('ip:<address>')
    - Edge Types: TRANSFERRED_FUNDS (Account -> Account), USES_DEVICE (Account -> Device), USES_IP (Account -> IP)
    - Multi-Edge Support: Preserves all transactions between the same account pair using unique transaction_id keys.
    """

    def __init__(self) -> None:
        """Initialize a new isolated NetworkX MultiDiGraph instance."""
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()

    # ── Internal Identifier Helpers ────────────────────────────────────

    @staticmethod
    def _account_node_id(account_id: str) -> str:
        """Format a deterministic, collision-free account node ID."""
        acc = str(account_id).strip()
        return acc if acc.startswith("account:") else f"account:{acc}"

    @staticmethod
    def _device_node_id(device_id: str) -> str:
        """Format a deterministic, collision-free device node ID."""
        dev = str(device_id).strip()
        return dev if dev.startswith("device:") else f"device:{dev}"

    @staticmethod
    def _ip_node_id(ip_address: str) -> str:
        """Format a deterministic, collision-free IP node ID."""
        ip = str(ip_address).strip()
        return ip if ip.startswith("ip:") else f"ip:{ip}"

    @staticmethod
    def _raw_id(typed_id: str) -> str:
        """Strip type prefix for public/domain consumers."""
        for prefix in ("account:", "device:", "ip:"):
            if typed_id.startswith(prefix):
                return typed_id[len(prefix) :]
        return typed_id

    # ── GraphRepository Port Implementation ───────────────────────────

    async def add_transaction(self, event: TransactionEvent) -> None:
        """Ingest a canonical transaction event into the graph topology.

        Creates or updates sender and receiver account nodes and establishes
        a directed TRANSFERRED_FUNDS edge keyed by the transaction_id.
        Optionally links device and IP entities if present on the event.

        Args:
            event: Canonical TransactionEvent to ingest.
        """
        sender_id = self._account_node_id(event.sender_account)
        receiver_id = self._account_node_id(event.receiver_account)

        # 1. Upsert Sender Node
        if sender_id not in self.graph:
            self.graph.add_node(
                sender_id,
                type="account",
                account_number=event.sender_account,
                bank_name=event.sender_bank or "State Bank of India",
                customer_name="Account Holder",
            )
        else:
            if event.sender_bank:
                self.graph.nodes[sender_id]["bank_name"] = event.sender_bank

        # 2. Upsert Receiver Node
        if receiver_id not in self.graph:
            self.graph.add_node(
                receiver_id,
                type="account",
                account_number=event.receiver_account,
                bank_name=event.receiver_bank or "HDFC Bank",
                customer_name="Beneficiary Holder",
            )
        else:
            if event.receiver_bank:
                self.graph.nodes[receiver_id]["bank_name"] = event.receiver_bank

        # 3. Add Directed Edge (TRANSFERRED_FUNDS)
        edge_key = str(event.transaction_id)
        ts_str = (
            event.timestamp.isoformat()
            if hasattr(event.timestamp, "isoformat")
            else str(event.timestamp)
        )

        edge_attrs = {
            "relationship": "TRANSFERRED_FUNDS",
            "transaction_id": edge_key,
            "ref": edge_key,
            "amount": float(event.amount),
            "currency": event.currency,
            "channel": event.channel,
            "timestamp": ts_str,
            "sender_account": event.sender_account,
            "receiver_account": event.receiver_account,
            "narration": event.narration or "",
        }

        # MultiDiGraph.add_edge with key is idempotent: overwriting same key updates attributes
        self.graph.add_edge(sender_id, receiver_id, key=edge_key, **edge_attrs)

        # 4. Link Device if provided
        if event.device_id:
            await self.link_account_device(event.sender_account, event.device_id)

        # 5. Link IP if provided
        if event.ip_address:
            ip_node = self._ip_node_id(event.ip_address)
            if ip_node not in self.graph:
                self.graph.add_node(
                    ip_node,
                    type="ip",
                    ip_address=event.ip_address,
                )
            ip_link_key = f"ip_link:{sender_id}->{ip_node}"
            self.graph.add_edge(
                sender_id,
                ip_node,
                key=ip_link_key,
                relationship="USES_IP",
                account_id=event.sender_account,
                ip_address=event.ip_address,
            )

    async def get_subgraph(self, account_id: str, hops: int = 2) -> dict[str, Any]:
        """Retrieve the local neighborhood graph centered on an account.

        Traverses both incoming and outgoing connections up to `hops` distance.

        Args:
            account_id: Target account identifier.
            hops: Maximum traversal distance from the root account (default: 2).

        Returns:
            Dictionary with 'nodes' and 'edges' lists.
        """
        root_node = self._account_node_id(account_id)
        if root_node not in self.graph:
            return {"nodes": [], "edges": [], "account_id": account_id}

        # Traversal over undirected view to capture bidirectional relationships and linked devices
        undirected_view = self.graph.to_undirected(as_view=True)
        sub_nodes = set(
            nx.single_source_shortest_path_length(
                undirected_view, root_node, cutoff=hops
            ).keys()
        )

        nodes_list: list[dict[str, Any]] = []
        for n in sub_nodes:
            attrs = dict(self.graph.nodes[n])
            label = (
                attrs.get("account_number")
                or attrs.get("fingerprint")
                or attrs.get("ip_address")
                or self._raw_id(n)
            )
            nodes_list.append(
                {
                    "id": n,
                    "label": str(label),
                    "type": attrs.get("type", "account"),
                    **attrs,
                }
            )

        edges_list: list[dict[str, Any]] = []
        for u, v, k, data in self.graph.edges(sub_nodes, keys=True, data=True):
            if v in sub_nodes:
                edge_dict = dict(data)
                edge_dict["source"] = u
                edge_dict["target"] = v
                edge_dict["key"] = k
                edges_list.append(edge_dict)

        return {
            "nodes": nodes_list,
            "edges": edges_list,
            "account_id": account_id,
        }

    async def trace_transaction_path(
        self, transaction_id: str, max_depth: int = 5
    ) -> dict[str, Any]:
        """Trace the multi-hop fund flow path associated with a transaction.

        Finds the transaction and traces downstream funds transferred from the
        receiving account up to `max_depth` hops.

        Args:
            transaction_id: Unique transaction reference / ID.
            max_depth: Maximum path traversal depth in hops (default: 5).

        Returns:
            Dictionary with 'nodes', 'edges', and 'path_summary'.
        """
        target_tx = str(transaction_id).strip()
        matched_edge: Optional[tuple[str, str, str, dict[str, Any]]] = None

        # 1. Locate the initiating transaction edge
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            if (
                data.get("transaction_id") == target_tx
                or data.get("ref") == target_tx
                or str(k) == target_tx
            ):
                matched_edge = (u, v, k, data)
                break

        if not matched_edge:
            return {
                "nodes": [],
                "edges": [],
                "path_summary": f"Transaction {transaction_id} not found in graph.",
            }

        start_u, start_v, start_k, start_data = matched_edge
        path_edges: list[dict[str, Any]] = [
            {
                "source": start_u,
                "target": start_v,
                "key": start_k,
                **dict(start_data),
            }
        ]
        visited_nodes: set[str] = {start_u, start_v}

        # 2. Trace downstream transfers via BFS queue
        queue: deque[tuple[str, int]] = deque([(start_v, 1)])
        while queue:
            curr_acc, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for _, next_node, edge_k, edge_data in self.graph.out_edges(
                curr_acc, keys=True, data=True
            ):
                if edge_data.get("relationship") == "TRANSFERRED_FUNDS":
                    edge_dict = {
                        "source": curr_acc,
                        "target": next_node,
                        "key": edge_k,
                        **dict(edge_data),
                    }
                    if edge_dict not in path_edges:
                        path_edges.append(edge_dict)
                    if next_node not in visited_nodes:
                        visited_nodes.add(next_node)
                        queue.append((next_node, depth + 1))

        # 3. Format response nodes and edges
        nodes_list: list[dict[str, Any]] = []
        for n in visited_nodes:
            attrs = dict(self.graph.nodes.get(n, {}))
            label = attrs.get("account_number") or self._raw_id(n)
            nodes_list.append(
                {
                    "id": n,
                    "label": str(label),
                    "type": attrs.get("type", "account"),
                    **attrs,
                }
            )

        unique_accounts = {
            self._raw_id(n) for n in visited_nodes if n.startswith("account:")
        }
        hop_count = len(path_edges)

        summary = (
            f"Funds were traced across {hop_count} hops involving "
            f"{len(unique_accounts)} unique accounts. Layering detected."
        )

        return {
            "nodes": nodes_list,
            "edges": path_edges,
            "path_summary": summary,
        }

    async def find_circular_paths(
        self, start_account: str, max_depth: int = 5
    ) -> list[list[str]]:
        """Detect circular fund routing loops originating from an account.

        Traverses directed TRANSFERRED_FUNDS relationships to detect cycles
        where funds loop back to the start account within `max_depth` hops.

        Args:
            start_account: Account identifier to start cycle detection from.
            max_depth: Maximum cycle length in hops (default: 5).

        Returns:
            List of detected cycles as ordered lists of account identifiers.
        """
        root_node = self._account_node_id(start_account)
        if root_node not in self.graph:
            return []

        # Build a directed subgraph of only fund transfer edges to avoid traversing device/IP edges
        fund_edges = [
            (u, v)
            for u, v, d in self.graph.edges(data=True)
            if d.get("relationship") == "TRANSFERRED_FUNDS"
        ]
        fund_graph = nx.DiGraph(fund_edges)

        if root_node not in fund_graph:
            return []

        detected_cycles: list[list[str]] = []

        # Find all cycles from root_node returning to root_node within max_depth hops
        for neighbor in fund_graph.successors(root_node):
            if neighbor == root_node:
                # Direct self-loop (1 hop)
                raw_acc = self._raw_id(root_node)
                detected_cycles.append([raw_acc, raw_acc])
                continue

            # Look for simple paths from neighbor back to root_node within (max_depth - 1) hops
            try:
                paths_back = nx.all_simple_paths(
                    fund_graph,
                    source=neighbor,
                    target=root_node,
                    cutoff=max_depth - 1,
                )
                for path in paths_back:
                    full_cycle = [root_node] + path
                    clean_cycle = [self._raw_id(n) for n in full_cycle]
                    if clean_cycle not in detected_cycles:
                        detected_cycles.append(clean_cycle)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        return detected_cycles

    async def link_account_device(self, account_id: str, device_id: str) -> None:
        """Establish a relationship between an account and a device fingerprint.

        Links an account node to a device node via a directed USES_DEVICE edge.
        Idempotent: does not duplicate links.

        Args:
            account_id: Unique account identifier.
            device_id: Hardware fingerprint or device identifier.
        """
        acc_node = self._account_node_id(account_id)
        dev_node = self._device_node_id(device_id)

        # Upsert account node if not present
        if acc_node not in self.graph:
            self.graph.add_node(
                acc_node,
                type="account",
                account_number=str(account_id),
                bank_name="Unknown Bank",
            )

        # Upsert device node if not present
        if dev_node not in self.graph:
            self.graph.add_node(
                dev_node,
                type="device",
                fingerprint=str(device_id),
                device_id=str(device_id),
            )

        edge_key = f"link:{acc_node}->{dev_node}"
        self.graph.add_edge(
            acc_node,
            dev_node,
            key=edge_key,
            relationship="USED_DEVICE",
            account_id=str(account_id),
            device_id=str(device_id),
        )
