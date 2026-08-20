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
