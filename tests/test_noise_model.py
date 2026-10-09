from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("qiskit_aer")

from automitigate import noise_model as nm  # noqa: E402
from automitigate.arms import ARMS, apply_arm, transpile_once  # noqa: E402
from automitigate.circuits import ghz4  # noqa: E402
from automitigate.score import frac_target, score_pull  # noqa: E402

DAILY = Path(__file__).resolve().parents[1] / "data" / "calibration_daily_fez.parquet"
needs_data = pytest.mark.skipif(not DAILY.exists(), reason="derived daily table not present")


@pytest.fixture(scope="module")
def daily():
    return nm.load_daily(DAILY)


@pytest.fixture(scope="module")
def ghz4_cells():
    qc_t = transpile_once(ghz4(), [0, 1, 2, 3], seed=1)
    return [apply_arm(qc_t, ARMS[0], twin_rng_seed=s) for s in range(4)]


def score_arm0(cells, model, shots=4000, seed=0):
    vals = []
    for k, (circs, target) in enumerate(cells):
        counts = nm.run(circs, model, shots, nm.seed_for("t", seed, k))
        vals.append(score_pull(counts, ARMS[0], target, 4)[0])
    return float(np.mean(vals))


def score_arm(arm, cells_arm, model, shots, seed=0):
    vals = []
    for k, (circs, target) in enumerate(cells_arm):
        counts = nm.run(circs, model, shots, nm.seed_for("t", seed, k))
        vals.append(score_pull(counts, arm, target, 4)[0])
    return float(np.mean(vals)), float(np.std(vals) / np.sqrt(len(vals)))


@needs_data
def test_N1_every_day_builds(daily):
    days = nm.snapshots(daily)
    assert len(days) == 241
    chain = nm.choose_chain(daily, days[0], 4)
    assert nm.first_complete_day(daily) <= days[3]
    skipped = []
    for d in days:
        try:
            nm.noise_model_for(daily, d, chain)
        except nm.SkipDay as e:
            skipped.append((d, str(e)))
    assert len(skipped) <= 2, skipped
    chain8 = nm.choose_chain(daily, days[0], 8)
    assert len(chain8) == 8 and len(set(chain8)) == 8
    assert nm.choose_chain(daily, days[0], 4, rank="median") != chain


@needs_data
def test_N2_low_error_day_beats_high_error_day(daily, ghz4_cells):
    days = nm.snapshots(daily)
    chain = nm.choose_chain(daily, days[0], 4)
    err = {}
    for d in days:
        if d < nm.first_complete_day(daily):
            continue
        st = nm.daily_state(daily, d)
        vals = []
        for a, b in zip(chain, chain[1:]):
            for x, y in ((a, b), (b, a)):
                v = st.get(("cz_error", x, y))
                if v and not v[1] and np.isfinite(v[0]) and v[0] < 0.999:
                    vals.append(v[0])
        if len(vals) == 2 * (len(chain) - 1):
            err[d] = float(np.mean(vals))
    lo, hi = min(err, key=err.get), max(err, key=err.get)
    s_lo = score_arm0(ghz4_cells, nm.noise_model_for(daily, lo, chain))
    s_hi = score_arm0(ghz4_cells, nm.noise_model_for(daily, hi, chain))
    assert s_lo > s_hi, (lo, s_lo, hi, s_hi)


def test_N3_monotone_in_2q_error(ghz4_cells):
    scores = [score_arm0(ghz4_cells, nm.ionq_static(0.0, p2, 0.0)) for p2 in (0.001, 0.005, 0.02, 0.05)]
    assert all(a >= b - 0.01 for a, b in zip(scores, scores[1:])), scores


def test_N4_seed_determinism(ghz4_cells):
    circs, _ = ghz4_cells[0]
    model = nm.ionq_static(0.001, 0.01, 0.01)
    a = nm.run(circs, model, 300, nm.seed_for("2026-02-02", 3))
    b = nm.run(circs, model, 300, nm.seed_for("2026-02-02", 3))
    c = nm.run(circs, model, 300, nm.seed_for("2026-02-03", 3))
    assert a == b and a != c


def test_N5_readout_only(ghz4_cells):
    r = 0.03
    circs, target = ghz4_cells[0]
    counts = nm.run(circs, nm.ionq_static(0.0, 0.0, r), 100000, 5)[0]
    assert frac_target(counts, target) == pytest.approx((1 - r) ** 4, abs=0.004)


@needs_data
def test_N6_coherent_fraction_echo(daily):
    """With a coherent fraction the mirror circuit partially echoes the over-rotation:
    the untwirled score stays close to its f=0 value while the twirled score falls
    (twirling converts the coherent part into stochastic error that no longer cancels)."""
    rows = []
    for q in range(4):
        for p, v in (("T1", 300.0), ("T2", 200.0), ("sx_length", 24.0), ("readout_length", 1560.0),
                     ("sx_error", 2e-4), ("x_error", 2e-4), ("prob_meas1_prep0", 0.0), ("prob_meas0_prep1", 0.0)):
            rows.append((p, q, -1, v))
    for a in range(3):
        for x, y in ((a, a + 1), (a + 1, a)):
            rows.append(("cz_error", x, y, 0.03))
            rows.append(("cz_length", x, y, 68.0))
    import pandas as pd
    d = pd.DataFrame(rows, columns=["property_family", "qubit_a", "qb", "value"])
    d["day"] = "D"
    d["ceiling"] = False
    qc_t = transpile_once(ghz4(), [0, 1, 2, 3], seed=1)
    cells = {i: [apply_arm(qc_t, ARMS[i], twin_rng_seed=100 + s) for s in range(8)] for i in (0, 2)}
    out = {}
    for f in (0.0, 0.3):
        model = nm.noise_model_for(d, "D", [0, 1, 2, 3], f=f)
        out[f] = {i: score_arm(ARMS[i], cells[i], model, 4000) for i in (0, 2)}
    (u0, u0se), (t0, _) = out[0.0][0], out[0.0][2]
    (u3, u3se), (t3, t3se) = out[0.3][0], out[0.3][2]
    assert abs(t3 - t0) < 3 * (t3se + 0.002) + 0.01, out  # twirled: same total infidelity, same score
    assert u3 > u0 - 3 * (u0se + u3se), out  # untwirled: the mirror echoes part of the coherent error
    assert u3 - u0 > t3 - t0, out  # so f flatters the untwirled arm relative to the twirled one
