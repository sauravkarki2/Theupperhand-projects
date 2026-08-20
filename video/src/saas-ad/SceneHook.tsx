import { AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame } from "remotion";

export const SceneHook: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0b0d12",
        justifyContent: "center",
        padding: 160,
      }}
    >
      <Interactive.Div
        name="Hook line one"
        style={{
          fontFamily: "sans-serif",
          fontSize: 156,
          fontWeight: 700,
          letterSpacing: -6,
          lineHeight: 1,
          color: "#7b8798",
          opacity: interpolate(frame, [0, 10], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(frame, [0, 16], ["0px 50px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        Six tools.
      </Interactive.Div>
      <Interactive.Div
        name="Hook line two"
        style={{
          fontFamily: "sans-serif",
          fontSize: 156,
          fontWeight: 700,
          letterSpacing: -6,
          lineHeight: 1,
          marginTop: 16,
          color: "#ffffff",
          opacity: interpolate(frame, [12, 24], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(frame, [12, 30], ["0px 50px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        One dashboard.
      </Interactive.Div>
      <Interactive.Div
        name="Hook underline"
        style={{
          width: 240,
          height: 10,
          borderRadius: 5,
          marginTop: 48,
          backgroundColor: "#6366f1",
          scale: interpolate(frame, [20, 40], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
            output: "perceptual-scale",
          }),
        }}
      />
    </AbsoluteFill>
  );
};
