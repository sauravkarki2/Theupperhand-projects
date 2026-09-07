# Module 03 — Lighting, Camera & Render
### Beverage Commercial in Blender · field manual

**Target build:** Blender **3.6 LTS** (the version the source tutorial used), with every
**4.0 / 4.2 / 4.5 API and UI difference flagged inline.**
**Scope:** lights, world/HDRI, camera, motion blur, render engine, colour management, output.
**Out of scope (other modules):** materials/shaders, fluid sim setup, geometry nodes, compositing
node trees. Two comp topics appear here only because they are render-settings decisions:
the **Vector pass** (motion blur alternative) and **denoise-in-comp**.

---

## 0. Scene assumptions used by every number in this document

Every position, size and wattage below is written for this canonical setup. If your scene
differs, rescale with the laws in §0.2 — do not copy numbers blind.

| Quantity | Value | Note |
|---|---|---|
| Unit system | Metric, **Unit Scale 1.0**, metres | Cycles is physically based; wrong scale wrecks light falloff and DOF |
| Bottle height | **0.25 m** | base sits on `z = 0`, so the bottle spans `z = 0.00 → 0.25` |
| Bottle diameter | ~0.07 m | body; shoulder tapers above `z ≈ 0.17` |
| Label centre | **`z ≈ 0.13`** | this is the "hero point" — camera and focus target aim here |
| Splash ribbon | ~0.8 m wide × 0.5 m tall, wrapped around the bottle | breaks frame left and right |
| Backdrop | seamless curved plane behind and under the product, emissive orange→amber | see §4 |
| Camera axis | camera sits at **−Y**, looks toward **+Y** | so screen-left = **−X**, screen-right = **+X**, "behind the product" = **+Y** |
| Frame rate / range | **25 fps, frames 1–250** (10.0 s) — or 24 fps, 1–240 | evidence frame 163 lands at 6.52 s |
| Aspect / resolution | 16:9, **1920×1080** final (3840×2160 if you have the VRAM) | |

### 0.1 Cheat sheet of the whole shot

```
                    TOP LIGHT (0.45 m sq, 120 W)
                              |
        KEY (1.2×1.8 m,   .   |    .   STRIP-R  (0.12×1.10 m, 180 W, 6500 K)
        600 W, 5600 K)     \  |  /
             \              \ | /
              \   [ BOTTLE ]  |          <- KICKER behind, through the liquid
               \      ||      |             (0.30 m disk, 250 W, 4000 K,
        STRIP-L  ....  ||  ....              camera-invisible)
        (mirror of R)  ||
                       ||
   WATER CARD (L) ============ WATER CARD (R)     <- huge emission planes, light-linked
   2.2×2.6 m, E=4.0                                  to the splash ONLY (§1.6)
                       ||
                    CAMERA @ (0, -2.0, 0.11), 100 mm, f/4
```

### 0.2 The two scaling laws you will use constantly

1. **Light power vs distance (inverse square).** Blender Area/Point/Spot `energy` is in **Watts**
   of total radiant power. Irradiance at the subject `E ∝ P / d²`. If you move a light from
   `d_old` to `d_new` and want identical exposure:
   `P_new = P_old × (d_new / d_old)²`
   Moving a 600 W key from 1.77 m to 2.50 m → `600 × (2.50/1.77)² = 1197 W`.
2. **Softness vs apparent size.** Shadow/terminator softness is governed by the light's
   **angular size** as seen from the subject, `θ ≈ 2·atan(L / 2d)` for a light of width `L`
   at distance `d`. A 1.2 m light at 1.2 m (θ ≈ 53°) is soft. The *same* light at 4 m
   (θ ≈ 17°) is comparatively hard. **Big + close = soft. Small + far = hard.**
   Doubling `L` and `d` together keeps softness identical but drops exposure 4×.

> **Rule of thumb for product:** the key light's shortest dimension should be **≥ 3× the
> subject's silhouette width** and sit **1–2× the subject height away**. For a 0.25 m bottle
> that's a light ≥ 0.75 m short-side (we use 1.2 m) at ~1.2–1.8 m.

---

## 1. Studio product lighting, applied to a beverage bottle

A beverage hero shot is not "lit" in the diffuse sense. Glass, liquid and water are almost
entirely **specular and transmissive**. You are not painting light onto the subject — you are
**arranging bright and dark shapes for it to reflect and refract.** Every light below exists
to put a specific *shape* into the bottle's surface.

### 1.1 The big soft key — the one light that says "photographed, not rendered"

| Property | Value | Why |
|---|---|---|
| Type | **Area**, shape **Rectangle** | rectangles read as a real softbox in the bottle's reflection |
| Size | **1.2 m × 1.8 m** (portrait, long axis vertical) | a *tall* key gives a tall vertical reflection that flatters a tall bottle |
| Position | `(-1.10, -0.95, 1.15)` | upper-front-**left**, matching the reference frame |
| Aim | `(0, 0, 0.14)` → rotation `(55.2°, 0°, -49.2°)` | |
| Distance | 1.77 m | θ ≈ 39° apparent — soft but still directional |
| Power | **600 W** | with View Transform = Filmic and Exposure 0 |
| Colour | **5600 K** ≈ `(1.000, 0.930, 0.880)` | daylight-neutral; the warmth comes from the backdrop, not the key |
| Spread | 120–180° | wide; see §2.2 |

**Why upper-front-left and not straight on?** A frontal key puts its reflection in the *centre*
of the bottle, killing the sense of roundness and blowing out the label. Raked 45° left and
~35° up, the key's reflection lands on the **left third** of the body, leaving the right side
to be defined by the right strip light. That left-bright / right-bright / dark-centre pattern
is exactly what reads as "glass" to the eye.

**Height matters more than people think.** With the key at `z = 1.15` and the bottle 0.25 m
tall, the light is ~35–40° above horizontal. Higher → shadow drops under the bottle and the
shoulder/cap catch more; lower → longer horizontal reflection band and a shadow that runs back
into the frame. For a low hero angle you want the shadow going **away** from camera, so keep
the key above 30°.

### 1.2 Twin strip / edge lights — the signature bottle look

This is the single most recognisable trick in beverage advertising: **two tall, narrow, bright
sources raked from behind-left and behind-right**, drawing two bright vertical lines down the
bottle's silhouette. They define the *edges*, separating the product from the backdrop without
a rim of white outline, and they make the glass look thick.

| | Strip-L | Strip-R |
|---|---|---|
| Type / shape | Area / **Rectangle** | Area / **Rectangle** |
| Size (W × H) | **0.12 m × 1.10 m** | **0.12 m × 1.10 m** |
| Location | `(-0.62, 0.55, 0.45)` | `(0.62, 0.55, 0.45)` |
| Aim | `(0, 0, 0.16)` | `(0, 0, 0.16)` |
| Rotation | `(70.7°, 0°, -131.6°)` | `(70.7°, 0°, 131.6°)` |
| Distance | 0.88 m | 0.88 m |
| Power | **180 W** | **180 W** (or 140 W to break symmetry) |
| Colour | **6500 K** = `(1.00, 1.00, 1.00)` | 6500 K, or 7000 K on one side |
| **Spread** | **45°** | **45°** |
| Cycles → Max Bounces | **0** | **0** |

**Why they're so much "brighter" than the key at a third of the wattage.** Specular
reflection is driven by **radiance** (W per m² per steradian), not total power.
The key: 600 W / (1.2 × 1.8 m) = **278 W/m²**. A strip: 180 W / (0.12 × 1.10 m) = **1364 W/m²**
— about **5× the surface brightness**. It therefore burns a bright, hard-edged line into the
glass while contributing almost nothing to overall exposure. That is the whole point.

**Why they go BEHIND the product (`+Y`).** From behind, their reflection wraps the *outer
silhouette*. From the front they'd land in the middle of the body and look like two more
softboxes. Rule: **edge lights live between 100° and 145° off the camera axis.**

**Practical adjustments**
- Slide a strip **left/right in X** to move the bright line toward or away from the silhouette
  edge. Move it **up/down in Z** to change where the line brightens along the height.
- Set **Max Bounces = 0** so the strips only ever contribute direct specular — no orange GI
  contamination and much less noise.
- Deliberately break the symmetry (180 W vs 140 W, 6500 K vs 7200 K). Perfectly mirrored
  edge lights look CG.
- If a strip's own rectangle is visible in the render (a bright bar floating in the backdrop),
  turn off its object-level camera visibility — see §2.4.

### 1.3 The kicker through the liquid — the most important light in the shot

The reference frame's amber liquid **glows**. That is not diffuse shading, it is
**transmission**: light entering the far side of the liquid, being absorbed selectively
(Beer–Lambert), and exiting toward camera as saturated amber. **A translucent product lit only
from the front is dead.** No amount of key light produces that glow, because front light
reflects off the glass instead of passing through the liquid.

| Property | Value |
|---|---|
| Type / shape | **Area**, **Disk** |
| Size | **0.30 m** diameter |
| Location | `(0.10, 0.62, 0.16)` — behind the bottle, roughly at liquid height |
| Aim | `(0, 0, 0.13)` → rotation `(87.3°, 0°, 170.8°)` |
| Power | **250 W** (this is your main "glow" dial) |
| Colour | **4000 K** `(1.00, 0.80, 0.63)` — warm, pushes the amber |
| Object → Visibility → **Camera: OFF** | mandatory — it is aimed straight down the lens |
| Cycles → Max Bounces | 4 (it *should* contribute GI, unlike the strips) |

**Tuning it:**
- Slightly **off-centre in X** (`0.10`) so the glow isn't a symmetric blob.
- Height at `z ≈ 0.16` puts it just above liquid mid-line: the liquid glows brightest near the
  top where the light path through the liquid is shortest, which reads as "fresh, not murky".
- If the glow is blotchy/noisy: it is transmission bounces, not sampling — see §8.4.
- If the disk itself shows as a hotspot **through** the bottle (a visible light-shape burned
  into the liquid), enlarge it (0.45 m) and drop power proportionally, or move it further back.
- **`Cast Shadow = OFF`** on this light is a legitimate cheat if the backdrop geometry is
  blocking it: the light then passes through the backdrop plane as if it weren't there.

### 1.4 Top light — cap, shoulder and condensation

| Property | Value |
|---|---|
| Type / shape | Area, **Square** |
| Size | **0.45 m** |
| Location | `(0.00, -0.10, 0.95)` |
| Aim | `(0, 0, 0.25)` → rotation `(8.1°, 0°, 0°)` |
| Power | **120 W** |
| Colour | 6500 K |

The cap/crown of a bottle is a horizontal-ish surface: nothing else in the rig reaches it.
Without this light the top of the bottle goes dark and the product looks decapitated. Pulled
slightly toward camera (`y = -0.10`) so its reflection lands on the front of the shoulder
rather than the exact top. Keep it modest — a strong top light flattens the vertical strips.

### 1.5 Bounce and negative fill — shaping with geometry, not lights

These are **planes**, not lights. They work because Cycles is a GI renderer: a white plane
returns light, a black plane removes it by occupying reflection angles that would otherwise
show something bright.

| Card | Size | Location | Material | Purpose |
|---|---|---|---|---|
| **White bounce** | 1.2 × 1.6 m | `(1.25, -0.70, 0.50)`, faced at `(0,0,0.13)` | Emission, strength **1.5**, white; **camera visibility OFF** | lifts the camera-right shadow side; gives a soft wide reflection opposite the key |
| **Negative fill / flag** | 1.0 × 1.6 m | `(0.95, -1.20, 0.20)` | Diffuse, base colour `0.02` black | kills milky wash on the lower-right of the glass, restores a dark edge to contrast the right strip |
| **Overhead sky card** | 3.0 × 3.0 m | `(0, 0.2, 2.2)`, facing down | Emission, strength **2.0**, slightly cool; camera OFF | the "ambient" the water reflects from above — see §1.6 |

**Emission plane vs Area light — when to use which**

| | Area light | Emission plane |
|---|---|---|
| Sampled directly (MIS) | Yes — low noise | Only via light tree / indirect; noisier |
| Can be bent / curved / shaped | No (4 shapes only) | **Yes** — curve it around the bottle for a wrapping highlight |
| Can carry a texture/gradient | No | **Yes** (falloff gradient in the emission = graduated softbox) |
| Cheap | **Very** | More expensive |
| Shows a rectangle in reflections | Yes | Yes, and you control its exact shape |

**Use Area lights for the key/strips/kicker; use emission planes for anything curved,
gradated, or huge.**

### 1.6 Why the splash gets its OWN lights

Water is ~**95 % specular**. It has essentially no diffuse albedo. You cannot "light" a splash —
**you can only give it something bright to reflect and refract.** In the reference frame the
splash reads bright silver-white against the orange backdrop; that white is not the key light
hitting the water, it is **large white sources being mirrored** by the water's surface.

**The recipe:**
1. Build **two very large white emission planes** flanking the shot, well outside frame:
   `2.2 m × 2.6 m` at `(-1.90, -0.20, 1.00)` and `(1.90, -0.20, 1.00)`, both faced at
   `(0, 0, 0.30)`, **Emission strength 4.0**, pure white.
2. Turn **Ray Visibility → Camera OFF** on both so they never appear in the plate.
3. Consider **Diffuse visibility OFF** too — otherwise they wash the backdrop pale and destroy
   your saturated orange. Leave **Glossy and Transmission ON**: that is all the water needs.
4. Add the overhead sky card from §1.5. Splash crowns curl upward; their top rims sample the
   *upper* hemisphere, so an overhead source is what makes the rim ridges pop.

**Restricting a light to only the water.** Two mechanisms, and they are *not* the same:

| Mechanism | Blender version | What it actually does |
|---|---|---|
| **Light Groups** | 3.2+ | Renders each light's contribution into its **own render pass**. Nothing is restricted at render time — you re-mix afterwards. Full sampling cost of every light on every object. |
| **Light Linking** | **4.0+ only** | True per-object restriction: a light illuminates only objects in its **Receiver Collection**; blockers listed in **Blocker Collection** stop casting its shadows. This is the real tool. |

- **On 4.0+:** select each water card → *Object Properties → Shading → Light Linking →*
  new **Receiver Collection** containing only `SPLASH_MESH` and `LIQUID`. The cards now
  physically cannot brighten the bottle, label or backdrop. This is how you make the splash
  blazing white while the bottle stays moody.
- **On 3.6:** you have no light linking. Two workarounds:
  1. **Light Groups + compositing:** put the water cards in lightgroup `WATER`, render the
     `Combined` + `WATER` passes, and dial `WATER` down/up in comp. (Comp is another module —
     but the *render setting* is: create the lightgroup and add the pass.)
  2. **Ray-visibility surgery:** turn the cards' **Diffuse** visibility off so they only affect
     glossy/transmission. Since the backdrop and label are mostly diffuse and the water is
     entirely specular, this is ~80 % of light linking for free.

```python
# 3.6+: create a lightgroup and assign objects/lights to it
vl = bpy.context.view_layer
if "WATER" not in vl.lightgroups:
    vl.lightgroups.new(name="WATER")           # 3.2+
for name in ("CARD_Water_L", "CARD_Water_R", "CARD_Sky"):
    bpy.data.objects[name].lightgroup = "WATER"
# The pass appears in the Compositor as a "WATER" output on the Render Layers node.
```

### 1.7 The order you should actually build the rig in

Turn everything off, then bring lights up **one at a time**, judging each in isolation:

1. **Backdrop emission only.** Set its strength so the frame's background sits where you want
   it (§4). Everything else is balanced against this.
2. **Kicker.** Get the liquid glowing. This decides the shot.
3. **Key.** Bring in form and the label.
4. **Strip-L, then Strip-R.** Place by eye; move in X until the bright line sits ~10–15 % in
   from the silhouette edge.
5. **Top light.** Just enough to define the cap.
6. **Water cards.** Push until the splash reads silver-white.
7. **Bounce / negative fill.** Last, small corrections only.

---

## 2. Light object specifics

### 2.1 Shapes

| Shape | RNA `light.shape` | Reflection it leaves | Use for |
|---|---|---|---|
| Square | `'SQUARE'` | square softbox | top light, general fill |
| Rectangle | `'RECTANGLE'` | tall/wide softbox — the classic photographic look | **key**, **strip lights** |
| Disk | `'DISK'` | round highlight, like a beauty dish / ring | **kicker**, anything you want to read as a lens/bulb |
| Ellipse | `'ELLIPSE'` | oval | soft edge highlights without rectangle corners |

Rectangle uses `size` (X) and `size_y` (Y); Square/Disk use `size` only.

### 2.2 Spread — the most under-used control in Blender lighting

`light.spread` (Area lights only, **radians** in Python, degrees in the UI). Default **180°**
(`math.pi`): the light emits over the full hemisphere, like a bare softbox.

- **Lower spread = the light behaves like a softbox with a grid/eggcrate.** Rays leave in a
  narrower cone, so the *specular highlight it leaves on curved glass gets narrower and
  brighter*, and spill onto the backdrop collapses.
- **This is the single best control for specular width.** Widening or narrowing the light
  changes its softness *and* its coverage; changing spread changes **coverage and contrast
  without changing softness**.

| Spread | Character | Where |
|---|---|---|
| 180° (default) | full wrap, lots of spill | key, bounce cards |
| 90–120° | controlled, less floor spill | top light |
| **30–60°** | crisp, punchy specular line; almost no spill | **strip / edge lights** — use 45° |
| < 20° | nearly collimated, very hard, aliasing-prone; noisy | special-effect shafts only |

> Gotcha: very low spread on a large light gets **noisy**, because MIS has a much smaller
> valid solid angle to sample. If a 20° spread light is grainy, raise it to 40° or increase
> samples.

### 2.3 Portals

`light.cycles.is_portal = True` on an Area light. A portal is not a light: it tells Cycles
"HDRI/world light enters the scene through this rectangle, sample it here." It only helps
**interiors** lit by a world through small openings.

**In an open studio product shot, portals do nothing but slow you down. Leave them off.**
The one exception: if you build an enclosed light-tent / cyc box around the product and light
it with an HDRI outside, place a portal over the opening.

### 2.4 Ray visibility and per-light Cycles settings

| Control | Where (3.6) | RNA | Use |
|---|---|---|---|
| **Multiple Importance Sampling** | Light Data → Light → Cycles | `light.cycles.use_multiple_importance_sampling` | Leave **ON**. Off = the light is only found by chance ray hits; huge noise. Only turn off for a large, dim, purely-ambient card where MIS is wasted. |
| **Max Bounces** | Light Data → Light → Cycles | `light.cycles.max_bounces` | How many bounces this light contributes to. **0 = direct light only.** Set 0 on strips (no GI pollution, less noise). Default 1024. |
| **Cast Shadow** | Light Data → Light → Cycles | `light.cycles.cast_shadow` | Off = light passes through all geometry. Cheat for a kicker blocked by the backdrop. |
| **Shadow Caustics** | Light Data → Light → Caustics (3.4+) | `light.cycles.is_caustics_light` | See §2.5 |
| **Camera / Diffuse / Glossy / Transmission / Shadow visibility** | **Object** Properties → Visibility → Ray Visibility | `ob.visible_camera`, `ob.visible_diffuse`, `ob.visible_glossy`, `ob.visible_transmission`, `ob.visible_volume_scatter`, `ob.visible_shadow` | On the *object*, not the light data. This is how you hide the kicker from camera and stop the water cards washing the backdrop. |
| **Light contribution to Diffuse/Glossy/Transmission/Volume** | Light Data → Light → Cycles | — (in 4.x lights also expose `use_shadow`) | 3.6 exposes these on the *object* ray visibility for lights too |

### 2.5 Shadow Caustics (MNEE) — for the water, with caveats

Cycles' path tracer cannot find caustics well: light that refracts through water onto a
surface is a near-impossible path to sample backwards. **Shadow Caustics (Manifold Next Event
Estimation, 3.4+)** solves the specific case of light → *one or two specular refractions* →
diffuse receiver.

**To enable, all three must be set:**
1. On the **light**: *Light Data → Caustics → Shadow Caustics* (`light.cycles.is_caustics_light = True`).
2. On the **water / bottle / liquid object**: *Object → Shading → Caustics → **Cast Shadow Caustics***.
3. On the **surface receiving them** (backdrop, table): *Object → Shading → Caustics → **Receive Shadow Caustics***.

**Caveats — read before you rely on it:**
- Works best with **small, sharp lights**. A 1.2 × 1.8 m key produces mush. Add a dedicated
  small (0.05–0.15 m) high-power caustic light.
- Only handles a limited number of specular interfaces. A splash sheet *plus* bottle glass
  *plus* liquid usually exceeds what MNEE can solve, and the effect silently disappears.
- Not supported on every GPU backend historically (CPU + CUDA/OptiX safest; verify on HIP/Metal).
- Refractive object needs a **smooth, non-noisy** normal; a jagged fluid mesh defeats it.

**Realistic verdict for this shot:** enable it on one small light aimed through the *bottle*
onto the backdrop for a beautiful amber caustic pool. Do **not** expect it to work through the
flying splash — for the splash, fake it (a projected texture from a spot) or let brute-force
caustics + denoise handle it.

### 2.6 Complete starting rig — table

Bottle 0.25 m at origin; camera at `(0, -2.0, 0.11)`. Rotations in degrees XYZ.

| # | Name | Type | Shape | Size (m) | Location | Rotation | Power / Strength | Colour (K) | Spread | Cam vis | Max bounce |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `KEY_Soft` | Area | Rectangle | 1.20 × 1.80 | `(-1.10, -0.95, 1.15)` | `(55.2, 0, -49.2)` | **600 W** | 5600 | 150° | on | 8 |
| 2 | `STRIP_L` | Area | Rectangle | 0.12 × 1.10 | `(-0.62, 0.55, 0.45)` | `(70.7, 0, -131.6)` | **180 W** | 6500 | **45°** | off | **0** |
| 3 | `STRIP_R` | Area | Rectangle | 0.12 × 1.10 | `(0.62, 0.55, 0.45)` | `(70.7, 0, 131.6)` | **140 W** | 7000 | **45°** | off | **0** |
| 4 | `KICK_Liquid` | Area | Disk | 0.30 | `(0.10, 0.62, 0.16)` | `(87.3, 0, 170.8)` | **250 W** | 4000 | 180° | **off** | 4 |
| 5 | `TOP_Cap` | Area | Square | 0.45 | `(0.00, -0.10, 0.95)` | `(8.1, 0, 0)` | **120 W** | 6500 | 110° | off | 4 |
| 6 | `CARD_Bounce_R` | Mesh plane | — | 1.20 × 1.60 | `(1.25, -0.70, 0.50)` | faces `(0,0,0.13)` | Emission **1.5** | white | — | **off** | — |
| 7 | `FLAG_Neg_R` | Mesh plane | — | 1.00 × 1.60 | `(0.95, -1.20, 0.20)` | faces `(0,0,0.13)` | Diffuse **0.02** | black | — | off | — |
| 8 | `CARD_Water_L` | Mesh plane | — | 2.20 × 2.60 | `(-1.90, -0.20, 1.00)` | faces `(0,0,0.30)` | Emission **4.0** | white | — | **off**, diffuse **off** | — |
| 9 | `CARD_Water_R` | Mesh plane | — | 2.20 × 2.60 | `(1.90, -0.20, 1.00)` | faces `(0,0,0.30)` | Emission **4.0** | white | — | **off**, diffuse **off** | — |
| 10 | `CARD_Sky` | Mesh plane | — | 3.00 × 3.00 | `(0.00, 0.20, 2.20)` | faces `(0,0,0.25)` | Emission **2.0** | 7000 K | — | **off**, diffuse **off** | — |

**Colour-temperature → linear RGB quick table** (set `light.color` to these; Blender light
colour is linear, not sRGB-encoded):

| K | RGB | Feel |
|---|---|---|
| 2700 | `(1.000, 0.630, 0.340)` | tungsten, very warm |
| 3200 | `(1.000, 0.710, 0.460)` | warm practical |
| 4000 | `(1.000, 0.800, 0.630)` | **kicker** — pushes amber |
| 4500 | `(1.000, 0.840, 0.710)` | warm neutral |
| 5600 | `(1.000, 0.930, 0.880)` | **key** — daylight |
| 6500 | `(1.000, 1.000, 1.000)` | **strips** — neutral D65 |
| 7000 | `(0.930, 0.960, 1.000)` | slightly cool |
| 7500 | `(0.900, 0.940, 1.000)` | cool edge |
| 9000 | `(0.820, 0.890, 1.000)` | icy rim, good on water |

> Complementary-colour trick: the backdrop is orange, so cool the *edges* (6500–9000 K) and
> keep the key neutral. Warm light on a warm backdrop = mud.

### 2.7 `bpy` — build the entire light rig

```python
# ============================================================================
# 03_light_rig.py  —  full beverage product rig
# Blender 3.6 LTS; 4.x-safe (guards on renamed/added properties).
# Run in the Scripting workspace. Idempotent: re-running rebuilds the rig.
# ============================================================================
import bpy, math
from mathutils import Vector

HERO   = Vector((0.0, 0.0, 0.14))      # aim point ~ label centre
RIGCOL = "LIGHTS_Product"

# ---------- helpers ---------------------------------------------------------
def get_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def purge(prefixes=("KEY_", "STRIP_", "KICK_", "TOP_", "CARD_", "FLAG_")):
    for ob in list(bpy.data.objects):
        if ob.name.startswith(prefixes):
            bpy.data.objects.remove(ob, do_unlink=True)

def aim_euler(loc, target, track='-Z', up='Y'):
    """Euler that points `track` axis of an object at `loc` toward `target`."""
    return (Vector(target) - Vector(loc)).to_track_quat(track, up).to_euler()

def add_area(name, shape, size, size_y, loc, target, power, color,
             spread_deg=180.0, cam_vis=True, max_bounces=1024,
             cast_shadow=True, caustics=False, col=None):
    ldata = bpy.data.lights.new(name=name, type='AREA')
    ldata.shape   = shape                      # SQUARE / RECTANGLE / DISK / ELLIPSE
    ldata.size    = size
    if shape in {'RECTANGLE', 'ELLIPSE'}:
        ldata.size_y = size_y
    ldata.energy  = power                      # Watts
    ldata.color   = color
    ldata.spread  = math.radians(spread_deg)   # RADIANS in Python
    ldata.cycles.max_bounces = max_bounces
    ldata.cycles.cast_shadow = cast_shadow
    ldata.cycles.use_multiple_importance_sampling = True
    # Shadow Caustics (3.4+). Name has been stable, but guard anyway.
    if caustics and hasattr(ldata.cycles, "is_caustics_light"):
        ldata.cycles.is_caustics_light = True

    ob = bpy.data.objects.new(name, ldata)
    ob.location       = loc
    ob.rotation_euler = aim_euler(loc, target, '-Z', 'Y')
    ob.visible_camera = cam_vis                # Object-level ray visibility (3.0+)
    (col or bpy.context.scene.collection).objects.link(ob)
    return ob

def add_card(name, w, h, loc, target, emit=None, base=None, strength=1.0,
             cam_vis=False, diffuse_vis=True, col=None):
    """Emission or black-flag plane. Plane normal is +Z, so we track 'Z'."""
    me = bpy.data.meshes.new(name)
    vs = [(-w/2, -h/2, 0), (w/2, -h/2, 0), (w/2, h/2, 0), (-w/2, h/2, 0)]
    me.from_pydata(vs, [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location       = loc
    ob.rotation_euler = aim_euler(loc, target, 'Z', 'Y')
    ob.visible_camera      = cam_vis
    ob.visible_diffuse     = diffuse_vis
    ob.visible_glossy      = True
    ob.visible_transmission= True
    ob.visible_shadow      = False             # cards should never cast shadows
    (col or bpy.context.scene.collection).objects.link(ob)

    mat = bpy.data.materials.new(name + "_MAT")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    if emit is not None:
        node = nt.nodes.new('ShaderNodeEmission')
        node.inputs['Color'].default_value    = (*emit, 1.0)
        node.inputs['Strength'].default_value = strength
    else:
        node = nt.nodes.new('ShaderNodeBsdfDiffuse')
        node.inputs['Color'].default_value = (*base, 1.0)
    node.location = (-220, 0)
    nt.links.new(node.outputs[0], out.inputs['Surface'])
    ob.data.materials.append(mat)
    return ob

K5600 = (1.000, 0.930, 0.880)
K6500 = (1.000, 1.000, 1.000)
K7000 = (0.930, 0.960, 1.000)
K4000 = (1.000, 0.800, 0.630)

# ---------- build -----------------------------------------------------------
purge()
COL = get_collection(RIGCOL)

add_area("KEY_Soft",   'RECTANGLE', 1.20, 1.80, (-1.10, -0.95, 1.15), HERO,
         600.0, K5600, spread_deg=150, cam_vis=True,  max_bounces=8,  col=COL)

add_area("STRIP_L",    'RECTANGLE', 0.12, 1.10, (-0.62,  0.55, 0.45), (0, 0, 0.16),
         180.0, K6500, spread_deg=45,  cam_vis=False, max_bounces=0,  col=COL)

add_area("STRIP_R",    'RECTANGLE', 0.12, 1.10, ( 0.62,  0.55, 0.45), (0, 0, 0.16),
         140.0, K7000, spread_deg=45,  cam_vis=False, max_bounces=0,  col=COL)

add_area("KICK_Liquid",'DISK',      0.30, 0.30, ( 0.10,  0.62, 0.16), (0, 0, 0.13),
         250.0, K4000, spread_deg=180, cam_vis=False, max_bounces=4,
         cast_shadow=False, caustics=True, col=COL)

add_area("TOP_Cap",    'SQUARE',    0.45, 0.45, ( 0.00, -0.10, 0.95), (0, 0, 0.25),
         120.0, K6500, spread_deg=110, cam_vis=False, max_bounces=4,  col=COL)

add_card("CARD_Bounce_R", 1.20, 1.60, ( 1.25, -0.70, 0.50), (0, 0, 0.13),
         emit=(1, 1, 1), strength=1.5, col=COL)
add_card("FLAG_Neg_R",    1.00, 1.60, ( 0.95, -1.20, 0.20), (0, 0, 0.13),
         base=(0.02, 0.02, 0.02), col=COL)

WCOL = get_collection("LIGHTS_Water")
w1 = add_card("CARD_Water_L", 2.20, 2.60, (-1.90, -0.20, 1.00), (0, 0, 0.30),
              emit=(1, 1, 1), strength=4.0, diffuse_vis=False, col=WCOL)
w2 = add_card("CARD_Water_R", 2.20, 2.60, ( 1.90, -0.20, 1.00), (0, 0, 0.30),
              emit=(1, 1, 1), strength=4.0, diffuse_vis=False, col=WCOL)
w3 = add_card("CARD_Sky",     3.00, 3.00, ( 0.00,  0.20, 2.20), (0, 0, 0.25),
              emit=(0.93, 0.96, 1.0), strength=2.0, diffuse_vis=False, col=WCOL)

# ---------- Light Group (3.2+) so the water cards can be re-mixed later -----
vl = bpy.context.view_layer
if "WATER" not in [lg.name for lg in vl.lightgroups]:
    vl.lightgroups.new(name="WATER")
for ob in (w1, w2, w3):
    ob.lightgroup = "WATER"

# ---------- Light Linking (4.0+ ONLY) --------------------------------------
# Restrict the water cards so they illuminate ONLY the splash + liquid.
# In 3.6 this block is skipped and you rely on diffuse-visibility + lightgroups.
if bpy.app.version >= (4, 0, 0):
    recv = get_collection("LL_WaterReceivers")
    for target_name in ("SPLASH_MESH", "LIQUID"):          # rename to your objects
        t = bpy.data.objects.get(target_name)
        if t and t.name not in recv.objects:
            recv.objects.link(t)
    for ob in (w1, w2, w3):
        ob.light_linking.receiver_collection = recv
    print("Light linking applied (Blender 4.x).")
else:
    print("Blender 3.x: no light linking; using lightgroup 'WATER' + diffuse-vis off.")

print("Light rig built in collections:", RIGCOL, "/ LIGHTS_Water")
```

**4.x flags in the code above**
- `ob.light_linking.receiver_collection` / `.blocker_collection` — **4.0+ only**.
- `light.use_shadow` (a per-light shadow toggle separate from `cycles.cast_shadow`) — **4.2+**;
  in 4.2 EEVEE Next this is the one that matters.
- `light.cycles.is_caustics_light` still valid through 4.5.
- `light.normalize` (**4.5**) — new option to keep intensity constant when resizing the light.
  If you are on 4.5 and your key changes brightness when you scale it, that's this toggle.

