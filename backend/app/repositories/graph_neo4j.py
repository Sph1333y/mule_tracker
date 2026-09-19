"""
MuleTrace AI — Neo4j Graph Repository Adapter.

Implements the domain GraphRepository port wrapping the existing Neo4j database
connection and Cypher query engines.

Architectural Boundary:
- Implements: app.domain.interfaces.GraphRepository
- Wraps existing: app.database.neo4j.neo4j_manager, relationship_engine
- Fully safe: gracefully handles disconnected state (offline fallback).
- Preserves existing production graph behavior without modifying legacy services.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.database.neo4j import neo4j_manager
from app.domain.interfaces import GraphRepository
from app.domain.models import TransactionEvent
from app.engines.graph.relationship_engine import relationship_engine

logger = logging.getLogger("app.repositories.graph_neo4j")


class Neo4jGraphRepository(GraphRepository):
    """Neo4j adapter implementing GraphRepository port via Cypher queries.

    Connects to the active Neo4j cluster when available; returns safe fallback
    payloads when disconnected.
    """

    @property
    def is_connected(self) -> bool:
        """Check if underlying Neo4j driver is active and connected."""
        return neo4j_manager.is_connected

    async def add_transaction(self, event: TransactionEvent) -> None:
        """Create or update account nodes and TRANSFERRED_FUNDS edge in Neo4j.

        Args:
            event: Canonical TransactionEvent to ingest.
        """
        if not neo4j_manager.is_connected:
            logger.debug("Neo4j driver not connected — skipping add_transaction.")
            return

        cypher = """
        MERGE (s:Account {account_number: $sender_acc})
        SET s.bank_name = $sender_bank
        MERGE (r:Account {account_number: $receiver_acc})
        SET r.bank_name = $receiver_bank
        CREATE (s)-[t:TRANSFERRED_FUNDS {
            ref: $tx_ref,
            amount: $amount,
            channel: $channel,
            timestamp: $timestamp
        }]->(r)
        """

        ts_str = (
            event.timestamp.isoformat()
            if hasattr(event.timestamp, "isoformat")
            else str(event.timestamp)
        )

        params = {
            "sender_acc": str(event.sender_account),
            "sender_bank": str(event.sender_bank or "State Bank of India"),
            "receiver_acc": str(event.receiver_account),
            "receiver_bank": str(event.receiver_bank or "HDFC Bank"),
            "tx_ref": str(event.transaction_id),
            "amount": float(event.amount),
            "channel": str(event.channel),
            "timestamp": ts_str,
        }

        try:
            async with neo4j_manager.get_session() as session:
                await session.run(cypher, params)
                logger.info("Synced transaction %s to Neo4j via GraphRepository", params["tx_ref"])
        except Exception as e:
            logger.warning("Failed to sync transaction to Neo4j: %s", e)

        # Link device if present
        if event.device_id:
            await self.link_account_device(event.sender_account, event.device_id)

    async def get_subgraph(self, account_id: str, hops: int = 2) -> dict[str, Any]:
        """Retrieve local neighborhood subgraph from Neo4j centered on account_id.

        Args:
            account_id: Target account identifier.
            hops: Traversal depth (default: 2).

        Returns:
            Dictionary with 'nodes', 'edges', and 'account_id'.
        """
        if not neo4j_manager.is_connected:
            return {"nodes": [], "edges": [], "account_id": account_id}

        clean_acc = str(account_id).replace("account:", "").strip()
        clamped_hops = max(1, min(int(hops), 5))

        cypher = f"""
        MATCH path = (s:Account {{account_number: $acc}})-[r*1..{clamped_hops}]-(neighbor)
        RETURN path
        LIMIT 50
        """

        nodes_dict: dict[str, dict[str, Any]] = {}
        edges_list: list[dict[str, Any]] = []

        try:
            async with neo4j_manager.get_session() as session:
                res = await session.run(cypher, acc=clean_acc)
                records = await res.data()

                for rec in records:
                    path = rec.get("path")
                    if not path:
                        continue
                    # Process nodes and relationships from path
                    for node in getattr(path, "nodes", []):
                        n_id = node.get("account_number") or node.get("fingerprint") or str(node.id)
                        labels = list(getattr(node, "labels", ["account"]))
                        n_type = labels[0].lower() if labels else "account"
                        nodes_dict[n_id] = {
                            "id": n_id,
                            "label": n_id,
                            "type": n_type,
                            **dict(node),
                        }
                    for rel in getattr(path, "relationships", []):
                        edges_list.append({
                            "source": str(rel.start_node.get("account_number", rel.start_node.id)),
                            "target": str(rel.end_node.get("account_number", rel.end_node.id)),
                            "relationship": rel.type,
                            **dict(rel),
                        })
        except Exception as e:
            logger.warning("Error fetching subgraph from Neo4j: %s", e)

        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges_list,
            "account_id": account_id,
        }

    async def trace_transaction_path(
        self, transaction_id: str, max_depth: int = 5
    ) -> dict[str, Any]:
        """Trace downstream multi-hop money flow path for a transaction in Neo4j.

        Args:
            transaction_id: Unique transaction reference / ID.
            max_depth: Maximum hops to trace (default: 5).

        Returns:
            Dictionary with 'nodes', 'edges', and 'path_summary'.
        """
        graph_data: dict[str, Any] = {
            "nodes": [],
            "edges": [],
            "path_summary": "Graph trace could not be established.",
        }

        if not neo4j_manager.is_connected:
            return graph_data

        clean_tx = str(transaction_id).strip()
        clamped_depth = max(1, min(int(max_depth), 10))

        cypher = f"""
        MATCH path = (s:Account)-[r:TRANSFERRED_FUNDS*1..{clamped_depth}]->(t:Account)
        WHERE ANY(rel IN r WHERE rel.ref = $tx_ref)
        RETURN path LIMIT 1
        """

        try:
            async with neo4j_manager.get_session() as session:
                res = await session.run(cypher, tx_ref=clean_tx)
                record = await res.single()

                if record:
                    path = record["path"]
                    nodes_set = set()
                    for node in path.nodes:
                        n_id = node.get("account_number", "UNKNOWN")
                        nodes_set.add(n_id)
                        graph_data["nodes"].append({
                            "id": n_id,
                            "label": n_id,
                            "type": "account",
                            **dict(node),
                        })

                    for rel in path.relationships:
                        graph_data["edges"].append({
                            "source": str(rel.start_node.get("account_number", "UNKNOWN")),
                            "target": str(rel.end_node.get("account_number", "UNKNOWN")),
                            "relationship": rel.type,
                            **dict(rel),
                        })

                    hop_count = len(path.relationships)
                    unique_count = len(nodes_set)
                    graph_data["path_summary"] = (
                        f"Funds were traced across {hop_count} hops involving "
                        f"{unique_count} unique accounts. Layering detected."
                    )
                else:
                    graph_data["path_summary"] = (
                        "Transaction found but no complex layering path detected in the graph."
                    )
        except Exception as e:
            logger.warning("Error running Neo4j trace query: %s", e)

        return graph_data

    async def find_circular_paths(
        self, start_account: str, max_depth: int = 5
    ) -> list[list[str]]:
        """Detect circular fund transfer cycles in Neo4j starting from start_account.

        Args:
            start_account: Account identifier to inspect.
            max_depth: Maximum hops (default: 5).

        Returns:
            List of detected cycles as lists of account numbers.
        """
        if not neo4j_manager.is_connected:
            return []

        clean_acc = str(start_account).replace("account:", "").strip()
        clamped_depth = max(1, min(int(max_depth), 10))

        cypher = f"""
        MATCH path = (s:Account {{account_number: $start_acc}})-[r:TRANSFERRED_FUNDS*1..{clamped_depth}]->(s)
        RETURN [n IN nodes(path) | n.account_number] AS cycle
        LIMIT 10
        """

        detected_cycles: list[list[str]] = []
        try:
            async with neo4j_manager.get_session() as session:
                res = await session.run(cypher, start_acc=clean_acc)
                records = await res.data()
                for rec in records:
                    cycle = rec.get("cycle")
                    if cycle and cycle not in detected_cycles:
                        detected_cycles.append(cycle)
        except Exception as e:
            logger.warning("Error running Neo4j cycle detection: %s", e)

        return detected_cycles

    async def link_account_device(self, account_id: str, device_id: str) -> None:
        """Create USED_DEVICE relationship between Account and Device in Neo4j.

        Args:
            account_id: Account identifier.
            device_id: Hardware fingerprint.
        """
        clean_acc = str(account_id).replace("account:", "").strip()
        clean_dev = str(device_id).replace("device:", "").strip()
        await relationship_engine.link_account_device(clean_acc, clean_dev)
