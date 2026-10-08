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

# ELLECTRIFY_QUALITY=final (default) follows section 5 exactly.
# ELLECTRIFY_QUALITY=preview renders at 50% / 16 samples with a coarser cloth grid (CPU-friendly).
QUALITY = os.environ.get("ELLECTRIFY_QUALITY", "final").lower()
PREVIEW = QUALITY == "preview"

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
    if PREVIEW:
        sc.render.resolution_percentage = 50
        sc.cycles.samples = 16
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
    im.color_depth = "8" if PREVIEW else "16"


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


# ---------------------------------------------------------------- shot building
GLOBAL_START = {"S1_Folded": 1, "S2_Unfurl": 91, "S3_Exploded": 226,
                "S4_Snap": 376, "S5_Bed": 466, "S6_Logo": 541}


def reset_scene(name, frames):
    """Get a shot scene and clear only objects it owns (prefixed with the shot code)."""
    sc = get_scene(name)
    code = name.split("_")[0] + "_"
    for ob in list(sc.collection.all_objects):
        if ob.name.startswith(code):
            remove_object(ob.name)
    sc.frame_start, sc.frame_end = 1, frames
    return sc, code


def place(sc, src, name, loc=None, rot=None, scale=None, parent=None):
    """Linked duplicate of a LIB object (shares mesh data and materials).
    Transforms left as None keep the LIB object's own transform."""
    remove_object(name)
    ob = bpy.data.objects[src].copy()
    ob.name = name
    if loc is not None:
        ob.location = loc
    if rot is not None:
        ob.rotation_euler = rot
    if scale is not None:
        ob.scale = scale
    ob.animation_data_clear()
    sc.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def empty(sc, name, loc=(0, 0, 0), rot=(0, 0, 0)):
    remove_object(name)
    ob = bpy.data.objects.new(name, None)
    ob.location, ob.rotation_euler = loc, rot
    ob.empty_display_size = 0.1
    sc.collection.objects.link(ob)
    return ob


def key_frames(target, data_path, frames, fn, index=-1):
    """Key `fn(frame)` on every frame with LINEAR interpolation, so curves are exact
    (strong ease-outs, linear camera moves) and never depend on Bezier handles."""
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    try:
        for f in frames:
            v = fn(f)
            if data_path.startswith('["'):
                target[data_path[2:-2]] = v
            elif index >= 0:
                getattr(target, data_path)[index] = v
            else:
                setattr(target, data_path, v)
            target.keyframe_insert(data_path, index=index, frame=f)
    finally:
        prefs.keyframe_new_interpolation_type = old


def ease_out(t, power=4):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** power


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def camera(sc, name, lens, fstop, aim, focus=None):
    """Camera with a Track To aim empty; focus on `focus` object (or the aim)."""
    remove_object(name)
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit = "AUTO"
    cd.clip_start = 0.005
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    tgt = empty(sc, name + "_aim", aim)
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    cd.dof.focus_object = focus or tgt
    sc.camera = cam
    return cam, tgt


def area_light(sc, name, size, size_y, energy, kelvin=5600, loc=(0, 0, 0), aim=(0, 0, 0)):
    remove_object(name)
    ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, "AREA")
    ld.type = "AREA"
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size, size_y
    ld.energy = energy
    ld.use_temperature = True
    ld.temperature = kelvin
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    sc.collection.objects.link(ob)
    look_at(ob, aim)
    return ob


def window_shadow(sc, name, key, target, frac=0.45):
    """Section 8: a frame with four vertical slots between the key and the product.
    Invisible to camera and reflections; only shades the key light."""
    import bmesh
    from mathutils import Vector
    remove_object(name)
    me = bpy.data.meshes.get(name)
    if me is not None:
        bpy.data.meshes.remove(me)
    bm = bmesh.new()
    W, H, bar = 2.6, 2.2, 0.16
    def rect(x0, x1, z0, z1):
        vs = [bm.verts.new((x0, 0, z0)), bm.verts.new((x1, 0, z0)), bm.verts.new((x1, 0, z1)), bm.verts.new((x0, 0, z1))]
        bm.faces.new(vs)
    rect(-W / 2 - 1.5, W / 2 + 1.5, H / 2, H / 2 + 1.5)          # top
    rect(-W / 2 - 1.5, W / 2 + 1.5, -H / 2 - 1.5, -H / 2)        # bottom
    rect(-W / 2 - 1.5, -W / 2, -H / 2, H / 2)                    # left
    rect(W / 2, W / 2 + 1.5, -H / 2, H / 2)                      # right
    slot = (W - 3 * bar) / 4
    for i in range(1, 4):                                        # 3 mullions -> 4 slots
        x = -W / 2 + i * slot + (i - 1) * bar
        rect(x, x + bar, -H / 2, H / 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    k, t = Vector(key.location), Vector(target)
    ob.location = k.lerp(t, frac)
    d = (t - k).normalized()
    ob.rotation_euler = d.to_track_quat("Y", "Z").to_euler()
    ob.visible_camera = False
    ob.visible_glossy = False
    ob.visible_transmission = False
    ob.visible_diffuse = False
    return ob


def room(sc, code, wall_y=2.0, floor=True, wall_w=12.0, wall_h=6.0, floor_mat="MAT_backdrop_floor"):
    """Backdrop wall behind the product (camera looks along +Y) and a floor."""
    import bmesh
    obs = []
    for nm, size, loc, rot, mat in [
        (code + "wall", (wall_w, wall_h), (0, wall_y, wall_h / 2), (math.radians(90), 0, 0), "MAT_backdrop"),
        (code + "floor", (wall_w, wall_w), (0, wall_y - wall_w / 2, 0), (0, 0, 0), floor_mat),
    ][: 2 if floor else 1]:
        remove_object(nm)
        me = bpy.data.meshes.get(nm)
        if me is not None:
            bpy.data.meshes.remove(me)
        bm = bmesh.new()
        sx, sy = size[0] / 2, size[1] / 2
        vs = [bm.verts.new(v) for v in ((-sx, -sy, 0), (sx, -sy, 0), (sx, sy, 0), (-sx, sy, 0))]
        bm.faces.new(vs)
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me); bm.free()
        me.materials.append(material(mat))
        ob = bpy.data.objects.new(nm, me)
        ob.location, ob.rotation_euler = loc, rot
        sc.collection.objects.link(ob)
        obs.append(ob)
    return obs


def blanket_object(sc, name, preview=None):
    """Per-shot cloth blanket: 1.52 x 2.03 m, ~12 mm grid (24 mm in preview),
    Cloth -> Solidify 15 mm (material offset 1) -> Subdivision 1."""
    import bmesh
    if preview is None:
        preview = PREVIEW
    nx, ny = (64, 85) if preview else (127, 169)
    remove_object(name)
    me = bpy.data.meshes.get(name)
    if me is not None:
        bpy.data.meshes.remove(me)
    bm = bmesh.new()
    verts = [[bm.verts.new(((i / nx - .5) * 1.52, (j / ny - .5) * 2.03, 0)) for i in range(nx + 1)]
             for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(material("MAT_quilt_cotton"))
    me.materials.append(material("MAT_silver_layer"))
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    return ob


def cloth_settings(ob, speed, pin_group=None):
    """Section 9 S2 cloth recipe."""
    cl = ob.modifiers.get("Cloth") or ob.modifiers.new("Cloth", "CLOTH")
    s = cl.settings
    s.mass = 0.45
    s.tension_stiffness = s.compression_stiffness = 15
    s.shear_stiffness = 5
    s.bending_stiffness = 8
    s.quality = 12
    s.time_scale = speed
    if pin_group:
        s.vertex_group_mass = pin_group
    c = cl.collision_settings
    c.use_collision = True
    c.use_self_collision = True
    c.self_distance_min = 0.006
    c.distance_min = 0.006
    return cl


def finish_blanket_stack(ob):
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness, sol.offset, sol.material_offset, sol.use_even_offset = 0.015, -1.0, 1, True
    sub = ob.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = sub.render_levels = 1


def bake_cloth(sc, ob):
    """Bake the cloth point cache by stepping frames in order, then lock it as baked."""
    cl = ob.modifiers["Cloth"]
    pc = cl.point_cache
    pc.frame_start, pc.frame_end = sc.frame_start, sc.frame_end
    pc.use_disk_cache = True
    t0 = time.time()
    try:
        with bpy.context.temp_override(scene=sc, point_cache=pc, active_object=ob, object=ob):
            bpy.ops.ptcache.free_bake()
            bpy.ops.ptcache.bake(bake=True)
        how = "ptcache.bake"
    except Exception as e:  # pragma: no cover - fallback when the operator lacks context
        log(f"ptcache.bake unavailable ({e}); stepping frames")
        for f in range(sc.frame_start, sc.frame_end + 1):
            sc.frame_set(f)
        how = "frame stepping"
    log(f"baked cloth {ob.name} frames {pc.frame_start}-{pc.frame_end} via {how} in {time.time() - t0:.0f}s")


def shot_light_rig(sc, code, target, key_offset=(-3.2, -1.4, 1.5), key_energy=600, rim=False, rim_energy=150,
                   window=True):
    from mathutils import Vector
    t = Vector(target)
    key = area_light(sc, code + "key", 4.0, 2.5, key_energy, 5600, t + Vector(key_offset), t)
    obs = [key]
    if window:
        obs.append(window_shadow(sc, code + "window", key, t))
    if rim:
        obs.append(area_light(sc, code + "rim", 1.8, 0.12, rim_energy, 5600, t + Vector((0.5, 2.0, 1.4)), t))
    world_fill(sc)
    return obs
