import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, EASE_OUT } from "./theme";
import { SANS } from "../shared/fonts";

/**
 * One streamed word.
 *
 * Ported from 21st.dev's `AiStreamingText`, which reveals tokens on a
 * `requestAnimationFrame` timer. That approach can't survive a Remotion
 * render — every frame is rasterised in isolation, so wall-clock state never
 * accumulates. The tokenisation and caret idiom are kept; the reveal is
 * re-driven from `useCurrentFrame()` so it is deterministic and seekable.
 */
export const Word: React.FC<{
  text: string;
  punch: boolean;
  appearAt: number;
  size: number;
  color?: string;
  isLast?: boolean;
}> = ({ text, punch, appearAt, size, color = COLORS.fg, isLast = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - appearAt;

  const enter = spring({
    frame: local,
    fps,
    config: punch
      ? { damping: 11, stiffness: 190, mass: 0.62 }
      : { damping: 200, stiffness: 180, mass: 0.5 },
  });

  const opacity = interpolate(local, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  const blur = interpolate(local, [0, 9], [punch ? 14 : 8, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  const y = interpolate(enter, [0, 1], [punch ? 26 : 14, 0]);
  const scale = interpolate(enter, [0, 1], [punch ? 0.72 : 0.94, 1]);


  return (
    <span
      style={{
        display: "inline-block",
        position: "relative",
        marginRight: isLast ? 0 : punch ? size * 0.26 : size * 0.24,
        opacity,
        filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
        transform: `translateY(${y}px) scale(${scale})`,
        transformOrigin: "left bottom",
        fontFamily: SANS,
        fontWeight: punch ? 900 : 400,
        fontSize: punch ? size * 1.16 : size,
        lineHeight: 1.34,
        letterSpacing: punch ? "-0.028em" : "-0.011em",
        color: punch ? COLORS.accent : color,
        whiteSpace: "pre",
      }}
    >
      {text}
    </span>
  );
};
