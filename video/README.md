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
