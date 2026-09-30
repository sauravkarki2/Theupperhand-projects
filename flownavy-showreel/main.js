// Flow Navy — motion graphics showreel.
// Every frame is a pure function of time t (seconds): renderAt(t) draws it.
// 2D canvas = type, HUD, graphic scenes. WebGL canvas (three.js) = 3D scenes.
import * as THREE from './lib/three.module.min.js';

export const W = 1920, H = 1080, DUR = 32, FPS = 60;

const C = {
  bg: '#040A1C', deep: '#07122E', navy: '#0A1A3F', royal: '#1D4ED8',
  cyan: '#22D3EE', aqua: '#5EEAD4', white: '#F1F5FF', coral: '#FF6B4A',
};
const SANS = 'Inter Tight', GROT = 'Space Grotesk';

// ---------- math / easing ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const P = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, t) => a + (b - a) * t;
const TAU = Math.PI * 2;
const E = {
  outExpo: t => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  inExpo: t => (t <= 0 ? 0 : Math.pow(2, 10 * t - 10)),
  inOutExpo: t => (t <= 0 ? 0 : t >= 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2),
  outCubic: t => 1 - Math.pow(1 - t, 3),
  inOutCubic: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  outBack: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
};
function rng(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const hash = n => { const r = rng(n * 9973 + 17); return r(); };

// ---------- canvases ----------
const c2d = document.getElementById('c2d');
const ctx = c2d.getContext('2d');
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('c3d'), antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);

// ---------- 2D helpers ----------
function bg(col) { ctx.fillStyle = col; ctx.fillRect(0, 0, W, H); }
function setFont(weight, size, fam = SANS, ls = 0) {
  ctx.font = `${weight} ${size}px "${fam}"`;
  ctx.letterSpacing = `${ls}px`;
}
// Text that rises into view from behind a mask; `pin` 0→1 reveals, `pout` 0→1 exits upward.
function maskText(str, x, y, size, pin, pout = 0, o = {}) {
  const { weight = 800, fam = SANS, color = C.white, align = 'left', ls = 0 } = o;
  if (pin <= 0 || pout >= 1) return;
  ctx.save();
  setFont(weight, size, fam, ls);
  ctx.textAlign = align; ctx.textBaseline = 'alphabetic';
  const w = ctx.measureText(str).width;
  const x0 = align === 'left' ? x : align === 'center' ? x - w / 2 : x - w;
  ctx.beginPath(); ctx.rect(x0 - 40, y - size * 0.98, w + 80, size * 1.24); ctx.clip();
  ctx.fillStyle = color;
  ctx.fillText(str, x, y + (1 - pin) * size * 1.2 - pout * size * 1.2);
  ctx.restore();
}
function glowLine(pts, width, color, blur) {
  ctx.beginPath();
  pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
  ctx.lineWidth = width; ctx.strokeStyle = color;
  ctx.shadowBlur = blur; ctx.shadowColor = color;
  ctx.stroke(); ctx.shadowBlur = 0;
}
function hexA(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`;
}

// Particles shared by the flow-field scene and the logo backdrop.
const PT = Array.from({ length: 1700 }, (_, i) => {
  const r = rng(i * 7 + 1);
  return { x0: r() * (W + 400), y0: r() * H * 1.2 - H * 0.1, v: 180 + r() * 520, ph: r() * TAU, c: r() };
});
function ppos(p, t) {
  const span = W + 400;
  const x = ((p.x0 + p.v * t) % span) - 200;
  const y = p.y0 + 70 * Math.sin(x * 0.0035 + p.y0 * 0.008 + t * 0.7) + 28 * Math.sin(x * 0.011 - t * 1.4 + p.ph);
  return [x, y];
}
function drawParticles(T, alpha, trail = 0.22) {
  const groups = [[C.white, 2.2, []], [C.cyan, 1.8, []], [C.royal, 1.6, []], [C.aqua, 1.2, []]];
  for (const p of PT) {
    const g = p.c < 0.07 ? 0 : p.c < 0.5 ? 1 : p.c < 0.85 ? 2 : 3;
    const seg = [];
    let px = null;
    for (let j = 0; j <= 6; j++) {
      const [x, y] = ppos(p, T - trail * (j / 6));
      if (px !== null && Math.abs(x - px) > 300) break;
      seg.push([x, y]); px = x;
    }
    groups[g][2].push(seg);
  }
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.globalAlpha = alpha;
  ctx.lineCap = 'round';
  for (const [col, w, segs] of groups) {
    ctx.beginPath();
    for (const s of segs) s.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    ctx.lineWidth = w; ctx.strokeStyle = col; ctx.stroke();
  }
  ctx.restore();
}

// ---------- 3D: wave ocean ----------
const wave = (() => {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(C.bg);
  const cam = new THREE.PerspectiveCamera(55, W / H, 0.1, 300);
  const geo = new THREE.PlaneGeometry(160, 160, 280, 280);
  geo.rotateX(-Math.PI / 2);
  const mat = new THREE.ShaderMaterial({
    uniforms: { uT: { value: 0 }, uAmp: { value: 0 } },
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: `
      uniform float uT; uniform float uAmp; varying float vH; varying float vFog;
      void main(){
        vec3 p = position;
        float h = sin(p.x*0.16 + uT*1.1)*1.1 + sin(p.z*0.21 - uT*1.7)*1.3 + sin((p.x*0.7 + p.z)*0.09 + uT*0.6)*1.8;
        p.y = h * uAmp; vH = h * uAmp;
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        float d = -mv.z;
        vFog = clamp(1.0 - (d - 4.0) / 80.0, 0.0, 1.0);
        gl_PointSize = clamp(110.0 / d, 1.2, 7.0);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      varying float vH; varying float vFog;
      void main(){
        float r = length(gl_PointCoord - 0.5);
        if (r > 0.5) discard;
        float a = smoothstep(0.5, 0.05, r) * vFog;
        vec3 col = mix(vec3(0.11,0.30,0.85), vec3(0.13,0.83,0.93), smoothstep(-2.0, 2.4, vH));
        col = mix(col, vec3(0.95,0.97,1.0), smoothstep(2.6, 3.8, vH));
        gl_FragColor = vec4(col * a, a);
      }`,
  });
  scene.add(new THREE.Points(geo, mat));
  return {
    render(lt) {
      mat.uniforms.uT.value = lt + 2;
      mat.uniforms.uAmp.value = E.inOutCubic(P(lt, 0, 1.4));
      const k = E.inOutCubic(P(lt, 0, 4));
      cam.position.set(Math.sin(lt * 0.5) * 3, lerp(9, 5, k), lerp(46, 26, k));
      cam.up.set(Math.sin(lt * 0.4) * 0.08, 1, 0).normalize();
      cam.lookAt(0, 0, -30);
      renderer.render(scene, cam);
    },
  };
})();

// ---------- 3D: ring tunnel ----------
const tunnel = (() => {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(C.bg);
  scene.fog = new THREE.FogExp2(C.bg, 0.03);
  const cam = new THREE.PerspectiveCamera(70, W / H, 0.1, 400);
  const pts = [];
  for (let i = 0; i < 16; i++) pts.push(new THREE.Vector3(Math.sin(i * 0.9) * 12, Math.cos(i * 0.7) * 8, -i * 25));
  const curve = new THREE.CatmullRomCurve3(pts);
  const cols = [C.cyan, C.royal, C.white, C.aqua];
  const geos = [0.55, 0.8, 0.35].map(arc => new THREE.TorusGeometry(4.2, 0.045, 6, 120, TAU * arc));
  const rings = [];
  const N = 150;
  for (let i = 0; i < N; i++) {
    const u = i / N;
    const p = curve.getPointAt(u), tan = curve.getTangentAt(u);
    const m = new THREE.Mesh(geos[i % 3], new THREE.MeshBasicMaterial({ color: cols[i % 4], fog: true }));
    m.position.copy(p);
    m.lookAt(p.clone().add(tan));
    rings.push({ m, base: m.quaternion.clone(), dir: i % 2 ? 1 : -1, off: hash(i) * TAU });
    scene.add(m);
  }
  const r = rng(5);
  const pp = [];
  for (let i = 0; i < 4000; i++) {
    const p = curve.getPointAt(r());
    const a = r() * TAU, rad = 1 + r() * 2.8;
    pp.push(p.x + Math.cos(a) * rad, p.y + Math.sin(a) * rad, p.z);
  }
  const pg = new THREE.BufferGeometry();
  pg.setAttribute('position', new THREE.Float32BufferAttribute(pp, 3));
  scene.add(new THREE.Points(pg, new THREE.PointsMaterial({ color: C.aqua, size: 0.07, fog: true })));
  const zq = new THREE.Quaternion(), Z = new THREE.Vector3(0, 0, 1);
  return {
    render(lt) {
      for (const g of rings) {
        zq.setFromAxisAngle(Z, g.off + g.dir * lt * 1.1);
        g.m.quaternion.copy(g.base).multiply(zq);
      }
      const u = 0.01 + 0.6 * Math.pow(lt / 3.5, 1.7);
      cam.position.copy(curve.getPointAt(u));
      cam.up.set(Math.sin(lt * 0.7), Math.cos(lt * 0.7), 0);
      cam.lookAt(curve.getPointAt(Math.min(1, u + 0.025)));
      renderer.render(scene, cam);
    },
  };
})();

// ---------- scenes ----------
// Each scene: [start, end, label, draw(lt, t), uses3d]
function sceneOpen(lt) {
  bg(C.bg);
  const draw = E.inOutCubic(P(lt, 0.1, 1.1));
  const amp = E.outCubic(P(lt, 0.9, 1.9)) * 90;
  const split = E.outExpo(P(lt, 1.6, 2.4));
  const col = E.inExpo(P(lt, 2.55, 2.95));
  const n = 9, mid = 4;
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (let k = 0; k < n; k++) {
    const o = k - mid;
    if (k !== mid && split <= 0) continue;
    const pts = [];
    for (let x = 0; x <= W * draw; x += 8) {
      const env = 0.55 + 0.45 * Math.sin(x * 0.0017 + lt * 0.8);
      const y = H / 2 + o * split * 40 * (1 - col) + amp * (1 - col) * env * Math.sin(x * 0.006 - lt * 4 + o * 0.35 * split);
      pts.push([x, y]);
    }
    ctx.globalAlpha = k === mid ? 1 : split * (1 - Math.abs(o) * 0.14);
    glowLine(pts, k === mid ? 3 : 2, k === mid ? C.white : Math.abs(o) % 2 ? C.cyan : C.royal, 18);
  }
  ctx.restore();
  if (draw > 0 && draw < 1) {
    const hx = W * draw;
    const g = ctx.createRadialGradient(hx, H / 2, 0, hx, H / 2, 60);
    g.addColorStop(0, 'rgba(255,255,255,0.9)'); g.addColorStop(1, 'rgba(34,211,238,0)');
    ctx.fillStyle = g; ctx.fillRect(hx - 60, H / 2 - 60, 120, 120);
  }
  const ta = P(lt, 0.4, 1.0) * (1 - P(lt, 2.2, 2.6));
  if (ta > 0) {
    ctx.save();
    ctx.globalAlpha = ta;
    setFont(500, 22, GROT, lerp(34, 16, E.outCubic(P(lt, 0.4, 2.2))));
    ctx.textAlign = 'center'; ctx.fillStyle = C.white;
    ctx.fillText('SHOWREEL 2026', W / 2, H / 2 - 190);
    ctx.restore();
  }
  if (col > 0) {
    ctx.fillStyle = hexA('#FFFFFF', col);
    ctx.fillRect(0, H / 2 - 2 - col * 3, W, 4 + col * 6);
  }
}

function sceneFlow(lt) {
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, C.bg); g.addColorStop(1, C.deep);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save();
  const s = 1 + 0.07 * (lt / 4);
  ctx.translate(W / 2, H / 2); ctx.scale(s, s); ctx.translate(-W / 2, -H / 2);
  drawParticles(lt + 3, E.outCubic(P(lt, 0, 0.5)));
  ctx.restore();
  const shade = ctx.createLinearGradient(0, 0, W * 0.7, 0);
  shade.addColorStop(0, 'rgba(4,10,28,0.75)'); shade.addColorStop(1, 'rgba(4,10,28,0)');
  ctx.fillStyle = shade; ctx.fillRect(0, 0, W, H);
  const out = E.inExpo(P(lt, 3.45, 3.85));
  maskText('IDEAS', 150, H / 2 - 20, 200, E.outExpo(P(lt, 0.25, 1.0)), out);
  maskText('IN MOTION.', 150, H / 2 + 170, 200, E.outExpo(P(lt, 0.4, 1.15)), out, { color: C.cyan });
}

const SLAMS = [
  ['MOVE', C.navy, C.white, C.cyan],
  ['SHAPE', C.cyan, C.deep, C.royal],
  ['GUIDE', C.white, C.navy, C.cyan],
  ['FLOW', C.royal, C.white, C.aqua],
];
function sceneSlam(lt) {
  const i = Math.min(3, Math.floor(lt)), wl = lt - i;
  const [word, b, f, a] = SLAMS[i];
  bg(b);
  const hit = 1 - E.outExpo(clamp(wl / 0.3));
  ctx.save();
  const r = rng(i * 31 + Math.floor(wl * 60));
  const shake = Math.max(0, 1 - wl / 0.18) * 14;
  ctx.translate((r() - 0.5) * shake, (r() - 0.5) * shake);
  setFont(800, 360, SANS, -8);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.lineWidth = 2; ctx.strokeStyle = hexA(a, 0.55);
  const dir = i % 2 ? 1 : -1;
  for (let e = -3; e <= 3; e++) {
    if (!e) continue;
    ctx.globalAlpha = 1 - Math.abs(e) * 0.22;
    ctx.strokeText(word, W / 2, H / 2 + 20 + e * 300 + dir * wl * 140);
  }
  ctx.globalAlpha = 1;
  ctx.translate(W / 2, H / 2 + 20);
  ctx.transform(1, 0, -0.3 * hit, 1, 0, 0);
  const s = 1 + 0.55 * hit + 0.05 * wl;
  ctx.scale(s, s);
  ctx.fillStyle = f;
  ctx.fillText(word, 0, 0);
  ctx.restore();
  ctx.fillStyle = a;
  ctx.fillRect(0, H - 14, W * E.outCubic(wl), 14);
  setFont(600, 26, GROT, 6);
  ctx.fillStyle = f; ctx.textAlign = 'left';
  ctx.fillText(`0${i + 1} / 04`, 150, H - 70);
  const fl = Math.max(0, 1 - wl / 0.08);
  if (fl > 0) bg(hexA('#FFFFFF', fl * 0.5));
}

function sceneWave(lt) {
  wave.render(lt);
  const hz = ctx.createRadialGradient(W / 2, H * 0.34, 0, W / 2, H * 0.34, W * 0.6);
  hz.addColorStop(0, 'rgba(34,211,238,0.12)'); hz.addColorStop(1, 'rgba(34,211,238,0)');
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = hz; ctx.fillRect(0, 0, W, H); ctx.restore();
  const out = E.inExpo(P(lt, 3.5, 3.9));
  maskText('CHART', 150, H - 320, 150, E.outExpo(P(lt, 0.5, 1.2)), out);
  maskText('THE COURSE.', 150, H - 170, 150, E.outExpo(P(lt, 0.65, 1.35)), out, { color: C.cyan });
}

const ROUTE = [[-250, 170], [-110, 60], [40, 130], [160, -40], [60, -190], [250, -250]];
function scramble(str, lt, settle, seed) {
  const r = rng(seed + Math.floor(lt * 20));
  return [...str].map((ch, i) => (/\d/.test(ch) && lt < settle + i * 0.05 ? String(Math.floor(r() * 10)) : ch)).join('');
}
function sceneCompass(lt) {
  bg(C.deep);
  ctx.save();
  ctx.strokeStyle = 'rgba(94,234,212,0.05)'; ctx.lineWidth = 1;
  for (let x = 0; x < W; x += 60) { ctx.beginPath(); ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, H); ctx.stroke(); }
  for (let y = 0; y < H; y += 60) { ctx.beginPath(); ctx.moveTo(0, y + 0.5); ctx.lineTo(W, y + 0.5); ctx.stroke(); }
  ctx.restore();
  const cx = W * 0.64, cy = H / 2;
  const sweepA = E.outCubic(P(lt, 0.3, 1.0));
  if (sweepA > 0) {
    const cg = ctx.createConicGradient(lt * 2.4 - Math.PI / 2, cx, cy);
    cg.addColorStop(0, 'rgba(34,211,238,0)'); cg.addColorStop(0.86, 'rgba(34,211,238,0)');
    cg.addColorStop(0.999, `rgba(34,211,238,${0.32 * sweepA})`); cg.addColorStop(1, 'rgba(34,211,238,0)');
    ctx.fillStyle = cg; ctx.beginPath(); ctx.arc(cx, cy, 430, 0, TAU); ctx.fill();
  }
  const RINGS = [[110, 36, 0.5], [190, 72, -0.3], [280, 120, 0.18], [360, 0, 0], [430, 180, -0.1]];
  RINGS.forEach(([R, ticks, spd], i) => {
    const end = TAU * E.outCubic(P(lt, 0.05 + i * 0.1, 0.9 + i * 0.1));
    if (end <= 0) return;
    const rot = lt * spd - Math.PI / 2;
    ctx.save();
    ctx.strokeStyle = i === 3 ? 'rgba(241,245,255,0.25)' : hexA(i % 2 ? C.cyan : C.white, 0.7);
    ctx.lineWidth = i === 3 ? 1 : 1.5;
    if (i === 3) ctx.setLineDash([4, 10]);
    ctx.beginPath(); ctx.arc(cx, cy, R, rot, rot + end); ctx.stroke();
    ctx.setLineDash([]);
    for (let k = 0; k < ticks; k++) {
      const a = (k / ticks) * TAU;
      if (a > end) break;
      const len = k % 5 ? 7 : 16;
      const aa = rot + a;
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(aa) * R, cy + Math.sin(aa) * R);
      ctx.lineTo(cx + Math.cos(aa) * (R - len), cy + Math.sin(aa) * (R - len));
      ctx.stroke();
    }
    ctx.restore();
  });
  const cross = E.outCubic(P(lt, 0.2, 0.9));
  ctx.strokeStyle = 'rgba(241,245,255,0.18)'; ctx.setLineDash([2, 8]);
  ctx.beginPath(); ctx.moveTo(cx - 470 * cross, cy); ctx.lineTo(cx + 470 * cross, cy);
  ctx.moveTo(cx, cy - 470 * cross); ctx.lineTo(cx, cy + 470 * cross); ctx.stroke(); ctx.setLineDash([]);
  // route
  const rp = E.inOutCubic(P(lt, 1.0, 3.0));
  const segs = ROUTE.length - 1;
  const reach = rp * segs;
  ctx.save();
  ctx.strokeStyle = C.aqua; ctx.lineWidth = 3; ctx.shadowBlur = 14; ctx.shadowColor = C.aqua;
  ctx.beginPath();
  for (let s = 0; s <= Math.min(segs - 1, Math.floor(reach)); s++) {
    const [x0, y0] = ROUTE[s], [x1, y1] = ROUTE[s + 1];
    const f = clamp(reach - s);
    if (s === 0) ctx.moveTo(cx + x0, cy + y0);
    ctx.lineTo(cx + lerp(x0, x1, f), cy + lerp(y0, y1, f));
  }
  if (rp > 0) ctx.stroke();
  ctx.restore();
  ROUTE.forEach(([x, y], i) => {
    const on = P(lt, 1.0 + (i / segs) * 2.0 - 0.05, 1.0 + (i / segs) * 2.0 + 0.3);
    if (on <= 0) return;
    const last = i === ROUTE.length - 1;
    const col = last ? C.coral : C.white;
    ctx.fillStyle = col;
    ctx.beginPath(); ctx.arc(cx + x, cy + y, 7 * E.outBack(on), 0, TAU); ctx.fill();
    const pulse = ((lt - 1 - (i / segs) * 2) * 1.2) % 1;
    ctx.strokeStyle = hexA(last ? C.coral : C.cyan, (1 - pulse) * 0.8);
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(cx + x, cy + y, 8 + pulse * 30, 0, TAU); ctx.stroke();
  });
  // heading needle
  const hdg = 47 * E.outCubic(P(lt, 0.8, 2.6));
  ctx.save();
  ctx.translate(cx, cy); ctx.rotate((hdg * Math.PI) / 180);
  ctx.globalAlpha = E.outCubic(P(lt, 0.3, 0.8));
  ctx.fillStyle = C.coral;
  ctx.beginPath(); ctx.moveTo(0, -80); ctx.lineTo(12, 0); ctx.lineTo(-12, 0); ctx.closePath(); ctx.fill();
  ctx.fillStyle = C.white;
  ctx.beginPath(); ctx.moveTo(0, 80); ctx.lineTo(12, 0); ctx.lineTo(-12, 0); ctx.closePath(); ctx.fill();
  ctx.restore();
  // readouts
  const ra = E.outCubic(P(lt, 0.6, 1.2));
  if (ra > 0) {
    ctx.save(); ctx.globalAlpha = ra;
    setFont(500, 20, GROT, 5); ctx.fillStyle = hexA(C.white, 0.6); ctx.textAlign = 'left';
    const rx = cx + 300, ry = cy - 400;
    ctx.fillText('HEADING', rx, ry);
    ctx.fillText('POSITION', rx, ry + 110);
    setFont(700, 44, GROT, 2); ctx.fillStyle = C.white;
    ctx.fillText(`${String(Math.round(hdg)).padStart(3, '0')}°`, rx, ry + 52);
    setFont(500, 26, GROT, 2); ctx.fillStyle = C.cyan;
    ctx.fillText(scramble('N 36°51′04″', lt, 2.2, 11), rx, ry + 150);
    ctx.fillText(scramble('W 76°17′31″', lt, 2.4, 23), rx, ry + 186);
    ctx.restore();
  }
  const out = E.inExpo(P(lt, 3.5, 3.9));
  maskText('DIRECTION,', 150, H / 2 - 10, 120, E.outExpo(P(lt, 0.35, 1.0)), out);
  maskText('BY DESIGN.', 150, H / 2 + 120, 120, E.outExpo(P(lt, 0.5, 1.15)), out, { color: C.cyan });
}

const CUTS = ['BOLD', 'CLEAR', 'FAST', 'SHARP', 'SMOOTH', 'SIMPLE', 'HONEST', 'ALIVE'];
function sceneMontage(lt) {
  const ci = Math.min(7, Math.floor(lt / 0.5)), cl = lt - ci * 0.5;
  ctx.save();
  switch (ci) {
    case 0: {
      bg(C.navy); ctx.fillStyle = C.cyan;
      for (let i = 0; i < 12; i++) for (let j = 0; j < 7; j++) {
        const r = 30 * (0.5 + 0.5 * Math.sin(cl * 14 - (i + j) * 0.6));
        ctx.beginPath(); ctx.arc(120 + i * 153, 90 + j * 150, r, 0, TAU); ctx.fill();
      }
      break;
    }
    case 1: {
      bg(C.cyan); ctx.translate(W / 2, H / 2); ctx.rotate(-Math.PI / 6); ctx.fillStyle = C.deep;
      for (let x = -1800; x < 1800; x += 110) ctx.fillRect(x + ((cl * 700) % 110), -1400, 48, 2800);
      break;
    }
    case 2: {
      bg(C.white); ctx.fillStyle = C.navy;
      for (let i = 0; i < 9; i++) for (let j = 0; j < 5; j++) {
        ctx.save(); ctx.translate(160 + i * 200, 140 + j * 200); ctx.rotate(cl * Math.PI + (i + j) * 0.2);
        ctx.beginPath(); ctx.roundRect(-55, -55, 110, 110, 55 * E.inOutCubic(clamp(cl * 2.2))); ctx.fill(); ctx.restore();
      }
      break;
    }
    case 3: {
      bg(C.royal); ctx.strokeStyle = C.white; ctx.lineWidth = 6;
      for (let k = 0; k < 12; k++) {
        const r = (k * 110 + cl * 600) % 1320;
        ctx.globalAlpha = 1 - r / 1320;
        ctx.beginPath(); ctx.arc(W / 2, H / 2, r, 0, TAU); ctx.stroke();
      }
      break;
    }
    case 4: {
      bg(C.deep);
      for (let i = 0; i < 48; i++) {
        const h = (0.25 + 0.75 * Math.abs(Math.sin(i * 0.45 + cl * 16) * Math.sin(i * 0.13 + cl * 5))) * H * 0.8;
        ctx.fillStyle = i % 3 ? C.cyan : C.aqua;
        ctx.fillRect(40 * i + 4, H - h, 28, h);
      }
      break;
    }
    case 5: {
      bg(C.navy); ctx.fillStyle = C.aqua;
      for (let x = 20; x < W; x += 34) for (let y = 20; y < H; y += 34) {
        const r = 13 * (0.5 + 0.5 * Math.sin(x * 0.01 + y * 0.008 - cl * 12));
        ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
      }
      break;
    }
    case 6: {
      bg(C.coral); ctx.strokeStyle = C.deep; ctx.lineWidth = 8; ctx.translate(W / 2, H / 2);
      for (let k = 1; k <= 9; k++) {
        ctx.save(); ctx.rotate(cl * 3 * (k % 2 ? 1 : -1) + k * 0.2);
        const R = k * 80;
        ctx.beginPath();
        for (let v = 0; v < 3; v++) { const a = (v / 3) * TAU - Math.PI / 2; v ? ctx.lineTo(Math.cos(a) * R, Math.sin(a) * R) : ctx.moveTo(Math.cos(a) * R, Math.sin(a) * R); }
        ctx.closePath(); ctx.stroke(); ctx.restore();
      }
      break;
    }
    default: {
      bg(C.bg); ctx.translate(W / 2, H / 2); ctx.fillStyle = C.cyan;
      for (let k = 0; k < 320; k++) {
        const a = k * 0.35 + cl * 6, r = k * 3.1 * (0.6 + cl);
        ctx.globalAlpha = 1 - k / 320;
        ctx.beginPath(); ctx.arc(Math.cos(a) * r, Math.sin(a) * r, 2 + k * 0.03, 0, TAU); ctx.fill();
      }
    }
  }
  ctx.restore();
  ctx.save();
  ctx.globalCompositeOperation = 'difference';
  setFont(800, 200, SANS, -4);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.translate(W / 2, H / 2 + 10);
  const s = 1 + 0.18 * (1 - E.outExpo(clamp(cl / 0.2)));
  ctx.scale(s, s);
  ctx.fillStyle = '#FFFFFF';
  ctx.fillText(CUTS[ci], 0, 0);
  ctx.restore();
}

const ZOOM_WORDS = [['FIND', 0.25, 1.1], ['YOUR', 1.1, 1.95], ['FLOW', 1.95, 3.0]];
function sceneTunnel(lt) {
  tunnel.render(lt);
  for (const [w, a, b] of ZOOM_WORDS) {
    const p = P(lt, a, b);
    if (p <= 0 || p >= 1) continue;
    const s = lerp(0.55, 2.6, Math.pow(p, 2.2));
    const al = Math.min(1, p * 6) * (1 - P(p, 0.7, 1));
    ctx.save();
    ctx.globalAlpha = al;
    setFont(800, 190, SANS, -2);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.translate(W / 2, H / 2); ctx.scale(s, s);
    ctx.fillStyle = w === 'FLOW' ? C.cyan : C.white;
    ctx.shadowBlur = 30; ctx.shadowColor = 'rgba(34,211,238,0.6)';
    ctx.fillText(w, 0, 0);
    ctx.restore();
  }
  const wo = E.inExpo(P(lt, 2.85, 3.5));
  if (wo > 0) {
    const g = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, lerp(60, 1400, wo));
    g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.5, `rgba(255,255,255,${wo})`); g.addColorStop(1, `rgba(241,245,255,${wo * wo})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
}

function sceneLogo(lt) {
  const g = ctx.createRadialGradient(W / 2, H / 2 - 60, 0, W / 2, H / 2, W * 0.7);
  g.addColorStop(0, '#0C2156'); g.addColorStop(1, C.bg);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  drawParticles(lt + 20, 0.13, 0.35);
  const cx = W / 2, cy = H / 2 - 120, R = 92;
  // iris: full-screen white closes down into the emblem ring
  const iris = E.inOutExpo(P(lt, 0, 0.75));
  const ir = lerp(1250, R, iris);
  const fillA = 1 - P(lt, 0.55, 0.9);
  if (fillA > 0) { ctx.fillStyle = hexA('#FFFFFF', fillA); ctx.beginPath(); ctx.arc(cx, cy, ir, 0, TAU); ctx.fill(); }
  ctx.strokeStyle = C.white; ctx.lineWidth = 5;
  ctx.beginPath(); ctx.arc(cx, cy, ir, 0, TAU); ctx.stroke();
  // north notch
  const nn = E.outBack(P(lt, 0.8, 1.2));
  if (nn > 0) {
    ctx.fillStyle = C.cyan;
    ctx.beginPath(); ctx.moveTo(cx, cy - R - 26 * nn); ctx.lineTo(cx + 10 * nn, cy - R - 4); ctx.lineTo(cx - 10 * nn, cy - R - 4); ctx.closePath(); ctx.fill();
  }
  // waves inside the emblem
  ctx.save();
  ctx.beginPath(); ctx.arc(cx, cy, R - 8, 0, TAU); ctx.clip();
  [[C.cyan, -26], [C.white, 2], [C.royal, 30]].forEach(([col, off], k) => {
    const d = E.inOutCubic(P(lt, 0.6 + k * 0.12, 1.35 + k * 0.12));
    if (d <= 0) return;
    const pts = [];
    for (let x = cx - R; x <= cx - R + 2 * R * d; x += 3) pts.push([x, cy + off + 13 * Math.sin((x - cx) * 0.055 + lt * 2.2 + k * 0.9)]);
    ctx.lineCap = 'round';
    glowLine(pts, 8, col, 8);
  });
  ctx.restore();
  // wordmark, letter by letter
  const word = 'FLOW NAVY';
  const ls = lerp(46, 20, E.outExpo(P(lt, 1.0, 2.2)));
  setFont(700, 116, GROT, 0);
  const widths = [...word].map(ch => ctx.measureText(ch).width);
  const total = widths.reduce((a, b) => a + b, 0) + ls * (word.length - 1);
  let x = cx - total / 2;
  const wy = cy + 250;
  [...word].forEach((ch, i) => {
    const p = E.outExpo(P(lt, 1.0 + i * 0.05, 1.7 + i * 0.05));
    if (p > 0 && ch !== ' ') {
      ctx.save();
      ctx.beginPath(); ctx.rect(x - 10, wy - 120, widths[i] + 20, 150); ctx.clip();
      ctx.fillStyle = i < 4 ? C.white : C.cyan;
      ctx.textAlign = 'left';
      ctx.fillText(ch, x, wy + (1 - p) * 130);
      ctx.restore();
    }
    x += widths[i] + ls;
  });
  const dl = E.inOutCubic(P(lt, 1.8, 2.5));
  ctx.fillStyle = hexA(C.white, 0.35);
  ctx.fillRect(cx - 200 * dl, wy + 58, 400 * dl, 2);
  const ta = E.outCubic(P(lt, 2.1, 2.8));
  if (ta > 0) {
    ctx.save(); ctx.globalAlpha = ta;
    setFont(300, 42, SANS, 1); ctx.textAlign = 'center'; ctx.fillStyle = C.white;
    ctx.fillText('Find your flow.', cx, wy + 130 + (1 - ta) * 20);
    ctx.restore();
  }
  const ua = E.outCubic(P(lt, 2.5, 3.2));
  if (ua > 0) {
    ctx.save(); ctx.globalAlpha = ua;
    setFont(500, 26, GROT, lerp(18, 9, ua)); ctx.textAlign = 'center'; ctx.fillStyle = C.cyan;
    ctx.fillText('FLOWNAVY.COM', cx, wy + 200);
    ctx.restore();
  }
  const fo = P(lt, 5.1, 5.5);
  if (fo > 0) bg(hexA('#000000', fo));
}

export const SCENES = [
  [0, 3, 'OPEN', sceneOpen, false, 'A single line of light draws across the dark, starts to ripple, then splits into nine glowing currents. "SHOWREEL 2026" tracks in. The currents collapse into a white streak.'],
  [3, 7, 'FLOW', sceneFlow, false, 'Hard cut to a flow field of 1,700 particles streaming left to right like ocean currents while the camera slowly pushes in. "IDEAS / IN MOTION." rises from a mask, then exits upward.'],
  [7, 11, 'KINETIC', sceneSlam, false, 'Four type slams on the beat: MOVE, SHAPE, GUIDE and FLOW. Each hits with a skew, a camera shake and a white flash, over its own background color. Outline echoes scroll behind, and a progress bar fills along the bottom.'],
  [11, 15, '3D OCEAN', sceneWave, true, 'Real-time 3D (three.js): a flat plane of 78,000 points swells into a rolling ocean as the camera glides forward and lowers. "CHART / THE COURSE." rises in the lower left.'],
  [15, 19, 'NAVIGATE', sceneCompass, false, 'A navigation HUD. Compass rings draw on and counter-rotate, a radar sweep circles, and the needle swings to 047°. A route plots between waypoints to a coral target while the coordinates unscramble. "DIRECTION, / BY DESIGN."'],
  [19, 23, 'MONTAGE', sceneMontage, false, 'Eight rapid cuts, two per second, on the beat: dot grid, stripes, squares morphing into circles, ripples, EQ bars, halftone, nested triangles and a spiral. Each carries one word in difference-blend: BOLD, CLEAR, FAST, SHARP, SMOOTH, SIMPLE, HONEST, ALIVE.'],
  [23, 26.5, '3D TUNNEL', sceneTunnel, true, 'Real-time 3D: the camera accelerates through a tunnel of 150 counter-rotating open rings and 4,000 particles, rolling as it goes. "FIND / YOUR / FLOW" zooms through the lens, and the tunnel whites out.'],
  [26.5, 32, 'LOGO', sceneLogo, false, 'The white screen irises down into the emblem ring (a match cut), and a north notch pops on. Three waves draw inside the ring. "FLOW NAVY" rises letter by letter while the tracking tightens. Then the tagline and FLOWNAVY.COM appear, followed by a hold and a fade out.'],
];

// ---------- global overlays ----------
const grains = [0, 1, 2].map(k => {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const g = c.getContext('2d'); const d = g.createImageData(256, 256); const r = rng(k + 3);
  for (let i = 0; i < d.data.length; i += 4) { const v = r() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
  g.putImageData(d, 0, 0); return ctx.createPattern(c, 'repeat');
});
function overlays(t, idx) {
  // hard-cut flashes on scene boundaries without a wipe
  for (const at of [3, 19, 23]) {
    const f = P(t, at, at + 0.1);
    if (f > 0 && f < 1) bg(hexA('#FFFFFF', (1 - f) * 0.35));
  }
  // diagonal wipes
  for (const at of [7, 11, 15]) wipe(t, at);
  // HUD
  if (t < 26.5) {
    const a = P(t, 0.6, 1.2) * 0.7;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.globalCompositeOperation = 'difference';
    ctx.fillStyle = '#FFFFFF';
    setFont(700, 17, GROT, 6); ctx.textAlign = 'left';
    ctx.fillText('FLOW NAVY', 70, 76);
    setFont(400, 17, GROT, 6);
    ctx.fillText('SHOWREEL ’26', 70 + 170, 76);
    const fr = Math.floor(t * 30);
    const tc = `00:00:${String(Math.floor(fr / 30)).padStart(2, '0')}:${String(fr % 30).padStart(2, '0')}`;
    ctx.textAlign = 'right';
    ctx.fillText(tc, W - 70, 76);
    ctx.fillText('FLOWNAVY.COM', W - 70, H - 60);
    ctx.textAlign = 'left';
    ctx.fillText(`${String(idx + 1).padStart(2, '0')} — ${SCENES[idx][2]}`, 70, H - 60);
    ctx.fillRect(70, 94, 60 + 1720 * (t / 26.5), 1);
    ctx.restore();
  }
  // vignette + grain
  const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.5)');
  ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  ctx.save();
  ctx.globalAlpha = 0.05;
  ctx.fillStyle = grains[Math.floor(t * 30) % 3];
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
}
function wipe(t, at) {
  const d = 0.28, skew = 360;
  let l, r;
  if (t >= at - d && t < at) { l = -skew; r = lerp(-skew, W + skew, E.inOutExpo(P(t, at - d, at))); }
  else if (t >= at && t < at + d) { l = lerp(-skew, W + skew, E.inOutExpo(P(t, at, at + d))); r = W + skew; }
  else return;
  ctx.fillStyle = C.cyan;
  ctx.beginPath(); ctx.moveTo(l, H); ctx.lineTo(l + skew, 0); ctx.lineTo(r + skew, 0); ctx.lineTo(r, H); ctx.closePath(); ctx.fill();
  ctx.fillStyle = C.white;
  ctx.beginPath(); ctx.moveTo(r - 24, H); ctx.lineTo(r - 24 + skew, 0); ctx.lineTo(r + skew, 0); ctx.lineTo(r, H); ctx.closePath(); ctx.fill();
}

// ---------- frame ----------
export function renderAt(t) {
  t = clamp(t, 0, DUR - 1e-6);
  let idx = SCENES.findIndex(s => t >= s[0] && t < s[1]);
  if (idx < 0) idx = SCENES.length - 1;
  const [st, , , draw] = SCENES[idx];
  ctx.clearRect(0, 0, W, H);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.letterSpacing = '0px';
  draw(t - st, t);
  overlays(t, idx);
}

window.renderAt = renderAt;
window.SCENES = SCENES.map(s => ({ start: s[0], end: s[1], label: s[2], note: s[5] }));
window.DUR = DUR;

await document.fonts.load(`800 100px "${SANS}"`);
await document.fonts.load(`300 100px "${SANS}"`);
await document.fonts.load(`700 100px "${GROT}"`);
await document.fonts.load(`400 100px "${GROT}"`);
window.ready = true;

// ---------- live playback ----------
if (new URLSearchParams(location.search).has('render')) {
  document.body.classList.add('render');
} else {
  const stage = document.getElementById('stage');
  const fit = () => {
    const s = Math.min(innerWidth / W, innerHeight / H);
    stage.style.transform = `translate(${(innerWidth - W * s) / 2}px, ${(innerHeight - H * s) / 2}px) scale(${s})`;
  };
  addEventListener('resize', fit); fit();
  let playing = true, t0 = performance.now(), cur = 0;
  addEventListener('keydown', e => {
    if (e.code === 'Space') { playing = !playing; t0 = performance.now() - cur * 1000; }
    if (e.code === 'ArrowRight') { cur = Math.min(DUR, cur + 1); t0 = performance.now() - cur * 1000; }
    if (e.code === 'ArrowLeft') { cur = Math.max(0, cur - 1); t0 = performance.now() - cur * 1000; }
  });
  const loop = now => {
    if (playing) cur = ((now - t0) / 1000) % DUR;
    renderAt(cur);
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
}
