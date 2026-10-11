# AutoMitigate

Demo video: https://www.youtube.com/watch?v=gv-lP-Qzrl8 · Code: https://github.com/I-ala-Wilson/automitigate · Qollab project: https://qollab.xyz/u/S0cra13s/quantum-automitigation

**A bandit that learns which error-mitigation settings to use for your circuit, and notices when the device changes.**

## The problem

Quantum computers return slightly wrong answers because the hardware is noisy. A handful of software tricks clean the answers up. You can run the circuit at deliberately higher noise and extrapolate back to zero (ZNE), wrap two-qubit gates in random Pauli flips so coherent errors average out (Pauli twirling), or undo the measurement's own bias with a calibration matrix (readout-error mitigation). Each helps on some circuits and hurts on others, costs extra circuits, and there is no rule for which combination to use. Worse, the hardware's error rates drift from day to day and reset at every recalibration, so a setting chosen on Monday may be the wrong one on Thursday.

AutoMitigate treats the choice as a multi-armed bandit, the algorithm behind A/B testing. Each arm is one combination of the three tricks, it tries one, scores the result, updates its belief and tries again. The score comes from a randomised mirror circuit, a twin that applies the gates and then undoes them with a random Pauli layer in the middle, so the correct answer is a known bitstring and no ideal simulation is needed. On top of the tool we ran the experiment the question deserves: on a real device's eight-month calibration log, does the best setting actually change?

## How it works

| arm | ZNE | twirl | REM | circuits per pull |
|---|---|---|---|---|
| 0 | | | | 1 |
| 1 | | | x | 1 (+2 calibration) |
| 2 | | x | | 8 |
| 3 | | x | x | 8 (+2) |
| 4 | x | | | 3 |
| 5 | x | | x | 3 (+2) |
| 6 | x | x | | 24 |
| 7 | x | x | x | 24 (+2) |

Reward = P(target bitstring) of the randomised mirror circuit, averaged over twirl copies, extrapolated 1x/3x/5x to zero noise for ZNE arms, corrected by the assignment matrix for REM arms; every arm spends the same 1,200 shots per pull. Learners: ε-greedy, UCB1, Thompson sampling, and three non-stationary variants (discounted, sliding-window and change-detection Thompson), always plotted against four fixed policies, which are nothing, everything on, the best fixed arm in hindsight and the per-day oracle.

Two data sources, both simulated locally with Qiskit Aer: (1) a per-day noise model rebuilt from eight months of real ibm_fez calibration data (T1, T2, gate errors, readout, 240 daily snapshots), the headline and the demo's default source; (2) an IonQ-like model (depolarising constants at IonQ's published Aria-1 figures, spot-checked against Qollab's Aria-1 simulator) with a synthetic drift schedule (stable, slow, jump), the demo's second source.

## How to run it

Press **Run** and keep the built-in simulator. The form under Run settings picks the circuit (ghz4, qft3, grover3, ghz8, qaoa6), the source (ibm or ionq), the drift schedule and the learner; the replay uses the committed reward tables and finishes in a few seconds, showing the regret chart, the arm-switch strip and a recommendation with a Qiskit snippet. With `live = True` the chosen circuit is also executed on the selected backend, raw and with readout mitigation from two calibration circuits in the same job; pick an IBM noise-model simulator to see the noise (IonQ backends accept one circuit per job, so there only the raw run is made).

To reproduce the tables: `pip install -e ".[sweep,dev]"`, `pytest -q`, then `python scripts/run_queue.py --laptop ian --dry-run` lists every sweep stage; `docs/analysis_plan.md` has the pre-registered definitions.

## Results

We pre-registered the analysis before the data existed, then replayed 240 daily snapshots of real ibm_fez calibration data (1 February to 9 October 2026) with 20 seeds. On the best chain the best fixed setting was the same on all five circuits, and the per-day best arm left it on only three of 1200 circuit-days. The drift value, which is what a perfect per-day tracker gains over the best fixed setting, is at most 0.01 % of the static oracle (ghz4 0.00, ghz8 0.00, grover3 0.01 with 2 significant switches, qaoa6 0.00, qft3 0.00 with 1 significant switch). ZNE + readout mitigation (arm 5) is the best fixed setting every time. A setting chosen once is as good as tracking; the bandit's job is to find it cheaply. ε-greedy does, with dynamic pseudo-regret of 1.60 / 3.26 / 3.08 / 3.19 / 2.16 (ghz4 / ghz8 / grover3 / qaoa6 / qft3) against 4.46 / 11.47 / 14.87 / 13.73 / 3.96 for the everything-on default, 45 to 79 % lower, with 95 % intervals in `docs/results.md`. The Thompson family sits between the two, UCB1 is worst. On the median-ranked chain the best setting did move, drift value 0.37 % with 9 significant switches on ghz4, so tracking matters where the hardware is worse.

- **Regret chart** (`figures/regret_*.png`, and the top panel of every Run): cumulative pseudo-regret against the per-day oracle for the learner, plain Thompson, the everything-on default and the best fixed arm; the learner's curve flattens once it locks onto arm 5.
- **Arm-choice strip** (`figures/best_arm_*.png`, bottom panel of every Run): the arm chosen each day over the per-day best arm; one forced pass over all eight arms, then arm 5 with the 10 % exploration dots.
- **Per-day proxy validation** (`figures/proxy_per_day.png`): the mirror score's ranking of the eight arms agrees with the real forward error at a median Spearman correlation of 0.88 / 0.93 / 0.62 (ghz4 / grover3 / qft3), and the arm it picks costs about 8 % of the worst arm's forward error at most, so the tool works without ever knowing the circuit's answer.
- **IonQ-like source**: on ghz4 the everything-on arm stays best on both sides of the jump, so that replay shows the cost of exploration when there is nothing to track; the local model agrees with Qollab's Aria-1 simulator to mean |ΔP| = 0.027 on 8 identical single circuits.

## What is new

- arXiv 2608.06426 (CMAB-ZNE): a contextual bandit over ZNE fold sets only; ours spans three real techniques with self-implemented arms.
- arXiv 2604.24551 (GSC-QEMit): arms are simulator knobs; ours are the mitigation techniques themselves.
- arXiv 2610.01253 (APGEM): the reward needs the ideal answer; our mirror-circuit reward does not.
- None of them tests non-stationary learners under real device drift. We do, on eight months of real calibration data, with a pre-registered analysis. No quantum-advantage claim is made.

## Limitations

Everything is simulation. The drift replay is a noise model rebuilt from calibration data, not the device itself; the model is Markovian with no crosstalk or leakage; the coherent fraction of the two-qubit error is assumed (0 primary, 0.3 sensitivity), and under coherent error the mirror score partially echoes the error and flatters the non-twirled arms; one device, one chain per circuit size; the mirror reward is a proxy for the user's observable, quantified per day by the proxy validation; the IonQ-side drift is synthetic; Qollab's IonQ simulator is itself a model, and its compiler cancels mirror and folded structure (an identity chain of 40 gates comes back at P = 1.0), so neither ZNE nor mirror scoring can be run through Qollab's IonQ backends as submitted; the IonQ-like constants are therefore defaults near IonQ's published Aria-1 figures, and the spot check against Qollab's simulator (mean |ΔP| = 0.027 over 8 identical circuits) is informative only on cells where injected errors survive compilation. Full list in `docs/analysis_plan.md`.

## Disclosure

This effort is supported by Qollab & IonQ. AI coding assistants were used during development; the plan and the empty repository skeleton (packaging, CI, README template) were prepared before the window and are the only pre-window material. Aer sweeps ran locally on two laptops; the IBM calibration data is `phanerozoic/qiskit-calibration-drift` (CC-BY-4.0, revision 56f55fb8; its CC-BY-NC `SN` column was never loaded); IonQ-simulator runs on Qollab are listed with job IDs in `data/ionq/spot_check.json` and `data/e0_runs.jsonl`. Libraries: Qiskit, Qiskit Aer, NumPy, SciPy, pandas, Matplotlib, scikit-learn.

## Accessibility

Labelled form controls (Run settings), keyboard-navigable, figures use line styles and labels rather than colour alone, and every number in the figures is also printed as text.
