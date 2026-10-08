"""S1 Form (90 frames): the blanket forms from nothing. Thin threads of light streak in diagonally
and the quilt weaves itself into existence behind a soft glowing front (a see-through thread mesh
that fills in solid), while it swirls in mid-air and the camera circles the other way.
White side to camera; the cut into S2 is on motion. No text."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from _common import (open_blend, save_blend, reset_scene, camera, key_frames, room, empty, smooth,  # noqa: E402
                     shot_light_rig, apply_render_settings, blanket_object, cloth_settings, material,
                     finish_blanket_stack, bake_cloth, remove_object, deg, log, remove_objects)

open_blend()
# the folded-on-plinth opener was replaced by this shot (client request)
old = bpy.data.scenes.get("S1_Folded")
if old is not None:
    for ob in list(old.collection.all_objects):
        if ob.name.startswith("S1_"):
            remove_object(ob.name)
    bpy.data.scenes.remove(old)

N = 90
sc, C = reset_scene("S1_Form", N)
apply_render_settings(sc)
room(sc, C, wall_y=2.6)
shot_light_rig(sc, C, (0, 0, 1.3), key_energy=900, rim=True, rim_energy=200)

CENTRE = Vector((0, 0, 2.45))          # pin line centre at rest

# ---- cloth, hanging by its two top corners, cotton facing camera
ob = blanket_object(sc, C + "blanket")
ob.rotation_euler = (math.radians(90), 0, 0)
ob.location = (0, 0, CENTRE.z - 2.03 / 2)
me = ob.data
pins = ob.vertex_groups.new(name="pins")
groups = {"L": ob.vertex_groups.new(name="pin_L"), "R": ob.vertex_groups.new(name="pin_R")}
corners = {"L": Vector((-0.76, 1.015, 0)), "R": Vector((0.76, 1.015, 0))}
# the whole top edge is pinned, blended linearly between the two corner hooks, so the cloth
# swirls as one sheet instead of sagging into a V between two points
for v in me.vertices:
    if v.co.y > 1.015 - 0.02:
        u = (v.co.x + 0.76) / 1.52
        groups["L"].add([v.index], 1.0 - u, "REPLACE")
        groups["R"].add([v.index], u, "REPLACE")
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
cloth_settings(ob, speed=0.5, pin_group="pins")
finish_blanket_stack(ob)


# circular motion: the pin line turns about the vertical while each corner traces its own loop
# (opposite phases), so the cloth rolls and swirls instead of just swinging
def corner_pos(side, f):
    t = (f - 1) / (N - 1)
    turn = deg(35) - deg(55) * smooth(t)
    loop = 2 * math.pi * t * 1.25 + (0 if side == "L" else math.pi)
    base = math.pi if side == "L" else 0.0
    r = 0.76 - 0.10 * (0.5 + 0.5 * math.sin(loop))
    ang = base + turn
    p = CENTRE + Vector((r * math.cos(ang), -r * math.sin(ang), 0))
    p += Vector((0.10 * math.cos(loop), 0.18 * math.sin(loop), 0.10 * math.sin(loop)))
    return p


for side, e in hooks.items():
    key_frames(e, "location", range(1, N + 1), lambda f, s=side: corner_pos(s, f))

# forming: only this shot's blanket carries build_on, so other shots are unaffected
ob["build_on"] = 1.0
ob["build"] = -0.45
key_frames(ob, '["build"]', range(1, N + 1), lambda f: -0.45 + 1.95 * smooth((f - 6) / 60))

# ---- thread streaks: ribbons that fly in from camera-upper-left toward the cloth
rnd = random.Random(11)
name = C + "streaks"
remove_object(name)
if name in bpy.data.meshes:
    bpy.data.meshes.remove(bpy.data.meshes[name])
bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap")
phase_layer = bm.faces.layers.float.new("phase")
D = Vector((0.55, 0.45, -0.70)).normalized()
for i in range(160):
    target = Vector((rnd.uniform(-0.75, 0.75), rnd.uniform(-0.15, 0.15), rnd.uniform(0.6, 2.45)))
    length = rnd.uniform(1.6, 2.8)
    start = target - D * length
    width = rnd.uniform(0.002, 0.005)
    side = D.cross(Vector((0, 1, 0))).normalized() * width / 2
    vs = [bm.verts.new(start - side), bm.verts.new(target - side), bm.verts.new(target + side), bm.verts.new(start + side)]
    f = bm.faces.new(vs)
    for loop, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uvl].uv = uv
    f[phase_layer] = rnd.random()
smesh = bpy.data.meshes.new(name)
bm.to_mesh(smesh); bm.free()
# face float layers become a FACE attribute named "phase" (read by MAT_thread_streak)
smesh.materials.append(material("MAT_thread_streak"))
streaks = bpy.data.objects.new(name, smesh)
sc.collection.objects.link(streaks)
for vis in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission"):
    setattr(streaks, vis, False)
streaks["streak_t"] = 0.0
key_frames(streaks, '["streak_t"]', range(1, N + 1), lambda f: (f - 1) / 62)

# ---- camera circles the other way around the swirling cloth
cam, aim = camera(sc, C + "cam", 35, 5.6, (0, 0, 1.5))


def orbit(f):
    t = (f - 1) / (N - 1)
    a = deg(-32 + 50 * t)
    return (3.6 * math.sin(a), -3.6 * math.cos(a), 1.3 + 0.3 * t)


key_frames(cam, "location", range(1, N + 1), orbit)

save_blend()
bake_cloth(sc, ob)
save_blend()
log("S1 Form built and baked")
