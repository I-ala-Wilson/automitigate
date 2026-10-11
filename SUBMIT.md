# SUBMIT.md: what Thomas does to get AutoMitigate submitted (Sunday 11 Oct, deadline 19:00 ET)

Ian is offline from about 16:20. Everything that can be prepared is prepared and in HEAD: code, data, analysis, README, project-card text, demo bundle, video kit. What remains is hands-on and listed here in order. Tick them off top to bottom. If something fails, the fallback is under each step.

## 0. Pull
```
git pull
```
Confirm `git log -1` shows a commit from today. Do not edit code; nothing below needs code changes.

## 1. Video (do this first, it is the only thing that takes real time)
Open `docs/video/HANDOFF.md`. In short: 17 slides `docs/video/01.png` … `17.png`, read `docs/video/SCRIPT.md` over them in iMovie using the times in `docs/video/CUES.md`, export 1080p, upload to YouTube as **Unlisted**, title "AutoMitigate: a bandit that learns your error-mitigation settings (Qollab + IonQ hackathon 2026)". Must be 2:00 to 3:00. Open the link in an incognito window to confirm it plays without sign-in.
Fallback: if iMovie is a problem, QuickTime screen-record Preview stepping through the PNGs full-screen while you read; trim ends; same upload.

## 2. Put the video link in the repo
- `README.md` line 7: replace `*(link added before submission)*` with the URL.
- `docs/project_card.md`: add a first line `Demo video: <URL>` under the title.
```
git add README.md docs/project_card.md && git commit -m "[thomas] video link" && git push
```

## 3. Upload the demo to your Qollab project (the one that gets published)
1. Open your AutoMitigate project on qollab.xyz → **Code** tab → file-tree icon → drag `qollab_project.zip` (from HEAD, 8.9 MB, 54 files) onto the upload area.
2. Dialog "Unpack qollab_project.zip?" → **Unpack**. Dialog "Erase existing files first?" → **Erase first** → **Delete and upload**. Wait for "Saved".
3. **Run Project** → **Run** → in the Select QPU dialog leave Built-in simulator → **Run**. Expect in about 4 s: the regret table, `figure.svg`, and three lines starting `Live run on basic_simulator`.
4. Press **Run** again → QPU dialog → expand **IBM** → **Fez** → **Run**. Expect about 13 s, then `raw = 0.8x, after readout mitigation = 0.9x, ideal = 1.000`. That is the run a judge will see.
Never select the two "IonQ … (36q) Credits apply" rows.
Fallback: if the zip upload fails, unzip it locally and drag the `qollab_project` folder instead. If the Fez run takes longer than a minute, press Stop; the built-in run is enough.

## 4. Project card
Open the **Project Card** tab of the same project. Paste `docs/project_card.md` section by section: the bold pitch line, The problem, How it works (table included), How to run it, Results, What is new, Limitations, Disclosure, Accessibility. Put `Demo video: <URL>` and `Code: https://github.com/I-ala-Wilson/automitigate` at the top. Keep the Disclosure paragraph exactly as written (it contains the required attribution line and the AI-assistance sentence).

## 5. Publish (target 16:00, no later than 18:00)
Press **Publish** on the project. Copy the public URL. Put it in `README.md` line 7 in place of `*(link added at publish)*`, then:
```
git add README.md && git commit -m "[thomas] published project link" && git push
```

## 6. Incognito check (5 minutes, do not skip)
In a private window, logged out: open the public project URL, press Run, see the chart. Open the video URL, it plays. Open the repo URL, README shows both links at the top.

## 7. Submit (target 17:00, hard stop 18:30)
Hackathon submission form. Fields you will need:
- Project: the public Qollab URL from step 5
- Repository: https://github.com/I-ala-Wilson/automitigate
- Video: the YouTube URL from step 1
- Team: Ian Wilson, Thomas Sebahi (McGill University)
- Theme: Quantum Impact
- One-line description: `A bandit that auto-tunes quantum error-mitigation settings per circuit, per machine, per hour, using a mirror-circuit reward that needs no ideal answer.`
After submitting, screenshot the confirmation and commit it as `docs/submission_confirmation.png` with message `[thomas] submitted`.

## What is already verified (no need to redo)
- Demo bundle runs on Qollab's built-in simulator, IBM Fez simulator and IonQ Aria-1 simulator (tested Saturday night and Sunday on Ian's scratch project).
- Fresh clone + `pip install -e ".[sweep,dev]"` + `pytest -q`: 37 tests pass (Saturday 22:50).
- README, `docs/results.md`, `docs/project_card.md`, `docs/analysis_plan.md`, `docs/related_work.md` are final.
- No AI attribution anywhere in the repo or commits; the disclosure sentence lives only in the project card and README Disclosure section. Keep it that way: commit messages are `[thomas] …`, nothing else.
