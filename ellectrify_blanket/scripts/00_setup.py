"""Step 1 (section 11): check Blender + GPU, create folders and the project blend,
apply the section 5 render settings, list missing assets, time a test render."""
import glob
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from _common import (ROOT, BLEND, ASSETS, PREVIEWS, SHOTS, SHOT_FRAMES, log, gpu_setup,  # noqa: E402
                     apply_render_settings, get_collection, get_scene, world_fill, render_still,
                     look_at, save_blend)

report = []


def say(msg):
    log(msg)
    report.append(msg)


# ---- version ---------------------------------------------------------------
ver = bpy.app.version
say(f"Blender {bpy.app.version_string}")
if ver < (4, 2, 0):
    raise SystemExit("Blender is older than 4.2 - stop and tell Saurav before continuing (spec section 12).")

# ---- GPU -------------------------------------------------------------------
gpus = gpu_setup()
if gpus:
    say("Cycles devices: " + ", ".join(f"{k} {n}" for k, n in gpus))
else:
    say("Cycles devices: CPU only (no OptiX/CUDA GPU found). Settings fall back to CPU + OpenImageDenoise; "
        "on the RTX 4080 machine the same scripts switch to OptiX automatically.")

# ---- folders ---------------------------------------------------------------
for d in ["assets/logo", "assets/ref", "assets/fonts", "assets/audio", "scripts", "blend", "cache",
          *[f"renders/s{i}" for i in range(1, 7)], "previews", "out"]:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)

# ---- asset check (section 3) -----------------------------------------------
def files(sub, exts):
    out = []
    for e in exts:
        out += glob.glob(os.path.join(ASSETS, sub, f"*.{e}")) + glob.glob(os.path.join(ASSETS, sub, f"*.{e.upper()}"))
    return sorted(set(out))


img = ("png", "jpg", "jpeg", "webp")
checks = [
    ("Ellectrify logo, SVG or transparent PNG", files("logo", ("svg", "png")), 1),
    ("Three blanket product photos + Instagram cord image", files("ref", img), 4),
    ("Serif font files, regular and italic", files("fonts", ("ttf", "otf")), 2),
    ("Music bed and four sound effects", files("audio", ("wav", "mp3", "flac", "ogg", "aif", "aiff")), 5),
]
missing = []
for label, found, need in checks:
    state = "OK" if len(found) >= need else f"MISSING ({len(found)}/{need} files)"
    say(f"asset check - {label}: {state}")
    if len(found) < need:
        missing.append(label)

# ---- project blend ---------------------------------------------------------
if os.path.exists(BLEND):
    bpy.ops.wm.open_mainfile(filepath=BLEND)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)

lib_scene = bpy.data.scenes[0] if "LIB" not in bpy.data.scenes else bpy.data.scenes["LIB"]
lib_scene.name = "LIB"
lib = get_collection("LIB", lib_scene.collection)

for name in SHOTS + ["EDIT"]:
    sc = get_scene(name)
    sc.frame_start = 1
    sc.frame_end = SHOT_FRAMES.get(name, 600)
for sc in bpy.data.scenes:
    if sc.name == "EDIT":
        sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = 1080, 1920, 30
        continue
    apply_render_settings(sc, preview=True, standard_view=(sc.name == "S6_Logo"), gpu=bool(gpus))
    if sc.name != "S6_Logo":
        world_fill(sc)

# ---- test render -----------------------------------------------------------
test = bpy.data.scenes.get("TEST") or bpy.data.scenes.new("TEST")
for ob in list(test.collection.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
apply_render_settings(test, preview=True, gpu=bool(gpus))
world_fill(test)
bpy.ops.mesh.primitive_plane_add(size=4)
plane = bpy.context.active_object
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 0.3))
sphere = bpy.context.active_object
for ob in (plane, sphere):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    test.collection.objects.link(ob)
cam = bpy.data.objects.new("TEST_cam", bpy.data.cameras.new("TEST_cam"))
cam.location = (0, -2.5, 1.2)
look_at(cam, (0, 0, 0.3))
test.collection.objects.link(cam)
test.camera = cam
key = bpy.data.objects.new("TEST_key", bpy.data.lights.new("TEST_key", "AREA"))
key.data.energy = 400
key.location = (-2, -1, 2.5)
look_at(key, (0, 0, 0.3))
test.collection.objects.link(key)
dt = render_still(test, os.path.join(PREVIEWS, "step1_test_render.png"))
say(f"test render (1080x1920, 48 samples, simple scene) took {dt:.1f}s on "
    f"{'GPU' if gpus else 'CPU'}")
for ob in list(test.collection.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.scenes.remove(test)
bpy.data.orphans_purge(do_recursive=True)
if bpy.context.window:
    bpy.context.window.scene = lib_scene
save_blend()

with open(os.path.join(PREVIEWS, "step1_report.txt"), "w") as f:
    f.write("\n".join(report) + "\n")
    if missing:
        f.write("\nMissing before the build can be finished:\n" + "\n".join(f" - {m}" for m in missing) + "\n")
log("step 1 done")
