# 📚 Smart Pass Manager: A Noise-Aware Transpiler Extension for Qiskit

This repository implements **Smart Pass Manager**, a noise-aware extension for the [Qiskit](https://qiskit.org/) transpiler. It selects a connected subset of physical qubits on IBM Quantum backends using live calibration data to minimize noise during circuit execution.

---

## 🚀 Project Highlights

* **Noise‑Weighted Graph**: Builds a directed coupling graph with composite weights capturing two-qubit errors, single-qubit errors, readout errors, decoherence, CX direction fidelity, and proximity.
* **Greedy Patch Selection**: Uses a multi-start, seedable greedy heuristic to pick a low‑noise, connected k-qubit patch.
* **Seamless Qiskit Integration**:

  * **smart\_transpile.py** wraps Qiskit's `transpile`, adding noise‑adaptive layout and metadata.
  * **passes.py** provides `SmartLayoutPass` for custom `PassManager` pipelines.
* **Live Calibration**: Automatically scales hyper‑parameters from backend statistics (mean/max errors, T1 times).

Inspired by **Murali et al.**, *Noise-Adaptive Compiler Mappings for NISQ* ([ASPLOS'19](https://arxiv.org/abs/1901.11054)).

---

## 📦 Repository Structure

```
smart-pass-manager/
├── smart_transpile.py    # Noise‑aware transpile wrapper
├── scoring.py            # Coupling‑graph builder & patch selector
├── passes.py             # Qiskit TransformationPass: SmartLayoutPass
├── benchmark.ipynb       # Notebook: generate, transpile, simulate, analyze
└── README.md             # Project overview and instructions
```

---

## 🛠 Installation

1. **Python**: 3.8+
2. (Recommended) Create & activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate    # Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:

   ```bash
   pip install qiskit qiskit-aer numpy matplotlib pandas networkx
   ```

---

## 🔨 Basic Usage

1. **Clone & enter**:

   ```bash
   git clone https://github.com/yourusername/smart-pass-manager.git
   cd smart-pass-manager
   ```

2. **Standard transpile**:

   ```python
   from qiskit import QuantumCircuit, transpile
   from smart_pass_manager.smart_transpile import smart_transpile

   qc = QuantumCircuit(4, 4)
   # ... build your circuit ...
   backend = provider.get_backend('ibm_nairobi')
   qc_opt = smart_transpile(qc, backend, optimization_level=2, seed=42)
   ```

3. **Custom PassManager**:

   ```python
   from qiskit.transpiler import PassManager
   from smart_pass_manager.passes import SmartLayoutPass

   pm = PassManager([
       SmartLayoutPass(backend, hyper_params=None, seed=42),
       # ... additional Qiskit passes ...
   ])
   qc_opt = transpile(qc, backend, pass_manager=pm, optimization_level=3)
   ```

---

## 📊 Benchmark & Visualization

Open `benchmark.ipynb` to:

* Generate random circuits of varying depth/qubit count
* Transpile with standard Qiskit vs. Smart Pass Manager
* Simulate with IBM Fake Backends noise models
* Compute and plot Fidelity, Relative Infidelity Reduction (RIR)
* Group results by backend, qubit count, circuit depth

Plots use matplotlib and pandas; dataframes are saved for further analysis.

---

## 📚 Citation

If you use this work, please cite:

```bibtex
@inproceedings{murali2019noise,
  title={Noise-Adaptive Compiler Mappings for Noisy Intermediate-Scale Quantum Computers},
  author={Murali, Prakash and Baker, Jonathan M and Abhari, Ali Javadi and Chong, Frederic T and Martonosi, Margaret},
  booktitle={ASPLOS'19},
  pages={1015--1029},
  year={2019}
}
```

---

## ⚖️ License

MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

Built on the Qiskit open-source ecosystem and inspired by Murali et al. Code structure and documentation improved with assistance from ChatGPT (OpenAI).
