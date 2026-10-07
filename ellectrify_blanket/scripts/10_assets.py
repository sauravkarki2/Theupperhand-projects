"""Section 6: build every shared asset into the LIB collection (one sub-collection per
asset so scenes can instance them). Safe to run twice: rebuilds objects by name."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402  (import before bmesh/mathutils when run as a module)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from _common import open_blend, save_blend, get_collection, remove_object, log  # noqa: E402

open_blend()
LIB = get_collection("LIB", bpy.data.scenes["LIB"].collection)

ASSETS = ["BLANKET_full", "BLANKET_folded", "SWATCH", "SNAP_stud", "CORD", "PLINTH", "BEDROOM"]


def sub(name):
    return get_collection(f"LIB_{name}", LIB)


def mesh_object(name, bm, coll, smooth=False):
    remove_object(name)
    me = bpy.data.meshes.get(name)
    if me is not None:
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def grid(width, height, nx, ny):
    """Quad grid centred on the origin in XY, nx x ny faces."""
    bm = bmesh.new()
    verts = [[bm.verts.new(((i / nx - .5) * width, (j / ny - .5) * height, 0)) for i in range(nx + 1)]
             for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
    return bm


def box(bm, size, center, cuts=0):
    """Add an axis-aligned box (optionally subdivided) to bm."""
    geom = bmesh.ops.create_cube(bm, size=1.0)["verts"]
    for v in geom:
        v.co = Vector((v.co.x * size[0] + center[0], v.co.y * size[1] + center[1], v.co.z * size[2] + center[2]))
    if cuts:
        edges = list({e for v in geom for e in v.link_edges})
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True)
    return geom


def cylinder(bm, r, depth, z0, segments=64):
    m = Matrix.Translation((0, 0, z0 + depth / 2))
    return bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                                 radius1=r, radius2=r, depth=depth, matrix=m)["verts"]


def add_mod(ob, kind, name, **kw):
    m = ob.modifiers.new(name, kind)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


# ---------------------------------------------------------------- BLANKET_full
# 1.52 x 2.03 m, ~12 mm quad spacing. Cloth -> Solidify (15 mm, material offset 1) -> Subdivision 1.
ob = mesh_object("BLANKET_full", grid(1.52, 2.03, 127, 169), sub("BLANKET_full"), smooth=True)
add_mod(ob, "CLOTH", "Cloth")
add_mod(ob, "SOLIDIFY", "Solidify", thickness=0.015, offset=-1.0, material_offset=1, material_offset_rim=0,
        use_rim=True, use_even_offset=True)
add_mod(ob, "SUBSURF", "Subdivision", levels=1, render_levels=1)

# ---------------------------------------------------------------- BLANKET_folded
# Modelled, not simulated: folded in thirds then in half = 6 layers, ~0.55 x 0.45 x 0.22 m.
bm = bmesh.new()
layers = 6
th = 0.22 / layers
jitter = [(0.000, 0.000, 0.000), (0.004, -0.003, 0.006), (-0.003, 0.002, -0.004),
          (0.002, 0.004, 0.005), (-0.004, -0.002, -0.003), (0.001, 0.003, 0.004)]
for i in range(layers):
    dx, dy, dw = jitter[i]
    box(bm, (0.55 + dw, 0.45 + dw * .6, th * 0.98), (dx, dy, th * (i + .5)), cuts=22)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
ob = mesh_object("BLANKET_folded", bm, sub("BLANKET_folded"), smooth=True)
add_mod(ob, "BEVEL", "Bevel", width=th * 0.47, segments=8, limit_method="ANGLE")
add_mod(ob, "SUBSURF", "Subdivision", levels=1, render_levels=1)

# ---------------------------------------------------------------- SWATCH layers
# 0.50 x 0.50 m, 2 mm solidify, one gently curled corner (the +X +Y corner).
def swatch(name, z):
    bm = grid(0.5, 0.5, 100, 100)
    for v in bm.verts:
        t = max(0.0, (v.co.x + v.co.y) / 0.5 - 0.5) / 0.5      # 0 .. 1 toward the corner
        v.co.z = z + 0.06 * t ** 2.2
    ob = mesh_object(name, bm, sub("SWATCH"), smooth=True)
    add_mod(ob, "SOLIDIFY", "Solidify", thickness=0.002, offset=-1.0, use_even_offset=True)
    add_mod(ob, "SUBSURF", "Subdivision", levels=1, render_levels=1)
    return ob


swatch("SW_cotton", 0.004)
swatch("SW_fill", 0.002)
swatch("SW_silver", 0.0)

# ---------------------------------------------------------------- SNAP_stud
# 12 mm stud, 5 mm tall, on a 16 mm base ring. Origin = centre of the base.
# Lathe profile (radius, height): 16 mm base ring -> 12 mm post -> rounded crown.
PROFILE = [(0.0, 0.0), (0.0078, 0.0), (0.0080, 0.0004), (0.0078, 0.0009), (0.0070, 0.0011),
           (0.0062, 0.0012), (0.0060, 0.0016), (0.0060, 0.0036), (0.0058, 0.0042), (0.0053, 0.0047),
           (0.0042, 0.00495), (0.0020, 0.0050), (0.0, 0.0050)]
bm = bmesh.new()
edges = []
vs = [bm.verts.new((r, 0, z)) for r, z in PROFILE]
for a, b in zip(vs, vs[1:]):
    edges.append(bm.edges.new((a, b)))
bmesh.ops.spin(bm, geom=vs + edges, cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=96,
               use_merge=True)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
ob = mesh_object("SNAP_stud", bm, sub("SNAP_stud"), smooth=True)

# ---------------------------------------------------------------- CORD
# White moulded snap cap ~22 mm across with a metal socket underneath (material index 1),
# plus a 3 mm round white cable leaving the side of the cap.
bm = bmesh.new()
cap = cylinder(bm, 0.011, 0.009, 0.0015)
sock = cylinder(bm, 0.0045, 0.0016, 0.0)
sock_set = set(sock)
cap_ob = mesh_object("CORD_cap", bm, sub("CORD"), smooth=False)
for p in cap_ob.data.polygons:
    zs = [cap_ob.data.vertices[i].co.z for i in p.vertices]
    p.material_index = 1 if max(zs) <= 0.0016 + 1e-6 else 0
    p.use_smooth = True
add_mod(cap_ob, "BEVEL", "Bevel", width=0.0028, segments=6, limit_method="ANGLE")

remove_object("CORD")
cu = bpy.data.curves.get("CORD")
if cu is not None:
    bpy.data.curves.remove(cu)
cu = bpy.data.curves.new("CORD", "CURVE")
cu.dimensions = "3D"
cu.bevel_depth = 0.0015
cu.bevel_resolution = 4
cu.use_fill_caps = True
cu.resolution_u = 24
sp = cu.splines.new("BEZIER")
pts = [(0.009, 0, 0.006), (0.05, 0.004, 0.0035), (0.14, 0.035, 0.0018), (0.28, 0.01, 0.0018), (0.48, -0.06, 0.0018)]
sp.bezier_points.add(len(pts) - 1)
for bp, co in zip(sp.bezier_points, pts):
    bp.co = co
    bp.handle_left_type = bp.handle_right_type = "AUTO"
cord = bpy.data.objects.new("CORD", cu)
sub("CORD").objects.link(cord)
cord.parent = cap_ob

# ---------------------------------------------------------------- PLINTH
bm = bmesh.new()
box(bm, (1.2, 0.8, 0.9), (0, 0, 0.45))
ob = mesh_object("PLINTH", bm, sub("PLINTH"))
add_mod(ob, "BEVEL", "Bevel", width=0.006, segments=3, limit_method="ANGLE")

# ---------------------------------------------------------------- BEDROOM set
# Queen bed (head toward +Y, against the wall), low dark-oak frame, white fitted mattress,
# cream wall behind, pale stone floor. No lamps, pictures or props that could carry text.
bed = sub("BEDROOM")
bm = bmesh.new()
box(bm, (1.66, 2.17, 0.20), (0, 0, 0.18))                          # rail box
for sx in (-1, 1):
    for sy in (-1, 1):
        box(bm, (0.07, 0.07, 0.08), (sx * 0.76, sy * 1.0, 0.04))   # short legs
ob = mesh_object("BED_frame", bm, bed)
add_mod(ob, "BEVEL", "Bevel", width=0.008, segments=3, limit_method="ANGLE")

bm = bmesh.new()
box(bm, (1.66, 0.06, 0.62), (0, 1.115, 0.39))
ob = mesh_object("BED_headboard", bm, bed)
add_mod(ob, "BEVEL", "Bevel", width=0.008, segments=3, limit_method="ANGLE")

bm = bmesh.new()
box(bm, (1.52, 2.03, 0.24), (0, 0, 0.40), cuts=8)
ob = mesh_object("BED_mattress", bm, bed, smooth=True)
add_mod(ob, "BEVEL", "Bevel", width=0.035, segments=5, limit_method="ANGLE")

bm = grid(7.0, 3.2, 1, 1)
ob = mesh_object("BED_wall", bm, bed)
ob.rotation_euler = (math.radians(90), 0, 0)
ob.location = (0, 1.16, 1.6)

bm = grid(10.0, 10.0, 1, 1)
ob = mesh_object("BED_floor", bm, bed)

log("assets built: " + ", ".join(ASSETS))
save_blend()
