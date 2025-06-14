"""
SmartLayoutPass: Qiskit pass selecting a noise-aware k-qubit patch
and setting it as the initial layout.
"""
from __future__ import annotations
from typing import Optional

from qiskit.transpiler.basepasses import TransformationPass as BasePass
from qiskit.transpiler import Layout, TranspilerError

from .scoring import WeightHyperParams, build_weighted_graph, greedy_pick


class SmartLayoutPass(BasePass):
    """
    Noise-aware layout pass for Qiskit.

    Builds a weighted coupling graph from backend properties,
    picks a k-qubit connected patch, and sets it as the initial layout
    if none is already defined.
    """
    def __init__(
        self,
        backend,
        *,
        hyper_params: Optional[WeightHyperParams] = None,
        picker: Callable[..., list[int]] = greedy_pick,
        seed: Optional[int] = None,
    ):
        super().__init__()
        self.backend = backend
        self.hyper_params = hyper_params or WeightHyperParams()
        self.picker = picker
        self.seed = seed

    def run(self, dag):
        # Skip if layout already set
        if "layout" in self.property_set:
            return dag

        # Build weighted graph and pick patch
        k = dag.num_qubits()
        props = self.backend.properties()
        G = build_weighted_graph(self.backend, props, k, hyper=self.hyper_params)
        try:
            phys_patch = self.picker(G, k, seed=self.seed)
        except Exception as err:
            raise TranspilerError(f"Patch selection failed: {err}") from err

        # Assign layout
        self.property_set["layout"] = Layout.from_intlist(phys_patch)
        return dag
