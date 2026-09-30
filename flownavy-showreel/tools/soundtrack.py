"""Synthesizes the Flow Navy showreel soundtrack (32 s, 120 BPM, D minor) to out/soundtrack.wav.

Every sound is generated here from oscillators and noise; there are no samples.
Cue times mirror the SCENES table and scene timings in main.js.
Usage: python3 tools/soundtrack.py   (needs numpy + scipy)
"""
import os
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
DUR = 32.0
BEAT = 0.5  # 120 BPM
N = int(SR * DUR)
rng = np.random.default_rng(7)

L = np.zeros(N)
R = np.zeros(N)
SEND = np.zeros(N)  # mono reverb send


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def filt(x, kind, f, order=2):
    wn = np.asarray(f, dtype=float) / (SR / 2)
    return sosfilt(butter(order, wn if wn.ndim else float(wn), btype=kind, output="sos"), x)


def sweep_filter(x, f0, f1, kind="lowpass", blocks=64):
    """Crude time-varying filter: process in overlapping blocks with an exponential cutoff sweep."""
    out = np.zeros_like(x)
    n = len(x)
    size = max(256, n // blocks)
    hop = size // 2
    win = np.hanning(size)
    for s in range(0, n, hop):
        seg = x[s:s + size]
        if len(seg) == 0:
            break
        fc = f0 * (f1 / f0) ** min(1.0, s / max(1, n - 1))
        y = filt(np.pad(seg, (0, size - len(seg))), kind, min(fc, SR / 2 * 0.95))
        out[s:s + size] += (y * win)[: len(seg)]
    return out


def env(n, a, d, curve=1.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(d, 1e-4))
    return e ** curve


def place(sig, t, gain=1.0, pan=0.0, send=0.0):
    i = int(round(t * SR))
    if i >= N:
        return
    sig = sig[: N - max(i, 0)]
    if i < 0:
        sig = sig[-i:]
        i = 0
    gl = gain * np.cos((pan + 1) * np.pi / 4)
    gr = gain * np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * gl
    R[i:i + len(sig)] += sig * gr
    SEND[i:i + len(sig)] += sig * gain * send


def secs(d):
    return np.arange(int(d * SR)) / SR


# ---------- instruments ----------
def kick(big=False):
    t = secs(0.9 if big else 0.45)
    f = 45 + 120 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * (3.5 if big else 7))
    click = filt(rng.standard_normal(len(t)), "highpass", 2000) * np.exp(-t * 250) * 0.3
    return np.tanh((body + click) * (2.2 if big else 1.6)) * 0.9


def clap():
    t = secs(0.35)
    n = filt(rng.standard_normal(len(t)), "bandpass", [900, 3500])
    e = np.zeros(len(t))
    for k, off in enumerate([0, 0.011, 0.022]):
        e += (t >= off) * np.exp(-np.maximum(0, t - off) * (90 if k < 2 else 16))
    return n * e * 0.55


def hat(open_=False):
    t = secs(0.25 if open_ else 0.06)
    n = filt(rng.standard_normal(len(t)), "highpass", 7000)
    return n * np.exp(-t * (14 if open_ else 70)) * 0.28


def saw(f, t, detune=0.0):
    ph = (f * (1 + detune)) * t
    return 2 * (ph - np.floor(ph + 0.5))


def pad(notes, d, bright=2400):
    t = secs(d)
    x = np.zeros(len(t))
    for m in notes:
        for dt in (-0.006, 0.0, 0.007):
            x += saw(hz(m), t, dt)
    x = filt(x / (3 * len(notes)), "lowpass", bright)
    e = np.minimum(1, t / 0.35) * np.minimum(1, (d - t) / 0.4)
    return x * np.clip(e, 0, 1)


def bass_note(m, d):
    t = secs(d)
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.tanh(3 * np.sin(2 * np.pi * f * t))
    x += 0.25 * filt(saw(f, t), "lowpass", 600)
    return x * env(len(t), 0.004, d * 0.6) * 0.55


def pluck(m, d=0.35):
    t = secs(d)
    f = hz(m)
    x = saw(f, t) * 0.5 + np.sin(2 * np.pi * 2 * f * t) * 0.3
    return filt(x, "lowpass", 3200) * env(len(t), 0.002, 0.12)


def bell(m, d=2.5):
    t = secs(d)
    f = hz(m)
    mod = np.sin(2 * np.pi * f * 3.5 * t) * 2.2 * np.exp(-t * 2.5)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 1.6)
    x += 0.3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 3)
    return x * 0.35


def impact(d=2.2):
    t = secs(d)
    f = 30 + 70 * np.exp(-t * 6)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.8)
    crash = filt(rng.standard_normal(len(t)), "bandpass", [300, 9000]) * np.exp(-t * 3.5) * 0.4
    return np.tanh(1.6 * (boom + crash)) * 0.9


def whoosh(d, up=True, lo=300, hi=6000):
    t = secs(d)
    n = rng.standard_normal(len(t))
    x = sweep_filter(n, lo if up else hi, hi if up else lo, "lowpass")
    e = np.sin(np.pi * t / d) ** 2
    return x * e * 0.5


def riser(d, lo=200, hi=8000, tonal=None):
    t = secs(d)
    x = sweep_filter(rng.standard_normal(len(t)), lo, hi, "lowpass")
    if tonal is not None:
        f = hz(tonal) * 2 ** (2 * (t / d) ** 2)
        x = x * 0.6 + 0.35 * saw(1, np.cumsum(f) / SR)
    e = (t / d) ** 2.2
    return x * e * 0.45


def blip(m, d=0.12):
    t = secs(d)
    return np.sin(2 * np.pi * hz(m) * t) * env(len(t), 0.001, 0.035) * 0.4


def ping(m):
    t = secs(1.2)
    return np.sin(2 * np.pi * hz(m) * t) * np.exp(-t * 5) * 0.22


# ---------- arrangement ----------
# D minor: Dm – Bb – F – C, one chord per bar (2 s), bars start on even seconds.
CHORDS = {0: [50, 53, 57, 62], 1: [46, 50, 53, 58], 2: [53, 57, 60, 65], 3: [48, 52, 55, 60]}
ROOTS = {0: 38, 1: 34, 2: 41, 3: 36}


def chord_at(t):
    return int(t // 2) % 4


# 0–3 OPEN: drone, the line's shimmer, riser into the cut
place(pad([38, 45, 50], 3.2, 900), 0.0, 0.5, send=0.4)
t = secs(1.2)
place(np.sin(2 * np.pi * np.cumsum(hz(74) * 2 ** (t * 1.2)) / SR) * np.sin(np.pi * t / 1.2) * 0.12, 0.1, 1.0, pan=-0.3, send=0.6)
for k, m in enumerate([62, 65, 69, 72, 74]):  # currents splitting
    place(bell(m, 1.5) * 0.5, 1.6 + k * 0.08, 0.6, pan=(k - 2) * 0.35, send=0.7)
place(riser(1.4, 300, 9000), 1.6, 0.8, send=0.3)
place(whoosh(0.4, up=False, lo=200, hi=5000), 2.55, 0.7)  # collapse into a streak

# 3–11 FLOW + KINETIC groove; 15–26 NAVIGATE / MONTAGE / TUNNEL groove
def groove(a, b, kicks=True, claps=True, hats=True, bass=True):
    beat = a
    while beat < b - 1e-6:
        if kicks:
            place(kick(), beat, 0.95)
        if claps and abs((beat % 1.0) - 0.5) < 1e-6:
            place(clap(), beat, 0.7, pan=0.05, send=0.25)
        if hats:
            place(hat(open_=abs((beat % 2.0) - 1.75) < 0.3), beat + 0.25, 0.8, pan=0.3)
            place(hat(), beat + 0.125, 0.35, pan=-0.3)
        if bass:
            for s in (0.0, 0.25):
                rt = ROOTS[chord_at(beat + s)]
                place(bass_note(rt + (12 if s and beat % 2 >= 1.5 else 0), 0.24), beat + s, 0.75)
        beat += BEAT


place(impact(), 3.0, 0.9, send=0.3)
groove(3.0, 11.0)
for bar in range(1, 16):  # pad across the whole groove
    s = bar * 2.0
    if s < 26.5:
        a = max(s, 3.0)
        place(pad(CHORDS[chord_at(s)], min(s + 2, 26.5) - a + 0.3, 1800 if 11 <= s < 15 else 2600), a, 0.32, send=0.5)

# KINETIC slams at 7, 8, 9, 10
for i, t0 in enumerate([7.0, 8.0, 9.0, 10.0]):
    place(impact(0.9) * 0.8, t0, 0.8, send=0.2)
    for m in CHORDS[chord_at(t0)]:
        place(pluck(m + 12, 0.5), t0, 0.35, pan=(i % 2 - 0.5) * 0.4, send=0.4)

# diagonal wipes centred on 7, 11, 15
for at in (7.0, 11.0, 15.0):
    place(whoosh(0.56), at - 0.28, 0.9, pan=-0.4)

# 11–15 3D OCEAN: breakdown — sub swell, sparse hats, opening pad, riser back in
for k in range(4):
    place(bass_note(ROOTS[chord_at(11 + k)], 1.0) * 0.6, 11.0 + k, 0.8)
for k in range(8):
    place(hat(), 11.25 + k * 0.5, 0.5, pan=0.3)
place(whoosh(3.2, up=True, lo=150, hi=1800) * 0.6, 11.2, 0.6, send=0.5)  # swell of the waves
place(riser(1.0, 400, 10000, tonal=62), 14.0, 0.7, send=0.3)

# 15–19 NAVIGATE: groove back, radar pings, coordinate ticks
groove(15.0, 19.0, claps=True)
for k in range(4):
    place(ping(81), 15.3 + k * 1.0, 1.0, pan=0.5, send=0.6)
for k in range(24):
    place(blip(96 + (k * 5) % 12, 0.03) * 0.5, 16.0 + k * 0.06, 0.4, pan=0.6)

# 19–23 MONTAGE: a pitched hit on every cut
arp = [74, 77, 81, 86, 70, 74, 77, 82]
groove(19.0, 23.0)
for k in range(8):
    t0 = 19.0 + k * 0.5
    place(pluck(arp[k], 0.3), t0, 0.5, pan=(-1) ** k * 0.5, send=0.35)
    place(blip(arp[k] + 12), t0, 0.35)

# 23–26.5 TUNNEL: build — kick drives to 25.5, accelerating snare roll, risers, word zooms
groove(23.0, 25.5, claps=False, hats=True)
t0, step = 23.0, 0.25
while t0 < 26.3:
    place(clap() * 0.7, t0, 0.4 + 0.8 * (t0 - 23) / 3.3, send=0.2)
    t0 += step
    step = max(0.0625, step * 0.9)
place(riser(3.4, 200, 12000, tonal=50), 23.0, 1.4, send=0.3)
for a in (23.25, 24.1, 24.95):
    place(whoosh(0.8, up=True, lo=400, hi=9000), a, 0.6, pan=0.3)
place(whoosh(0.65, up=True, lo=800, hi=14000), 25.85, 0.8)  # white-out

# 26.5–32 LOGO: impact, notch pop chime, waves, letters, tagline, URL, fade
place(kick(big=True), 26.5, 1.0)
place(impact(3.0), 26.5, 1.0, send=0.5)
place(pad([38, 50, 57, 62, 64, 69], 5.4, 2000), 26.5, 0.42, send=0.7)
place(bass_note(26, 4.0) * 0.8, 26.5, 0.8)
place(bell(86, 3.0), 27.3, 0.5, send=0.8)  # north notch pops on
for k in range(3):  # three waves draw in
    place(whoosh(0.75, up=True, lo=300, hi=3000) * 0.5, 27.1 + k * 0.12, 0.5, pan=(k - 1) * 0.5, send=0.5)
for i in range(9):  # FLOW NAVY letters rise
    place(blip(81 + [0, 3, 5, 7, 10, 12, 10, 7, 12][i], 0.08) * 0.5, 27.5 + i * 0.05, 0.4, pan=(i - 4) * 0.12, send=0.6)
place(bell(74, 3.0), 28.6, 0.45, send=0.8)  # tagline
place(bell(81, 3.0), 29.0, 0.35, send=0.8)  # FLOWNAVY.COM

# ---------- mix ----------
ir_t = secs(2.6)
irL = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.4)
irR = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.4)
send = filt(SEND, "highpass", 250)
wetL = fftconvolve(send, irL)[:N]
wetR = fftconvolve(send, irR)[:N]
wet_gain = 0.35 / max(np.abs(wetL).max(), np.abs(wetR).max(), 1e-9) * max(np.abs(L).max(), 1e-9) * 0.5
L += wetL * wet_gain
R += wetR * wet_gain

tt = np.arange(N) / SR
fade = np.clip((32.0 - tt) / 0.5, 0, 1) * np.clip(tt / 0.05, 0, 1)
mix = np.stack([L, R], 1) * fade[:, None]
mix = filt(mix.T, "highpass", 25).T
mix /= np.abs(mix).max()
mix = np.tanh(mix * 1.6) / np.tanh(1.6)  # glue / soft limit
mix *= 10 ** (-1 / 20) / np.abs(mix).max()

out = os.path.join(os.path.dirname(__file__), "..", "out", "soundtrack.wav")
os.makedirs(os.path.dirname(out), exist_ok=True)
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("wrote", os.path.abspath(out))
