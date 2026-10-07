"""S6 Logo (60 frames): black #0A0A0A card. The brand's own logo file goes on an emission plane
at 42% of frame width, slightly above middle, fading in over frames 1-15. If assets/logo/ is empty
the scene renders the black card only and 90_edit.py adds a 'LOGO HERE' placeholder.
The logo is never redrawn or approximated."""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from _common import (open_blend, save_blend, reset_scene, camera, key_frames, smooth,  # noqa: E402
                     apply_render_settings, hex_rgba, remove_object, log, ASSETS)

open_blend()
sc, C = reset_scene("S6_Logo", 60)
apply_render_settings(sc, standard_view=True)
w = bpy.data.worlds.get("WORLD_S6_Logo") or bpy.data.worlds.new("WORLD_S6_Logo")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = hex_rgba("#0A0A0A")
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
sc.world = w

cam, aim = camera(sc, C + "cam", 50, 16, (0, 0, 0))
cam.location = (0, -2.0, 0)
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.0          # frame height 2.0 -> width 1.125 in 9:16
cam.data.dof.use_dof = False

logos = sorted(glob.glob(os.path.join(ASSETS, "logo", "*.png")))
if logos:
    img = bpy.data.images.load(logos[0], check_existing=True)
    aspect = img.size[1] / img.size[0]
    width = 1.125 * 0.42
    bpy.ops.mesh.primitive_plane_add(size=1)
    pl = bpy.context.active_object
    for c in list(pl.users_collection):
        c.objects.unlink(pl)
    sc.collection.objects.link(pl)
    pl.name = C + "logo"
    pl.rotation_euler = (1.5708, 0, 0)
    pl.scale = (width, width * aspect, 1)
    pl.location = (0, 0, 0.12)
    mat = bpy.data.materials.get("MAT_logo") or bpy.data.materials.new("MAT_logo")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.interpolation = "Closest"
    em = nt.nodes.new("ShaderNodeEmission")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    fade = nt.nodes.new("ShaderNodeMath"); fade.operation = "MULTIPLY"
    nt.links.new(tx.outputs["Color"], em.inputs["Color"])
    nt.links.new(tx.outputs["Alpha"], fade.inputs[0])
    nt.links.new(fade.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    pl.data.materials.append(mat)
    key_frames(fade.inputs[1], "default_value", range(1, 61), lambda f: smooth((f - 1) / 14))
    log(f"S6 logo plane from {os.path.basename(logos[0])}")
else:
    log("S6: no logo in assets/logo/ - black card only; the edit adds a LOGO HERE placeholder")

sc.cycles.samples = 16
sc.render.use_motion_blur = False
save_blend()
