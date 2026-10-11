"""E0 checks for Qollab, ONE circuit per Run (Qollab's IonQ simulator accepts one circuit per job
and one job per code run).

By hand, 7 Runs of about a minute each:
  1. set RUN = 1 below, press Run, copy the single line that starts with {"run": into the file
     data/e0_runs.jsonl in the repo (one line per Run, append).
  2. set RUN = 2, Run, copy the line. Repeat up to RUN = 7.
  3. commit `[thomas] e0 runs`, push. Ian's script fits the constants from that file.
Qollab calls main() after loading the file.
"""
import json
import time

from qiskit import QuantumCircuit

RUN = 1  # <-- change to 1, 2, 3, 4, 5, 6, 7 and press Run each time
SHOTS = 1200  # IonQ simulator rejects 5000 ("TooManyShots"); 1200 works
RZ_ANGLES = [0.37, 1.21, 2.63, 0.84, 1.97, 3.01, 0.52, 2.28, 1.46, 0.11,
             2.85, 1.73, 0.66, 2.09, 1.32, 0.95, 2.51, 1.08, 0.29, 1.88]


def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    return qc


def twin(qc):
    t = qc.copy()
    t.barrier()
    t.compose(qc.inverse(), inplace=True)
    return t


def fold3(qc):
    f = qc.copy()
    f.barrier()
    f.compose(qc.inverse(), inplace=True)
    f.barrier()
    f.compose(qc, inplace=True)
    return f


def chain_2q(depth):
    fwd = QuantumCircuit(2)
    for i in range(depth):
        fwd.sx(0)
        fwd.sx(1)
        fwd.rz(RZ_ANGLES[i % len(RZ_ANGLES)], 0)
        fwd.cz(0, 1)
    return twin(fwd)


def chain_1q(depth):
    fwd = QuantumCircuit(1)
    for i in range(depth):
        fwd.sx(0)
        fwd.rz(RZ_ANGLES[i % len(RZ_ANGLES)], 0)
    return twin(fwd)


def circuit_for(run):
    if run == 1:
        return "ro00", QuantumCircuit(2), "00"
    if run == 2:
        qc = QuantumCircuit(2)
        qc.x([0, 1])
        return "ro11", qc, "11"
    if run == 3:
        return "twin_ghz4", twin(ghz(4)), "0000"
    if run == 4:
        return "fold3_ghz4", fold3(twin(ghz(4))), "0000"
    if run == 5:
        return "chain2q_d10", chain_2q(10), "00"
    if run == 6:
        return "chain2q_d20", chain_2q(20), "00"
    if run == 7:
        return "chain1q_d20", chain_1q(20), "0"
    raise ValueError("RUN must be 1..7")


def main():
    label, qc, target = circuit_for(RUN)
    qc = qc.copy()
    qc.measure_all()
    ops = qc.count_ops()
    n2q = sum(n for g, n in ops.items() if g in ("cz", "cx"))
    n1q = sum(n for g, n in ops.items() if g in ("sx", "sxdg", "x"))
    t = time.time()
    job = backend.run(qc, shots=SHOTS)  # noqa: F821 (injected by Qollab)
    counts = job.result().get_counts()
    counts = {str(k).replace(" ", ""): int(v) for k, v in counts.items()}
    opts = getattr(backend, "options", None)  # noqa: F821
    row = {"run": RUN, "label": label, "target": target, "n2q": n2q, "n1q": n1q, "shots": SHOTS,
           "backend": str(getattr(backend, "name", None)),  # noqa: F821
           "noise_model": str(getattr(opts, "noise_model", None)) if opts is not None else None,
           "p_target": round(counts.get(target, 0) / max(sum(counts.values()), 1), 4),
           "latency_s": round(time.time() - t, 2), "counts": counts,
           "job_id": str(getattr(job, "job_id", lambda: None)() if callable(getattr(job, "job_id", None)) else getattr(job, "job_id", None))}
    print(f"RUN {RUN} ({label}): P(target) = {row['p_target']} in {row['latency_s']} s. Copy the next line into data/e0_runs.jsonl:")
    print(json.dumps(row))
