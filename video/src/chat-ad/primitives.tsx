import { useCurrentFrame } from "remotion";
import { COLORS } from "./theme";

/**
 * Frame-driven caret. The 21st.dev components blink theirs with a CSS
 * `animate-pulse`, which is wall-clock based and would render inconsistently
 * across Remotion's independently-rasterised frames — so the blink is derived
 * from the frame number instead.
 */
export const Cursor: React.FC<{
  height: number;
  color?: string;
  width?: number;
}> = ({ height, color = COLORS.accent, width = 3 }) => {
  const frame = useCurrentFrame();
  const lit = Math.floor(frame / 8) % 2 === 0;
  return (
    <span
      style={{
        display: "inline-block",
        width,
        height,
        backgroundColor: color,
        opacity: lit ? 1 : 0.05,
        verticalAlign: "middle",
        marginLeft: 4,
        transform: "translateY(-1px)",
      }}
    />
  );
};

/** Unbranded assistant mark — a squared-off aperture, drawn to match the
 *  mono/brutalist language of the 21st.dev bubble it sits next to. */
export const Mark: React.FC<{ size: number; color?: string }> = ({
  size,
  color = COLORS.accent,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <title>Assistant</title>
    <path
      d="M4 4h7v3H7v10h10v-4h3v7H4V4Z"
      fill={color}
      fillOpacity={0.55}
    />
    <path d="M13 4h7v7h-3V7h-4V4Z" fill={color} />
    <rect x="10.5" y="10.5" width="3" height="3" fill={color} />
  </svg>
);
