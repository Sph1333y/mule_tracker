"""
MuleTrace AI — Graph Repository Factory.

Provides a controlled, backward-compatible adapter selection mechanism for the
domain GraphRepository port.

Configuration:
- Environment variable: GRAPH_BACKEND (default: "neo4j")
- Supported values: "neo4j", "networkx"

Production Flow Guarantee:
- The default adapter remains "neo4j", strictly preserving legacy production flow.
- "networkx" can be selected explicitly for BUILD IT local testing and offline workflows.
"""

from __future__ import annotations

import os
from typing import Optional

from app.domain.interfaces import GraphRepository
from app.repositories.graph_neo4j import Neo4jGraphRepository
from app.repositories.graph_nx import NetworkXGraphRepository

DEFAULT_GRAPH_BACKEND = "neo4j"


def get_graph_repository(backend: Optional[str] = None) -> GraphRepository:
    """Factory function to instantiate the configured GraphRepository adapter.

    Args:
        backend: Optional override for the backend type ('neo4j' or 'networkx').
            If not specified, reads the GRAPH_BACKEND environment variable,
            defaulting to 'neo4j'.

    Returns:
        GraphRepository instance (Neo4jGraphRepository or NetworkXGraphRepository).

    Raises:
        ValueError: If an unknown backend identifier is specified.
    """
    selected = (backend or os.getenv("GRAPH_BACKEND", DEFAULT_GRAPH_BACKEND)).strip().lower()

    if selected == "networkx":
        return NetworkXGraphRepository()
    elif selected == "neo4j":
        return Neo4jGraphRepository()
    else:
        raise ValueError(
            f"Unsupported GRAPH_BACKEND '{selected}'. Must be 'neo4j' or 'networkx'."
        )
