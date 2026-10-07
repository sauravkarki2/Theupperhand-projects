"""Step 2 sign-off (section 11): material board - cotton, silver, fill, steel, cord side by side.
Renders one 48-sample tile per material into previews/step2_tiles/ and, when Pillow is
available, stitches them into previews/step2_material_board.png (labels are 2D, on the board
image only - never on a 3D object)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from _common import (open_blend, save_blend, get_scene, remove_objects, apply_render_settings,  # noqa: E402
                     world_fill, render_still, look_at, deg, log, PREVIEWS, material)

open_blend()
sc = get_scene("BOARD")
remove_objects(["BOARD_"])
apply_render_settings(sc, preview=True)
sc.render.resolution_x, sc.render.resolution_y = 720, 900
sc.render.use_motion_blur = False
world_fill(sc)
root = sc.collection


def dup(src, name, loc=(0, 0, 0), rot=(0, 0, 0)):
    ob = bpy.data.objects[src].copy()
    ob.name = name
    ob.location, ob.rotation_euler = loc, rot
    root.objects.link(ob)
    return ob


# ground
import bmesh  # noqa: E402
me = bpy.data.meshes.get("BOARD_ground") or bpy.data.meshes.new("BOARD_ground")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=10)
bm.to_mesh(me); bm.free()
me.materials.clear(); me.materials.append(material("MAT_cream"))
ground = bpy.data.objects.new("BOARD_ground", me)
root.objects.link(ground)

# items: each tile sits at its own x so it can be framed alone
SW_ROT = (0, 0, deg(200))      # curled corner turned toward camera-left
tiles = []
cot = dup("SW_cotton", "BOARD_cotton", (0, 0, 0.0), SW_ROT)
tiles.append(("cotton", "MAT_quilt_cotton", [cot], (0, 0, 0.02), (0, -0.98, 0.80), 50))
sil = dup("SW_silver", "BOARD_silver", (3, 0, 0.004), SW_ROT)
tiles.append(("silver", "MAT_silver_layer", [sil], (3, 0, 0.02), (3, -0.98, 0.80), 50))
fil = dup("SW_fill", "BOARD_fill", (6, 0, 0.0), SW_ROT)
tiles.append(("fill", "MAT_fill", [fil], (6, 0, 0.02), (6, -0.98, 0.80), 50))
# steel: the stud on a silver swatch, 40 mm in from a corner
base = dup("SW_silver", "BOARD_steel_base", (9, 0, 0.004), (0, 0, 0))
stud_xy = (9 - 0.25 + 0.04, -0.25 + 0.04)
stud = dup("SNAP_stud", "BOARD_stud", (stud_xy[0], stud_xy[1], 0.0045))
tiles.append(("steel", "MAT_steel", [base, stud], (stud_xy[0], stud_xy[1], 0.007),
              (stud_xy[0] + 0.03, stud_xy[1] - 0.09, 0.06), 100))
# cord: cap + cable lying on the cream ground, socket side down
cap = dup("CORD_cap", "BOARD_cap", (12, 0, 0.0))
cord = dup("CORD", "BOARD_cord")
cord.parent = cap
tiles.append(("cord", "MAT_cord_white", [cap, cord], (12.04, 0.005, 0.005), (11.95, -0.20, 0.12), 70))

# lights: key (4 x 2.5 m area, 5600 K, camera-left and above) + narrow rim strip behind
def area(name, size, size_y, energy, kelvin=5600):
    ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size, size_y
    ld.energy = energy
    ld.use_temperature = True
    ld.temperature = kelvin
    ob = bpy.data.objects.new(name, ld)
    root.objects.link(ob)
    return ob


key = area("BOARD_key", 4.0, 2.5, 260)
rim = area("BOARD_rim", 1.6, 0.12, 120)
cam = bpy.data.objects.new("BOARD_cam", bpy.data.cameras.get("BOARD_cam") or bpy.data.cameras.new("BOARD_cam"))
root.objects.link(cam)
sc.camera = cam

out_dir = os.path.join(PREVIEWS, "step2_tiles")
os.makedirs(out_dir, exist_ok=True)
all_items = [o for t in tiles for o in t[2]]
paths = []
for name, mat, items, target, cam_loc, lens in tiles:
    for o in all_items:
        o.hide_render = o not in items
    tgt = Vector(target)
    cam.location = cam_loc
    cam.data.lens = lens
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = (Vector(cam_loc) - tgt).length
    cam.data.dof.aperture_fstop = 5.6 if lens < 100 else 8
    look_at(cam, tgt)
    key.location = tgt + Vector((-3.2, -1.6, 2.4))
    look_at(key, tgt)
    rim.location = tgt + Vector((0.6, 2.2, 1.6))
    look_at(rim, tgt)
    rim.hide_render = name not in ("silver", "steel")
    p = os.path.join(out_dir, f"{name}.png")
    render_still(sc, p)
    paths.append((name, mat, p))

save_blend()

# stitch the board
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    log("Pillow not available - tiles are in previews/step2_tiles/")
    raise SystemExit(0)
pad, label_h = 24, 70
tw, th = 720, 900
board = Image.new("RGB", (pad + len(paths) * (tw + pad), pad + th + label_h), (24, 24, 24))
draw = ImageDraw.Draw(board)
font = None
for f in ("/usr/share/fonts/opentype/inter/Inter-Medium.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
    if os.path.exists(f):
        font = ImageFont.truetype(f, 30)
        break
for i, (name, mat, p) in enumerate(paths):
    im = Image.open(p).convert("RGB")
    x = pad + i * (tw + pad)
    board.paste(im, (x, pad))
    draw.text((x + 4, pad + th + 18), mat, fill=(235, 232, 225), font=font)
board.save(os.path.join(PREVIEWS, "step2_material_board.png"))
log("board: previews/step2_material_board.png")
