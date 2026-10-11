# Cue sheet: which slide sits under which words

Total about 3:05 at a normal conversational pace (517 words, about 170 a minute). The whole video is these 16 images plus your voice. In iMovie: drag 01.png to 16.png in order, set each clip to the seconds column (Ken Burns off, crop = Fit), record the voiceover reading SCRIPT.md straight through, then nudge clip lengths to where you actually are. If a take runs past 3:00, drop slide 14's line, then the last sentence of slide 3.

| slide | start | end | seconds | words spoken over it |
|---|---|---|---|---|
| `01.png` | 0:00 | 0:08 | 8 | This is AutoMitigate. It decides which error-mitigation settings to use on a quantum computer, and it learns that choice from the machine itself. |
| `02.png` | 0:08 | 0:28 | 21 | It exists because quantum computers are still noisy. Every answer comes back slightly wrong, so you have to clean it up, and there are three standard ways. Run at deliberately higher noise and extrapolate back to zero, wrap each two-qubit gate in random Pauli flips so the systematic errors cancel, or measure the detector's bias and subtract it. |
| `03.png` | 0:28 | 0:49 | 21 | The trouble is that none of them is free and none always helps. Each costs extra runs, each suits some circuits and not others, and the errors they fight are not constant. Here is our qubits' two-qubit error over nine months, jumping at every recalibration. So the right combination depends on your circuit, your machine, and the day. |
| `04.png` | 0:49 | 1:05 | 16 | Which is why we made the computer choose. We treat it as a bandit, the same maths behind A/B testing. Eight arms, one per combination of the three tricks. Pull one, score it, update, repeat, until it settles on the arm that keeps scoring best. |
| `05.png` | 1:05 | 1:23 | 18 | The scoring is the part I like most. We run the circuit, scramble it with random Paulis, then run it backwards, so the right answer is one bitstring we already know, and the score is how often it comes out. No ideal simulation, so it works on circuits whose answer nobody knows. |
| `06.png` | 1:23 | 1:33 | 10 | Here it is on Qollab. GHZ on eight qubits, the real-drift data, press Run, and it replays nine months of real IBM calibration logs, one pull per day. |
| `07.png` | 1:33 | 1:46 | 13 | The top panel is regret, the score lost by not pulling each day's best arm. Blue is our learner, green dashed is everything switched on. It finds the right arm within a week and stays there. |
| `08.png` | 1:46 | 1:57 | 11 | Then the circuit runs for real on the simulator you chose, raw and with readout mitigation. On IBM's Fez model, 0.82 raw, 0.94 mitigated, where a noiseless machine gives 1. |
| `09.png` | 1:57 | 2:07 | 10 | We pre-registered the analysis, and across 240 days the best setting never changed. A perfect tracker would gain under a hundredth of a percent over picking once. |
| `10.png` | 2:07 | 2:13 | 7 | ZNE with readout mitigation won every day on every circuit, so picking once is as good as tracking. |
| `11.png` | 2:13 | 2:22 | 9 | The bandit's job is then to find that setting cheaply, and epsilon-greedy does, with 45 to 79 percent less regret than switching everything on. |
| `12.png` | 2:22 | 2:33 | 11 | The obvious doubt is whether a mirror score tracks your real circuit, so we checked day by day. Its ranking of the arms matches the true error at 0.6 to 0.9. |
| `13.png` | 2:33 | 2:42 | 9 | On an IonQ-style model where the noise jumps halfway, the best setting still does not move, so the gap is just the cost of checking. |
| `14.png` | 2:42 | 2:46 | 4 | The model itself agrees with Qollab's Aria-1 simulator. |
| `15.png` | 2:46 | 2:57 | 11 | The caveat is that this held on good qubits. On a middling chain the best setting did drift, nine switches in nine months, so tracking matters where the hardware is worse. |
| `16.png` | 2:57 | 3:05 | 8 | Everything is open source under MIT and installs with pip. Thomas Sebahi and I built it this weekend at McGill. Thanks for watching. |
