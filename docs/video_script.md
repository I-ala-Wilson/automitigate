# Demo video: shot list and script (2:35, Ian's voice, one take)

Recorded as a QuickTime screen recording of one Chrome window whose tabs are in this order
(switch with ⌘1…⌘0): 1 diagram 05 · 2 diagram 01 · 3 diagram 02 · 4 Qollab project, Run
settings ghz8 / ibm / eps-greedy · 5 figures/drift_value.png · 6 figures/best_arm_ghz4.png ·
7 figures/proxy_per_day.png · 8 Qollab project, Run settings ghz4 / ionq / jump / Discounted TS ·
9 data/ionq/spot_check.json · 0 the repo front page. Both Qollab tabs are run once before
recording so the runtime is cached.

| # | time | on screen | narration |
|---|---|---|---|
| 1 | 0:00 | diagram 05 | Every quantum computer today is noisy, and there is a toolbox of tricks to clean the answers up: zero-noise extrapolation, Pauli twirling, readout mitigation. Which ones to switch on depends on the circuit and on the machine, and the machine's error rates drift from day to day. Nobody can diagnose that fast enough to choose by hand. |
| 2 | 0:18 | diagram 01, then diagram 02 at "eight arms" | AutoMitigate treats the choice as a bandit, the algorithm behind A/B testing. Eight arms: each trick on or off. It pulls an arm, scores it with a randomised mirror circuit, a twin that applies the gates and then undoes them, so the right answer is a known bitstring and no ideal simulation is needed, then updates and pulls again. |
| 3 | 0:40 | Qollab, press Run, scroll through chart, arm strip, recommendation | Here it is on Qollab, replay mode, no backend needed. I pick GHZ-8 and the real-drift source, press Run, and it replays nine months of real IBM calibration data, one pull per day. The chart is cumulative regret against a perfect per-day oracle: the learner, plain Thompson, the everything-on default, the best fixed arm. Below it, the arm it chose each day, and at the bottom the recommendation with the Qiskit snippet to apply it. |
| 4 | 1:05 | drift_value.png, then best_arm_ghz4.png at "best setting" | We pre-registered the analysis before the data existed, and the answer is clear. Over 240 daily snapshots of ibm_fez the best setting never changed: the drift value, what a perfect tracker gains over the best fixed setting, is below a hundredth of a percent on all five circuits, and ZNE plus readout mitigation wins every day. A setting chosen once is as good as tracking. The bandit's job is to find it cheaply: epsilon-greedy does, and beats the everything-on default by 45 to 79 percent in regret. |
| 5 | 1:35 | proxy_per_day.png | Is the mirror score honest? Per day, its ranking of the eight arms agrees with the real forward error at a Spearman correlation of 0.6 to 0.9, and the arm it picks costs at most 8 percent of the worst arm's error. So this works without ever knowing the circuit's answer. |
| 6 | 1:55 | second Qollab tab, press Run, scroll to the arm strip; spot_check.json at "job IDs" | Same tool, different machine: an IonQ-like model with a drift jump halfway through. The best arm switches and the discounted learner follows it. The model is checked against Qollab's own Aria-1 simulator on identical circuits, mean difference under 3 percent, job IDs in the repo. |
| 7 | 2:15 | repo front page, end on the team line | One caveat we found on the way: on a mediocre chain of qubits the best setting did drift, nine switches, so tracking matters exactly where the hardware is worse. Everything is open source under MIT, pip-installable, every number reproducible from the committed tables, built this weekend by Ian Wilson and Thomas Sebahi at McGill. AutoMitigate. |

If a take runs past 2:55, drop the last sentence of shot 3 and the first sentence of shot 5.
Numbers: `data/analysis/headline.json`, `learners.json`, `proxy.json`, `sensitivity.json`,
`data/ionq/spot_check.json`. Three takes, keep the cleanest, trim in QuickTime, export 1080p,
upload unlisted, confirm it plays in an incognito window, link it in the project card and README.
