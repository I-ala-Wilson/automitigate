"""E0 checks for the Qollab Code tab.

How to use (Thomas, by hand): in the Qollab project select IonQ Aria-1 as the
QPU, paste this whole file into the Code tab, press Run, wait for the line
"COPY EVERYTHING BELOW THIS LINE INTO data/e0.json" and copy the JSON block
that follows it into data/e0.json in the repo. Nothing here reads or writes
files or touches the network except through the injected `backend`.

What it measures: whether list jobs work and their latency, whether a 3x
folded circuit keeps its two-qubit gates through the compiler, whether repeated
runs give identical counts, readout flip rates, and a depth sweep that is fitted
to per-gate depolarising constants (p1q_fit, p2q_fit) for the IonQ-like model.
"""
import json
import math
import time
import traceback

from qiskit import QuantumCircuit

SHOTS = 1000
MAX_DEPTH = 20
TWO_Q_NAMES = {"cz", "cx", "ecr", "ms", "zz", "rzz", "rxx", "ryy", "xx", "yy", "cnot", "swap"}
RZ_ANGLES = [0.37, 1.21, 2.63, 0.84, 1.97, 3.01, 0.52, 2.28, 1.46, 0.11,
             2.85, 1.73, 0.66, 2.09, 1.32, 0.95, 2.51, 1.08, 0.29, 1.88]

R = {"version": 1, "shots": SHOTS, "errors": {}}
T0 = time.time()


def log(msg):
    print(f"[e0 {time.time() - T0:6.1f}s] {msg}", flush=True)


def probe(name, fn):
    try:
        fn()
    except Exception as exc:  # keep going; the JSON records what failed
        R["errors"][name] = "".join(traceback.format_exception_only(type(exc), exc)).strip()[-300:]
        log(f"{name}: FAILED ({R['errors'][name][:120]})")


def submit(circs, shots=SHOTS):
    """Submit one circuit or a list. Returns (list of counts dicts, job)."""
    job = backend.run(circs, shots=shots)  # noqa: F821 (injected by Qollab)
    counts = job.result().get_counts()
    if isinstance(counts, dict):
        counts = [counts]
    return [{str(k): int(v) for k, v in c.items()} for c in counts], job


def run_many(circs, shots=SHOTS):
    """List job when the backend accepts one, else one job per circuit."""
    if R.get("list_jobs_ok"):
        counts, _ = submit(circs, shots)
        if len(counts) == len(circs):
            return counts
    out = []
    for c in circs:
        out.extend(submit(c, shots)[0])
    return out


def frac(counts, target):
    tot = sum(counts.values()) or 1
    return counts.get(target, 0) / tot


def two_q_count(qc):
    return sum(n for g, n in qc.count_ops().items() if g in TWO_Q_NAMES)


def compiled_two_q(job):
    """Best effort: number of two-qubit gates in whatever the backend compiled."""
    for attr in ("compiled_circuit", "compiled_circuits", "compiled"):
        obj = getattr(job, attr, None)
        if obj is None:
            continue
        try:
            obj = obj() if callable(obj) else obj
        except Exception:
            continue
        R.setdefault("compiled_type", type(obj).__name__)
        R.setdefault("compiled_preview", repr(obj)[:400])
        if isinstance(obj, list) and obj and hasattr(obj[0], "count_ops"):
            obj = obj[0]
        if hasattr(obj, "count_ops"):
            return two_q_count(obj)
        if isinstance(obj, dict):
            gates = obj.get("circuit") or obj.get("gates") or obj.get("instructions") or []
            return sum(1 for g in gates if isinstance(g, dict) and str(g.get("gate", g.get("name", ""))).lower() in TWO_Q_NAMES)
        if isinstance(obj, str):
            low = obj.lower()
            return sum(low.count(f'"{g}"') for g in TWO_Q_NAMES)
    return None


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
    """Mirror circuit with `depth` CZ layers each side; ideal outcome 00."""
    fwd = QuantumCircuit(2)
    for i in range(depth):
        fwd.sx(0)
        fwd.sx(1)
        fwd.rz(RZ_ANGLES[i % len(RZ_ANGLES)], 0)
        fwd.cz(0, 1)
    return twin(fwd)


def chain_1q(depth):
    """Mirror circuit with `depth` sx layers each side on one qubit; ideal outcome 0."""
    fwd = QuantumCircuit(1)
    for i in range(depth):
        fwd.sx(0)
        fwd.rz(RZ_ANGLES[i % len(RZ_ANGLES)], 0)
    return twin(fwd)


def fit_depolarising(points, base, p_other=0.0, gates_other_per_n=0):
    """points = [(n_gates, P_target)]; model P = base + (1-base) * S * (1-p)^n.

    S (readout survival) is the fitted intercept, so readout error does not bias p.
    p_other / gates_other_per_n remove the contribution of the other gate type
    (the 1q dressing inside each 2q layer) when it is already known.
    """
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


def p_backend():
    R["backend_class"] = type(backend).__name__  # noqa: F821
    R["backend_name"] = str(getattr(backend, "name", None))  # noqa: F821
    R["backend_attrs"] = sorted(a for a in dir(backend) if not a.startswith("_"))[:80]  # noqa: F821
    try:
        import qiskit
        R["qiskit_version"] = qiskit.__version__
    except Exception:
        pass


def p_bell():
    counts, job = submit(measured(ghz(2)))
    R["bell_counts"] = counts[0]
    R["bell_p_correct"] = round(frac(counts[0], "00") + frac(counts[0], "11"), 4)
    R["job_attrs"] = sorted(a for a in dir(job) if not a.startswith("_"))[:60]
    R["job_id_example"] = job_id_of(job)
    log(f"bell ok, P(00|11) = {R['bell_p_correct']}")


def p_list_job():
    circs = [measured(ghz(4)) for _ in range(24)]
    t = time.time()
    try:
        counts, job = submit(circs)
        R["latency_s"] = round(time.time() - t, 2)
        R["list_jobs_ok"] = len(counts) == 24
        R["list_job_n_results"] = len(counts)
    except Exception as exc:
        R["list_jobs_ok"] = False
        R["errors"]["list_job"] = str(exc)[:300]
        t = time.time()
        submit(circs[0])
        R["latency_s"] = round(time.time() - t, 2)
    log(f"list job ok = {R['list_jobs_ok']}, latency {R['latency_s']} s")


def p_fold():
    tw = measured(twin(ghz(4)))
    fd = measured(fold3(twin(ghz(4))))
    R["twin_2q_submitted"] = two_q_count(tw)
    R["fold_2q_submitted"] = two_q_count(fd)
    c1, j1 = submit(tw)
    c3, j3 = submit(fd)
    R["twin_p_target"] = round(frac(c1[0], "0000"), 4)
    R["fold_p_target"] = round(frac(c3[0], "0000"), 4)
    R["twin_2q_compiled"] = compiled_two_q(j1)
    R["fold_2q_compiled"] = compiled_two_q(j3)
    R["fold_survives_compiler"] = (
        None if R["fold_2q_compiled"] is None
        else R["fold_2q_compiled"] >= 0.9 * R["fold_2q_submitted"]
    )
    log(f"twin P(0000) = {R['twin_p_target']}, fold3 P(0000) = {R['fold_p_target']}, "
        f"2q submitted {R['fold_2q_submitted']} compiled {R['fold_2q_compiled']}")


def p_repeat():
    a, _ = submit(measured(ghz(4)))
    b, _ = submit(measured(ghz(4)))
    R["repeat_identical"] = a[0] == b[0]
    log(f"repeat identical = {R['repeat_identical']}")


def p_readout():
    q0 = measured(QuantumCircuit(2))
    q1 = QuantumCircuit(2)
    q1.x([0, 1])
    q1 = measured(q1)
    c0, c1 = run_many([q0, q1])
    R["readout_p00_prep00"] = round(frac(c0, "00"), 4)
    R["readout_p11_prep11"] = round(frac(c1, "11"), 4)
    R["r0_fit"] = round(1 - math.sqrt(max(R["readout_p00_prep00"], 1e-9)), 5)
    R["r1_fit"] = round(1 - math.sqrt(max(R["readout_p11_prep11"], 1e-9)), 5)
    log(f"readout: P(00|00) = {R['readout_p00_prep00']}, P(11|11) = {R['readout_p11_prep11']}")


def p_depth_2q():
    depths = list(range(1, MAX_DEPTH + 1))
    circs = [measured(chain_2q(d)) for d in depths]
    counts = run_many(circs)
    curve = []
    for d, qc, c in zip(depths, circs, counts):
        curve.append({"depth": d, "n2q_submitted": two_q_count(qc), "p_target": round(frac(c, "00"), 4)})
    R["depth_curve_2q"] = curve
    R["p2q_fit"] = fit_depolarising([(pt["n2q_submitted"], pt["p_target"]) for pt in curve], 0.25,
                                    p_other=R.get("p1q_fit") or 0.0, gates_other_per_n=2)
    _, jmax = submit(circs[-1])
    R["depth20_2q_compiled"] = compiled_two_q(jmax)
    if R["depth20_2q_compiled"]:
        scale = R["depth20_2q_compiled"] / curve[-1]["n2q_submitted"]
        R["p2q_fit_per_compiled_gate"] = fit_depolarising(
            [(pt["n2q_submitted"] * scale, pt["p_target"]) for pt in curve], 0.25,
            p_other=R.get("p1q_fit") or 0.0, gates_other_per_n=2 / scale)
    log(f"2q depth sweep done, p2q_fit = {R['p2q_fit']}")


def p_depth_1q():
    depths = list(range(1, MAX_DEPTH + 1))
    circs = [measured(chain_1q(d)) for d in depths]
    counts = run_many(circs)
    curve = []
    for d, qc, c in zip(depths, circs, counts):
        n1 = sum(n for g, n in qc.count_ops().items() if g in ("sx", "sxdg", "x"))
        curve.append({"depth": d, "n1q_submitted": n1, "p_target": round(frac(c, "0"), 4)})
    R["depth_curve_1q"] = curve
    R["p1q_fit"] = fit_depolarising([(pt["n1q_submitted"], pt["p_target"]) for pt in curve], 0.5)
    log(f"1q depth sweep done, p1q_fit = {R['p1q_fit']}")


log("start")
probe("backend", p_backend)
probe("bell", p_bell)
probe("list_job", p_list_job)
probe("fold", p_fold)
probe("repeat", p_repeat)
probe("readout", p_readout)
probe("depth_1q", p_depth_1q)
probe("depth_2q", p_depth_2q)
R["elapsed_s"] = round(time.time() - T0, 1)
R["ok"] = not R["errors"]
log(f"done in {R['elapsed_s']} s, errors: {list(R['errors']) or 'none'}")
print("=" * 64)
print("COPY EVERYTHING BELOW THIS LINE INTO data/e0.json")
print(json.dumps(R, indent=1, default=str))
