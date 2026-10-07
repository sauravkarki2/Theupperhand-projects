"""Shared helpers for the Ellectrify Grounding Blanket build.

Every script can be run either way:
    blender -b blend/ellectrify_blanket.blend -P scripts/<name>.py
    python scripts/<name>.py            (with the `bpy` module installed)

Units are metres, Z is up, rotations are radians.
"""
import math
import os
import sys
import time

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLEND = os.path.join(ROOT, "blend", "ellectrify_blanket.blend")
ASSETS = os.path.join(ROOT, "assets")
PREVIEWS = os.path.join(ROOT, "previews")
RENDERS = os.path.join(ROOT, "renders")
CACHE = os.path.join(ROOT, "cache")
OUT = os.path.join(ROOT, "out")

SHOTS = ["S1_Folded", "S2_Unfurl", "S3_Exploded", "S4_Snap", "S5_Bed", "S6_Logo"]
SHOT_FRAMES = {  # local length in frames (section 9)
    "S1_Folded": 90, "S2_Unfurl": 135, "S3_Exploded": 150,
    "S4_Snap": 90, "S5_Bed": 75, "S6_Logo": 60,
}


def log(msg):
    print(f"[ellectrify] {msg}", flush=True)


# ---------------------------------------------------------------- blend file
def open_blend():
    """Open the project blend unless it is already the open file."""
    if not os.path.exists(BLEND):
        raise SystemExit("blend/ellectrify_blanket.blend not found - run scripts/00_setup.py first")
    if bpy.data.filepath and os.path.abspath(bpy.data.filepath) == os.path.abspath(BLEND):
        return
    bpy.ops.wm.open_mainfile(filepath=BLEND)


def save_blend():
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    log(f"saved {os.path.relpath(BLEND, ROOT)}")


# ---------------------------------------------------------------- idempotency
def remove_object(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return
    data = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if data is not None and data.users == 0:
        for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.lights, bpy.data.cameras):
            if data.name in coll and coll[data.name] == data:
                coll.remove(data)
                break


def remove_objects(prefixes):
    for ob in list(bpy.data.objects):
        if any(ob.name.startswith(p) for p in prefixes):
            remove_object(ob.name)


def get_collection(name, parent=None):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    if parent is not None and coll.name not in parent.children:
        parent.children.link(coll)
    return coll


def link_only(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)


def get_scene(name):
    sc = bpy.data.scenes.get(name)
    if sc is None:
        sc = bpy.data.scenes.new(name)
    return sc


def material(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        raise KeyError(f"material {name} missing - run scripts/20_materials.py")
    return mat


# ---------------------------------------------------------------- colour
def hex_rgba(h, a=1.0):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)


# ---------------------------------------------------------------- rendering
def gpu_setup():
    """Enable OptiX GPUs when present; report what Cycles will use."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    found = []
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
        except TypeError:
            continue
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == kind]
        if gpus:
            for d in prefs.devices:
                d.use = d.type == kind
            found = [(kind, d.name) for d in gpus]
            break
    if not found:
        prefs.compute_device_type = "NONE"
    return found


def apply_render_settings(sc, preview=False, standard_view=False, gpu=None):
    """Section 5 global render settings (adapted when no OptiX GPU exists)."""
    if gpu is None:
        gpu = bool(gpu_setup())
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU" if gpu else "CPU"
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    sc.render.resolution_percentage = 100
    sc.render.fps = 30
    sc.cycles.samples = 48 if preview else 192
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPTIX" if gpu else "OPENIMAGEDENOISE"
    sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    sc.cycles.max_bounces = 8
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 4
    sc.cycles.sample_clamp_indirect = 10
    sc.render.use_persistent_data = True
    sc.render.use_motion_blur = not standard_view
    sc.render.motion_blur_shutter = 0.5
    vs = sc.view_settings
    if standard_view:
        vs.view_transform = "Standard"
        vs.look = "None"
    else:
        vs.view_transform = "AgX"
        for look in ("AgX - Base Contrast", "Base Contrast"):
            try:
                vs.look = look
                break
            except TypeError:
                pass
    im = sc.render.image_settings
    im.file_format = "PNG"
    im.color_mode = "RGB"
    im.color_depth = "16"


def world_fill(sc, hex_colour="#F3EFE8", strength=0.6):
    """Section 8 fill: flat world colour, no HDRI."""
    name = f"WORLD_{sc.name}"
    w = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = hex_rgba(hex_colour)
    bg.inputs["Strength"].default_value = strength
    sc.world = w
    return w


def render_still(sc, path, frame=None):
    if frame is not None:
        sc.frame_set(frame)
    window_scene = bpy.context.window.scene if bpy.context.window else None
    if bpy.context.window:
        bpy.context.window.scene = sc
    sc.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True, scene=sc.name)
    dt = time.time() - t0
    if window_scene and bpy.context.window:
        bpy.context.window.scene = window_scene
    log(f"rendered {os.path.relpath(path, ROOT)} in {dt:.1f}s")
    return dt


def look_at(ob, target):
    from mathutils import Vector
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def deg(x):
    return math.radians(x)
