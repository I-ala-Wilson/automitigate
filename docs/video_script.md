# AutoMitigate, demo video script (v3)

Read it as one explanation, not sixteen captions. The number in brackets is the slide on screen when you reach that line; CUES.md has the timings. About 2 minutes 50 seconds at a normal pace; the two bracketed sentences at the end are the first to drop if a take runs long.

**[1]**

This is AutoMitigate. It picks your error-mitigation settings for you.

**[2]**

A quantum computer gives you a slightly wrong answer, and there are three well-known tricks for cleaning it up. Run at higher noise and extrapolate back, wrap each two-qubit gate in random Pauli flips, or measure the detector's bias and subtract it.

**[3]**

Each helps some circuits and hurts others, and the error they fight is not constant. This is the two-qubit error on our qubits over nine months, jumping at every recalibration. So the right combination depends on the circuit, the machine, and the day.

**[4]**

So we made the computer choose, as a bandit, the same maths as A/B testing. Eight arms, one per combination of the tricks. Pull one, score it, update, pull again, until it settles on whatever keeps scoring best.

**[5]**

The scoring is the part I find most interesting. We run the circuit, scramble it with random Paulis, then run it backwards, so the right answer is one bitstring we already know, and the score is how often it comes out. No ideal simulation, so it works on circuits whose answer nobody knows.

**[6]**

Here it is on Qollab. GHZ on eight qubits, the real-drift data, press Run, and it replays nine months of real IBM calibration logs, one pull per day.

**[7]**

The top panel is regret, the score lost by not pulling each day's best arm. Blue is our learner, green dashed is everything switched on. Below, the arm it picked each day. It finds the right one within a week and stays.

**[8]**

Then the circuit runs for real on the simulator you chose, raw and with readout mitigation. On IBM's Fez model, 0.82 raw, 0.94 mitigated, where a noiseless machine gives 1.

**[9]**

What surprised us is this. We pre-registered the analysis, and across 240 days the best setting never changed. A tracker that knew the right arm every day would gain under a hundredth of a percent over picking once.

**[10]**

ZNE with readout mitigation won every day, so picking once is as good as tracking.

**[11]**

The bandit's job is then to find that setting cheaply, and epsilon-greedy does, with 45 to 79 percent less regret than switching everything on.

**[12]**

The obvious doubt is whether a mirror score tracks your real circuit, so we checked day by day. Its ranking of the arms matches the true error at 0.6 to 0.9, and its pick costs at most 8 percent of the worst arm.

**[13]**

On an IonQ-style model where the noise jumps halfway, the best setting still does not move, so the gap is just the cost of checking.

**[14]**

And that model agrees with Qollab's own Aria-1 simulator, job IDs in the repo.

**[15]**

The caveat is that this held on good qubits. On a middling chain the best setting did drift, nine switches in nine months, so tracking matters where the hardware is worse.

**[16]**

It is open source under MIT, installs with pip, and every number comes from committed tables. Thomas Sebahi and I built it this weekend at McGill. Thanks for watching.
