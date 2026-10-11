# AutoMitigate, demo video script

One continuous explanation. The number in brackets is the slide on screen when you reach that line; CUES.md has the timings. If a take runs long, drop slide 15's line first, then the last sentence of slide 3.

**[1]**

This is AutoMitigate. You give it your circuit and your machine, and it works out which error-mitigation settings to use.

**[2]**

It exists because quantum computers are still noisy, and there are three standard ways to clean up the answer. You can run at higher noise and extrapolate back, wrap each two-qubit gate in random Pauli flips, or measure the detector's bias and subtract it.

**[3]**

The trouble is that none of them is free and none always helps, and the errors they fight keep changing. This is our qubits' error over eight months, jumping at every recalibration.

**[4]**

Which is why we made the computer choose. We treat it as a bandit, the same maths behind A/B testing. Eight arms, one per combination of the tricks. Pull one, score it, update, repeat, until it settles on the best, and hands you the setting with the Qiskit lines to apply it.

**[5]**

The scoring is the part I like most. We run the circuit, scramble it with random Paulis, then run it backwards, so the right answer is one bitstring we already know, and the score is how often it comes out. No ideal simulation, so it works on circuits whose answer nobody knows.

**[6]**

Here it is on Qollab. GHZ on eight qubits, press Run, and it replays eight months of real IBM calibration logs, one pull per day.

**[7]**

The top panel is regret, the score lost by not pulling each day's best arm. Blue is our learner, green dashed is everything switched on. It finds the right arm within a week and stays there.

**[8]**

Then the circuit runs for real on the simulator you chose, raw and with readout mitigation. On IBM's Fez model, 0.82 raw, 0.94 mitigated, where a noiseless machine gives 1.

**[9]**

We fixed the analysis before we had any data. Across 240 days, a tracker that knew the right arm every day would gain under a hundredth of a percent over picking once.

**[10]**

ZNE with readout mitigation was the best fixed setting on every circuit, so picking once is as good as tracking.

**[11]**

So the bandit's job is to find that setting cheaply, and epsilon-greedy does, with 45 to 79 percent less regret than switching everything on.

**[12]**

It is the same on all five circuits, with the learner well below everything-on.

**[13]**

The obvious doubt is whether a mirror score tracks your real circuit, so we checked day by day. Its ranking of the arms matches the true error at 0.6 to 0.9.

**[14]**

On an IonQ-style model where the noise jumps halfway, the best setting for this circuit does not move, so the gap is just the cost of checking.

**[15]**

The model itself agrees with Qollab's Aria-1 simulator.

**[16]**

The caveat is that this held on good qubits. On a middling chain the best setting did drift, nine switches in eight months, so tracking matters where the hardware is worse.

**[17]**

If you run circuits on real hardware, this replaces guessing which tricks to switch on. It is open source under MIT and installs with pip. Thomas Sebahi and I built it this weekend at McGill.
