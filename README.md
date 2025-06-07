# 📚 Smart Pass Manager: A Noise-Aware Transpiler Pass for Qiskit

This repository contains the implementation of **Smart Pass Manager**, a noise-aware transpiler extension for [Qiskit](https://qiskit.org/). It selects a connected subset of physical qubits on IBM Quantum devices based on calibration data to minimize noise during circuit execution.

---

## 🚀 Project Overview

**Smart Pass Manager** enhances the standard Qiskit transpilation pipeline by:

- Building a **noise-weighted coupling graph** from backend properties.
- Selecting a near-optimal set of qubits via a **multi-start greedy heuristic** with **local refinement**.
- Integrating seamlessly with Qiskit's `transpile` function.
- Improving circuit fidelity by reducing gate and readout errors based on live calibration data.

The project is inspired by:  
**Murali et al.**, *Noise-Adaptive Compiler Mappings for Noisy Intermediate-Scale Quantum Computers*, [ASPLOS'19](https://arxiv.org/abs/1901.11054).

---

## 📦 Repository Contents

```
/smart-pass-manager
  ├── smart_transpile.py    # Noise-aware transpiler wrapper
  ├── scoring.py            # Build weighted graph and select qubit patches
  ├── passes.py              # Custom Qiskit transpiler passes
  ├── __init__.py            # Package initialization
  ├── benchmark.ipynb        # Jupyter Notebook: generate, mirror, transpile, simulate circuits
  └── README.md              # This file
```

---

## 🧩 Installation

1. Install Python 3.8+.
2. (Optional but recommended) Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. Install required packages:

```bash
pip install qiskit qiskit-aer numpy matplotlib pandas seaborn jupyterlab
```

---

## 🔨 Usage

1. Clone the repository:

```bash
git clone https://github.com/yourusername/smart-pass-manager.git
cd smart-pass-manager
```

2. Open the Jupyter Notebook:

```bash
jupyter lab benchmark.ipynb
```

or

```bash
jupyter notebook benchmark.ipynb
```

3. Run the notebook cells to:
- Generate random quantum circuits.
- Mirror the circuits (forward + inverse).
- Transpile using both standard Qiskit and Smart Pass Manager.
- Simulate the circuits with realistic noise models from IBM Fake Backends.
- Collect and save results into a Pandas DataFrame.

---

## 📊 Visualization

The notebook provides utilities to:
- Compare **Success Rates** (proxy for fidelity).
- Analyze **Relative Infidelity Reduction (RIR)**.
- Study performance grouped by **backend**, **qubit count**, and **circuit depth**.

Plots are suitable for inclusion in reports or publications.

---

## 📚 Citation

If you use this project in academic work, please cite:

```bibtex
@inproceedings{murali2019noise,
  title={Noise-Adaptive Compiler Mappings for Noisy Intermediate-Scale Quantum Computers},
  author={Murali, Prakash and Baker, Jonathan M and Abhari, Ali Javadi and Chong, Frederic T and Martonosi, Margaret},
  booktitle={Proceedings of the Twenty-Fourth International Conference on Architectural Support for Programming Languages and Operating Systems},
  pages={1015--1029},
  year={2019}
}
```

---

## ⚖️ License

This project is licensed under the **MIT License**.

---

## 🙏 Acknowledgements

This project builds upon the open-source contributions of the Qiskit community and is inspired by the work of Murali et al. Substantial assistance in code development and documentation was provided by ChatGPT (OpenAI GPT-4o), and all content was critically reviewed by the author.
