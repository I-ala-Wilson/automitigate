"""Reward from mirror-circuit counts: target fraction, ZNE extrapolation, REM."""
from __future__ import annotations

import numpy as np

from automitigate.arms import SCALES, TWIRL_COPIES, apply_rem


def frac_target(counts: dict, target: str) -> float:
    tot = sum(counts.values())
    if tot == 0:
        return 0.0
    hit = sum(v for k, v in counts.items() if k.replace(" ", "")[-len(target):] == target)
    return float(hit / tot)


def polarisation(p: float, n: int) -> float:
    base = 2.0 ** (-n)
    return float((p - base) / (1 - base))


def _zne(scores_by_scale: dict, method: str, base: float) -> tuple[float, bool, str]:
    """(value, clipped, method_used). exp falls back to linear when a score sits at
    or below the uniform baseline, and says so in method_used."""
    s = np.array(sorted(int(k) for k in scores_by_scale), dtype=float)
    y = np.array([scores_by_scale[k] for k in sorted(scores_by_scale, key=int)], dtype=float)
    value, used = None, "linear"
    if method == "exp":
        d = y - base
        if np.all(d > 0):
            b, a = np.polyfit(s, np.log(d), 1)
            value, used = base + float(np.exp(a)), "exp"
    if value is None:
        slope, intercept = np.polyfit(s, y, 1)
        value = float(intercept)
    clipped = value < -1e-9 or value > 1.0 + 1e-9
    return float(min(1.0, max(0.0, value))), clipped, used


def zne_extrapolate(scores_by_scale: dict, method: str = "linear", n_qubits: int = 0) -> float:
    """Zero-noise value from scores at scales {1,3,5}. linear = fit read at 0 (primary);
    exp = a*exp(-b s) + 2^-n (sensitivity). Clipped to [0, 1]."""
    return _zne(scores_by_scale, method, 2.0 ** (-n_qubits) if n_qubits else 0.0)[0]


def score_pull(list_of_counts: list[dict], arm: dict, target: str, n_qubits: int,
               cal_counts: list[dict] | None = None, zne_method: str = "linear") -> tuple[float, dict]:
    """Reward of one pull and its breakdown. Counts are grouped by scale in the order
    apply_arm produced them: all copies of scale 1, then 3, then 5."""
    scales = SCALES if arm["zne"] else [1]
    copies = TWIRL_COPIES if arm["twirl"] else 1
    if len(list_of_counts) != len(scales) * copies:
        raise ValueError(f"expected {len(scales) * copies} counts, got {len(list_of_counts)}")
    if len(target) != n_qubits:
        raise ValueError(f"target {target!r} is not {n_qubits} bits")
    raw = float(np.mean([frac_target(c, target) for c in list_of_counts[:copies]]))  # scale 1, before REM
    if arm["rem"]:
        if cal_counts is None:
            raise ValueError("REM arm needs cal_counts")
        list_of_counts = [apply_rem(c, cal_counts) for c in list_of_counts]
    by_scale = {}
    for i, s in enumerate(scales):
        block = list_of_counts[i * copies:(i + 1) * copies]
        by_scale[s] = float(np.mean([frac_target(c, target) for c in block]))
    clipped, used = False, None
    if arm["zne"]:
        score, clipped, used = _zne(by_scale, zne_method, 2.0 ** (-n_qubits))
    else:
        score = by_scale[1]
    aux = {
        "raw": raw,
        "by_scale": {str(k): v for k, v in by_scale.items()} if arm["zne"] else None,
        "rem": by_scale[1] if arm["rem"] else None,
        "zne_method": used,
        "clipped": clipped,
        "polarisation": polarisation(score, n_qubits),
    }
    return float(score), aux


def cost(arm: dict) -> int:
    """Circuits per pull: 1 / 3 / 8 / 24, plus 2 calibration circuits if rem."""
    return (3 if arm["zne"] else 1) * (TWIRL_COPIES if arm["twirl"] else 1) + (2 if arm["rem"] else 0)
