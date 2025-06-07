# smart_transpile.py

"""
Transpile a circuit in a hardware- and noise-aware manner, using the same seed
for both layout selection and the Qiskit transpiler.
"""
from qiskit import transpile
from qiskit.transpiler import Layout
from .scoring import build_weighted_graph, greedy_pick


def smart_transpile(circ, backend, *, optimization_level: int = 3, alpha: float = 0.3, beta: float = 0.2, seed: int = None):
    """
    - Build a noise-weighted coupling graph.
    - Use greedy_pick with seed for deterministic layout.
    - Transpile with seed for reproducible routing and optimization.
    """
    props = backend.properties()
    G = build_weighted_graph(backend, props, alpha=alpha, beta=beta)
    k = circ.num_qubits

    phys_patch = greedy_pick(G, k, num_starts=15, seed=seed)

    init_layout = Layout({circ.qubits[i]: phys_patch[i] for i in range(len(phys_patch))})

    qc_opt = transpile(
        circ,
        backend=backend,
        initial_layout=init_layout,
        optimization_level=optimization_level,
        seed_transpiler=seed
    )

    qc_opt.metadata = qc_opt.metadata or {}
    qc_opt.metadata["smartlayout"] = {
        "num_qubits": k,
        "phys_qubits": phys_patch,
        "alpha": alpha,
        "beta": beta,
        "calib_time": props.last_update_date.isoformat(),
    }
    return qc_opt
