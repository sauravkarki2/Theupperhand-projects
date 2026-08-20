import { AbsoluteFill, Easing, Interactive, interpolate, OffthreadVideo, staticFile, useCurrentFrame } from "remotion";

export const SceneOpener: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0d12" }}>
      <AbsoluteFill>
        <OffthreadVideo
          name="Live action plate"
          src={staticFile("opener.mp4")}
          trimBefore={18}
          muted
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          background: "linear-gradient(90deg, rgba(11,13,18,0.92) 0%, rgba(11,13,18,0.72) 45%, rgba(11,13,18,0.15) 100%)",
        }}
      />

      <AbsoluteFill style={{ justifyContent: "center", padding: 160 }}>
        <Interactive.Div
          name="Hook line one"
          style={{
            fontFamily: "sans-serif",
            fontSize: 128,
            fontWeight: 700,
            letterSpacing: -5,
            lineHeight: 1,
            color: "#9aa5b4",
            opacity: interpolate(frame, [6, 18], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
            }),
            translate: interpolate(frame, [6, 24], ["0px 40px", "0px 0px"], {
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
            fontSize: 128,
            fontWeight: 700,
            letterSpacing: -5,
            lineHeight: 1,
            marginTop: 12,
            color: "#ffffff",
            opacity: interpolate(frame, [18, 30], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
            }),
            translate: interpolate(frame, [18, 36], ["0px 40px", "0px 0px"], {
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
            width: 220,
            height: 10,
            borderRadius: 5,
            marginTop: 40,
            backgroundColor: "#6366f1",
            scale: interpolate(frame, [28, 46], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
              output: "perceptual-scale",
            }),
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
