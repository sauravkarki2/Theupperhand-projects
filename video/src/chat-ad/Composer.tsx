import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { BEAT, COLORS, EASE_OUT, EASE_SNAP } from "./theme";
import { MONO } from "./fonts";
import { Cursor } from "./primitives";
import { PROMPT } from "./script";

/**
 * The input bar. Types the prompt out character by character, then empties on
 * send with a short press on the submit key.
 */
export const Composer: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sent = frame >= BEAT.send;

  const chars = Math.round(
    interpolate(frame, [BEAT.promptStart, BEAT.promptEnd], [0, PROMPT.length], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: EASE_SNAP,
    }),
  );
  const typed = sent ? "" : PROMPT.slice(0, chars);

  // Submit key: fills with accent once there is text, then takes a quick press.
  const armed = interpolate(frame, [BEAT.promptStart + 4, BEAT.promptStart + 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const press = spring({
    frame: frame - BEAT.send,
    fps,
    config: { damping: 12, stiffness: 320, mass: 0.5 },
  });
  const pressScale =
    frame < BEAT.send ? 1 : interpolate(press, [0, 1], [0.82, 1]);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 20,
        padding: "22px 22px 22px 30px",
        border: `1px solid ${COLORS.border}`,
        backgroundColor: COLORS.panel,
      }}
    >
      <div
        style={{
          flex: 1,
          minWidth: 0,
          fontFamily: MONO,
          fontWeight: 500,
          fontSize: 27,
          letterSpacing: "-0.01em",
          color: typed.length > 0 ? COLORS.fg : COLORS.muted,
          whiteSpace: "nowrap",
          overflow: "hidden",
        }}
      >
        {typed.length > 0 ? typed : "Ask anything"}
        <Cursor height={30} />
      </div>

      <div
        style={{
          flexShrink: 0,
          width: 56,
          height: 56,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: `rgba(184, 255, 46, ${0.12 + armed * 0.88})`,
          transform: `scale(${pressScale})`,
        }}
      >
        <svg width={24} height={24} viewBox="0 0 24 24" fill="none">
          <title>Send</title>
          <path
            d="M12 20V5m0 0-7 7m7-7 7 7"
            stroke={armed > 0.5 ? COLORS.bg : COLORS.muted}
            strokeWidth={2.4}
            strokeLinecap="square"
          />
        </svg>
      </div>
    </div>
  );
};
