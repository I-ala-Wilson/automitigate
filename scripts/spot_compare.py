"""Compare Thomas's single-circuit Qollab runs with the local IonQ-like model on the same cells.

  python scripts/spot_compare.py   # data/ionq/spot_runs.jsonl -> data/ionq/spot_check.json

For each run: rebuild the identical circuit (qollab/spot_check_single.cell_circuit), simulate it
on ionq_static(p1, p2, r) with the constants in data/e0.json (20000 shots), and report the
absolute difference in P(target). The mean over cells is the number quoted in the README.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "qollab"))

from automitigate import noise_model as nm  # noqa: E402
from spot_check_single import CELLS, cell_circuit  # noqa: E402

RUNS = ROOT / "data" / "ionq" / "spot_runs.jsonl"
OUT = ROOT / "data" / "ionq" / "spot_check.json"


def main():
    if not RUNS.exists():
        sys.exit(f"{RUNS} missing")
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip().startswith("{")]
    const = nm.ionq_constants()
    model = nm.ionq_static(const["p1"], const["p2"], const["r"])
    out = []
    for r in rows:
        circuit, setting, seed = CELLS[r["run"] - 1]
        qc, target, drift, _ = cell_circuit(circuit, setting, seed)
        model_r = nm.ionq_static(const["p1"], const["p2"], const["r"] + drift["r"]) if drift["r"] else model
        counts = nm.run([qc], model_r, 20000, nm.seed_for("spot", r["run"]))[0]
        local = counts.get(target, 0) / 20000
        out.append({**{k: r[k] for k in ("run", "circuit", "setting", "seed", "arm", "target", "score", "job_id", "n2q")},
                    "local_score": round(local, 4), "abs_diff": round(abs(local - r["score"]), 4)})
    res = {"constants": const, "n": len(out), "mean_abs_diff": sum(o["abs_diff"] for o in out) / max(len(out), 1),
           "max_abs_diff": max((o["abs_diff"] for o in out), default=None), "rows": out}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(f"spot check: {res['n']} cells, mean |P_qollab - P_local| = {res['mean_abs_diff']:.4f} (max {res['max_abs_diff']})")


if __name__ == "__main__":
    main()
