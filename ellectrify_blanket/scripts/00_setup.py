"""00_setup.py - Step 1 of the Ellectrify Grounding Blanket build.

Creates (or rebuilds) blend/ellectrify_blanket.blend with:
  - one scene per shot (S1_Folded .. S6_Logo) plus EDIT, each with its local frame range
  - the LIB collection that holds shared objects and materials
  - the global render settings from section 5 of the spec

Run headless:   blender -b -P scripts/00_setup.py
or with the bpy module:   python scripts/00_setup.py

Safe to run twice: it starts from an empty file every time.
Prints a JSON report with the Blender version, the render device and a test render time.
"""
import json
import os
import time

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLEND = os.path.join(ROOT, "blend", "ellectrify_blanket.blend")

# Shot name, local length in frames, global start frame (section 9)
SHOTS = [
    ("S1_Folded", 90, 1),
    ("S2_Unfurl", 135, 91),
    ("S3_Exploded", 150, 226),
    ("S4_Snap", 90, 376),
    ("S5_Bed", 75, 466),
    ("S6_Logo", 60, 541),
]


def setup_device():
    """Use OptiX on an RTX card when one exists, otherwise fall back to the CPU."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for backend in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = backend
        except TypeError:
            continue
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == backend]
        if gpus:
            for d in prefs.devices:
                d.use = d.type == backend
            return "GPU", backend, [d.name for d in gpus]
    prefs.compute_device_type = "NONE"
    return "CPU", "NONE", []


def apply_render_settings(sc, device):
    r = sc.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
    r.fps, r.fps_base = 30, 1.0
    r.use_persistent_data = True
    r.use_motion_blur = sc.name != "S6_Logo"
    r.motion_blur_shutter = 0.5
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA" if sc.name == "S6_Logo" else "RGB"
    r.image_settings.color_depth = "16"

    c = sc.cycles
    c.device = device
    c.samples = 192
    c.preview_samples = 48
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.02
    c.use_denoising = True
    # OptiX denoiser needs an RTX card; OpenImageDenoise is the CPU fallback.
    c.denoiser = "OPTIX" if device == "GPU" else "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.max_bounces = 8
    c.glossy_bounces = 4
    c.transmission_bounces = 4
    c.sample_clamp_indirect = 10.0

    vs = sc.view_settings
    if sc.name == "S6_Logo":
        vs.view_transform = "Standard"
        vs.look = "None"
    else:
        vs.view_transform = "AgX"
        # The look name changed between versions ('Base Contrast' vs 'AgX - Base Contrast').
        for l in ("AgX - Base Contrast", "Base Contrast"):
            try:
                vs.look = l
                break
            except TypeError:
                continue


def main():
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    device, backend, gpus = setup_device()

    first = bpy.context.scene
    first.name = SHOTS[0][0]
    scenes = [first] + [bpy.data.scenes.new(n) for n, _, _ in SHOTS[1:]]
    for sc, (name, length, gstart) in zip(scenes, SHOTS):
        sc.frame_start, sc.frame_end = 1, length
        sc["global_start"] = gstart
        sc.unit_settings.system = "METRIC"
        sc.unit_settings.scale_length = 1.0
        apply_render_settings(sc, device)

    edit = bpy.data.scenes.new("EDIT")
    edit.frame_start, edit.frame_end = 1, 600
    apply_render_settings(edit, device)
    edit.render.use_motion_blur = False

    # Shared library collection. Kept off-scene here; later scripts link it into each shot.
    lib = bpy.data.collections.new("LIB")
    lib.use_fake_user = True

    # Test render: a simple lit cube at preview quality (48 samples), full 1080x1920.
    sc = scenes[0]
    sc.cycles.samples = 48
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0.25))
    test_objs = [bpy.context.active_object]
    test_objs[0].name = "TMP_test_cube"
    cam_data = bpy.data.cameras.new("TMP_test_cam")
    cam = bpy.data.objects.new("TMP_test_cam", cam_data)
    sc.collection.objects.link(cam)
    cam.location = (0, -2.0, 0.6)
    cam.rotation_euler = (1.45, 0, 0)
    sc.camera = cam
    light_data = bpy.data.lights.new("TMP_test_key", "AREA")
    light_data.energy = 300
    light = bpy.data.objects.new("TMP_test_key", light_data)
    sc.collection.objects.link(light)
    light.location = (-1.5, -1.0, 2.0)
    test_objs += [cam, light]

    tr = time.time()
    sc.render.filepath = os.path.join(ROOT, "previews", "step1_test_render.png")
    bpy.ops.render.render(write_still=True, scene=sc.name)
    render_seconds = round(time.time() - tr, 1)

    # Clean up the test objects so the file starts empty.
    for o in test_objs:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if data and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Camera):
                bpy.data.cameras.remove(data)
            elif isinstance(data, bpy.types.Light):
                bpy.data.lights.remove(data)
    sc.camera = None
    sc.cycles.samples = 192

    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)

    report = {
        "blender_version": bpy.app.version_string,
        "meets_4_2": bpy.app.version >= (4, 2, 0),
        "device": device,
        "backend": backend,
        "gpus": gpus,
        "scenes": [s.name for s in bpy.data.scenes],
        "test_render_seconds_48spp_1080x1920": render_seconds,
        "blend": BLEND,
        "total_seconds": round(time.time() - t0, 1),
    }
    print("SETUP_REPORT " + json.dumps(report))
    return report


if __name__ == "__main__":
    main()
