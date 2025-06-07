# Smart Pass Manager: A Noise-Aware Transpiler Pass for Qiskit

This repository contains the implementation of **Smart Pass Manager**, a noise-aware transpiler extension for [Qiskit](https://qiskit.org/). It selects a connected subset of physical qubits on IBM Quantum devices based on calibration data to minimize noise during circuit execution.

## 🚀 Project Overview

**Smart Pass Manager** enhances the standard Qiskit transpilation pipeline by:

- Building a **noise-weighted coupling graph** from backend properties.
- Selecting a near-optimal set of qubits via a **multi-start greedy heuristic** with **local refinement**.
- Integrating seamlessly with Qiskit's `transpile` function.
- Improving circuit fidelity by reducing gate and readout errors based on live calibration data.

The project is inspired by [Murali et al., ASPLOS'19](https://arxiv.org/abs/1901.11054).

---

## 📦 Repository Contents
