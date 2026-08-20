import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, EASE_DRIFT, EASE_OUT } from "./theme";
import { Bloom } from "./atmos";

const FACE = 128;

/** Static per-face shading. With a slow tumble, fixed face values read as a
 *  lit solid — cheaper and steadier than computing a normal per frame. */
const FACES: { transform: string; bg: string }[] = [
  { transform: `translateZ(${FACE / 2}px)`, bg: "#F2F2F4" },
  { transform: `rotateY(90deg) translateZ(${FACE / 2}px)`, bg: "#9C9CA4" },
  { transform: `rotateY(180deg) translateZ(${FACE / 2}px)`, bg: "#C9C9CF" },
  { transform: `rotateY(-90deg) translateZ(${FACE / 2}px)`, bg: "#B4B4BC" },
  { transform: `rotateX(90deg) translateZ(${FACE / 2}px)`, bg: "#FFFFFF" },
  { transform: `rotateX(-90deg) translateZ(${FACE / 2}px)`, bg: "#7E7E86" },
];

const Solid: React.FC<{ rx: number; ry: number; scale: number }> = ({
  rx,
  ry,
  scale,
}) => (
  <div
    style={{
      width: FACE,
      height: FACE,
      position: "relative",
      transformStyle: "preserve-3d",
      transform: `scale(${scale}) rotateX(${rx}deg) rotateY(${ry}deg)`,
    }}
  >
    {FACES.map((f, i) => (
      <div
        key={i}
        style={{
          position: "absolute",
          inset: 0,
          backgroundColor: f.bg,
          transform: f.transform,
        }}
      />
    ))}
  </div>
);

/**
 * The bookend shot. The cube is drawn twice: a heavily blurred copy underneath
 * supplies real bloom that follows the geometry as it tumbles, and a sharp copy
 * sits on top. A gradient-only glow can't do that — it stays circular while the
 * silhouette changes.
 */
export const Cube: React.FC<{
  local: number;
  duration: number;
  tint?: string;
}> = ({ local, duration, tint = C.hot }) => {
  useCurrentFrame();

  const rx = -22 + local * 0.09;
  const ry = 34 + local * 0.16;

  // Breathes very slightly, and drifts closer across the shot.
  const scale = interpolate(local, [0, duration], [0.86, 1.06], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_DRIFT,
  });

  const born = interpolate(local, [0, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const out = interpolate(local, [duration - 18, duration], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const alive = born * out;

  const pulse = 1 + Math.sin(local / 21) * 0.06;

  return (
    <AbsoluteFill style={{ opacity: alive }}>
      <Bloom
        x="50%"
        y="50%"
        size={400 * pulse}
        intensity={0.5 * alive}
        color={tint}
      />

      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          perspective: 900,
        }}
      >
        {/* Bloom source: the same geometry, blurred and tinted. */}
        <div
          style={{
            position: "absolute",
            filter: `blur(26px) saturate(${tint === C.hot ? 1 : 2.2})`,
            opacity: 0.95,
            transformStyle: "preserve-3d",
          }}
        >
          <Solid rx={rx} ry={ry} scale={scale * 1.16} />
        </div>

        <div style={{ position: "absolute", transformStyle: "preserve-3d" }}>
          <Solid rx={rx} ry={ry} scale={scale} />
        </div>
      </AbsoluteFill>

      {/* A tighter core pass on top seals the hot centre. */}
      <Bloom x="50%" y="50%" size={150 * pulse} intensity={0.4 * alive} color={tint} />
    </AbsoluteFill>
  );
};
