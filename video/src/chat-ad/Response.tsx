import { interpolate, useCurrentFrame } from "remotion";
import { COLORS, EASE_OUT } from "./theme";
import { MONO } from "./fonts";
import { BLOCKS, type PlacedBlock } from "./script";
import { blockFrame, wordFrame } from "./timing";
import { Word } from "./Word";
import { Cursor } from "./primitives";

const Line: React.FC<{
  block: PlacedBlock;
  blockIdx: number;
  punch: boolean;
  size: number;
  color?: string;
}> = ({ block, blockIdx, punch, size, color }) => {
  const frame = useCurrentFrame();
  const tokens = block.tokens
    .map((token, i) => ({ token, i }))
    .filter(({ token }) => token.punch === punch);

  if (tokens.length === 0) {
    return null;
  }

  // A punch line carries one continuous accent rule that wipes across the whole
  // phrase as its words land — not one rule per word.
  const first = wordFrame(blockIdx, tokens[0].i);
  const last = wordFrame(blockIdx, tokens[tokens.length - 1].i);

  // This line owns the caret while it is the one actively being written.
  const active = frame >= first && frame < last + 8;
  const revealed = tokens.filter(({ i }) => frame >= wordFrame(blockIdx, i)).length;

  return (
    <div
      style={
        punch
          ? {
              display: "inline-block",
              position: "relative",
              paddingBottom: size * 0.24,
            }
          : undefined
      }
    >
      {tokens.flatMap(({ token, i }, n) => {
        const word = (
          <Word
            key={i}
            text={token.text}
            punch={token.punch}
            appearAt={wordFrame(blockIdx, i)}
            size={size}
            color={color}
            isLast={n === tokens.length - 1}
          />
        );
        // Words that have not been revealed yet still occupy layout, so the
        // caret has to be spliced in at the reveal boundary rather than
        // appended — otherwise it parks at the far end of the finished line.
        return active && n === revealed
          ? [
              <Cursor key="caret" height={size * 1.05} width={punch ? 4 : 3} />,
              word,
            ]
          : [word];
      })}
      {active && revealed >= tokens.length ? (
        <Cursor height={size * 1.05} width={punch ? 4 : 3} />
      ) : null}
      {punch ? <PunchRule from={first + 4} to={last + 14} size={size} /> : null}
    </div>
  );
};

const PunchRule: React.FC<{ from: number; to: number; size: number }> = ({
  from,
  to,
  size,
}) => {
  const frame = useCurrentFrame();
  const wipe = interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: size * 0.06,
        height: Math.max(2, size * 0.08),
        backgroundColor: COLORS.accent,
        opacity: 0.85,
        transform: `scaleX(${wipe})`,
        transformOrigin: "left center",
      }}
    />
  );
};

const Bullet: React.FC<{ block: PlacedBlock; blockIdx: number }> = ({
  block,
  blockIdx,
}) => {
  const frame = useCurrentFrame();
  const start = blockFrame(blockIdx);

  // Accent rule grows down the left edge as the bullet starts streaming.
  const rule = interpolate(frame, [start - 4, start + 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const badge = interpolate(frame, [start - 4, start + 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  return (
    <div style={{ display: "flex", gap: 22, alignItems: "stretch" }}>
      <div
        style={{
          flexShrink: 0,
          width: 3,
          backgroundColor: COLORS.accent,
          opacity: 0.5,
          transform: `scaleY(${rule})`,
          transformOrigin: "top center",
        }}
      />
      <div style={{ flex: 1, minWidth: 0, paddingBottom: 4 }}>
        <div
          style={{
            fontFamily: MONO,
            fontWeight: 500,
            fontSize: 16,
            letterSpacing: "0.22em",
            color: COLORS.accent,
            opacity: badge * 0.75,
            marginBottom: 6,
            transform: `translateX(${interpolate(badge, [0, 1], [-10, 0])}px)`,
          }}
        >
          {block.kind === "bullet" ? block.index : ""}
        </div>
        <Line block={block} blockIdx={blockIdx} punch size={46} />
        <div style={{ marginTop: 10 }}>
          <Line block={block} blockIdx={blockIdx} punch={false} size={27} />
        </div>
      </div>
    </div>
  );
};

/** The assistant's streamed answer. */
export const Response: React.FC = () => (
  <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
    {BLOCKS.map((block, blockIdx) => {
      if (block.kind === "bullet") {
        return <Bullet key={blockIdx} block={block} blockIdx={blockIdx} />;
      }
      return (
        <div key={blockIdx}>
          <Line
            block={block}
            blockIdx={blockIdx}
            punch={false}
            size={block.kind === "lead" ? 31 : 27}
            color={block.kind === "close" ? COLORS.muted : COLORS.fg}
          />
        </div>
      );
    })}
  </div>
);
