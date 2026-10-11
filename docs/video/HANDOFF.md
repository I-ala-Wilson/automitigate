# Video kit handoff (Sunday 11 Oct, 16:00 ET)

Ian's wifi is too poor to continue; Thomas finishes the video from this folder. Deadline 19:00 ET; the video must be 2:00 to 3:00, public or unlisted, no sign-in.

## What is here
- `01.png` … `17.png`: the 17 slides, 3200x2000, white, black hairline cards, Helvetica. The whole video is these 17 images plus a voiceover; nothing else is needed.
- `SCRIPT.md`: the narration, one block per slide, written in Ian's voice. about 2:55 at a normal pace at a brisk conversational pace. If a take runs past 3:00, drop slide 15's line first, then the last sentence of slide 3.
- `CUES.md`: start and end time per slide and the exact words spoken over it.
- `src/gen2.py`: regenerates the slides (`python3 src/gen2.py` writes `01.html` … `17.html` next to it, then render each with headless Chrome: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --no-sandbox --force-device-scale-factor=2 --window-size=1600,1000 --virtual-time-budget=3000 --user-data-dir=/tmp/p --screenshot=NN.png file:///absolute/path/to/docs/video/src/NN.html`, 12 s timeout each; Chrome writes the PNG then hangs on exit, kill it). `src/diagram_style.py` holds the shared CSS, `src/shots/` the Qollab screenshots and the two demo charts, `src/cz_series.json` the real per-day cz error for slide 3. Figures come from `../../figures/`.

## Ian's instructions for the slides (apply before assembling)
1. White, black hairline cards, Helvetica, no colour. Simple, not cringe, as few words as possible.
2. Every title sits at the top-left at the same height on every slide; the content is centred in the space below. (Done in the current render; verify.)
3. Caption words only where they make the slide clearer; otherwise none. The current captions are already cut down; cut further if a line adds nothing.
4. No footer line. Files are just 01 to 17.
5. Visual check done at 16:10 on all 17: titles top-left at one height, content centred, nothing clipped or bleeding, slide 13's legend moved above the strip, slides 1 and 16 centred. Re-check only if you re-render.
6. Fill the frame: no slide should be mostly empty.
7. Slides must show the results: 7 (demo regret chart), 9 (drift value), 10 (best arm per day, all five circuits), 11 (regret table), 12 (regret curves, all five circuits), 13 (proxy validation), 14 (IonQ-like run), 15 (spot check), 16 (median-chain caveat).

## Ian's instructions for the script
- One continuous spoken explanation, not seventeen captions; each block leads into the next.
- In Ian's voice (plain, first person, mechanism then consequence, no hype, no dashes).
- Introduce the problem properly before the three tricks; say why a bandit is the answer.
- Under 3:00 when read aloud.

## Assembling (iMovie, 15 min)
1. New movie, drag `01.png` … `17.png` in order. Select all: crop = Fit, Ken Burns off.
2. Set each clip's duration from CUES.md.
3. Record the voiceover (microphone button above the timeline) reading SCRIPT.md straight through; nudge clip lengths to match.
4. Export 1080p. YouTube, Unlisted, title "AutoMitigate: a bandit that learns your error-mitigation settings (Qollab + IonQ hackathon 2026)". Open the link in an incognito window to confirm it plays.
5. Put the link into README.md (top line placeholder) and the Qollab project card, commit `[thomas] video link`, push.

## Rest of Sunday
Upload the latest `qollab_project.zip` to the Qollab project (erase first, unpack), Run once; 16:00 Publish; 16:15 incognito check; 17:00 Submit.
