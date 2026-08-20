import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { BEAT, COLORS, EASE_OUT } from "./theme";
import { MONO, SANS, loadFonts } from "../shared/fonts";
import { PROMPT } from "./script";
import { Bubble } from "./Bubble";
import { Composer } from "./Composer";
import { Mark } from "./primitives";
import { Outro } from "./Outro";
import { Response } from "./Response";

const TopBar: React.FC = () => {
  const frame = useCurrentFrame();
  const on = Math.floor(frame / 14) % 2 === 0;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
      <Mark size={26} />
      <div
        style={{
          fontFamily: SANS,
          fontWeight: 600,
          fontSize: 22,
          letterSpacing: "0.02em",
          color: COLORS.fg,
        }}
      >
        Slate AI
      </div>
      <div style={{ flex: 1 }} />
      <div
        style={{
          width: 8,
          height: 8,
          backgroundColor: COLORS.accent,
          opacity: on ? 1 : 0.25,
        }}
      />
      <div
        style={{
          fontFamily: MONO,
          fontWeight: 500,
          fontSize: 16,
          letterSpacing: "0.2em",
          textTransform: "uppercase",
          color: COLORS.muted,
        }}
      >
        Live
      </div>
    </div>
  );
};

/** Pulsing squares shown while the model "thinks", before the first token. */
const Thinking: React.FC = () => {
  const frame = useCurrentFrame();
  const fade = interpolate(
    frame,
    [BEAT.thinkStart, BEAT.thinkStart + 8, BEAT.streamStart - 6, BEAT.streamStart],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_OUT },
  );

  if (fade <= 0.001) {
    return null;
  }

  return (
    <div style={{ display: "flex", gap: 10, opacity: fade, paddingTop: 12 }}>
      {[0, 1, 2].map((i) => {
        const phase = Math.floor((frame - i * 3) / 6) % 3;
        return (
          <div
            key={i}
            style={{
              width: 12,
              height: 12,
              backgroundColor: COLORS.accent,
              opacity: phase === 0 ? 1 : 0.22,
            }}
          />
        );
      })}
    </div>
  );
};

export const ChatAd: React.FC = () => {
  loadFonts();
  const frame = useCurrentFrame();

  // Slow push-in across the answer, so the frame never sits perfectly still.
  const push = interpolate(frame, [BEAT.send, BEAT.streamEnd], [1, 1.035], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  // The chat recedes as the closing lockup takes over.
  const exit = interpolate(
    frame,
    [BEAT.outroStart - 10, BEAT.outroStart + 12],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_OUT },
  );
  const outroLocal = frame - BEAT.outroStart;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      {/* Faint accent bloom behind the answer, to keep the black from going flat. */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(120% 70% at 12% 78%, rgba(184,255,46,0.10) 0%, rgba(184,255,46,0) 58%)`,
        }}
      />

      <AbsoluteFill
        style={{
          opacity: 1 - exit,
          transform: `scale(${push * (1 - exit * 0.06)})`,
          filter: exit > 0.001 ? `blur(${exit * 14}px)` : undefined,
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            padding: 48,
            gap: 28,
          }}
        >
          <TopBar />

          <div
            style={{
              flex: 1,
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
              justifyContent: "flex-end",
              gap: 40,
            }}
          >
            {frame >= BEAT.send ? (
              <Bubble role="user" appearAt={BEAT.send}>
                {PROMPT}
              </Bubble>
            ) : null}

            {frame >= BEAT.thinkStart ? (
              <Bubble role="assistant" appearAt={BEAT.thinkStart}>
                <Thinking />
                {frame >= BEAT.streamStart - 6 ? (
                  <Response />
                ) : null}
              </Bubble>
            ) : null}
          </div>

          <Composer />
        </div>
      </AbsoluteFill>

      {outroLocal >= -10 ? (
        <AbsoluteFill style={{ opacity: exit }}>
          <Outro local={outroLocal} />
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
