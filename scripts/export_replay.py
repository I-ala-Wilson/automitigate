"""Export compact replay tables for the demo (main.py) from the full reward tables.

  python scripts/export_replay.py   # -> data/replay/*.json (+ summary.json)

Each file: {"source", "circuit", "schedule", "snapshots": [...], "seeds": [...],
            "samples": [T][8][S] mirror scores (null where missing), "means": [T][8]}
The demo reads these by literal path, so every file name is fixed here and in main.py.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from analysis import cube, ibm_primary, load_json, load_rows  # noqa: E402
from automitigate.arms import ARMS  # noqa: E402

OUT = ROOT / "data" / "replay"
CIRCUITS = ["ghz4", "qft3", "grover3", "ghz8", "qaoa6"]
SCHEDULES = ["stable", "slow", "jump"]


def dump(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, separators=(",", ":")))


def pack(arr, snapshots, seeds, **meta):
    samples = np.round(arr, 4)
    means = np.round(np.nanmean(arr, axis=2), 4)
    return {**meta, "arms": [{"zne": a["zne"], "twirl": a["twirl"], "rem": a["rem"]} for a in ARMS],
            "snapshots": list(snapshots), "seeds": [int(s) for s in seeds],
            "samples": [[[None if np.isnan(x) else float(x) for x in row] for row in day] for day in samples],
            "means": [[None if np.isnan(x) else float(x) for x in row] for row in means]}


def main():
    df = load_rows()
    written = []
    d = ibm_primary(df)
    if not d.empty:
        for c in CIRCUITS:
            if (d.circuit == c).any():
                arr, days, seeds = cube(d, c)
                dump(f"ibm_{c}.json", pack(arr, days, seeds, source="ibm", circuit=c, schedule=None))
                written.append(f"ibm_{c}.json")
    like = df[df.source == "aer_ionq_like"] if not df.empty else df
    if not like.empty:
        for c in CIRCUITS:
            for sch in SCHEDULES:
                dc = like[(like.circuit == c) & (like.schedule == sch)]
                if dc.empty:
                    continue
                steps = sorted(dc.step.unique())
                seeds = sorted(dc.seed.unique())
                arr = np.full((len(steps), len(ARMS), len(seeds)), np.nan)
                si, ti = {s: i for i, s in enumerate(seeds)}, {t: i for i, t in enumerate(steps)}
                for t, a, s, sc in zip(dc.step, dc.arm, dc.seed, dc.score):
                    arr[ti[t], a, si[s]] = sc
                dump(f"ionq_{c}_{sch}.json", pack(arr, [int(t) for t in steps], seeds, source="ionq_like", circuit=c, schedule=sch))
                written.append(f"ionq_{c}_{sch}.json")
    head = load_json("headline") or {}
    learners = load_json("learners") or {}
    summary = {c: {"drift_value_pct": h["drift_value_pct"], "n_significant": h["n_significant"], "raw_flips": h["raw_flips"],
                   "static_arm": h["static_arm"], "n_days": h["n_days"], "n_seeds": h["n_seeds"],
                   "significant_switches": h["significant_switches"],
                   "learners": {n: {"regret": L["regret_mean"], "ci": [L["ci_lo"], L["ci_hi"]]}
                                for n, L in learners.get(c, {}).get("learners", {}).items()},
                   "hp": learners.get(c, {}).get("hp")}
               for c, h in head.items()}
    dump("summary.json", summary)
    written.append("summary.json")
    sizes = {w: round((OUT / w).stat().st_size / 1e6, 2) for w in written}
    big = [w for w, s in sizes.items() if s > 1.9]
    print(f"export_replay: {len(written)} files, MB each: {sizes}{' OVER 2 MB: ' + str(big) if big else ''}")


if __name__ == "__main__":
    main()
