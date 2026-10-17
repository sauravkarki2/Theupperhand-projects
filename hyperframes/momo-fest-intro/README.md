# Momo Festival intro — first 10s (HyperFrames)

HyperFrames edit of the first 10 seconds of `VID-20261016-WA0001.mp4` (vertical 1080×1920).

| Time | What happens |
| --- | --- |
| 0–1.06s | Slow push-in on the room shot |
| 1.06–3.46s | Punch-in on the namaste gesture; word-pop captions **JWAJALAPA / NAMASTE** + "Hello, everyone!" |
| 3.46–4.1s | Ease back out |
| 4.1–6.1s | White flash → **background swap**: speaker matted onto a crimson→blue (Nepal flag) gradient with scrolling "MOMO • KE CHA?" outline type behind him; caption **KE CHA?** ("How's everyone doing?") |
| 6.1s | Flash + punch-out back into the room |
| 7.84s | **TODAY...** pop caption |
| 8.6–10s | Punch-in + **INTERNATIONAL MOMO FESTIVAL** lower-third with shine sweep |

Color grade (both the a-roll and the matted subject): `skin-soft` preset at 0.72, with more contrast, highlights pulled down, warmer, a little more vibrance, and a light vignette. It is applied through `hyperframes media-treatment` as `data-color-grading`.

- `first10.mp4` is the source trimmed to 10s, re-encoded to H.264 30fps.
- `assets/subject.webm` is the speaker with the background removed (`hyperframes remove-background`, u2net_human_seg).
- `renders/momo-fest-intro-first10.mp4` is the rendered output.

```bash
npx hyperframes@0.8.167 preview   # edit in Studio
npx hyperframes@0.8.167 render    # re-render
```
