# AutoMitigate, demo video script (v3)

Read it as one explanation, not sixteen captions. The number in brackets is the slide on screen when you reach that line; CUES.md has the timings. About 2 minutes 50 seconds.

**[1]**

This is AutoMitigate. It picks your error-mitigation settings for you, because nobody can keep picking them by hand.

**[2]**

A quantum computer gives you a slightly wrong answer, and there are three well-known tricks for cleaning it up. You run at higher noise and extrapolate back to zero, you wrap each two-qubit gate in random Pauli flips, or you measure the detector's bias and subtract it.

**[3]**

Each one helps on some circuits and hurts on others, and the error they fight is not constant. This is the two-qubit error on the qubits we used, over nine months, and it jumps at every recalibration. So the right combination depends on your circuit, your machine, and the day.

**[4]**

So we made the computer choose. We treat it as a bandit, the same maths as A/B testing. Eight arms, one per way of switching the three tricks on or off. Pull an arm, score it, update, pull again, and the learner settles on whatever keeps scoring best.

**[5]**

The scoring is the part I find most interesting. We run the circuit, scramble it with random Paulis, then run it backwards, so the right answer is one bitstring we already know. The score is how often it comes out. We never simulate the ideal result, which is why this works on circuits whose answer nobody knows.

**[6]**

Here it is on Qollab. We pick GHZ on eight qubits and the real-drift data, press Run, and it replays nine months of real IBM calibration logs, one pull per day.

**[7]**

The top panel is regret, the score you lose by not pulling each day's best arm. Blue is our learner, green dashed is switching everything on. Below, the arm it picked each day. It finds the right one in the first week and sits on it.

**[8]**

Then the circuit runs for real on the simulator you chose, raw and with readout mitigation. On IBM's Fez model, 0.82 raw, 0.94 mitigated, where a noiseless machine gives 1.

**[9]**

What surprised us is this. We wrote the analysis down before we had data, and across 240 days the best setting never changed. A tracker that knew the right arm every day would gain less than a hundredth of a percent over picking once.

**[10]**

That is because ZNE with readout mitigation won every single day. On this chain, picking once is as good as tracking.

**[11]**

So the bandit's real job is to find that setting cheaply, and epsilon-greedy does, with 45 to 79 percent less regret than switching everything on.

**[12]**

The obvious doubt is whether a mirror score says anything about your real circuit, so we checked day by day. Its ranking of the arms agrees with the true error at 0.6 to 0.9, and its pick costs at most 8 percent of the worst arm.

**[13]**

Against an IonQ-style model where the noise jumps halfway, the best setting still does not move, so the gap is just the cost of checking.

**[14]**

And that model agrees with Qollab's own Aria-1 simulator on identical circuits, job IDs in the repo.

**[15]**

The caveat is that this held on good qubits. On a middling chain the best setting did drift, nine switches in nine months, so tracking matters exactly where the hardware is worse.

**[16]**

It is open source under MIT, installs with pip, and every number comes from committed tables. Thomas Sebahi and I built it this weekend at McGill. Thanks for watching.
