import { AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame } from "remotion";

const NAV = ["Overview", "Revenue", "Funnel", "Cohorts", "Alerts"];
const BARS = [0.42, 0.58, 0.36, 0.71, 0.55, 0.86, 0.64];

export const SceneProduct: React.FC = () => {
  const frame = useCurrentFrame();

  const revenue = interpolate(frame, [12, 52], [0, 48.2], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const signups = interpolate(frame, [16, 54], [0, 1284], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const uptime = interpolate(frame, [20, 56], [0, 99.9], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0b0d12",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <Interactive.Div
        name="App window"
        style={{
          width: 1480,
          height: 830,
          borderRadius: 24,
          overflow: "hidden",
          backgroundColor: "#12151c",
          border: "1px solid #232833",
          boxShadow: "0 60px 120px rgba(0,0,0,0.55)",
          display: "flex",
          flexDirection: "column",
          opacity: interpolate(frame, [0, 12], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          scale: interpolate(frame, [0, 26], [0.9, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
            output: "perceptual-scale",
          }),
          translate: interpolate(frame, [0, 26], ["0px 60px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <div
          style={{
            height: 64,
            flexShrink: 0,
            borderBottom: "1px solid #232833",
            display: "flex",
            alignItems: "center",
            gap: 12,
            paddingLeft: 28,
          }}
        >
          <div style={{ width: 14, height: 14, borderRadius: 7, backgroundColor: "#3a4150" }} />
          <div style={{ width: 14, height: 14, borderRadius: 7, backgroundColor: "#3a4150" }} />
          <div style={{ width: 14, height: 14, borderRadius: 7, backgroundColor: "#3a4150" }} />
          <div style={{ fontFamily: "sans-serif", fontSize: 26, fontWeight: 600, color: "#7b8798", marginLeft: 24 }}>
            Slate
          </div>
        </div>

        <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
          <div
            style={{
              width: 280,
              flexShrink: 0,
              backgroundColor: "#0e1117",
              borderRight: "1px solid #232833",
              padding: 24,
            }}
          >
            {NAV.map((label, i) => (
              <div
                key={label}
                style={{
                  height: 62,
                  borderRadius: 12,
                  paddingLeft: 20,
                  display: "flex",
                  alignItems: "center",
                  fontFamily: "sans-serif",
                  fontSize: 27,
                  fontWeight: i === 0 ? 600 : 400,
                  color: i === 0 ? "#ffffff" : "#5c677a",
                  backgroundColor: i === 0 ? "#6366f1" : "transparent",
                  opacity: interpolate(frame, [10 + i * 4, 26 + i * 4], [0, 1], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  }),
                }}
              >
                {label}
              </div>
            ))}
          </div>

          <div style={{ flex: 1, padding: 40, display: "flex", flexDirection: "column", gap: 28 }}>
            <div style={{ display: "flex", gap: 24 }}>
              <StatTile label="Revenue" value={`$${revenue.toFixed(1)}k`} delay={12} accent />
              <StatTile label="Signups" value={Math.round(signups).toLocaleString()} delay={16} />
              <StatTile label="Uptime" value={`${uptime.toFixed(1)}%`} delay={20} />
            </div>

            <div
              style={{
                flex: 1,
                borderRadius: 18,
                border: "1px solid #232833",
                backgroundColor: "#0e1117",
                padding: 32,
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div style={{ fontFamily: "sans-serif", fontSize: 26, color: "#7b8798", marginBottom: 24 }}>
                Weekly active
              </div>
              <div style={{ flex: 1, display: "flex", alignItems: "flex-end", gap: 20 }}>
                {BARS.map((height, i) => (
                  <div
                    key={i}
                    style={{
                      flex: 1,
                      borderRadius: 10,
                      backgroundColor: i === 5 ? "#6366f1" : "#2b3242",
                      height: `${height * 100}%`,
                      scale: interpolate(frame, [20 + i * 3, 46 + i * 3], ["100% 0%", "100% 100%"], {
                        extrapolateLeft: "clamp",
                        extrapolateRight: "clamp",
                        easing: Easing.bezier(0.16, 1, 0.3, 1),
                      }),
                      transformOrigin: "bottom",
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </Interactive.Div>
    </AbsoluteFill>
  );
};

const StatTile: React.FC<{ label: string; value: string; delay: number; accent?: boolean }> = ({
  label,
  value,
  delay,
  accent,
}) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        flex: 1,
        borderRadius: 18,
        border: "1px solid #232833",
        backgroundColor: "#0e1117",
        padding: 28,
        opacity: interpolate(frame, [delay, delay + 14], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        }),
        translate: interpolate(frame, [delay, delay + 20], ["0px 24px", "0px 0px"], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
      }}
    >
      <div style={{ fontFamily: "sans-serif", fontSize: 24, color: "#5c677a", marginBottom: 12 }}>{label}</div>
      <div
        style={{
          fontFamily: "sans-serif",
          fontSize: 58,
          fontWeight: 700,
          letterSpacing: -1,
          color: accent ? "#818cf8" : "#e8ecf3",
        }}
      >
        {value}
      </div>
    </div>
  );
};
