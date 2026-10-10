"""Pick the two drift settings A and B for the IonQ-like schedules from the calibration grid.

  python scripts/pick_ab.py [--grid data/calib/grid.jsonl] [--out data/calib/ab.json]

A = the lowest-noise grid cell whose best arm (seed-mean score, summed over circuits)
has ZNE off. B = the cell whose best arm differs from A's with the largest margin
(score of its own best arm minus the score of A's best arm in that cell).
"""
import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from automitigate.arms import ARMS  # noqa: E402


def load(grid):
    rows = [json.loads(l) for l in open(grid) if l.strip()]
    rows = [r for r in rows if r["source"] == "aer_static"]
    cells = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        d = r["drift"]
        cells[(d["p"], d["theta"], d["r"])][(r["circuit"], r["arm"])].append(r["score"])
    return cells


def summarise(cells):
    out = {}
    for key, per in cells.items():
        circuits = sorted({c for c, _ in per})
        mean = {arm: sum(sum(per[(c, arm)]) / max(len(per[(c, arm)]), 1) for c in circuits) / len(circuits)
                for arm in range(len(ARMS))}
        best = max(mean, key=mean.get)
        per_circuit = {c: max(range(len(ARMS)), key=lambda a: sum(per[(c, a)]) / max(len(per[(c, a)]), 1))
                       for c in circuits}
        out[key] = {"mean": mean, "best": best, "per_circuit": per_circuit, "n": len(per[(circuits[0], 0)])}
    return out


def pick(summary):
    noise = lambda k: (k[0] + k[1] / 3 + k[2], k)  # p, theta/3, r on a comparable scale
    candidates = sorted(summary, key=noise)
    A = next((k for k in candidates if ARMS[summary[k]["best"]]["zne"] == 0), candidates[0])
    bestA = summary[A]["best"]
    B, margin = None, -1.0
    for k in candidates:
        s = summary[k]
        if s["best"] == bestA:
            continue
        m = s["mean"][s["best"]] - s["mean"][bestA]
        if m > margin:
            B, margin = k, m
    if B is None:  # no cell flips the best arm: take the noisiest cell and say so
        B, margin = candidates[-1], 0.0
    return A, B, margin


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", default=str(ROOT / "data" / "calib" / "grid.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "data" / "calib" / "ab.json"))
    a = ap.parse_args()
    summary = summarise(load(a.grid))
    if not summary:
        sys.exit("empty grid")
    A, B, margin = pick(summary)
    res = {
        "A": dict(zip(("p", "theta", "r"), A)), "B": dict(zip(("p", "theta", "r"), B)),
        "best_arm_A": summary[A]["best"], "best_arm_B": summary[B]["best"], "margin": margin,
        "per_circuit_A": summary[A]["per_circuit"], "per_circuit_B": summary[B]["per_circuit"],
        "seeds_per_cell": summary[A]["n"], "flips": margin > 0,
        "table": [{"p": k[0], "theta": k[1], "r": k[2], "best": s["best"],
                   "score_best": round(s["mean"][s["best"]], 4), "score_arm0": round(s["mean"][0], 4),
                   "score_arm7": round(s["mean"][7], 4)} for k, s in sorted(summary.items())],
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(f"A={res['A']} best arm {res['best_arm_A']}; B={res['B']} best arm {res['best_arm_B']}; "
          f"margin {margin:.4f}; flips={res['flips']}")


if __name__ == "__main__":
    main()
