# AutoMitigate, demo video script (v4)

One continuous explanation. The number in brackets is the slide on screen when you reach that line; CUES.md has the timings. About 2 minutes 50 seconds at a normal pace. If a take runs long, drop slide 14's line first, then the last sentence of slide 3.

**[1]**

This is AutoMitigate. It decides which error-mitigation settings to use on a quantum computer, and it learns that choice from the machine itself.

**[2]**

It exists because quantum computers are still noisy. Every answer comes back slightly wrong, so you have to clean it up, and there are three standard ways. Run at deliberately higher noise and extrapolate back to zero, wrap each two-qubit gate in random Pauli flips so the systematic errors cancel, or measure the detector's bias and subtract it.

**[3]**

The trouble is that none of them is free and none always helps. Each costs extra runs, each suits some circuits and not others, and the errors they fight are not constant. Here is our qubits' two-qubit error over nine months, jumping at every recalibration. So the right combination depends on your circuit, your machine, and the day.

**[4]**

Which is why we made the computer choose. We treat it as a bandit, the same maths behind A/B testing. Eight arms, one per combination of the three tricks. Pull one, score it, update, repeat, until it settles on the arm that keeps scoring best.

**[5]**

The scoring is the part I like most. We run the circuit, scramble it with random Paulis, then run it backwards, so the right answer is one bitstring we already know, and the score is how often it comes out. No ideal simulation, so it works on circuits whose answer nobody knows.

**[6]**

Here it is on Qollab. GHZ on eight qubits, the real-drift data, press Run, and it replays nine months of real IBM calibration logs, one pull per day.

**[7]**

The top panel is regret, the score lost by not pulling each day's best arm. Blue is our learner, green dashed is everything switched on. It finds the right arm within a week and stays there.

**[8]**

Then the circuit runs for real on the simulator you chose, raw and with readout mitigation. On IBM's Fez model, 0.82 raw, 0.94 mitigated, where a noiseless machine gives 1.

**[9]**

We pre-registered the analysis, and across 240 days the best setting never changed. A perfect tracker would gain under a hundredth of a percent over picking once.

**[10]**

ZNE with readout mitigation won every day on every circuit, so picking once is as good as tracking.

**[11]**

The bandit's job is then to find that setting cheaply, and epsilon-greedy does, with 45 to 79 percent less regret than switching everything on.

**[12]**

The obvious doubt is whether a mirror score tracks your real circuit, so we checked day by day. Its ranking of the arms matches the true error at 0.6 to 0.9.

**[13]**

On an IonQ-style model where the noise jumps halfway, the best setting still does not move, so the gap is just the cost of checking.

**[14]**

The model itself agrees with Qollab's Aria-1 simulator.

**[15]**

The caveat is that this held on good qubits. On a middling chain the best setting did drift, nine switches in nine months, so tracking matters where the hardware is worse.

**[16]**

Everything is open source under MIT and installs with pip. Thomas Sebahi and I built it this weekend at McGill. Thanks for watching.
