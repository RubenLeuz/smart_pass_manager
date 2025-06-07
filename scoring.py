# scoring.py

"""
Helper functions to build a noise-weighted coupling graph from an IBM backend
and to select a connected k-qubit patch with minimal aggregate noise.
"""
from typing import List
import warnings
import random

try:
    import networkx as nx
except ImportError:
    nx = None


def build_weighted_graph(backend, props, alpha: float = 0.3, beta: float = 0.2):
    """
    Construct a weighted coupling graph for the given backend.

    - Add all physical qubits (0..n_qubits-1) as nodes.
    - Collect native 2-qubit gate errors from props.gates.
    - Collect single-qubit and readout errors from props.qubits.
    - For each edge in backend.configuration().coupling_map:
        • Use the native 2-qubit error if available; otherwise DEFAULT_WEIGHT.
        • Add alpha * (sum of the two single-qubit errors) + beta * (sum of the two readout errors).
    - Return a NetworkX graph with 'weight' on each edge.
    """
    if nx is None:
        raise ImportError("Please install networkx: pip install networkx")

    G = nx.Graph()
    n_qubits = backend.configuration().n_qubits

    # Add all physical qubits as nodes
    for q in range(n_qubits):
        G.add_node(q)

    # Gather all 2-qubit errors
    twoq_err = {}
    for gate in props.gates:
        if len(gate.qubits) == 2:
            q0, q1 = gate.qubits
            if getattr(gate, "error", None) is not None:
                err = gate.error
            else:
                err = None
                for param in gate.parameters:
                    if getattr(param, "name", "") == "gate_error":
                        err = param.value
                        break
                if err is None:
                    continue
            pair = (min(q0, q1), max(q0, q1))
            existing = twoq_err.get(pair)
            if existing is None or err < existing:
                twoq_err[pair] = err

    # Collect single-qubit and readout errors
    oneq_err = {}
    readout_err = {}
    for idx, param_list in enumerate(props.qubits):
        for param in param_list:
            name = getattr(param, "name", "")
            if name in {"gate_error", "single_qubit_error"}:
                oneq_err[idx] = param.value
            if name in {"readout_error", "prob_meas1_prep0"}:
                readout_err[idx] = param.value

    # Get the coupling map
    coupling_map = backend.configuration().coupling_map
    if not coupling_map:
        warnings.warn("Backend has no coupling_map; graph will have isolated nodes.")
        return G

    DEFAULT_WEIGHT = 10.0
    for q0, q1 in coupling_map:
        pair = (min(q0, q1), max(q0, q1))
        e2 = twoq_err.get(pair, DEFAULT_WEIGHT)
        e1_sum = oneq_err.get(q0, 0.0) + oneq_err.get(q1, 0.0)
        r_sum = readout_err.get(q0, 0.0) + readout_err.get(q1, 0.0)
        weight = e2 + alpha * e1_sum + beta * r_sum
        G.add_edge(q0, q1, weight=weight)

    if G.number_of_edges() == 0:
        warnings.warn("Graph still has no edges after processing the coupling_map.")

    return G


def greedy_pick(G: "nx.Graph", k: int, num_starts: int = 15, seed: int = None) -> List[int]:
    """
    Heuristically select a connected k-qubit patch in G (deterministic via seed).

    1. Initialize a local RNG with `seed`.
    2. Sample up to `num_starts` random start edges.
    3. For each start edge, grow a patch of size k by greedily adding the lowest-weight neighbor.
    4. Keep the patch with minimal total edge weight.
    5. Perform local refinement (single-node swaps) until no further improvement.
    """
    if nx is None:
        raise ImportError("Please install networkx: pip install networkx")
    if k > G.number_of_nodes():
        raise ValueError(f"{k} > number of qubits ({G.number_of_nodes()}).")

    rng = random.Random(seed)

    def total_weight(patch: set) -> float:
        return sum(d["weight"] for _, _, d in G.subgraph(patch).edges(data=True))

    def grow_from_edge(edge: tuple) -> set:
        q0, q1 = edge
        patch = {q0, q1}
        while len(patch) < k:
            frontier = []
            for u in patch:
                for nbr in G.neighbors(u):
                    if nbr not in patch:
                        front_w = G[u][nbr].get("weight", float("inf"))
                        frontier.append((front_w, nbr))
            if not frontier:
                break
            _, candidate = min(frontier, key=lambda x: x[0])
            patch.add(candidate)
        return patch

    all_edges = list(G.edges)
    if not all_edges:
        raise ValueError("No edges in graph; cannot build a connected patch.")

    starts = min(num_starts, len(all_edges))
    start_edges = rng.sample(all_edges, starts)

    best_patch = None
    best_w = float("inf")
    for edge in start_edges:
        patch = grow_from_edge(edge)
        if len(patch) < k:
            continue
        w = total_weight(patch)
        if w < best_w:
            best_w = w
            best_patch = patch.copy()

    if best_patch is None:
        u_min, v_min = min(all_edges, key=lambda e: G[e[0]][e[1]]["weight"])
        best_patch = grow_from_edge((u_min, v_min))
        best_w = total_weight(best_patch)

    improved = True
    while improved:
        improved = False
        boundary = {nbr for u in best_patch for nbr in G.neighbors(u) if nbr not in best_patch}
        curr_w = best_w
        for i in sorted(best_patch):
            for w in sorted(boundary):
                if w in best_patch:
                    continue
                temp_patch = best_patch.copy()
                temp_patch.remove(i)
                temp_patch.add(w)
                if not nx.is_connected(G.subgraph(temp_patch)):
                    continue
                new_w = total_weight(temp_patch)
                if new_w < curr_w:
                    best_patch = temp_patch
                    best_w = new_w
                    improved = True
                    break
            if improved:
                break

    return list(best_patch)
