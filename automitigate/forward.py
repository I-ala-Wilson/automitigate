"""Forward observables for the proxy validation (fidelity_fwd).

One observable per circuit, ideal value from the statevector:
  ghz4, ghz8 -> <Z...Z> (= 1)            grover3 -> P(marked = 101)
  qaoa6     -> <C> of the ring MaxCut Hamiltonian from one Z-basis measurement
  qft3      -> the product Pauli string with the largest ideal |<P>| (basis change appended)
The same arm is applied to the forward circuit (folds, twirl copies, REM on counts, same shot
budget); the arm's forward estimate E_a is ZNE-extrapolated for ZNE arms, and
fidelity_fwd = 1 - |E_a - E_ideal| / range(observable).
"""
from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from automitigate.arms import SCALES, TWIRL_COPIES, apply_rem, fold, translate, twirl
from automitigate.circuits import CIRCUITS, GROVER3_MARKED, QAOA6_EDGES


def _bit(key: str, q: int) -> int:
    return int(key.replace(" ", "")[-1 - q])


def _probs(counts: dict) -> dict:
    tot = sum(counts.values()) or 1
    return {k.replace(" ", ""): v / tot for k, v in counts.items()}


def _pauli_string_for_qft3() -> list[str]:
    sv = Statevector(CIRCUITS["qft3"]())
    best = []
    for q in range(3):
        vals = {p: abs(float(np.real(sv.expectation_value(_single(p, q, 3))))) for p in "XYZ"}
        best.append(max(vals, key=vals.get))
    return best


def _single(p: str, q: int, n: int):
    from qiskit.quantum_info import Pauli
    label = ["I"] * n
    label[n - 1 - q] = p
    return Pauli("".join(label))


def spec(name: str) -> dict:
    """{'circuit': forward circuit with basis change (no measurements), 'kind', 'ideal', 'range', ...}"""
    qc = CIRCUITS[name]()
    n = qc.num_qubits
    if name.startswith("ghz"):
        from qiskit.quantum_info import Pauli
        ideal = float(np.real(Statevector(qc).expectation_value(Pauli("Z" * n))))
        return {"circuit": qc, "kind": "parity", "ideal": ideal, "range": 2.0, "n": n}
    if name == "grover3":
        probs = Statevector(qc).probabilities_dict()
        return {"circuit": qc, "kind": "marked", "ideal": float(probs.get(GROVER3_MARKED, 0.0)), "range": 1.0,
                "n": n, "marked": GROVER3_MARKED}
    if name == "qaoa6":
        sv = Statevector(qc)
        from qiskit.quantum_info import SparsePauliOp
        terms = []
        for a, b in QAOA6_EDGES:
            label = ["I"] * n
            label[n - 1 - a] = "Z"
            label[n - 1 - b] = "Z"
            terms.append(("".join(label), -0.5))
        op = SparsePauliOp.from_list([("I" * n, 0.5 * len(QAOA6_EDGES))] + terms)
        return {"circuit": qc, "kind": "maxcut", "ideal": float(np.real(sv.expectation_value(op))),
                "range": float(len(QAOA6_EDGES)), "n": n, "edges": QAOA6_EDGES}
    if name == "qft3":
        paulis = _pauli_string_for_qft3()
        sv = Statevector(qc)
        from qiskit.quantum_info import Pauli
        ideal = float(np.real(sv.expectation_value(Pauli("".join(reversed(paulis))))))
        fwd = qc.copy()
        for q, p in enumerate(paulis):
            if p == "X":
                fwd.h(q)
            elif p == "Y":
                fwd.sdg(q)
                fwd.h(q)
        return {"circuit": fwd, "kind": "pauli", "ideal": ideal, "range": 2.0, "n": n, "paulis": paulis}
    raise ValueError(name)


def estimate(counts: dict, sp: dict, perm: list[int] | None = None) -> float:
    """Observable value from Z-basis counts of the (rotated) forward circuit.
    perm[q] = position of logical qubit q in the measured register (transpiler layout)."""
    n = sp["n"]
    perm = perm or list(range(n))
    pr = _probs(counts)
    if sp["kind"] == "parity":
        return float(sum(v * (1 - 2 * (sum(_bit(k, perm[q]) for q in range(n)) % 2)) for k, v in pr.items()))
    if sp["kind"] == "marked":
        return float(sum(v for k, v in pr.items()
                         if "".join(str(_bit(k, perm[q])) for q in reversed(range(n))) == sp["marked"]))
    if sp["kind"] == "maxcut":
        tot = 0.0
        for k, v in pr.items():
            z = [1 - 2 * _bit(k, perm[q]) for q in range(n)]
            tot += v * sum(0.5 * (1 - z[a] * z[b]) for a, b in sp["edges"])
        return float(tot)
    if sp["kind"] == "pauli":
        qs = [q for q, p in enumerate(sp["paulis"]) if p != "I"]
        return float(sum(v * (1 - 2 * (sum(_bit(k, perm[q]) for q in qs) % 2)) for k, v in pr.items()))
    raise ValueError(sp["kind"])


def layout_perm(qc_t) -> list[int]:
    """Logical qubit -> measured position after transpile_once (identity if no routing)."""
    lay = getattr(qc_t, "layout", None)
    if lay is None:
        return list(range(qc_t.num_qubits))
    try:
        fin = lay.final_index_layout(filter_ancillas=True)
        return [int(x) for x in fin]
    except Exception:
        return list(range(qc_t.num_qubits))


def forward_circuits(qc_t_fwd, arm: dict, draw_seed: int) -> list[QuantumCircuit]:
    """The arm applied to the transpiled forward circuit: folds, twirl copies, measure, translate."""
    rng = np.random.default_rng([draw_seed, 2])
    scales = SCALES if arm["zne"] else [1]
    copies = TWIRL_COPIES if arm["twirl"] else 1
    out = []
    for s in scales:
        f = fold(qc_t_fwd, s)
        for _ in range(copies):
            qc = twirl(f, rng) if arm["twirl"] else f.copy()
            qc.measure_all()
            out.append(translate(qc))
    return out


def forward_fidelity(list_of_counts: list[dict], arm: dict, sp: dict, perm: list[int],
                     cal_counts: list[dict] | None = None) -> tuple[float, float]:
    """(fidelity_fwd, E_a) from the counts of forward_circuits in emission order."""
    scales = SCALES if arm["zne"] else [1]
    copies = TWIRL_COPIES if arm["twirl"] else 1
    if arm["rem"]:
        list_of_counts = [apply_rem(c, cal_counts) for c in list_of_counts]
    by_scale = {}
    for i, s in enumerate(scales):
        block = list_of_counts[i * copies:(i + 1) * copies]
        by_scale[s] = float(np.mean([estimate(c, sp, perm) for c in block]))
    if arm["zne"]:
        s = np.array(sorted(by_scale), dtype=float)
        y = np.array([by_scale[k] for k in sorted(by_scale)])
        slope, intercept = np.polyfit(s, y, 1)
        e = float(intercept)
        lo, hi = (-1.0, 1.0) if sp["kind"] in ("parity", "pauli") else (0.0, sp["range"])
        e = min(hi, max(lo, e))
    else:
        e = by_scale[1]
    return float(1.0 - abs(e - sp["ideal"]) / sp["range"]), e
