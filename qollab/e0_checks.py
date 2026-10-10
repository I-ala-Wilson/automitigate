"""E0 checks for the Qollab Code tab, as ONE job (Qollab allows a single backend.run per Run).

How to use (Thomas, by hand): in the Qollab project select IonQ Aria-1 as the QPU,
paste this whole file into the Code tab, press Run, wait for the line
"COPY EVERYTHING BELOW THIS LINE INTO data/e0.json" and copy the JSON block that
follows it into data/e0.json in the repo. Qollab calls main() after loading the file.

Everything is submitted as one list job of ~47 circuits x 1000 shots and read back from
its position in the list. Measured: list-job latency, mirror twin vs its 3x fold (a fold
that scores like the unfolded twin was cancelled by the compiler), two identical circuits
(identical counts = seeded), readout flips, and 1q / 2q depth sweeps fitted to per-gate
depolarising constants p1q_fit, p2q_fit and readout flips r0_fit, r1_fit.
"""
import json
import math
import time
import traceback

from qiskit import QuantumCircuit

SHOTS = 1000
MAX_DEPTH = 20
RZ_ANGLES = [0.37, 1.21, 2.63, 0.84, 1.97, 3.01, 0.52, 2.28, 1.46, 0.11,
             2.85, 1.73, 0.66, 2.09, 1.32, 0.95, 2.51, 1.08, 0.29, 1.88]
TWO_Q_NAMES = {"cz", "cx", "ecr", "ms", "zz", "rzz", "rxx", "ryy", "xx", "yy", "cnot", "swap"}


def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    return qc


def measured(qc):
    m = qc.copy()
    m.measure_all()
    return m


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


def two_q_count(qc):
    return sum(n for g, n in qc.count_ops().items() if g in TWO_Q_NAMES)


def frac(counts, target):
    tot = sum(counts.values()) or 1
    return counts.get(target, 0) / tot


def fit_depolarising(points, base, p_other=0.0, gates_other_per_n=0):
    """points = [(n_gates, P_target)]; model P = base + (1-base) * S * (1-p)^n, S = readout
    survival (fitted intercept). p_other removes a known other-gate contribution."""
    xs, ys = [], []
    for n, p in points:
        y = (p - base) / (1 - base)
        if n > 0 and y > 0.02:
            xs.append(float(n))
            ys.append(math.log(y))
    if len(xs) < 3:
        return None
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    if p_other and gates_other_per_n:
        slope -= gates_other_per_n * math.log(1 - p_other)
    return round(min(1.0, max(0.0, 1.0 - math.exp(slope))), 6)


def job_id_of(job):
    for attr in ("job_id", "id"):
        v = getattr(job, attr, None)
        if v is None:
            continue
        try:
            return str(v() if callable(v) else v)
        except Exception:
            pass
    return None


def build_batch():
    """The one list job: (label, circuit) in order."""
    batch = [("bell", measured(ghz(2))), ("ghz4_a", measured(ghz(4))), ("ghz4_b", measured(ghz(4))),
             ("twin", measured(twin(ghz(4)))), ("fold3", measured(fold3(twin(ghz(4)))))]
    q0 = measured(QuantumCircuit(2))
    q1 = QuantumCircuit(2)
    q1.x([0, 1])
    batch += [("ro00", q0), ("ro11", measured(q1))]
    batch += [(f"d2q_{d}", measured(chain_2q(d))) for d in range(1, MAX_DEPTH + 1)]
    batch += [(f"d1q_{d}", measured(chain_1q(d))) for d in range(1, MAX_DEPTH + 1)]
    return batch


def analyse(R, batch, counts):
    c = dict(zip([lab for lab, _ in batch], counts))
    circ = dict(batch)
    R["bell_counts"] = c["bell"]
    R["bell_p_correct"] = round(frac(c["bell"], "00") + frac(c["bell"], "11"), 4)
    R["repeat_identical"] = c["ghz4_a"] == c["ghz4_b"]
    R["twin_2q_submitted"] = two_q_count(circ["twin"])
    R["fold_2q_submitted"] = two_q_count(circ["fold3"])
    R["twin_p_target"] = round(frac(c["twin"], "0000"), 4)
    R["fold_p_target"] = round(frac(c["fold3"], "0000"), 4)
    se = math.sqrt(max(R["twin_p_target"] * (1 - R["twin_p_target"]), 1e-4) / SHOTS)
    R["fold_survives_compiler"] = R["fold_p_target"] < R["twin_p_target"] - 3 * se
    R["readout_p00_prep00"] = round(frac(c["ro00"], "00"), 4)
    R["readout_p11_prep11"] = round(frac(c["ro11"], "11"), 4)
    R["r0_fit"] = round(1 - math.sqrt(max(R["readout_p00_prep00"], 1e-9)), 5)
    R["r1_fit"] = round(1 - math.sqrt(max(R["readout_p11_prep11"], 1e-9)), 5)
    c1 = [{"depth": d, "n1q_submitted": sum(n for g, n in circ[f"d1q_{d}"].count_ops().items() if g in ("sx", "sxdg", "x")),
           "p_target": round(frac(c[f"d1q_{d}"], "0"), 4)} for d in range(1, MAX_DEPTH + 1)]
    R["depth_curve_1q"] = c1
    R["p1q_fit"] = fit_depolarising([(pt["n1q_submitted"], pt["p_target"]) for pt in c1], 0.5)
    c2 = [{"depth": d, "n2q_submitted": two_q_count(circ[f"d2q_{d}"]), "p_target": round(frac(c[f"d2q_{d}"], "00"), 4)}
          for d in range(1, MAX_DEPTH + 1)]
    R["depth_curve_2q"] = c2
    R["depth_curve"] = c2
    R["p2q_fit"] = fit_depolarising([(pt["n2q_submitted"], pt["p_target"]) for pt in c2], 0.25,
                                    p_other=R.get("p1q_fit") or 0.0, gates_other_per_n=2)


def main():
    R = {"version": 2, "shots": SHOTS, "errors": {}}
    t0 = time.time()

    def log(msg):
        print(f"[e0 {time.time() - t0:6.1f}s] {msg}", flush=True)

    try:
        R["backend_class"] = type(backend).__name__  # noqa: F821 (injected by Qollab)
        R["backend_name"] = str(getattr(backend, "name", None))  # noqa: F821
        R["max_circuits"] = getattr(backend, "max_circuits", None)  # noqa: F821
        try:
            import qiskit
            R["qiskit_version"] = qiskit.__version__
        except Exception:
            pass
        batch = build_batch()
        R["n_circuits_submitted"] = len(batch)
        log(f"submitting one job of {len(batch)} circuits x {SHOTS} shots")
        t = time.time()
        job = backend.run([qc for _, qc in batch], shots=SHOTS)  # noqa: F821
        R["job_id"] = job_id_of(job)
        result = job.result()
        R["latency_s"] = round(time.time() - t, 2)
        counts = result.get_counts()
        if isinstance(counts, dict):
            counts = [counts]
        counts = [{str(k).replace(" ", ""): int(v) for k, v in cc.items()} for cc in counts]
        R["n_results"] = len(counts)
        R["list_jobs_ok"] = len(counts) == len(batch)
        log(f"got {len(counts)} results in {R['latency_s']} s")
        if R["list_jobs_ok"]:
            analyse(R, batch, counts)
            log(f"p1q_fit={R['p1q_fit']} p2q_fit={R['p2q_fit']} r0={R['r0_fit']} r1={R['r1_fit']} "
                f"fold_survives={R['fold_survives_compiler']} repeat_identical={R['repeat_identical']}")
        else:
            R["errors"]["list_job"] = f"expected {len(batch)} results, got {len(counts)}"
    except Exception as exc:
        R["errors"]["run"] = "".join(traceback.format_exception_only(type(exc), exc)).strip()[-400:]
        log(f"FAILED: {R['errors']['run'][:160]}")
    R["elapsed_s"] = round(time.time() - t0, 1)
    R["ok"] = not R["errors"]
    print("=" * 64)
    print("COPY EVERYTHING BELOW THIS LINE INTO data/e0.json")
    print(json.dumps(R, indent=1, default=str))
