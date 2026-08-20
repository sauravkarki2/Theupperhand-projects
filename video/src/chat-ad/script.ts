export const PROMPT = "Write a launch tweet for our analytics app";

export type Block =
  | { kind: "text"; words: string[] }
  | { kind: "bullet"; words: string[] };

export const RESPONSE: Block[] = [
  { kind: "text", words: ["Here", "are", "three", "angles", "you", "could", "run", "with:"] },
  { kind: "bullet", words: ["Stop", "guessing.", "Slate", "turns", "raw", "product", "data", "into", "answers."] },
  { kind: "bullet", words: ["Six", "dashboards,", "one", "screen.", "Your", "whole", "funnel", "at", "a", "glance."] },
  { kind: "bullet", words: ["The", "metrics", "meeting", "that", "used", "to", "take", "an", "hour", "now", "takes", "a", "minute."] },
  { kind: "text", words: ["Want", "me", "to", "draft", "the", "thread", "version?"] },
];

export const TOTAL_WORDS = RESPONSE.reduce((n, b) => n + b.words.length, 0);
