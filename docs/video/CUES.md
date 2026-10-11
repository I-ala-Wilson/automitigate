# Cue sheet: which slide sits under which words

Total about 3:03 at a normal conversational pace (509 words, about 170 a minute). The whole video is these 17 images plus your voice. In iMovie: drag 01.png to 17.png in order, set each clip to the seconds column (Ken Burns off, crop = Fit), record the voiceover reading SCRIPT.md straight through, then nudge clip lengths to where you actually are. If a take runs past 3:00, drop slide 15's line, then the last sentence of slide 3.

| slide | start | end | seconds | words spoken over it |
|---|---|---|---|---|
| `01.png` | 0:00 | 0:07 | 7 | This is AutoMitigate. You give it your circuit and your machine, and it works out which error-mitigation settings to use. |
| `02.png` | 0:07 | 0:22 | 15 | It exists because quantum computers are still noisy, and there are three standard ways to clean up the answer: run at higher noise and extrapolate back, wrap each two-qubit gate in random Pauli flips, or measure the detector's bias and subtract it. |
| `03.png` | 0:22 | 0:34 | 12 | The trouble is that none of them is free and none always helps, and the errors they fight keep changing. This is our qubits' error over eight months, jumping at every recalibration. |
| `04.png` | 0:34 | 0:52 | 18 | Which is why we made the computer choose. We treat it as a bandit, the same maths behind A/B testing. Eight arms, one per combination of the tricks. Pull one, score it, update, repeat, until it settles on the best, and hands you the setting with the Qiskit lines to apply it. |
| `05.png` | 0:52 | 1:11 | 19 | The scoring is the part I like most. We run the circuit, scramble it with random Paulis, then run it backwards, so the right answer is one bitstring we already know, and the score is how often it comes out. No ideal simulation, so it works on circuits whose answer nobody knows. |
| `06.png` | 1:11 | 1:20 | 9 | Here it is on Qollab. GHZ on eight qubits, press Run, and it replays eight months of real IBM calibration logs, one pull per day. |
| `07.png` | 1:20 | 1:32 | 12 | The top panel is regret, the score lost by not pulling each day's best arm. Blue is our learner, green dashed is everything switched on. It finds the right arm within a week and stays there. |
| `08.png` | 1:32 | 1:43 | 11 | Then the circuit runs for real on the simulator you chose, raw and with readout mitigation. On IBM's Fez model, 0.82 raw, 0.94 mitigated, where a noiseless machine gives 1. |
| `09.png` | 1:43 | 1:55 | 12 | We fixed the analysis before we had any data. Across 240 days, a tracker that knew the right arm every day would gain under a hundredth of a percent over picking once. |
| `10.png` | 1:55 | 2:02 | 7 | ZNE with readout mitigation was the best fixed setting on every circuit, so picking once is as good as tracking. |
| `11.png` | 2:02 | 2:11 | 9 | So the bandit's job is to find that setting cheaply, and epsilon-greedy does, with 45 to 79 percent less regret than switching everything on. |
| `12.png` | 2:11 | 2:15 | 4 | The same on all five circuits: the learner sits well below everything-on. |
| `13.png` | 2:15 | 2:26 | 11 | The obvious doubt is whether a mirror score tracks your real circuit, so we checked day by day. Its ranking of the arms matches the true error at 0.6 to 0.9. |
| `14.png` | 2:26 | 2:36 | 10 | On an IonQ-style model where the noise jumps halfway, the best setting for this circuit does not move, so the gap is just the cost of checking. |
| `15.png` | 2:36 | 2:39 | 3 | The model itself agrees with Qollab's Aria-1 simulator. |
| `16.png` | 2:39 | 2:51 | 12 | The caveat is that this held on good qubits. On a middling chain the best setting did drift, nine switches in eight months, so tracking matters where the hardware is worse. |
| `17.png` | 2:51 | 3:03 | 12 | If you run circuits on real hardware, this replaces guessing which tricks to switch on. It is open source under MIT and installs with pip. Thomas Sebahi and I built it this weekend at McGill. |
