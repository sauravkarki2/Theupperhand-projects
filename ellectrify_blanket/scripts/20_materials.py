"""Section 7: build every material (Principled BSDF) and assign them to the LIB assets.
Rebuilds node trees from scratch each run."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from _common import open_blend, save_blend, hex_rgba, log  # noqa: E402

open_blend()

# Pulse colour: sampled from the logo file when it exists (section 7), else the expected value.
PULSE_HEX = "#F2EE8A"
LOGO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo")


def sample_logo_yellow():
    pngs = [f for f in os.listdir(LOGO_DIR) if f.lower().endswith(".png")] if os.path.isdir(LOGO_DIR) else []
    if not pngs:
        return None
    img = bpy.data.images.load(os.path.join(LOGO_DIR, pngs[0]), check_existing=True)
    px = list(img.pixels)
    acc, n = [0.0, 0.0, 0.0], 0
    for i in range(0, len(px), 4 * 7):          # every 7th pixel is plenty
        if px[i + 3] > 0.9:
            acc[0] += px[i]; acc[1] += px[i + 1]; acc[2] += px[i + 2]; n += 1
    return (acc[0] / n, acc[1] / n, acc[2] / n, 1.0) if n else None


class Graph:
    def __init__(self, name):
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        self.mat, self.nt = mat, nt
        self.out = self.node("ShaderNodeOutputMaterial", (900, 0))
        self.bsdf = self.node("ShaderNodeBsdfPrincipled", (500, 0))
        self.link(self.bsdf, "BSDF", self.out, "Surface")

    def node(self, kind, loc=None, **props):
        n = self.nt.nodes.new(kind)
        if loc:
            n.location = loc
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(self, a, out, b, inp):
        self.nt.links.new(a.outputs[out], b.inputs[inp])

    def set(self, **inputs):
        for k, v in inputs.items():
            self.bsdf.inputs[k.replace("_", " ")].default_value = v

    def math(self, op, a=None, b=None, va=None, vb=None):
        n = self.node("ShaderNodeMath", operation=op)
        if a is not None:
            self.link(a[0], a[1], n, 0)
        elif va is not None:
            n.inputs[0].default_value = va
        if b is not None:
            self.link(b[0], b[1], n, 1)
        elif vb is not None:
            n.inputs[1].default_value = vb
        return n

    def obj_coords(self):
        return self.node("ShaderNodeTexCoord")

    def weave(self, repeats_per_m):
        """Two crossed Wave textures -> 0..1 weave height."""
        tc = self.obj_coords()
        # Blender wave bands: sin(20 * scale * x) -> one period = 2*pi / (20 * scale)
        scale = repeats_per_m * 2 * math.pi / 20
        waves = []
        for axis in ("X", "Y"):
            w = self.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction=axis, wave_profile="SIN")
            w.inputs["Scale"].default_value = scale
            w.inputs["Distortion"].default_value = 0.6
            w.inputs["Detail"].default_value = 0.0
            self.link(tc, "Object", w, "Vector")
            waves.append(w)
        return self.math("MULTIPLY", (waves[0], "Fac"), (waves[1], "Fac"))

    def bump(self, height_node, strength, distance=0.0004):
        b = self.node("ShaderNodeBump")
        b.inputs["Strength"].default_value = strength
        b.inputs["Distance"].default_value = distance
        self.link(height_node, 0, b, "Height")
        self.link(b, "Normal", self.bsdf, "Normal")
        return b

    def displace(self, height_node, scale, socket=0):
        d = self.node("ShaderNodeDisplacement", (700, -300))
        d.inputs["Midlevel"].default_value = 0.0
        d.inputs["Scale"].default_value = scale
        self.link(height_node, socket, d, "Height")
        self.link(d, "Displacement", self.out, "Displacement")
        self.mat.displacement_method = "BOTH"
        return d


# ---------------------------------------------------------------- MAT_quilt_cotton
g = Graph("MAT_quilt_cotton")
g.set(Base_Color=hex_rgba("#F2F0EA"), Roughness=0.9, Sheen_Weight=0.6, Sheen_Roughness=0.5,
      Subsurface_Weight=0.05)
g.bsdf.inputs["Subsurface Scale"].default_value = 0.004
# diamonds: object coords rotated 45 deg, scaled so one diamond is 100 mm
tc = g.obj_coords()
mp = g.node("ShaderNodeMapping", vector_type="POINT")
mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
mp.inputs["Scale"].default_value = (10, 10, 10)          # 1 unit = 100 mm
g.link(tc, "Object", mp, "Vector")
sep = g.node("ShaderNodeSeparateXYZ")
g.link(mp, "Vector", sep, "Vector")
su = g.math("ABSOLUTE", (g.math("SINE", (g.math("MULTIPLY", (sep, "X"), vb=math.pi), 0)), 0))
sv = g.math("ABSOLUTE", (g.math("SINE", (g.math("MULTIPLY", (sep, "Y"), vb=math.pi), 0)), 0))
quilt = g.math("MULTIPLY", (su, 0), (sv, 0))
# meshes may carry a "quilt_flat" point attribute (1 = no puff, e.g. the folded stack's sides)
flat = g.node("ShaderNodeAttribute", attribute_type="GEOMETRY", attribute_name="quilt_flat")
quilt = g.math("MULTIPLY", (quilt, 0), (g.math("SUBTRACT", None, (flat, "Fac"), va=1.0), 0))
g.displace(quilt, 0.009)                                  # 9 mm puff, stitch lines sit low
g.bump(g.weave(900), 0.15)

# ---------------------------------------------------------------- MAT_silver_layer (+ pulse)
g = Graph("MAT_silver_layer")
g.set(Base_Color=hex_rgba("#8E9094"), Metallic=0.7, Anisotropic=0.4)
weave = g.weave(1200)
g.bump(weave, 0.25)
noise = g.node("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 900.0
noise.inputs["Detail"].default_value = 2.0
g.link(g.obj_coords(), "Object", noise, "Vector")
rng = g.node("ShaderNodeMapRange")
rng.inputs["To Min"].default_value = 0.3
rng.inputs["To Max"].default_value = 0.5
g.link(noise, "Fac", rng, "Value")
g.link(rng, "Result", g.bsdf, "Roughness")
# Pulse: emission in a 60 mm band at distance R from the snap, multiplied by the weave.
# Driven by object custom properties on whichever object wears this material:
#   pulse_R (m), pulse_strength (0..3), snap_pos (object-space xyz).
attrR = g.node("ShaderNodeAttribute", attribute_type="OBJECT", attribute_name="pulse_R")
attrS = g.node("ShaderNodeAttribute", attribute_type="OBJECT", attribute_name="pulse_strength")
attrP = g.node("ShaderNodeAttribute", attribute_type="OBJECT", attribute_name="snap_pos")
dist = g.node("ShaderNodeVectorMath", operation="DISTANCE")
g.link(g.obj_coords(), "Object", dist, 0)
g.link(attrP, "Vector", dist, 1)
diff = g.math("ABSOLUTE", (g.math("SUBTRACT", (dist, "Value"), (attrR, "Fac")), 0))
band = g.node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")   # 1 at centre, 0 at +-30 mm
band.inputs["From Min"].default_value = 0.03
band.inputs["From Max"].default_value = 0.0
g.link(diff, 0, band, "Value")
threads = g.math("POWER", (weave, 0), vb=0.5)
strength = g.math("MULTIPLY", (g.math("MULTIPLY", (band, "Result"), (threads, 0)), 0), (attrS, "Fac"))
g.link(strength, 0, g.bsdf, "Emission Strength")
pulse_col = sample_logo_yellow()
g.bsdf.inputs["Emission Color"].default_value = pulse_col or hex_rgba(PULSE_HEX)
log("pulse colour: " + ("sampled from logo" if pulse_col else f"logo missing, using expected {PULSE_HEX}"))

# ---------------------------------------------------------------- MAT_fill
g = Graph("MAT_fill")
g.set(Base_Color=hex_rgba("#FAFAF7"), Roughness=1.0, Sheen_Weight=1.0, Subsurface_Weight=0.2)
g.bsdf.inputs["Subsurface Scale"].default_value = 0.004
n = g.node("ShaderNodeTexNoise")
n.inputs["Scale"].default_value = 60.0
n.inputs["Detail"].default_value = 8.0
n.inputs["Roughness"].default_value = 0.7
g.link(g.obj_coords(), "Object", n, "Vector")
g.displace(n, 0.002)

# ---------------------------------------------------------------- simple ones
g = Graph("MAT_steel");      g.set(Base_Color=hex_rgba("#C9CBCD"), Metallic=1.0, Roughness=0.22)
g = Graph("MAT_cord_white"); g.set(Base_Color=hex_rgba("#F4F4F2"), Roughness=0.4, Subsurface_Weight=0.1)
g.bsdf.inputs["Subsurface Scale"].default_value = 0.002
g = Graph("MAT_cream");      g.set(Base_Color=hex_rgba("#EFEAE0"), Roughness=0.7)

# Backdrop: changed from the spec's cream walls to slate blue for contrast with the white quilt
# and the silver face (client request). Swap these three values to re-colour every set.
BACKDROP_WALL, BACKDROP_FLOOR, PLINTH = "#4E5D6C", "#3E4A56", "#6A7A8A"
g = Graph("MAT_backdrop");   g.set(Base_Color=hex_rgba(BACKDROP_WALL), Roughness=0.8)
g = Graph("MAT_plinth");     g.set(Base_Color=hex_rgba(PLINTH), Roughness=0.7)

# MAT_oak_dark: stretched noise for grain
g = Graph("MAT_oak_dark")
g.set(Roughness=0.5)
mp = g.node("ShaderNodeMapping", vector_type="POINT")
mp.inputs["Scale"].default_value = (3.0, 3.0, 80.0)        # long grain along local Y after the swap below
mp.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
g.link(g.obj_coords(), "Object", mp, "Vector")
n = g.node("ShaderNodeTexNoise")
n.inputs["Scale"].default_value = 4.0
n.inputs["Detail"].default_value = 6.0
g.link(mp, "Vector", n, "Vector")
ramp = g.node("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = hex_rgba("#4A3B2F")
ramp.color_ramp.elements[1].color = hex_rgba("#6A5848")
g.link(n, "Fac", ramp, "Fac")
g.link(ramp, "Color", g.bsdf, "Base Color")

# MAT_backdrop_floor: matte floor a step darker than the wall, with a quiet noise break-up
g = Graph("MAT_backdrop_floor")
g.set(Roughness=0.6)
n = g.node("ShaderNodeTexNoise")
n.inputs["Scale"].default_value = 3.0
n.inputs["Detail"].default_value = 10.0
g.link(g.obj_coords(), "Object", n, "Vector")
ramp = g.node("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = hex_rgba(BACKDROP_FLOOR)
ramp.color_ramp.elements[1].color = hex_rgba("#465360")
g.link(n, "Fac", ramp, "Fac")
g.link(ramp, "Color", g.bsdf, "Base Color")

# ---------------------------------------------------------------- assignment
ASSIGN = {
    "BLANKET_full": ["MAT_quilt_cotton", "MAT_silver_layer"],
    "BLANKET_folded": ["MAT_quilt_cotton"],
    "SW_cotton": ["MAT_quilt_cotton"],
    "SW_fill": ["MAT_fill"],
    "SW_silver": ["MAT_silver_layer"],
    "SNAP_stud": ["MAT_steel"],
    "CORD_cap": ["MAT_cord_white", "MAT_steel"],
    "CORD": ["MAT_cord_white"],
    "PLINTH": ["MAT_plinth"],
    "BED_frame": ["MAT_oak_dark"],
    "BED_headboard": ["MAT_oak_dark"],
    "BED_mattress": ["MAT_quilt_cotton"],
    "BED_wall": ["MAT_backdrop"],
    "BED_floor": ["MAT_backdrop_floor"],
}
# a plain white fitted sheet for the mattress (no quilting, so the blanket reads on top)
g = Graph("MAT_sheet_white")
g.set(Base_Color=hex_rgba("#F6F5F1"), Roughness=0.85, Sheen_Weight=0.4)
ASSIGN["BED_mattress"] = ["MAT_sheet_white"]

for obname, mats in ASSIGN.items():
    ob = bpy.data.objects.get(obname)
    if ob is None:
        log(f"warning: {obname} missing - run 10_assets.py")
        continue
    ob.data.materials.clear()
    for m in mats:
        ob.data.materials.append(bpy.data.materials[m])

log("materials built and assigned")
save_blend()
