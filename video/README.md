# Remotion video

<p align="center">
  <a href="https://github.com/remotion-dev/logo">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://github.com/remotion-dev/logo/raw/main/animated-logo-banner-dark.apng">
      <img alt="Animated Remotion Logo" src="https://github.com/remotion-dev/logo/raw/main/animated-logo-banner-light.gif">
    </picture>
  </a>
</p>

Welcome to your Remotion project!

## Commands

**Install Dependencies**

```console
npm i
```

**Start Preview**

```console
npm run dev
```

**Render video**

```console
npx remotion render
```

**Upgrade Remotion**

```console
npx remotion upgrade
```

## Docs

Get started with Remotion by reading the [fundamentals page](https://www.remotion.dev/docs/the-fundamentals).

## Help

We provide help on our [Discord server](https://discord.gg/6VzzNDwUwV).

## Issues

Found an issue with Remotion? [File an issue here](https://github.com/remotion-dev/remotion/issues/new).

## License

Note that for some entities a company license is needed. [Read the terms here](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md).

## Rendering in Claude Code cloud sessions

Remotion normally downloads its own Chrome Headless Shell from `remotion.media`
on the first render. That host is blocked by the cloud environment's network
egress policy, so the download fails with a 403. Point Remotion at the Chromium
that is already installed in the image instead:

```console
npx remotion render TitleCard out/title-card.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
```

The flag is unnecessary on a local machine, where the download works normally.
Alternatively, add `remotion.media` (and `remotion.dev` for docs lookups) to the
environment's allowed hosts.

## The live-action opener plate

`SceneOpener` expects a clip at `public/opener.mp4` — the live-action plate the
hook text sits over. It is not committed; supply it before rendering `SaasAd`,
or the render fails with a 404 for that file.

The current plate was generated with Higgsfield (Seedance 2.0, 4s, 1080p, 16:9,
silent). Downloading it inside a cloud session requires Higgsfield's CDN host to
be added to the environment's allowed hosts; otherwise download it on a machine
with open network access and drop it in `public/`.

`trimBefore={18}` skips the first 0.6s of the plate so the shot is already
moving when the ad starts. Adjust to taste.

## The `ChatAd` composition

A 13-second, 1080x1080 product demo for an AI assistant: a prompt is typed and
sent, the model thinks, and the answer streams in word by word with a
kinetic-typography treatment. Source lives in `src/chat-ad/`.

```console
npx remotion render ChatAd out/chat-ad.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \
  --codec=h264 --crf=18
```

### Editing it

Almost everything worth changing lives in two files:

- `script.ts` — the prompt, the answer, and the closing lockup. Wrap a phrase in
  `[[double brackets]]` to mark it as a *punch* phrase: punch phrases are
  rendered as the large accent headline of their bullet, and everything else in
  that bullet becomes the smaller supporting line. Word counts feed the stream
  timing automatically, so re-writing the copy re-times the animation.
- `theme.ts` — palette, canvas size, duration, and the `BEAT` map. Every
  animation in the piece is derived from those beat frames, so retiming the ad
  means editing that one object.

`timing.ts` turns the beats plus the word counts into a per-word reveal
schedule (`WORD_STEP`, `BLOCK_GAP`). If the copy grows, check that the last
word still lands before `BEAT.streamEnd`.

### Fonts

Inter and JetBrains Mono are embedded as base64 woff2 in `fonts-data.ts` and
registered through the `FontFace` API in `fonts.ts`, behind a `delayRender()`
gate. Nothing is fetched at render time, so the render is unaffected by the
network egress policy and no frame can rasterise against a fallback face.

### Provenance of the UI

The chat UI is adapted from two 21st.dev components by `@elements-`:
[`message-bubble`](https://21st.dev/@elements-/components/message-bubble) and
[`streaming-text`](https://21st.dev/@elements-/components/streaming-text).

Both ship as React components that animate on wall-clock time — `useState` plus
`requestAnimationFrame` for the token reveal, CSS `animate-pulse` for the
caret. Neither survives a Remotion render, where every frame is rasterised in
isolation and no wall-clock state accumulates. So the *design* was ported and
the *animation* rebuilt: layout, type scale, the squared mono chrome, the
inverted user block and the caret idiom are kept; the reveal is re-driven from
`useCurrentFrame()` so it is deterministic and seekable. Tailwind classes were
resolved to inline styles because this canvas is 1080px square, roughly 2.6x
the components' web type scale.

The assistant mark, the "Slate AI" name, and the closing wordmark are
placeholders — swap them in `primitives.tsx` and `script.ts`.

## The `Reel` composition

A 15-second, 1080x1920 vertical montage in the "AI agent product film" idiom —
black, warm amber bloom, glass UI, light streaks, slow camera. Source lives in
`src/reel/`.

```console
npx remotion render Reel out/upper-hand-reel.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \
  --codec=h264 --crf=17
```

### The four shots

| Frames | Shot |
|---|---|
| 0–82 | Glowing cube, white |
| 74–246 | Agent IDE — held wide, then one long push into the task rail |
| ~224–276 | Light-streak flood: the frame blows out to amber and the cut happens inside it |
| 252–340 | Composer bar close-up, mode menu opening |
| 336–396 | Cube again, amber |
| 392–450 | `THE UPPER HAND` lockup |

`theme.ts` holds the `SHOT` map that every shot boundary derives from, plus the
palette. Note the shots deliberately overlap: the flood peaks *across* the
IDE→composer cut, so light does the edit rather than a dissolve.

### How the look is built

There is no 3D renderer and no compositing app in the pipeline — it is all DOM
and SVG, driven from `useCurrentFrame()`:

- **Bloom** (`atmos.tsx`) is three stacked radial stops, not one. A single
  gradient falls off too evenly and reads as a flat disc; real bloom has a hot
  core, a wide mid and a long tail.
- **The cube** (`Cube.tsx`) is a CSS 3D box drawn twice — a heavily blurred copy
  underneath supplies bloom that follows the silhouette as it tumbles, with a
  sharp copy on top. A gradient-only glow stays circular and gives the trick
  away.
- **The streaks** (`Flood.tsx`) are SVG paths with `pathLength={1}`, so a short
  `strokeDasharray` segment can be walked along each curve with
  `strokeDashoffset` regardless of its real length. Each arc is stroked four
  times — ember halo, amber body, hot core, white centre.
- **Grain** is `feTurbulence` rendered at 270x480 and scaled up. At full
  resolution it is far too slow to rasterise 450 times, and the upscale gives a
  coarser, more filmic grain than per-pixel noise anyway.
- **The logo sheen** paints into each word's own text fill via
  `background-clip: text`. An overlay gradient with a blend mode lights the
  background between the letters too, which reads as a grey rectangle.

### The composer, and 21st.dev

`ComposerBar.tsx` is a port of [`ai-prompt-input`](https://21st.dev/@senommu/components/ai-prompt-input)
by **@senommu** on 21st.dev — "premium AI prompt composer with rotating
placeholders, floating toolbar, and Cursor-style model selector".

What survived the port is the *surface language*: the heavy `rounded-[1.75rem]`
two-pixel-bordered shell, removable tool chips above the field, a toolbar fenced
off by a top border with icon buttons left and send right, and the model pill
that splits a name from its modifiers (`Opus 4.5` · `High` · `Fast`). The model
list is trimmed from the component's own `DEFAULT_AI_MODELS`.

What did not survive is all ~2600 lines of behaviour. The original drives every
open, close and hover through framer-motion springs, `AnimatePresence` and
controlled React state — wall-clock animation that cannot work in a Remotion
render, where each frame is rasterised in isolation and no state accumulates
between them. Every transition here is instead a plain 0→1 number the caller
derives from the frame: `menu`, `chips`, `hovered`. This is the general rule for
pulling anything off 21st.dev into Remotion — **take the design, rebuild the
motion.**

The bar is drawn once at a fixed intrinsic width (`INTRINSIC = 1000`) and scaled
to fit by the `Composer` wrapper, so the version at the foot of the IDE pane and
the one filling the frame in shot 4 are provably the same object at two
distances, not two separately-tuned designs.

### What this is not

The piece is a study of a reel by **@jup.creatives** — same shot grammar and
grade, rebuilt from scratch with this project's own branding and content. The
original's second shot is a real screen recording of an IDE; here that UI is
rebuilt in DOM (`IdeWindow.tsx`, `ComposerBar.tsx`) so the camera can push into
it at any magnification without turning to mush. It is a generic agent IDE, not
a clone of any shipping product's chrome.

There is no audio. The reference is cut to music, which carries a lot of its
energy; this renders silent and wants a track laid under it.

## shadcn/ui components in this project

This is a Remotion project, not a Next.js app, but it now carries the shadcn
layout so registry components drop in unmodified:

```
components.json          # style: new-york, cssVariables, aliases
src/components/ui/       # vendored components land here
src/lib/utils.ts         # the standard `cn()` helper
```

`@/*` maps to `./src/*` in **two** places, and both are required:
`tsconfig.json` `paths` satisfies the typechecker, and a `resolve.alias` in
`remotion.config.ts` satisfies the bundler — Remotion resolves modules itself
and does not read tsconfig paths.

### The shadcn CLI does not work here

`npx shadcn@latest init` and `add` both fetch from `ui.shadcn.com`, which this
environment's egress policy blocks (403 at the proxy). The structure above was
created by hand instead. On an unrestricted machine the CLI would work normally
against this `components.json`.

### Two things to fix in every component you vendor

Remotion's own ESLint plugin catches both, and they are the same two problems
every time:

- **`@remotion/warn-native-media-tag`** — a bare `<img>` is not waited on, so
  frames rasterise before the image decodes and you get half-painted elements.
  Either swap it for Remotion's `<Img>`, or preload at the call site behind
  `delayRender()`; `GalleryDemo.tsx` does the latter so the vendored file stays
  pristine.
- **`@remotion/non-pure-animation`** — CSS transitions, `useState` hovers and
  framer-motion springs all animate on wall-clock time. Nothing hovers in a
  render and no state accumulates between frames, so these render frozen. Any
  motion has to be re-driven from `useCurrentFrame()`.

`src/components/ui/**` is excluded from lint so vendored files stay diffable
against upstream; the fixes live at the call site.
