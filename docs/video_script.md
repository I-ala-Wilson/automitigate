# Demo video script (2.5 min, Ian's voice)

Record Sunday after the freeze, once `docs/results.md` has the final numbers. Fill every
<N>, <X>, <K>, <Y> from `docs/results.md` before recording; never record with numbers that
will change. Screen capture: the Qollab project with no QPU selected, then the figures.

| t | on screen | voice |
|---|---|---|
| 0:00 | diagram 05 (drift in ones and zeros) | Which error-mitigation setting to use changes with the machine and the hour, and nobody can diagnose it fast enough to choose by hand. |
| 0:20 | diagram 01 (the loop), then 02 (the eight arms) | AutoMitigate treats the choice as a bandit. Eight arms: zero-noise extrapolation, Pauli twirling and readout mitigation, on or off. It pulls an arm, scores it with a randomised mirror circuit whose right answer is known in advance, and updates. No ideal simulation needed. |
| 0:45 | Qollab: pick ghz8, source ibm, learner Discounted TS, press Run; regret chart appears | Here it replays nine months of real ibm_fez calibration data, one pull per day. The curves are cumulative regret against a perfect per-day oracle: the learner, plain Thompson, the everything-on default, the best fixed arm. |
| 1:20 | `docs/results.md` first paragraph, drift_value.png | The pre-registered headline: over <N> days a perfect tracker would have gained <X> % over the best fixed setting, and the best setting changed significantly <K> times. For a researcher that means <one sentence: "pick once per device" or "re-tune after recalibrations">. <Learner> captured the most of it against the everything-on default. |
| 1:40 | proxy_per_day.png | Is the mirror score honest? On <Y> % of days the setting it picks is the one that also minimises the real error on the forward circuit, measured per day, not pooled. |
| 2:00 | Qollab: source ionq, schedule jump, press Run; arm strip shows the switch | Same tool, different machine: an IonQ-like model with a drift jump, spot-checked against Qollab's own Aria-1 simulator with job IDs in the repo. The learner notices the jump and moves. |
| 2:20 | README top, `pip install -e .`, LICENSE, project card disclosure line; end on the recommendation card | Open source, MIT, pip-installable, every number reproducible from the committed tables, and the recommendation comes with the Qiskit snippet to apply it. |

Three takes, keep the cleanest. Upload unlisted to YouTube (or Drive, anyone with the link);
confirm it opens in an incognito window before pasting the link into the project card.
