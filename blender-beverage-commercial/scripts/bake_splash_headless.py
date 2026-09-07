"""
bake_splash_headless.py
=======================
Bake the Mantaflow splash in a SEPARATE, headless Blender process.

WHY THIS EXISTS
---------------
Triggering `bpy.ops.fluid.bake_data()` inside an interactive Blender that is
being driven over an MCP/socket bridge takes Blender down: the bridge runs on
Blender's main thread, and the bake blocks that thread for its entire duration,
so the addon's socket stops answering and the connection is dropped.

In background mode (`blender -b`) there is no UI event loop to starve and no
socket to lose. The operator runs synchronously, prints progress, and exits.
The cache lands on disk exactly where the .blend already points, so the
interactive session picks it up on reload.

USAGE
-----
    blender -b "C:\\Users\\Public\\New.blend" -P bake_splash_headless.py

Optional overrides, after a `--` separator:

    blender -b "New.blend" -P bake_splash_headless.py -- --resolution 140 --end 200

Close the interactive Blender first, or at least do not save over the file
while this runs — two processes writing one cache directory is asking for a
corrupt bake.
"""

import argparse
import os
import sys
import time

import bpy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser(prog="bake_splash_headless")
    p.add_argument("--domain", default="SIM_domain",
                   help="Name of the fluid domain object")
    p.add_argument("--resolution", type=int, default=None,
                   help="Override Resolution Divisions (default: leave as saved)")
    p.add_argument("--start", type=int, default=None, help="Cache start frame")
    p.add_argument("--end", type=int, default=None, help="Cache end frame")
    p.add_argument("--mesh", action="store_true",
                   help="Also bake the surface mesh after the data bake")
    p.add_argument("--free", action="store_true",
                   help="Free any existing cache first (recommended after "
                        "changing the scene)")
    return p.parse_args(argv)


def find_domain(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise SystemExit("ERROR: no object named %r in %s"
                         % (name, bpy.data.filepath))
    mod = next((m for m in obj.modifiers if m.type == "FLUID"), None)
    if mod is None or mod.fluid_type != "DOMAIN":
        raise SystemExit("ERROR: %r has no Fluid modifier set to Domain" % name)
    return obj, mod.domain_settings


def human(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return "%dh %02dm %02ds" % (h, m, s) if h else "%dm %02ds" % (m, s)


def main():
    args = parse_args()
    obj, ds = find_domain(args.domain)

    if args.resolution is not None:
        ds.resolution_max = args.resolution
    if args.start is not None:
        ds.cache_frame_start = args.start
    if args.end is not None:
        ds.cache_frame_end = args.end

    cache = bpy.path.abspath(ds.cache_directory)
    os.makedirs(cache, exist_ok=True)

    frames = ds.cache_frame_end - ds.cache_frame_start + 1
    size = max(obj.dimensions)
    print("=" * 66)
    print("HEADLESS FLUID BAKE")
    print("=" * 66)
    print("blend        : %s" % bpy.data.filepath)
    print("domain       : %s" % obj.name)
    print("domain size  : %.3f m  (largest axis)" % size)
    print("resolution   : %d   -> %.2f mm cells"
          % (ds.resolution_max, size / ds.resolution_max * 1000.0))
    print("frames       : %d - %d  (%d frames)"
          % (ds.cache_frame_start, ds.cache_frame_end, frames))
    print("cache        : %s" % cache)
    print("cache type   : %s" % ds.cache_type)
    print("=" * 66)
    sys.stdout.flush()

    # Operators still need a sane context even in background mode.
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    if args.free:
        print("[1/2] freeing existing cache ...")
        sys.stdout.flush()
        with bpy.context.temp_override(active_object=obj, object=obj,
                                       selected_objects=[obj]):
            try:
                bpy.ops.fluid.free_data()
            except Exception as exc:                      # noqa: BLE001
                print("      (nothing to free: %s)" % exc)

    print("[2/2] baking data ... this blocks until finished")
    sys.stdout.flush()
    t0 = time.time()
    with bpy.context.temp_override(active_object=obj, object=obj,
                                   selected_objects=[obj]):
        bpy.ops.fluid.bake_data()
    dt = time.time() - t0

    if args.mesh:
        print("      baking surface mesh ...")
        sys.stdout.flush()
        with bpy.context.temp_override(active_object=obj, object=obj,
                                       selected_objects=[obj]):
            bpy.ops.fluid.bake_mesh()

    def folder_stats(sub):
        path = os.path.join(cache, sub)
        if not os.path.isdir(path):
            return 0, 0.0
        files = os.listdir(path)
        total = sum(os.path.getsize(os.path.join(path, f)) for f in files)
        return len(files), total / 1e6

    n_data, mb_data = folder_stats("data")
    n_mesh, mb_mesh = folder_stats("mesh")

    print("=" * 66)
    print("DONE in %s  (%.1f s/frame)" % (human(dt), dt / max(frames, 1)))
    print("data files   : %d   (%.1f MB)" % (n_data, mb_data))
    print("mesh files   : %d   (%.1f MB)" % (n_mesh, mb_mesh))
    print("=" * 66)
    if n_data == 0:
        print("WARNING: no data files were written. Check that the inflow "
              "object sits INSIDE the domain and that Use Flow is keyed on.")
    print("Reopen the .blend in your interactive Blender to pick up the cache.")


if __name__ == "__main__":
    main()
