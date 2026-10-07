"""Step 6: render every shot to its PNG sequence: renders/sN/0001.png ...
Usage: python scripts/80_render.py [S1_Folded S2_Unfurl ...]   (default: all six)
Set ELLECTRIFY_QUALITY=preview for the CPU-friendly preview pass."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from _common import open_blend, SHOTS, RENDERS, log, apply_render_settings, PREVIEW  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
open_blend()
for name in args or SHOTS:
    sc = bpy.data.scenes[name]
    apply_render_settings(sc, standard_view=(name == "S6_Logo"))
    if name == "S6_Logo":
        sc.render.use_motion_blur = False
    idx = SHOTS.index(name) + 1
    out = os.path.join(RENDERS, f"s{idx}")
    os.makedirs(out, exist_ok=True)
    sc.render.filepath = os.path.join(out, "")
    if bpy.context.window:
        bpy.context.window.scene = sc
    t0 = time.time()
    bpy.ops.render.render(animation=True, scene=sc.name)
    n = sc.frame_end - sc.frame_start + 1
    log(f"{name}: {n} frames in {time.time() - t0:.0f}s ({(time.time() - t0) / n:.1f}s/frame)"
        f"{' [preview]' if PREVIEW else ''}")
