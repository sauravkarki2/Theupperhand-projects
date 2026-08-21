import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, EASE_DRIFT, EASE_OUT, SHOT } from "./theme";
import { loadFonts } from "../shared/fonts";
import { Bloom, Grain, Vignette } from "./atmos";
import { Composer } from "./ComposerBar";
import { Cube } from "./Cube";
import { Flood } from "./Flood";
import { IdeWindow, WIN_H, WIN_W } from "./IdeWindow";
import { Logo } from "./Logo";

const fade = (frame: number, inAt: number, outAt: number, len = 12) =>
  interpolate(
    frame,
    [inAt, inAt + len, outAt - len, outAt],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_OUT },
  );

/**
 * Shot 2. One unbroken push from "whole window in frame" to "one task row fills
 * the screen". The focus point travels as well as the scale, so the move reads
 * as a camera closing on the task rail rather than a flat zoom.
 */
const IdeShot: React.FC<{ local: number; span: number }> = ({ local, span }) => {
  // Held wide for the first half, then a long accelerating push. A single
  // eased ramp reached the close-up far too early to read the window at all.
  const e = (pts: number[]) =>
    interpolate(local, [0, span * 0.42, span * 0.72, span], pts, {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: EASE_DRIFT,
    });

  const scale = e([0.54, 0.6, 1.12, 2.5]);
  const fx = e([WIN_W / 2, WIN_W / 2, 420, 236]);
  const fy = e([WIN_H / 2, WIN_H / 2, 400, 322]);
  const tilt = e([3.4, 2.6, 1.2, 0.2]);

  const tx = -(fx - WIN_W / 2) * scale;
  const ty = -(fy - WIN_H / 2) * scale;

  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", perspective: 2200 }}>
      <div
        style={{
          transform: `translate(${tx}px, ${ty}px) scale(${scale}) rotateY(${tilt}deg)`,
          transformStyle: "preserve-3d",
        }}
      >
        <IdeWindow local={local} />
      </div>
    </AbsoluteFill>
  );
};

/** Shot 4. The same composer bar as in the window, now filling the frame. */
const ComposerShot: React.FC<{ local: number; span: number }> = ({ local, span }) => {
  const menu = interpolate(local, [16, 46], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const push = interpolate(local, [0, span], [1.0, 1.07], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_DRIFT,
  });
  const chips = interpolate(local, [4, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const drift = interpolate(local, [0, span], [238, 150], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_DRIFT,
  });

  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <Bloom x="10%" y="74%" size={520} intensity={0.24} color={C.ember} />
      <div style={{ transform: `translateY(${drift}px) scale(${push})` }}>
        <Composer
          width={980}
          menu={menu}
          hovered={1}
          prompt="Plan the mission interface"
          chips={chips}
        />
      </div>
    </AbsoluteFill>
  );
};

export const Reel: React.FC = () => {
  loadFonts();
  const frame = useCurrentFrame();

  // The warm key light lives across the whole piece and only changes level, so
  // the four shots read as one location rather than four separate cards.
  const key = interpolate(
    frame,
    [0, SHOT.ideIn, SHOT.ideOut, SHOT.composerOut, SHOT.logoIn],
    [0.12, 0.34, 0.42, 0.3, 0.16],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const floodT = interpolate(
    frame,
    [SHOT.floodPeak - 26, SHOT.floodPeak + 26],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill style={{ backgroundColor: C.black }}>
      <Bloom x="6%" y="62%" size={620} intensity={key} color={C.ember} />
      <Bloom x="88%" y="24%" size={420} intensity={key * 0.5} color={C.deep} />

      {frame < SHOT.cubeOut + 4 ? (
        <AbsoluteFill>
          <Cube local={frame - SHOT.cubeIn} duration={SHOT.cubeOut - SHOT.cubeIn} />
        </AbsoluteFill>
      ) : null}

      {frame >= SHOT.ideIn - 4 && frame < SHOT.ideOut + 20 ? (
        <AbsoluteFill style={{ opacity: fade(frame, SHOT.ideIn, SHOT.ideOut + 18, 14) }}>
          <IdeShot local={frame - SHOT.ideIn} span={SHOT.ideOut - SHOT.ideIn} />
        </AbsoluteFill>
      ) : null}

      {frame >= SHOT.composerIn - 4 && frame < SHOT.composerOut + 16 ? (
        <AbsoluteFill style={{ opacity: fade(frame, SHOT.composerIn, SHOT.composerOut + 14, 14) }}>
          <ComposerShot
            local={frame - SHOT.composerIn}
            span={SHOT.composerOut - SHOT.composerIn}
          />
        </AbsoluteFill>
      ) : null}

      {frame >= SHOT.emberIn - 4 && frame < SHOT.emberOut + 6 ? (
        <AbsoluteFill>
          <Cube
            local={frame - SHOT.emberIn}
            duration={SHOT.emberOut - SHOT.emberIn}
            tint={C.amber}
          />
        </AbsoluteFill>
      ) : null}

      {frame >= SHOT.logoIn ? (
        <AbsoluteFill style={{ opacity: fade(frame, SHOT.logoIn, SHOT.logoOut + 30, 16) }}>
          <Logo local={frame - SHOT.logoIn} />
        </AbsoluteFill>
      ) : null}

      <Flood t={floodT} />

      <Vignette strength={0.72} />
      <Grain />
    </AbsoluteFill>
  );
};
