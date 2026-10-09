import pytest


def test_package_imports():
    import automitigate
    assert automitigate.__version__


def test_aer_runs_if_installed():
    aer = pytest.importorskip("qiskit_aer")
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    counts = aer.AerSimulator(seed_simulator=1).run(qc, shots=200).result().get_counts()
    assert set(counts) <= {"00", "11"}
