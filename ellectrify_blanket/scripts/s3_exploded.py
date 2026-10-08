"""S3 Exploded (150 frames): a corner swatch separates into cotton / fill / silver layers while
the camera orbits 80 deg at constant speed. Label anchors are exported for the Sequencer edit
(labels are clean type added in 90_edit.py - never text on a 3D object)."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402
from _common import (open_blend, save_blend, reset_scene, place, camera, key_frames, room, empty,  # noqa: E402
                     ease_out, shot_light_rig, apply_render_settings, deg, log, CACHE)

open_blend()
sc, C = reset_scene("S3_Exploded", 150)
apply_render_settings(sc)
room(sc, C, wall_y=2.6)
shot_light_rig(sc, C, (0, 0, 1.0), key_energy=700, rim=True, rim_energy=220)

stack = empty(sc, C + "stack", (0, 0, 1.0), (deg(15), 0, 0))      # tilted 15 deg toward camera
cotton = place(sc, "SW_cotton", C + "cotton", parent=stack)
fill = place(sc, "SW_fill", C + "fill", parent=stack)
silver = place(sc, "SW_silver", C + "silver", parent=stack)
stud = place(sc, "SNAP_stud", C + "stud", (-0.21, -0.21, 0.0), parent=silver)   # 40 mm in, near corner

# frames 20-80: 130 mm gaps; cotton starts at 20, fill 28, silver 36, each over 45 frames, strong ease-out,
# with a 3 deg counter-rotation between neighbouring layers.
LAYERS = [(cotton, 20, 0.17, 3.0), (fill, 28, 0.04, 0.0), (silver, 36, -0.09, -3.0)]
for ob, start, dz, rot in LAYERS:
    key_frames(ob, "location", range(1, 151), lambda f, s=start, d=dz: (0, 0, d * ease_out((f - s) / 45)))
    key_frames(ob, "rotation_euler", range(1, 151),
               lambda f, s=start, r=rot: (0, 0, deg(r) * ease_out((f - s) / 45)))

# camera: 70 mm, orbit 80 deg around (0, 0, 1.0), radius 1.5 m, height 1.25 m, constant speed
# Spec asks for 70 mm; at 1.5 m in a 9:16 frame that is only 0.43 m wide, narrower than the 0.5 m
# swatch, so the layers and label anchors fall outside frame. 45 mm keeps the whole swatch in view.
cam, aim = camera(sc, C + "cam", 45, 5.6, (0, 0, 1.0))


def orbit(f):
    a = deg(-40 + 80 * (f - 1) / 149)
    return (1.5 * math.sin(a), -1.5 * math.cos(a), 1.25)


key_frames(cam, "location", range(1, 151), orbit)
save_blend()

# label anchors (normalised frame coords, origin bottom-left) for the edit
ANCHORS = {
    "cotton": (cotton, Vector((0.20, -0.20, 0.008))),
    "silver": (silver, Vector((0.20, -0.20, 0.0))),
    "snap": (stud, Vector((0.0, 0.0, 0.005))),
}
data = {}
if bpy.context.window:
    bpy.context.window.scene = sc
dg = sc.view_layers[0].depsgraph
for f in range(1, 151):
    sc.frame_set(f)
    dg.update()
    cam_e = cam.evaluated_get(dg)
    data[f] = {k: tuple(world_to_camera_view(sc, cam_e, ob.evaluated_get(dg).matrix_world @ p)[:2])
               for k, (ob, p) in ANCHORS.items()}
os.makedirs(CACHE, exist_ok=True)
with open(os.path.join(CACHE, "s3_label_anchors.json"), "w") as fh:
    json.dump(data, fh)
log("S3 built; label anchors -> cache/s3_label_anchors.json")
