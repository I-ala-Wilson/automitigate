"""Spot check of the local IonQ-like model against Qollab's Aria-1 simulator, ONE circuit per Run.

Thomas, by hand, 8 Runs (about a minute each): set RUN = 1, press Run, copy the single line
that starts with {"run": into data/ionq/spot_runs.jsonl (append), then RUN = 2 ... 8.
Commit `[thomas] spot check runs`, push. scripts/spot_compare.py turns the file into
data/ionq/spot_check.json and the comparison line in docs/results.md.

Each Run is one mirror circuit of the arm-0 shape (no ZNE, no twirl) built exactly as the
local sweep builds it: ghz4 or qft3, drift setting A or B from data/calib/ab.json (hard-coded
below from the pushed file), twin seed 0 or 1. The local table has the same cells, so the
comparison is the mean absolute difference of P(target) over the 8 cells.
"""
import json
import time

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap

RUN = 1  # <-- change to 1..8 and press Run each time
SHOTS = 1200
A = {"p": 0.03, "theta": 0.05, "r": 0.0}
B = {"p": 0.01, "theta": 0.15, "r": 0.0}
BASIS = ["sx", "rz", "x", "cz"]
CELLS = [("ghz4", "A", 0), ("ghz4", "A", 1), ("ghz4", "B", 0), ("ghz4", "B", 1),
         ("qft3", "A", 0), ("qft3", "A", 1), ("qft3", "B", 0), ("qft3", "B", 1)]

# --- the same constructions as automitigate.arms, inlined so the file is self-contained ---
_PAULIS = ("I", "X", "Y", "Z")
_MUL = {("I", "I"): "I", ("I", "X"): "X", ("I", "Y"): "Y", ("I", "Z"): "Z", ("X", "I"): "X", ("X", "X"): "I",
        ("X", "Y"): "Z", ("X", "Z"): "Y", ("Y", "I"): "Y", ("Y", "X"): "Z", ("Y", "Y"): "I", ("Y", "Z"): "X",
        ("Z", "I"): "Z", ("Z", "X"): "Y", ("Z", "Y"): "X", ("Z", "Z"): "I"}


def _cz_conj(pa, pb):
    return (_MUL[(pa, "Z")] if pb in ("X", "Y") else pa), (_MUL[(pb, "Z")] if pa in ("X", "Y") else pb)


def _apply_pauli(qc, p, q):
    if p == "X":
        qc.x(q)
    elif p == "Y":
        qc.y(q)
    elif p == "Z":
        qc.z(q)


def _qubits(qc, instr):
    return [qc.find_bit(q).index for q in instr.qubits]


def ghz4():
    qc = QuantumCircuit(4)
    qc.h(0)
    for i in range(3):
        qc.cx(i, i + 1)
    return qc


def qft3():
    from math import pi
    qc = QuantumCircuit(3)
    qc.x(0)
    qc.x(2)
    for j in range(3):
        qc.h(j)
        for k in range(j + 1, 3):
            qc.cp(pi / 2 ** (k - j), k, j)
    qc.swap(0, 2)
    return qc


def seed_for(*parts):
    import hashlib
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(h[:4], "big") % (2 ** 31)


def transpile_once(qc, seed):
    return transpile(qc, basis_gates=BASIS, coupling_map=CouplingMap.from_line(qc.num_qubits, bidirectional=True),
                     optimization_level=1, seed_transpiler=seed)


def conj_inv(op, pauli):
    inv = op.inverse()
    if pauli == "I" or op.name == "x":
        return inv
    if op.name == "sx":
        return op if pauli in ("Y", "Z") else inv
    return op if pauli in ("X", "Y") else inv


def build_twin(qc_t, rng):
    n = qc_t.num_qubits
    twin = QuantumCircuit(n)
    for instr in qc_t.data:
        if instr.operation.name != "barrier":
            twin.append(instr.operation, _qubits(qc_t, instr))
    twin.barrier()
    frame = [_PAULIS[k] for k in rng.integers(0, 4, size=n)]
    for q, p in enumerate(frame):
        _apply_pauli(twin, p, q)
    for instr in reversed(qc_t.data):
        op = instr.operation
        qs = _qubits(qc_t, instr)
        if op.name == "barrier":
            continue
        if op.name == "cz":
            a, b = qs
            twin.cz(a, b)
            frame[a], frame[b] = _cz_conj(frame[a], frame[b])
        else:
            twin.append(conj_inv(op, frame[qs[0]]), qs)
    target = "".join("1" if frame[q] in ("X", "Y") else "0" for q in reversed(range(n)))
    return twin, target


def inject_drift(qc, p, theta, rng):
    out = QuantumCircuit(*qc.qregs)
    for instr in qc.data:
        op = instr.operation
        qs = _qubits(qc, instr)
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
            out.append(op, qs)
    return out


def cell_circuit(circuit, setting, seed):
    qc = ghz4() if circuit == "ghz4" else qft3()
    qc_t = transpile_once(qc, seed_for("transpile", circuit))
    twin, target = build_twin(qc_t, np.random.default_rng(seed_for("twin", circuit, seed)))
    drift = A if setting == "A" else B
    draw_seed = seed_for("draw", circuit, seed, setting)
    rng = np.random.default_rng([draw_seed, 1])
    qc = inject_drift(twin, drift["p"], drift["theta"], rng)
    qc.measure_all()
    return transpile(qc, basis_gates=BASIS + ["rzz"], optimization_level=0), target, drift, draw_seed


def main():
    circuit, setting, seed = CELLS[RUN - 1]
    qc, target, drift, draw_seed = cell_circuit(circuit, setting, seed)
    t = time.time()
    job = backend.run(qc, shots=SHOTS)  # noqa: F821 (injected by Qollab)
    counts = {str(k).replace(" ", ""): int(v) for k, v in job.result().get_counts().items()}
    jid = getattr(job, "job_id", None)
    opts = getattr(backend, "options", None)  # noqa: F821
    row = {"run": RUN, "source": "ionq_aria1", "circuit": circuit, "setting": setting, "drift": drift, "seed": seed,
           "backend": str(getattr(backend, "name", None)),  # noqa: F821
           "noise_model": str(getattr(opts, "noise_model", None)) if opts is not None else None,
           "draw_seed": draw_seed, "arm": 0, "target": target, "shots": SHOTS,
           "score": round(counts.get(target, 0) / max(sum(counts.values()), 1), 4),
           "latency_s": round(time.time() - t, 2), "n2q": sum(n for g, n in qc.count_ops().items() if g in ("cz", "rzz")),
           "job_id": str(jid() if callable(jid) else jid), "counts": counts}
    print(f"RUN {RUN} ({circuit}, {setting}, seed {seed}): P(target) = {row['score']}. Copy the next line into data/ionq/spot_runs.jsonl:")
    print(json.dumps(row))
