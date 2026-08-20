import { AbsoluteFill, Composition, Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const MyComposition = () => {
  return (
    <Composition
      id="TitleCard"
      component={TitleCard}
      durationInFrames={150}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};

export const TitleCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0d0f12",
        justifyContent: "center",
        padding: 160,
      }}
    >
      <Interactive.Div
        name="Accent bar"
        style={{
          width: 120,
          height: 10,
          borderRadius: 5,
          marginBottom: 48,
          backgroundColor: "#e8552d",
          scale: interpolate(frame, [0, fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.spring({ damping: 200 }),
            output: "perceptual-scale",
          }),
        }}
      />
      <Interactive.Div
        name="Headline"
        style={{
          fontFamily: "sans-serif",
          fontSize: 150,
          fontWeight: 700,
          letterSpacing: -4,
          lineHeight: 1.05,
          color: "#ffffff",
          opacity: interpolate(frame, [6, 30], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(frame, [6, 36], ["0px 60px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        The Upper Hand
      </Interactive.Div>
      <Interactive.Div
        name="Subtitle"
        style={{
          fontFamily: "sans-serif",
          fontSize: 78,
          fontWeight: 400,
          marginTop: 32,
          color: "#9aa3ad",
          opacity: interpolate(frame, [24, 54], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(frame, [24, 60], ["0px 40px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        Motion design that moves product
      </Interactive.Div>
    </AbsoluteFill>
  );
};
