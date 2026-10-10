import numpy as np
import pytest
from qiskit.primitives import StatevectorSampler

from automitigate.arms import ARMS, rem_calibration_circuits, shots_per_circuit, transpile_once
from automitigate.circuits import CIRCUITS
from automitigate.forward import estimate, forward_circuits, forward_fidelity, layout_perm, spec


def counts_of(qc, shots, seed=0):
    return StatevectorSampler(seed=seed).run([qc], shots=shots).result()[0].data.meas.get_counts()


@pytest.mark.parametrize("name", list(CIRCUITS))
def test_ideal_estimate_matches_statevector(name):
    sp = spec(name)
    qc = sp["circuit"].copy()
    qc.measure_all()
    est = estimate(counts_of(qc, 20000), sp)
    assert est == pytest.approx(sp["ideal"], abs=0.03), (name, est, sp["ideal"])
    assert sp["ideal"] > 0.5 if sp["kind"] != "maxcut" else sp["ideal"] > 1.5  # fixed angles give <C> = 2.08 on the 6-ring


@pytest.mark.parametrize("name", ["ghz4", "qft3", "grover3", "qaoa6"])
def test_transpiled_forward_with_layout(name):
    sp = spec(name)
    qc_t = transpile_once(sp["circuit"], list(range(sp["n"])), seed=3)
    perm = layout_perm(qc_t)
    assert sorted(perm) == list(range(sp["n"]))
    qc = qc_t.copy()
    qc.measure_all()
    assert estimate(counts_of(qc, 20000), sp, perm) == pytest.approx(sp["ideal"], abs=0.03)


def test_forward_fidelity_ideal_is_one():
    sp = spec("ghz4")
    qc_t = transpile_once(sp["circuit"], [0, 1, 2, 3], seed=3)
    perm = layout_perm(qc_t)
    cal = [counts_of(c, 400, 1) for c in rem_calibration_circuits(4)]
    for arm in ARMS:
        circs = forward_circuits(qc_t, arm, draw_seed=5)
        counts = [counts_of(c, shots_per_circuit(arm), seed=k) for k, c in enumerate(circs)]
        fid, e = forward_fidelity(counts, arm, sp, perm, cal if arm["rem"] else None)
        assert fid == pytest.approx(1.0, abs=1e-9) and e == pytest.approx(1.0)
