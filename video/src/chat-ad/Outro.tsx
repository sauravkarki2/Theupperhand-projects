import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, EASE_OUT } from "./theme";
import { MONO, SANS } from "../shared/fonts";
import { OUTRO } from "./script";
import { Mark } from "./primitives";

/** Closing lockup. `local` is frames since the outro began. */
export const Outro: React.FC<{ local: number }> = ({ local }) => {
  const { fps } = useVideoConfig();
  useCurrentFrame();

  const line = (i: number) =>
    spring({
      frame: local - 4 - i * 7,
      fps,
      config: { damping: 13, stiffness: 175, mass: 0.68 },
    });

  const kicker = interpolate(local, [26, 42], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const rule = interpolate(local, [24, 44], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const lockup = interpolate(local, [36, 52], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "0 84px",
      }}
    >
      {OUTRO.headline.map((text, i) => {
        const s = line(i);
        return (
          <div
            key={text}
            style={{
              fontFamily: SANS,
              fontWeight: 900,
              fontSize: 96,
              lineHeight: 1.06,
              letterSpacing: "-0.04em",
              color: i === OUTRO.headline.length - 1 ? COLORS.accent : COLORS.fg,
              opacity: interpolate(s, [0, 0.5], [0, 1], {
                extrapolateRight: "clamp",
              }),
              transform: `translateY(${interpolate(s, [0, 1], [46, 0])}px)`,
            }}
          >
            {text}
          </div>
        );
      })}

      <div
        style={{
          height: 2,
          backgroundColor: COLORS.border,
          margin: "40px 0 26px",
          transform: `scaleX(${rule})`,
          transformOrigin: "left center",
        }}
      />

      <div
        style={{
          fontFamily: MONO,
          fontWeight: 500,
          fontSize: 26,
          letterSpacing: "0.16em",
          textTransform: "uppercase",
          color: COLORS.muted,
          opacity: kicker,
          transform: `translateY(${interpolate(kicker, [0, 1], [14, 0])}px)`,
        }}
      >
        {OUTRO.kicker}
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 18,
          marginTop: 78,
          opacity: lockup,
          transform: `translateY(${interpolate(lockup, [0, 1], [16, 0])}px)`,
        }}
      >
        <Mark size={40} />
        <div
          style={{
            fontFamily: SANS,
            fontWeight: 600,
            fontSize: 32,
            letterSpacing: "0.03em",
            color: COLORS.fg,
          }}
        >
          {OUTRO.wordmark}
        </div>
      </div>
    </div>
  );
};
