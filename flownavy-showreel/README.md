# Flow Navy — motion graphics showreel

A 32-second, 1920×1080, 60 fps showreel. Every frame is generated in code: Canvas 2D handles the type, HUD and graphic scenes, and three.js handles the 3D ocean and tunnel. The soundtrack is synthesized in code too (120 BPM, D minor), with its hits placed on the video's cuts and slams. No generative video model or audio samples are used.

**Final video:** `out/flownavy_showreel.mp4`

- `index.html` / `main.js`: the composition. Open it through any static server to play it live (Space pauses, ← → seek).
- `storyboard/`: key frames, a contact sheet and shot notes (`node tools/storyboard.mjs`).

## Rendering

Needs Node 22 with Playwright (Chromium), Python 3 with numpy + scipy, and ffmpeg.

```sh
node tools/render.mjs 4          # frames → out/flownavy_showreel_silent.mp4 (4 parallel browsers)
python3 tools/soundtrack.py      # → out/soundtrack.wav
tools/mux.sh                     # → out/flownavy_showreel.mp4 (AAC 320k, −14 LUFS)
```

If ffmpeg isn't on `PATH`, set `FFMPEG=/path/to/ffmpeg` (for example, from `pip install imageio-ffmpeg`).

## Sound cues

| Time | Picture | Sound |
|---|---|---|
| 0:00–0:03 | Line of light, splits into currents | Low drone, rising shimmer, bell cascade, riser, reverse "suck" into the cut |
| 0:03 | Hard cut to flow field | Impact; four-on-the-floor groove, bass and pad start |
| 0:07–0:10 | MOVE / SHAPE / GUIDE / FLOW slams | Impact and a chord stab on each slam |
| 0:07, 0:11, 0:15 | Diagonal wipes | Whooshes |
| 0:11–0:15 | 3D ocean | Breakdown: sub swells, sparse hats, wave-like noise swell, riser back in |
| 0:15–0:19 | Navigation HUD | Groove returns; radar pings; data ticks while coordinates unscramble |
| 0:19–0:23 | 8-cut montage | A pitched pluck and blip on every cut |
| 0:23–0:26.5 | 3D tunnel | Accelerating snare roll, pitched riser, a whoosh per zooming word, white-out swell |
| 0:26.5 | Iris into the emblem | Big kick and impact, sub drop, open pad |
| 0:27.3–0:29 | Notch, waves, letters, tagline, URL | Bell on the notch, whooshes on the waves, a note per letter, bells on the tagline and URL; fade out |
