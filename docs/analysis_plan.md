# Analysis plan (pre-registered)

Committed 2026-10-09 ~23:00 ET, before the first IBM-drift reward row existed. After this
commit the file is only edited for typos, each with a dated note at the bottom. Everything
below was decided before seeing any drift result; the README reports what the data then said.

## 1. The question

On a real device whose calibration drifts, does the best combination of error-mitigation
settings for a given circuit change over time, and if so, can a non-stationary bandit track it
better than a fixed choice?

## 2. Primary unit of analysis

- **Device and data:** ibm_fez calibration log (HF `phanerozoic/qiskit-calibration-drift`,
  revision `56f55fb8`, CC-BY-4.0). One **daily snapshot** per observed day: the latest value of
  each property observed on or before the end of that UTC day (last value carried forward).
  241 observed days, 2026-01-31 to 2026-10-09. The first day lacks gate-length values and is
  skipped; days where any chain qubit or edge is at the failure ceiling or missing are skipped and
  listed in `data/ibm/skipped_*.json`. The time axis is never subsampled.
- **Noise model per day (Aer, density-matrix method):** thermal relaxation from T1, T2 and the
  reported sx, x, cz and readout durations; depolarising on sx, x and cz sized so the average gate
  infidelity equals the reported error after relaxation; asymmetric readout from
  `prob_meas1_prep0` / `prob_meas0_prep1`. Primary coherent fraction **f = 0** (every cz error
  stochastic). `rz` is noiseless.
- **Chain:** one fixed linear chain per circuit size, chosen once on the first complete day as the
  path with the lowest mean cz error (`rank 0`), reused for every day. Chains are recorded in
  `data/calib/chains.json`.
- **Circuits:** ghz4, qft3 (QFT of |101>), grover3 (2 iterations, marked |101>), qaoa6
  (one-layer MaxCut on the 6-ring, fixed angles), ghz8. Transpiled once at optimisation level 1
  to {sx, rz, x, cz} on the chain; never re-optimised afterwards.
- **Arms (8):** ZNE {off, on} x Pauli twirl {off, on} x readout mitigation (REM) {off, on};
  arm 0 = nothing, arm 7 = everything on (the practitioner's default). Opt level is fixed at 1.
- **Reward (mirror score):** randomised mirror circuit U · Q · Ũ⁻¹ with a random Pauli layer Q
  and a Pauli-frame-corrected inverse, so the ideal output is a known bitstring. Score =
  P(target), averaged over the 8 twirl copies, extrapolated 1x/3x/5x -> 0x by a **linear** fit
  for ZNE arms (clipped to [0, 1], clips flagged), corrected by tensored assignment-matrix
  inversion for REM arms. Equal budget of **1200 shots per pull** for every arm
  (1200 / 400 / 150 / 50 shots per circuit for the 1 / 3 / 8 / 24-circuit shapes).
  Polarisation (p − 2⁻ⁿ)/(1 − 2⁻ⁿ) is reported next to p.
- **Seeds:** 20 seed passes; seed k fixes the twin's Pauli layer and twirl draws per circuit and
  the simulator seed per (day, circuit). The eight arms of a cell share the same Q.

## 3. Headline quantities (computed by `scripts/analysis.py headline`)

Per circuit, with r̄_t(a) the seed-mean reward of arm a on day t and SE its standard error:

1. **Static oracle** a*_static = argmax_a Σ_t r̄_t(a). **Dynamic oracle** = max_a r̄_t(a) per day.
2. **Drift value** = Σ_t [max_a r̄_t(a) − r̄_t(a*_static)] expressed as a percentage of the
   static oracle's cumulative score Σ_t r̄_t(a*_static). Learner-independent. This is the first
   headline number.
3. **Significant best-arm switch**: day t where argmax_a r̄_t(a) differs from the previous
   day's argmax **and** the new best exceeds the old best by more than 2·SE (SE of the difference
   over seeds). Raw argmax changes are reported as a secondary line. The **ambiguous-day
   fraction** = share of days where the top two arms are within 2·SE. Epoch lengths = days between
   significant switches. This is the second headline number.
4. **Learners** (dynamic pseudo-regret vs the seed-mean dynamic oracle, one pull per day,
   replayed 200 times from the stored samples; CIs from the replay spread): ε-greedy (0.1), UCB1,
   Thompson (Bernoulli trick), Discounted TS (γ), Sliding-Window TS (window), Change-Detection TS
   (M-UCB detector). Fixed policies on the same plot: arm 0, arm 7, static oracle, dynamic oracle.
   Hyperparameters γ ∈ {0.8, 0.9, 0.95, 0.99}, window ∈ {10, 20, 40} are **chosen on seeds 0–9 and
   reported on seeds 10–19**. Secondary: 4 pulls per day on disjoint seeds.
5. **Proxy validation per day** (`proxy`, Q2b): for ghz4, qft3, grover3 and each day, the same
   8 arms applied to the forward circuit with a known observable (ghz: ⟨Z⊗n⟩; grover3: P(marked);
   qft3: the Pauli with the largest ideal expectation). Reported: top-1 agreement rate (mirror
   best arm = forward best arm), Spearman correlation across the 8 arms, and the forward regret of
   the mirror-chosen arm as a percentage of the worst arm's. Per-day numbers are the claim; the
   pooled scatter is drawn but not quoted.
6. **Drivers** (`drivers`): best arm vs mean 2q error, readout error, T1, T2 of the chain per day
   (multinomial logistic fit) and whether significant switches cluster within one day of a
   chip-wide recalibration event (83 such days).

## 4. Headline sentence per outcome (one of these goes into the README verbatim with numbers)

- **Switches found:** "Over N daily snapshots of real ibm_fez calibration data, a perfect tracker
  would have gained X % over the best fixed setting; the best setting changed significantly K
  times (M epochs, median length L days). <Learner> captured Y % of that gain at a dynamic
  pseudo-regret of R ± C, against R₇ ± C₇ for the everything-on default."
- **No significant switch:** "Over N daily snapshots the best mitigation setting for <circuit>
  was stationary: the drift value is X % (a fixed setting chosen once is within X % of a perfect
  tracker), with K raw argmax flips and an ambiguous-day fraction of A. The learner comparison
  then measures only the cost of exploration: ..."
- **Mixed (some circuits switch, some do not):** both sentences, per circuit, and the drift value
  per circuit in one table.

## 5. Sensitivities (each reported as one line next to the primary; never replaces it)

- Coherent fraction f = 0.3 (ghz4, qft3, seeds 0–9).
- Exponential instead of linear ZNE, recomputed offline from the stored per-scale scores
  (`aux.by_scale`); rows where the exponential fit falls back to linear are counted.
- Median-ranked chain instead of the best chain (ghz4, seeds 0–4).
- Shot budget 600 / 1200 / 2400 on the static model (Q4, Pareto figure only; cost is not in the
  headline because every arm spends the same shots).
- 4 pulls per snapshot (learner table only).

## 6. Source 1 (IonQ-like model, the demo's first data source)

Depolarising after every 1q / 2q gate plus a symmetric readout flip, constants p1, p2, r fitted
from Qollab's Aria-1 simulator by `qollab/e0_checks.py` when available (the `model` field of every
row records the constants actually used; defaults are p1 = 5e-4, p2 = 6e-3, r = 4e-3). Synthetic
drift: extra per-cz Pauli probability p, cz over-rotation θ (as an over-rotated cz, still one
two-qubit gate), extra readout flip r. Settings A and B are chosen by `scripts/pick_ab.py` from the
calibration grid (A = lowest-noise cell whose best arm has ZNE off; B = the cell with a different
best arm and the largest margin); schedules stable (A), slow (linear A -> B over 300 steps), jump
(A for 150 steps, then B). The Qollab spot check compares the local model with Qollab's own
simulator on the same circuits (mean absolute score difference).

## 7. Threats to validity (also in the README)

1. **Simulation, not hardware.** Every reward comes from Aer with a noise model rebuilt from
   calibration data; the device itself was never run.
2. **Markovian, local model.** No crosstalk, leakage, non-Markovian or time-correlated noise
   within a day; gate errors are depolarising plus relaxation.
3. **Coherent fraction is assumed.** f = 0 primary, 0.3 sensitivity. Under coherent error the
   mirror construction partially echoes the over-rotation between its two halves, which
   **flatters the non-twirled arms** on the mirror score (measured: at f = 0.3 the untwirled score
   does not fall while the twirled one does not rise), so the mirror proxy cannot show twirling's
   benefit against coherent error; only the forward-observable validation (item 5 above) can.
4. **One device, one chain per size.** Switches are about this chain's qubits.
5. **Mirror proxy ≠ the user's observable.** Quantified per day by the proxy validation.
6. **Synthetic drift on source 1.** The IonQ-like schedules are designed, not measured.
7. **IonQ simulator accuracy.** Qollab's Aria-1 simulator is itself a model of the device.
8. **Daily snapshot, last value carried forward.** Sub-daily changes (readout recalibrates every
   few hours) are not resolved.
9. **Seed-mean oracle.** The dynamic oracle uses seed-mean rewards; a learner only ever sees one
   sample per pull, so "pseudo-regret" is relative to an unattainable reference.

## 8. Implementation notes (so the test list and the code agree)

- Plan test 5 ("transpile_once(fold(...)) keeps the 2q count") is implemented as "basis
  translation keeps the 2q count": an optimising transpile of a folded circuit legitimately
  cancels the fold, which is exactly why no optimising pass runs after the twin.
- The twin's Pauli layer is seeded per (circuit, seed), not per (day, seed), so the circuit set is
  built once per seed pass and only the noise model changes per day; the simulator seed is per
  (day, circuit, seed, shape).
- Folding happens before twirling and drift injection so that every folded copy of a cz gets
  its own twirl Paulis and its own error draw.
- Qollab allows one `backend.run` per Run; the E0 checks and the spot check are therefore
  single list jobs, and live mode on Qollab is out of scope.

## Typo log

- 2026-10-10 18:00 ET, added threat 10 (a finding, not a definition change): **IonQ's compiler cancels mirror and
  folded structure.** On Qollab's Aria-1 noise-model simulator, identity chains of up to 40 gates and a 3x-folded mirror
  twin all return P(target) = 1.0, so the E0 depth sweep could not fit constants and the IonQ-like model keeps its
  defaults; the spot check is informative only on cells where injected errors survive compilation. ZNE by folding is
  not executable through Qollab's IonQ backends without native-gate control. The IBM study is unaffected (Aer applies
  no optimisation after basis translation).
