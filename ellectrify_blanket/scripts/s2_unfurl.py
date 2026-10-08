"""S2 Unfurl (135 frames): the blanket hangs by two pinned corners at z = 2.3, white side to
camera, swings forward and up, then the corners cross so the silver face turns to camera by ~f90."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from _common import (open_blend, save_blend, reset_scene, camera, key_frames, room, empty, smooth,  # noqa: E402
                     shot_light_rig, apply_render_settings, blanket_object, cloth_settings,
                     finish_blanket_stack, bake_cloth, log)

open_blend()
sc, C = reset_scene("S2_Unfurl", 135)
apply_render_settings(sc)
room(sc, C, wall_y=2.4)
shot_light_rig(sc, C, (0, 0, 1.4), key_energy=900)

# hang vertically in the XZ plane, cotton (+normal) facing the camera (-Y)
ob = blanket_object(sc, C + "blanket")
ob.rotation_euler = (math.radians(90), 0, 0)
ob.location = (0, 0, 2.3 - 2.03 / 2)
sc.view_layers[0].update()

# pin groups at the two top corners
me = ob.data
pins = ob.vertex_groups.new(name="pins")
groups = {"L": ob.vertex_groups.new(name="pin_L"), "R": ob.vertex_groups.new(name="pin_R")}
corners = {"L": Vector((-0.76, 1.015, 0)), "R": Vector((0.76, 1.015, 0))}
for v in me.vertices:
    for side, c in corners.items():
        if (v.co - c).length < 0.05:
            groups[side].add([v.index], 1.0, "REPLACE")
            pins.add([v.index], 1.0, "REPLACE")

mw = Matrix.LocRotScale(ob.location, ob.rotation_euler.to_quaternion(), Vector((1, 1, 1)))
hooks = {}
for side, c in corners.items():
    e = empty(sc, C + f"pin_{side}", mw @ c)
    m = ob.modifiers.new(f"Hook_{side}", "HOOK")
    m.object = e
    m.vertex_group = groups[side].name
    m.matrix_inverse = (mw.inverted() @ Matrix.Translation(e.location)).inverted()
    hooks[side] = e

cloth_settings(ob, speed=0.4, pin_group="pins")
finish_blanket_stack(ob)

# empties: frames 1-60 swing forward (-Y) and up; 45-95 the pair turns 180 deg about the
# vertical so L passes in front of R (one crosses over the other) and the silver face turns
# to camera; then they drift gently.
def corner_pos(side, f):
    fwd = smooth((f - 1) / 59)
    centre = Vector((0, -0.55 * fwd, 2.3 + 0.35 * fwd - 0.12 * smooth((f - 95) / 40)))
    turn = math.pi * smooth((f - 45) / 50)
    base = math.pi if side == "L" else 0.0
    ang = base + turn
    r = 0.76 - 0.1 * math.sin(turn)      # corners come slightly together while crossing
    return centre + Vector((r * math.cos(ang), r * math.sin(ang) * -1, 0)) * 1.0


for side, e in hooks.items():
    key_frames(e, "location", range(1, 136), lambda f, s=side: corner_pos(s, f))

cam, aim = camera(sc, C + "cam", 35, 5.6, (0, 0, 1.4))
a, b = (0, -3.6, 0.9), (0, -3.4, 1.2)
key_frames(cam, "location", [1, 135], lambda f: [a[i] + (b[i] - a[i]) * (f - 1) / 134 for i in range(3)])

save_blend()
bake_cloth(sc, ob)
save_blend()
log("S2 built and baked")
