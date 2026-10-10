"""AutoMitigate: a bandit that learns which error-mitigation settings to use for your circuit,
and notices when the device changes.

Press Run. The form under Run settings picks the circuit, the data source and the learner.
Replay mode needs no backend: the learner is replayed on reward tables committed in data/replay/,
recorded on two laptops from (a) a per-day noise model rebuilt from nine months of real
ibm_fez calibration data and (b) an IonQ-like model with a synthetic drift schedule.
With live = True the chosen backend runs one real pull of the recommended setting (Qollab
allows one circuit per run), so you can compare it with the replay.
"""
import json

import numpy as np

from automitigate.learners import LEARNERS, DynamicOracle, FixedArm, StaticOracle, run_episode, smooth_means

# Every data file the demo can read, as literal paths (the runtime loads only named files).
FILES = {
    "ibm:ghz4": "data/replay/ibm_ghz4.json", "ibm:qft3": "data/replay/ibm_qft3.json",
    "ibm:grover3": "data/replay/ibm_grover3.json", "ibm:ghz8": "data/replay/ibm_ghz8.json",
    "ibm:qaoa6": "data/replay/ibm_qaoa6.json",
    "ionq:ghz4:stable": "data/replay/ionq_ghz4_stable.json", "ionq:ghz4:slow": "data/replay/ionq_ghz4_slow.json",
    "ionq:ghz4:jump": "data/replay/ionq_ghz4_jump.json",
    "ionq:qft3:stable": "data/replay/ionq_qft3_stable.json", "ionq:qft3:slow": "data/replay/ionq_qft3_slow.json",
    "ionq:qft3:jump": "data/replay/ionq_qft3_jump.json",
    "ionq:grover3:stable": "data/replay/ionq_grover3_stable.json", "ionq:grover3:slow": "data/replay/ionq_grover3_slow.json",
    "ionq:grover3:jump": "data/replay/ionq_grover3_jump.json",
}
SUMMARY = "data/replay/summary.json"
ARM_LABEL = ["nothing", "REM", "twirl", "twirl + REM", "ZNE", "ZNE + REM", "ZNE + twirl", "ZNE + twirl + REM"]
SNIPPET = {
    "zne": "folded = fold(circuit, scale)            # run at scales 1, 3, 5 and extrapolate to 0",
    "twirl": "copies = [twirl(circuit, rng) for _ in range(8)]   # random Pauli pairs around each 2q gate",
    "rem": "probs = apply_rem(counts, cal_counts)   # tensored assignment-matrix inversion from |0..0>, |1..1>",
}


def load(path):
    with open(path) as fh:
        return json.load(fh)


def samples_array(table):
    arr = np.array([[[np.nan if x is None else x for x in row] for row in day] for day in table["samples"]], dtype=float)
    return arr


def recommendation(arms, window=20):
    tail = arms[-window:]
    counts = np.bincount(tail, minlength=8)
    return int(np.argmax(counts)), counts[np.argmax(counts)] / len(tail)


def snippet_for(arm):
    a = {"zne": arm & 4, "twirl": arm & 2, "rem": arm & 1}
    lines = ["from automitigate.arms import fold, twirl, apply_rem, transpile_once",
             "qc_t = transpile_once(circuit, chain, seed=0)   # optimisation level 1, once"]
    for k in ("zne", "twirl", "rem"):
        if a[k]:
            lines.append(SNIPPET[k])
    if not any(a.values()):
        lines.append("# nothing: run qc_t as is")
    return "\n".join(lines)


def main(circuit: str = "ghz8", source: str = "ibm", schedule: str = "jump", learner: str = "eps-greedy",
         replays: int = 30, live: bool = False):
    import matplotlib.pyplot as plt

    key = f"ionq:{circuit}:{schedule}" if source.startswith("ionq") else f"ibm:{circuit}"
    if key not in FILES:
        print(f"No replay table for {key}. Choose circuit in {sorted({k.split(':')[1] for k in FILES})}, "
              f"source ibm or ionq, schedule stable / slow / jump (ionq only).")
        return
    try:
        table = load(FILES[key])
    except OSError:
        print(f"{FILES[key]} is not in this project yet (the sweep that produces it has not finished).")
        return
    if learner not in LEARNERS:
        print(f"learner must be one of {list(LEARNERS)}")
        return
    arr = samples_array(table)
    T, K, S = arr.shape
    smooth = 1 if source == "ibm" else 21  # 5 seeds per step on the IonQ-like tables: oracle from a 21-step moving average
    means = smooth_means(np.nanmean(arr, axis=2), smooth)
    best = np.nanargmax(means, axis=1)
    static_arm = int(np.argmax(np.nansum(means, axis=0)))
    try:
        summary = load(SUMMARY).get(circuit, {})
    except OSError:
        summary = {}
    hp = (summary.get("hp") or {}) if source == "ibm" else {}
    hp_map = {"Discounted TS": {"gamma": hp.get("gamma", 0.9)}, "Sliding-Window TS": {"window": hp.get("window", 20)},
              "Change-Detection TS": {"window": hp.get("window", 20), "threshold": 3.0}}

    unit = "daily calibration snapshot" if source == "ibm" else "drift step"
    print(f"AutoMitigate replay: {circuit}, source = {'real ibm_fez drift (' + str(T) + ' days)' if source == 'ibm' else 'IonQ-like model, ' + schedule + ' schedule (' + str(T) + ' steps)'}, "
          f"{S} seed(s) per cell, learner = {learner}, {replays} replays.")
    print(f"Arms: " + ", ".join(f"{i} = {l}" for i, l in enumerate(ARM_LABEL)))
    if source == "ibm" and summary:
        print(f"Pre-registered headline for {circuit}: drift value {summary['drift_value_pct']:.1f} % of the static oracle, "
              f"{summary['n_significant']} significant best-arm switches ({summary['raw_flips']} raw flips) over {summary['n_days']} days "
              f"x {summary['n_seeds']} seeds; static oracle = arm {summary['static_arm']} ({ARM_LABEL[summary['static_arm']]}).")

    policies = {learner: lambda i: LEARNERS[learner](K, seed=i, **hp_map.get(learner, {})),
                "Thompson": lambda i: LEARNERS["Thompson"](K, seed=i),
                "everything on (arm 7)": lambda i: FixedArm(K, seed=i, arm=7),
                "static oracle": lambda i: StaticOracle(K, seed=i, arm=static_arm),
                "dynamic oracle": lambda i: DynamicOracle(K, seed=i, best_per_step=best.tolist())}
    if learner == "Thompson":
        policies.pop("Thompson")
    results, example = {}, None
    for name, factory in policies.items():
        n = replays if name in LEARNERS else max(3, replays // 5)
        curves, finals, arms_runs = [], [], []
        for i in range(n):
            out = run_episode(factory(i), arr, np.random.default_rng(100 + i), smooth=smooth)
            curves.append(out["pseudo_regret"])
            finals.append(out["pseudo_regret"][-1])
            arms_runs.append(out["arms"])
        results[name] = {"curve": np.mean(curves, axis=0), "final": float(np.mean(finals)),
                         "lo": float(np.percentile(finals, 2.5)), "hi": float(np.percentile(finals, 97.5)), "arms": arms_runs[0]}
    print()
    print(f"{'policy':28s} {'pseudo-regret':>14s}   95 % interval")
    for name, r in results.items():
        print(f"{name:28s} {r['final']:14.2f}   [{r['lo']:.2f}, {r['hi']:.2f}]")

    arms = np.array(results[learner]["arms"])
    rec, share = recommendation(arms)
    print()
    print(f"Recommendation after {T} pulls: arm {rec} = {ARM_LABEL[rec]} (chosen in {100 * share:.0f} % of the last 20 pulls; "
          f"best arm at the end by the seed-mean table{'' if smooth == 1 else f' ({smooth}-step moving average)'}: arm {int(best[-1])} = {ARM_LABEL[int(best[-1])]}).")
    print("Qiskit snippet for that setting:")
    print(snippet_for(rec))
    switches = [t for t in range(1, T) if best[t] != best[t - 1]]
    print(f"\nThe seed-mean best arm changed {len(switches)} times along this replay"
          + (f"; the learner's first pick after the last change came {int(np.argmax(arms[switches[-1]:] == best[-1]))} pulls later." if switches else "."))

    fig, axes = plt.subplots(2, 1, figsize=(8, 6.5), gridspec_kw={"height_ratios": [3, 1.6]})
    ax = axes[0]
    for name, r in results.items():
        style = {"everything on (arm 7)": "--", "static oracle": "-.", "dynamic oracle": ":"}.get(name, "-")
        ax.plot(r["curve"], label=name, linestyle=style, linewidth=2 if name == learner else 1.2)
    ax.set_xlabel(f"pull (one per {unit})")
    ax.set_ylabel("cumulative pseudo-regret")
    ax.set_title(f"{circuit} on {'real ibm_fez drift' if source == 'ibm' else 'IonQ-like drift, ' + schedule}: {learner} vs fixed policies")
    ax.legend(fontsize=8, frameon=False)
    ax = axes[1]
    ax.step(range(T), best, where="mid", color="black", linewidth=1,
            label="best arm (seed mean)" if smooth == 1 else f"best arm (seed mean, {smooth}-step moving average)")
    ax.scatter(range(T), arms, s=6, color="tab:blue", label=f"{learner} choice")
    ax.set_yticks(range(K))
    ax.set_yticklabels(ARM_LABEL, fontsize=7)
    ax.set_xlabel(unit)
    ax.legend(fontsize=7, frameon=False, loc="upper right")
    fig.tight_layout()
    plt.show()

    if live:
        live_pull(circuit, rec)


def live_pull(circuit, arm):
    """One real pull on the selected backend: the mirror circuit of the recommended setting's
    cheapest shape (one circuit, because Qollab allows one job per run)."""
    try:
        from automitigate.arms import apply_arm, transpile_once
        from automitigate.circuits import CIRCUITS
        from automitigate.score import frac_target
    except Exception as e:
        print(f"live mode needs the automitigate package in the project ({e})")
        return
    qc = CIRCUITS[circuit]()
    qc_t = transpile_once(qc, list(range(qc.num_qubits)), seed=0)
    circs, target = apply_arm(qc_t, {"zne": 0, "twirl": 0, "rem": 0}, twin_rng_seed=0)
    print(f"\nLive: running one mirror circuit of {circuit} on {getattr(backend, 'name', 'the selected backend')} ...")  # noqa: F821
    job = backend.run(circs[0], shots=1200)  # noqa: F821
    counts = {str(k).replace(" ", ""): v for k, v in job.result().get_counts().items()}
    print(f"P(target={target}) = {frac_target(counts, target):.3f} on the backend (arm 0 shape; the recommended arm {arm} "
          f"adds {ARM_LABEL[arm]} on top, which needs several circuits).")
