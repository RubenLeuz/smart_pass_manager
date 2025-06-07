# passes.py

"""
SmartLayoutPass: Qiskit transformation pass that selects a noise-aware k-qubit patch
and sets it as the initial layout.
"""
from qiskit.transpiler.basepasses import TransformationPass as BasePass
from qiskit.transpiler import Layout, TranspilerError
from .scoring import build_weighted_graph, greedy_pick


class SmartLayoutPass(BasePass):
    """
    Noise-aware layout pass for Qiskit.

    If an initial layout is not yet set, build a weighted graph from
    backend properties, pick a k-qubit patch, and set it as the layout.
    """
    def __init__(self, backend, picker=greedy_pick, *, alpha: float = 0.3, beta: float = 0.2):
        super().__init__()
        self.backend = backend
        self.picker = picker
        self.alpha = alpha
        self.beta = beta

    def run(self, dag):
        if "layout" in self.property_set:
            return dag

        k = dag.num_qubits()
        props = self.backend.properties()
        G = build_weighted_graph(self.backend, props, alpha=self.alpha, beta=self.beta)

        try:
            phys_patch = self.picker(G, k)
        except RuntimeError as err:
            raise TranspilerError(str(err)) from err

        self.property_set["layout"] = Layout.from_intlist(phys_patch)
        return dag


# __init__.py

from .smart_transpile import smart_transpile
from .passes import SmartLayoutPass

__all__ = ["smart_transpile", "SmartLayoutPass"]
