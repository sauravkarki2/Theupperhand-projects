import { AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame } from "remotion";

export const SceneCta: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0b0d12",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <Interactive.Div
        name="Logo mark"
        style={{
          width: 128,
          height: 128,
          borderRadius: 32,
          marginBottom: 44,
          backgroundColor: "#6366f1",
          scale: interpolate(frame, [0, 18], [0.4, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.spring({ damping: 14 }),
            output: "perceptual-scale",
          }),
          rotate: interpolate(frame, [0, 22], ["-20deg", "0deg"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.spring({ damping: 14 }),
          }),
        }}
      >
        <div
          style={{
            width: 46,
            height: 46,
            borderRadius: 12,
            backgroundColor: "#ffffff",
            marginTop: 41,
            marginLeft: 41,
          }}
        />
      </Interactive.Div>
      <Interactive.Div
        name="Wordmark"
        style={{
          fontFamily: "sans-serif",
          fontSize: 140,
          fontWeight: 700,
          letterSpacing: -5,
          lineHeight: 1,
          color: "#ffffff",
          opacity: interpolate(frame, [6, 18], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(frame, [6, 22], ["0px 30px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        Slate
      </Interactive.Div>
      <Interactive.Div
        name="Tagline"
        style={{
          fontFamily: "sans-serif",
          fontSize: 62,
          fontWeight: 400,
          marginTop: 20,
          color: "#7b8798",
          opacity: interpolate(frame, [12, 24], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        Every metric. One screen.
      </Interactive.Div>
      <Interactive.Div
        name="CTA pill"
        style={{
          marginTop: 52,
          paddingTop: 26,
          paddingBottom: 26,
          paddingLeft: 62,
          paddingRight: 62,
          borderRadius: 100,
          fontFamily: "sans-serif",
          fontSize: 46,
          fontWeight: 600,
          color: "#0b0d12",
          backgroundColor: "#ffffff",
          opacity: interpolate(frame, [18, 28], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          scale: interpolate(frame, [18, 34], [0.86, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.spring({ damping: 16 }),
            output: "perceptual-scale",
          }),
        }}
      >
        Start free
      </Interactive.Div>
    </AbsoluteFill>
  );
};
