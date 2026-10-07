"""Step 7 (section 10): assemble the EDIT scene in the Video Sequencer and export the MP4.

- Hard cuts between shots, except a 6-frame dip to black at the S5 -> S6 cut.
- S3 labels are clean Sequencer text (Playfair Display stand-in) with thin 1 px leader lines.
  The lines follow the orbiting camera, using anchors exported by s3_exploded.py.
  They are drawn as a transparent PNG overlay sequence (no text on any 3D object).
- S6: tagline in the serif italic, optional disclaimer line, and 'LOGO HERE' while no logo file exists.
- Sound per section 10; real files in assets/audio/ win over assets/audio/placeholder/.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from _common import (open_blend, save_blend, get_scene, hex_rgba, log, ROOT, ASSETS, RENDERS, CACHE, OUT,  # noqa: E402
                     SHOTS, GLOBAL_START, SHOT_FRAMES)

W, H = 1080, 1920
FONT_REG = os.path.join(ASSETS, "fonts", "PlayfairDisplay[wght].ttf")
FONT_ITA = os.path.join(ASSETS, "fonts", "PlayfairDisplay-Italic[wght].ttf")
INK = "#2E2B28"           # labels on the cream set
OFF_WHITE = "#F4F1EA"

LABELS = [  # (key, text, S3 local start frame, align, x, baseline y)  - normalised, y up
    ("cotton", "Quilted cotton exterior", 85, "RIGHT", 0.94, 0.705),
    ("silver", "Silver-thread conductive layer", 100, "RIGHT", 0.94, 0.215),
    ("snap", "Snap-button connection", 115, "LEFT", 0.06, 0.145),
]
LABEL_PX = 42
FADE = 12

open_blend()
sc = get_scene("EDIT")
sc.frame_start, sc.frame_end = 1, 600
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.render.fps = 30
sc.view_settings.view_transform = "Standard"
se = sc.sequence_editor_create()
for s in list(se.strips_all):
    if s.parent_meta is None:
        se.strips.remove(s)
if sc.animation_data:
    sc.animation_data_clear()


def frames_of(shot):
    idx = SHOTS.index(shot) + 1
    return sorted(glob.glob(os.path.join(RENDERS, f"s{idx}", "*.png")))


def image_seq(name, files, channel, start):
    st = se.strips.new_image(name=name, filepath=files[0], channel=channel, frame_start=start, fit_method="FIT")
    for f in files[1:]:
        st.elements.append(os.path.basename(f))
    return st


def key_alpha(strip, pairs):
    for f, a in pairs:
        strip.blend_alpha = a
        strip.keyframe_insert("blend_alpha", frame=f)


# ---------------------------------------------------------------- pictures
missing = []
strips = {}
for shot in SHOTS:
    files = frames_of(shot)
    start = GLOBAL_START[shot]
    n = SHOT_FRAMES[shot]
    if len(files) < n:
        missing.append(f"{shot} ({len(files)}/{n} frames)")
    if not files:
        continue
    strips[shot] = image_seq(shot, files[:n], 1, start)
    strips[shot].frame_final_duration = min(n, len(files))
if missing:
    log("WARNING missing renders: " + ", ".join(missing))

if "S6_Logo" not in strips:
    col = se.strips.new_effect(name="S6_card", type="COLOR", channel=1, frame_start=541, length=60)
    col.color = hex_rgba("#0A0A0A")[:3]

# 6-frame dip to black from S5 into S6 (S6 itself opens on the black card)
if "S5_Bed" in strips:
    key_alpha(strips["S5_Bed"], [(534, 1.0), (540, 0.0)])

# ---------------------------------------------------------------- S3 labels + leaders
font_reg = bpy.data.fonts.load(FONT_REG, check_existing=True)
font_ita = bpy.data.fonts.load(FONT_ITA, check_existing=True)


def _srgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def text(name, body, channel, start, end, x, y, size, colour, font, align="CENTER", alpha=1.0):
    st = se.strips.new_effect(name=name, type="TEXT", channel=channel, frame_start=start, length=end - start + 1)
    st.text = body
    st.font = font
    st.font_size = size
    st.color = (*_srgb(colour), alpha)          # Sequencer colours are display-referred sRGB
    st.location = (x, y)
    st.anchor_x = align
    st.alignment_x = align
    st.anchor_y = "BOTTOM"
    st.use_shadow = False
    st.blend_type = "ALPHA_OVER"
    return st


s3_start = GLOBAL_START["S3_Exploded"]
s3_end = s3_start + SHOT_FRAMES["S3_Exploded"] - 1
for i, (key, body, f0, align, x, y) in enumerate(LABELS):
    g0 = s3_start + f0 - 1
    st = text(f"label_{key}", body, 5 + i, g0, s3_end, x, y, LABEL_PX, INK, font_reg, align)
    key_alpha(st, [(g0, 0.0), (g0 + FADE, 1.0)])

# leader lines: anchor dot -> end of a hairline rule under the label, redrawn every frame
anchors_path = os.path.join(CACHE, "s3_label_anchors.json")
try:
    from PIL import Image, ImageDraw, ImageFont
    have_pil = True
except ImportError:
    have_pil = False
if have_pil and os.path.exists(anchors_path):
    anchors = json.load(open(anchors_path))
    pil_font = ImageFont.truetype(FONT_REG, LABEL_PX)
    ink = _srgb(INK)
    ink8 = tuple(int(c * 255) for c in ink)
    out_dir = os.path.join(RENDERS, "s3_labels")
    os.makedirs(out_dir, exist_ok=True)
    files = []
    first_local = min(l[2] for l in LABELS)
    for f in range(first_local, SHOT_FRAMES["S3_Exploded"] + 1):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        for key, body, f0, align, x, y in LABELS:
            a = max(0.0, min(1.0, (f - f0) / FADE))
            if a <= 0:
                continue
            tw = dr.textlength(body, font=pil_font)
            rule_y = H * (1 - y) + 10                      # just under the baseline
            if align == "RIGHT":
                x1 = W * x; x0 = x1 - tw
                end = (x0 - 6, rule_y)
            else:
                x0 = W * x; x1 = x0 + tw
                end = (x0 - 6, rule_y)
            ax, ay = anchors[str(f)][key]
            p = (ax * W, (1 - ay) * H)
            col = (*ink8, int(255 * a))
            dr.line([(x0 - 6, rule_y), (x1, rule_y)], fill=col, width=1)
            dr.line([p, end], fill=col, width=1)
            r = 4
            dr.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
        path = os.path.join(out_dir, f"{f:04d}.png")
        im.save(path)
        files.append(path)
    ov = image_seq("S3_leaders", files, 4, s3_start + first_local - 1)
    ov.blend_type = "ALPHA_OVER"
else:
    log("WARNING: leaders skipped (Pillow or cache/s3_label_anchors.json missing)")

# ---------------------------------------------------------------- S6 end card text
s6 = GLOBAL_START["S6_Logo"]
if not glob.glob(os.path.join(ASSETS, "logo", "*.png")):
    ph = text("logo_placeholder", "LOGO HERE", 8, s6, 600, 0.5, 0.53, 96, OFF_WHITE, font_reg, "CENTER")
    key_alpha(ph, [(s6, 0.0), (s6 + 14, 1.0)])
tag = text("tagline", "Sleep grounded. Wake restored.", 9, s6 + 14, 600, 0.5, 0.445, 64, OFF_WHITE, font_ita, "CENTER")
key_alpha(tag, [(s6 + 14, 0.0), (s6 + 29, 1.0)])
disc = text("disclaimer", "Not intended to diagnose or treat any condition.", 10, s6 + 29, 600,
            0.5, 0.05, 28, OFF_WHITE, font_reg, "CENTER", alpha=1.0)
key_alpha(disc, [(s6 + 29, 0.0), (s6 + 41, 0.6)])

# ---------------------------------------------------------------- sound
def audio(name):
    for ext in ("wav", "flac", "mp3", "ogg", "aif", "aiff"):
        for d in (os.path.join(ASSETS, "audio"), os.path.join(ASSETS, "audio", "placeholder")):
            p = os.path.join(d, f"{name}.{ext}")
            if os.path.exists(p):
                return p
    return None


SOUND = [  # (file stem, global start, channel, volume)
    ("music_bed", 1, 12, 0.30),
    ("rustle", 91, 13, 0.55),
    ("tones", 246, 14, 0.45),
    ("click", 400, 15, 1.00),     # the loudest moment in the film
    ("hum", 402, 16, 0.50),
]
for stem, start, ch, vol in SOUND:
    p = audio(stem)
    if p is None:
        log(f"WARNING: no audio for {stem}")
        continue
    snd = se.strips.new_sound(name=stem, filepath=p, channel=ch, frame_start=start)
    snd.volume = vol
    if stem == "music_bed":
        snd.frame_final_duration = 600
        snd.keyframe_insert("volume", frame=580)
        snd.volume = 0.0
        snd.keyframe_insert("volume", frame=600)
    log(f"sound {stem}: {os.path.relpath(p, ROOT)} at {start}")

# ---------------------------------------------------------------- export
os.makedirs(OUT, exist_ok=True)
r = sc.render
r.use_sequencer = True
r.use_compositing = False
r.image_settings.media_type = "VIDEO"
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"
r.ffmpeg.codec = "H264"
r.ffmpeg.constant_rate_factor = "HIGH"
r.ffmpeg.ffmpeg_preset = "BEST"
r.ffmpeg.audio_codec = "AAC"
r.ffmpeg.audio_bitrate = 192
r.ffmpeg.audio_channels = "STEREO"
r.ffmpeg.audio_mixrate = 48000
version = os.environ.get("ELLECTRIFY_VERSION", "v01")
r.filepath = os.path.join(OUT, f"ellectrify_blanket_{version}.mp4")
r.use_file_extension = False
save_blend()
if "--range" in sys.argv:                       # quick test: --range <first> <last>
    k = sys.argv.index("--range")
    sc.frame_start, sc.frame_end = int(sys.argv[k + 1]), int(sys.argv[k + 2])
if "--no-render" not in sys.argv:
    if bpy.context.window:
        bpy.context.window.scene = sc
    bpy.ops.render.render(animation=True, scene=sc.name)
    log(f"exported {os.path.relpath(r.filepath, ROOT)}")
