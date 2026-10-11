# How the weekend ran

The project was built between Friday 9 October 19:00 and Sunday 11 October 19:00 ET (Montreal) by Ian Wilson and Thomas Sebahi on two laptops. This file replaces the append-only operational log the two laptops kept during the window; the results themselves are in README.md and docs/results.md, and every number is in data/analysis/.

Friday evening: repository, packaging, the arms (ZNE, Pauli twirling, readout mitigation), the randomised mirror reward, the per-day noise model rebuilt from the ibm_fez calibration log, and the pre-registered analysis plan (docs/analysis_plan.md), committed before the first drift reward existed.

Friday night to Saturday: the two laptops ran the sweeps as a queue, one pull per day for 240 days, five circuits, eight arms and twenty seeds, plus the forward-observable validation, the coherent-fraction and median-chain sensitivities, and the IonQ-like table. Learners, the analysis script and the figures were written while the queue ran.

Saturday: the Qollab demo (main.py) and its bundle; the spot check against Qollab's Aria-1 simulator; the discovery that Qollab's compiler cancels mirrored and folded structure on every backend (threat 10), which ruled out fitting the IonQ-like constants there and limited the live step to a forward run with readout mitigation.

Sunday: final regenerate of the tables and figures, the README, the project card, the video kit (docs/video/), a fresh-clone test, the arXiv re-check in docs/related_work.md, and a vetting pass of every quoted number against the data.
