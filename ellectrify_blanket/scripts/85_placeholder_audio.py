"""Placeholder sound (section 10) until the real music bed and four effects are supplied.
Synthesised with numpy into assets/audio/placeholder/. 90_edit.py prefers files in assets/audio/
named music_bed / rustle / tones / click / hum (any wav/mp3/flac) and falls back to these.

  music_bed.wav  20 s  very quiet ambient pad, soft pulse only from S3 (7.5 s) on
  rustle.wav     3.7 s fabric rustle and air for the unfurl (global 91-200)
  tones.wav      1.0 s three soft rising tones 8 frames apart (global 246, 254, 262)
  click.wav      0.4 s one clean metallic snap click (global 400) - the loudest moment
  hum.wav        4.7 s low warm hum that rises with the pulse and resolves (global 402-541)
"""
import os
import wave

import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "audio", "placeholder")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, a, r, sustain=1.0):
    e = np.full(n, sustain)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, sustain, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def onepole_lp_fast(x, cutoff):
    from itertools import accumulate
    a = float(np.exp(-2 * np.pi * cutoff / SR))
    return np.fromiter(accumulate(x * (1 - a), lambda acc, v: v + a * acc), float, len(x))


def write(name, left, right=None, peak=0.9):
    right = left if right is None else right
    st = np.stack([left, right], axis=1)
    m = np.abs(st).max() or 1.0
    st = (st / m * peak * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
    print("wrote", name)


def note(f, t, detune=0.0):
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t + 0.3)
            + 0.12 * np.sin(2 * np.pi * 3 * f * (1 + detune) * t))


# ---- music bed: calm major-7 pad, slow chord changes, soft heartbeat-like pulse from 7.5 s
t = t_axis(20.0)
chords = [(0, [146.83, 220.0, 277.18, 369.99]),     # Dmaj7-ish
          (5, [123.47, 185.0, 246.94, 329.63]),     # Bm9-ish
          (10, [130.81, 196.0, 246.94, 329.63]),    # Cmaj7
          (15, [146.83, 220.0, 293.66, 369.99])]    # D
L = np.zeros_like(t); R = np.zeros_like(t)
for k, (start, freqs) in enumerate(chords):
    end = chords[k + 1][0] if k + 1 < len(chords) else 20.0
    m = (t >= start - 1.5) & (t < end + 1.5)
    w = np.clip(np.minimum((t - (start - 1.5)) / 2.0, ((end + 1.5) - t) / 2.0), 0, 1)
    for i, f in enumerate(freqs):
        L += w * m * note(f * (1 + 0.0015 * i), t) * 0.25
        R += w * m * note(f * (1 - 0.0015 * i), t + 0.004) * 0.25
air = onepole_lp_fast(rng.standard_normal(len(t)), 900) * 0.6
L += air; R += np.roll(air, 900)
beat = np.zeros_like(t)
for bt in np.arange(7.5, 19.4, 60 / 72):
    i = int(bt * SR); n = int(0.35 * SR)
    seg = t_axis(0.35)
    k = np.sin(2 * np.pi * (55 + 30 * np.exp(-seg * 25)) * seg) * np.exp(-seg * 9)
    beat[i:i + n] += k[: len(beat[i:i + n])]
beat *= np.clip((t - 7.5) / 2.0, 0, 1) * 0.5
L += beat; R += beat
fade = np.clip((20.0 - t) / (20 / 30), 0, 1)     # last 20 frames handled again in the edit
write("music_bed.wav", L * fade, R * fade)

# ---- fabric rustle and air
t = t_axis(3.7)
n = rng.standard_normal(len(t))
hp = n - onepole_lp_fast(n, 1500)
body = onepole_lp_fast(n, 600)
swell = np.clip(np.sin(np.pi * t / 3.7), 0, 1) ** 0.8 * (0.6 + 0.4 * np.sin(2 * np.pi * 1.3 * t) ** 2)
crackle = (rng.random(len(t)) < 0.0015) * rng.standard_normal(len(t)) * 3
x = (hp * 0.5 + body * 1.2 + onepole_lp_fast(crackle, 4000)) * swell
write("rustle.wav", x, np.roll(x, 600), peak=0.7)

# ---- three soft rising tones, 8 frames apart
t = t_axis(1.2)
x = np.zeros_like(t)
for k, (f0, f1) in enumerate([(392.0, 440.0), (440.0, 493.88), (493.88, 587.33)]):
    s = int(k * 8 / 30 * SR)
    tt = t_axis(0.6)
    f = f0 + (f1 - f0) * np.clip(tt / 0.25, 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = (np.sin(ph) + 0.2 * np.sin(2 * ph)) * env(len(tt), 0.03, 0.45) * np.exp(-tt * 2.5)
    x[s:s + len(tt)] += tone
write("tones.wav", x, peak=0.6)

# ---- one clean metallic snap click
t = t_axis(0.4)
tr = rng.standard_normal(len(t)) * np.exp(-t * 900)
tr = tr - onepole_lp_fast(tr, 2500)
ring = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d)
           for f, a, d in [(2830, 0.5, 60), (4170, 0.35, 75), (6310, 0.25, 90), (8900, 0.15, 120)])
thump = np.sin(2 * np.pi * 140 * t) * np.exp(-t * 60) * 0.6
write("click.wav", tr * 1.4 + ring + thump, peak=0.98)

# ---- low warm hum that rises with the pulse and resolves
t = t_axis(4.7)
f = 98.0
x = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t) + 0.25 * np.sin(2 * np.pi * 3 * f * t)
     + 0.12 * np.sin(2 * np.pi * 1.5 * f * t))
rise = np.interp(t, [0, 0.6, 1.6, 3.6, 4.7], [0, 0.6, 1.0, 0.55, 0.0])
res = np.clip((t - 3.0) / 1.0, 0, 1) * np.interp(t, [3, 4.7], [1, 0])
chord = sum(np.sin(2 * np.pi * ff * t) for ff in (196.0, 246.94, 293.66)) * 0.3 * res
x = onepole_lp_fast(x * rise + chord, 1800)
write("hum.wav", x, np.roll(x, 300), peak=0.6)
