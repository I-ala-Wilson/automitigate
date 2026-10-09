import itertools

import numpy as np
import pytest
from qiskit.circuit.library import CZGate
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import Pauli, Statevector

from automitigate.arms import (ARMS, BASIS, TRANSLATE_BASIS, _cz_conj, apply_arm, apply_rem,
                               build_twin, fold, inject_drift, rem_calibration_circuits,
                               shots_per_circuit, translate, transpile_once, twirl, two_q_count)
from automitigate.circuits import CIRCUITS, ghz4
from automitigate.score import cost, frac_target, polarisation, score_pull, zne_extrapolate

CHAIN4 = [10, 11, 12, 13]


def ideal_counts(qc, shots=1000, seed=0):
    return StatevectorSampler(seed=seed).run([qc], shots=shots).result()[0].data.meas.get_counts()


def measured(qc):
    m = qc.copy()
    m.measure_all()
    return m


def ghz4_t():
    return transpile_once(ghz4(), CHAIN4, seed=1)


def test_1_ghz4_ideal():
    c = ideal_counts(measured(ghz4()))
    assert set(c) == {"0000", "1111"}
    assert 400 <= c["0000"] <= 600


def test_2_twin_is_target_only():
    twin, target = build_twin(ghz4_t(), np.random.default_rng(3))
    assert ideal_counts(measured(twin)) == {target: 1000}


def test_3_twirl_keeps_target():
    twin, target = build_twin(ghz4_t(), np.random.default_rng(3))
    tw = twirl(twin, np.random.default_rng(5))
    assert ideal_counts(measured(tw)) == {target: 1000}
    assert two_q_count(tw) == two_q_count(twin)


def test_4_fold_keeps_target_and_triples_2q():
    twin, target = build_twin(ghz4_t(), np.random.default_rng(3))
    f3 = fold(twin, 3)
    assert ideal_counts(measured(f3)) == {target: 1000}
    assert two_q_count(f3) == 3 * two_q_count(twin)
    assert two_q_count(fold(twin, 5)) == 5 * two_q_count(twin)


def test_5_translate_does_not_eat_fold_or_twirl():
    twin, target = build_twin(ghz4_t(), np.random.default_rng(3))
    f3 = twirl(fold(twin, 3), np.random.default_rng(5))
    t = translate(measured(f3))
    assert two_q_count(t) == 3 * two_q_count(twin)
    assert ideal_counts(t) == {target: 1000}


def test_6_drift_zero_is_noop_and_nonzero_is_not():
    twin, target = build_twin(ghz4_t(), np.random.default_rng(3))
    clean = inject_drift(twin, 0, 0, np.random.default_rng(0))
    assert ideal_counts(measured(clean)) == {target: 1000}
    dirty = inject_drift(twin, 0.2, 0.3, np.random.default_rng(0))
    assert frac_target(ideal_counts(measured(dirty)), target) < 0.99
    assert two_q_count(dirty) == two_q_count(twin)


def test_7_apply_arm_shapes_and_rem_pairs():
    qc_t = ghz4_t()
    sizes = {}
    for i, arm in enumerate(ARMS):
        circs, target = apply_arm(qc_t, arm, twin_rng_seed=11)
        sizes[i] = len(circs)
        assert len(target) == 4
    assert [sizes[i] for i in range(8)] == [1, 1, 8, 8, 3, 3, 24, 24]
    for i in (0, 2, 4, 6):
        a, ta = apply_arm(qc_t, ARMS[i], twin_rng_seed=11)
        b, tb = apply_arm(qc_t, ARMS[i + 1], twin_rng_seed=11)
        assert ta == tb and all(x == y for x, y in zip(a, b))
    targets = {apply_arm(qc_t, arm, twin_rng_seed=11)[1] for arm in ARMS}
    assert len(targets) == 1


def test_8_score_pull_ideal_is_one():
    qc_t = ghz4_t()
    cal = [ideal_counts(c, 400, 1) for c in rem_calibration_circuits(4)]
    for arm in ARMS:
        circs, target = apply_arm(qc_t, arm, twin_rng_seed=2)
        counts = [ideal_counts(c, shots_per_circuit(arm), seed=k) for k, c in enumerate(circs)]
        score, aux = score_pull(counts, arm, target, 4, cal_counts=cal if arm["rem"] else None)
        assert score == pytest.approx(1.0)
        assert aux["clipped"] is False
        assert aux["polarisation"] == pytest.approx(1.0)
        assert (aux["by_scale"] is not None) == bool(arm["zne"])


def test_9_seeds():
    qc = measured(ghz4())
    assert ideal_counts(qc, seed=4) == ideal_counts(qc, seed=4)
    assert ideal_counts(qc, seed=4) != ideal_counts(qc, seed=5)


def test_10_randomised_mirror_statevector():
    rng = np.random.default_rng(123)
    for name, make in CIRCUITS.items():
        qc = make()
        qc_t = transpile_once(qc, list(range(qc.num_qubits)), seed=7)
        for _ in range(20):
            twin, target = build_twin(qc_t, rng)
            probs = Statevector(twin).probabilities_dict()
            assert probs.get(target, 0.0) == pytest.approx(1.0, abs=1e-9), name


def test_10b_cz_frame_table_matches_quantum_info():
    for pa, pb in itertools.product("IXYZ", repeat=2):
        got = _cz_conj(pa, pb)
        ref = Pauli(pb + pa).evolve(CZGate(), frame="h")
        assert Pauli(got[1] + got[0]).equiv(ref), (pa, pb)


def test_11_translate_basis_and_2q_count():
    for name, make in CIRCUITS.items():
        qc = make()
        qc_t = transpile_once(qc, list(range(qc.num_qubits)), seed=7)
        for arm in (ARMS[0], ARMS[7]):
            circs, _ = apply_arm(qc_t, arm, twin_rng_seed=1, drift={"p": 0.05, "theta": 0.1})
            for c in circs:
                names = set(c.count_ops()) - {"barrier", "measure"}
                assert names <= set(TRANSLATE_BASIS), (name, names)
            plain, _ = apply_arm(qc_t, arm, twin_rng_seed=1)
            assert [two_q_count(c) for c in circs] == [two_q_count(c) for c in plain]
            for c in plain:
                assert set(c.count_ops()) - {"barrier", "measure"} <= set(BASIS)


def _flip_dist(true_bits: str, r: float, shots=1000):
    n = len(true_bits)
    out = {}
    for bits in itertools.product("01", repeat=n):
        key = "".join(bits)
        p = 1.0
        for a, b in zip(key, true_bits):
            p *= (1 - r) if a == b else r
        out[key] = p * shots
    return out


def test_12_rem_identity_and_recovery():
    n = 4
    cal = [_flip_dist("0" * n, 0.0), _flip_dist("1" * n, 0.0)]
    counts = {"0110": 700, "1001": 300}
    out = apply_rem(counts, cal)
    assert out["0110"] == pytest.approx(0.7) and out["1001"] == pytest.approx(0.3)
    cal = [_flip_dist("0" * n, 0.05), _flip_dist("1" * n, 0.05)]
    noisy = _flip_dist("0110", 0.05)
    assert frac_target(noisy, "0110") < 0.85
    out = apply_rem(noisy, cal)
    assert frac_target(out, "0110") == pytest.approx(1.0, abs=0.01)


def test_zne_and_helpers():
    assert zne_extrapolate({1: 0.9, 3: 0.7, 5: 0.5}) == pytest.approx(1.0)
    assert zne_extrapolate({1: 0.8, 3: 0.6, 5: 0.4}) == pytest.approx(0.9)
    assert zne_extrapolate({1: 0.8, 3: 0.6, 5: 0.4}, method="exp", n_qubits=4) > 0.8
    assert polarisation(1.0, 4) == 1.0 and polarisation(1 / 16, 4) == 0.0
    assert [cost(a) for a in ARMS] == [1, 3, 8, 10, 3, 5, 24, 26]
    assert [shots_per_circuit(a) for a in ARMS] == [1200, 1200, 150, 150, 400, 400, 50, 50]
