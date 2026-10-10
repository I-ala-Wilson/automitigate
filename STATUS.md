# STATUS

Work log for the AutoMitigate repo. One block per work session or pipeline stage, newest at the bottom. Signed `[ian]` or `[thomas]`. The sweep pipeline (`scripts/run_queue.py`) appends its own blocks. This file is append-only (`.gitattributes` merges concurrent appends).

Format:

```
## YYYY-MM-DD HH:MM ET  [ian|thomas]
done: ...
blocked: ...
next: ...
needs-other-side: ...
```

---

## 2026-10-09 19:00 ET  [ian]
done: repo created from the seed, Thomas added as collaborator, Actions enabled.
blocked: none
next: qollab/e0_checks.py (by 19:30), then circuits.py, arms.py, score.py, tests 1–13; docs/analysis_plan.md before Q2 pass 0; run_queue.py + queue.ps1/queue.sh by 22:00, then `run_queue ready` is posted here.
needs-other-side: none until `run_queue ready` appears below.

## 2026-10-09 19:40 ET  [ian]
done: repo public at https://github.com/I-ala-Wilson/automitigate; qollab/e0_checks.py pushed (list-job, fold, repeat, readout, 1q/2q depth sweeps fitted to p1q_fit/p2q_fit/r0_fit/r1_fit; tested against a fake simulator with known noise, fits recover the constants within 10 %). circuits.py, arms.py (randomised mirror twin with Pauli-frame-propagated inverse, global fold, twirl, drift, REM), score.py; tests 1–12 green on the ideal sampler (test 13 lands with learners.py).
note: order inside apply_arm is twin -> fold -> twirl -> drift so every folded copy of a cz gets its own twirl Paulis and error draw; drift theta is an over-rotated cz (rzz(pi/2+theta) + rz dressing, still one two-qubit gate), so a theta sweep does not change the gate count.
blocked: none
next: scripts/run_queue.py + queue.ps1/queue.sh, then `run_queue ready` here; scripts/sweep.py; noise_model.py; docs/analysis_plan.md before Q2 pass 0.
needs-other-side: Thomas: E0 (paste qollab/e0_checks.py into the Code tab on Aria-1, copy the JSON into data/e0.json, push).

## 2026-10-09 21:40 ET  [thomas]
done: E0 run on Qollab, IonQ Aria-1 simulator (25q); JSON in data/e0.json.
blocked: Qollab allows ONE circuit-execution job per code run. Bell probe ran (P(00|11) = 0.992); list_job, fold, repeat, readout, depth_1q, depth_2q all failed with "The code has already filed one circuit execution job; only one job is allowed per code run". list_jobs_ok = false, ok = false, 12 s total.
note: after the script ends Qollab raises NameError: name 'main' is not defined, so it seems to expect a main() entry point.
next: waiting for a fixed e0_checks.py (one job per Run, or split into several scripts) and for `run_queue ready`.
needs-other-side: Ian: this affects E0, E4 spot check (200 pulls) and live mode.