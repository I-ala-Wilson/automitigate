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
## 2026-10-09 22:50 ET  [ian]
done: scripts/sweep.py (static / ionq_like / ibm, resumable, #progress lines), scripts/pick_ab.py, scripts/run_queue.py + scripts/queue.sh + scripts/queue.ps1, data/calibration_daily_fez.parquet (241 days), noise_model.py with tests N1–N6 (22 tests green). Measured on the Mac, seconds per (day, circuit) cell: ghz4 0.3, qft3 0.5, ghz8 1.4, grover3 1.5, qaoa6 3.2. Simulation is density-matrix (the statevector method wedges on these Kraus models at 8 qubits).
split: Mac runs Q1, Q1b, Q2 passes for ghz4, ghz8, grover3, Q3/Q4/Q5; Yoga runs Q2 passes for qft3, qaoa6, then Q2b and Q6. The queue only runs a stage whose inputs exist, so it can be started now and waits by itself.
run_queue ready
blocked: none
next: docs/analysis_plan.md (the ibm passes wait for it), then a one-job rewrite of qollab/e0_checks.py (Qollab allows one backend.run per Run and calls main()), learners.py + analysis.py Saturday morning.
needs-other-side: Thomas: `git pull` then `.\scripts\queue.ps1` in the repo PowerShell with the venv active; leave the window open. Re-run E0 when the new e0_checks.py lands (it will say so here).

## 2026-10-09 22:49 ET  [ian]
done: queue started on ian (darwin, python 3.12.3)
blocked: none
next: first runnable stage
needs-other-side: none

## 2026-10-09 23:10 ET  [ian]
done: qollab/e0_checks.py rewritten as ONE list job (47 circuits x 1000 shots) with a main() entry point, as Qollab requires; tested against a fake one-job backend (fits recover p1q 0.001 -> 0.001, p2q 0.01 -> 0.009). docs/analysis_plan.md committed before any IBM pass. Mac queue running.
blocked: none
next: learners.py, analysis.py, qollab/spot_check_ionq.py (also single-job) Saturday morning.
needs-other-side: Thomas: re-run E0 with the new qollab/e0_checks.py (git pull, paste, Run, copy the JSON into data/e0.json, commit `[thomas] e0 checks v2`, push). Then start the queue if not yet running: `.\scripts\queue.ps1`.

## 2026-10-09 22:58 ET  [thomas]
done: queue started on thomas (win32, python 3.12.10)
blocked: none
next: first runnable stage
needs-other-side: none

## 2026-10-09 23:10 ET  [thomas]
done: E0 v2 run on Qollab, IonQ Aria-1 simulator; JSON in data/e0.json.
blocked: the single 47-circuit list job is rejected: IonQAPIError 400 "Only job type ionq.circuit.v1 is supported". Combined with v1 ("only one job is allowed per code run"), Qollab's IonQ simulator takes ONE circuit per code run. max_circuits = null, 0.6 s.
next: Ian's call on E0/E4/live mode given one circuit per run (e.g. a tiny E0 with one circuit, or run probes as separate Runs).
needs-other-side: Ian.
## 2026-10-09 23:25 ET  [ian]
done: Qollab = one circuit per Run, so E0 is now qollab/e0_single.py: 7 Runs by hand (set RUN = 1..7, Run, copy the one JSON line into data/e0_runs.jsonl), then scripts/fit_e0.py fits p1q/p2q/r0/r1 and the fold check into data/e0.json. Tested on a fake backend: recovers the injected constants. The spot check (E4) will be a few single-circuit Runs the same way; live mode is out. Neither queue depends on any of this.
blocked: none
next: learners.py, analysis.py, forward.py, spot check, web (Saturday).
needs-other-side: Thomas, Sat ~11:00 (not tonight): the 7 E0 Runs above, then `git add data/e0_runs.jsonl`, commit `[thomas] e0 runs`, push.

## 2026-10-09 23:08 ET  [ian]
done: Q2_seed0 finished in 14 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-09 23:15 ET  [ian]
done: Q1 finished in 7 min (ladder: max_seeds=20, rungs=none)
## 2026-10-09 23:15 ET  [thomas]
done: Q2_seed0 finished in 17 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-09 23:35 ET  [thomas]
done: Q2_seed0 pushed (17 min on the Yoga).
blocked: the queue's push got stuck mid-rebase on a conflict in data/calib/chains.json: both laptops write it (Mac: sizes 3/4/8, Yoga: sizes 3/6; size 3 identical). Resolved by hand as the union of both, pushed. The queue's later pulls would have stayed stuck until then.
needs-other-side: Ian: make chains.json single-writer or per-laptop (chains_<laptop>.json), or it will conflict again the next time either side rewrites it.
## 2026-10-09 23:23 ET  [ian]
done: queue started on ian (darwin, python 3.12.3)
blocked: none
next: first runnable stage
needs-other-side: none

## 2026-10-10 00:05 ET  [ian]
done: automitigate/learners.py (6 learners + fixed policies + replay episode, tests incl. 13), scripts/analysis.py (headline, learners, best-arm, proxy, drivers, sensitivity, pareto, figures, results-md, all; 80 s on 5 circuits). First look at seed pass 0 (one seed, so no SE yet): static oracle = arm 5 (ZNE+REM) on every circuit, drift value 0.1–0.7 %, many raw argmax flips (shot noise). Real numbers come with more passes. The Mac queue now runs Q3 after every pass and regenerates docs/results.md and figures/.
blocked: none
next: automitigate/forward.py + sweep --forward (Q2b), qollab/spot_check (single-circuit runs), web/.
needs-other-side: none.

## 2026-10-09 23:32 ET  [thomas]
done: Q2_seed1 finished in 12 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-09 23:43 ET  [thomas]
done: Q2_seed2 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-09 23:50 ET  [ian]
done: chains record is per laptop since 494cd98 (`data/calib/chains_<laptop>.json`; analysis merges them), so the chains.json conflict cannot recur. Pushed since the last block: forward.py + `sweep --forward` (Q2b now runnable after the Yoga's pass 5), spot check as 8 single-circuit Qollab runs (`qollab/spot_check_single.py` + `scripts/spot_compare.py`), replay tables (`data/replay/`), the Qollab demo `main.py` (Run-settings form; replay needs no backend), `scripts/build_qollab_project.py` (-> qollab_project.zip for Sunday's upload), `docs/project_card.md` draft, `docs/video_script.md`. Both queues healthy: Mac on Q1b (ETA ~02:30) then seeds 1-19; Yoga 3 passes done at 11-12 min each.
blocked: none
next: wait for passes; Sat: README numbers from docs/results.md, related-work re-check, final figures.
needs-other-side: Thomas, Sat ~11:00: the 7 E0 runs (qollab/e0_single.py) and 8 spot-check runs (qollab/spot_check_single.py), then `commit the Qollab runs`. Nothing before then.
## 2026-10-09 23:54 ET  [thomas]
done: Q2_seed3 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 00:06 ET  [thomas]
done: Q2_seed4 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 00:17 ET  [thomas]
done: Q2_seed5 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 01:15 ET  [thomas]
done: Q2b finished in 58 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 01:26 ET  [thomas]
done: Q2_seed6 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 01:37 ET  [thomas]
done: Q2_seed7 finished in 11 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 01:45 ET  [ian]
done: Q1b finished in 142 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 01:46 ET  [ian]
done: Q3_after0 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 01:48 ET  [thomas]
done: Q2_seed8 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 01:58 ET  [ian]
done: Q2_seed1 finished in 12 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 01:59 ET  [ian]
done: Q3_after1 finished in 1 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 01:59 ET  [thomas]
done: Q2_seed9 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 02:10 ET  [thomas]
done: Q2_seed10 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 02:12 ET  [ian]
done: Q2_seed2 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 02:14 ET  [ian]
done: Q3_after2 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 02:14 ET  [ian]
done: Q4 finished in 0 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 02:27 ET  [ian]
done: Q2_seed3 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 02:28 ET  [ian]
done: Q3_after3 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 02:41 ET  [ian]
done: Q2_seed4 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 02:42 ET  [ian]
done: Q3_after4 finished in 1 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 02:48 ET  [thomas]
done: Q6a finished in 37 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 02:55 ET  [thomas]
done: Q6b finished in 7 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 02:56 ET  [ian]
done: Q2_seed5 finished in 14 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 02:57 ET  [ian]
done: Q3_after5 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none
