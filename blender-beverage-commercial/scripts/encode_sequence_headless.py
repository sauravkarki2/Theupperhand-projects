"""
encode_sequence_headless.py
===========================
Turn the rendered PNG sequence into delivery MP4s using Blender's own FFmpeg,
so no separate ffmpeg install is needed.

    blender -b -P encode_sequence_headless.py -- --dir "C:\\Users\\Public\\mrlemon_render"

Options:
    --fps 30
    --preset social      9:16 vertical H.264, the native format  (default)
    --preset all         also writes a 1:1 and a 16:9 centre-crop
"""

import argparse
import glob
import os
import re
import sys

import bpy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser(prog="encode_sequence_headless")
    p.add_argument("--dir", default=r"C:\Users\Public\mrlemon_render")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--preset", choices=("social", "all"), default="social")
    p.add_argument("--crf", type=int, default=18)
    return p.parse_args(argv)


def frame_files(d):
    files = sorted(glob.glob(os.path.join(d, "*.png")))
    real = []
    for f in files:
        # Placeholders are zero-byte claims, not finished frames.
        if os.path.getsize(f) > 1024:
            real.append(f)
    return files, real


def build(a, name, w, h):
    sc = bpy.context.scene
    files, real = frame_files(a.dir)
    if not real:
        raise SystemExit("ERROR: no finished PNGs in %s" % a.dir)

    nums = [int(re.findall(r"(\d+)", os.path.basename(f))[-1]) for f in real]
    first, last = min(nums), max(nums)

    sc.sequence_editor_clear()
    se = sc.sequence_editor_create()
    strip = se.sequences.new_image(
        name="seq", filepath=real[0], channel=1, frame_start=1)
    for f in real[1:]:
        strip.elements.append(os.path.basename(f))

    sc.frame_start = 1
    sc.frame_end = len(real)
    sc.render.fps = a.fps
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100

    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = (
        "HIGH" if a.crf <= 18 else "MEDIUM")
    sc.render.ffmpeg.ffmpeg_preset = "GOOD"
    sc.render.ffmpeg.gopsize = a.fps * 2
    sc.render.ffmpeg.audio_codec = "NONE"

    out = os.path.join(a.dir, "MrLemon_%s.mp4" % name)
    sc.render.filepath = out
    sc.render.use_overwrite = True
    sc.render.use_placeholder = False

    print("encoding %-8s %dx%d  %d frames @ %d fps -> %s"
          % (name, w, h, len(real), a.fps, out))
    sys.stdout.flush()
    bpy.ops.render.render(animation=True)

    made = out if os.path.exists(out) else None
    if made:
        print("  wrote %.1f MB" % (os.path.getsize(out) / 1e6))
    return made, len(real), len(files) - len(real)


def main():
    a = parse_args()
    files, real = frame_files(a.dir)
    print("=" * 68)
    print("ENCODE  dir=%s" % a.dir)
    print("png files: %d   finished: %d   placeholders/empty: %d"
          % (len(files), len(real), len(files) - len(real)))
    print("=" * 68)
    if len(files) != len(real):
        print("NOTE: unfinished frames are skipped. Re-run the render to "
              "fill them before final delivery.")

    targets = [("vertical", 1080, 1920)]
    if a.preset == "all":
        targets += [("square", 1080, 1080), ("wide", 1920, 1080)]

    for name, w, h in targets:
        build(a, name, w, h)

    print("\nAll encodes complete.")


if __name__ == "__main__":
    main()
