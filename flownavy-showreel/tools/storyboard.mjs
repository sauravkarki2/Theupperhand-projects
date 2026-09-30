// Captures key frames per scene and builds storyboard/storyboard.png + storyboard/index.html.
import fs from 'node:fs';
import path from 'node:path';
import { openReel, ROOT } from './serve.mjs';

const OUT = path.join(ROOT, 'storyboard');
fs.mkdirSync(path.join(OUT, 'frames'), { recursive: true });

const reel = await openReel();
const scenes = await reel.page.evaluate(() => window.SCENES);
// Two beats per scene: the build and the peak.
const PICKS = { OPEN: [1.3, 2.3], FLOW: [1.6, 3.0], KINETIC: [0.5, 2.5], '3D OCEAN': [1.8, 3.2], NAVIGATE: [1.6, 3.1], MONTAGE: [0.3, 2.3], '3D TUNNEL': [0.8, 2.3], LOGO: [0.9, 3.6] };

const shots = [];
for (const s of scenes) {
  for (const lt of PICKS[s.label]) {
    const t = s.start + lt;
    const file = `frames/${t.toFixed(2).replace('.', '_')}.jpg`;
    fs.writeFileSync(path.join(OUT, file), await reel.frame(t));
    shots.push({ ...s, t, file });
    console.log('frame', t.toFixed(2), s.label);
  }
}

const fmt = t => `0:${t.toFixed(1).padStart(4, '0')}`;
const cards = scenes.map((s, i) => {
  const fr = shots.filter(x => x.label === s.label);
  return `<section class="scene">
    <header><span class="n">${String(i + 1).padStart(2, '0')}</span><h2>${s.label}</h2><span class="tc">${fmt(s.start)} – ${fmt(s.end)}</span></header>
    <div class="frames">${fr.map(f => `<figure><img src="${f.file}"><figcaption>${fmt(f.t)}</figcaption></figure>`).join('')}</div>
    <p>${s.note}</p>
  </section>`;
}).join('\n');

fs.writeFileSync(path.join(OUT, 'index.html'), `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="../fonts.css">
<style>
body{margin:0;background:#050b1f;color:#e6ecff;font:16px/1.5 "Inter Tight",sans-serif;padding:56px 64px;width:1792px}
h1{font:700 44px "Space Grotesk";margin:0 0 6px;letter-spacing:1px}
.sub{color:#8ea3cf;margin:0 0 40px;font-size:18px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:36px 40px}
.scene header{display:flex;align-items:baseline;gap:14px;margin-bottom:12px}
.n{font:700 15px "Space Grotesk";color:#22d3ee;letter-spacing:3px}
h2{font:700 22px "Space Grotesk";margin:0;letter-spacing:3px}
.tc{margin-left:auto;font:500 14px "Space Grotesk";color:#8ea3cf;letter-spacing:2px}
.frames{display:grid;grid-template-columns:1fr 1fr;gap:10px}
figure{margin:0;position:relative}
img{width:100%;display:block;border-radius:6px;border:1px solid #1b2a52}
figcaption{position:absolute;left:8px;bottom:8px;font:600 12px "Space Grotesk";background:#050b1fcc;padding:2px 8px;border-radius:4px;letter-spacing:1px}
.scene p{margin:12px 0 0;color:#b9c6e6;font-size:15.5px}
</style></head><body>
<h1>FLOW NAVY — Showreel storyboard</h1>
<p class="sub">32 s · 16:9 · 1920×1080 · 60 fps · 120 BPM · 8 scenes · rendered in code (Canvas 2D + three.js), with a synthesized soundtrack added at final render</p>
<div class="grid">${cards}</div></body></html>`);

await reel.page.setViewportSize({ width: 1920, height: 1080 });
const url = reel.page.url().replace(/index\.html.*/, 'storyboard/index.html');
await reel.page.goto(url);
await reel.page.evaluate(() => document.fonts.ready);
await reel.page.screenshot({ path: path.join(OUT, 'storyboard.png'), fullPage: true });
await reel.close();
console.log('done');
