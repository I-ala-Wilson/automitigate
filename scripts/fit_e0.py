"""Fit the IonQ-like constants from the single-circuit E0 runs.

  python scripts/fit_e0.py   # reads data/e0_runs.jsonl, writes data/e0.json

Model per run: P(target) = base + (1 - base) * S * (1-p1)^n1q * (1-p2)^n2q with S the readout
survival from runs 1 and 2 (r0, r1), base = 2^-n. p1 from run 7 (1q chain), p2 from runs 5 and 6
(2q chains, 1q dressing removed). Fold survives the compiler when run 4 scores clearly below run 3.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "e0_runs.jsonl"
OUT = ROOT / "data" / "e0.json"


def fit_ladder(rows, e0, p1_default=0.0005):
    """E0 v3 (qollab/e0_ladder.py): readout from the 0000 / 1111 runs, p2 from the decay between the
    12-CX and 36-CX ladders (X gates charged at p1_default). Readout survival of a target string
    is the product of the per-bit survivals, so it cancels in the slope between the two ladders
    only approximately; it is corrected per target explicitly."""
    import math
    r0 = 1 - rows["ro0000"]["p_target"] ** 0.25
    r1 = 1 - rows["ro1111"]["p_target"] ** 0.25
    base = 1 / 16

    def survival(target):
        return math.prod((1 - r1) if b == "1" else (1 - r0) for b in target)

    def decay(row):
        y = (row["p_target"] - base) / (1 - base) / survival(row["target"])
        return math.log(max(y, 1e-6))

    a, b = rows["ladder_d12"], rows["ladder_d36"]
    if a["p_target"] >= 0.999 and b["p_target"] >= 0.999:
        print("both ladders returned 1.0: still cancelled or an ideal backend; e0.json unchanged")
        return 2
    slope = (decay(b) - decay(a)) / (b["n2q"] - a["n2q"])
    slope -= (b["n1q"] - a["n1q"]) / (b["n2q"] - a["n2q"]) * math.log(1 - p1_default)
    p2 = 1 - math.exp(slope)
    e0.update({"version": 4, "method": "ladder", "r0_fit": round(max(r0, 0.0), 5), "r1_fit": round(max(r1, 0.0), 5),
               "p1q_fit": p1_default, "p1q_note": "not fitted (single-qubit chains are merged by the compiler); default",
               "p2q_fit": round(max(p2, 0.0), 6),
               "ladder": {k: {"p_target": rows[k]["p_target"], "n2q": rows[k]["n2q"], "n1q": rows[k]["n1q"], "target": rows[k]["target"]}
                          for k in ("ladder_d12", "ladder_d36")},
               "backend": rows["ladder_d36"].get("backend"), "noise_model": rows["ladder_d36"].get("noise_model"),
               "job_ids": {k: r.get("job_id") for k, r in rows.items()}, "ok": True})
    e0.pop("errors", None)
    OUT.write_text(json.dumps(e0, indent=1))
    print(f"ladder fit: p2q_fit={e0['p2q_fit']} r0={e0['r0_fit']} r1={e0['r1_fit']} (p1 default {p1_default}); "
          f"ladders P = {a['p_target']} @ {a['n2q']} CX, {b['p_target']} @ {b['n2q']} CX")
    return 0


def main():
    rows = {}
    for line in RUNS.read_text().splitlines():
        line = line.strip()
        if line.startswith("{"):
            r = json.loads(line)
            rows[r["label"]] = r
    e0 = json.loads(OUT.read_text()) if OUT.exists() else {}
    e0 = {k: v for k, v in e0.items() if k not in ("errors", "ok")}
    e0["version"] = 3
    e0["runs"] = sorted(rows)
    if {"ro0000", "ro1111", "ladder_d12", "ladder_d36"} <= set(rows):
        return fit_ladder(rows, e0)
    need = {"ro00", "ro11", "chain2q_d10", "chain2q_d20", "chain1q_d20"}
    missing = need - set(rows)
    if missing:
        print(f"missing runs: {sorted(missing)}; e0.json left without fits")
        e0["errors"] = {"missing_runs": sorted(missing)}
        e0["ok"] = False
        OUT.write_text(json.dumps(e0, indent=1))
        return 1
    if all(r["p_target"] >= 0.999 for r in rows.values()):
        print("every run scored P(target) = 1.0, including the depth-20 chains: these runs came from an ideal "
              "simulator, not the Aria-1 noise model. Select the IonQ Aria-1 noise-model simulator in Select QPU "
              "and run again. e0.json left unchanged.")
        return 2
    p00, p11 = rows["ro00"]["p_target"], rows["ro11"]["p_target"]
    r0 = 1 - math.sqrt(max(p00, 1e-9))
    r1 = 1 - math.sqrt(max(p11, 1e-9))
    s2 = (1 - r0) ** 2  # readout survival of a 2-qubit all-zero target
    s1 = 1 - r0

    def decay(row, base, s):
        y = (row["p_target"] - base) / (1 - base) / s
        return math.log(max(y, 1e-6))

    c1 = rows["chain1q_d20"]
    p1 = 1 - math.exp(decay(c1, 0.5, s1) / c1["n1q"])
    a, b = rows["chain2q_d10"], rows["chain2q_d20"]
    # slope between the two 2q chains removes any constant offset; subtract the 1q dressing
    slope = (decay(b, 0.25, s2) - decay(a, 0.25, s2)) / (b["n2q"] - a["n2q"])
    slope -= (b["n1q"] - a["n1q"]) / (b["n2q"] - a["n2q"]) * math.log(1 - p1)
    p2 = 1 - math.exp(slope)
    e0.update({"r0_fit": round(r0, 5), "r1_fit": round(r1, 5), "p1q_fit": round(max(p1, 0.0), 6),
               "p2q_fit": round(max(p2, 0.0), 6), "readout_p00_prep00": p00, "readout_p11_prep11": p11,
               "depth_curve": [{"depth": d, "n2q_submitted": rows[k]["n2q"], "p_target": rows[k]["p_target"]}
                               for d, k in ((10, "chain2q_d10"), (20, "chain2q_d20"))]})
    if "twin_ghz4" in rows and "fold3_ghz4" in rows:
        tw, fd = rows["twin_ghz4"]["p_target"], rows["fold3_ghz4"]["p_target"]
        se = math.sqrt(max(tw * (1 - tw), 1e-4) / rows["twin_ghz4"]["shots"])
        e0.update({"twin_p_target": tw, "fold_p_target": fd, "fold_survives_compiler": fd < tw - 3 * se})
    e0["job_ids"] = {k: r.get("job_id") for k, r in rows.items()}
    e0["ok"] = True
    OUT.write_text(json.dumps(e0, indent=1))
    print(f"p1q_fit={e0['p1q_fit']} p2q_fit={e0['p2q_fit']} r0={e0['r0_fit']} r1={e0['r1_fit']} "
          f"fold_survives={e0.get('fold_survives_compiler')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
