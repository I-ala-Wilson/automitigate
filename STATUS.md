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

## 2026-10-10 03:06 ET  [thomas]
done: Q2_seed11 finished in 11 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 03:11 ET  [ian]
done: Q2_seed6 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 03:12 ET  [ian]
done: Q3_after6 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 03:17 ET  [thomas]
done: Q2_seed12 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 03:25 ET  [ian]
done: Q2_seed7 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 03:26 ET  [ian]
done: Q3_after7 finished in 1 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 03:28 ET  [thomas]
done: Q2_seed13 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 03:39 ET  [ian]
done: Q2_seed8 finished in 13 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 03:39 ET  [thomas]
done: Q2_seed14 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 03:40 ET  [ian]
done: Q3_after8 finished in 1 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 03:50 ET  [thomas]
done: Q2_seed15 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 03:54 ET  [ian]
done: Q2_seed9 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 03:55 ET  [ian]
done: Q3_after9 finished in 1 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 04:01 ET  [thomas]
done: Q2_seed16 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 04:08 ET  [ian]
done: Q2_seed10 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 04:09 ET  [ian]
done: Q3_after10 finished in 1 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 04:12 ET  [thomas]
done: Q2_seed17 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 04:23 ET  [ian]
done: Q2_seed11 finished in 13 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 04:24 ET  [thomas]
done: Q2_seed18 finished in 11 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 04:24 ET  [ian]
done: Q3_after11 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 04:35 ET  [thomas]
done: Q2_seed19 finished in 11 min (ladder: max_seeds=20, rungs=none)
## 2026-10-10 04:37 ET  [ian]
done: Q2_seed12 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 04:38 ET  [ian]
done: Q3_after12 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 04:52 ET  [ian]
done: Q2_seed13 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 04:53 ET  [ian]
done: Q3_after13 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 05:07 ET  [ian]
done: Q2_seed14 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 05:08 ET  [ian]
done: Q3_after14 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 05:21 ET  [ian]
done: Q2_seed15 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 05:23 ET  [ian]
done: Q3_after15 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 05:36 ET  [ian]
done: Q2_seed16 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 05:37 ET  [ian]
done: Q3_after16 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 05:50 ET  [ian]
done: Q2_seed17 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 05:52 ET  [ian]
done: Q3_after17 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 06:05 ET  [ian]
done: Q2_seed18 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 06:06 ET  [ian]
done: Q3_after18 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 06:19 ET  [ian]
done: Q2_seed19 finished in 13 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 06:21 ET  [ian]
done: Q3_after19 finished in 1 min (ladder: max_seeds=20, rungs=none)
blocked: none
next: next runnable stage
needs-other-side: none

## 2026-10-10 10:53 ET  [thomas]
done: spot check on Qollab IonQ Aria 1 simulator, qollab/spot_check_single.py RUN = 1..8, 8/8 succeeded, lines in data/ionq/spot_runs.jsonl (job IDs included).
blocked: E0 runs (qollab/e0_single.py) RUN = 1 failed twice: IonQJobFailureError "TooManyShots" (jobs 01a12646-4fae-7528-b653-70b207854647, 01a12647-6e2d-7576-a462-861bd0e6d0a5). SHOTS = 5000 is above the simulator's limit; the spot check at 1200 shots works. RUN = 2..7 not attempted since every run uses the same SHOTS; data/e0_runs.jsonl not created.
note: qft3 spot scores are low on 3 of 4 runs (0.024, 0.46, 0.0125; 0.926 on run 8) with counts piled on non-target bitstrings (e.g. run 5: 100 and 111 vs target 000). ghz4 runs score 0.92-1.0. Looks like the qft3 twin's target or bit order on IonQ, not noise.
needs-other-side: Ian: lower SHOTS in e0_single.py (1200 works) and check qft3 targets; then E0 can be re-run.
## 2026-10-10 11:05 ET  [ian]
done: spot check compared (scripts/spot_compare.py -> data/ionq/spot_check.json): on the 8 identical circuits the local IonQ-like model matches Qollab's Aria-1 simulator to mean |dP| = 0.027 (max 0.088); the line is in docs/results.md. The low qft3 scores (0.02, 0.46, 0.01) are the designed drift: setting A injects a random Pauli after each cz with probability 0.03, and on those two twin seeds a Pauli fired, flipping the outcome; the local simulation of the same circuit gives the same 0.02, so target and bit order are right. E0: qollab/e0_single.py now uses 1200 shots (IonQ rejects 5000).
blocked: none
next: fit the IonQ constants once the 7 E0 lines land (scripts/fit_e0.py), then decide whether to rerun the IonQ-like table with them.
needs-other-side: Thomas: `git pull`, then qollab/e0_single.py RUN = 1..7 as before, lines into data/e0_runs.jsonl, commit `[thomas] e0 runs`, push.

## 2026-10-10 11:06 ET  [thomas]
done: E0 on Qollab IonQ Aria 1 simulator, qollab/e0_single.py RUN = 1..7 at 1200 shots, 7/7 succeeded, lines in data/e0_runs.jsonl.
note: every E0 run has p_target = 1.0 with all 1200 shots on the target, including fold3_ghz4 (18 two-qubit gates) and chain2q_d20 (40 two-qubit gates). Either the noise model is not applied to these circuits or IonQ's compiler cancels the identity chains/folds before simulation, so the depolarising fits will come out ~0. The spot check (drift gates injected) does show noise.
needs-other-side: Ian: check fit_e0.py output before using p1q/p2q; consider non-identity depth circuits.
## 2026-10-10 11:30 ET  [ian]
done: E0 lines received, but all seven score exactly 1.0 (even the 40-gate chains), so they were run on an ideal backend, not the Aria-1 noise-model simulator (the spot check an hour earlier was noisy: ghz4 0.92-1.0). scripts/fit_e0.py now refuses all-1.0 runs; data/e0.json unchanged (defaults). qollab/e0_single.py and spot_check_single.py now record the backend name and noise_model in each line. Nothing downstream depends on E0: the IonQ-like table stays on the defaults, validated by the spot check (mean |dP| 0.027). Video script and the demo bundle (qollab_project.zip, 53 files) are pushed.
blocked: none
next: video tonight; Sunday 09:00 final regenerate by hand.
needs-other-side: Thomas (1) optional, 10 min: in Select QPU pick the IonQ **Aria-1** entry with the noise model (same one used for the spot check), `git pull`, delete data/e0_runs.jsonl, rerun qollab/e0_single.py RUN 1-7; run 6 must print P(target) well below 1. (2) needed today, 10 min: `git pull`, download qollab_project.zip from the repo, drag it into the project's file tree on Qollab (choose unpack), no QPU selected, press Run, confirm the chart appears, do not Publish; text Ian "demo renders".

## 2026-10-10 17:55 ET  [ian]
done: Thomas's reading is right: E0 ran on the Aria-1 noise model and the 1.0s are IonQ's compiler cancelling the identity chains (and the folded twin). Consequences recorded in docs/analysis_plan.md (typo log, threat 10) and docs/project_card.md (Limitations): no fitted IonQ constants (defaults kept), spot check informative only on cells with surviving injected errors, ZNE-by-folding not executable through Qollab's IonQ backends. No further E0 attempts. Demo default learner switched to eps-greedy (the winner on every circuit); qollab_project.zip rebuilt.
blocked: none
next: video tonight on a scratch project under Ian's account (so the draft needn't be published); Sunday 09:00 final regenerate + zip; Thomas re-uploads the final zip Sunday 14:30 before Publish.
needs-other-side: Thomas: README tonight (paste docs/results.md under "The headline result", write the rest), project card from docs/project_card.md.

## 2026-10-10 18:20 ET  [ian]
done: E0 v3 = qollab/e0_ladder.py, 4 Runs the compiler cannot cancel (4-qubit CX ladder, consecutive gates on different pairs, an X after every CX, basis-state walk with a known outcome); scripts/fit_e0.py fits p2 and readout from it (tested on a fake noisy backend: recovers p2 to ~20 %). Thomas's E0 files from today are left as they are (the fitter ignores identity-chain runs that score 1.0).
blocked: none
next: video tonight; Sunday 09:00 final regenerate; if the ladder runs land by 11:30 Sunday, refit, rerun the IonQ-like table (2.5 h), re-export, re-zip before the 14:00 freeze.
needs-other-side: Thomas, Sunday morning, 10 min, optional but worth it: `git pull`, delete data/e0_runs.jsonl, on the IonQ Aria-1 noise-model simulator run qollab/e0_ladder.py with RUN = 1, 2, 3, 4 (one circuit each), append the four printed lines to data/e0_runs.jsonl, commit `[thomas] e0 ladder runs`, push. Run 4 should print P(target) clearly below 1.

## 2026-10-10 20:50 ET  [ian]
done: probe on Qollab's IBM Fez noise-model simulator (throwaway draft project, never published): list jobs accepted (12 circuits in one job, ~8 s); real gate noise (144-CX ladder decays 0.97 -> 0.89); but an identity CX chain stays at P = 0.98 at any depth, with or without barriers, so the compiler cancels inverse structure there too (threat 10 now covers all Qollab backends). Consequence: the "paste your circuit, measure all 8 arms" idea is not viable (ZNE folds and the mirror twin are compiled away). Demo live step rewritten instead: main.py `live_run` executes the chosen circuit forward on the selected backend plus the two readout-calibration circuits in one job and prints raw vs readout-mitigated vs ideal (IonQ backends: raw only, says so). forward.py added to the Qollab bundle; project card, video script shot 3 and analysis_plan typo log updated. 37 tests pass.
blocked: none
next: upload the rebuilt zip to the scratch project, verify on Built-in and on IBM Fez (time it); Ian re-records the two Qollab clips with IBM -> Fez selected; Sunday 09:00 final regenerate + zip.
needs-other-side: Thomas: README and project card still untouched as of 20:50; Sunday 14:30 re-upload uses the zip built after this commit.

## 2026-10-10 21:40 ET  [ian]
done: README written in full (headline table from docs/results.md, how it works, Qollab + local run instructions incl. the new live run, threats 1–10, replication commands, extend-it, disclosures, related work). Thomas: review and edit, do not start from the template.
blocked: none
next: Ian records the two Qollab clips (IBM Fez selected) and cuts the video; Sunday 09:00 final regenerate + zip; video and project links go into the README placeholders at the top.
needs-other-side: Thomas: README review + Qollab project card (paste docs/project_card.md); Sunday schedule unchanged.

## 2026-10-10 23:10 ET  [ian]
done: E0 v3 ladder runs done from Ian's account (probe draft project, IonQ Aria-1 noise-model simulator, 1200 shots): ro0000 P = 1.0, ro1111 P = 0.9975, ladder 12 CX P = 1.0, ladder 36 CX P = 1.0 (data/e0_runs.jsonl, job IDs inside). The simulator applies no visible two-qubit error to a 4-qubit Clifford ladder, so no p2 fit is possible; IonQ-like constants stay at defaults, IonQ-like table NOT rerun (decision closed). Readout from ro1111: ~6e-4 per-qubit flip for |1>, 0 for |0>. e0_ladder.py's RUN is now a Run-settings field. Fresh-clone check done tonight: new venv, pip install -e ".[sweep,dev]", 37 tests pass, replay runs. README threat 10 and disclosure updated.
blocked: none
next: Ian's video; Sunday 09:00 final regenerate + zip (no table changes expected); Thomas Sunday: README review, card, 14:30 upload, 16:00 Publish, 17:00 Submit. Thomas's optional 11:00 ladder runs and 12:00 fresh-clone check are no longer needed.
needs-other-side: Thomas: README review + project card tonight.
