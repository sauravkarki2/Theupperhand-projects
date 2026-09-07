# -*- coding: utf-8 -*-
"""
build_beverage_ad.py
====================
Parametric scene builder for a beverage / product splash commercial in Blender,
reconstructing the setup seen in "lets make a beverage commercial in blender 2"
(Blender 3.6 LTS, native Mantaflow FLIP liquid).

DESIGN GOALS
------------
1. Idempotent-ish: running it twice into a fresh file gives the same scene.
2. Version tolerant: guarded attribute setting so it degrades gracefully across
   Blender 3.6 -> 4.x where socket and property names changed.
3. Staged: every stage is a separate function you can call on its own from the
   Python console, so you can rebuild just the lights or just the sim.
4. Art-directable: all the numbers live in CONFIG at the top.

USAGE
-----
    # Full build, from Blender's Scripting workspace:
    exec(open(r"C:\\path\\to\\build_beverage_ad.py").read())
    build_all()

    # Or stage by stage:
    reset_scene(); build_product(); build_set(); build_lights(); build_camera()
    build_fluid_domain(); build_emitter_on_curve(); build_force_rig()
    configure_render(preset="lookdev")

    # Headless:
    blender -b -P build_beverage_ad.py

NOT YET RUN AGAINST A LIVE BLENDER. Treat the first execution as a smoke test.
Every risky property write goes through `_set()`, which reports what it could not
set rather than raising, so a version mismatch produces a warning list, not a
traceback.
"""

import math
import os

import bpy
import mathutils
from mathutils import Vector, Euler

# ============================================================================
# CONFIG — every art-directable number lives here
# ============================================================================

CONFIG = {
    # ---- Scene / timing -----------------------------------------------------
    "fps": 24,
    "frame_start": 1,
    "frame_end": 250,
    "hero_frame": 163,          # the frame the whole shot is engineered to deliver
    "splash_impact_frame": 60,  # when the inflow starts throwing water
    "splash_burst_frames": 45,  # how long the inflow stays on

    # ---- Product ------------------------------------------------------------
    "bottle_height": 0.25,      # metres. Real 500ml PET bottle ~0.22-0.25 m.
    "bottle_radius": 0.033,
    "bottle_location": (0.0, 0.0, 0.0),

    # ---- Fluid domain (values read directly off the tutorial's UI) ----------
    "domain_size": (0.60, 0.60, 0.60),
    "domain_center": (0.0, 0.0, 0.18),
    "resolution": 100,          # PREVIEW. Final: 200-400. See modules/01.
    "flip_ratio": 0.97,
    "cfl": 4.0,
    "timesteps_min": 1,
    "timesteps_max": 4,
    "particle_radius": 1.0,
    "particle_sampling": 2,
    "particle_randomness": 0.1,
    "particle_min": 8,
    "particle_max": 16,
    "narrow_band_width": 3.0,
    "fractions_distance": 0.5,
    "open_domain": True,        # ALL border collisions OFF — the key choice
    "cache_dir": "//cache_fluid/",

    # ---- Emitter / curve ----------------------------------------------------
    "curve_radius": 0.14,       # radius of the spiral around the bottle
    "curve_turns": 1.25,
    "curve_z_start": 0.02,
    "curve_z_end": 0.26,
    "curve_points": 24,
    "emitter_radius": 0.018,
    "emitter_velocity_normal": 1.6,   # m/s thrown along the emitter normal

    # ---- Force rig (the three objects in the tutorial's "forces" collection) -
    "vortex_strength_peak": 6.0,
    "force_strength_peak": 9.0,
    "turbulence_strength_peak": 3.0,
    "turbulence_size": 0.6,

    # ---- Camera -------------------------------------------------------------
    "lens_mm": 105.0,
    "camera_distance": 1.05,
    "camera_height": 0.14,
    "camera_fstop": 3.2,
    "push_in_amount": 0.12,     # metres of dolly over the whole shot

    # ---- Lighting -----------------------------------------------------------
    "key_power": 300.0,
    "strip_power": 220.0,
    "back_power": 400.0,
    "reflection_card_power": 60.0,

    # ---- Backdrop -----------------------------------------------------------
    "bg_color_top": (1.000, 0.478, 0.094, 1.0),   # #FF7A18 saturated orange
    "bg_color_bottom": (0.769, 0.235, 0.000, 1.0),  # #C43C00 burnt amber
    "bg_emission_strength": 4.0,

    # ---- Render -------------------------------------------------------------
    "res_x": 1920,
    "res_y": 1080,
    "output_dir": "//render/",
}

COLLECTIONS = ["PRODUCT", "SIM", "FORCES", "LIGHTS", "CAM", "SET", "FX"]

_WARNINGS = []


# ============================================================================
# Helpers
# ============================================================================

def _set(obj, attr, value, label=None):
    """Set an attribute, recording a warning instead of raising if it's absent.

    Blender renames properties between versions. Rather than branch on
    bpy.app.version everywhere, we attempt the write and log misses. The
    warning list is printed at the end of build_all().
    """
    if obj is None:
        _WARNINGS.append("target is None for %s" % attr)
        return False
    if not hasattr(obj, attr):
        _WARNINGS.append("%s: no attribute '%s'" % (label or repr(obj), attr))
        return False
    try:
        setattr(obj, attr, value)
        return True
    except Exception as exc:  # noqa: BLE001 - we genuinely want any failure
        _WARNINGS.append("%s: could not set '%s' = %r (%s)"
                         % (label or repr(obj), attr, value, exc))
        return False


def _set_socket(node, names, value):
    """Set the first input socket that exists, from a list of candidate names.

    Blender 4.0 renamed many Principled BSDF sockets:
        Transmission        -> Transmission Weight
        Subsurface          -> Subsurface Weight
        Specular            -> Specular IOR Level
        Clearcoat           -> Coat Weight
        Emission            -> Emission Color
    Passing a list lets one call cover both eras.
    """
    if isinstance(names, str):
        names = [names]
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            try:
                socket.default_value = value
                return True
            except Exception as exc:  # noqa: BLE001
                _WARNINGS.append("socket %s: %s" % (name, exc))
    _WARNINGS.append("no socket found among %r on node %s" % (names, node.name))
    return False


def is_4x():
    return bpy.app.version >= (4, 0, 0)


def get_collection(name):
    """Fetch or create a top-level collection and link it to the scene."""
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def move_to_collection(obj, coll_name):
    """Unlink an object from everything and link it to exactly one collection."""
    coll = get_collection(coll_name)
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    coll.objects.link(obj)
    return obj


def iter_fcurves(obj):
    """Yield an object's F-curves across Blender 3.6 through 5.x.

    Blender 5.x replaced the flat `Action.fcurves` list with a layers /
    strips / slots hierarchy, so the old attribute raises AttributeError.
    `keyframe_insert()` is unchanged — only reading the curves back moved.
    """
    anim = getattr(obj, "animation_data", None)
    action = getattr(anim, "action", None)
    if action is None:
        return
    if hasattr(action, "fcurves"):          # 3.6 / 4.x
        for fcurve in action.fcurves:
            yield fcurve
        return
    for layer in action.layers:             # 5.x
        for strip in layer.strips:
            for slot in action.slots:
                bag = strip.channelbag(slot)
                if bag:
                    for fcurve in bag.fcurves:
                        yield fcurve


def keyframe(obj, data_path, frames_values, index=-1, interp="BEZIER"):
    """Set keyframes from [(frame, value), ...] and apply an interpolation mode.

    `data_path` is resolved on `obj`, so nested paths work for things like
    modifier or field properties when you pass the owning ID instead.
    """
    for frame, value in frames_values:
        # Resolve dotted paths so we can key e.g. "field.strength".
        target = obj
        path = data_path
        if "." in data_path:
            head, path = data_path.rsplit(".", 1)
            target = obj.path_resolve(head)
        if index >= 0:
            current = list(getattr(target, path))
            current[index] = value
            setattr(target, path, current)
        else:
            setattr(target, path, value)
        target.keyframe_insert(data_path=path, frame=frame,
                               index=index if index >= 0 else -1)

    # Apply interpolation to whatever we just created.
    for fcurve in iter_fcurves(obj):
        for kp in fcurve.keyframe_points:
            kp.interpolation = interp
            if interp == "BEZIER":
                kp.handle_left_type = "AUTO_CLAMPED"
                kp.handle_right_type = "AUTO_CLAMPED"


# ============================================================================
# Stage 0 — reset
# ============================================================================

def reset_scene(keep_startup=False):
    """Wipe the scene down to nothing so the build is deterministic."""
    if not keep_startup:
        bpy.ops.wm.read_factory_settings(use_empty=True)

    scene = bpy.context.scene
    scene.render.fps = CONFIG["fps"]
    scene.frame_start = CONFIG["frame_start"]
    scene.frame_end = CONFIG["frame_end"]
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"

    for name in COLLECTIONS:
        get_collection(name)

    print("[reset] scene cleared, %d collections ready" % len(COLLECTIONS))
    return scene


# ============================================================================
# Stage 1 — product
# ============================================================================

def build_product():
    """Build a placeholder bottle: body, cap, and a separate interior liquid mesh.

    The liquid MUST be its own mesh, slightly inset from the bottle wall. If the
    liquid and the bottle share a surface, Cycles sees coincident faces with
    different IORs and you get black artefacts and z-fighting. The inset is the
    fix, and it is also physically right — there is a thin air gap nowhere, but
    the renderer needs the separation.
    """
    h = CONFIG["bottle_height"]
    r = CONFIG["bottle_radius"]
    loc = Vector(CONFIG["bottle_location"])

    # --- body -------------------------------------------------------------
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64, radius=r, depth=h,
        location=loc + Vector((0, 0, h / 2.0)),
    )
    body = bpy.context.object
    body.name = "mountain_dew_bottle"
    move_to_collection(body, "PRODUCT")

    # Shade smooth + a bevel so the silhouette catches the strip lights.
    bpy.ops.object.shade_smooth()
    bevel = body.modifiers.new("Bevel", "BEVEL")
    _set(bevel, "width", 0.0015, "Bevel")
    _set(bevel, "segments", 3, "Bevel")
    _set(bevel, "limit_method", "ANGLE", "Bevel")

    subsurf = body.modifiers.new("Subdivision", "SUBSURF")
    _set(subsurf, "levels", 1, "Subsurf")
    _set(subsurf, "render_levels", 2, "Subsurf")

    # --- cap --------------------------------------------------------------
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=48, radius=r * 0.62, depth=h * 0.09,
        location=loc + Vector((0, 0, h + h * 0.045)),
    )
    cap = bpy.context.object
    cap.name = "bottle_cap"
    move_to_collection(cap, "PRODUCT")
    bpy.ops.object.shade_smooth()

    # --- interior liquid (inset!) ----------------------------------------
    inset = 0.0015
    liquid_h = h * 0.86
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64, radius=r - inset, depth=liquid_h,
        location=loc + Vector((0, 0, liquid_h / 2.0 + inset)),
    )
    liquid = bpy.context.object
    liquid.name = "bottle_liquid"
    move_to_collection(liquid, "PRODUCT")
    bpy.ops.object.shade_smooth()

    # --- materials --------------------------------------------------------
    body.data.materials.append(make_pet_plastic_material())
    cap.data.materials.append(make_cap_material())
    liquid.data.materials.append(make_amber_liquid_material())

    print("[product] bottle, cap, liquid built")
    return {"body": body, "cap": cap, "liquid": liquid}


# ============================================================================
# Stage 2 — materials
# ============================================================================

def _new_material(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def _principled(mat, location=(0, 0)):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = location
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (location[0] + 320, location[1])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return bsdf, out


def make_water_material():
    """The splash shader.

    Water is ~95% specular. Base Color is almost irrelevant; what matters is
    Transmission 1.0, Roughness 0.0, IOR 1.333, and enough transmission bounces
    in the render settings for light to survive the trip through it.

    We use Principled rather than Glass BSDF because Principled gives us a
    single node that also handles the tiny bit of reflection weighting, and it
    behaves better with Cycles' light-path clamping.
    """
    mat = _new_material("WATER_splash")
    bsdf, _ = _principled(mat)
    _set_socket(bsdf, "Base Color", (1.0, 1.0, 1.0, 1.0))
    _set_socket(bsdf, ["Transmission Weight", "Transmission"], 1.0)
    _set_socket(bsdf, "Roughness", 0.0)
    _set_socket(bsdf, "IOR", 1.333)
    # 4.x moved specular; harmless if absent.
    _set_socket(bsdf, ["Specular IOR Level", "Specular"], 0.5)
    _set(mat, "use_screen_refraction", True, "WATER")   # EEVEE
    _set(mat, "blend_method", "HASHED", "WATER")
    return mat


def make_pet_plastic_material():
    """Clear PET bottle wall. IOR ~1.46, near-zero roughness, slight thickness."""
    mat = _new_material("PET_plastic")
    bsdf, _ = _principled(mat)
    _set_socket(bsdf, "Base Color", (1.0, 1.0, 1.0, 1.0))
    _set_socket(bsdf, ["Transmission Weight", "Transmission"], 1.0)
    _set_socket(bsdf, "Roughness", 0.03)
    _set_socket(bsdf, "IOR", 1.46)
    _set(mat, "use_screen_refraction", True, "PET")
    _set(mat, "blend_method", "HASHED", "PET")
    return mat


def make_amber_liquid_material():
    """The soda itself.

    The saturated amber comes from VOLUME ABSORPTION, not from Base Color.
    Absorption is what makes the colour deepen with thickness — which is why a
    real bottle looks pale at the neck and rich through the belly. Base-colour
    tinting cannot do that and always reads as plastic.
    """
    mat = _new_material("AMBER_liquid")
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = nodes.new("ShaderNodeBsdfGlass")
    bsdf.location = (0, 200)
    _set_socket(bsdf, "Color", (1.0, 1.0, 1.0, 1.0))
    _set_socket(bsdf, "Roughness", 0.0)
    _set_socket(bsdf, "IOR", 1.35)

    absorb = nodes.new("ShaderNodeVolumeAbsorption")
    absorb.location = (0, -100)
    _set_socket(absorb, "Color", (1.0, 0.42, 0.05, 1.0))
    _set_socket(absorb, "Density", 55.0)

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (340, 60)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    links.new(absorb.outputs["Volume"], out.inputs["Volume"])
    return mat


def make_cap_material():
    mat = _new_material("CAP_plastic")
    bsdf, _ = _principled(mat)
    _set_socket(bsdf, "Base Color", (0.85, 0.28, 0.03, 1.0))
    _set_socket(bsdf, "Roughness", 0.35)
    _set_socket(bsdf, ["Coat Weight", "Clearcoat"], 0.4)
    return mat


def make_backdrop_material():
    """Emissive orange gradient.

    Built as an emissive plane rather than a world shader so it (a) reads as a
    real seamless sweep behind the product and (b) actually throws bounce light
    onto the bottle's shadow side. A world gradient lights the scene but has no
    position, so you lose the falloff that makes the backdrop feel like a set.
    """
    mat = _new_material("BACKDROP_gradient")
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    texco = nodes.new("ShaderNodeTexCoord")
    texco.location = (-700, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-520, 0)
    mapping.inputs["Rotation"].default_value = (0.0, math.radians(90.0), 0.0)

    grad = nodes.new("ShaderNodeTexGradient")
    grad.location = (-340, 0)
    grad.gradient_type = "LINEAR"

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-160, 0)
    ramp.color_ramp.elements[0].position = 0.05
    ramp.color_ramp.elements[0].color = CONFIG["bg_color_bottom"]
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = CONFIG["bg_color_top"]

    emit = nodes.new("ShaderNodeEmission")
    emit.location = (60, 0)
    _set_socket(emit, "Strength", CONFIG["bg_emission_strength"])

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (280, 0)

    links.new(texco.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], grad.inputs["Vector"])
    links.new(grad.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emit.inputs["Color"])
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


# ============================================================================
# Stage 3 — set
# ============================================================================

def build_set():
    """A large emissive plane behind the product, plus two white reflection cards.

    The cards are the least obvious and most important part. Water has almost no
    diffuse response — it only shows you what it reflects. Without big bright
    planes off-camera, a physically correct splash renders as a dark, muddy,
    unreadable blob no matter how many samples you throw at it.
    """
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 1.6, 0.6))
    backdrop = bpy.context.object
    backdrop.name = "BACKDROP"
    backdrop.rotation_euler = Euler((math.radians(90), 0, 0))
    move_to_collection(backdrop, "SET")
    backdrop.data.materials.append(make_backdrop_material())

    cards = []
    card_mat = _new_material("REFLECTION_card")
    emit_bsdf = card_mat.node_tree.nodes.new("ShaderNodeEmission")
    card_out = card_mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    _set_socket(emit_bsdf, "Strength", CONFIG["reflection_card_power"])
    _set_socket(emit_bsdf, "Color", (1.0, 1.0, 1.0, 1.0))
    card_mat.node_tree.links.new(emit_bsdf.outputs["Emission"],
                                 card_out.inputs["Surface"])

    for sign, label in ((-1, "L"), (1, "R")):
        bpy.ops.mesh.primitive_plane_add(size=1.6,
                                         location=(sign * 0.85, -0.15, 0.45))
        card = bpy.context.object
        card.name = "REFLECT_CARD_%s" % label
        card.rotation_euler = Euler((math.radians(90), 0,
                                     math.radians(90 * sign)))
        card.data.materials.append(card_mat)
        # Invisible to camera, visible to reflections/refractions only.
        _set(card, "visible_camera", False, card.name)
        _set(card, "visible_shadow", False, card.name)
        move_to_collection(card, "SET")
        cards.append(card)

    print("[set] backdrop + %d reflection cards built" % len(cards))
    return {"backdrop": backdrop, "cards": cards}


# ============================================================================
# Stage 4 — lighting
# ============================================================================

def build_lights():
    """The classic bottle rig: soft key, twin strips, backlight, top.

    The twin strips are the signature. Two tall narrow area lights raked from
    behind draw the bright vertical lines down both silhouette edges of the
    bottle. That pair of lines is what makes a bottle read as glass-and-liquid
    rather than as a grey cylinder, and it is visible in the reference frame.

    The backlight through the liquid is the other non-negotiable: it is the only
    thing that makes the amber contents GLOW instead of sitting there as a
    surface colour.
    """
    made = {}

    def add_area(name, location, rotation, size, size_y, power, color=(1, 1, 1),
                 shape="RECTANGLE", spread=math.radians(180)):
        light_data = bpy.data.lights.new(name, type="AREA")
        light_data.shape = shape
        light_data.size = size
        if shape in {"RECTANGLE", "ELLIPSE"}:
            light_data.size_y = size_y
        light_data.energy = power
        light_data.color = color
        _set(light_data, "spread", spread, name)
        obj = bpy.data.objects.new(name, light_data)
        obj.location = location
        obj.rotation_euler = Euler(rotation)
        move_to_collection(obj, "LIGHTS")
        made[name] = obj
        return obj

    # Broad soft key, upper front left.
    add_area("KEY_soft",
             location=(-0.75, -0.85, 0.95),
             rotation=(math.radians(52), 0, math.radians(-42)),
             size=1.2, size_y=1.2, power=CONFIG["key_power"],
             color=(1.0, 0.97, 0.93), shape="SQUARE")

    # Twin strip / edge lights, raked from behind.
    add_area("STRIP_left",
             location=(-0.55, 0.45, 0.28),
             rotation=(math.radians(90), 0, math.radians(-125)),
             size=0.05, size_y=1.1, power=CONFIG["strip_power"])

    add_area("STRIP_right",
             location=(0.55, 0.45, 0.28),
             rotation=(math.radians(90), 0, math.radians(125)),
             size=0.05, size_y=1.1, power=CONFIG["strip_power"])

    # Backlight through the liquid — makes the amber glow.
    add_area("BACK_through_liquid",
             location=(0.0, 0.95, 0.14),
             rotation=(math.radians(90), 0, math.radians(180)),
             size=0.7, size_y=0.7, power=CONFIG["back_power"],
             color=(1.0, 0.88, 0.72), shape="SQUARE")

    # Top light for the cap and shoulder.
    add_area("TOP_cap",
             location=(0.0, -0.1, 1.05),
             rotation=(0, 0, 0),
             size=0.6, size_y=0.6, power=CONFIG["key_power"] * 0.5,
             shape="SQUARE")

    print("[lights] %d lights built" % len(made))
    return made


# ============================================================================
# Stage 5 — camera
# ============================================================================

def build_camera():
    """Long lens, hero-low angle, DOF focused on the label via an empty.

    105 mm because a long lens keeps the bottle's vertical edges parallel. A
    wide lens splays them outward and instantly reads as amateur product work.
    Focus goes on an empty parented to the bottle so the focus plane tracks the
    product if you animate it.
    """
    cam_data = bpy.data.cameras.new("CAM_hero")
    cam_data.lens = CONFIG["lens_mm"]
    cam_data.sensor_width = 36.0
    cam = bpy.data.objects.new("CAM_hero", cam_data)
    cam.location = (0.0, -CONFIG["camera_distance"], CONFIG["camera_height"])
    cam.rotation_euler = Euler((math.radians(88.0), 0.0, 0.0))
    move_to_collection(cam, "CAM")
    bpy.context.scene.camera = cam

    # Focus target.
    focus = bpy.data.objects.new("CAM_focus_target", None)
    focus.empty_display_type = "PLAIN_AXES"
    focus.empty_display_size = 0.03
    focus.location = (0.0, 0.0, CONFIG["bottle_height"] * 0.55)
    move_to_collection(focus, "CAM")

    cam_data.dof.use_dof = True
    cam_data.dof.focus_object = focus
    cam_data.dof.aperture_fstop = CONFIG["camera_fstop"]

    # Slow push-in across the whole shot. Constant-ish, eased at both ends.
    y_start = -CONFIG["camera_distance"]
    y_end = y_start + CONFIG["push_in_amount"]
    keyframe(cam, "location",
             [(CONFIG["frame_start"], y_start), (CONFIG["frame_end"], y_end)],
             index=1)

    print("[camera] %.0fmm, f/%.1f, push-in %.2fm"
          % (CONFIG["lens_mm"], CONFIG["camera_fstop"], CONFIG["push_in_amount"]))
    return {"camera": cam, "focus": focus}


# ============================================================================
# Stage 6 — fluid domain
# ============================================================================

def build_fluid_domain():
    """The Mantaflow liquid domain, with every value from the reference UI.

    The one choice that defines the look: ALL SIX BORDER COLLISIONS OFF. That
    makes the domain an open window rather than a sealed tank. Water that
    reaches the boundary leaves and is deleted — no bounce-back, no pooling, no
    slosh. An ad splash must feel like it exists in a void; a closed domain
    gives you an aquarium.
    """
    sx, sy, sz = CONFIG["domain_size"]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=CONFIG["domain_center"])
    dom = bpy.context.object
    dom.name = "FLUID_DOMAIN"
    dom.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(dom, "SIM")
    dom.display_type = "WIRE"
    _set(dom, "hide_render", True, "FLUID_DOMAIN")

    bpy.ops.object.modifier_add(type="FLUID")
    fluid = dom.modifiers["Fluid"]
    fluid.fluid_type = "DOMAIN"
    ds = fluid.domain_settings
    ds.domain_type = "LIQUID"

    L = "domain_settings"
    _set(ds, "resolution_max", CONFIG["resolution"], L)
    _set(ds, "time_scale", 1.0, L)
    _set(ds, "cfl_condition", CONFIG["cfl"], L)
    _set(ds, "use_adaptive_timesteps", True, L)
    _set(ds, "timesteps_max", CONFIG["timesteps_max"], L)
    _set(ds, "timesteps_min", CONFIG["timesteps_min"], L)
    _set(ds, "gravity", (0.0, 0.0, -9.81), L)
    _set(ds, "delete_in_obstacle", True, L)

    # Simulation method / particle behaviour.
    _set(ds, "simulation_method", "FLIP", L)
    _set(ds, "flip_ratio", CONFIG["flip_ratio"], L)
    _set(ds, "sys_particle_maximum", 0, L)
    _set(ds, "particle_radius", CONFIG["particle_radius"], L)
    _set(ds, "particle_number", CONFIG["particle_sampling"], L)
    _set(ds, "particle_randomness", CONFIG["particle_randomness"], L)
    _set(ds, "particle_max", CONFIG["particle_max"], L)
    _set(ds, "particle_min", CONFIG["particle_min"], L)
    _set(ds, "particle_band_width", CONFIG["narrow_band_width"], L)
    _set(ds, "use_fractions", True, L)
    _set(ds, "fractions_distance", CONFIG["fractions_distance"], L)

    # THE key choice: open domain.
    if CONFIG["open_domain"]:
        for side in ("front", "back", "right", "left", "top", "bottom"):
            _set(ds, "use_collision_border_%s" % side, False, L)

    # Surface mesh — needed for a renderable splash, and speed vectors are
    # required for correct motion blur on a mesh whose vertex count changes
    # every frame.
    _set(ds, "use_mesh", True, L)
    _set(ds, "mesh_scale", 2, L)
    _set(ds, "use_speed_vectors", True, L)

    # Cache. Must live on disk, outside the .blend, and NOT in a cloud-synced
    # folder — the sync client will fight the solver for the files.
    _set(ds, "cache_type", "MODULAR", L)
    _set(ds, "cache_directory", CONFIG["cache_dir"], L)
    _set(ds, "cache_frame_start", CONFIG["frame_start"], L)
    _set(ds, "cache_frame_end", CONFIG["frame_end"], L)

    dom.data.materials.append(make_water_material())

    print("[fluid] domain built @ res %d, open=%s"
          % (CONFIG["resolution"], CONFIG["open_domain"]))
    return dom


def make_bottle_effector(bottle):
    """Make the product a fluid obstacle so the splash wraps it instead of
    passing through. Surface Distance gives the collider a small skin; too
    small and fast particles tunnel straight through the thin bottle wall."""
    bpy.context.view_layer.objects.active = bottle
    bpy.ops.object.modifier_add(type="FLUID")
    bottle.modifiers["Fluid"].fluid_type = "EFFECTOR"
    es = bottle.modifiers["Fluid"].effector_settings
    _set(es, "effector_type", "COLLISION", "effector")
    _set(es, "surface_distance", 0.5, "effector")
    _set(es, "use_effector", True, "effector")
    print("[fluid] bottle set as collision effector")
    return bottle


# ============================================================================
# Stage 7 — the curve-guided emitter (the headline technique)
# ============================================================================

def build_spiral_curve():
    """A Bezier spiral wrapping the bottle, built from explicit points.

    This is the path the emitter rides. The spiral is what turns a plain
    outward burst into a ribbon that wraps the product — the shape that makes
    the reference frame read as designed rather than random.
    """
    turns = CONFIG["curve_turns"]
    n = CONFIG["curve_points"]
    r = CONFIG["curve_radius"]
    z0, z1 = CONFIG["curve_z_start"], CONFIG["curve_z_end"]

    curve_data = bpy.data.curves.new("SPLASH_PATH", type="CURVE")
    curve_data.dimensions = "3D"
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(n - 1)

    for i in range(n):
        t = i / float(n - 1)
        angle = t * turns * 2.0 * math.pi
        pt = spline.bezier_points[i]
        pt.co = (r * math.cos(angle), r * math.sin(angle), z0 + (z1 - z0) * t)
        pt.handle_left_type = "AUTO"
        pt.handle_right_type = "AUTO"

    curve_obj = bpy.data.objects.new("SPLASH_PATH", curve_data)
    move_to_collection(curve_obj, "SIM")

    # Path animation drives Evaluation Time; we key it explicitly instead so we
    # control exactly when the emitter starts and stops travelling.
    curve_data.use_path = True
    curve_data.path_duration = CONFIG["splash_burst_frames"]

    print("[curve] spiral path built: %d points, %.2f turns" % (n, turns))
    return curve_obj


def build_emitter_on_curve(curve_obj=None):
    """The inflow, riding the spiral via a Follow Path constraint.

    Three things combine to make the ribbon:
      1. The emitter TRAVELS along the spiral (Follow Path, keyed offset_factor).
      2. The emitter THROWS liquid outward along its normal (velocity_normal).
      3. Use Flow is keyed on for a finite burst, then off — so you get a
         ribbon with a beginning and an end, not an endless hose.

    Miss any one of the three and it doesn't read.

    NOTE ON THE CURVE GUIDE FORCE FIELD: Blender ships a 'CURVE_GUIDE' field type
    that sounds like the right tool here. It does not work for Mantaflow liquid —
    documented defect T97172, particles spray in one direction instead of tracking
    the curve, and Mantaflow is effectively unmaintained upstream. The domain's
    Guides sub-panel has its own open regression (#97264). Follow Path is not a
    workaround for the proper tool; with stock Blender it IS the tool.
    """
    if curve_obj is None:
        curve_obj = bpy.data.objects.get("SPLASH_PATH") or build_spiral_curve()

    # A DISC, not a sphere. This matters more than it looks: `velocity_normal`
    # throws liquid along the emitter's face normals. A sphere's normals point in
    # every direction, so the throw cancels out radially and you get a soft blob
    # sitting on the curve. A disc's normals all point one way, so you get a
    # clean directed jet — which is what makes the ribbon read.
    bpy.ops.mesh.primitive_circle_add(
        vertices=24, radius=CONFIG["emitter_radius"],
        fill_type="NGON", location=(0, 0, 0),
    )
    emitter = bpy.context.object
    emitter.name = "SPLASH_EMITTER"
    # Face the disc outward (local +X) so that, once Follow Path aligns local +Y
    # to the curve tangent, the throw is radial rather than along the direction
    # of travel. If the jet fires inward on the first bake, negate
    # CONFIG["emitter_velocity_normal"] rather than re-rotating the mesh.
    emitter.rotation_euler = Euler((0.0, math.radians(90.0), 0.0))
    move_to_collection(emitter, "SIM")
    emitter.display_type = "WIRE"
    _set(emitter, "hide_render", True, "SPLASH_EMITTER")

    con = emitter.constraints.new("FOLLOW_PATH")
    con.target = curve_obj
    con.use_curve_follow = True
    con.use_fixed_location = True   # lets us drive offset_factor 0..1 directly
    con.forward_axis = "FORWARD_Y"
    con.up_axis = "UP_Z"

    # Fluid inflow.
    bpy.context.view_layer.objects.active = emitter
    bpy.ops.object.modifier_add(type="FLUID")
    emitter.modifiers["Fluid"].fluid_type = "FLOW"
    fs = emitter.modifiers["Fluid"].flow_settings
    _set(fs, "flow_type", "LIQUID", "flow")
    _set(fs, "flow_behavior", "INFLOW", "flow")
    _set(fs, "use_inflow", True, "flow")
    _set(fs, "use_initial_velocity", True, "flow")
    _set(fs, "velocity_normal", CONFIG["emitter_velocity_normal"], "flow")
    _set(fs, "velocity_factor", 1.0, "flow")
    _set(fs, "subframes", 2, "flow")   # kills stuttering on a fast-moving emitter

    f0 = CONFIG["splash_impact_frame"]
    f1 = f0 + CONFIG["splash_burst_frames"]

    # 1. Travel along the spiral.
    keyframe(emitter, "constraints[\"Follow Path\"].offset_factor",
             [(f0, 0.0), (f1, 1.0)], interp="LINEAR")

    # 2. Burst on, then off. CONSTANT interpolation — a fluid switch must snap,
    #    never ramp, or you get a frame of half-emission that reads as a glitch.
    mod = emitter.modifiers["Fluid"]
    for frame, value in ((f0 - 1, False), (f0, True), (f1, True), (f1 + 1, False)):
        fs.use_inflow = value
        fs.keyframe_insert(data_path="use_inflow", frame=frame)
    if emitter.animation_data and emitter.animation_data.action:
        for fcurve in emitter.animation_data.action.fcurves:
            if "use_inflow" in fcurve.data_path:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "CONSTANT"

    print("[emitter] inflow on curve, burst f%d-f%d" % (f0, f1))
    return emitter


# ============================================================================
# Stage 8 — the three-force rig
# ============================================================================

def build_force_rig():
    """Vortex + radial Force + Turbulence, keyed to bloom then decay.

    This reconstructs the three objects seen in the tutorial's `forces`
    collection. Each has a distinct job:

      VORTEX     — spins the sheet AROUND the bottle. This is what makes the
                   splash wrap the product instead of blowing past it.
      FORCE      — positive strength at the base, flaring the crown outward so
                   it breaks the left and right frame edges.
      TURBULENCE — low strength, breaks the sheet into irregular rims and
                   detached droplets so it doesn't read as a clean CG cone.

    All three ramp up at impact, peak at the hero frame, then decay. Keyframing
    force strength is how you make a physics sim hit a mark on a chosen frame —
    without it you are just rolling dice and re-baking.
    """
    f0 = CONFIG["splash_impact_frame"]
    hero = CONFIG["hero_frame"]
    f_end = CONFIG["frame_end"]
    made = {}

    def add_field(name, ftype, location, peak, extra=None):
        bpy.ops.object.effector_add(type=ftype, location=location)
        obj = bpy.context.object
        obj.name = name
        move_to_collection(obj, "FORCES")
        field = obj.field
        _set(field, "strength", peak, name)
        _set(field, "use_max_distance", True, name)
        _set(field, "distance_max", 0.45, name)
        _set(field, "falloff_power", 1.5, name)
        for key, value in (extra or {}).items():
            _set(field, key, value, name)

        # Bloom then decay.
        keyframe(obj, "field.strength", [
            (f0 - 5, 0.0),
            (f0 + 8, peak),
            (hero, peak * 0.85),
            (f_end, 0.0),
        ])
        made[name] = obj
        return obj

    add_field("FORCE_vortex", "VORTEX",
              (0.0, 0.0, 0.10), CONFIG["vortex_strength_peak"])

    add_field("FORCE_radial", "FORCE",
              (0.0, 0.0, 0.05), CONFIG["force_strength_peak"])

    add_field("FORCE_turbulence", "TURBULENCE",
              (0.0, 0.0, 0.16), CONFIG["turbulence_strength_peak"],
              extra={"size": CONFIG["turbulence_size"], "flow": 0.4})

    print("[forces] %d fields built, peak @ f%d" % (len(made), hero))
    return made


# ============================================================================
# Stage 9 — render settings
# ============================================================================

def configure_render(preset="lookdev"):
    """Two presets: fast iteration, and final beauty.

    The single most important non-obvious setting for this shot is
    TRANSMISSION BOUNCES. Light entering the splash has to survive: water
    surface -> water interior -> water surface -> bottle wall -> bottle
    interior -> amber liquid -> bottle wall -> out. That is easily 8-12
    transmission events before a ray reaches the camera. Cycles' default of 12
    is marginal; drop it and the splash renders BLACK. This is the number one
    reason beginners' splash renders look dead.
    """
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = CONFIG["res_x"]
    scene.render.resolution_y = CONFIG["res_y"]
    scene.render.fps = CONFIG["fps"]
    scene.frame_start = CONFIG["frame_start"]
    scene.frame_end = CONFIG["frame_end"]

    cy = scene.cycles
    _set(cy, "device", "GPU", "cycles")
    _set(cy, "feature_set", "SUPPORTED", "cycles")

    if preset == "lookdev":
        scene.render.resolution_percentage = 50
        _set(cy, "samples", 64, "cycles")
        _set(cy, "use_adaptive_sampling", True, "cycles")
        _set(cy, "adaptive_threshold", 0.05, "cycles")
        _set(cy, "use_denoising", True, "cycles")
        _set(cy, "transmission_bounces", 12, "cycles")
        _set(cy, "max_bounces", 12, "cycles")
        _set(scene.render, "use_motion_blur", False, "render")
    else:  # final
        scene.render.resolution_percentage = 100
        _set(cy, "samples", 1024, "cycles")
        _set(cy, "use_adaptive_sampling", True, "cycles")
        _set(cy, "adaptive_threshold", 0.01, "cycles")
        _set(cy, "use_denoising", True, "cycles")
        _set(cy, "denoiser", "OPENIMAGEDENOISE", "cycles")
        _set(cy, "max_bounces", 32, "cycles")
        _set(cy, "transmission_bounces", 24, "cycles")   # <- the critical one
        _set(cy, "glossy_bounces", 8, "cycles")
        _set(cy, "transparent_max_bounces", 16, "cycles")
        _set(cy, "blur_glossy", 1.0, "cycles")           # firefly control
        _set(cy, "sample_clamp_indirect", 10.0, "cycles")
        _set(scene.render, "use_motion_blur", True, "render")
        _set(scene.render, "motion_blur_shutter", 0.5, "render")  # 180 deg rule

    # Persistent Data is a large win on animation: it keeps the BVH between
    # frames instead of rebuilding it every frame. Costs RAM, saves hours.
    _set(scene.render, "use_persistent_data", True, "render")

    # Output: image sequence, never straight to video.
    scene.render.filepath = CONFIG["output_dir"]
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = "16"
    scene.render.image_settings.compression = 15
    # Placeholders + no-overwrite = a render you can resume after a crash and
    # can split across several machines.
    _set(scene.render, "use_overwrite", False, "render")
    _set(scene.render, "use_placeholder", True, "render")

    # Colour management. A 3.6-era look will NOT match on 4.x without this:
    # 4.0 changed the default view transform from Filmic to AgX, which
    # desaturates a saturated orange backdrop noticeably.
    try:
        scene.view_settings.view_transform = "AgX" if is_4x() else "Filmic"
        scene.view_settings.look = "None"
    except Exception as exc:  # noqa: BLE001
        _WARNINGS.append("view transform: %s" % exc)

    print("[render] preset '%s' applied (%s)"
          % (preset, "4.x" if is_4x() else "3.x"))
    return scene


# ============================================================================
# Orchestration
# ============================================================================

def build_all(preset="lookdev"):
    """Full build in the correct production order.

    The order matters and is not arbitrary:
      set/camera before sim, because the sim only has to look right FROM THE
      CAMERA — art-directing a splash you haven't framed yet is wasted work.
      Sim before materials, because a splash that's the wrong shape can't be
      rescued by a good shader.
      Materials before lights, because you light a surface, not a placeholder.
    """
    _WARNINGS.clear()

    reset_scene()
    product = build_product()
    build_set()
    build_lights()
    build_camera()

    domain = build_fluid_domain()
    make_bottle_effector(product["body"])
    curve = build_spiral_curve()
    build_emitter_on_curve(curve)
    build_force_rig()

    configure_render(preset=preset)

    print("\n" + "=" * 68)
    print("BUILD COMPLETE")
    print("=" * 68)
    print("Blender %s" % (".".join(str(v) for v in bpy.app.version)))
    print("Hero frame: %d   Range: %d-%d @ %d fps"
          % (CONFIG["hero_frame"], CONFIG["frame_start"],
             CONFIG["frame_end"], CONFIG["fps"]))
    print("Domain resolution: %d  (raise to 200-400 for final)"
          % CONFIG["resolution"])
    print("\nNEXT STEPS:")
    print("  1. Save the .blend FIRST (the cache path is relative to it).")
    print("  2. Physics > Fluid > Bake Data. Watch it at res 100.")
    print("  3. Art-direct the force strengths, re-bake, repeat.")
    print("  4. Only when the SHAPE is right: raise resolution, bake Mesh.")
    print("  5. configure_render(preset='final') and render the sequence.")

    if _WARNINGS:
        print("\n%d WARNING(S) — properties this Blender version didn't accept:"
              % len(_WARNINGS))
        for warning in _WARNINGS:
            print("  ! %s" % warning)
    else:
        print("\nNo property warnings. All settings applied cleanly.")

    return {"product": product, "domain": domain}


if __name__ == "__main__":
    build_all()
