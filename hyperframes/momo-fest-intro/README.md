# Momo Festival vlog edit (HyperFrames)

HyperFrames edit of `VID-20261016-WA0001.mp4` (vertical 1080×1920, 148.5s). The first 10s were built first; the rest continues in the same style.

| Time | What happens |
| --- | --- |
| 0–1.06s | Slow push-in on the room shot |
| 1.06–3.46s | Punch-in on the namaste gesture; word-pop captions **JWAJALAPA / NAMASTE** + "Hello, everyone!" |
| 3.46–4.1s | Ease back out |
| 4.1–6.1s | White flash → **background swap**: speaker matted onto a crimson→blue (Nepal flag) gradient with scrolling "MOMO • KE CHA?" outline type behind him; caption **KE CHA?** ("How's everyone doing?") |
| 6.1s | Flash + punch-out back into the room |
| 7.84s | **TODAY...** pop caption |
| 8.6–10s | Punch-in + **INTERNATIONAL MOMO FESTIVAL** lower-third with shine sweep |

### 10s → end

| Time | What happens |
| --- | --- |
| throughout | Zoom rhythm: a new framing (wide / medium / tight) punches in at each phrase, with a slow drift inside it; saffron progress bar across the top |
| 10–12.8s | "International Momo Festival" card holds, then exits |
| 15.4s | Subtitle: "I'm making this video today." |
| 30.3–41.7s | Kinetic title **INTERNATIONAL / DUMPLING / FESTIVAL** + "I'm here at the International Dumpling Festival." |
| 42.2s | Subtitle: "I'm so grateful to all of you." |
| 48.6–61.2s | Background swap (picture-in-picture card on the crimson/blue backdrop, "THANK YOU • DHANYABAD" type): **HUGE THANKS** "to the International Dumpling Festival team" |
| 63.8s | Animated momo sticker |
| 109.2s | Subtitle: "Please give us your blessings." |
| 119–128.6s | Background swap (PiP card, "MOMO • DUMPLINGS" type): **MOMOS!** "We ate momos and taught the kids how to make them." |
| 135.7–141.3s | Location lower-third: 📍 **QUEEN VICTORIA MARKET** · International Dumpling Festival |
| 143.6–148.5s | Outro swap: **THANK YOU!** "Thanks so much for watching." then fade to black |

Captions after 10s come from a machine translation of the Nepali audio (Whisper small, two passes cross-checked) and only appear where the passes agreed. Long stretches (≈63–108s) are left uncaptioned on purpose rather than guessed. **Review before publishing:** "Queen Victoria Market" is inferred from "Queens Victoria", and the speaker also names team members (heard as "Raju" and "Maniz") who are left out of the thank-you caption.

`assets/a-roll-full-graded.mp4` is the full video at 30fps with the same baked grade.

Color grade (both the a-roll and the matted subject): `skin-soft` preset at 0.72, with more contrast, highlights pulled down, warmer, a little more vibrance, and a light vignette on the a-roll.
The grade was designed with `hyperframes media-treatment` / `grade-compare`, then **baked into the footage** so rendering doesn't need WebGL (in a GPU-less container the live shader grade took ~95 min per render; baked, it takes ~40s):

- `assets/festival-warm.cube` is a 33³ LUT fitted to HyperFrames' own graded frame (mean error ≈0.5/255), applied with ffmpeg `lut3d`, plus `vignette=angle=0.24` on the a-roll.
- `assets/a-roll-graded.mp4` is the source trimmed to 10s (`first10.mp4`) with the grade baked in.
- `assets/subject-graded.webm` is the speaker with the background removed (`hyperframes remove-background`, u2net_human_seg → `assets/subject.webm`), graded, alpha kept.
- `renders/momo-fest-intro-first10.mp4` is the first-10s render; `renders/momo-fest-full.mp4` is the full edit (1080×1920, 30fps, 148.5s, ~3.8 Mbps).

On a machine with a GPU you can switch back to the live, editable grade: point the `<video>` tags at `first10.mp4` / `assets/subject.webm` and re-apply it with `hyperframes media-treatment --selector "#a-roll" --grading '<json>' --apply`.

```bash
npx hyperframes@0.8.167 preview   # edit in Studio
npx hyperframes@0.8.167 render    # re-render
```
