"""Analysis of the reward tables. Reads every data/**/*.jsonl(.gz), writes data/analysis/*.json,
figures/*.png and docs/results.md.

  python scripts/analysis.py headline | learners | best-arm | proxy | drivers | sensitivity |
                             pareto | figures [--quick] | results-md | all [--final]

Definitions are the pre-registered ones in docs/analysis_plan.md. Every subcommand prints a
one-paragraph summary and tolerates missing inputs (prints what is missing and returns).
"""
import argparse
import glob
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from automitigate.arms import ARMS  # noqa: E402
from automitigate.learners import (LEARNERS, DynamicOracle, FixedArm, StaticOracle, run_episode)  # noqa: E402
from automitigate.score import zne_extrapolate  # noqa: E402

OUT = ROOT / "data" / "analysis"
FIG = ROOT / "figures"
K = len(ARMS)
ARM_LABEL = ["".join(("Z" if a["zne"] else "-", "T" if a["twirl"] else "-", "R" if a["rem"] else "-")) for a in ARMS]
GAMMAS = [0.8, 0.9, 0.95, 0.99]
WINDOWS = [10, 20, 40]
REPLAYS = 200
N_QUBITS = {"ghz4": 4, "qft3": 3, "grover3": 3, "ghz8": 8, "qaoa6": 6}


# ---------------------------------------------------------------- data

def load_rows(pattern="data/**/*.jsonl*"):
    rows = []
    for path in sorted(glob.glob(str(ROOT / pattern), recursive=True)):
        if "/analysis/" in path or not (path.endswith(".jsonl") or path.endswith(".jsonl.gz")):
            continue
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                d = r.get("drift") or {}
                aux = r.get("aux") or {}
                rows.append({
                    "source": r["source"], "snapshot": r.get("snapshot"), "schedule": r.get("schedule"),
                    "step": r.get("step", 0), "circuit": r["circuit"], "arm": int(r["arm"]), "seed": int(r["seed"]),
                    "f": float(r.get("f", 0.0)), "chain_rank": str(r.get("chain_rank", 0)), "shots": int(r.get("shots", 1200)),
                    "score": float(r["score"]), "fidelity_fwd": r.get("fidelity_fwd"),
                    "p": float(d.get("p", 0.0)), "theta": float(d.get("theta", 0.0)), "r": float(d.get("r", 0.0)),
                    "by_scale": aux.get("by_scale"), "clipped": bool(aux.get("clipped", False)),
                    "laptop": r.get("laptop"), "file": Path(path).name,
                })
    df = pd.DataFrame(rows)
    return df


def ibm_primary(df):
    """Primary IBM rows: f = 0, best chain, 1200 shots, no forward column, one row per cell/arm/seed."""
    if df.empty or "source" not in df:
        return df
    d = df[(df.source == "aer_ibm_fez") & (df.f == 0.0) & (df.chain_rank == "0") & (df.shots == 1200)
           & df.fidelity_fwd.isna()]
    return d.drop_duplicates(["circuit", "snapshot", "arm", "seed"], keep="last")


def cube(d, circuit):
    """samples[T, K, S], days list, seeds list for one circuit."""
    dc = d[d.circuit == circuit]
    days = sorted(dc.snapshot.unique())
    seeds = sorted(dc.seed.unique())
    arr = np.full((len(days), K, len(seeds)), np.nan)
    di = {x: i for i, x in enumerate(days)}
    si = {x: i for i, x in enumerate(seeds)}
    for sn, a, s, sc in zip(dc.snapshot, dc.arm, dc.seed, dc.score):
        arr[di[sn], a, si[s]] = sc
    return arr, days, seeds


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, default=float))


def load_json(name):
    p = OUT / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


# ---------------------------------------------------------------- headline

def headline_for(arr, days):
    T, _, S = arr.shape
    mean = np.nanmean(arr, axis=2)
    n = np.sum(~np.isnan(arr), axis=2)
    se = np.nanstd(arr, axis=2, ddof=1) / np.sqrt(np.maximum(n, 1)) if S > 1 else np.full(mean.shape, np.nan)
    static_arm = int(np.argmax(np.nansum(mean, axis=0)))
    best = np.argmax(mean, axis=1)
    dyn = mean[np.arange(T), best]
    static = mean[:, static_arm]
    drift_value = float(100.0 * np.nansum(dyn - static) / max(np.nansum(static), 1e-9))
    raw_flips, sig, ambiguous = 0, [], 0
    for t in range(T):
        order = np.argsort(mean[t])[::-1]
        top, second = order[0], order[1]
        diff = arr[t, top, :] - arr[t, second, :]
        diff = diff[~np.isnan(diff)]
        se_d = float(np.std(diff, ddof=1) / math.sqrt(len(diff))) if len(diff) > 1 else float("inf")
        if mean[t, top] - mean[t, second] <= 2 * se_d:
            ambiguous += 1
        if t > 0 and best[t] != best[t - 1]:
            raw_flips += 1
            old = best[t - 1]
            d2 = arr[t, best[t], :] - arr[t, old, :]
            d2 = d2[~np.isnan(d2)]
            se2 = float(np.std(d2, ddof=1) / math.sqrt(len(d2))) if len(d2) > 1 else float("inf")
            if mean[t, best[t]] - mean[t, old] > 2 * se2:
                sig.append(t)
    bounds = [0] + sig + [T]
    epochs = [b - a for a, b in zip(bounds, bounds[1:])]
    return {
        "days": days, "n_days": T, "n_seeds": int(S), "static_arm": static_arm, "static_label": ARM_LABEL[static_arm],
        "best_per_day": best.tolist(), "mean": mean.tolist(), "se": se.tolist(),
        "drift_value_pct": drift_value, "raw_flips": raw_flips, "significant_switches": sig,
        "n_significant": len(sig), "epochs": epochs, "median_epoch_days": float(np.median(epochs)) if epochs else float(T),
        "ambiguous_fraction": ambiguous / max(T, 1),
        "static_cum": float(np.nansum(static)), "dynamic_cum": float(np.nansum(dyn)),
        "arm0_cum": float(np.nansum(mean[:, 0])), "arm7_cum": float(np.nansum(mean[:, 7])),
    }


def cmd_headline(df):
    d = ibm_primary(df)
    if d.empty:
        print("headline: no primary IBM rows yet")
        return None
    res = {}
    for c in sorted(d.circuit.unique()):
        arr, days, seeds = cube(d, c)
        res[c] = headline_for(arr, days)
    save("headline", res)
    for c, h in res.items():
        print(f"headline {c}: {h['n_days']} days x {h['n_seeds']} seeds; static oracle = arm {h['static_arm']} "
              f"({h['static_label']}); drift value {h['drift_value_pct']:.2f} % of the static oracle; "
              f"{h['n_significant']} significant switches ({h['raw_flips']} raw argmax flips), median epoch "
              f"{h['median_epoch_days']:.0f} days, ambiguous-day fraction {h['ambiguous_fraction']:.2f}.")
    return res


# ---------------------------------------------------------------- learners

def learner_set(hp_sel):
    out = {"eps-greedy": {}, "UCB1": {}, "Thompson": {},
           "Discounted TS": {"gamma": hp_sel.get("gamma", 0.9)},
           "Sliding-Window TS": {"window": hp_sel.get("window", 20)},
           "Change-Detection TS": {"window": hp_sel.get("window", 20), "threshold": 3.0}}
    return out


def replay(learner_factory, arr, cols, pulls, switches, n=REPLAYS):
    finals, curves, lags = [], [], []
    for i in range(n):
        rng = np.random.default_rng(1000 + i)
        out = run_episode(learner_factory(i), arr, rng, pulls_per_snapshot=pulls, switches=switches, seed_cols=cols)
        finals.append(out["pseudo_regret"][-1])
        curves.append(out["pseudo_regret"])
        lags.append(out["switch_lag"])
    finals = np.array(finals)
    curve = np.mean(np.array(curves), axis=0)
    lag_mean = {}
    for s in switches or []:
        vals = [l[s] for l in lags if l.get(s) is not None]
        lag_mean[str(s)] = {"mean": float(np.mean(vals)) if vals else None, "found": len(vals) / n}
    return {"regret_mean": float(finals.mean()), "ci_lo": float(np.percentile(finals, 2.5)),
            "ci_hi": float(np.percentile(finals, 97.5)), "curve": curve.tolist(), "switch_lag": lag_mean}


def cmd_learners(df, pulls=1):
    d = ibm_primary(df)
    if d.empty:
        print("learners: no primary IBM rows yet")
        return None
    head = load_json("headline") or {}
    res = {}
    for c in sorted(d.circuit.unique()):
        arr, days, seeds = cube(d, c)
        S = len(seeds)
        tune = [i for i, s in enumerate(seeds) if s <= 9]
        report = [i for i, s in enumerate(seeds) if s >= 10]
        same = len(report) == 0
        if same:
            report = list(range(S))
            tune = list(range(S))
        if pulls > 1:
            report = report[:max(1, len(report) // pulls) * 1]
        h = head.get(c) or headline_for(arr, days)
        switches = h["significant_switches"]
        # hyperparameter selection on the tuning seeds (fewer replays)
        sel = {}
        best_g, best_v = None, None
        for g in GAMMAS:
            v = replay(lambda i, g=g: LEARNERS["Discounted TS"](K, seed=i, gamma=g), arr, tune, pulls, [], n=40)["regret_mean"]
            if best_v is None or v < best_v:
                best_g, best_v = g, v
        best_w, best_v = None, None
        for w in WINDOWS:
            v = replay(lambda i, w=w: LEARNERS["Sliding-Window TS"](K, seed=i, window=w), arr, tune, pulls, [], n=40)["regret_mean"]
            if best_v is None or v < best_v:
                best_w, best_v = w, v
        sel = {"gamma": best_g, "window": best_w}
        entry = {"n_days": len(days), "n_seeds": S, "tuned_on": [int(seeds[i]) for i in tune],
                 "reported_on": [int(seeds[i]) for i in report], "same_seeds_flag": same, "hp": sel,
                 "pulls_per_snapshot": pulls, "learners": {}}
        for name, hp in learner_set(sel).items():
            entry["learners"][name] = replay(lambda i, name=name, hp=hp: LEARNERS[name](K, seed=i, **hp), arr, report, pulls, switches)
        entry["learners"]["arm 0"] = replay(lambda i: FixedArm(K, seed=i, arm=0), arr, report, pulls, switches, n=20)
        entry["learners"]["arm 7"] = replay(lambda i: FixedArm(K, seed=i, arm=7), arr, report, pulls, switches, n=20)
        entry["learners"]["static oracle"] = replay(lambda i: StaticOracle(K, seed=i, arm=h["static_arm"]), arr, report, pulls, switches, n=20)
        entry["learners"]["dynamic oracle"] = replay(lambda i: DynamicOracle(K, seed=i, best_per_step=h["best_per_day"]), arr, report, pulls, switches, n=20)
        for name, e in entry["learners"].items():
            e["captured_pct"] = (100.0 * (entry["learners"]["arm 7"]["regret_mean"] - e["regret_mean"])
                                 / max(entry["learners"]["arm 7"]["regret_mean"], 1e-9))
        res[c] = entry
    save("learners" if pulls == 1 else f"learners_pulls{pulls}", res)
    for c, e in res.items():
        best = min((n for n in e["learners"] if n in LEARNERS), key=lambda n: e["learners"][n]["regret_mean"])
        L = e["learners"]
        print(f"learners {c} (reported on seeds {e['reported_on']}{', same as tuning' if e['same_seeds_flag'] else ''}, "
              f"gamma={e['hp']['gamma']}, window={e['hp']['window']}): best learner {best} regret "
              f"{L[best]['regret_mean']:.2f} [{L[best]['ci_lo']:.2f}, {L[best]['ci_hi']:.2f}] vs arm 7 "
              f"{L['arm 7']['regret_mean']:.2f}, static oracle {L['static oracle']['regret_mean']:.2f}.")
    return res


# ---------------------------------------------------------------- best-arm, proxy, drivers

def cmd_best_arm(df):
    out = {}
    d = ibm_primary(df)
    if not d.empty:
        tab = d.groupby(["circuit", "snapshot", "arm"]).score.mean().unstack("arm")
        out["ibm"] = {f"{c}|{s}": int(row.idxmax()) for (c, s), row in tab.iterrows()}
    st = df[df.source == "aer_static"] if not df.empty else df
    if not st.empty:
        tab = st.groupby(["circuit", "p", "theta", "r", "arm"]).score.mean().unstack("arm")
        out["static"] = {f"{c}|p={p}|theta={t}|r={r}": int(row.idxmax()) for (c, p, t, r), row in tab.iterrows()}
    save("best_arm", out)
    print(f"best-arm: {len(out.get('ibm', {}))} ibm cells, {len(out.get('static', {}))} static cells")
    return out


def cmd_proxy(df):
    d = df[(df.source == "aer_ibm_fez") & df.fidelity_fwd.notna()] if not df.empty else df
    if d.empty:
        print("proxy: no forward rows yet (Q2b)")
        return None
    from scipy.stats import spearmanr
    res = {}
    for c in sorted(d.circuit.unique()):
        dc = d[d.circuit == c]
        per_day = []
        for sn, g in dc.groupby("snapshot"):
            m = g.groupby("arm").agg(score=("score", "mean"), fwd=("fidelity_fwd", "mean"))
            if len(m) < K:
                continue
            rho = spearmanr(m.score, m.fwd).correlation
            mirror_pick = int(m.score.idxmax())
            fwd_best, fwd_worst = float(m.fwd.max()), float(m.fwd.min())
            regret = 0.0 if fwd_best == fwd_worst else float((fwd_best - m.fwd[mirror_pick]) / (fwd_best - fwd_worst))
            per_day.append({"day": sn, "spearman": None if np.isnan(rho) else float(rho),
                            "top1": bool(mirror_pick == int(m.fwd.idxmax())), "fwd_regret": regret})
        if per_day:
            res[c] = {"n_days": len(per_day), "per_day": per_day,
                      "top1_rate": float(np.mean([p["top1"] for p in per_day])),
                      "spearman_median": float(np.nanmedian([p["spearman"] for p in per_day if p["spearman"] is not None] or [np.nan])),
                      "fwd_regret_median_pct": float(100 * np.median([p["fwd_regret"] for p in per_day]))}
    save("proxy", res)
    for c, r in res.items():
        print(f"proxy {c}: top-1 agreement {100 * r['top1_rate']:.0f} % of {r['n_days']} days, median Spearman "
              f"{r['spearman_median']:.2f}, median forward regret of the mirror pick {r['fwd_regret_median_pct']:.0f} % of the worst arm's.")
    return res


def chain_features(days, chain):
    from automitigate.noise_model import daily_state, load_daily
    daily = load_daily()
    recal = set(daily.attrs.get("recal_days", []))
    feats = []
    for day in days:
        st = daily_state(daily, day)
        cz = [v for (p, a, b), (v, c) in st.items() if p == "cz_error" and b >= 0 and {a, b} <= set(chain)
              and set((a, b)) in [set(e) for e in zip(chain, chain[1:])] and not c and np.isfinite(v)]
        ro = [v for (p, a, b), (v, c) in st.items() if p == "readout_error" and a in chain and b < 0 and np.isfinite(v)]
        t1 = [v for (p, a, b), (v, c) in st.items() if p == "T1" and a in chain and b < 0 and np.isfinite(v)]
        t2 = [v for (p, a, b), (v, c) in st.items() if p == "T2" and a in chain and b < 0 and np.isfinite(v)]
        feats.append([np.mean(cz) if cz else np.nan, np.mean(ro) if ro else np.nan,
                      np.mean(t1) if t1 else np.nan, np.mean(t2) if t2 else np.nan, day in recal])
    return np.array(feats, dtype=float), recal


def cmd_drivers(df):
    head = load_json("headline")
    chains = json.loads((ROOT / "data" / "calib" / "chains.json").read_text()) if (ROOT / "data" / "calib" / "chains.json").exists() else {}
    if not head or not chains:
        print("drivers: needs headline.json and data/calib/chains.json")
        return None
    res = {}
    for c, h in head.items():
        chain = chains.get("0", {}).get(str(N_QUBITS[c]))
        if not chain:
            continue
        X, recal = chain_features(h["days"], chain)
        y = np.array(h["best_per_day"])
        ok = ~np.isnan(X[:, :4]).any(axis=1)
        entry = {"n": int(ok.sum()), "features": ["cz_error", "readout_error", "T1", "T2"]}
        if ok.sum() >= 20 and len(set(y[ok])) > 1:
            try:
                from sklearn.linear_model import LogisticRegression
                from sklearn.model_selection import cross_val_score
                from sklearn.pipeline import make_pipeline
                from sklearn.preprocessing import StandardScaler
                clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
                acc = cross_val_score(clf, X[ok, :4], y[ok], cv=5).mean()
                clf.fit(X[ok, :4], y[ok])
                entry.update({"cv_accuracy": float(acc), "majority_rate": float(np.bincount(y[ok]).max() / ok.sum()),
                              "coef": clf[-1].coef_.tolist(), "classes": clf[-1].classes_.tolist()})
            except Exception as e:
                entry["error"] = str(e)[:200]
        sig = h["significant_switches"]
        near = sum(1 for t in sig if any(h["days"][u] in recal for u in range(max(0, t - 1), min(len(h["days"]), t + 2))))
        base = np.mean([any(h["days"][u] in recal for u in range(max(0, t - 1), min(len(h["days"]), t + 2))) for t in range(len(h["days"]))]) if h["days"] else 0
        entry.update({"switches": len(sig), "switches_within_1_day_of_recal": near, "base_rate_near_recal": float(base)})
        res[c] = entry
    save("drivers", res)
    for c, e in res.items():
        acc = f"cv accuracy {e['cv_accuracy']:.2f} vs majority {e['majority_rate']:.2f}" if "cv_accuracy" in e else "too few days or one class"
        print(f"drivers {c}: best arm vs (cz error, readout, T1, T2): {acc}; {e['switches_within_1_day_of_recal']}/{e['switches']} "
              f"significant switches within a day of a recalibration (base rate {e['base_rate_near_recal']:.2f}).")
    return res


# ---------------------------------------------------------------- sensitivity, pareto

def cmd_sensitivity(df):
    res = {}
    head = load_json("headline") or {}
    if df.empty:
        print("sensitivity: no rows")
        return None
    # exponential ZNE recomputed from stored per-scale scores
    d = ibm_primary(df).copy()
    if not d.empty:
        def exp_score(row):
            if row.by_scale and ARMS[row.arm]["zne"]:
                return zne_extrapolate({int(k): v for k, v in row.by_scale.items()}, "exp", N_QUBITS[row.circuit])
            return row.score
        d["score"] = d.apply(exp_score, axis=1)
        res["exp_zne"] = {}
        for c in sorted(d.circuit.unique()):
            arr, days, _ = cube(d, c)
            h = headline_for(arr, days)
            res["exp_zne"][c] = {"drift_value_pct": h["drift_value_pct"], "n_significant": h["n_significant"],
                                 "static_arm": h["static_arm"], "linear_drift_value_pct": head.get(c, {}).get("drift_value_pct")}
    # coherent fraction f = 0.3
    f3 = df[(df.source == "aer_ibm_fez") & (df.f == 0.3)]
    if not f3.empty:
        res["f03"] = {}
        for c in sorted(f3.circuit.unique()):
            arr, days, seeds = cube(f3, c)
            h = headline_for(arr, days)
            base = ibm_primary(df)
            base = base[(base.circuit == c) & base.seed.isin(seeds)]
            hb = headline_for(*cube(base, c)[:2]) if not base.empty else {}
            res["f03"][c] = {"drift_value_pct": h["drift_value_pct"], "n_significant": h["n_significant"], "static_arm": h["static_arm"],
                             "f0_same_seeds": {k: hb.get(k) for k in ("drift_value_pct", "n_significant", "static_arm")}}
    med = df[(df.source == "aer_ibm_fez") & (df.chain_rank == "median")]
    if not med.empty:
        res["median_chain"] = {}
        for c in sorted(med.circuit.unique()):
            arr, days, _ = cube(med, c)
            h = headline_for(arr, days)
            res["median_chain"][c] = {"drift_value_pct": h["drift_value_pct"], "n_significant": h["n_significant"], "static_arm": h["static_arm"]}
    spot = ROOT / "data" / "ionq" / "spot_check.json"
    like = df[df.source == "aer_ionq_like"]
    if spot.exists() and not like.empty:
        try:
            sp = json.loads(spot.read_text())
            diffs = []
            for r in sp.get("rows", []):
                m = like[(like.circuit == r["circuit"]) & (like.schedule == r.get("schedule")) & (like.step == r.get("step")) & (like.arm == r["arm"])]
                if not m.empty:
                    diffs.append(abs(m.score.mean() - r["score"]))
            res["spot_check"] = {"n": len(diffs), "mean_abs_diff": float(np.mean(diffs)) if diffs else None}
        except Exception as e:
            res["spot_check"] = {"error": str(e)[:200]}
    save("sensitivity", res)
    for k, v in res.items():
        print(f"sensitivity {k}: {json.dumps(v, default=float)[:300]}")
    return res


def cmd_pareto(df):
    st = df[(df.source == "aer_static") & df.file.str.startswith("shots")] if not df.empty else df
    if st.empty:
        print("pareto: no shot-ablation rows yet (Q4)")
        return None
    tab = st.groupby(["circuit", "shots", "arm"]).score.agg(["mean", "std", "count"]).reset_index()
    tab["circuits_per_pull"] = tab.arm.map(lambda a: (3 if ARMS[a]["zne"] else 1) * (8 if ARMS[a]["twirl"] else 1))
    res = tab.to_dict("records")
    save("pareto", res)
    print(f"pareto: {len(res)} (circuit, shots, arm) points")
    return res


# ---------------------------------------------------------------- figures, results-md

def _style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False})
    return plt


def cmd_figures(df, quick=False):
    plt = _style()
    FIG.mkdir(exist_ok=True)
    made = []
    head = load_json("headline") or {}
    learners = load_json("learners") or {}
    for c, e in learners.items():
        fig, ax = plt.subplots(figsize=(6, 3.4))
        styles = {"arm 0": ":", "arm 7": "--", "static oracle": "-.", "dynamic oracle": "-"}
        for name, L in e["learners"].items():
            ax.plot(L["curve"], label=name, linestyle=styles.get(name, "-"), linewidth=1.2 if name in styles else 1.6,
                    color="0.55" if name in styles else None)
        ax.set_xlabel("pull (one per daily snapshot)")
        ax.set_ylabel("cumulative pseudo-regret")
        ax.set_title(f"{c}: learners vs fixed policies (seeds {e['reported_on'][0]}–{e['reported_on'][-1]})")
        ax.legend(fontsize=7, ncol=2, frameon=False)
        fig.tight_layout()
        p = FIG / f"regret_{c}.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        made.append(p.name)
        if quick:
            break
    if not quick:
        for c, h in head.items():
            fig, ax = plt.subplots(figsize=(7, 2.2))
            ax.step(range(h["n_days"]), h["best_per_day"], where="mid", color="black", linewidth=1)
            for t in h["significant_switches"]:
                ax.axvline(t, color="0.6", linewidth=0.8)
            ax.set_yticks(range(K))
            ax.set_yticklabels(ARM_LABEL, fontsize=7)
            ax.set_xlabel("daily snapshot")
            ax.set_title(f"{c}: best arm per day (Z=ZNE, T=twirl, R=readout mitigation); grey = significant switch")
            fig.tight_layout()
            p = FIG / f"best_arm_{c}.png"
            fig.savefig(p, dpi=150)
            plt.close(fig)
            made.append(p.name)
        if head:
            fig, ax = plt.subplots(figsize=(4.5, 3))
            cs = list(head)
            ax.bar(cs, [head[c]["drift_value_pct"] for c in cs], color="0.5")
            ax.set_ylabel("drift value (% of static oracle)")
            ax.set_title("What a perfect tracker gains over the best fixed arm")
            fig.tight_layout()
            p = FIG / "drift_value.png"
            fig.savefig(p, dpi=150)
            plt.close(fig)
            made.append(p.name)
        proxy = load_json("proxy") or {}
        if proxy:
            fig, axes = plt.subplots(len(proxy), 1, figsize=(7, 1.6 * len(proxy)), squeeze=False)
            for ax, (c, r) in zip(axes[:, 0], proxy.items()):
                ax.plot([p["spearman"] if p["spearman"] is not None else np.nan for p in r["per_day"]], color="black", linewidth=0.8)
                ax.scatter(range(r["n_days"]), [1.05 if p["top1"] else np.nan for p in r["per_day"]], s=6, color="0.4")
                ax.set_ylim(-1.1, 1.15)
                ax.set_ylabel(f"{c}\nSpearman", fontsize=7)
            axes[-1, 0].set_xlabel("day (dots at the top = mirror and forward agree on the best arm)")
            fig.tight_layout()
            p = FIG / "proxy_per_day.png"
            fig.savefig(p, dpi=150)
            plt.close(fig)
            made.append(p.name)
        pareto = load_json("pareto") or []
        if pareto:
            fig, ax = plt.subplots(figsize=(5, 3.2))
            for shots in sorted({r["shots"] for r in pareto}):
                pts = [r for r in pareto if r["shots"] == shots]
                ax.scatter([r["circuits_per_pull"] for r in pts], [r["mean"] for r in pts], label=f"{shots} shots", s=14)
            ax.set_xscale("log")
            ax.set_xlabel("circuits per pull")
            ax.set_ylabel("mirror score")
            ax.legend(frameon=False, fontsize=7)
            fig.tight_layout()
            p = FIG / "pareto.png"
            fig.savefig(p, dpi=150)
            plt.close(fig)
            made.append(p.name)
    print(f"figures: {', '.join(made) if made else 'nothing to draw yet'}")
    return made


def headline_sentence(c, h, L):
    if h["n_significant"] > 0:
        s = (f"Over {h['n_days']} daily snapshots of real ibm_fez calibration data, a perfect tracker would have gained "
             f"{h['drift_value_pct']:.1f} % over the best fixed setting for {c} (arm {h['static_arm']}, {h['static_label']}); "
             f"the best setting changed significantly {h['n_significant']} times ({len(h['epochs'])} epochs, median length "
             f"{h['median_epoch_days']:.0f} days; {h['raw_flips']} raw argmax flips, ambiguous-day fraction {h['ambiguous_fraction']:.2f}).")
    else:
        s = (f"Over {h['n_days']} daily snapshots the best mitigation setting for {c} was stationary: the drift value is "
             f"{h['drift_value_pct']:.1f} % (a fixed setting chosen once is within {h['drift_value_pct']:.1f} % of a perfect tracker), "
             f"with {h['raw_flips']} raw argmax flips and an ambiguous-day fraction of {h['ambiguous_fraction']:.2f}.")
    if L:
        best = min((n for n in L["learners"] if n in LEARNERS), key=lambda n: L["learners"][n]["regret_mean"])
        b, a7, so = L["learners"][best], L["learners"]["arm 7"], L["learners"]["static oracle"]
        s += (f" {best} had the lowest dynamic pseudo-regret, {b['regret_mean']:.2f} [{b['ci_lo']:.2f}, {b['ci_hi']:.2f}], "
              f"against {a7['regret_mean']:.2f} for the everything-on default and {so['regret_mean']:.2f} for the static oracle "
              f"(seeds {L['reported_on'][0]}–{L['reported_on'][-1]}{', tuned on the same seeds' if L['same_seeds_flag'] else ''}).")
    return s


def cmd_results_md(df):
    head = load_json("headline") or {}
    learners = load_json("learners") or {}
    proxy = load_json("proxy") or {}
    drivers = load_json("drivers") or {}
    sens = load_json("sensitivity") or {}
    lines = ["<!-- generated by scripts/analysis.py results-md; regenerated after every seed pass -->", ""]
    if not head:
        lines.append("No IBM drift results yet.")
    for c, h in head.items():
        lines.append(f"**{c}.** " + headline_sentence(c, h, learners.get(c)))
        lines.append("")
    if learners:
        lines += ["| circuit | learner | pseudo-regret (mean) | 95 % CI | vs arm 7 | switch lag (pulls) |", "|---|---|---|---|---|---|"]
        for c, e in learners.items():
            for name, L in e["learners"].items():
                lag = ", ".join(f"{v['mean']:.0f}" if v["mean"] is not None else "–" for v in L["switch_lag"].values()) or "–"
                lines.append(f"| {c} | {name} | {L['regret_mean']:.2f} | [{L['ci_lo']:.2f}, {L['ci_hi']:.2f}] | {L['captured_pct']:+.0f} % | {lag} |")
        lines.append("")
    if proxy:
        lines.append("**Proxy validation (per day).** " + " ".join(
            f"{c}: the mirror score picked the forward-best arm on {100 * r['top1_rate']:.0f} % of {r['n_days']} days "
            f"(median Spearman {r['spearman_median']:.2f}, median forward regret of the mirror pick {r['fwd_regret_median_pct']:.0f} % of the worst arm's)."
            for c, r in proxy.items()))
        lines.append("")
    if drivers:
        lines.append("**Drivers.** " + " ".join(
            (f"{c}: a multinomial logistic fit of the best arm on chain cz error, readout error, T1 and T2 reaches cross-validated accuracy "
             f"{e['cv_accuracy']:.2f} against a majority rate of {e['majority_rate']:.2f}; " if "cv_accuracy" in e else f"{c}: ")
            + f"{e['switches_within_1_day_of_recal']} of {e['switches']} significant switches fall within a day of a chip-wide recalibration (base rate {e['base_rate_near_recal']:.2f})."
            for c, e in drivers.items()))
        lines.append("")
    if sens:
        for k, v in sens.items():
            lines.append(f"**Sensitivity, {k.replace('_', ' ')}.** `{json.dumps(v, default=float)[:600]}`")
        lines.append("")
    figs = sorted(p.name for p in FIG.glob("*.png")) if FIG.exists() else []
    if figs:
        lines.append("**Figures.** " + ", ".join(f"`figures/{f}`" for f in figs))
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "results.md").write_text("\n".join(lines) + "\n")
    print(f"results-md: docs/results.md written ({len(lines)} lines)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["headline", "learners", "best-arm", "proxy", "drivers", "sensitivity", "pareto", "figures", "results-md", "all"])
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--pulls-per-snapshot", type=int, default=1)
    a = ap.parse_args()
    df = load_rows()
    print(f"loaded {len(df)} rows from data/")
    steps = {"headline": lambda: cmd_headline(df), "learners": lambda: cmd_learners(df, a.pulls_per_snapshot),
             "best-arm": lambda: cmd_best_arm(df), "proxy": lambda: cmd_proxy(df), "drivers": lambda: cmd_drivers(df),
             "sensitivity": lambda: cmd_sensitivity(df), "pareto": lambda: cmd_pareto(df),
             "figures": lambda: cmd_figures(df, a.quick), "results-md": lambda: cmd_results_md(df)}
    if a.cmd == "all":
        order = ["headline", "learners", "best-arm", "proxy", "drivers", "sensitivity", "pareto", "figures", "results-md"]
        if a.final:
            steps["learners4"] = lambda: cmd_learners(df, 4)
            order.insert(2, "learners4")
        for name in order:
            try:
                steps[name]()
            except Exception as e:
                print(f"{name}: failed: {type(e).__name__}: {str(e)[:300]}")
    else:
        steps[a.cmd]()


if __name__ == "__main__":
    main()
