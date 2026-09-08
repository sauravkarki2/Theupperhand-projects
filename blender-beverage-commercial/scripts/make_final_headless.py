"""
make_final_headless.py
======================
Bake the splash and render the full sequence in a headless Blender process.

    blender -b "C:\\Users\\Public\\New.blend" -P make_final_headless.py

Options after `--`:
    --skip-bake            render only (cache already baked)
    --skip-render          bake only
    --samples 512          final sample count
    --pct 100              resolution percentage
    --start 1 --end 300    frame range override
    --preview              fast pass: 50%, 128 samples, no motion blur

WHY HEADLESS
------------
Long modal operators (`fluid.bake_data`, animation renders) block Blender's
main thread. Driven over a socket bridge that starves the connection and the
session dies. Background mode has no UI loop to starve: the operators run
synchronously and the process exits cleanly.

RESUMABLE
---------
The .blend ships with Overwrite OFF and Placeholders ON. Each frame claims its
output file before rendering, so re-running after a crash picks up where it
stopped, and a second process on another machine skips frames already claimed.
"""

import argparse
import os
import sys
import time

import bpy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser(prog="make_final_headless")
    p.add_argument("--skip-bake", action="store_true")
    p.add_argument("--skip-render", action="store_true")
    p.add_argument("--samples", type=int, default=512)
    p.add_argument("--pct", type=int, default=100)
    p.add_argument("--start", type=int, default=None)
    p.add_argument("--end", type=int, default=None)
    p.add_argument("--preview", action="store_true")
    p.add_argument("--domain", default="SIM_domain")
    return p.parse_args(argv)


def human(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return "%dh %02dm %02ds" % (h, m, s) if h else "%dm %02ds" % (m, s)


def banner(title):
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)
    sys.stdout.flush()


def enable_sim(name):
    """The interactive file keeps the domain disabled — an unbaked Mantaflow
    domain in the evaluation path can stall Blender. Turn it on only here."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        print("WARNING: no object %r — skipping sim entirely" % name)
        return None, None
    for coll in (bpy.data.collections.get("SIM"),
                 bpy.data.collections.get("FORCES")):
        if coll:
            coll.hide_viewport = False
            coll.hide_render = False
    for n in ("SIM_domain", "SIM_emitter"):
        o = bpy.data.objects.get(n)
        if o:
            o.hide_viewport = False
    mod = next((m for m in obj.modifiers if m.type == "FLUID"), None)
    if mod is None or mod.fluid_type != "DOMAIN":
        print("WARNING: %r has no Fluid Domain modifier" % name)
        return obj, None
    mod.show_viewport = True
    mod.show_render = True
    obj.hide_render = True          # the domain box itself never renders
    return obj, mod.domain_settings


def bake(obj, ds):
    cache = bpy.path.abspath(ds.cache_directory)
    os.makedirs(cache, exist_ok=True)
    frames = ds.cache_frame_end - ds.cache_frame_start + 1
    size = max(obj.dimensions)
    banner("STAGE 1 — FLUID BAKE")
    print("domain      : %s  (%.3f m)" % (obj.name, size))
    print("resolution  : %d  -> %.2f mm cells"
          % (ds.resolution_max, size / ds.resolution_max * 1000.0))
    print("frames      : %d-%d  (%d)"
          % (ds.cache_frame_start, ds.cache_frame_end, frames))
    print("cache       : %s" % cache)
    sys.stdout.flush()

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    t0 = time.time()
    with bpy.context.temp_override(active_object=obj, object=obj,
                                   selected_objects=[obj]):
        try:
            bpy.ops.fluid.free_data()
        except Exception as exc:                       # noqa: BLE001
            print("(no cache to free: %s)" % exc)
        bpy.ops.fluid.bake_data()
        try:
            bpy.ops.fluid.bake_mesh()
        except Exception as exc:                       # noqa: BLE001
            print("mesh bake skipped: %s" % exc)
    dt = time.time() - t0

    def stats(sub):
        path = os.path.join(cache, sub)
        if not os.path.isdir(path):
            return 0, 0.0
        fs = os.listdir(path)
        return len(fs), sum(os.path.getsize(os.path.join(path, f))
                            for f in fs) / 1e6

    nd, md = stats("data")
    nm, mm = stats("mesh")
    print("bake done in %s   data %d files (%.0f MB)   mesh %d files (%.0f MB)"
          % (human(dt), nd, md, nm, mm))
    if nd == 0:
        print("WARNING: zero data files. Check the inflow sits INSIDE the "
              "domain and that Use Flow is keyed on.")
    sys.stdout.flush()


def configure_render(a):
    sc = bpy.context.scene
    cy = sc.cycles
    if a.preview:
        sc.render.resolution_percentage = 50
        cy.samples = 128
        cy.transmission_bounces = 12
        cy.max_bounces = 16
        cy.adaptive_threshold = 0.02
        sc.render.use_motion_blur = False
    else:
        sc.render.resolution_percentage = a.pct
        cy.samples = a.samples
        cy.adaptive_threshold = 0.01
        # Transmission is THE setting for this shot: light must survive
        # ribbon -> cup wall -> drink -> cup wall -> ice -> lens.
        cy.transmission_bounces = 20
        cy.max_bounces = 24
        cy.glossy_bounces = 8
        cy.transparent_max_bounces = 16
        cy.blur_glossy = 1.0
        cy.sample_clamp_indirect = 10.0
        sc.render.use_motion_blur = True
        sc.render.motion_blur_shutter = 0.5

    cy.device = "GPU"
    cy.use_adaptive_sampling = True
    cy.use_denoising = True
    try:
        cy.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.render.use_persistent_data = True
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    if a.start is not None:
        sc.frame_start = a.start
    if a.end is not None:
        sc.frame_end = a.end
    return sc


def render(a):
    sc = configure_render(a)
    out = bpy.path.abspath(sc.render.filepath)
    os.makedirs(out, exist_ok=True)
    n = sc.frame_end - sc.frame_start + 1
    px = (int(sc.render.resolution_x * sc.render.resolution_percentage / 100),
          int(sc.render.resolution_y * sc.render.resolution_percentage / 100))

    banner("STAGE 2 — SEQUENCE RENDER")
    print("frames      : %d-%d  (%d)" % (sc.frame_start, sc.frame_end, n))
    print("resolution  : %dx%d   samples %d   motion blur %s"
          % (px[0], px[1], sc.cycles.samples, sc.render.use_motion_blur))
    print("transmission: %d bounces" % sc.cycles.transmission_bounces)
    print("output      : %s" % out)
    print("resumable   : overwrite=%s placeholders=%s"
          % (sc.render.use_overwrite, sc.render.use_placeholder))
    sys.stdout.flush()

    # Time one frame first so the projection is measured, not guessed.
    probe = sc.frame_start + n // 2
    sc.frame_set(probe)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    per = time.time() - t0
    print("\nprobe frame %d took %.1f s  ->  estimated total %s for %d frames"
          % (probe, per, human(per * n), n))
    print("starting full sequence ...\n")
    sys.stdout.flush()

    t0 = time.time()
    bpy.ops.render.render(animation=True)
    dt = time.time() - t0

    done = len([f for f in os.listdir(out) if f.lower().endswith(".png")])
    banner("DONE")
    print("elapsed     : %s   (%.1f s/frame)" % (human(dt), dt / max(n, 1)))
    print("png files   : %d" % done)
    print("output      : %s" % out)
    if done < n:
        print("NOTE: %d frames missing. Re-run this script to resume — "
              "placeholders make it pick up where it stopped." % (n - done))


def main():
    a = parse_args()
    print("blend: %s" % bpy.data.filepath)
    if not a.skip_bake:
        obj, ds = enable_sim(a.domain)
        if ds is not None:
            bake(obj, ds)
    else:
        enable_sim(a.domain)
        print("skipping bake (--skip-bake)")
    if not a.skip_render:
        render(a)
    else:
        print("skipping render (--skip-render)")


if __name__ == "__main__":
    main()
