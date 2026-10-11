"""E0 v3: fit the IonQ simulator's two-qubit error with circuits the compiler cannot cancel.

Why v3: identity (mirror) chains and folded twins come back at P = 1.0 on Qollab's IonQ
backends because the compiler cancels them, and any two-qubit-only chain is resynthesised
into at most three CNOTs. These circuits avoid both: four qubits, a CX ladder whose
consecutive gates never share the same pair (so no two-qubit block is consolidated), an X
gate after every CX (so no adjacent inverse pairs), and the whole thing walks a basis
state, so the correct outcome is known exactly and the decay of P(target) with the number
of CX gates gives the per-gate error.

Four Runs on the IonQ Aria-1 noise-model simulator: set RUN = 1 in the Run-settings form, press
Run, append the printed {"run": ...} line to data/e0_runs.jsonl (delete the old file first),
then RUN = 2, 3, 4. Commit `[thomas] e0 ladder runs`, push. scripts/fit_e0.py does the rest.
"""
import json
import time

from qiskit import QuantumCircuit

SHOTS = 1200
PAIRS = [(0, 1), (1, 2), (2, 3), (3, 0)]


def ladder(depth):
    qc = QuantumCircuit(4)
    bits = [0, 0, 0, 0]
    qc.x(0)
    bits[0] = 1
    for i in range(depth):
        a, b = PAIRS[i % 4]
        qc.cx(a, b)
        bits[b] ^= bits[a]
        q = (i * 3) % 4
        qc.x(q)
        bits[q] ^= 1
    target = "".join(str(bits[q]) for q in reversed(range(4)))
    return qc, target


def circuit_for(run):
    if run == 1:
        return "ro0000", QuantumCircuit(4), "0000"
    if run == 2:
        qc = QuantumCircuit(4)
        qc.x([0, 1, 2, 3])
        return "ro1111", qc, "1111"
    if run == 3:
        qc, t = ladder(12)
        return "ladder_d12", qc, t
    if run == 4:
        qc, t = ladder(36)
        return "ladder_d36", qc, t
    raise ValueError("RUN must be 1..4")


def main(RUN: int = 1):
    """RUN is a field in the Run-settings form: 1, 2, 3, 4."""
    label, qc, target = circuit_for(RUN)
    qc = qc.copy()
    qc.measure_all()
    ops = qc.count_ops()
    n2q = int(ops.get("cx", 0))
    n1q = int(ops.get("x", 0))
    opts = getattr(backend, "options", None)  # noqa: F821 (injected by Qollab)
    t = time.time()
    job = backend.run(qc, shots=SHOTS)  # noqa: F821
    counts = {str(k).replace(" ", ""): int(v) for k, v in job.result().get_counts().items()}
    jid = getattr(job, "job_id", None)
    row = {"run": RUN, "label": label, "target": target, "n2q": n2q, "n1q": n1q, "shots": SHOTS,
           "backend": str(getattr(backend, "name", None)),  # noqa: F821
           "noise_model": str(getattr(opts, "noise_model", None)) if opts is not None else None,
           "p_target": round(counts.get(target, 0) / max(sum(counts.values()), 1), 4),
           "latency_s": round(time.time() - t, 2), "counts": counts,
           "job_id": str(jid() if callable(jid) else jid)}
    print(f"RUN {RUN} ({label}): P(target={target}) = {row['p_target']}, {n2q} CX. Copy the next line into data/e0_runs.jsonl:")
    print(json.dumps(row))
