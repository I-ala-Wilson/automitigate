# AutoMitigate

*A bandit that auto-tunes quantum error-mitigation settings per circuit, per machine, per hour, using a mirror-circuit reward that needs no ideal answer.*

Built for the Qollab + IonQ Global Quantum Hackathon, Oct 9–11 2026. MIT licensed.

> README owner: Thomas. Fill every section below before Sunday 14:00 ET. Judges weight Documentation Quality equally with the code. "The headline result" is pasted from `docs/results.md`, which the sweep pipeline regenerates after every pass.

## What it does

<!-- 3–5 sentences. The problem (choosing mitigation is machine- and time-dependent; nobody can diagnose fast enough), the tool (8 arms = ZNE × twirl × readout mitigation, 6 learners, randomised mirror-circuit reward), the headline result from the real-drift replay. -->

## The headline result

<!-- Paste docs/results.md here verbatim. Its first sentence is the pre-registered headline: the drift value (what a perfect tracker gains over the best fixed setting, % of the static oracle) and the number of significant best-arm switches (margin > 2·SE over the seeds) over N daily snapshots of real ibm_fez calibration data, then which learner captured how much of it against the everything-on default. Includes CIs. If there is no significant switch, that sentence is the one written for that case in docs/analysis_plan.md. -->

## How it works

<!-- Arms table (8 rows: zne, twirl, rem, circuits per pull). Reward definition (randomised mirror circuit with a random Pauli layer; cite Proctor et al.). Learners and the four fixed baselines. Link diagrams in docs/diagrams/. -->

## Run it

### On Qollab (what the judges do)
<!-- Link to the published project. Replay mode needs no backend. Live mode: Select QPU → IonQ Aria-1. -->

### Locally
```bash
git clone https://github.com/<ian>/automitigate && cd automitigate
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: py -3.12 -m venv .venv && .venv\Scripts\activate
python -m pip install --upgrade pip                      # pip < 23 cannot do editable installs
pip install -e ".[sweep,dev]"
pytest -q
```

## Analysis plan and threats to validity

<!-- Link docs/analysis_plan.md (committed before any drift data existed) and copy its threats-to-validity list here: simulation not hardware; Markovian noise model, no crosstalk or leakage; coherent fraction assumed (primary f = 0, sensitivity f = 0.3); one device, one qubit chain (median-chain sensitivity reported); mirror proxy is not the user's observable (per-day agreement reported); synthetic drift on the IonQ-like source; IonQ simulator accuracy caveats. -->

## Replicate the tables

<!-- scripts/fetch_calibration.py (dataset revision pinned) → scripts/sweep.py (args, runtime per laptop, seeds) → scripts/analysis.py. State the exact drift constants and the fitted IonQ-like depolarising constants (data/e0.json), and the spot-check job IDs file. -->

## Extend it

<!-- How to add an arm (dict in ARMS + branch in apply_arm), a learner (class with select/update/reset), a circuit (function in circuits.py), a backend (anything with .run). -->

## Data and disclosures

- Drift study: IBM calibration time series `phanerozoic/qiskit-calibration-drift` (ibm_fez, Jan 31 → Oct 9 2026, 241 observed days, CC-BY-4.0; revision pinned in `scripts/fetch_calibration.py`; the CC-BY-NC `SN` column is never loaded), replayed through Qiskit Aer noise models rebuilt per day by last-value-carried-forward. Aer sweeps ran locally on two laptops.
- IonQ-like table: Qiskit Aer with depolarising constants fitted from Qollab's free IonQ Aria-1 simulator (`data/e0.json`), spot-checked against that simulator (`data/ionq/spot_check.json`, job IDs inside). Drift there is synthetic (injected Pauli rate, RZZ over-rotation and readout flips on a schedule); constants listed above.
- The IonQ simulator is a static depolarising model with no readout or idle noise; IonQ gives no accuracy guarantee for it.
- Built in the hackathon window. Planning documents and this skeleton were prepared before the window opened.

## Related work

<!-- CMAB-ZNE 2608.06426, GSC-QEMit 2604.24551, APGEM 2610.01253, Mitiq Calibrator, randomised mirror circuits (Proctor et al. 2008.11294, 2112.09853), non-stationary bandits (Garivier & Moulines 2011; Raj & Kalyani 2017; Trovò et al. 2020; Cao et al. 2019), TuniQ 2605.11375 (real calibration windows), 2609.38713 (ZNE hurts 80–88%), 2507.01195 (raw fidelity stationary). One line each on how ours differs. -->

## Team

Ian Wilson (McGill) and Thomas Sebahi (McGill).
