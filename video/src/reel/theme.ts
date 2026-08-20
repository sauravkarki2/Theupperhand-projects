import { Easing } from "remotion";

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const DURATION = 450; // 15s

/**
 * Near-monochrome black with a single warm light source. Everything that
 * "glows" in this piece is one of the amber values below at some intensity —
 * there is no second hue anywhere, which is what keeps it feeling lit rather
 * than coloured.
 */
export const C = {
  black: "#000000",
  ink: "#08080A",
  panel: "#141416",
  panelHi: "#1D1D20",
  border: "#2A2A2E",
  fg: "#EDEDEF",
  dim: "#8A8A92",
  faint: "#55555C",

  hot: "#FFF6E8", // white-hot core of a light source
  amber: "#FFA53A",
  ember: "#C25E12",
  deep: "#6A2E05",
};

export const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);
export const EASE_IN_OUT = Easing.bezier(0.65, 0, 0.35, 1);
/** Long, almost-linear drift used for the slow camera pushes. */
export const EASE_DRIFT = Easing.bezier(0.4, 0.05, 0.55, 0.98);

/**
 * Shot boundaries in frames. Shots overlap deliberately — the flood peaks
 * across the IDE→composer cut so the light, not a dissolve, does the joining.
 */
export const SHOT = {
  cubeIn: 0,
  cubeOut: 82,

  ideIn: 74,
  ideOut: 246,

  floodPeak: 250,

  composerIn: 252,
  composerOut: 340,

  emberIn: 336,
  emberOut: 396,

  logoIn: 392,
  logoOut: 450,
};
