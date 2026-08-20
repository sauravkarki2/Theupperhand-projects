import { BEAT } from "./theme";
import { BLOCKS, TOTAL_WORDS } from "./script";

/** Frames between consecutive streamed words. ~7.3 words/sec at 30fps. */
const WORD_STEP = 4.1;
/** Extra pause inserted before each new block, so bullets land as beats. */
const BLOCK_GAP = 10;

/** The frame at which a given block's word reveal begins. */
export const blockFrame = (blockIdx: number): number =>
  BEAT.streamStart + BLOCKS[blockIdx].start * WORD_STEP + blockIdx * BLOCK_GAP;

/** The frame at which one word of one block appears. */
export const wordFrame = (blockIdx: number, wordIdx: number): number =>
  blockFrame(blockIdx) + wordIdx * WORD_STEP;

/** Frame the very last word lands on — the stream's true end. */
export const STREAM_LAST = wordFrame(
  BLOCKS.length - 1,
  BLOCKS[BLOCKS.length - 1].tokens.length - 1,
);

export { TOTAL_WORDS };
