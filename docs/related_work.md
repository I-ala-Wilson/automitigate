# Related work

<!-- Drafted Fri night from the pre-window reading; the Sunday 12:00 arXiv re-check adds anything
     new under "Re-check" at the bottom. One line per paper on what they did and what differs here. -->

## Bandits over error mitigation (2026)

- **CMAB-ZNE, arXiv 2608.06426.** A contextual bandit chooses among zero-noise-extrapolation fold sets. Arms are fold sets only; drift is synthetic; the reward needs a known answer. Here: three real techniques as arms (ZNE, Pauli twirling, readout mitigation), a mirror-circuit reward that needs no ideal answer, and nine months of real calibration drift.
- **GSC-QEMit, arXiv 2604.24551.** Bandit-style selection where the arms are simulator noise knobs rather than mitigation techniques. Here: the arms are the techniques a user would actually switch on.
- **APGEM, arXiv 2610.01253.** Adaptive mitigation whose reward compares against the ideal expectation value. Here: the randomised mirror circuit gives a known target bitstring for free, so the learner can run on circuits whose answer is unknown.

None of the three evaluates non-stationary learners under real device drift; that comparison, with a pre-registered analysis plan, is the contribution of this repo.

## Mirror circuits and randomised compiling

- **Proctor et al., arXiv 2008.11294 (mirror-circuit benchmarking) and 2112.09853.** Mirror circuits with a random Pauli layer give a known output bitstring and avoid the echo cancellation of coherent errors that a plain U·U⁻¹ suffers. We use the single-central-Pauli-layer variant with a Pauli-frame-corrected inverse; `docs/analysis_plan.md` records the residual echo as a threat to validity.

## Non-stationary bandits

- **Agrawal and Goyal 2012.** Thompson sampling with the Bernoulli trick for rewards in [0, 1] (our `Thompson`).
- **Raj and Kalyani 2017.** Discounted Thompson sampling (`DiscountedTS`, γ chosen on seeds 0–9).
- **Trovò et al. 2020.** Sliding-window Thompson sampling (`SlidingWindowTS`, window chosen on seeds 0–9).
- **Cao et al. 2019 (M-UCB).** Change detection by comparing the two halves of a per-arm window with forced exploration; we attach the detector to a Thompson base (`ChangeDetectTS`).

## Drift on real devices

- **Teegarden et al., arXiv 2601.09943.** Accuracy of IonQ simulators versus hardware; the reason the IonQ-like model is spot-checked against Qollab's Aria-1 simulator and treated as a model of a model.
- **arXiv 2507.01195.** Reports raw fidelity largely stationary within calibration cycles on IBM devices.
- **arXiv 2609.38713.** Reports ZNE hurting on most runs on ibm_marrakesh. The two together are the open contradiction this replay speaks to: whether the *best mitigation setting* moves, not just the raw fidelity.
- **Calibration data:** `phanerozoic/qiskit-calibration-drift` (Hugging Face, CC-BY-4.0, revision 56f55fb8), ibm_fez, Jan 31 to Oct 9 2026, 241 observed days.

## Re-check (Sunday 12:00)

Queries run 2026-10-11 11:35 ET on arXiv: "bandit quantum error mitigation selection", "mirror circuit reward adaptive error mitigation drift calibration", "non-stationary bandit quantum device drift mitigation". Already covered above: CMAB-ZNE (2608.06426), GSC-QEMit (2604.24551). New hits:

- **QBalance, arXiv 2605.02966 (May 2026).** A workflow library that treats compilation, noise suppression and mitigation (measurement mitigation, ZNE, circuit cutting) as a finite multi-objective strategy-selection problem and orders candidates with Thompson sampling; the reward is a survival-product error proxy and no device drift over time is evaluated. Here: the arms are only the mitigation techniques, the reward is measured on the device (mirror circuit), and nine months of real calibration drift are replayed.
- **Decision Kernels for QEM, arXiv 2607.02888 (July 2026).** Argues that expectation-value accuracy is the wrong benchmark when mitigated values feed a downstream decision (argmin, ranking, top-k), since such decisions depend on gaps, not absolute values. Relevant to our proxy validation: we report per-day rank agreement (Spearman) and the forward regret of the mirror-chosen arm, which are gap-type metrics, alongside top-1 agreement.
- **Fast-feedback calibration and drift control, arXiv 2512.07815 (Dec 2025).** Shot-by-shot and definite-outcome feedback protocols that re-tune device parameters against drift in real time; no mitigation-technique selection. Complementary: it moves the hardware, we choose the software setting on top of whatever the hardware does.

Nothing found that evaluates non-stationary learners over mitigation settings on real calibration history; the comparison in this repo remains, to our knowledge, the first.
