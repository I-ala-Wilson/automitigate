"""Reward-table sweep. One JSONL row per (cell, arm); resumable from its own output.

  --source static     grid over --p/--theta/--r (IonQ-like constants from data/e0.json)
  --source ionq_like  drift schedules stable|slow|jump between A and B (data/calib/ab.json)
  --source ibm        one noise model per observed day of ibm_fez calibration data

Per cell (snapshot or step, circuit, seed): the four (zne, twirl) circuit shapes are run
as four simulator jobs (1200 / 400 / 150 / 50 shots per circuit, equal 1200-shot budget)
plus the two readout-calibration circuits; the eight arms are scored from those counts.
Prints a `#progress` line every 30 s with rows/min and an ETA.
"""
import argparse
import itertools
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from automitigate import noise_model as nm  # noqa: E402
from automitigate.arms import ARMS, SHOTS_PER_PULL, apply_arm, rem_calibration_circuits, shots_per_circuit, transpile_once  # noqa: E402
from automitigate.circuits import CIRCUITS  # noqa: E402
from automitigate.score import score_pull  # noqa: E402

SHAPES = [(0, 0), (0, 1), (1, 0), (1, 1)]  # (zne, twirl); rem arms reuse the counts
SOURCE_NAME = {"static": "aer_static", "ionq_like": "aer_ionq_like", "ibm": "aer_ibm_fez"}
KEY_FIELDS = ("source", "snapshot", "schedule", "step", "circuit", "arm", "seed", "f", "chain_rank", "shots", "p", "theta", "r")


def parse_floats(s):
    return [float(x) for x in s.split(",")] if s else [0.0]


def parse_seeds(s):
    if "-" in s:
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]


def row_key(row):
    d = row.get("drift") or {}
    return (row["source"], row["snapshot"], row["schedule"], row["step"], row["circuit"], row["arm"],
            row["seed"], row["f"], str(row["chain_rank"]), row["shots"], d.get("p", 0.0), d.get("theta", 0.0), d.get("r", 0.0))


def load_done(path):
    done = set()
    if path.exists():
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        done.add(row_key(json.loads(line)))
                    except Exception:
                        pass
    return done


def schedules(ab, steps):
    A, B = ab["A"], ab["B"]

    def lerp(t):
        w = t / max(steps - 1, 1)
        return {k: (1 - w) * A[k] + w * B[k] for k in ("p", "theta", "r")}

    return {
        "stable": lambda t: dict(A),
        "slow": lerp,
        "jump": lambda t: dict(A) if t < steps // 2 else dict(B),
    }


class Sweep:
    def __init__(self, args):
        self.a = args
        self.out = Path(args.out)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.done = load_done(self.out)
        self.fh = open(self.out, "a")
        self.sets = {}  # (circuit, seed, p, theta, draw_seed) -> (sets by shape, target)
        self.qct = {}  # circuit -> transpiled circuit
        self.chains = {}
        self.models = {}
        self.t0 = time.time()
        self.t_last = self.t0
        self.n_rows = 0
        self.n_cells = 0
        self.const = nm.ionq_constants()
        self.skipped = {}
        if args.forward and not (ROOT / "automitigate" / "forward.py").exists():
            sys.exit("--forward needs automitigate/forward.py (forward observables land Saturday)")

    # ---- circuits
    def transpiled(self, circuit):
        if circuit not in self.qct:
            qc = CIRCUITS[circuit]()
            chain = self.chain_for(qc.num_qubits)
            self.qct[circuit] = transpile_once(qc, chain, seed=nm.seed_for("transpile", circuit))
        return self.qct[circuit]

    def chain_for(self, n):
        if n not in self.chains:
            if self.a.source == "ibm":
                rank = "median" if self.a.chain_rank == "median" else int(self.a.chain_rank)
                self.chains[n] = nm.choose_chain(self.daily, self.days[0], n, rank)
            else:
                self.chains[n] = list(range(n))
        return self.chains[n]

    def circuit_sets(self, circuit, seed, drift, draw_seed):
        key = (circuit, seed, drift["p"], drift["theta"], draw_seed)
        if key not in self.sets:
            qc_t = self.transpiled(circuit)
            twin_seed = nm.seed_for("twin", circuit, seed)
            sets, target = {}, None
            for z, t in SHAPES:
                circs, target = apply_arm(qc_t, {"zne": z, "twirl": t, "rem": 0}, twin_seed,
                                          drift if (drift["p"] or drift["theta"]) else None, draw_seed)
                sets[(z, t)] = circs
            if len(self.sets) > 64:
                self.sets.clear()
            self.sets[key] = (sets, target)
        return self.sets[key]

    # ---- one cell = 8 rows
    def run_cell(self, meta, circuit, seed, model, drift, draw_seed, shots):
        t_cell = time.time()
        sets, target = self.circuit_sets(circuit, seed, drift, draw_seed)
        n = len(target)
        base = (meta["source"], meta["snapshot"], meta["schedule"], meta["step"], circuit, seed, meta["f"], shots,
                drift["p"], drift["theta"], drift["r"])
        counts = {}
        for shape, circs in sets.items():
            arm = {"zne": shape[0], "twirl": shape[1], "rem": 0}
            counts[shape] = nm.run(circs, model, shots_per_circuit(arm, shots), nm.seed_for(*base, shape))
        cal = nm.run(rem_calibration_circuits(n), model, shots, nm.seed_for(*base, "cal"))
        rows = []
        for arm_id, arm in enumerate(ARMS):
            shape = (arm["zne"], arm["twirl"])
            score, aux = score_pull(counts[shape], arm, target, n, cal if arm["rem"] else None)
            rows.append({**meta, "circuit": circuit, "chain": self.chain_for(n), "arm": arm_id, "seed": seed,
                         "target": target, "score": score, "aux": aux, "fidelity_fwd": None,
                         "n_circuits": len(sets[shape]) + (2 if arm["rem"] else 0), "shots": shots,
                         "job_id": None, "laptop": self.a.laptop, "drift": dict(drift),
                         "model": dict(self.const), "t_cell_s": round(time.time() - t_cell, 3)})
        for r in rows:
            self.fh.write(json.dumps(r) + "\n")
        self.fh.flush()
        self.n_rows += len(rows)
        self.n_cells += 1

    def progress(self, total):
        now = time.time()
        if now - self.t_last < 30 and self.n_cells < total:
            return
        self.t_last = now
        el = now - self.t0
        rate = self.n_cells / el if el > 0 else 0
        eta = (total - self.n_cells) / rate if rate > 0 else -1
        pct = 100.0 * self.n_cells / total if total else 100.0
        print(f"#progress {self.n_cells}/{total} {pct:.1f} eta_s={eta:.0f} rows_per_min={60 * rate * 8:.0f} "
              f"s_per_cell={1 / rate if rate else 0:.2f}", flush=True)

    # ---- sources
    def cells_static(self):
        for shots in self.a.shots:
            for p, theta, r in itertools.product(self.a.p, self.a.theta, self.a.r):
                for seed in self.a.seeds:
                    for circuit in self.a.circuits:
                        meta = {"source": SOURCE_NAME["static"], "snapshot": None, "schedule": None, "step": 0,
                                "chain_rank": 0, "f": 0.0}
                        drift = {"p": p, "theta": theta, "r": r}
                        yield meta, circuit, seed, drift, nm.seed_for("draw", circuit, seed, p, theta), shots, None

    def cells_ionq_like(self):
        ab = json.loads((ROOT / "data" / "calib" / "ab.json").read_text())
        sch = schedules(ab, self.a.steps)
        for name in self.a.schedule:
            for seed in self.a.seeds:
                for step in range(self.a.steps):
                    drift = sch[name](step)
                    for circuit in self.a.circuits:
                        meta = {"source": SOURCE_NAME["ionq_like"], "snapshot": None, "schedule": name, "step": step,
                                "chain_rank": 0, "f": 0.0}
                        yield meta, circuit, seed, drift, nm.seed_for("draw", circuit, seed, name, step), self.a.shots[0], None

    def cells_ibm(self):
        for seed in self.a.seeds:
            for day in self.days:
                for circuit in self.a.circuits:
                    meta = {"source": SOURCE_NAME["ibm"], "snapshot": day, "schedule": None, "step": 0,
                            "chain_rank": self.a.chain_rank, "f": self.a.f}
                    drift = {"p": 0.0, "theta": 0.0, "r": 0.0}
                    yield meta, circuit, seed, drift, nm.seed_for("draw", circuit, seed), self.a.shots[0], day

    def model_for(self, source, drift, day, n):
        if source == "ibm":
            key = (day, n)
            if key not in self.models:
                if len(self.models) > 8:
                    self.models.clear()
                self.models[key] = nm.noise_model_for(self.daily, day, self.chain_for(n), f=self.a.f)
            return self.models[key]
        c = self.const
        return nm.ionq_static(c["p1"], c["p2"], c["r"] + drift["r"])

    def run(self):
        a = self.a
        if a.source == "ibm":
            self.daily = nm.load_daily()
            days = nm.snapshots(self.daily)
            if a.days:
                lo, hi = a.days.split(":")
                days = [d for d in days if (not lo or d >= lo) and (not hi or d <= hi)]
            first = nm.first_complete_day(self.daily)
            self.days = [d for d in days if d >= first]
            for d in days:
                if d < first:
                    self.skipped.setdefault("all", []).append(d)
        gen = {"static": self.cells_static, "ionq_like": self.cells_ionq_like, "ibm": self.cells_ibm}[a.source]
        cells = list(gen())
        todo = []
        for meta, circuit, seed, drift, draw_seed, shots, day in cells:
            probe = {**meta, "circuit": circuit, "seed": seed, "shots": shots, "drift": drift}
            if not all(row_key({**probe, "arm": k}) in self.done for k in range(len(ARMS))):
                todo.append((meta, circuit, seed, drift, draw_seed, shots, day))
        total = len(todo)
        print(f"#start source={a.source} cells_total={len(cells)} cells_todo={total} out={self.out}", flush=True)
        for meta, circuit, seed, drift, draw_seed, shots, day in todo:
            n = CIRCUITS[circuit]().num_qubits
            try:
                model = self.model_for(a.source, drift, day, n)
            except nm.SkipDay as e:
                self.skipped.setdefault(circuit, []).append(f"{day}: {e}")
                self.n_cells += 1
                continue
            self.run_cell(meta, circuit, seed, model, drift, draw_seed, shots)
            self.progress(total)
        self.fh.close()
        if a.source == "ibm":
            sk = ROOT / "data" / "ibm" / f"skipped_{a.laptop}.json"
            sk.parent.mkdir(parents=True, exist_ok=True)
            old = json.loads(sk.read_text()) if sk.exists() else {}
            for k, v in self.skipped.items():
                old[k] = sorted(set(old.get(k, [])) | set(v))
            sk.write_text(json.dumps(old, indent=1))
            ch = ROOT / "data" / "calib" / "chains.json"
            ch.parent.mkdir(parents=True, exist_ok=True)
            oldc = json.loads(ch.read_text()) if ch.exists() else {}
            oldc[str(a.chain_rank)] = {**oldc.get(str(a.chain_rank), {}), **{str(k): v for k, v in self.chains.items()}}
            ch.write_text(json.dumps(oldc, indent=1))
        el = time.time() - self.t0
        print(f"#done rows={self.n_rows} cells={self.n_cells} elapsed_s={el:.0f} "
              f"s_per_cell={el / max(self.n_cells, 1):.2f} skipped={sum(len(v) for v in self.skipped.values())}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["static", "ionq_like", "ibm"], required=True)
    ap.add_argument("--circuits", default="ghz4", help="comma list of ghz4,qft3,grover3,ghz8,qaoa6")
    ap.add_argument("--seeds", default="0", help="one seed index, a-b (inclusive), or a,b,c")
    ap.add_argument("--shots", default=str(SHOTS_PER_PULL), help="shot budget per pull; comma list for the ablation")
    ap.add_argument("--days", default="", help="ibm: YYYY-MM-DD:YYYY-MM-DD subset")
    ap.add_argument("--f", type=float, default=0.0, help="ibm: coherent fraction of the cz error")
    ap.add_argument("--chain-rank", default="0", help="ibm: 0 (best chain) or median")
    ap.add_argument("--forward", action="store_true", help="also fill fidelity_fwd (needs automitigate/forward.py)")
    ap.add_argument("--p", default="0", help="static: comma list of extra per-cz Pauli probabilities")
    ap.add_argument("--theta", default="0", help="static: comma list of cz over-rotations (rad)")
    ap.add_argument("--r", default="0", help="static: comma list of extra readout flip probabilities")
    ap.add_argument("--schedule", default="stable,slow,jump", help="ionq_like: comma list of stable,slow,jump")
    ap.add_argument("--steps", type=int, default=300, help="ionq_like: steps per schedule")
    ap.add_argument("--laptop", default="ian", choices=["ian", "thomas"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    a.circuits = [c for c in a.circuits.split(",") if c]
    for c in a.circuits:
        if c not in CIRCUITS:
            ap.error(f"unknown circuit {c}")
    a.seeds = parse_seeds(a.seeds)
    a.shots = [int(x) for x in a.shots.split(",")]
    a.p, a.theta, a.r = parse_floats(a.p), parse_floats(a.theta), parse_floats(a.r)
    a.schedule = a.schedule.split(",")
    a.chain_rank = "median" if a.chain_rank == "median" else int(a.chain_rank)
    Sweep(a).run()


if __name__ == "__main__":
    main()
