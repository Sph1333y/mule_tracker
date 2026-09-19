"""
MuleTrace AI — Graph Intelligence Engine.

Orchestrates deterministic graph feature extraction over the domain GraphRepository
port. Evaluates account-level graph topologies, degree distributions, fan-in/out
ratios, neighborhood density, circular fund cycles, shared hardware/IP syndicates,
and explainability audit signals.

Architectural Boundary:
- Works with ANY GraphRepository implementation (NetworkX, Neo4j, Neptune).
- Zero dependency on FastAPI, SQLAlchemy, or AWS.
- Preserves multi-edge semantics, strict directionality, and determinism.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.domain.interfaces import GraphRepository
from app.domain.models import TransactionEvent
from app.engines.graph.intelligence.graph_metrics import (
    compute_connectivity_and_paths,
    compute_cycle_metrics,
    compute_degree_metrics,
    compute_fan_metrics,
    compute_neighborhood_metrics,
    compute_shared_entity_metrics,
    normalize_node_id,
    synthesize_evidence_signals,
)
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.repositories.graph_factory import get_graph_repository

logger = logging.getLogger("app.engines.graph.intelligence.graph_engine")


class GraphIntelligenceEngine:
    """Core deterministic graph intelligence evaluation engine."""

    def __init__(self, repository: Optional[GraphRepository] = None) -> None:
        """Initialize engine with a GraphRepository adapter.

        Args:
            repository: Optional GraphRepository instance. If None, defaults
                to the factory-configured adapter (e.g. NetworkX or Neo4j).
        """
        self._repository: Optional[GraphRepository] = repository

    @property
    def repository(self) -> GraphRepository:
        """Lazy-load repository if not explicitly injected."""
        if self._repository is None:
            self._repository = get_graph_repository()
        return self._repository

    async def extract_features(
        self,
        account_id: str,
        hops: int = 2,
        max_depth: int = 5,
        reference_time: Optional[datetime] = None,
    ) -> GraphFeatures:
        """Extract deterministic, explainable graph features for a target account.

        Args:
            account_id: Unique account identifier (raw or prefixed 'account:').
            hops: Traversal depth for neighborhood subgraph (default: 2).
            max_depth: Maximum path length for cycle and reachability tracing (default: 5).
            reference_time: Optional reference anchor time for audit timestamp.

        Returns:
            GraphFeatures containing degree, fan-in/out, neighborhood, cycle,
            shared entity, and explainability audit maps.
        """
        safe_hops = max(0, int(hops))
        safe_max_depth = max(1, min(20, int(max_depth)))
        norm_account = normalize_node_id(account_id)
        ref_ts = (
            reference_time.isoformat()
            if reference_time is not None and hasattr(reference_time, "isoformat")
            else str(reference_time) if reference_time is not None
            else None
        )

        # 1. Query neighborhood subgraph from repository
        try:
            subgraph = await self.repository.get_subgraph(norm_account, hops=safe_hops)
        except Exception as e:
            logger.warning("Error retrieving subgraph for account %s: %s", norm_account, e)
            subgraph = {"nodes": [], "edges": []}

        nodes: list[dict[str, Any]] = subgraph.get("nodes", []) if subgraph else []
        edges: list[dict[str, Any]] = subgraph.get("edges", []) if subgraph else []

        # 2. Handle Empty Graph / Unseen Account Gracefully
        if not nodes:
            return GraphFeatures(
                account_id=norm_account,
                node_type="account",
                hop_depth=safe_hops,
                reference_timestamp=ref_ts,
                path_summary=f"Account {norm_account} not found in graph topology.",
                explanations=[f"Account {norm_account} has no recorded graph interactions."],
            )

        # 3. A. Degree Metrics (Multi-edge safe)
        (
            in_degree,
            out_degree,
            total_degree,
            u_in,
            u_out,
            in_cps,
            out_cps,
        ) = compute_degree_metrics(edges, norm_account)

        # 4. B. Fan-In / Fan-Out Dispersion & Volumes
        (
            inbound_vol,
            outbound_vol,
            fan_in_ratio,
            fan_out_ratio,
        ) = compute_fan_metrics(
            edges=edges,
            focal_account=norm_account,
            unique_senders=u_in,
            unique_receivers=u_out,
            inbound_tx_count=in_degree,
            outbound_tx_count=out_degree,
        )

        # 5. C. Neighborhood Structure & Density
        (
            neighbor_accounts,
            neighbor_devices,
            neighbor_ips,
            node_counts_by_type,
            density,
        ) = compute_neighborhood_metrics(nodes, edges, norm_account)

        # 6. D & E. Connectivity, Reachability & Paths
        (
            reachable_count,
            downstream_accs,
            upstream_accs,
            max_path_length,
            path_summary,
        ) = compute_connectivity_and_paths(nodes, edges, norm_account, max_depth=safe_max_depth)

        # 7. F. Circular Flow Cycle Detection
        try:
            raw_cycles = await self.repository.find_circular_paths(
                norm_account, max_depth=safe_max_depth
            )
        except Exception as e:
            logger.warning("Error finding circular paths for account %s: %s", norm_account, e)
            raw_cycles = []

        (
            has_cycle,
            cycle_count,
            cycle_lengths,
            valid_cycles,
            cycle_nodes,
        ) = compute_cycle_metrics(raw_cycles, norm_account)

        # 8. G & H. Shared Hardware / IP Syndicates
        global_graph = getattr(self.repository, "graph", None)
        (
            shared_device_count,
            shared_ip_count,
            accounts_per_device,
            accounts_per_ip,
            assoc_devices,
            assoc_ips,
        ) = compute_shared_entity_metrics(
            nodes=nodes,
            edges=edges,
            focal_account=norm_account,
            global_graph=global_graph,
        )

        # 9. Audit Trail & Contributing Entities
        contributing_node_ids = sorted(
            {str(n.get("id", "")) for n in nodes if n.get("id")}
        )
        contributing_tx_ids = sorted(
            {
                str(e.get("transaction_id") or e.get("ref") or e.get("key", ""))
                for e in edges
                if e.get("relationship") == "TRANSFERRED_FUNDS"
                and (e.get("transaction_id") or e.get("ref") or e.get("key"))
            }
        )

        # 10. Synthesize Explainability Signals & Narratives
        signals, explanations = synthesize_evidence_signals(
            account_id=norm_account,
            in_degree=in_degree,
            out_degree=out_degree,
            unique_senders=u_in,
            unique_receivers=u_out,
            inbound_volume=inbound_vol,
            outbound_volume=outbound_vol,
            fan_in_ratio=fan_in_ratio,
            fan_out_ratio=fan_out_ratio,
            has_cycle=has_cycle,
            cycle_count=cycle_count,
            cycle_lengths=cycle_lengths,
            shared_device_count=shared_device_count,
            shared_ip_count=shared_ip_count,
            accounts_per_device=accounts_per_device,
            accounts_per_ip=accounts_per_ip,
            reachable_accounts=reachable_count,
            inbound_tx_count=in_degree,
            outbound_tx_count=out_degree,
        )

        return GraphFeatures(
            account_id=norm_account,
            node_type="account",
            hop_depth=safe_hops,
            reference_timestamp=ref_ts,
            # Degrees
            in_degree=in_degree,
            out_degree=out_degree,
            total_degree=total_degree,
            unique_inbound_counterparties=u_in,
            unique_outbound_counterparties=u_out,
            # Fan-In / Fan-Out
            unique_senders_count=u_in,
            unique_receivers_count=u_out,
            inbound_tx_count=in_degree,
            outbound_tx_count=out_degree,
            inbound_volume_total=inbound_vol,
            outbound_volume_total=outbound_vol,
            fan_in_ratio=fan_in_ratio,
            fan_out_ratio=fan_out_ratio,
            # Neighborhood
            neighboring_accounts_count=neighbor_accounts,
            neighboring_devices_count=neighbor_devices,
            neighboring_ips_count=neighbor_ips,
            unique_node_count_by_type=node_counts_by_type,
            neighborhood_density=density,
            # Connectivity & Paths
            reachable_node_count=reachable_count,
            downstream_accounts=downstream_accs,
            upstream_accounts=upstream_accs,
            max_downstream_path_length=max_path_length,
            path_summary=path_summary,
            # Cycles
            has_cycle=has_cycle,
            cycle_count=cycle_count,
            cycle_lengths=cycle_lengths,
            cycles=valid_cycles,
            contributing_cycle_nodes=cycle_nodes,
            # Shared Entities
            shared_device_count=shared_device_count,
            shared_ip_count=shared_ip_count,
            accounts_per_shared_device=accounts_per_device,
            accounts_per_shared_ip=accounts_per_ip,
            associated_devices=assoc_devices,
            associated_ips=assoc_ips,
            # Audit & Explainability
            subgraph_node_count=len(nodes),
            subgraph_edge_count=len(edges),
            contributing_node_ids=contributing_node_ids,
            contributing_transaction_ids=contributing_tx_ids,
            evidence_signals=signals,
            explanations=explanations,
        )

    async def analyze_account(
        self,
        account_id: str,
        hops: int = 2,
        max_depth: int = 5,
    ) -> GraphFeatures:
        """Alias for extract_features."""
        return await self.extract_features(account_id=account_id, hops=hops, max_depth=max_depth)

    async def extract_for_event(
        self,
        event: TransactionEvent,
        hops: int = 2,
        max_depth: int = 5,
        ingest: bool = False,
    ) -> dict[str, GraphFeatures]:
        """Extract graph features for both sender and receiver of an event.

        Args:
            event: Canonical TransactionEvent to evaluate.
            hops: Subgraph hop depth.
            max_depth: Max path / cycle tracing depth.
            ingest: If True, first ingests the event into the repository.

        Returns:
            Dictionary with 'sender' and 'receiver' GraphFeatures.
        """
        if ingest:
            await self.repository.add_transaction(event)

        sender_features = await self.extract_features(
            account_id=event.sender_account,
            hops=hops,
            max_depth=max_depth,
            reference_time=event.timestamp if hasattr(event.timestamp, "isoformat") else None,
        )
        receiver_features = await self.extract_features(
            account_id=event.receiver_account,
            hops=hops,
            max_depth=max_depth,
            reference_time=event.timestamp if hasattr(event.timestamp, "isoformat") else None,
        )

        return {
            "sender": sender_features,
            "receiver": receiver_features,
        }

    def extract_features_sync(
        self,
        account_id: str,
        hops: int = 2,
        max_depth: int = 5,
    ) -> GraphFeatures:
        """Synchronous wrapper for extract_features."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run,
                    self.extract_features(account_id=account_id, hops=hops, max_depth=max_depth),
                ).result()
        else:
            return asyncio.run(
                self.extract_features(account_id=account_id, hops=hops, max_depth=max_depth)
            )


# Default singleton instance
graph_intelligence_engine = GraphIntelligenceEngine()
