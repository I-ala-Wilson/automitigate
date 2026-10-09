"""The five benchmark circuits, without measurements."""
from math import pi

from qiskit import QuantumCircuit


def ghz(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, name=f"ghz{n}")
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    return qc


def ghz4() -> QuantumCircuit:
    return ghz(4)


def ghz8() -> QuantumCircuit:
    return ghz(8)


def qft3() -> QuantumCircuit:
    """QFT of the basis state |101>, so the output has non-trivial phases."""
    qc = QuantumCircuit(3, name="qft3")
    qc.x(0)
    qc.x(2)
    for j in range(3):
        qc.h(j)
        for k in range(j + 1, 3):
            qc.cp(pi / 2 ** (k - j), k, j)
    qc.swap(0, 2)
    return qc


def _ccz(qc: QuantumCircuit) -> None:
    qc.h(2)
    qc.ccx(0, 1, 2)
    qc.h(2)


def grover3() -> QuantumCircuit:
    """Two Grover iterations on 3 qubits, marked state |101> (P ~ 0.945)."""
    qc = QuantumCircuit(3, name="grover3")
    qc.h(range(3))
    for _ in range(2):
        qc.x(1)
        _ccz(qc)
        qc.x(1)
        qc.h(range(3))
        qc.x(range(3))
        _ccz(qc)
        qc.x(range(3))
        qc.h(range(3))
    return qc


QAOA6_EDGES = [(i, (i + 1) % 6) for i in range(6)]
QAOA6_GAMMA = 0.62
QAOA6_BETA = 0.39


def qaoa6() -> QuantumCircuit:
    """One-layer QAOA for MaxCut on the 6-ring with fixed angles."""
    qc = QuantumCircuit(6, name="qaoa6")
    qc.h(range(6))
    for a, b in QAOA6_EDGES:
        qc.rzz(2 * QAOA6_GAMMA, a, b)
    qc.rx(2 * QAOA6_BETA, range(6))
    return qc


GROVER3_MARKED = "101"

CIRCUITS = {"ghz4": ghz4, "qft3": qft3, "grover3": grover3, "ghz8": ghz8, "qaoa6": qaoa6}
