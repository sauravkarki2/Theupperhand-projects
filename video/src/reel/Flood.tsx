import { AbsoluteFill, interpolate } from "remotion";
import { C, EASE_IN_OUT, EASE_OUT } from "./theme";
import { HEIGHT, WIDTH } from "./theme";

type Arc = { d: string; w: number; delay: number; len: number };

/** Hand-placed so the arcs rake across the frame at different angles and
 *  speeds rather than reading as one radial burst. */
const ARCS: Arc[] = [
  { d: "M -180 900 Q 380 560 1220 820", w: 13, delay: 0.0, len: 0.26 },
  { d: "M 1260 700 Q 640 380 -120 690", w: 10, delay: 0.07, len: 0.22 },
  { d: "M -140 1180 Q 520 820 1240 1090", w: 16, delay: 0.04, len: 0.3 },
  { d: "M 1200 1020 Q 560 700 -80 960", w: 8, delay: 0.16, len: 0.18 },
  { d: "M -100 620 Q 600 940 1220 640", w: 11, delay: 0.11, len: 0.24 },
  { d: "M 240 1420 Q 700 1020 1120 1320", w: 7, delay: 0.2, len: 0.17 },
];

const Streak: React.FC<{ arc: Arc; t: number }> = ({ arc, t }) => {
  const p = interpolate(t, [arc.delay, arc.delay + 0.62], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_IN_OUT,
  });
  // Travels from just off the head of the path to past its tail.
  const offset = interpolate(p, [0, 1], [1 + arc.len, -arc.len]);
  const fade = interpolate(p, [0, 0.12, 0.8, 1], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  if (fade <= 0.001) {
    return null;
  }

  // Three passes: a wide soft halo, a mid body, and a thin hot core.
  const passes: [number, string, number, number][] = [
    [arc.w * 7, C.ember, 34, 1],
    [arc.w * 3.2, C.amber, 14, 1],
    [arc.w * 1.3, C.hot, 4, 1],
    [arc.w * 0.5, "#FFFFFF", 0, 1],
  ];

  return (
    <g opacity={fade}>
      {passes.map(([w, color, blur, op], i) => (
        <path
          key={i}
          d={arc.d}
          fill="none"
          stroke={color}
          strokeWidth={w}
          strokeLinecap="round"
          opacity={op}
          pathLength={1}
          strokeDasharray={`${arc.len} 1`}
          strokeDashoffset={offset}
          style={{ filter: blur > 2 ? `blur(${blur}px)` : undefined }}
        />
      ))}
    </g>
  );
};

/**
 * The transition that joins the two IDE shots. Rather than dissolving, a volley
 * of light arcs rakes through frame and blows the exposure out to amber; the
 * cut happens inside the blowout, so the light is doing the edit.
 *
 * `t` runs 0 -> 1 across the whole event.
 */
export const Flood: React.FC<{ t: number }> = ({ t }) => {
  if (t <= 0 || t >= 1) {
    return null;
  }

  // Exposure: slow lift, hard peak, slower decay.
  const blow = interpolate(t, [0.12, 0.42, 0.52, 0.92], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  return (
    <AbsoluteFill style={{ mixBlendMode: "screen" }}>
      <AbsoluteFill
        style={{
          background: [
            `radial-gradient(90% 60% at 42% 46%, ${C.amber} 0%, transparent 68%)`,
            `radial-gradient(140% 90% at 20% 62%, ${C.ember} 0%, transparent 72%)`,
            `radial-gradient(70% 40% at 66% 38%, ${C.hot} 0%, transparent 60%)`,
          ].join(","),
          opacity: blow * 0.92,
          filter: "blur(28px)",
        }}
      />
      <svg
        width={WIDTH}
        height={HEIGHT}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        style={{ position: "absolute", inset: 0 }}
      >
        <title>Light streaks</title>
        {ARCS.map((arc, i) => (
          <Streak key={i} arc={arc} t={t} />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
