"""Arms: transpile once, randomised mirror twin, fold, twirl, drift, readout mitigation.

Order of operations, fixed: transpile once (optimisation level 1) -> twin with a
random Pauli layer -> fold -> twirl -> drift -> measure -> basis translation at
optimisation level 0 -> never an optimising transpile again. Any optimising
pass after the twin would cancel the twin, the folds, the twirl Paulis and the
injected drift; any gate outside BASIS would run noiseless in the simulator.
Folding comes before twirling and drift so that every copy of a two-qubit gate
gets its own twirl Paulis and its own error draw, as on hardware.
"""
from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap

BASIS = ["sx", "rz", "x", "cz"]
TRANSLATE_BASIS = BASIS + ["rzz"]  # rzz is only produced by inject_drift (over-rotated cz)
TWO_Q = {"cz", "rzz"}
SCALES = [1, 3, 5]
TWIRL_COPIES = 8
SHOTS_PER_PULL = 1200

ARMS = [
    {"zne": z, "twirl": t, "rem": r}
    for z in (0, 1) for t in (0, 1) for r in (0, 1)
]

_PAULIS = ("I", "X", "Y", "Z")
_MUL = {  # Pauli product ignoring phase
    ("I", "I"): "I", ("I", "X"): "X", ("I", "Y"): "Y", ("I", "Z"): "Z",
    ("X", "I"): "X", ("X", "X"): "I", ("X", "Y"): "Z", ("X", "Z"): "Y",
    ("Y", "I"): "Y", ("Y", "X"): "Z", ("Y", "Y"): "I", ("Y", "Z"): "X",
    ("Z", "I"): "Z", ("Z", "X"): "Y", ("Z", "Y"): "X", ("Z", "Z"): "I",
}


def _cz_conj(pa: str, pb: str) -> tuple[str, str]:
    """Conjugate the Pauli pa (x) pb by CZ: X_a -> X_a Z_b, Y_a -> Y_a Z_b, Z fixed."""
    na = _MUL[(pa, "Z")] if pb in ("X", "Y") else pa
    nb = _MUL[(pb, "Z")] if pa in ("X", "Y") else pb
    return na, nb


def _apply_pauli(qc: QuantumCircuit, p: str, q: int) -> None:
    if p == "X":
        qc.x(q)
    elif p == "Y":
        qc.y(q)
    elif p == "Z":
        qc.z(q)


def _qubit_indices(qc: QuantumCircuit, instr) -> list[int]:
    return [qc.find_bit(q).index for q in instr.qubits]


def transpile_once(qc: QuantumCircuit, chain: list[int], seed: int) -> QuantumCircuit:
    """The only optimising transpile. Linear coupling map of len(chain) local qubits;
    local qubit i stands for physical qubit chain[i] in the noise model."""
    n = len(chain)
    if qc.num_qubits != n:
        raise ValueError(f"circuit has {qc.num_qubits} qubits, chain has {n}")
    cmap = CouplingMap.from_line(n, bidirectional=True)
    return transpile(qc, basis_gates=BASIS, coupling_map=cmap, optimization_level=1,
                     seed_transpiler=seed)


def _conjugated_inverse(op, pauli: str):
    """Pauli * G^-1 * Pauli as one gate, for G in {sx, x, rz}."""
    inv = op.inverse()
    if pauli == "I" or op.name == "x":
        return inv
    if op.name == "sx":  # inv = sxdg; conjugating by Y or Z gives sx, by X gives sxdg
        return op if pauli in ("Y", "Z") else inv
    if op.name == "rz":  # inv = rz(-theta); X or Y flips the sign back
        return op if pauli in ("X", "Y") else inv
    raise ValueError(f"unexpected 1q gate {op.name} in a transpiled circuit")


def build_twin(qc_t: QuantumCircuit, rng: np.random.Generator) -> tuple[QuantumCircuit, str]:
    """Randomised mirror circuit: qc_t, barrier, random Pauli layer Q, then the inverse
    of qc_t gate by gate with the Pauli frame propagated. Net unitary is a Pauli;
    returns the circuit and the ideal output bitstring (little-endian, as counts keys)."""
    n = qc_t.num_qubits
    twin = QuantumCircuit(n, name=f"{qc_t.name}_twin")
    for instr in qc_t.data:
        if instr.operation.name != "barrier":
            twin.append(instr.operation, _qubit_indices(qc_t, instr))
    twin.barrier()
    frame = [str(_PAULIS[k]) for k in rng.integers(0, 4, size=n)]
    for q, p in enumerate(frame):
        _apply_pauli(twin, p, q)
    for instr in reversed(qc_t.data):
        op = instr.operation
        qs = _qubit_indices(qc_t, instr)
        if op.name == "barrier":
            continue
        if op.name == "cz":
            a, b = qs
            twin.cz(a, b)
            frame[a], frame[b] = _cz_conj(frame[a], frame[b])
        elif op.num_qubits == 1:
            twin.append(_conjugated_inverse(op, frame[qs[0]]), qs)
        else:
            raise ValueError(f"unexpected gate {op.name} in a transpiled circuit")
    target = "".join("1" if frame[q] in ("X", "Y") else "0" for q in reversed(range(n)))
    return twin, target


def fold(qc: QuantumCircuit, scale: int) -> QuantumCircuit:
    """Global folding C -> C C^-1 C ... with barriers; scale in {1, 3, 5}."""
    if scale not in SCALES:
        raise ValueError("scale must be 1, 3 or 5")
    out = qc.copy()
    inv = qc.inverse()
    for _ in range((scale - 1) // 2):
        out.barrier()
        out.compose(inv, inplace=True)
        out.barrier()
        out.compose(qc, inplace=True)
    return out


def twirl(qc: QuantumCircuit, rng: np.random.Generator) -> QuantumCircuit:
    """Random Pauli pair before each cz and the compensating pair after; net identity."""
    out = QuantumCircuit(*qc.qregs, *qc.cregs, name=qc.name)
    for instr in qc.data:
        op = instr.operation
        qs = _qubit_indices(qc, instr)
        if op.name == "cz":
            a, b = qs
            pa, pb = (_PAULIS[k] for k in rng.integers(0, 4, size=2))
            _apply_pauli(out, pa, a)
            _apply_pauli(out, pb, b)
            out.cz(a, b)
            ca, cb = _cz_conj(pa, pb)
            _apply_pauli(out, ca, a)
            _apply_pauli(out, cb, b)
        else:
            out.append(op, qs, instr.clbits)
    return out


def inject_drift(qc: QuantumCircuit, p: float, theta: float, rng: np.random.Generator) -> QuantumCircuit:
    """Synthetic drift: each cz becomes an over-rotated cz (rzz(pi/2 + theta) with its
    rz dressing, one two-qubit gate) and, with probability p per qubit, is followed
    by a random Pauli. p = theta = 0 returns an equivalent circuit."""
    if p == 0 and theta == 0:
        return qc.copy()
    out = QuantumCircuit(*qc.qregs, *qc.cregs, name=qc.name)
    for instr in qc.data:
        op = instr.operation
        qs = _qubit_indices(qc, instr)
        if op.name == "cz":
            a, b = qs
            if theta:
                out.rzz(np.pi / 2 + theta, a, b)
                out.rz(-np.pi / 2, a)
                out.rz(-np.pi / 2, b)
            else:
                out.cz(a, b)
            for q in (a, b):
                if p and rng.random() < p:
                    _apply_pauli(out, _PAULIS[1 + rng.integers(0, 3)], q)
        else:
            out.append(op, qs, instr.clbits)
    return out


def translate(qc: QuantumCircuit) -> QuantumCircuit:
    """Basis translation only (optimisation level 0); nothing is cancelled."""
    return transpile(qc, basis_gates=TRANSLATE_BASIS, optimization_level=0)


def two_q_count(qc: QuantumCircuit) -> int:
    return sum(n for g, n in qc.count_ops().items() if g in TWO_Q)


def rem_calibration_circuits(n: int) -> list[QuantumCircuit]:
    zeros = QuantumCircuit(n, name="rem_cal_0")
    zeros.measure_all()
    ones = QuantumCircuit(n, name="rem_cal_1")
    ones.x(range(n))
    ones.measure_all()
    return [zeros, ones]


def _prob_tensor(counts: dict, n: int) -> np.ndarray:
    t = np.zeros((2,) * n)
    tot = sum(counts.values()) or 1
    for key, c in counts.items():
        bits = key.replace(" ", "")[-n:]
        idx = tuple(int(bits[-1 - q]) for q in range(n))  # axis q = qubit q
        t[idx] += c / tot
    return t


def apply_rem(counts: dict, cal_counts: list[dict]) -> dict:
    """Tensored assignment-matrix inversion from the |0..0> and |1..1> calibrations.
    Negative quasi-probabilities are clipped and the result renormalised."""
    n = len(next(iter(counts)).replace(" ", ""))
    cal0, cal1 = (_prob_tensor(c, n) for c in cal_counts)
    t = _prob_tensor(counts, n)
    for q in range(n):
        axes = tuple(i for i in range(n) if i != q)
        e0 = cal0.sum(axis=axes)[1]  # P(read 1 | prep 0)
        e1 = cal1.sum(axis=axes)[0]  # P(read 0 | prep 1)
        a = np.array([[1 - e0, e1], [e0, 1 - e1]])
        a_inv = np.linalg.inv(a) if abs(np.linalg.det(a)) > 1e-9 else np.eye(2)
        t = np.moveaxis(np.tensordot(a_inv, t, axes=([1], [q])), 0, q)
    t = np.clip(t, 0, None)
    s = t.sum()
    if s > 0:
        t /= s
    out = {}
    for idx in np.ndindex(*t.shape):
        if t[idx] > 0:
            key = "".join(str(idx[q]) for q in reversed(range(n)))
            out[key] = float(t[idx])
    return out


def apply_arm(qc_t: QuantumCircuit, arm: dict, twin_rng_seed: int,
              drift: dict | None = None) -> tuple[list[QuantumCircuit], str]:
    """The 1 / 3 / 8 / 24 measured, translated circuits of one pull and the target.
    The twin's Pauli layer depends only on twin_rng_seed, so the eight arms of a
    cell share it; twirl and drift draws come from a second stream."""
    twin, target = build_twin(qc_t, np.random.default_rng(twin_rng_seed))
    rng = np.random.default_rng([twin_rng_seed, 1])
    scales = SCALES if arm["zne"] else [1]
    copies = TWIRL_COPIES if arm["twirl"] else 1
    circs = []
    for s in scales:
        folded = fold(twin, s)
        for _ in range(copies):
            qc = twirl(folded, rng) if arm["twirl"] else folded.copy()
            if drift and (drift.get("p") or drift.get("theta")):
                qc = inject_drift(qc, drift.get("p", 0.0), drift.get("theta", 0.0), rng)
            qc.measure_all()
            circs.append(translate(qc))
    return circs, target


def shots_per_circuit(arm: dict, budget: int = SHOTS_PER_PULL) -> int:
    n = (3 if arm["zne"] else 1) * (TWIRL_COPIES if arm["twirl"] else 1)
    return budget // n
