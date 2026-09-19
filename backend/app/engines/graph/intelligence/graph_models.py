"""
MuleTrace AI — Graph Domain Models & Feature Contracts.

Defines deterministic data structures for topological graph features,
degree distributions, fan-in/out patterns, neighborhood connectivity,
circular routing loops, shared hardware/network entities, and explainability audit signals.

Architectural Boundary:
- Pure domain data contract: zero dependencies on FastAPI, SQLAlchemy, Neo4j, or AWS.
- Fully JSON-serializable via to_dict().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class GraphFeatures:
    """Canonical explainable feature container produced by the Graph Intelligence Engine.

    Encapsulates degree metrics, fan-in/fan-out ratios, multi-hop neighborhood statistics,
    connectivity reach, circular flow loops, shared device/IP syndicates, and complete
    evidence audit trails.
    """

    # ── Focal Entity Identification ─────────────────────────────────────
    account_id: str
    node_type: str = "account"
    hop_depth: int = 2

    # ── A. Degree Features ──────────────────────────────────────────────
    in_degree: int = 0
    out_degree: int = 0
    total_degree: int = 0
    unique_inbound_counterparties: int = 0
    unique_outbound_counterparties: int = 0

    # ── B. Fan-In / Fan-Out Features ────────────────────────────────────
    unique_senders_count: int = 0
    unique_receivers_count: int = 0
    inbound_tx_count: int = 0
    outbound_tx_count: int = 0
    inbound_volume_total: float = 0.0
    outbound_volume_total: float = 0.0
    fan_in_ratio: float = 0.0
    fan_out_ratio: float = 0.0

    # ── C. Neighborhood Features ────────────────────────────────────────
    neighboring_accounts_count: int = 0
    neighboring_devices_count: int = 0
    neighboring_ips_count: int = 0
    unique_node_count_by_type: dict[str, int] = field(default_factory=dict)
    neighborhood_density: float = 0.0

    # ── D & E. Connectivity & Path Features ─────────────────────────────
    reachable_node_count: int = 0
    downstream_accounts: list[str] = field(default_factory=list)
    upstream_accounts: list[str] = field(default_factory=list)
    max_downstream_path_length: int = 0
    path_summary: str = ""

    # ── F. Cycle Features ───────────────────────────────────────────────
    has_cycle: bool = False
    cycle_count: int = 0
    cycle_lengths: list[int] = field(default_factory=list)
    cycles: list[list[str]] = field(default_factory=list)
    contributing_cycle_nodes: list[str] = field(default_factory=list)

    # ── G & H. Shared Entity Features ───────────────────────────────────
    shared_device_count: int = 0
    shared_ip_count: int = 0
    accounts_per_shared_device: dict[str, int] = field(default_factory=dict)
    accounts_per_shared_ip: dict[str, int] = field(default_factory=dict)
    associated_devices: list[str] = field(default_factory=list)
    associated_ips: list[str] = field(default_factory=list)

    # ── Explainability & Audit Trail ────────────────────────────────────
    subgraph_node_count: int = 0
    subgraph_edge_count: int = 0
    contributing_node_ids: list[str] = field(default_factory=list)
    contributing_transaction_ids: list[str] = field(default_factory=list)
    evidence_signals: list[str] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)
    reference_timestamp: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert graph features into a clean, JSON-serializable dictionary."""
        return {
            "account_id": self.account_id,
            "node_type": self.node_type,
            "hop_depth": self.hop_depth,
            "reference_timestamp": self.reference_timestamp,
            "degrees": {
                "in_degree": self.in_degree,
                "out_degree": self.out_degree,
                "total_degree": self.total_degree,
                "unique_inbound_counterparties": self.unique_inbound_counterparties,
                "unique_outbound_counterparties": self.unique_outbound_counterparties,
            },
            "fan_in_out": {
                "unique_senders_count": self.unique_senders_count,
                "unique_receivers_count": self.unique_receivers_count,
                "inbound_tx_count": self.inbound_tx_count,
                "outbound_tx_count": self.outbound_tx_count,
                "inbound_volume_total": round(self.inbound_volume_total, 2),
                "outbound_volume_total": round(self.outbound_volume_total, 2),
                "fan_in_ratio": round(self.fan_in_ratio, 4),
                "fan_out_ratio": round(self.fan_out_ratio, 4),
            },
            "neighborhood": {
                "neighboring_accounts_count": self.neighboring_accounts_count,
                "neighboring_devices_count": self.neighboring_devices_count,
                "neighboring_ips_count": self.neighboring_ips_count,
                "unique_node_count_by_type": dict(self.unique_node_count_by_type),
                "neighborhood_density": round(self.neighborhood_density, 4),
            },
            "connectivity": {
                "reachable_node_count": self.reachable_node_count,
                "downstream_accounts": list(self.downstream_accounts),
                "upstream_accounts": list(self.upstream_accounts),
                "max_downstream_path_length": self.max_downstream_path_length,
                "path_summary": self.path_summary,
            },
            "cycles": {
                "has_cycle": self.has_cycle,
                "cycle_count": self.cycle_count,
                "cycle_lengths": list(self.cycle_lengths),
                "cycles": [list(c) for c in self.cycles],
                "contributing_cycle_nodes": list(self.contributing_cycle_nodes),
            },
            "shared_entities": {
                "shared_device_count": self.shared_device_count,
                "shared_ip_count": self.shared_ip_count,
                "accounts_per_shared_device": dict(self.accounts_per_shared_device),
                "accounts_per_shared_ip": dict(self.accounts_per_shared_ip),
                "associated_devices": list(self.associated_devices),
                "associated_ips": list(self.associated_ips),
            },
            "audit": {
                "subgraph_node_count": self.subgraph_node_count,
                "subgraph_edge_count": self.subgraph_edge_count,
                "contributing_node_ids": list(self.contributing_node_ids),
                "contributing_transaction_ids": list(self.contributing_transaction_ids),
                "evidence_signals": list(self.evidence_signals),
                "explanations": list(self.explanations),
            },
        }
