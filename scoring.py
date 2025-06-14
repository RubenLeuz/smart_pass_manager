"""
scoring.py – Noise-aware coupling-graph builder & patch selector.

Provides:
- WeightHyperParams: auto-scales weights from backend stats.
- build_weighted_graph: directed graph with composite noise weights.
- greedy_pick: picks connected k-qubit patch heuristically.
"""

from __future__ import annotations
import itertools
import random
import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import networkx as nx
from qiskit.providers.backend import Backend

###############################################################################
# Weight hyper-parameters
###############################################################################

@dataclass
class WeightHyperParams:
    """Parameters for composite edge weight; auto-scaled if None."""
    alpha: Optional[float] = None       # 2q error weight
    beta: Optional[float] = None        # readout error weight
    gamma: Optional[float] = None       # proximity penalty
    delta: Optional[float] = None       # decoherence term
    direction_penalty: float = 0.5      # penalty for non-native CX
    distance_weight: float = 0.0        # external distance cost weight

    def auto_scale(self, stats: Dict[str, float], k: int) -> None:
        """
        Fill missing params from backend stats:
        - alpha: mean 2q error / mean 1q error
        - beta: alpha / 2
        - gamma: mean 2q error / k
        - delta: default 0.01
        """
        mean_2q = stats.get("mean_2q_err", stats.get("mean_cx_err", 1e-3))
        if self.alpha is None:
            self.alpha = mean_2q / max(stats.get("mean_1q_err", 1e-6), 1e-6)
        if self.beta is None:
            self.beta = self.alpha / 2
        if self.gamma is None:
            self.gamma = mean_2q / max(k, 1)
        if self.delta is None:
            self.delta = 0.01

###############################################################################
# Backend statistics collector
###############################################################################

def _collect_backend_stats(backend: Backend, props) -> Dict[str, float]:
    """Extract mean/max errors and durations from backend properties."""
    twoq, oneq, ro, dur, t1 = [], [], [], [], []

    # 2Q gates
    for gate in props.gates:
        if len(gate.qubits) == 2:
            err = getattr(gate, "error", None)
            if err is None:
                for p in gate.parameters:
                    if p.name == "gate_error":
                        err = p.value
                        break
            if err is not None:
                twoq.append(err)
            length = getattr(gate, "gate_length", None)
            if length is None:
                for p in gate.parameters:
                    if p.name == "gate_length":
                        length = p.value
                        break
            if length is not None:
                dur.append(length)

    # per-qubit errors
    for qlist in props.qubits:
        for p in qlist:
            if p.name in {"gate_error", "single_qubit_error"}:
                oneq.append(p.value)
            if p.name in {"readout_error", "prob_meas1_prep0"}:
                ro.append(p.value)
            if p.name == "T1":
                t1.append(p.value)

    mean = lambda lst, default: sum(lst) / len(lst) if lst else default
    return {
        "mean_cx_err": mean(twoq, 1e-3),
        "max_cx_err": max(twoq) if twoq else 1e-3,
        "mean_1q_err": mean(oneq, 1e-4),
        "mean_ro_err": mean(ro, 0.02),
        "mean_cx_dur": mean(dur, 1e-6),
        "mean_T1": mean(t1, 60e-6),
    }

###############################################################################
# Graph builder
###############################################################################

def build_weighted_graph(
    backend: BackendV1 | BackendV2,
    props,
    k: int,
    *,
    hyper: WeightHyperParams,
) -> nx.DiGraph:
    """Create directed coupling graph with noise-informed weights."""
    stats = _collect_backend_stats(backend, props)
    hyper.auto_scale(stats, k)

    G = nx.DiGraph()
    n = backend.configuration().n_qubits
    G.add_nodes_from(range(n))

    # extract per-node errors
    oneq_err = {}
    ro_err = {}
    t1 = {}
    for q, plist in enumerate(props.qubits):
        for p in plist:
            if p.name in {"gate_error", "single_qubit_error"}:
                oneq_err[q] = p.value
            if p.name in {"readout_error", "prob_meas1_prep0"}:
                ro_err[q] = p.value
            if p.name == "T1":
                t1[q] = p.value

    # extract CX errors and durations
    cx_err, cx_dur = {}, {}
    for gate in props.gates:
        if len(gate.qubits) == 2:
            ctrl, tgt = gate.qubits
            err = getattr(gate, "error", None)
            dur_val = getattr(gate, "gate_length", None)
            for p in gate.parameters:
                if err is None and p.name == "gate_error":
                    err = p.value
                if dur_val is None and p.name == "gate_length":
                    dur_val = p.value
            if err is not None:
                cx_err[(ctrl, tgt)] = err
            if dur_val is not None:
                cx_dur[(ctrl, tgt)] = dur_val

    default_err = 1.5 * stats.get("max_2q_err", stats["max_cx_err"])

    # add edges
    for ctrl, tgt in backend.configuration().coupling_map:
        base = cx_err.get((ctrl, tgt), default_err)
        length = cx_dur.get((ctrl, tgt), stats["mean_cx_dur"])
        sq = oneq_err.get(ctrl, 0) + oneq_err.get(tgt, 0)
        ro_sum = ro_err.get(ctrl, 0) + ro_err.get(tgt, 0)
        decoh = hyper.delta * length / max(stats["mean_T1"], 1e-6)
        w = base + hyper.alpha * sq + hyper.beta * ro_sum + hyper.gamma + decoh
        G.add_edge(ctrl, tgt, weight=w)

        # reverse penalty
        if (tgt, ctrl) not in cx_err:
            G.add_edge(tgt, ctrl, weight=w + hyper.direction_penalty)

    if G.number_of_edges() == 0:
        warnings.warn("Empty graph: no coupling edges found.")
    return G

###############################################################################
# Patch selection
###############################################################################

def greedy_pick(
    G: nx.DiGraph,
    k: int,
    *,
    num_starts: int = 20,
    seed: Optional[int] = None,
) -> List[int]:
    """Select connected k-node subgraph minimizing total weight."""
    if k > G.number_of_nodes():
        raise ValueError("k exceeds qubit count")
    edges = list(G.edges)
    if not edges:
        raise ValueError("Graph has no edges")

    rng = random.Random(seed)

    def total(patch: Sequence[int]) -> float:
        return sum(d["weight"] for _, _, d in G.subgraph(patch).edges(data=True))

    def grow(edge):
        patch = set(edge)
        while len(patch) < k:
            frontier = []
            for q in patch:
                for nbr in set(G.successors(q)) | set(G.predecessors(q)):
                    if nbr not in patch:
                        w = G[q][nbr]["weight"] if G.has_edge(q, nbr) else G[nbr][q]["weight"]
                        frontier.append((w, nbr))
            if not frontier:
                break
            patch.add(min(frontier)[1])
        return patch

    best, best_w = None, float('inf')
    for edge in rng.sample(edges, min(num_starts, len(edges))):
        p = grow(edge)
        if len(p) == k:
            w = total(p)
            if w < best_w:
                best, best_w = p, w

    if best is None:
        best = set(rng.sample(range(G.number_of_nodes()), k))
    return sorted(best)

__all__ = [
    'WeightHyperParams',
    'build_weighted_graph',
    'greedy_pick',
]
