"""
MuleTrace AI — Graph Intelligence Metric Algorithms.

Provides deterministic, infrastructure-agnostic graph feature calculation
algorithms including:
- Degree & multi-edge metrics
- Fan-in and Fan-out dispersion ratios
- Multi-hop neighborhood structure & density
- Directed connectivity, reachability, and path tracing
- Circular loop detection & normalization
- Shared entity (Device / IP) syndicate detection
- Explainability & evidence signal synthesis

All algorithms adhere strictly to:
1. Multi-edge safety: Multiple transactions between same counterparties count individually
   for volume and transaction count, but collapse to 1 for unique counterparties.
2. Directionality: Inbound (target == focal) and Outbound (source == focal) are never conflated.
3. Determinism: All collections, cycles, node IDs, and signals are sorted stably.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Optional


def normalize_node_id(node_id: str) -> str:
    """Strip node type prefix ('account:', 'device:', 'ip:') to return raw identifier."""
    raw = str(node_id).strip()
    for prefix in ("account:", "device:", "ip:"):
        if raw.startswith(prefix):
            return raw[len(prefix) :]
    return raw


def get_account_node_id(account_id: str) -> str:
    """Format an account identifier into canonical 'account:<id>' format."""
    acc = str(account_id).strip()
    return acc if acc.startswith("account:") else f"account:{acc}"


def matches_account(node_id: str, account_id: str) -> bool:
    """Check if node_id matches account_id regardless of prefix format."""
    norm_node = normalize_node_id(node_id)
    norm_acc = normalize_node_id(account_id)
    return norm_node == norm_acc


def compute_degree_metrics(
    edges: list[dict[str, Any]],
    focal_account: str,
) -> tuple[int, int, int, int, int, set[str], set[str]]:
    """Compute directed in/out degrees and unique counterparty sets.

    Preserves multi-edge semantics: each transfer edge counts towards in_degree/out_degree,
    while counterparties are deduplicated.

    Returns:
        (in_degree, out_degree, total_degree, unique_inbound, unique_outbound,
         inbound_counterparties, outbound_counterparties)
    """
    in_degree = 0
    out_degree = 0
    inbound_counterparties: set[str] = set()
    outbound_counterparties: set[str] = set()

    for edge in edges:
        if edge.get("relationship") != "TRANSFERRED_FUNDS":
            continue

        src = str(edge.get("source", ""))
        tgt = str(edge.get("target", ""))

        is_src = matches_account(src, focal_account)
        is_tgt = matches_account(tgt, focal_account)

        # Self-transfers (A -> A) count for both in and out
        if is_src and is_tgt:
            in_degree += 1
            out_degree += 1
            inbound_counterparties.add(normalize_node_id(src))
            outbound_counterparties.add(normalize_node_id(tgt))
        elif is_tgt:
            in_degree += 1
            inbound_counterparties.add(normalize_node_id(src))
        elif is_src:
            out_degree += 1
            outbound_counterparties.add(normalize_node_id(tgt))

    total_degree = in_degree + out_degree
    unique_inbound = len(inbound_counterparties)
    unique_outbound = len(outbound_counterparties)

    return (
        in_degree,
        out_degree,
        total_degree,
        unique_inbound,
        unique_outbound,
        inbound_counterparties,
        outbound_counterparties,
    )


def compute_fan_metrics(
    edges: list[dict[str, Any]],
    focal_account: str,
    unique_senders: int,
    unique_receivers: int,
    inbound_tx_count: int,
    outbound_tx_count: int,
) -> tuple[float, float, float, float]:
    """Calculate monetary sums and dispersion ratios for fan-in and fan-out patterns.

    Returns:
        (inbound_volume_total, outbound_volume_total, fan_in_ratio, fan_out_ratio)
    """
    inbound_volume = 0.0
    outbound_volume = 0.0

    for edge in edges:
        if edge.get("relationship") != "TRANSFERRED_FUNDS":
            continue

        amount = float(edge.get("amount", 0.0))
        src = str(edge.get("source", ""))
        tgt = str(edge.get("target", ""))

        is_src = matches_account(src, focal_account)
        is_tgt = matches_account(tgt, focal_account)

        if is_src and is_tgt:
            inbound_volume += amount
            outbound_volume += amount
        elif is_tgt:
            inbound_volume += amount
        elif is_src:
            outbound_volume += amount

    # Ratios represent source/sink diversity (1.0 = each transaction from a distinct counterparty)
    fan_in_ratio = (
        round(unique_senders / inbound_tx_count, 4)
        if inbound_tx_count > 0
        else 0.0
    )
    fan_out_ratio = (
        round(unique_receivers / outbound_tx_count, 4)
        if outbound_tx_count > 0
        else 0.0
    )

    return (
        round(inbound_volume, 2),
        round(outbound_volume, 2),
        fan_in_ratio,
        fan_out_ratio,
    )


def compute_neighborhood_metrics(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    focal_account: str,
) -> tuple[int, int, int, dict[str, int], float]:
    """Compute counts of neighboring entities by type and graph density.

    Returns:
        (neighboring_accounts_count, neighboring_devices_count, neighboring_ips_count,
         unique_node_count_by_type, neighborhood_density)
    """
    type_counts: dict[str, int] = defaultdict(int)
    accounts_seen: set[str] = set()
    devices_seen: set[str] = set()
    ips_seen: set[str] = set()

    for node in nodes:
        node_id = str(node.get("id", ""))
        raw_id = normalize_node_id(node_id)
        node_type = str(node.get("type", "")).lower()

        if not node_type:
            if node_id.startswith("device:"):
                node_type = "device"
            elif node_id.startswith("ip:"):
                node_type = "ip"
            else:
                node_type = "account"

        type_counts[node_type] += 1

        if node_type == "account":
            if not matches_account(node_id, focal_account):
                accounts_seen.add(raw_id)
        elif node_type == "device":
            devices_seen.add(raw_id)
        elif node_type == "ip":
            ips_seen.add(raw_id)

    # Neighborhood density on transfer edges among accounts
    # N is all accounts in the neighborhood including focal account
    all_subgraph_accounts = set(accounts_seen)
    all_subgraph_accounts.add(normalize_node_id(focal_account))
    n_acc = len(all_subgraph_accounts)

    density = 0.0
    if n_acc >= 2:
        # Count unique directed account-to-account transfer pairs
        unique_transfer_pairs: set[tuple[str, str]] = set()
        for edge in edges:
            if edge.get("relationship") == "TRANSFERRED_FUNDS":
                u = normalize_node_id(str(edge.get("source", "")))
                v = normalize_node_id(str(edge.get("target", "")))
                if u in all_subgraph_accounts and v in all_subgraph_accounts:
                    unique_transfer_pairs.add((u, v))

        max_possible_edges = n_acc * (n_acc - 1)
        density = round(len(unique_transfer_pairs) / max_possible_edges, 4)

    return (
        len(accounts_seen),
        len(devices_seen),
        len(ips_seen),
        dict(type_counts),
        density,
    )


def compute_connectivity_and_paths(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    focal_account: str,
    max_depth: int = 5,
) -> tuple[int, list[str], list[str], int, str]:
    """Trace downstream reachability, upstream lineage, and max path distance.

    Returns:
        (reachable_node_count, downstream_accounts, upstream_accounts,
         max_downstream_path_length, path_summary)
    """
    focal_norm = normalize_node_id(focal_account)

    # Build directed transfer adjacency for accounts
    downstream_adj: dict[str, set[str]] = defaultdict(set)
    upstream_adj: dict[str, set[str]] = defaultdict(set)

    for edge in edges:
        if edge.get("relationship") != "TRANSFERRED_FUNDS":
            continue
        u = normalize_node_id(str(edge.get("source", "")))
        v = normalize_node_id(str(edge.get("target", "")))
        if u and v:
            downstream_adj[u].add(v)
            upstream_adj[v].add(u)

    # BFS for Downstream Reachability
    downstream_accounts: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(focal_norm, 0)])
    visited_downstream: set[str] = {focal_norm}
    max_path_len = 0

    while queue:
        curr, depth = queue.popleft()
        if depth > max_path_len:
            max_path_len = depth
        if depth >= max_depth:
            continue

        for nxt in sorted(downstream_adj.get(curr, set())):
            if nxt != focal_norm:
                downstream_accounts.add(nxt)
            if nxt not in visited_downstream:
                visited_downstream.add(nxt)
                queue.append((nxt, depth + 1))

    # BFS for Upstream Lineage
    upstream_accounts: set[str] = set()
    up_queue: deque[tuple[str, int]] = deque([(focal_norm, 0)])
    visited_upstream: set[str] = {focal_norm}

    while up_queue:
        curr, depth = up_queue.popleft()
        if depth >= max_depth:
            continue
        for prev in sorted(upstream_adj.get(curr, set())):
            if prev != focal_norm:
                upstream_accounts.add(prev)
            if prev not in visited_upstream:
                visited_upstream.add(prev)
                up_queue.append((prev, depth + 1))

    sorted_downstream = sorted(downstream_accounts)
    sorted_upstream = sorted(upstream_accounts)
    reachable_node_count = len(sorted_downstream)

    if reachable_node_count > 0:
        path_summary = (
            f"Account {focal_norm} can reach {reachable_node_count} downstream account(s) "
            f"across a maximum path length of {max_path_len} hops."
        )
    else:
        path_summary = f"Account {focal_norm} has no downstream fund transfers."

    return (
        reachable_node_count,
        sorted_downstream,
        sorted_upstream,
        max_path_len,
        path_summary,
    )


def compute_cycle_metrics(
    raw_cycles: list[list[str]],
    focal_account: str,
) -> tuple[bool, int, list[int], list[list[str]], list[str]]:
    """Process, validate, and deterministically sort cycle loops.

    Filters cycles to ensure they represent valid circular paths involving the focal account.

    Returns:
        (has_cycle, cycle_count, cycle_lengths, canonical_cycles, contributing_cycle_nodes)
    """
    focal_norm = normalize_node_id(focal_account)
    valid_cycles: list[list[str]] = []
    cycle_lengths: list[int] = []
    contributing_nodes: set[str] = set()

    for cycle in raw_cycles:
        if not cycle or len(cycle) < 2:
            continue

        norm_cycle = [normalize_node_id(node) for node in cycle]

        # Verify loop closes on start account
        if norm_cycle[0] != focal_norm or norm_cycle[-1] != focal_norm:
            # If focal_norm is in the cycle, re-orient to start and end at focal_norm
            if focal_norm in norm_cycle:
                idx = norm_cycle.index(focal_norm)
                # Avoid duplicate wrap
                nodes_no_end = norm_cycle[:-1] if norm_cycle[0] == norm_cycle[-1] else norm_cycle
                reordered = nodes_no_end[idx:] + nodes_no_end[:idx] + [focal_norm]
                norm_cycle = reordered
            else:
                continue

        # Cycle length is number of directed hops (len(nodes) - 1)
        length = len(norm_cycle) - 1
        if length < 1:
            continue

        if norm_cycle not in valid_cycles:
            valid_cycles.append(norm_cycle)
            cycle_lengths.append(length)
            for n in norm_cycle:
                contributing_nodes.add(n)

    # Sort deterministically
    valid_cycles.sort(key=lambda c: (len(c), c))
    cycle_lengths.sort()
    sorted_nodes = sorted(contributing_nodes)

    has_cycle = len(valid_cycles) > 0
    cycle_count = len(valid_cycles)

    return (
        has_cycle,
        cycle_count,
        cycle_lengths,
        valid_cycles,
        sorted_nodes,
    )


def compute_shared_entity_metrics(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    focal_account: str,
    global_graph: Optional[Any] = None,
) -> tuple[int, int, dict[str, int], dict[str, int], list[str], list[str]]:
    """Detect shared devices and shared IP addresses used across multiple accounts.

    Returns:
        (shared_device_count, shared_ip_count, accounts_per_shared_device,
         accounts_per_shared_ip, associated_devices, associated_ips)
    """
    focal_norm = normalize_node_id(focal_account)

    associated_devices: set[str] = set()
    associated_ips: set[str] = set()

    # 1. Identify associated devices & IPs for focal account
    for edge in edges:
        rel = str(edge.get("relationship", "")).upper()
        src_norm = normalize_node_id(str(edge.get("source", "")))
        tgt_norm = normalize_node_id(str(edge.get("target", "")))

        if rel in ("USED_DEVICE", "USES_DEVICE"):
            if src_norm == focal_norm:
                associated_devices.add(tgt_norm)
            elif tgt_norm == focal_norm:
                associated_devices.add(src_norm)
        elif rel in ("USED_IP", "USES_IP"):
            if src_norm == focal_norm:
                associated_ips.add(tgt_norm)
            elif tgt_norm == focal_norm:
                associated_ips.add(src_norm)

    # 2. Count accounts using each associated entity
    accounts_per_device: dict[str, int] = {}
    accounts_per_ip: dict[str, int] = {}

    if global_graph is not None and hasattr(global_graph, "edges"):
        # Query full graph for complete global accuracy
        for dev_id in sorted(associated_devices):
            dev_node = f"device:{dev_id}"
            accs: set[str] = set()
            if dev_node in global_graph:
                for u, v, _ in global_graph.in_edges(dev_node, keys=True):
                    if str(u).startswith("account:"):
                        accs.add(normalize_node_id(u))
            elif dev_id in global_graph:
                for u, v, _ in global_graph.in_edges(dev_id, keys=True):
                    accs.add(normalize_node_id(u))
            accs.add(focal_norm)
            if len(accs) > 1:
                accounts_per_device[dev_id] = len(accs)

        for ip_id in sorted(associated_ips):
            ip_node = f"ip:{ip_id}"
            accs = set()
            if ip_node in global_graph:
                for u, v, _ in global_graph.in_edges(ip_node, keys=True):
                    if str(u).startswith("account:"):
                        accs.add(normalize_node_id(u))
            elif ip_id in global_graph:
                for u, v, _ in global_graph.in_edges(ip_id, keys=True):
                    accs.add(normalize_node_id(u))
            accs.add(focal_norm)
            if len(accs) > 1:
                accounts_per_ip[ip_id] = len(accs)
    else:
        # Fallback to local subgraph
        for dev_id in sorted(associated_devices):
            accs = {focal_norm}
            for edge in edges:
                rel = str(edge.get("relationship", "")).upper()
                if rel in ("USED_DEVICE", "USES_DEVICE"):
                    src_norm = normalize_node_id(str(edge.get("source", "")))
                    tgt_norm = normalize_node_id(str(edge.get("target", "")))
                    if tgt_norm == dev_id:
                        accs.add(src_norm)
                    elif src_norm == dev_id:
                        accs.add(tgt_norm)
            if len(accs) > 1:
                accounts_per_device[dev_id] = len(accs)

        for ip_id in sorted(associated_ips):
            accs = {focal_norm}
            for edge in edges:
                rel = str(edge.get("relationship", "")).upper()
                if rel in ("USED_IP", "USES_IP"):
                    src_norm = normalize_node_id(str(edge.get("source", "")))
                    tgt_norm = normalize_node_id(str(edge.get("target", "")))
                    if tgt_norm == ip_id:
                        accs.add(src_norm)
                    elif src_norm == ip_id:
                        accs.add(tgt_norm)
            if len(accs) > 1:
                accounts_per_ip[ip_id] = len(accs)

    sorted_devices = sorted(associated_devices)
    sorted_ips = sorted(associated_ips)

    return (
        len(accounts_per_device),
        len(accounts_per_ip),
        accounts_per_device,
        accounts_per_ip,
        sorted_devices,
        sorted_ips,
    )


def synthesize_evidence_signals(
    account_id: str,
    in_degree: int,
    out_degree: int,
    unique_senders: int,
    unique_receivers: int,
    inbound_volume: float,
    outbound_volume: float,
    fan_in_ratio: float,
    fan_out_ratio: float,
    has_cycle: bool,
    cycle_count: int,
    cycle_lengths: list[int],
    shared_device_count: int,
    shared_ip_count: int,
    accounts_per_device: dict[str, int],
    accounts_per_ip: dict[str, int],
    reachable_accounts: int,
    inbound_tx_count: Optional[int] = None,
    outbound_tx_count: Optional[int] = None,
) -> tuple[list[str], list[str]]:
    """Synthesize objective, explainable evidence signals and human-readable narratives.

    Strictly produces factual topological observations without subjective fraud verdicts.
    """
    in_tx = inbound_tx_count if inbound_tx_count is not None else in_degree
    out_tx = outbound_tx_count if outbound_tx_count is not None else out_degree
    signals: list[str] = []
    explanations: list[str] = []
    norm_acc = normalize_node_id(account_id)

    # 1. Degree & Transfer Volume
    if in_degree > 0 or out_degree > 0:
        explanations.append(
            f"Account {norm_acc} recorded {in_degree} inbound transfer(s) (INR {inbound_volume:,.2f}) "
            f"from {unique_senders} unique sender(s) and {out_degree} outbound transfer(s) "
            f"(INR {outbound_volume:,.2f}) to {unique_receivers} unique receiver(s)."
        )

    # 2. Fan-In (Aggregation)
    if unique_senders >= 3 and fan_in_ratio >= 0.7:
        sig = f"HIGH_FAN_IN: {unique_senders} unique senders across {in_tx} transactions"
        signals.append(sig)
        explanations.append(
            f"Observed fan-in aggregation structure with {unique_senders} distinct senders."
        )

    # 3. Fan-Out (Distribution)
    if unique_receivers >= 3 and fan_out_ratio >= 0.7:
        sig = f"HIGH_FAN_OUT: {unique_receivers} unique receivers across {out_tx} transactions"
        signals.append(sig)
        explanations.append(
            f"Observed fan-out dispersion structure with {unique_receivers} distinct receivers."
        )

    # 4. Circular Routing Loops
    if has_cycle:
        min_len = cycle_lengths[0] if cycle_lengths else 0
        sig = f"CYCLE_DETECTED: {cycle_count} circular fund flow loop(s) detected (shortest: {min_len} hops)"
        signals.append(sig)
        explanations.append(
            f"Detected {cycle_count} closed-loop fund transfer cycle(s) returning to account {norm_acc}."
        )

    # 5. Shared Device Clusters
    if shared_device_count > 0:
        for dev, count in sorted(accounts_per_device.items()):
            sig = f"SHARED_DEVICE: Device {dev} is linked to {count} accounts"
            signals.append(sig)
        explanations.append(
            f"Account {norm_acc} shares {shared_device_count} hardware device(s) with other accounts."
        )

    # 6. Shared IP Clusters
    if shared_ip_count > 0:
        for ip, count in sorted(accounts_per_ip.items()):
            sig = f"SHARED_IP: IP {ip} is linked to {count} accounts"
            signals.append(sig)
        explanations.append(
            f"Account {norm_acc} shares {shared_ip_count} IP address(es) with other accounts."
        )

    # 7. Downstream Reachability
    if reachable_accounts >= 3:
        sig = f"HIGH_DOWNSTREAM_REACH: {reachable_accounts} reachable accounts"
        signals.append(sig)

    signals.sort()
    return signals, explanations
