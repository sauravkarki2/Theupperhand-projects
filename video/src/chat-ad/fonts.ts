import { continueRender, delayRender } from "remotion";
import { INTER_400, INTER_600, INTER_900, MONO_500 } from "./fonts-data";

export const SANS = "AdInter";
export const MONO = "AdMono";

const FACES: [string, string, number][] = [
  [SANS, INTER_400, 400],
  [SANS, INTER_600, 600],
  [SANS, INTER_900, 900],
  [MONO, MONO_500, 500],
];

let started = false;

/**
 * Registers the inlined woff2 faces and holds the render until they are
 * usable, so no frame is ever rasterised against a fallback font. Safe to call
 * from several components — the work only happens once per page.
 */
export const loadAdFonts = () => {
  if (started || typeof document === "undefined") {
    return;
  }
  started = true;

  const handle = delayRender("Loading chat-ad fonts");

  Promise.all(
    FACES.map(([family, src, weight]) => {
      const face = new FontFace(family, `url(${src}) format("woff2")`, {
        weight: String(weight),
        style: "normal",
      });
      return face.load().then((loaded) => {
        document.fonts.add(loaded);
      });
    }),
  )
    .then(() => document.fonts.ready)
    .then(() => continueRender(handle))
    .catch(() => continueRender(handle));
};
