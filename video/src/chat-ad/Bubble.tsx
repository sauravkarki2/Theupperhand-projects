import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, EASE_OUT } from "./theme";
import { MONO, SANS } from "../shared/fonts";
import { Mark } from "./primitives";

/**
 * Ported from 21st.dev's `AiMessageBubble`. The structure is kept faithfully —
 * squared-off mono chrome, reversed row for the user, an inverted solid block
 * for the user's turn and bare foreground text for the assistant's, bordered
 * square avatars, uppercase tracked timestamp — but the Tailwind classes are
 * resolved to inline styles (this canvas is 1080px square, so the type scale is
 * roughly 2.6x the component's web sizing) and the hover/copy affordances are
 * dropped since nothing hovers in a render.
 */
export const Bubble: React.FC<{
  role: "user" | "assistant";
  appearAt: number;
  timestamp?: string;
  children: React.ReactNode;
}> = ({ role, appearAt, timestamp, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - appearAt;
  const isUser = role === "user";

  const enter = spring({
    frame: local,
    fps,
    config: { damping: 15, stiffness: 170, mass: 0.7 },
  });

  const opacity = interpolate(local, [0, 7], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  return (
    <div
      style={{
        display: "flex",
        gap: 20,
        flexDirection: isUser ? "row-reverse" : "row",
        alignItems: "flex-start",
        opacity,
        transform: `translateY(${interpolate(enter, [0, 1], [30, 0])}px)`,
      }}
    >
      <div
        style={{
          flexShrink: 0,
          width: 54,
          height: 54,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: `1px solid ${isUser ? "transparent" : COLORS.border}`,
          backgroundColor: isUser ? COLORS.fg : COLORS.panel,
        }}
      >
        {isUser ? (
          <svg width={24} height={24} viewBox="0 0 24 24" fill="none">
            <title>You</title>
            <path
              d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM4 21a8 8 0 0 1 16 0"
              stroke={COLORS.bg}
              strokeWidth={2}
              strokeLinecap="square"
            />
          </svg>
        ) : (
          <Mark size={26} />
        )}
      </div>

      <div
        style={{
          position: "relative",
          maxWidth: isUser ? "78%" : "100%",
          padding: isUser ? "20px 26px" : "2px 0 0",
          backgroundColor: isUser ? COLORS.fg : "transparent",
          color: isUser ? COLORS.bg : COLORS.fg,
        }}
      >
        <div
          style={{
            fontFamily: isUser ? MONO : SANS,
            fontSize: isUser ? 27 : undefined,
            fontWeight: isUser ? 500 : undefined,
            lineHeight: 1.45,
            letterSpacing: isUser ? "-0.01em" : undefined,
          }}
        >
          {children}
        </div>

        {timestamp ? (
          <div
            style={{
              marginTop: 14,
              fontFamily: MONO,
              fontSize: 17,
              textTransform: "uppercase",
              letterSpacing: "0.14em",
              opacity: 0.55,
            }}
          >
            {timestamp}
          </div>
        ) : null}
      </div>
    </div>
  );
};
