import { AbsoluteFill, interpolate } from "remotion";
import { C, EASE_OUT } from "./theme";
import { SANS } from "../shared/fonts";
import { Bloom } from "./atmos";

const WORDS = ["THE", "UPPER", "HAND"];

/**
 * Closing lockup. The words don't fade as a block — each clears its own wipe a
 * beat apart, and a sheen of light passes across the finished wordmark.
 */
export const Logo: React.FC<{ local: number }> = ({ local }) => {
  const sheen = interpolate(local, [22, 52], [-40, 140], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  const settle = interpolate(local, [0, 40], [1.06, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  const rule = interpolate(local, [30, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <Bloom x="50%" y="50%" size={520} intensity={0.16} color={C.ember} />

      <div style={{ transform: `scale(${settle})`, textAlign: "center" }}>
        <div
          style={{
            position: "relative",
            display: "flex",
            gap: 26,
            justifyContent: "center",
            overflow: "hidden",
            padding: "10px 0",
          }}
        >
          {WORDS.map((w, i) => {
            const up = interpolate(local, [4 + i * 6, 26 + i * 6], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: EASE_OUT,
            });
            // The sweep is painted into each word's own text fill rather than
            // laid over the row as a blend — an overlay lights the background
            // between the letters too, which reads as a grey rectangle.
            const s = sheen - i * 26;
            return (
              <div
                key={w}
                style={{
                  fontFamily: SANS,
                  fontWeight: 900,
                  fontSize: 78,
                  letterSpacing: "0.06em",
                  opacity: up,
                  transform: `translateY(${interpolate(up, [0, 1], [56, 0])}px)`,
                  backgroundImage: `linear-gradient(102deg, ${C.fg} ${s - 26}%, ${C.hot} ${s}%, ${C.fg} ${s + 26}%)`,
                  WebkitBackgroundClip: "text",
                  backgroundClip: "text",
                  color: "transparent",
                }}
              >
                {w}
              </div>
            );
          })}
        </div>

        <div
          style={{
            height: 1,
            marginTop: 26,
            backgroundColor: C.border,
            transform: `scaleX(${rule})`,
          }}
        />
        <div
          style={{
            marginTop: 22,
            fontFamily: SANS,
            fontWeight: 500,
            fontSize: 21,
            letterSpacing: "0.42em",
            color: C.faint,
            opacity: rule,
          }}
        >
          MOTION &amp; INTERFACE
        </div>
      </div>
    </AbsoluteFill>
  );
};
