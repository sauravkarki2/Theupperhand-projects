"""S5 Bed (75 frames): the blanket settles over the made bed, white side up, as dawn light rises."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from _common import (open_blend, save_blend, reset_scene, place, camera, key_frames,  # noqa: E402
                     shot_light_rig, apply_render_settings, blanket_object, cloth_settings,
                     finish_blanket_stack, bake_cloth, log)

open_blend()
sc, C = reset_scene("S5_Bed", 75)
apply_render_settings(sc)

parts = {}
for src in ("BED_frame", "BED_headboard", "BED_mattress", "BED_wall", "BED_floor"):
    parts[src] = place(sc, src, C + src[4:])
parts["BED_wall"].scale = (1.6, 2.0, 1.0)                 # taller/wider so the frame never sees past it
for nm in ("BED_frame", "BED_mattress", "BED_headboard", "BED_floor"):
    col = parts[nm].modifiers.new("Collision", "COLLISION")
    parts[nm].collision.thickness_outer = 0.010

MATTRESS_TOP = 0.52
ob = blanket_object(sc, C + "blanket")
ob.location = (0, -0.18, MATTRESS_TOP + 0.35)              # flat, 0.35 m above the bed, white up
cloth_settings(ob, speed=0.6)
finish_blanket_stack(ob)

key, window = shot_light_rig(sc, C, (0, 0, 0.6), key_offset=(-3.4, -0.6, 1.9), key_energy=900)[:2]
# dawn: key from 40% / 4200 K to 100% / 5600 K across the shot
key_frames(key.data, "energy", range(1, 76), lambda f: 900 * (0.4 + 0.6 * (f - 1) / 74))
key_frames(key.data, "temperature", range(1, 76), lambda f: 4200 + 1400 * (f - 1) / 74)

cam, aim = camera(sc, C + "cam", 28, 5.6, (0, 0, 0.5))
a, b = (0.9, -3.0, 1.5), (1.1, -3.5, 1.7)
key_frames(cam, "location", [1, 75], lambda f: [a[i] + (b[i] - a[i]) * (f - 1) / 74 for i in range(3)])

save_blend()
bake_cloth(sc, ob)
save_blend()
log("S5 built and baked")
