export const PROMPT = "Write a launch tweet for our analytics app";

export type Token = { text: string; punch: boolean };

export type BlockBody =
  | { kind: "lead" }
  | { kind: "bullet"; index: string }
  | { kind: "close" };

export type Block = BlockBody & { tokens: Token[] };

/**
 * Splits copy into per-word tokens. Text wrapped in [[double brackets]] is
 * marked as a "punch" phrase — the words the kinetic treatment blows up.
 */
const tk = (source: string): Token[] =>
  source
    .split(/(\[\[.*?\]\])/g)
    .filter(Boolean)
    .flatMap((part) => {
      const punch = part.startsWith("[[");
      const body = punch ? part.slice(2, -2) : part;
      return body
        .split(/\s+/)
        .filter(Boolean)
        .map((text) => ({ text, punch }));
    });

const SOURCE: Block[] = [
  { kind: "lead", tokens: tk("Three angles — pick one:") },
  // Within a bullet the punch phrase leads and is rendered as the headline
  // line; everything after it becomes the smaller supporting line.
  {
    kind: "bullet",
    index: "01",
    tokens: tk("[[Stop guessing.]] Slate turns raw product data into plain answers."),
  },
  {
    kind: "bullet",
    index: "02",
    tokens: tk("[[One screen.]] Six dashboards, your whole funnel, one glance."),
  },
  {
    kind: "bullet",
    index: "03",
    tokens: tk("[[An hour to a minute.]] The metrics meeting, done before your coffee."),
  },
  { kind: "close", tokens: tk("Want the thread version?") },
];

/** Each block tagged with its offset into the global word stream. */
export type PlacedBlock = Block & { start: number };

export const BLOCKS: PlacedBlock[] = (() => {
  let cursor = 0;
  return SOURCE.map((block) => {
    const placed = { ...block, start: cursor };
    cursor += block.tokens.length;
    return placed;
  });
})();

export const TOTAL_WORDS = BLOCKS.reduce((n, b) => n + b.tokens.length, 0);

export const OUTRO = {
  headline: ["From prompt", "to post."],
  kicker: "in under nine seconds",
  wordmark: "SLATE AI",
};
