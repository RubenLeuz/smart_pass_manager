"""smart_transpile.py - Noise-adaptive transpilation helper.

Depends on scoring.py in the same package.
"""

from __future__ import annotations

from typing import Optional

from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap, Layout, PassManager
from qiskit.transpiler.passes import SabreLayout
from qiskit.providers.backend import Backend

from .scoring import WeightHyperParams, build_weighted_graph, greedy_pick

###############################################################################
# Top-level helper
###############################################################################

def _quick_distance_cost(circ: QuantumCircuit, layout: Layout) -> float:
    """Compute Manhattan-distance cost of all 2-qubit operations."""
    cost = 0.0
    for inst, qargs, _ in circ.data:
        if inst.name in {"cx", "cz", "iswap"} and len(qargs) == 2:
            lq0, lq1 = qargs
            p0, p1 = layout[lq0], layout[lq1]
            cost += abs(p0 // 8 - p1 // 8) + abs(p0 % 8 - p1 % 8)
    return cost

###############################################################################
# Main entry point
###############################################################################

def smart_transpile(
    circ: QuantumCircuit,
    backend: BackendV1 | BackendV2,
    *,
    optimization_level: int = 3,
    hyper_params: Optional[WeightHyperParams] = None,
    seed: Optional[int] = None,
    dynamic_fallback: bool = True,
):
    """Noise-aware transpilation wrapper.

    Parameters
    ----------
    circ : QuantumCircuit
        The logical circuit to transpile.
    backend : Qiskit backend
        Target backend providing coupling map and properties.
    optimization_level : int, default=3
        Qiskit optimization level for final transpile.
    hyper_params : WeightHyperParams or None
        Hyper-parameters for weighting; auto-filled if None.
    seed : int or None
        Seed for reproducible layout and transpilation.
    dynamic_fallback : bool, default=True
        If True and circuit has ≤8 qubits, use default transpile.
    """
    if hyper_params is None:
        hyper_params = WeightHyperParams()

    k = circ.num_qubits

    # Fallback for small circuits
    if dynamic_fallback and k <= 8:
        return transpile(
            circ,
            backend=backend,
            optimization_level=optimization_level,
            seed_transpiler=seed,
        )

    props = backend.properties()

    # Build weighted coupling graph and select initial layout
    G = build_weighted_graph(backend, props, k, hyper=hyper_params)
    phys_patch = greedy_pick(G, k, num_starts=25, seed=seed)
    init_layout = Layout({circ.qubits[i]: phys_patch[i] for i in range(k)})

    # Distance cost estimation
    dist_cost = 0.0
    if hyper_params.distance_weight > 0:
        dist_cost = hyper_params.distance_weight * _quick_distance_cost(circ, init_layout)

    # Sabre layout pass
    sabre = SabreLayout(
        coupling_map=CouplingMap(backend.configuration().coupling_map),
        max_iterations=1,
        seed=seed,
    )
    pm = PassManager([sabre])
    circ_tmp = pm.run(circ, property_set={"layout": init_layout})

    # Final transpilation pass
    qc_opt = transpile(
        circ_tmp,
        backend=backend,
        optimization_level=optimization_level,
        seed_transpiler=seed,
    )

    # Attach metadata
    qc_opt.metadata = qc_opt.metadata or {}
    qc_opt.metadata.update({
        "smartlayout": {
            "phys_qubits": phys_patch,
            "num_qubits": k,
            "weights": hyper_params.__dict__,
            "distance_cost": dist_cost,
            "calib_time": props.last_update_date.isoformat(),
        }
    })
    return qc_opt

###############################################################################
# Compatibility wrapper
###############################################################################

def smart_transpile_legacy(
    circ: QuantumCircuit,
    backend: BackendV1 | BackendV2,
    *,
    optimization_level: int = 3,
    alpha: float | None = None,
    beta: float | None = None,
    gamma: float | None = None,
    seed: int | None = None,
    dynamic_fallback: bool = True,
):
    """Legacy interface with alpha, beta, gamma parameters."""
    params = WeightHyperParams(alpha=alpha, beta=beta, gamma=gamma)
    return smart_transpile(
        circ,
        backend,
        optimization_level=optimization_level,
        hyper_params=params,
        seed=seed,
        dynamic_fallback=dynamic_fallback,
    )

###############################################################################
# Module exports
###############################################################################

__all__ = [
    "smart_transpile",
    "smart_transpile_legacy",
]
