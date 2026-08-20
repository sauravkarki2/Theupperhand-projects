import { Easing } from "remotion";

export const FPS = 30;
export const SIZE = 1080;
export const DURATION = 390; // 13s

export const COLORS = {
  bg: "#08090A",
  panel: "#0E1011",
  border: "#22262A",
  fg: "#F2F3F4",
  muted: "#6B7280",
  accent: "#B8FF2E",
};

/** Standard "settle" curve — fast out, long gentle landing. */
export const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);
/** Sharper curve for UI chrome that should feel mechanical, not soft. */
export const EASE_SNAP = Easing.bezier(0.4, 0, 0.1, 1);

/** Beat markers, in frames. The whole timeline is driven from these. */
export const BEAT = {
  promptStart: 6,
  promptEnd: 50,
  send: 54,
  thinkStart: 66,
  streamStart: 88,
  streamEnd: 300,
  outroStart: 310,
};
