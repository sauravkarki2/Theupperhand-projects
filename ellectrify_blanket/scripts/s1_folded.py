"""S1 Folded (90 frames): folded white blanket on the cream plinth, slow linear push in. No text."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from _common import (open_blend, save_blend, reset_scene, place, camera, key_frames, room,  # noqa: E402
                     shot_light_rig, apply_render_settings, log)

open_blend()
sc, C = reset_scene("S1_Folded", 90)
apply_render_settings(sc)

place(sc, "PLINTH", C + "plinth")                          # top at z = 0.9
blanket = place(sc, "BLANKET_folded", C + "blanket", (0, 0, 0.9), (0, 0, 0.06))
room(sc, C, wall_y=1.6, floor_mat="MAT_stone")
shot_light_rig(sc, C, (0, 0, 1.0), key_energy=650)

cam, aim = camera(sc, C + "cam", 50, 4.0, (0, 0, 1.02))
focus = bpy.data.objects.new(C + "focus", None)            # front fold
focus.location = (0, -0.23, 1.0)
sc.collection.objects.link(focus)
cam.data.dof.focus_object = focus
a, b = (0, -2.3, 1.30), (0, -1.6, 1.18)
key_frames(cam, "location", [1, 90], lambda f: [a[i] + (b[i] - a[i]) * (f - 1) / 89 for i in range(3)])

log("S1 built")
save_blend()
