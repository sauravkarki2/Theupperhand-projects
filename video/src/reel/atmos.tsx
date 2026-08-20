import { AbsoluteFill, useCurrentFrame } from "remotion";
import { C } from "./theme";

/**
 * A soft light source. Three stacked radial stops rather than one, because a
 * single gradient falls off too evenly and reads as a flat disc — real bloom
 * has a hot core, a wide mid, and a very long tail.
 */
export const Bloom: React.FC<{
  x: string;
  y: string;
  size: number;
  intensity: number;
  color?: string;
}> = ({ x, y, size, intensity, color = C.amber }) => {
  if (intensity <= 0.001) {
    return null;
  }
  return (
    <AbsoluteFill
      style={{
        background: [
          `radial-gradient(${size * 0.35}px ${size * 0.35}px at ${x} ${y}, ${color} 0%, transparent 70%)`,
          `radial-gradient(${size}px ${size}px at ${x} ${y}, ${color} 0%, transparent 62%)`,
          `radial-gradient(${size * 2.4}px ${size * 2.4}px at ${x} ${y}, ${color} 0%, transparent 58%)`,
        ].join(","),
        opacity: intensity,
        mixBlendMode: "screen",
      }}
    />
  );
};

/**
 * Animated film grain. `feTurbulence` at full 1080x1920 is far too slow to
 * rasterise 450 times, so the noise is generated at a quarter of that and
 * scaled up — which also gives the grain a coarser, more filmic size than
 * per-pixel noise would.
 */
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.16 }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        opacity,
        mixBlendMode: "overlay",
        pointerEvents: "none",
      }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 270 480"
        preserveAspectRatio="none"
      >
        <filter id="reel-grain">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.9"
            numOctaves={1}
            seed={frame % 17}
          />
        </filter>
        <rect width="270" height="480" filter="url(#reel-grain)" />
      </svg>
    </AbsoluteFill>
  );
};

/** Corner falloff, so the frame never reads as a flat black rectangle. */
export const Vignette: React.FC<{ strength?: number }> = ({
  strength = 0.85,
}) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(78% 55% at 50% 48%, transparent 40%, rgba(0,0,0,${strength}) 100%)`,
    }}
  />
);
