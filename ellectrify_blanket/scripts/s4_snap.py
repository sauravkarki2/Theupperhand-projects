"""S4 Snap (90 frames): macro - the cord's snap cap lowers onto the stud (contact at f25 with a
1 mm overshoot, settled by f29) and one soft pale-yellow pulse spreads through the threads."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from _common import (open_blend, save_blend, reset_scene, place, camera, key_frames, empty, smooth,  # noqa: E402
                     ease_out, shot_light_rig, apply_render_settings, material, remove_object, log, PREVIEW)

open_blend()
sc, C = reset_scene("S4_Snap", 90)
apply_render_settings(sc)

# silver face lying flat with soft wrinkles, kept flat right around the stud
n = 120 if PREVIEW else 240
name = C + "silver"
remove_object(name)
if name in bpy.data.meshes:
    bpy.data.meshes.remove(bpy.data.meshes[name])
bm = bmesh.new()
size = 0.9
vs = [[bm.verts.new(((i / n - .5) * size, (j / n - .5) * size, 0)) for i in range(n + 1)] for j in range(n + 1)]
for j in range(n):
    for i in range(n):
        bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
me = bpy.data.meshes.new(name)
bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
me.materials.append(material("MAT_silver_layer"))
plane = bpy.data.objects.new(name, me)
sc.collection.objects.link(plane)
vg = plane.vertex_groups.new(name="wrinkle")
for v in me.vertices:
    d = math.hypot(v.co.x, v.co.y)
    vg.add([v.index], smooth((d - 0.03) / 0.12), "REPLACE")
tex = bpy.data.textures.get(C + "wrinkles") or bpy.data.textures.new(C + "wrinkles", "CLOUDS")
tex.noise_scale = 0.12
tex.noise_depth = 2
disp = plane.modifiers.new("Wrinkles", "DISPLACE")
disp.texture = tex
disp.texture_coords = "OBJECT"
disp.strength = 0.008
disp.mid_level = 0.5
disp.vertex_group = "wrinkle"
sol = plane.modifiers.new("Solidify", "SOLIDIFY")
sol.thickness, sol.offset = 0.004, -1.0
sub = plane.modifiers.new("Subdivision", "SUBSURF")
sub.levels = sub.render_levels = 1

stud = place(sc, "SNAP_stud", C + "stud", (0, 0, 0))

# pulse driven by object custom properties read in MAT_silver_layer
plane["snap_pos"] = (0.0, 0.0, 0.0)
plane["pulse_R"] = 0.0
plane["pulse_strength"] = 0.0
key_frames(plane, '["pulse_R"]', range(1, 91), lambda f: 0.6 * min(1.0, max(0.0, (f - 27) / 45)))


def strength(f):
    if f <= 27:
        return 0.0
    if f <= 36:
        return 3.0 * smooth((f - 27) / 9)
    return 3.0 * (1 - smooth((f - 36) / 44))


key_frames(plane, '["pulse_strength"]', range(1, 91), strength)

# cap + cord: lowered 40 mm from above, contact at f25 (1 mm overshoot, settles over 4 frames)
cap = place(sc, "CORD_cap", C + "cap")
ZC = 0.0034                                     # cap origin height when seated on the stud
SETTLE = {25: -0.001, 26: -0.0004, 27: 0.0002, 28: 0.0, 29: 0.0}


def cap_z(f):
    if f < 25:
        t = (f - 1) / 24
        return ZC + 0.040 * (1 - t ** 1.6)      # accelerating press toward contact
    return ZC + SETTLE.get(f, 0.0)


key_frames(cap, "location", range(1, 91), lambda f: (0, 0, cap_z(f)))
cu_name = C + "cord"
remove_object(cu_name)
if cu_name in bpy.data.curves:
    bpy.data.curves.remove(bpy.data.curves[cu_name])
cu = bpy.data.curves.new(cu_name, "CURVE")
cu.dimensions = "3D"
cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps, cu.resolution_u = 0.0015, 4, True, 24
sp = cu.splines.new("BEZIER")
pts = [(0.0, 0.0, 0.0098), (0.0, 0.012, 0.026), (0.01, 0.06, 0.11), (0.03, 0.14, 0.32)]
sp.bezier_points.add(len(pts) - 1)
for bp, co in zip(sp.bezier_points, pts):
    bp.co = co
    bp.handle_left_type = bp.handle_right_type = "AUTO"
cu.materials.append(material("MAT_cord_white"))
cord = bpy.data.objects.new(cu_name, cu)
sc.collection.objects.link(cord)
cord.parent = cap

shot_light_rig(sc, C, (0, 0, 0.0), key_energy=300, rim=True, rim_energy=260, window=True)
# macro: a dimmer fill so the metal reads grey and the soft pulse is visible against it
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3

focus = empty(sc, C + "focus", (0, 0, 0.004))
cam, aim = camera(sc, C + "cam", 100, 2.8, (0, 0, 0.004), focus=focus)
a, b = (0.10, -0.42, 0.22), (0.06, -0.38, 0.20)
key_frames(cam, "location", [1, 90], lambda f: [a[i] + (b[i] - a[i]) * (f - 1) / 89 for i in range(3)])

log("S4 built")
save_blend()
