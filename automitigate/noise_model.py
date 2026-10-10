"""Per-day noise models from ibm_fez calibration data, the IonQ-like static model, and
the simulator entry points. The only module (with scripts/) that imports qiskit_aer."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

HF_REPO = "phanerozoic/qiskit-calibration-drift"
HF_REVISION = "56f55fb89d26e6f33dec7666230c779b0efdefd1"
BACKEND = "ibm_fez"
FAMILIES = ["T1", "T2", "sx_error", "x_error", "cz_error", "readout_error",
            "prob_meas0_prep1", "prob_meas1_prep0", "cz_length", "sx_length", "readout_length"]
COLUMNS = ["backend", "property_family", "qubit_a", "qubit_b", "value", "unit",
           "is_failure_ceiling", "calibrated_time", "observed_time", "chipwide_recal_event_id"]
RAW_PATH = Path("data/raw/train.parquet")
DAILY_PATH = Path("data/calibration_daily_fez.parquet")
E0_PATH = Path("data/e0.json")
IONQ_DEFAULTS = {"p1": 0.0005, "p2": 0.006, "r": 0.004}


class SkipDay(Exception):
    """A chain qubit or edge has no usable value on this day."""


def seed_for(*parts) -> int:
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(h[:4], "big") % (2 ** 31)


# ---------------------------------------------------------------- calibration data

def load_calibration(path=RAW_PATH) -> pd.DataFrame:
    """ibm_fez rows of the families we use, T1/T2 normalised to microseconds."""
    df = pd.read_parquet(path, columns=COLUMNS,
                         filters=[("backend", "==", BACKEND), ("property_family", "in", FAMILIES)])
    df = df.drop(columns=["backend"]).reset_index(drop=True)
    t = df.property_family.isin(["T1", "T2"]) & df.unit.isna()
    df.loc[t, "value"] = df.loc[t, "value"] * 1e6  # seconds -> microseconds
    df["qubit_b"] = df["qubit_b"].astype("Float64")
    df["is_failure_ceiling"] = df["is_failure_ceiling"].fillna(False).astype(bool)
    return df


def derive_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Long daily table: one row per (property, qubit_a, qubit_b, day) with the latest
    value observed on or before the end of that day (last value carried forward)."""
    df = df.sort_values("observed_time")
    df = df.assign(day=df.observed_time.dt.floor("D").dt.strftime("%Y-%m-%d"),
                   qb=df.qubit_b.fillna(-1).astype(int))
    last = df.groupby(["property_family", "qubit_a", "qb", "day"], sort=True).agg(
        value=("value", "last"), ceiling=("is_failure_ceiling", "last"),
        recal=("chipwide_recal_event_id", "last")).reset_index()
    days = sorted(df.day.unique())
    wide_v = last.pivot(index=["property_family", "qubit_a", "qb"], columns="day", values="value")
    wide_c = last.pivot(index=["property_family", "qubit_a", "qb"], columns="day", values="ceiling")
    wide_v = wide_v.reindex(columns=days).ffill(axis=1)
    wide_c = wide_c.reindex(columns=days).ffill(axis=1).fillna(False).astype(bool)
    out = wide_v.stack().rename("value").to_frame()
    out["ceiling"] = wide_c.stack()
    out = out.reset_index().rename(columns={"level_3": "day"})
    recal_days = sorted(set(last.loc[last.recal.notna(), "day"]))
    out.attrs["recal_days"] = recal_days
    return out[["property_family", "qubit_a", "qb", "day", "value", "ceiling"]]


def load_daily(path=DAILY_PATH) -> pd.DataFrame:
    d = pd.read_parquet(path)
    meta = Path(path).with_suffix(".json")
    if meta.exists():
        d.attrs.update(json.loads(meta.read_text()))
    return d


def save_daily(daily: pd.DataFrame, path=DAILY_PATH) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(path, index=False)
    Path(path).with_suffix(".json").write_text(json.dumps(
        {"recal_days": daily.attrs.get("recal_days", []), "hf_repo": HF_REPO,
         "hf_revision": HF_REVISION, "backend": BACKEND}, indent=1))


def snapshots(daily: pd.DataFrame) -> list[str]:
    return sorted(daily.day.unique())


def daily_state(daily: pd.DataFrame, day: str) -> dict:
    """{(property, qubit_a, qubit_b): (value, ceiling)} for one day; qubit_b = -1 for 1q."""
    d = daily[daily.day == day]
    return {(p, int(a), int(b)): (float(v), bool(c))
            for p, a, b, v, c in zip(d.property_family, d.qubit_a, d.qb, d.value, d.ceiling)}


def _edge_errors(state: dict) -> dict:
    """Undirected cz error per edge: mean of the two directions; None if either is unusable."""
    directed = {}
    for (p, a, b), (v, c) in state.items():
        if p == "cz_error" and b >= 0:
            directed.setdefault(frozenset((a, b)), []).append(None if (c or not np.isfinite(v) or v >= 0.999) else v)
    out = {}
    for e, vals in directed.items():
        out[e] = None if any(v is None for v in vals) else float(np.mean(vals))
    return out


def first_complete_day(daily: pd.DataFrame, first_day: str | None = None) -> str:
    """First snapshot on or after first_day on which every family we need has been observed
    (the dataset's first day lacks the gate-length families)."""
    need = set(FAMILIES) - {"readout_error"}
    n_q = daily.loc[daily.property_family == "T1", "qubit_a"].nunique()
    n_e = daily.loc[daily.property_family == "cz_error", ["qubit_a", "qb"]].drop_duplicates().shape[0]
    for d in snapshots(daily):
        if first_day and d < first_day:
            continue
        sub = daily[(daily.day == d) & daily.value.notna()]
        cov = sub.groupby("property_family").size()
        ok = all(cov.get(f, 0) >= 0.9 * (n_e if f.startswith("cz") else n_q) for f in need)
        if ok:
            return d
    raise ValueError("no complete day in the table")


def choose_chain(daily: pd.DataFrame, first_day: str, n: int, rank=0) -> list[int]:
    """Connected simple paths of n qubits ranked by mean cz error on the first complete day
    on or after first_day. rank=0 is the best, rank='median' the median path.
    Chosen once, reused every day."""
    state = daily_state(daily, first_complete_day(daily, first_day))
    edges = {e: v for e, v in _edge_errors(state).items() if v is not None}
    need = ("T1", "T2", "sx_error", "x_error", "sx_length", "readout_length",
            "prob_meas1_prep0", "prob_meas0_prep1")
    have = {}
    for (p, a, b), (v, c) in state.items():
        if p in need and b < 0 and not c and np.isfinite(v):
            have.setdefault(a, set()).add(p)
    usable = {a for a, ps in have.items() if len(ps) == len(need)}
    lengths = {frozenset((a, b)) for (p, a, b), (v, c) in state.items()
               if p == "cz_length" and b >= 0 and np.isfinite(v)}
    adj = {}
    for e, v in edges.items():
        a, b = tuple(e)
        if a in usable and b in usable and e in lengths:
            adj.setdefault(a, {})[b] = v
            adj.setdefault(b, {})[a] = v
    paths = []

    def dfs(path, total):
        if len(path) == n:
            if path[0] < path[-1]:
                paths.append((total / (n - 1), list(path)))
            return
        for nb, v in adj.get(path[-1], {}).items():
            if nb not in path:
                path.append(nb)
                dfs(path, total + v)
                path.pop()

    for q in adj:
        dfs([q], 0.0)
    if not paths:
        raise ValueError(f"no chain of length {n} on {first_day}")
    paths.sort(key=lambda t: (t[0], t[1]))
    idx = len(paths) // 2 if rank == "median" else int(rank)
    return paths[idx][1]


def _get(state, prop, a, b=-1):
    v = state.get((prop, a, b))
    if v is None:
        v = state.get((prop, b, a)) if b >= 0 else None
    if v is None or v[1] or not np.isfinite(v[0]):
        raise SkipDay(f"{prop} on {a},{b}")
    return v[0]


def _avg_infidelity(err) -> float:
    from qiskit.quantum_info import average_gate_fidelity
    return 1.0 - average_gate_fidelity(err.to_quantumchannel())


def noise_model_for(daily: pd.DataFrame, day: str, qubits: list[int], f: float = 0.0):
    """Aer noise model on local qubits 0..n-1 standing for physical `qubits` on `day`:
    thermal relaxation (T1, T2, gate and readout durations), depolarising to match
    the reported sx and cz errors, asymmetric readout. A fraction f of each cz
    error is a coherent rzz over-rotation instead of depolarising."""
    from qiskit.circuit.library import RZZGate
    from qiskit_aer.noise import (NoiseModel, ReadoutError, coherent_unitary_error,
                                  depolarizing_error, thermal_relaxation_error)
    state = daily_state(daily, day)
    nm = NoiseModel(basis_gates=["sx", "rz", "x", "cz", "rzz"])
    relax = {}
    for i, q in enumerate(qubits):
        t1 = _get(state, "T1", q)
        t2 = min(_get(state, "T2", q), 2 * t1)
        t_sx = _get(state, "sx_length", q) * 1e-9
        t_ro = _get(state, "readout_length", q) * 1e-9
        relax[i] = (t1 * 1e-6, t2 * 1e-6)
        r1 = thermal_relaxation_error(t1 * 1e-6, t2 * 1e-6, t_sx)
        e_relax = _avg_infidelity(r1)
        for gate, fam in (("sx", "sx_error"), ("x", "x_error")):
            p_dep = max(0.0, 2 * (_get(state, fam, q) - e_relax))
            nm.add_quantum_error(r1.compose(depolarizing_error(min(p_dep, 1.0), 1)), [gate], [i])
        nm.add_quantum_error(thermal_relaxation_error(t1 * 1e-6, t2 * 1e-6, t_ro), ["measure"], [i])
        e0 = _get(state, "prob_meas1_prep0", q)
        e1 = _get(state, "prob_meas0_prep1", q)
        nm.add_readout_error(ReadoutError([[1 - e0, e0], [e1, 1 - e1]]), [i])
    for i in range(len(qubits) - 1):
        a, b = qubits[i], qubits[i + 1]
        vals = []
        for x, y in ((a, b), (b, a)):
            v = state.get(("cz_error", x, y))
            if v is not None and not v[1] and np.isfinite(v[0]) and v[0] < 0.999:
                vals.append(v[0])
        if not vals:
            raise SkipDay(f"cz_error on {a},{b}")
        e_cz = float(np.mean(vals))
        t_cz = _get(state, "cz_length", a, b) * 1e-9
        ra = thermal_relaxation_error(*relax[i], t_cz)
        rb = thermal_relaxation_error(*relax[i + 1], t_cz)
        budget = max(0.0, e_cz - _avg_infidelity(ra.expand(rb)))
        # average-gate-infidelity convention throughout: the coherent rzz(theta) over-rotation
        # carries f * budget (its average infidelity is 0.8 sin^2(theta/2)), the depolarising
        # channel the remaining (1 - f) * budget (average infidelity 3p/4), so the total cz
        # infidelity matches the reported cz_error whatever f is.
        theta = 2 * np.arcsin(np.sqrt(min(1.25 * f * budget, 1.0))) if f > 0 and budget > 0 else 0.0
        p_dep = min(1.0, 4 / 3 * (1 - f) * budget)
        for order, (ra_, rb_) in (((i, i + 1), (ra, rb)), ((i + 1, i), (rb, ra))):
            err = ra_.expand(rb_)
            if theta:
                err = err.compose(coherent_unitary_error(RZZGate(theta).to_matrix()))
            err = err.compose(depolarizing_error(p_dep, 2))
            nm.add_quantum_error(err, ["cz", "rzz"], list(order))
    return nm


# ---------------------------------------------------------------- IonQ-like static model

def ionq_constants(path=E0_PATH) -> dict:
    """p1, p2, r fitted by qollab/e0_checks.py (data/e0.json), else the defaults."""
    c = dict(IONQ_DEFAULTS)
    if Path(path).exists():
        e0 = json.loads(Path(path).read_text())
        if e0.get("p1q_fit"):
            c["p1"] = float(e0["p1q_fit"])
        if e0.get("p2q_fit"):
            c["p2"] = float(e0["p2q_fit"])
        if e0.get("r0_fit") is not None and e0.get("r1_fit") is not None:
            c["r"] = float((e0["r0_fit"] + e0["r1_fit"]) / 2)
    return c


def ionq_static(p1: float, p2: float, r: float = 0.0):
    """Depolarising after every 1q and 2q gate plus a symmetric readout flip r."""
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
    nm = NoiseModel(basis_gates=["sx", "rz", "x", "cz", "rzz"])
    if p1 > 0:
        nm.add_all_qubit_quantum_error(depolarizing_error(min(p1, 1.0), 1), ["sx", "x"])
    if p2 > 0:
        nm.add_all_qubit_quantum_error(depolarizing_error(min(p2, 1.0), 2), ["cz", "rzz"])
    if r > 0:
        nm.add_all_qubit_readout_error(ReadoutError([[1 - r, r], [r, 1 - r]]))
    return nm


def static(p1q: float, p2q: float, readout: float = 0.0):
    """Alias of ionq_static with the calibration-grid argument names."""
    return ionq_static(p1q, p2q, readout)


# ---------------------------------------------------------------- simulation

def run(circs, nm, shots: int, seed: int) -> list[dict]:
    from qiskit_aer import AerSimulator
    # density_matrix is exact and fast for <= 8 qubits; the statevector method (which
    # "automatic" picks at 8 qubits) wedges on these Kraus noise models in Aer 0.17.
    sim = (AerSimulator(noise_model=nm, method="density_matrix", seed_simulator=seed) if nm is not None
           else AerSimulator(seed_simulator=seed))
    res = sim.run(circs, shots=shots).result()
    counts = res.get_counts()
    if isinstance(counts, dict):
        counts = [counts]
    return [dict(c) for c in counts]


def ideal_counts(circ, shots: int, seed: int) -> dict:
    return run([circ], None, shots, seed)[0]


def ideal_expectation(circ, observable) -> float:
    """<observable> on the noiseless statevector of circ (measurements stripped).
    observable: a Pauli label, a SparsePauliOp, or a {bitstring: weight} dict."""
    from qiskit.quantum_info import SparsePauliOp, Statevector
    sv = Statevector(circ.remove_final_measurements(inplace=False))
    if isinstance(observable, dict):
        probs = sv.probabilities_dict()
        return float(sum(w * probs.get(k, 0.0) for k, w in observable.items()))
    if isinstance(observable, str):
        observable = SparsePauliOp(observable)
    return float(np.real(sv.expectation_value(observable)))
