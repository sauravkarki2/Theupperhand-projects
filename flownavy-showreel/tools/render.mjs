// Renders the reel to out/flownavy_showreel_silent.mp4 (1920x1080, 60 fps, H.264).
// Frames are split into contiguous chunks, one headless browser per chunk, each piped
// into its own ffmpeg; the chunks are then joined losslessly.
// Usage: node tools/render.mjs [workers=4] [from=0] [to=DUR]
import fs from 'node:fs';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';
import { openReel, ROOT } from './serve.mjs';

const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const FPS = 60;
const WORKERS = +(process.argv[2] || 4);
const OUT = path.join(ROOT, 'out');
const TMP = path.join(OUT, 'segments');
fs.mkdirSync(TMP, { recursive: true });

const probe = await openReel();
const DUR = await probe.page.evaluate(() => window.DUR);
await probe.close();
const from = Math.round(+(process.argv[3] || 0) * FPS);
const to = Math.round(+(process.argv[4] || DUR) * FPS);
const total = to - from;
const per = Math.ceil(total / WORKERS);
const started = Date.now();
let done = 0;

async function worker(k) {
  const a = from + k * per, b = Math.min(to, a + per);
  if (a >= b) return null;
  const file = path.join(TMP, `seg_${String(k).padStart(2, '0')}.mp4`);
  const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-r', String(FPS), file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const closed = new Promise((res, rej) => ff.on('close', c => (c ? rej(new Error(`ffmpeg exit ${c}`)) : res())));
  const reel = await openReel();
  for (let i = a; i < b; i++) {
    const buf = await reel.frame(i / FPS, { quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (++done % 60 === 0) {
      const s = (Date.now() - started) / 1000;
      console.log(`${done}/${total} frames · ${s.toFixed(0)}s elapsed · ~${((total - done) * s / done).toFixed(0)}s left`);
    }
  }
  ff.stdin.end();
  await reel.close();
  await closed;
  return file;
}

const segs = (await Promise.all([...Array(WORKERS).keys()].map(worker))).filter(Boolean);
const list = path.join(TMP, 'list.txt');
fs.writeFileSync(list, segs.map(f => `file '${f}'`).join('\n'));
const dest = path.join(OUT, 'flownavy_showreel_silent.mp4');
execFileSync(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', dest]);
console.log('wrote', dest, `in ${((Date.now() - started) / 1000).toFixed(0)}s`);
