# AutoMitigate, demo video script (v2, Sunday)

Normal speaking pace, about 2 minutes 50 seconds. The number in brackets is the slide on screen; CUES.md has the exact timings.

**[1] Title**

AutoMitigate. A bandit that picks your error-mitigation settings for you.

**[2] Noisy answers, three fixes**

Quantum computers give you slightly wrong answers. There are software tricks that clean them up: zero-noise extrapolation, Pauli twirling, readout mitigation.

**[3] It depends on the day**

Each one helps on some circuits and hurts on others, and the machine's error rates move around from day to day. Nobody works that out by hand.

**[4] Treat it as a bandit**

AutoMitigate treats it as a bandit problem, the same maths as A/B testing. Eight arms, one for every way of switching the three tricks on or off. Pull one, score it, update, pull again.

**[5] The score is a mirror circuit**

The score comes from a mirror circuit. Run your circuit, scramble it with a random layer of Paulis, run it backwards. The right answer is one bitstring you already know, so there is no ideal simulation to run.

**[6] On Qollab**

On Qollab. We pick GHZ on eight qubits and the real-drift data, hit Run, and it replays nine months of actual IBM calibration logs, one pull per day.

**[7] The chart**

The top panel is regret against an oracle that knows the best arm every day. Our learner is the thick line. Below it, the arm it picked each day.

**[8] Then a real run**

Then it runs the circuit for real on whichever simulator you chose, raw and with readout mitigation. Raw 0.82, mitigated 0.94, ideal 1.

**[9] What we found**

We wrote the analysis down before we had any data. Across 240 days of ibm_fez the best setting never changed. A perfect tracker would gain less than a hundredth of a percent over picking once.

**[10] Every day the same arm**

ZNE plus readout mitigation won every single day. So picking once is as good as tracking.

**[11] The bandit's job**

The bandit's job is just to find that setting cheaply, and epsilon-greedy does. It beats switching everything on by 45 to 79 percent in regret.

**[12] Is the score honest?**

We checked the mirror score against the real forward error, day by day. Its ranking of the eight arms agrees with the truth at a Spearman correlation of 0.6 to 0.9, and the arm it picks costs at most 8 percent of the worst one.

**[13] A different machine**

Same tool on an IonQ-style model where the noise jumps halfway through. Nothing changes here either, and the chart shows what exploring costs when there is nothing to find.

**[14] Checked against IonQ's simulator**

We also checked the model against Qollab's own Aria-1 simulator on identical circuits.

**[15] One caveat**

One thing we did find. On a worse set of qubits the best setting did drift, nine switches in nine months. Tracking matters exactly where the hardware is worse.

**[16] The end**

Everything is open source under MIT, pip-installable. Built this weekend by Ian Wilson and Thomas Sebahi at McGill. AutoMitigate.
