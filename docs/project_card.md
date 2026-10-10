# AutoMitigate

<!-- Project card for Qollab (Thomas owns the wording; numbers come from docs/results.md).
     Required sections per the hackathon rules: pitch, problem, how it works, how to run,
     results, what is new, limitations, disclosure, accessibility. -->

**A bandit that learns which error-mitigation settings to use for your circuit, and notices when the device changes.**

## The problem

Quantum computers return slightly wrong answers because the hardware is noisy. A handful of software tricks clean the answers up: run the circuit at deliberately higher noise and extrapolate back to zero (ZNE), wrap two-qubit gates in random Pauli flips so coherent errors average out (Pauli twirling), or undo the measurement's own bias with a calibration matrix (readout-error mitigation). Each helps on some circuits and hurts on others, costs extra circuits, and there is no rule for which combination to use. Worse, the hardware's error rates drift hour to hour and reset at every recalibration, so a setting chosen on Monday may be the wrong one on Thursday.

AutoMitigate treats the choice as a multi-armed bandit, the algorithm behind A/B testing: each arm is one combination of the three tricks, it tries one, scores the result, updates its belief and tries again. The score comes from a randomised mirror circuit, a twin that applies the gates and then undoes them with a random Pauli layer in the middle, so the correct answer is a known bitstring and no ideal simulation is needed. On top of the tool we ran the experiment the question deserves: on a real device's nine-month calibration log, does the best setting actually change?

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

Reward = P(target bitstring) of the randomised mirror circuit, averaged over twirl copies, extrapolated 1x/3x/5x to zero noise for ZNE arms, corrected by the assignment matrix for REM arms; every arm spends the same 1,200 shots per pull. Learners: ε-greedy, UCB1, Thompson sampling, and three non-stationary variants (discounted, sliding-window and change-detection Thompson), always plotted against four fixed policies: nothing, everything on, the best fixed arm in hindsight and the per-day oracle.

Two data sources, both simulated locally with Qiskit Aer: (1) a per-day noise model rebuilt from nine months of real ibm_fez calibration data (T1, T2, gate errors, readout, 240 daily snapshots), the headline; (2) an IonQ-like model (depolarising constants near IonQ's published Aria-1 figures, spot-checked against Qollab's Aria-1 simulator) with a synthetic drift schedule (stable, slow, jump), the demo's first source.

## How to run it

Press **Run** with no backend selected: the form under Run settings picks the circuit (ghz4, qft3, grover3, ghz8, qaoa6), the source (ibm or ionq), the drift schedule and the learner; the replay uses the committed reward tables and finishes in a few seconds, showing the regret chart, the arm-switch strip and a recommendation with a Qiskit snippet. With an IonQ backend selected and `live = True`, the recommended setting is also run once on that backend (Qollab allows one circuit per run).

To reproduce the tables: `pip install -e ".[sweep,dev]"`, `pytest -q`, then `python scripts/run_queue.py --laptop ian --dry-run` lists every sweep stage; `docs/analysis_plan.md` has the pre-registered definitions.

## Results

<!-- paste the first paragraph(s) of docs/results.md here, then one sentence each on: regret chart, arm-switch strip, per-day proxy validation. -->

## What is new

- arXiv 2608.06426 (CMAB-ZNE): a contextual bandit over ZNE fold sets only; ours spans three real techniques with self-implemented arms.
- arXiv 2604.24551 (GSC-QEMit): arms are simulator knobs; ours are the mitigation techniques themselves.
- arXiv 2610.01253 (APGEM): the reward needs the ideal answer; our mirror-circuit reward does not.
- None of them tests non-stationary learners under real device drift. We do, on nine months of real calibration data, with a pre-registered analysis. No quantum-advantage claim is made.

## Limitations

Everything is simulation: the drift replay is a noise model rebuilt from calibration data, not the device itself; the model is Markovian with no crosstalk or leakage; the coherent fraction of the two-qubit error is assumed (0 primary, 0.3 sensitivity), and under coherent error the mirror score partially echoes the error and flatters the non-twirled arms; one device, one chain per circuit size; the mirror reward is a proxy for the user's observable, quantified per day by the proxy validation; the IonQ-side drift is synthetic; Qollab's IonQ simulator is itself a model, and its compiler cancels mirror and folded structure (an identity chain of 40 gates comes back at P = 1.0), so neither ZNE nor mirror scoring can be run through Qollab's IonQ backends as submitted; the IonQ-like constants are therefore defaults near IonQ's published Aria-1 figures, and the spot check agrees with Qollab's simulator only on cells where injected errors survive compilation (within 0.01), not on clean mirror cells (Qollab 1.0 vs local 0.95). Full list in `docs/analysis_plan.md`.

## Disclosure

This effort is supported by Qollab & IonQ. AI coding assistants were used during development; the plan, the empty repository skeleton (packaging, CI, README template) and the explainer diagrams were prepared before the window and are the only pre-window material. Aer sweeps ran locally on two laptops; the IBM calibration data is `phanerozoic/qiskit-calibration-drift` (CC-BY-4.0, revision 56f55fb8; its CC-BY-NC `SN` column was never loaded); IonQ-simulator runs on Qollab are listed with job IDs in `data/e0.json` and `data/ionq/spot_check.json`. Libraries: Qiskit, Qiskit Aer, NumPy, SciPy, pandas, Matplotlib, scikit-learn.

## Accessibility

Labelled form controls (Run settings), keyboard-navigable, figures use line styles and labels rather than colour alone, and every number in the figures is also printed as text.
