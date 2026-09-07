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

---

## 3. HDRI vs hand-built lights

| | Hand-built rig | Studio-softbox HDRI |
|---|---|---|
| Control over each highlight | **Total** — move one light, move one highlight | Coarse: you can only rotate/scale the whole environment |
| Water / splash reflections | Needs the big white cards of §1.6 | **Excellent out of the box** — a real 360° environment fills every facet of a chaotic splash mesh |
| Noise | Low (MIS on discrete lights) | Higher, especially with a high-contrast HDRI; needs more samples |
| Speed to a decent look | Slow | **Instant** |
| Art-directable | Yes | Only if you build/paint the HDRI |
| Render cost | Low | Moderate (env sampling on every ray) |

**When the HDRI wins:** the splash. A fluid mesh has thousands of randomly-oriented micro-facets;
each one mirrors a different direction. With five discrete lights, most facets see *black*, and
the splash reads dark and dead with a few blown speculars. With a studio HDRI every facet sees
*something*, and the crown lights up evenly. This is exactly what the reference frame shows:
a splash that is bright silver-white across its whole surface.

**The recommended hybrid for this shot** — and what most commercial artists actually do:

1. **HDRI in the world** at low-to-moderate strength (0.3–1.0) purely as **specular
   environment** for the water and glass.
2. **Hand-built rig on top** for the shapes that must be art-directed (key, strips, kicker).
3. **HDRI hidden from camera** so the orange gradient backdrop is what you see.

### 3.1 Rotating an HDRI with a Mapping node

```
Texture Coordinate (Generated) → Mapping (Rotation Z) → Environment Texture → Background → World Output
```

The `Rotation Z` on the Mapping node spins the environment around the vertical axis; that is
how you slide a softbox reflection along the bottle without touching a light. **Rotation Z is
your highlight-position dial.** Keyframe it for a slow drifting shimmer across the glass
(0.5–3° over the whole 250 frames — any more looks like the world is spinning).

```python
import bpy, math
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
nt = world.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_WORLD':
        nt.nodes.remove(n)
out  = nt.nodes['World Output']
bg   = nt.nodes.new('ShaderNodeBackground');        bg.location   = (-200, 0)
env  = nt.nodes.new('ShaderNodeTexEnvironment');    env.location  = (-500, 0)
map_ = nt.nodes.new('ShaderNodeMapping');           map_.location = (-750, 0)
tc   = nt.nodes.new('ShaderNodeTexCoord');          tc.location   = (-950, 0)

env.image = bpy.data.images.load("//hdri/studio_softbox_4k.exr")   # your file
bg.inputs['Strength'].default_value = 0.6
map_.inputs['Rotation'].default_value[2] = math.radians(35.0)      # THE dial

nt.links.new(tc.outputs['Generated'], map_.inputs['Vector'])
nt.links.new(map_.outputs['Vector'],  env.inputs['Vector'])
nt.links.new(env.outputs['Color'],    bg.inputs['Color'])
nt.links.new(bg.outputs['Background'],out.inputs['Surface'])
```

> On 4.x, `Texture Coordinate → Generated` into Mapping still works. Some rigs use
> `Vector → Mapping` with the default; Generated is the reliable one for a world.

### 3.2 Keeping the HDRI out of the visible background

Three options — **they are not equivalent:**

| Method | RNA | Effect | Use when |
|---|---|---|---|
| **Film → Transparent** | `scene.render.film_transparent = True` | Alpha-0 background. World still lights and still reflects. | You will comp a background later. **Not** what you want here — you already have a gradient backdrop *object*. |
| **World Ray Visibility → Camera OFF** | `world.cycles_visibility.camera = False` | World is invisible to primary rays but **still visible in reflections/refractions**. Background renders black (or shows whatever geometry is there — your backdrop). | **This is the right one for this shot.** |
| **Light Path → Is Camera Ray → Mix** | shader-level | Same as above but you can substitute a *different* colour for camera rays | You want a flat colour behind, while a rich HDRI lights the scene |

```python
w = bpy.context.scene.world
w.cycles_visibility.camera      = False   # hide from primary rays
w.cycles_visibility.diffuse     = True
w.cycles_visibility.glossy      = True    # <- keep: this is what the water reflects
w.cycles_visibility.transmission= True
w.cycles_visibility.scatter     = True
```

Also worth setting: `world.cycles.sampling_method = 'AUTOMATIC'` (3.6) — or `'MANUAL'` with a
higher `sample_map_resolution` (1024–2048) if a high-contrast HDRI is producing noise.

---

## 4. The gradient backdrop is a light — treat it as one

The saturated orange→amber seamless backdrop in the reference frame is doing **three jobs**:

1. It is the visible background.
2. It is the **largest light source in the scene** — an emissive plane subtending a huge solid
   angle behind and around the product. It is your ambient/fill.
3. It is the **colour of the shot**. Every diffuse surface picks up its orange bounce; every
   glossy surface mirrors it. Kill it and the bottle turns grey.

### 4.1 How to drive it

Two builds, pick one:

| Build | How | Pros | Cons |
|---|---|---|---|
| **Emissive backdrop** | Backdrop mesh with an `Emission` (or Principled with Emission) driven by a Gradient Texture through a ColorRamp | Exactly the pixels you want; independent of lighting; zero noise on the background itself | It *emits*, so it also lights the product — brightness is coupled to look |
| **Lit backdrop** | Diffuse/rough backdrop lit by its own dedicated wide area light with a gradient gobo | Photographically honest; reacts to the rig | Harder to get the exact gradient; adds noise |

The reference frame's perfectly smooth, noise-free gradient says **emissive**. Use emissive.

### 4.2 Balancing backdrop emission against the key

This is the single most important exposure relationship in the shot.

| Backdrop emission | Result |
|---|---|
| Too low (< 0.5) | Backdrop reads brown/muddy; product looks like it's floating in a dark box; edge lights look neon and detached |
| **Sweet spot (≈ 1.0–2.5)** | Backdrop sits ~1–1.5 stops **below** the key's diffuse value on the label; product separates; orange bounce warms the bottle's shadow side |
| Too high (> 4) | Backdrop's own GI washes the product, flattens contrast, **eats the specular contrast of the strip lights**, and the splash loses its silver — everything goes orange |

**The measurement, not the vibe:** with **False Colour** view transform (§10.5), the label
should sit **green (~0.18 mid-grey)**, the backdrop **just below** it, and the specular hits on
the glass in the orange/red band (not large white). If your backdrop is greener than your
label, it is too bright.

**Controls that let you have a bright background without wrecking the product:**
- Backdrop object → **Ray Visibility → Diffuse OFF** — it stays bright on camera but stops
  bouncing orange onto everything. Extreme, but a legitimate save.
- Keep **Glossy ON** — you *want* the orange in the bottle's reflection; that is the shot.
- Backdrop object → **Cycles → Max Bounces / Shadow OFF** to cut cost.
- Push the gradient's *bottom* darker with the ColorRamp rather than lowering global strength:
  a dark floor line under the bottle grounds it without dimming the halo behind it.

**Practical starting values:** backdrop emission **1.8**, key **600 W**, water cards **4.0**.
If you change backdrop strength, re-check the strip lights immediately — they are the first
thing to disappear.

---

## 5. Camera

### 5.1 Focal length — why 85–135 mm

| Lens | On a 0.25 m bottle | Verdict |
|---|---|---|
| 24–35 mm | Massive perspective; the bottle's vertical edges **converge**, the cap looks tiny, the base bulges. Barrel distortion bends the label. | Never for a hero product |
| 50 mm | Mild but visible convergence; still slightly "snapshot" | Acceptable for wide establishing beats only |
| **85 mm** | Near-parallel verticals, natural silhouette, camera ~1.7 m out | **Good** — a touch more depth in the splash |
| **100 mm** | Essentially orthographic on a 0.25 m subject; camera ~2.0 m out | **The default for this shot** |
| **135 mm** | Maximum compression; splash layers stack flat and graphic; camera ~2.7 m out | Great for a very graphic, flat, poster-like frame |
| 200 mm+ | Compression so extreme depth reads as a cutout; camera far away, hard to light around | Only for extreme macro detail beats |

**Why long is right, in three sentences.** (1) **Straight edges stay straight** — a bottle is
a vertical cylinder and any convergence instantly looks amateur. (2) **Compression flattens
the silhouette**, so the two strip-light lines run parallel down the sides instead of
converging, which is the whole look. (3) **Longer lens = narrower FOV = smaller set**: the
backdrop only has to cover a 0.72 m × 0.41 m window at 2 m instead of a whole room.

**Sensor.** Leave `sensor_width = 36.0 mm` (full-frame, Blender default) and
`sensor_fit = 'AUTO'`. Every focal-length intuition photographers have is full-frame-based; if
you change the sensor you invalidate all of it. If you must match a real cinema camera:
S35 ≈ 24.89 mm, ARRI Alexa Open Gate ≈ 28.25 mm, Micro Four Thirds = 17.3 mm.

### 5.2 Framing geometry (100 mm, 36 mm sensor, 16:9)

Vertical field of view = `2·atan((36 × 9/16) / (2 × 100)) = 11.6°`.

| Camera distance | Frame height | Frame width | 0.25 m bottle fills |
|---|---|---|---|
| 1.5 m | 0.304 m | 0.540 m | 82 % — too tight |
| **2.0 m** | **0.405 m** | **0.720 m** | **62 % — generous headroom, splash breaks both edges** ✔ |
| 2.5 m | 0.506 m | 0.900 m | 49 % — wide/graphic |
| 3.0 m | 0.608 m | 1.080 m | 41 % — establishing |

**Use 2.0 m.** That matches the reference framing: bottle centred, slightly low, headroom above
the cap, splash exceeding both side edges.

### 5.3 Camera height — the hero low angle

| Camera Z | Reads as |
|---|---|
| 0.30 m (above the cap) | Looking down — diminutive, "product on a shelf" |
| 0.13 m (label centre, dead level) | Neutral, catalogue |
| **0.10–0.12 m (just below label centre)** | **Hero.** The bottle is very slightly above you; the cap gains presence; the backdrop horizon drops so the bottle stands *against* the gradient rather than sitting *on* a floor line |
| 0.03 m (near the base) | Monumental / heroic-to-a-fault; you start seeing the underside of the splash |

**Use `z = 0.11`.** With the aim point at `z = 0.14`, you get a 0.9° upward tilt — enough to
read as "looking up" without any keystoning on the vertical edges.

### 5.4 Depth of field

**Blender's DOF is physically real**: `aperture_fstop` is an actual f-number, and depth of
field follows `H = f²/(N·c) + f`. Computed for **100 mm, subject at 2.0 m, full-frame
CoC 0.030 mm**:

| f-stop | Total DOF at 2.0 m | Near / far limits | Effect on the shot |
|---|---|---|---|
| **f/1.4** | ~32 mm | 1.984 – 2.016 | Only the label face is sharp; the bottle's own curvature goes soft. Too much. |
| **f/2.0** | ~46 mm | 1.977 – 2.023 | Dreamy; bottle edges soften |
| **f/2.8** | ~64 mm | 1.969 – 2.032 | Bottle *just* holds (body depth ≈ 70 mm); foreground fruit melts. Very filmic. |
| **f/4.0** | ~91 mm | 1.955 – 2.047 | **Recommended.** Whole bottle sharp, splash immediately in front/behind softens, flying fruit strongly defocused. Matches the reference. |
| **f/5.6** | ~128 mm | 1.937 – 2.065 | Safe; splash starts to hold detail |
| **f/8.0** | ~183 mm | 1.911 – 2.094 | Nearly everything sharp; only the closest fruit blurs |
| **f/16** | ~370 mm | 1.826 – 2.196 | Effectively deep focus |

**Focus object vs focus distance**

| | `dof.focus_distance` | `dof.focus_object` |
|---|---|---|
| What | A scalar in metres along the camera's local −Z | The camera focuses on another object's **origin** |
| Breaks when | Camera moves (a push-in changes the distance every frame, so the focus plane drifts backward through the product) | Never — the distance is recomputed each frame |
| Animatable | Yes, but you have to keyframe it in sync with the move | Focus pulls become "animate the empty" |

**Always use a focus Empty.** Create `FOCUS_TGT` (Empty, Plain Axes, radius 0.03) at
`(0, 0, 0.14)` — the label centre — and set it as `focus_object`. Now:
- push in, orbit, crane — focus stays locked automatically;
- a focus pull = keyframe the empty's Y from the splash to the label;
- parent the empty to the bottle and it follows if the product is ever animated.

**Extra DOF controls**
- `aperture_blades` — **0 = perfect circular bokeh**. Set **6–8** for polygonal, more
  photographic highlights. Water droplets become tiny hexagons: very "shot on a Zeiss".
- `aperture_rotation` — rotates the blade polygon.
- `aperture_ratio` — **1.0** = circular; **1.6–2.0** = anamorphic oval bokeh. Note this only
  stretches the *bokeh*, it does not give you anamorphic squeeze or flares.

**The DOF trade-off in a splash shot — read this before committing**

The splash is the most expensive and most detailed asset in the scene. Depth of field
**destroys the detail you paid for**: the fine crown ridges, the ligaments and the droplets in
front of and behind the focal plane turn to porridge. Simultaneously it is the thing that
makes the shot look photographed rather than rendered.

Resolution:
1. Keep the aperture **moderate (f/4–f/5.6)** so the splash *near the bottle* stays sharp and
   only the extreme foreground/background elements blur.
2. Put the **hero splash geometry within ±5 cm of the focus plane** deliberately when you set
   up the simulation framing. Bokeh should be spent on the flying fruit, not on the crown.
3. **Do not render DOF at 64 samples.** Defocused bright specular droplets are the #1 source of
   fireflies (see §13.2).
4. Consider rendering DOF **off** plus a Z/Cryptomatte pass and applying **Defocus in comp**
   for a lookdev pass — then re-enable real DOF for the final. In-render DOF is correct
   (it handles transparency and refraction); comp defocus is fast but wrong through glass.

### 5.5 `bpy` — camera + DOF + focus empty

```python
# ============================================================================
# 03_camera.py — hero camera with a focus empty
# ============================================================================
import bpy, math
from mathutils import Vector

HERO_AIM = Vector((0.0, 0.0, 0.14))
CAM_LOC  = Vector((0.0, -2.0, 0.11))

for n in ("CAM_Hero", "FOCUS_TGT", "CAM_PIVOT"):
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)

# --- focus target -----------------------------------------------------------
focus = bpy.data.objects.new("FOCUS_TGT", None)
focus.empty_display_type = 'PLAIN_AXES'
focus.empty_display_size = 0.03
focus.location = HERO_AIM
bpy.context.scene.collection.objects.link(focus)

# --- orbit pivot (see §6) ---------------------------------------------------
pivot = bpy.data.objects.new("CAM_PIVOT", None)
pivot.empty_display_type = 'SPHERE'
pivot.empty_display_size = 0.08
pivot.location = HERO_AIM
bpy.context.scene.collection.objects.link(pivot)

# --- camera -----------------------------------------------------------------
cdata = bpy.data.cameras.new("CAM_Hero")
cdata.lens             = 100.0          # mm
cdata.sensor_fit       = 'AUTO'
cdata.sensor_width     = 36.0           # full frame
cdata.clip_start       = 0.05
cdata.clip_end         = 100.0
cdata.dof.use_dof          = True
cdata.dof.focus_object     = focus      # NEVER focus_distance on a moving camera
cdata.dof.aperture_fstop   = 4.0
cdata.dof.aperture_blades  = 7          # 0 = circular bokeh; 7 = photographic
cdata.dof.aperture_rotation= 0.0
cdata.dof.aperture_ratio   = 1.0        # >1 = oval / pseudo-anamorphic bokeh
cdata.show_limits          = True       # draw the focus plane in the viewport
cdata.display_size         = 0.15

cam = bpy.data.objects.new("CAM_Hero", cdata)
bpy.context.scene.collection.objects.link(cam)
cam.parent   = pivot                     # local offset from the pivot
cam.location = CAM_LOC - HERO_AIM        # -> (0, -2.0, -0.03)

# --- aim: Track To beats hand-keyed rotation --------------------------------
trk = cam.constraints.new('TRACK_TO')
trk.target     = focus
trk.track_axis = 'TRACK_NEGATIVE_Z'      # cameras look down local -Z
trk.up_axis    = 'UP_Y'                  # locks roll to world up

bpy.context.scene.camera = cam

# --- format -----------------------------------------------------------------
scn = bpy.context.scene
scn.render.resolution_x = 1920
scn.render.resolution_y = 1080
scn.render.resolution_percentage = 100
scn.render.fps = 25
scn.frame_start, scn.frame_end = 1, 250
print("Camera ready: 100mm f/4, focus on FOCUS_TGT, parented to CAM_PIVOT")
```

**Track To vs Damped Track**

| Constraint | Controls | Use |
|---|---|---|
| **Track To** | Aim **and roll** (via `up_axis`) | **Default for a camera.** Horizon stays level. |
| **Damped Track** | Aim only; roll is whatever it was | Use when you *want* to author roll separately (e.g. a Dutch-angle keyframe on the camera's local Y), or when Track To gimbal-flips as the target passes directly overhead |

> Gimbal flip: Track To will snap 180° if the target crosses the pole defined by `up_axis`.
> On a crane-up that passes over the product, switch to **Damped Track** + a rotation-constrained
> parent, or keep the crane below 70° elevation.

---

## 6. Camera animation for a 10-second spot

### 6.1 The four moves, and when each one works

| Move | What it says | Length | Risk |
|---|---|---|---|
| **Slow push-in** | "Look closer. This is the product." | 6–10 s (the whole spot) | Boring if too slow to notice, cheap if too fast. Aim for **20–30 % focal coverage change** total. |
| **Orbit** | "It's real, it's three-dimensional." | 3–6 s, ≤ 40° of arc | A full 360° orbit is a turntable, not an ad. Keep the arc small. |
| **Crane-up reveal** | "Rising into the hero." Great **into** the splash impact. | 2–4 s | Passing the vertical destroys the Track To up-axis (§5.5 note) |
| **Whip-pan in** | Energy, impact, transition | 6–14 frames | Needs motion blur or it strobes; needs something to whip *from* |

**The professional default for a beverage spot: a slow push-in with a 15–25° orbit layered on
top, plus a 3–5 cm crane rise.** Three tiny moves combined read as one rich, expensive move.
One big move reads as a screensaver.

### 6.2 Why the camera is parented to an empty

For a perfect orbit you rotate the **pivot** (an Empty at the product), not the camera. The
camera's local offset from the pivot stays constant, so the radius is exactly constant —
something you will never achieve by keyframing camera XY by hand.

```
CAM_PIVOT (Empty @ 0,0,0.14)
   └── CAM_Hero  (local location 0, -2.0, -0.03)  + Track To → FOCUS_TGT
```

- **Orbit** → keyframe `CAM_PIVOT.rotation_euler.z`
- **Crane** → keyframe `CAM_PIVOT.location.z`
- **Push-in** → keyframe `CAM_Hero.location.y` (its local distance) **or** `camera.data.lens`
  — see §6.4
- **Roll / Dutch** → keyframe `CAM_Hero.rotation_euler.y` (Track To must be replaced with
  Damped Track for this to survive)

### 6.3 Concrete keyframe recipes (25 fps, frames 1–250)

**A. The 10-second hero push-in + micro-orbit + crane (recommended)**

| Object | Channel | F1 | F125 | F250 | Interp |
|---|---|---|---|---|---|
| `CAM_Hero` | `location.y` (local) | −2.35 | — | **−1.90** | Bezier, **Ease In-Out** |
| `CAM_PIVOT` | `rotation_euler.z` | **−14°** | — | **+8°** | Bezier, Ease In-Out |
| `CAM_PIVOT` | `location.z` | 0.10 | — | 0.145 | Bezier, Ease In-Out |
| `FOCUS_TGT` | `location.y` | −0.05 | — | 0.00 | Bezier (subtle focus settle) |

Net effect: 19 % push, 22° of arc, 4.5 cm rise, over 10 s. Nothing is fast; everything is
moving. The splash lands around f150–190 while the camera is still creeping forward.

**B. Whip-pan into the product (frames 1–14, then hold)**

| Object | Channel | F1 | F8 | F14 | F20 |
|---|---|---|---|---|---|
| `CAM_PIVOT` | `rotation_euler.z` | **−75°** | −18° | **+3°** | **0°** |

Interpolation: F1→F8 **Ease Out** (fast start), F8→F14 **Ease In**, F14→F20 a tiny
counter-swing overshoot settle. **Motion blur is mandatory** — at 75° in 13 frames you are
moving ~5.8°/frame; with shutter 0.5 that's a 2.9° smear, which is exactly the streak you want.
Without blur it strobes into a slideshow.

**C. Crane-up reveal (frames 1–70)**

| Object | Channel | F1 | F70 |
|---|---|---|---|
| `CAM_PIVOT` | `location.z` | **−0.22** | **+0.02** |
| `CAM_Hero` | `location.y` | −2.6 | −2.05 |

Starts below the bottle's base looking up through the splash, rises to the hero angle.
Keep `CAM_PIVOT.location.z` from exceeding the aim point or Track To will start looking down.

**D. Slow-orbit beauty pass (a separate 5 s cut, frames 1–125)**

| Object | Channel | F1 | F125 |
|---|---|---|---|
| `CAM_PIVOT` | `rotation_euler.z` | −20° | +20° |

Linear interpolation is acceptable **only** if the cut is a middle section that will be
trimmed at both ends; otherwise ease it.

### 6.4 Dolly vs zoom — do not keyframe the focal length by accident

- **Keyframing `location.y` (dolly)** changes perspective: the background scale changes
  relative to the product. This is a real camera move.
- **Keyframing `camera.data.lens` (zoom)** does not change perspective at all — just crops.
  It reads as *cheap* on a product because the bottle's proportions stay frozen.
- Keyframing **both in opposite directions** = a **dolly zoom / vertigo effect**. Spectacular
  once per career, wrong in a beverage ad.
- **Also: changing `lens` changes DOF.** A zoom-in at fixed f-stop gets shallower. If you must
  zoom, keyframe `aperture_fstop` to compensate.

**Use dolly. Set the lens once and never touch it.**

### 6.5 Easing — the difference between "expensive" and "student"

Blender's default keyframe interpolation is **Bezier** with **auto-clamped** handles, which
already eases. What ruins camera moves is (a) leaving it on **Linear** (robotic starts/stops)
or (b) using **Ease In-Out** on *every* channel so the whole move breathes in unison.

| Feel | Setting | When |
|---|---|---|
| **Ease In-Out** (`easing='EASE_IN_OUT'`, `interpolation='SINE'` or `'QUAD'`) | slow start, slow stop | The overall push-in — the default |
| **Ease Out only** | snaps away, glides to rest | Whip-pan, impacts |
| **Ease In only** | glides in, arrives hard | Camera settling onto a logo |
| **Linear** | constant speed | Only for a middle section of a longer move that gets cut on both sides |
| **Bezier + hand-dragged handles** | anything | The real answer for hero work — open the Graph Editor and shape the velocity curve directly |

**Offset your channels.** If the push, orbit and crane all start and stop on the same frames,
the move reads mechanical. Start the orbit 12 frames after the push and end it 20 frames
before. That overlap is the entire difference.

**Extra polish:** add a `Noise` F-modifier to `CAM_HERO.rotation_euler` with
`strength = 0.0015`, `scale = 40` for a whisper of handheld float. On a locked-off product
this is often what sells "filmed".

### 6.6 `bpy` — orbit + push-in + crane, fully eased

```python
# ============================================================================
# 03_camera_anim.py — 250-frame beverage move: push-in + micro-orbit + crane
# Requires 03_camera.py to have been run (CAM_Hero, CAM_PIVOT, FOCUS_TGT).
# ============================================================================
import bpy, math

scn   = bpy.context.scene
cam   = bpy.data.objects["CAM_Hero"]
pivot = bpy.data.objects["CAM_PIVOT"]
focus = bpy.data.objects["FOCUS_TGT"]

scn.frame_start, scn.frame_end, scn.render.fps = 1, 250, 25

def clear_anim(ob):
    ob.animation_data_clear()

def key(ob, data_path, index, frame, value):
    if data_path == "location":
        ob.location[index] = value
    elif data_path == "rotation_euler":
        ob.rotation_euler[index] = value
    ob.keyframe_insert(data_path=data_path, index=index, frame=frame)

def ease(ob, data_path, index, interp='BEZIER', easing='EASE_IN_OUT', mode='SINE'):
    """Apply interpolation/easing to every key on one channel."""
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            for kp in fc.keyframe_points:
                kp.interpolation = mode if mode in {
                    'SINE', 'QUAD', 'CUBIC', 'QUART', 'QUINT',
                    'EXPO', 'CIRC', 'BACK', 'BOUNCE', 'ELASTIC'} else interp
                kp.easing        = easing
                kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
            fc.update()

for ob in (cam, pivot, focus):
    clear_anim(ob)

# ---- PUSH-IN: camera local Y (distance from pivot) -------------------------
key(cam,   "location", 1, 1,   -2.35)
key(cam,   "location", 1, 250, -1.90)
ease(cam,  "location", 1, mode='SINE', easing='EASE_IN_OUT')

# ---- MICRO-ORBIT: pivot Z rotation, offset in time from the push ----------
key(pivot, "rotation_euler", 2, 12,  math.radians(-14.0))
key(pivot, "rotation_euler", 2, 230, math.radians(  8.0))
ease(pivot,"rotation_euler", 2, mode='SINE', easing='EASE_IN_OUT')

# ---- CRANE: pivot Z height ------------------------------------------------
key(pivot, "location", 2, 1,   0.100)
key(pivot, "location", 2, 250, 0.145)
ease(pivot,"location", 2, mode='SINE', easing='EASE_IN_OUT')

# ---- FOCUS SETTLE: pull from just in front of the label to the label -------
key(focus, "location", 1, 1,   -0.05)
key(focus, "location", 1, 160,  0.00)
ease(focus,"location", 1, mode='SINE', easing='EASE_IN_OUT')

# ---- Optional handheld float ----------------------------------------------
ADD_HANDHELD = False
if ADD_HANDHELD:
    cam.rotation_euler = cam.rotation_euler        # ensure channels exist
    cam.keyframe_insert("rotation_euler", frame=1)
    for fc in cam.animation_data.action.fcurves:
        if fc.data_path == "rotation_euler":
            m = fc.modifiers.new('NOISE')
            m.strength, m.scale, m.phase = 0.0015, 40.0, fc.array_index * 7.0

print("Camera animation written: f1-250 @ 25fps")
```

**Whip-pan variant** (drop in place of the orbit block):

```python
key(pivot, "rotation_euler", 2, 1,  math.radians(-75.0))
key(pivot, "rotation_euler", 2, 8,  math.radians(-18.0))
key(pivot, "rotation_euler", 2, 14, math.radians(  3.0))
key(pivot, "rotation_euler", 2, 20, math.radians(  0.0))
ease(pivot, "rotation_euler", 2, mode='EXPO', easing='EASE_OUT')
```

---

## 7. Motion blur — the make-or-break setting for a splash

A splash is fast-moving, thin, high-contrast geometry. Rendered sharp, every frame is a
crisp sculpture and the animation **strobes**: droplets teleport frame to frame instead of
streaking. Motion blur is not polish here, it is the difference between "liquid" and
"flying plastic".

### 7.1 Cycles motion blur settings

| Setting | UI (Render Properties → Motion Blur) | RNA | Value |
|---|---|---|---|
| Enable | Motion Blur | `scene.render.use_motion_blur` | **True** |
| Position | Position | `scene.cycles.motion_blur_position` | **`'CENTER'`** (blur straddles the frame time — matches a real shutter). `'START'`/`'END'` shift it; use `'START'` only to match an external renderer. |
| **Shutter** | Shutter | `scene.render.motion_blur_shutter` | **0.5** |
| Rolling Shutter | Rolling Shutter → Type / Duration | `scene.cycles.rolling_shutter_type` = `'NONE'` or `'TOP'`; `scene.cycles.rolling_shutter_duration` 0.0–1.0 | `'NONE'` normally; see 7.3 |
| Shutter Curve | Shutter Curve widget | `scene.render.motion_blur_shutter_curve` | Leave flat. A ramped curve gives a soft-edged "ghosting" trail. |

**Shutter 0.5 = the 180° rule.** Cinema shutters are open for half of each frame interval.
`shutter = 0.5` means Cycles samples motion across 0.5 of a frame. At 25 fps that is a
1/50 s exposure — the standard film look.

| Shutter | Angle | Look |
|---|---|---|
| 0.25 | 90° | Crisp, staccato, *Saving Private Ryan*. Splash reads gritty and fast. |
| **0.5** | **180°** | **Standard. Use this.** |
| 0.75 | 270° | Dreamy, smeary |
| 1.0 | 360° | Full smear; adjacent frames overlap completely. Splash becomes fog. |

### 7.2 Per-object motion blur (Cycles)

Object Properties → Motion Blur (visible when Cycles is active):

| Setting | RNA | Note |
|---|---|---|
| Motion Blur (per object) | `ob.cycles.use_motion_blur` | Default True. Turn **off** on the backdrop to save memory. |
| **Deformation** | `ob.cycles.use_deform_motion` | **Must be ON** for anything whose *vertices* move (fluid mesh, cloth, shape keys). Off = only the object transform blurs. |
| **Steps** | `ob.cycles.motion_steps` | Sub-frame samples. `1` = linear between two sub-frames. Raise to **3** for fast rotation/arcs so the blur curves instead of chording. Memory cost ≈ ×(2^steps−1) copies of the mesh — expensive on a big fluid mesh. |

### 7.3 Rolling shutter

`rolling_shutter_type = 'TOP'` simulates a CMOS sensor scanning top→bottom, so fast horizontal
motion skews (the "jello" effect). `rolling_shutter_duration` 0 = global shutter, 1 = full
rolling. Use **0.0 / `'NONE'`** for a clean commercial. Use **0.3–0.5** only if you are
deliberately matching handheld phone footage or a whip-pan plate shot on a DSLR.

### 7.4 THE classic failure: the fluid mesh does not blur

**Symptom.** The camera and the bottle blur correctly. The splash is razor sharp in every
frame and strobes horribly. Motion blur is on, deformation motion blur is on, and it still
does not work.

**Cause.** Cycles builds deformation motion blur by comparing the mesh at sub-frame times and
interpolating **per-vertex**. That requires the **vertex count and ordering to be identical**
across those sub-frames. A Mantaflow liquid mesh is **re-meshed from scratch every frame** —
the vertex count changes constantly. Cycles has nothing to interpolate, silently gives up, and
renders the mesh static.

**The fix: Speed Vectors.**

*Physics Properties → Fluid (Domain) → Liquid → **Mesh** → **Speed Vectors***
(`domain_settings.use_speed_vectors = True`)

This makes Mantaflow write a per-vertex **velocity attribute** into the baked mesh. Cycles
reads that attribute and blurs each vertex along its own velocity vector — **no vertex
correspondence required**. This is the same mechanism Cycles uses for Alembic/USD caches.

**Requirements and gotchas — all of them matter:**

| Requirement | Detail |
|---|---|
| **Mesh must be enabled** | The Speed Vectors checkbox only appears when Domain → Liquid → **Mesh** is on. Particle-only liquid has no mesh to blur. |
| **You must RE-BAKE** | Enabling Speed Vectors invalidates the mesh cache. *Free Mesh* → *Bake Mesh* (or Free All → Bake All). Toggling it without re-baking changes nothing. |
| **Cache type** | Works with **Replay / Modular / Final**. If you are on Modular, re-bake the **Mesh** step specifically. |
| Disk + memory cost | The velocity attribute adds ~30–50 % to the mesh cache size. |
| `use_deform_motion` | Still enable it on the fluid object. |
| **Motion steps** | Leave at **1** for fluid. Velocity-based blur is linear anyway, and higher steps multiply memory on an already-huge mesh. |
| Upres | If you use *Mesh → Upres Factor*, bake speed vectors at the same time; upresing afterwards discards them. |

```python
import bpy
dom = bpy.data.objects["FluidDomain"]                 # your domain object
mod = next(m for m in dom.modifiers if m.type == 'FLUID')
ds  = mod.domain_settings
ds.use_mesh          = True
ds.use_speed_vectors = True      # <-- THE fix. Re-bake the mesh after setting this.
# Cycles per-object motion blur on the domain:
dom.cycles.use_motion_blur  = True
dom.cycles.use_deform_motion= True
dom.cycles.motion_steps     = 1
# Scene-level:
scn = bpy.context.scene
scn.render.use_motion_blur      = True
scn.render.motion_blur_shutter  = 0.5
scn.cycles.motion_blur_position = 'CENTER'
scn.cycles.rolling_shutter_type = 'NONE'
```

### 7.5 Alternative: the Vector pass + comp blur

If ray-traced motion blur is too expensive (it can double or triple render time on a heavy
splash), render **without** motion blur and blur in the compositor.

| Step | Setting |
|---|---|
| Enable the pass | View Layer Properties → Passes → Data → **Vector** (`view_layer.use_pass_vector = True`) |
| **Disable render motion blur** | `scene.render.use_motion_blur = False` — **mandatory**: the Vector pass is not written when motion blur is enabled |
| Output | Must be **Multilayer OpenEXR** — vectors are 4-channel signed float and will be destroyed by PNG |
| Comp | Render Layers → **Vector Blur** node (Samples 32, Blur 1.0, Speed min/max 0) |

**Trade-offs:** Vector Blur is a 2D screen-space smear. It cannot blur *behind* a transparent
surface, it produces artefacts where fast objects cross silhouette edges, and it does nothing
for blur *seen through* the bottle glass. On a splash-through-glass shot it will show. Use it
for lookdev and previews; use real Cycles blur for the final. Also note the fluid still needs
**Speed Vectors** for the fluid mesh's velocities to reach the Vector pass at all.

---

## 8. Cycles settings for this shot

### 8.1 Device

```python
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'     # 'OPTIX'|'CUDA'|'HIP'|'ONEAPI'|'METAL'|'NONE'
prefs.get_devices()
for d in prefs.devices:
    d.use = (d.type in {'OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'})   # GPU only
bpy.context.scene.cycles.device = 'GPU'
```

| Backend | Hardware | Notes |
|---|---|---|
| **OptiX** | NVIDIA RTX | Fastest for this scene — hardware ray tracing on a heavy refractive mesh is a huge win. Also unlocks the OptiX denoiser. |
| CUDA | Any NVIDIA | Fallback; slower than OptiX on RTX cards |
| HIP | AMD RDNA2+ | Works; MNEE caustics support has historically lagged |
| oneAPI | Intel Arc | 3.6+ |
| Metal | Apple Silicon | Good; watch VRAM on unified memory — the fluid mesh competes with everything else |

**Enabling CPU *and* GPU together** speeds up small-tile work slightly but can *slow down*
heavy scenes (the CPU becomes the straggler on the last tile). For a 1920×1080 splash render:
**GPU only**.

### 8.2 Sampling

| Setting | RNA | Lookdev | Final |
|---|---|---|---|
| Max Samples | `cycles.samples` | 128 | **1024–2048** |
| Min Samples | `cycles.adaptive_min_samples` | 0 (auto) | 0 (auto) |
| Adaptive Sampling | `cycles.use_adaptive_sampling` | True | True |
| **Noise Threshold** | `cycles.adaptive_threshold` | **0.05** | **0.0035–0.005** |
| Time Limit | `cycles.time_limit` | 20 s/frame | 0 (off) |
| Seed / Animate Seed | `cycles.seed`, `cycles.use_animated_seed` | — | **`use_animated_seed = True`** |
| Light Tree (3.5+) | `cycles.use_light_tree` | True | True |
| Light Sampling Threshold | `cycles.light_sampling_threshold` | 0.01 | 0.01 |

**Adaptive sampling is the real dial, not Max Samples.** `adaptive_threshold` is the per-pixel
noise level at which Cycles stops. Max Samples is only the ceiling it is allowed to reach.
Halving the threshold roughly quadruples the samples spent on noisy regions. On a splash the
water eats the entire budget while the flat backdrop finishes in 16 samples — which is exactly
what you want.

**`use_animated_seed = True` is not optional for animation.** With a fixed seed, the noise
pattern is identical every frame, which the denoiser turns into a *static* grain that looks
like a dirty lens. With an animated seed the residual noise moves and reads as film grain.

### 8.3 Denoising

| Setting | RNA | Value |
|---|---|---|
| Denoise (render) | `cycles.use_denoising` | True |
| Denoiser | `cycles.denoiser` | `'OPENIMAGEDENOISE'` for finals, `'OPTIX'` for viewport |
| Passes | `cycles.denoising_input_passes` | **`'RGB_ALBEDO_NORMAL'`** |
| Prefilter (OIDN) | `cycles.denoising_prefilter` | `'ACCURATE'` for finals, `'FAST'` for lookdev |
| Viewport denoise | `cycles.use_preview_denoising`, `cycles.preview_denoiser` | True, `'OPTIX'` (or `'AUTO'`) |
| Denoise on GPU (**4.0+**) | `cycles.denoising_use_gpu` | True if you have the VRAM |

| | OptiX denoiser | OpenImageDenoise (OIDN) |
|---|---|---|
| Speed | Very fast (GPU, NVIDIA only) | Slower; CPU in 3.6, GPU-capable in 4.0+ |
| Quality on **water/glass** | Softer; can smear fine droplets and erase caustic sparkle | **Better** — preserves high-frequency specular detail |
| Temporal stability | Poorer | Poorer, but less bad |
| Use | Viewport / lookdev | **Final frames** |

**Denoise at render vs denoise in comp**

- **At render** (`use_denoising`): simple, bakes the result into the output. Fine for PNG output.
- **In comp:** turn scene denoising **off**, enable *View Layer → Passes → Data →
  **Denoising Data*** (`view_layer.cycles.denoising_store_passes = True`), write **multilayer
  EXR**, and feed Noisy Image + Denoising Normal + Denoising Albedo into the **Denoise** node.
  You keep the noisy original forever and can re-denoise without re-rendering. **This is the
  professional workflow for animation** — you *will* want to retune it.

**Temporal flicker warning.** Cycles has no temporal denoiser. Frame-independent denoising of a
sparkly splash produces boiling. Mitigations, in order of effectiveness:
1. Lower the noise threshold (0.0035) so the denoiser has less work to invent.
2. Raise Max Samples so bright speculars converge.
3. Denoise in comp with a slightly reduced strength and let a little grain through — grain
   reads as film, boiling reads as broken.
4. Externally: run OIDN with motion vectors, or Neat Video, over the sequence.

### 8.4 Light Paths — and why Transmission must go up

Defaults in 3.6: Total 12, Diffuse 4, Glossy 4, Transmission 12, Volume 0, Transparent 8.

**Count the interfaces a single camera ray crosses in this shot:**

```
camera → splash sheet front (1) → splash sheet back (2)
       → bottle glass outer  (3) → bottle glass inner (4)
       → amber liquid enter  (5) → liquid exit        (6)
       → bottle glass inner  (7) → bottle glass outer (8)
       → a second splash ligament in front of the backdrop (9)(10)
       → droplet (11)(12) → ...
```

**Every refractive interface costs one transmission bounce.** Water/glass/liquid meshes are
solid volumes with two surfaces each, so bounces are consumed in pairs and they add up
brutally. When the budget runs out, **Cycles terminates the ray and returns black.** That is
the origin of the classic *black core in the bottle*, *black patches in the splash*, and
*dark rings in the droplets*.

| Setting | RNA | Lookdev | **Final** | Why |
|---|---|---|---|---|
| **Total** | `cycles.max_bounces` | 12 | **32** | Must be ≥ the largest individual limit |
| Diffuse | `cycles.diffuse_bounces` | 2 | **4** | Backdrop/label; more adds nothing |
| Glossy | `cycles.glossy_bounces` | 4 | **10** | Inter-reflections between splash facets and the glass |
| **Transmission** | `cycles.transmission_bounces` | 8 | **16–24** | **The critical one.** Start at 16; go to 24 if any part of the splash or liquid still reads black. |
| Volume | `cycles.volume_bounces` | 0 | **2** | Only if the liquid or a fog card uses a Volume shader |
| **Transparent** | `cycles.transparent_max_bounces` | 8 | **16** | Separate budget: alpha-mapped labels, bubble cards, transparent shadow through the splash. If the splash's *shadow* is opaque black, this is the setting. |

**How to diagnose:** set Transmission to 2 and render — the bottle goes black. Raise it until
the black disappears, then add 4 for the frames where the splash stacks deeper. Do not just
set everything to 128: transmission bounces are the most expensive rays in the scene and
double-digit increases cost real time.

### 8.5 Clamping, Filter Glossy and caustics

| Setting | RNA | Value | Trade-off |
|---|---|---|---|
| **Clamp Direct** | `cycles.sample_clamp_direct` | **0.0 (off)** | Clamping direct light dims your strip-light speculars — the whole look. Never clamp direct on a product shot. |
| **Clamp Indirect** | `cycles.sample_clamp_indirect` | **10.0** default; **0 (off)** for max quality, **5–10** if fireflies are unmanageable | Kills fireflies, *also* kills genuine caustic sparkle in the water. Lowering below ~3 visibly dulls the splash. |
| **Filter Glossy** | `cycles.blur_glossy` | **0.5** (default 1.0) | Blurs sharp glossy/caustic paths to reduce noise. 1.0 is safe but softens droplet caustics; 0.0 is sharpest and noisiest. **0.5 is the compromise for water.** |
| Reflective Caustics | `cycles.caustics_reflective` | **True** | Off = flatter, cleaner water |
| Refractive Caustics | `cycles.caustics_refractive` | **True** | Off = the amber pool of light under the bottle disappears. This is a *look* decision, not a quality one. |
| Fast GI Approximation | `cycles.use_fast_gi`, `cycles.fast_gi_method` | Lookdev only: `True`, `'REPLACE'`, `ao_bounces_render = 1` | Replaces deep GI with AO. Big speedup, flattens the shot. **Off for finals.** |

**The firefly trade-off, stated plainly:** fireflies are *real* light — a sample that found a
tiny, extremely bright path (a droplet focusing the strip light into the lens). Clamping is
lying about that energy. Prefer, in order: (1) more samples / lower threshold,
(2) make the source physically larger (a 0.12 m strip instead of a 0.02 m one),
(3) Filter Glossy 0.5, (4) Clamp Indirect 10, (5) Clamp Indirect 3 as a last resort.

### 8.6 Performance settings

| Setting | RNA | Value | Note |
|---|---|---|---|
| **Persistent Data** | `scene.render.use_persistent_data` | **True** | **The biggest single win for animation.** Keeps the BVH, textures and geometry in memory between frames. On a scene with a big static bottle + backdrop, saves 20–60 % of total render time. Costs RAM/VRAM. **Caveat:** the fluid mesh changes every frame and *is* re-uploaded, and persistent data has historically leaked memory on long sequences — if RAM climbs frame after frame, turn it off. |
| Auto Tiles | `cycles.use_auto_tile` | True | |
| Tile Size | `cycles.tile_size` | **2048** (default). Drop to **1024 / 512** when short on VRAM | Smaller tiles = less peak VRAM, slightly slower |
| Simplify (viewport) | `render.use_simplify`, `simplify_subdivision` | True, **1** | Viewport only; make sure `simplify_subdivision_render` stays high |
| Texture Limit (viewport) | `cycles.texture_limit` | `'2048'` | |
| Texture Limit (render) | `cycles.texture_limit_render` | `'OFF'` | |
| Film Filter Width | `render.filter_width` | **1.50 px** (default). 1.2 for crisper droplets; 2.0 to soften aliasing on thin ligaments | |
| Film Transparent | `render.film_transparent` | **False** here — the backdrop is the background | |
| Pixel Filter type | `cycles.pixel_filter_type` | `'BLACKMAN_HARRIS'` | |

---

## 9. EEVEE / EEVEE Next as an alternative

### 9.1 What you gain and lose

| | Cycles | EEVEE (3.6) / EEVEE Next (4.2+) |
|---|---|---|
| Frame time, this shot | 1–6 min @1080p | **1–6 seconds** |
| True refraction | Yes, unlimited | **No** — screen-space only |
| Caustics | Yes | **No** (fake with a projected texture) |
| Reflections of off-screen objects | Yes | **No** — SSR can only reflect what is on screen; needs light/reflection probes |
| Correct transmission stacking (splash over glass over liquid) | Yes | **No** — one refraction layer, then it falls back to the probe/world |
| Soft shadows from big area lights | Yes, free | Approximated (`use_soft_shadows`, shadow map res) |
| Motion blur on a fluid mesh | Yes, via speed vectors | 3.6 EEVEE: accumulation blur, works but no per-vertex velocities; 4.2 EEVEE Next: much better |
| Verdict for this shot | **Final** | **Lookdev, previz, camera blocking, client WIP** |

**Use EEVEE to block the camera move and time the splash.** Render the final in Cycles.

### 9.2 Making a splash look acceptable in EEVEE 3.6

| Setting | RNA | Value |
|---|---|---|
| Screen Space Reflections | `scene.eevee.use_ssr` | **True** |
| **Refraction** | `scene.eevee.use_ssr_refraction` | **True** (and per-material `mat.use_screen_refraction = True`) |
| SSR Half Res Trace | `scene.eevee.use_ssr_halfres` | **False** (droplets need full res) |
| SSR Max Roughness | `scene.eevee.ssr_max_roughness` | 1.0 |
| SSR Thickness | `scene.eevee.ssr_thickness` | 0.02–0.2 — **tune this**; it is what stops reflections tearing off thin splash sheets |
| Bloom | `scene.eevee.use_bloom` | True, Threshold 1.0, Intensity 0.02–0.05 |
| Ambient Occlusion | `scene.eevee.use_gtao` | True, Distance 0.2 |
| Soft Shadows | `scene.eevee.use_soft_shadows` | True |
| Shadow Cube / Cascade | `shadow_cube_size`, `shadow_cascade_size` | `'2048'` |
| Render samples | `scene.eevee.taa_render_samples` | 64–128 |
| Motion blur | `scene.eevee.use_motion_blur`, `motion_blur_shutter`, `motion_blur_steps` | True, 0.5, 4 |

**Material-side requirements (3.6):** on water/glass materials set
`mat.use_screen_refraction = True`, `mat.blend_method = 'HASHED'` (or `'BLEND'`),
`mat.use_backface_culling = True` (removes the double-surface mess), and set
`mat.refraction_depth` to the object's approximate thickness so the fake refraction offset is
plausible. Add an **Irradiance Volume + Reflection Cubemap** around the product and bake
indirect lighting, or your splash will reflect nothing but the world.

**Known limits you cannot fix:** anything outside the camera frustum is not in the screen-space
buffer, so a splash at the frame edge loses its reflections and goes dark. Compensate by
raising the world/HDRI strength — EEVEE falls back to the world when the SSR trace misses.

### 9.3 EEVEE Next (Blender 4.2+) differences

| 3.6 EEVEE | 4.2 EEVEE Next |
|---|---|
| `scene.eevee.use_bloom` | **Removed.** Bloom is now a **compositor Glare node** (and a real-time viewport compositor option). Scripts that set `use_bloom` will error — guard with `hasattr`. |
| `use_ssr` / `use_ssr_refraction` | Replaced by a unified **Ray Tracing** panel: `scene.eevee.use_raytracing`, plus `scene.eevee.ray_tracing_options` (`resolution_scale`, `screen_trace_quality`, `screen_trace_thickness`, `trace_max_roughness`, `use_denoise`) |
| Shadow maps (cube/cascade) | **Virtual shadow maps**: `scene.eevee.use_shadows`, `shadow_ray_count`, `shadow_step_count`, `use_shadow_jitter_viewport`; per-light `light.use_shadow_jitter`, `light.shadow_filter_radius` |
| No proper AO from ray tracing | GTAO replaced by **horizon-scan / fast GI**; `scene.eevee.fast_gi_method`, `fast_gi_resolution` |
| Motion blur via `scene.eevee.*` | Uses `scene.render.use_motion_blur` / `motion_blur_shutter`, shared with Cycles |
| Light probes: Irradiance Volume / Reflection Cubemap | **Volume / Sphere / Plane** probes; irradiance grids bake differently |
| — | **Shadow/light "Clamp"** settings (`scene.eevee.clamp_surface_direct`, `clamp_surface_indirect`, `clamp_world`) to control fireflies |

EEVEE Next's ray-traced screen-space refraction is genuinely better on a splash than 3.6's, but
it is still screen-space. It does not change the verdict: **Cycles for finals.**

---

## 10. Colour management — the biggest 3.6 → 4.x gotcha in this whole project

### 10.1 The problem, stated up front

> **A tutorial recorded in Blender 3.6 was graded under the *Filmic* view transform.
> Blender 4.0+ defaults to *AgX*. If you build this shot in 4.x with the tutorial's light
> powers and the tutorial's orange backdrop colour, your render WILL NOT look like theirs.**
> It will be flatter, less saturated, and the orange will drift toward pale peach/white in the
> bright areas. Nothing is broken. This is the view transform.

### 10.2 The three transforms

| View Transform | Default in | Character |
|---|---|---|
| **Standard** | never (opt-in) | sRGB, no tone mapping. Highlights **clip hard** to pure white with an ugly hue shift. Only correct for UI/texture output. |
| **Filmic** | **3.6** | Wide-latitude film-like roll-off. Desaturates highlights moderately. Slightly milky, lower contrast; the "Filmic look" people compensate for with a Look. Still available in 4.x. |
| **AgX** | **4.0+** | Much better highlight handling — no hue skew, no magenta clipping on bright lights. Aggressively **desaturates as values approach the top of the range** (that is the point: real film/sensors do this). |
| Khronos PBR Neutral | 4.2+ (opt-in) | Preserves albedo colour accurately; designed for e-commerce product images. **Worth trying for a product shot** — it keeps saturated colours saturated. |
| False Color | any | Diagnostic, see 10.5 |
| Raw | any | No transform at all; for data passes |

### 10.3 Why AgX eats your orange backdrop, and how to compensate

AgX's tone curve pulls chroma toward the achromatic axis as luminance rises. A saturated orange
emission at strength 2.0 is a *bright, highly-chromatic* value — exactly the case AgX is
designed to tame. On screen it becomes a softer, sandier orange rather than the electric
orange of the reference frame.

**Compensations, best first:**

1. **Lower the backdrop's exposure, raise its saturation.** Instead of `emission 3.0` on a
   medium orange, use `emission 1.2` on a *deeply saturated* orange. AgX desaturates by
   luminance, so a darker, richer orange survives.
2. **Use a Look.** `view_settings.look = 'AgX - Punchy'` (4.0) restores contrast and chroma.
   *Punchy* is the closest thing to the 3.6 Filmic-Medium-High-Contrast look people default to.
3. **Just set the view transform back to Filmic** — it is still shipped in 4.x. If your goal
   is to match a 3.6 tutorial frame-for-frame, do this and stop fighting.
4. **Try Khronos PBR Neutral** (4.2+). It is designed exactly for "saturated product against a
   saturated background" and holds the orange far better than AgX.
5. **Grade in comp before the view transform** — a Hue/Saturation node with Saturation 1.15 on
   the render layer, which is scene-referred, so you are boosting chroma *before* AgX sees it.

**A note on Looks and version differences:** in 4.0 the Look enum identifiers carry the
transform name (`'AgX - Punchy'`, `'AgX - Medium High Contrast'`); in 3.6 they are
`'Filmic - Medium High Contrast'` etc.; 4.1+ tidied several of these. **Always set `look`
inside a try/except** — see the preset script in §12.

### 10.4 Exposure and the Look

| Control | RNA | Use |
|---|---|---|
| Exposure | `scene.view_settings.exposure` | Stops of exposure applied **before** the view transform. Use ±0.3 for fine-tuning. **Do not** use it to fix a badly lit scene — fix the lights, or the specular/diffuse relationship goes wrong. |
| Gamma | `scene.view_settings.gamma` | Leave at 1.0. |
| Look | `scene.view_settings.look` | Contrast preset. `'Punchy'`/`'Medium High Contrast'` for a commercial. |
| Use Curves | `scene.view_settings.use_curve_mapping` | A last-resort in-Blender grade. Prefer comp/DaVinci. |
| Sequencer colour space | `scene.sequencer_colorspace_settings.name` | Only matters if you use the VSE |

### 10.5 False Colour — the only objective way to judge exposure

Set **View Transform → False Color**. The image is remapped to a luminance key:

| Colour | Scene-referred value | Meaning |
|---|---|---|
| Black / dark purple | < 0.005 | crushed, no detail |
| Blue | ~0.02 | deep shadow |
| **Green** | **0.18** | **middle grey — where your label should sit** |
| Yellow / orange | 0.5 – 2 | highlights with detail |
| **Red** | ~4–8 | very hot, near the top |
| **White** | > ~16 | clipped, no recoverable detail |

**How to use it on this shot:**
1. Label front face → should be **green** (or green-yellow if you want it bright).
2. Orange backdrop → **just below** the label; blue-green is right, green is too bright.
3. Strip-light speculars on the bottle → **thin** yellow/red lines. If they are **thick white
   bands**, drop strip power — clipped speculars lose the gradient that makes glass look like glass.
4. The splash → mostly yellow with red/white only on the sharpest rims.
5. Anything large and **white** = clipped. Anything large and **black** = a hole in your lighting.

Flip back to Filmic/AgX when you are done. Never render out in False Color.

---

## 11. Output

### 11.1 Never render straight to video

| Reason | Detail |
|---|---|
| **No resume** | A crash at frame 210 of 250 loses the whole file. With an image sequence you restart at 210. |
| **No re-grade** | Video is display-referred, 8-bit, chroma-subsampled and already tone-mapped. You cannot recover a blown specular or shift the orange. |
| **No comp** | Passes (Denoising Data, Vector, Cryptomatte) cannot exist in an MP4. |
| **No render farm / no parallel machines** | Frame ranges can be split across machines only with sequences. |
| **Corruption risk** | One bad write and the container is unplayable. |

**Render to an image sequence, then assemble** in the VSE, comp, or an external NLE.

### 11.2 Format choice

| Format | Bits | Colour space | Size/frame @1080p | Use |
|---|---|---|---|---|
| PNG 8-bit | 8 | display-referred (view transform **baked in**) | ~1–3 MB | Client WIP, contact sheets. Banding risk in the smooth orange gradient. |
| **PNG 16-bit** | 16 | display-referred, baked | ~4–8 MB | **Good default for a finished-look sequence.** No banding on the gradient. What the tutorial's `frame 163` almost certainly is. |
| **OpenEXR half (16-bit float)** | 16f | **scene-referred linear**, view transform **not** baked | ~3–8 MB (DWAA) | **The right answer if you will comp or grade.** Full highlight latitude. |
| OpenEXR full (32-bit float) | 32f | scene-referred linear | ~12–25 MB | Overkill for beauty; use only for Vector/Position/Depth data passes that need precision |
| **Multilayer EXR** | 16f/32f | scene-referred | larger | Beauty + Denoising Data + Vector + Cryptomatte in one file. The professional animation output. |
| JPEG / WebP | 8 | display-referred | small | Previews only |
| FFmpeg MP4/H.264 | 8 | display-referred | — | **Final delivery only, assembled from the sequence** |

**The distinction that matters:** PNG/JPEG **bake the view transform** — what you see is what
is saved, and the extra range above 1.0 is gone forever. EXR float saves **linear
scene-referred** data with the highlights intact; you apply the view transform later in comp.
If there is any chance of grading, **render EXR half**.

**EXR codec:** `image_settings.exr_codec = 'DWAA'` — lossy but visually indistinguishable and
3–8× smaller than ZIP. Use `'ZIP'` (lossless) for data passes, `'PIZ'` for grainy content.

### 11.3 Resolution and the 50 % preview workflow

```python
scn.render.resolution_x = 1920
scn.render.resolution_y = 1080
scn.render.resolution_percentage = 50      # lookdev: 960x540, ~4x faster
# ...final:
scn.render.resolution_percentage = 100
```

`resolution_percentage` is the single fastest lookdev lever — 50 % is **4× fewer pixels**.
Two caveats: (1) noise *looks* lower at 50 % because you are viewing fewer, larger pixels —
do not tune your noise threshold at 50 %; (2) thin splash ligaments alias badly at 50 % and can
appear to break up. DOF, motion blur and lighting all evaluate identically, so it is safe for
everything else.

### 11.4 Frame range and naming

```python
scn.frame_start, scn.frame_end, scn.frame_step = 1, 250, 1
scn.render.filepath = "//render/bev_shot01/bev_"      # -> bev_0001.png ... bev_0250.png
scn.render.use_file_extension = True
scn.render.use_overwrite      = False   # don't redo finished frames
scn.render.use_placeholder    = True    # write a stub first -> lets several machines
                                        #   / instances share one output folder safely
```

- A trailing underscore matters: without it you get `bev0001.png`.
- Explicit padding: `"//render/bev_shot01/bev_####"` forces 4-digit padding wherever you want it.
- **`use_overwrite = False` + `use_placeholder = True`** is how you resume a crashed render and
  how you run two Blender instances on the same sequence.
- Keep every version in its own folder (`bev_shot01_v03/`) — never mix versions in one directory.

```bash
# Headless render of the full range (fastest, no UI overhead)
blender -b scene.blend -E CYCLES -o //render/bev_shot01/bev_ -F PNG -x 1 -s 1 -e 250 -a
# Re-render a single fixed frame
blender -b scene.blend -o //render/bev_shot01/bev_ -F PNG -f 163
```

---

## 12. Render settings presets

### 12.1 The table

| # | Setting | RNA | **(a) FAST LOOK-DEV** | **(b) FINAL BEAUTY** |
|---|---|---|---|---|
| 1 | Engine | `render.engine` | `CYCLES` (or `BLENDER_EEVEE` for blocking) | `CYCLES` |
| 2 | Device | `cycles.device` | `GPU` | `GPU` |
| 3 | Feature Set | `cycles.feature_set` | `SUPPORTED` | `SUPPORTED` |
| 4 | Max Samples | `cycles.samples` | **128** | **1536** |
| 5 | Adaptive Sampling | `cycles.use_adaptive_sampling` | True | True |
| 6 | Noise Threshold | `cycles.adaptive_threshold` | **0.05** | **0.0035** |
| 7 | Min Samples | `cycles.adaptive_min_samples` | 0 | 0 |
| 8 | Time Limit | `cycles.time_limit` | **25 s** | 0 |
| 9 | Animated Seed | `cycles.use_animated_seed` | True | **True** |
| 10 | Light Tree | `cycles.use_light_tree` | True | True |
| 11 | Denoise | `cycles.use_denoising` | True | True (or off + comp) |
| 12 | Denoiser | `cycles.denoiser` | `OPTIX` | **`OPENIMAGEDENOISE`** |
| 13 | Denoise passes | `cycles.denoising_input_passes` | `RGB_ALBEDO_NORMAL` | `RGB_ALBEDO_NORMAL` |
| 14 | Denoise prefilter | `cycles.denoising_prefilter` | `FAST` | **`ACCURATE`** |
| 15 | Total bounces | `cycles.max_bounces` | **12** | **32** |
| 16 | Diffuse | `cycles.diffuse_bounces` | 2 | 4 |
| 17 | Glossy | `cycles.glossy_bounces` | 4 | **10** |
| 18 | **Transmission** | `cycles.transmission_bounces` | **8** | **20** |
| 19 | Volume | `cycles.volume_bounces` | 0 | 2 |
| 20 | Transparent | `cycles.transparent_max_bounces` | 8 | **16** |
| 21 | Clamp Direct | `cycles.sample_clamp_direct` | 0.0 | **0.0** |
| 22 | Clamp Indirect | `cycles.sample_clamp_indirect` | 10.0 | **10.0** |
| 23 | Filter Glossy | `cycles.blur_glossy` | 1.0 | **0.5** |
| 24 | Reflective caustics | `cycles.caustics_reflective` | False | **True** |
| 25 | Refractive caustics | `cycles.caustics_refractive` | False | **True** |
| 26 | Fast GI | `cycles.use_fast_gi` | **True**, `REPLACE`, AO bounces 1 | **False** |
| 27 | Motion Blur | `render.use_motion_blur` | **False** | **True** |
| 28 | Shutter | `render.motion_blur_shutter` | — | **0.5** |
| 29 | MB Position | `cycles.motion_blur_position` | — | `CENTER` |
| 30 | Rolling shutter | `cycles.rolling_shutter_type` | `NONE` | `NONE` |
| 31 | Persistent Data | `render.use_persistent_data` | False | **True** |
| 32 | Auto Tile / size | `cycles.use_auto_tile`, `tile_size` | True / 2048 | True / **2048** (1024 if VRAM-tight) |
| 33 | Simplify | `render.use_simplify` | **True**, subdiv 1, tex limit 2048 | False |
| 34 | Resolution % | `render.resolution_percentage` | **50** | **100** |
| 35 | Resolution | `render.resolution_x/y` | 1920×1080 | 1920×1080 (or 3840×2160) |
| 36 | Film filter width | `render.filter_width` | 1.5 | 1.5 |
| 37 | Film transparent | `render.film_transparent` | False | False |
| 38 | View transform | `view_settings.view_transform` | Filmic (3.6) / AgX (4.x) | same, decided in §10 |
| 39 | Look | `view_settings.look` | `Medium High Contrast` | `Punchy` / `Medium High Contrast` |
| 40 | Format | `image_settings.file_format` | `PNG`, 8-bit | **`OPEN_EXR_MULTILAYER`** 16f DWAA, or PNG 16-bit |
| 41 | Frame range | `frame_start/end` | 150–175 (a test slice) | 1–250 |
| 42 | Approx. time/frame | — | **~8–25 s** | **~2–6 min** @1080p on an RTX-class GPU |

### 12.2 `bpy` — apply either preset

```python
# ============================================================================
# 03_render_presets.py
#   apply_preset("lookdev")   -> fast iteration
#   apply_preset("final")     -> beauty pass
# Blender 3.6 LTS; guarded for 4.0 / 4.2 / 4.5.
# ============================================================================
import bpy

def _set(obj, attr, value):
    """Set only if the property exists on this Blender version."""
    if hasattr(obj, attr):
        try:
            setattr(obj, attr, value)
            return True
        except Exception as e:
            print("  ! could not set %s = %r (%s)" % (attr, value, e))
    else:
        print("  - skipped %s (not in Blender %s)"
              % (attr, ".".join(str(v) for v in bpy.app.version)))
    return False

def setup_gpu(backend='OPTIX'):
    prefs = bpy.context.preferences.addons['cycles'].preferences
    _set(prefs, "compute_device_type", backend)
    try:
        prefs.get_devices()
    except Exception:
        pass
    for d in prefs.devices:
        d.use = (d.type != 'CPU')
    print("GPU backend:", backend,
          "| enabled:", [d.name for d in prefs.devices if d.use])

def set_color_management(match_36_tutorial=False):
    vs = bpy.context.scene.view_settings
    if match_36_tutorial:
        # Reproduce a Blender 3.6 tutorial's look on ANY version.
        for tf in ("Filmic",):
            try:
                vs.view_transform = tf
                break
            except Exception:
                pass
        for lk in ("Filmic - Medium High Contrast", "Medium High Contrast",
                   "AgX - Medium High Contrast", "None"):
            try:
                vs.look = lk
                break
            except Exception:
                continue
    else:
        # Modern default: AgX (4.x) or Filmic (3.6), punchy.
        for tf in ("AgX", "Filmic"):
            try:
                vs.view_transform = tf
                break
            except Exception:
                continue
        for lk in ("AgX - Punchy", "Punchy",
                   "Filmic - Medium High Contrast", "Medium High Contrast", "None"):
            try:
                vs.look = lk
                break
            except Exception:
                continue
    vs.exposure = 0.0
    vs.gamma    = 1.0
    print("View transform:", vs.view_transform, "| Look:", vs.look)

def apply_preset(mode="final", out_dir="//render/bev_shot01/", basename="bev_"):
    scn, r, c = bpy.context.scene, bpy.context.scene.render, bpy.context.scene.cycles
    r.engine = 'CYCLES'
    _set(c, "device", 'GPU')
    _set(c, "feature_set", 'SUPPORTED')
    _set(c, "use_adaptive_sampling", True)
    _set(c, "adaptive_min_samples", 0)
    _set(c, "use_animated_seed", True)
    _set(c, "use_light_tree", True)                      # 3.5+
    _set(c, "use_denoising", True)
    _set(c, "denoising_input_passes", 'RGB_ALBEDO_NORMAL')
    _set(c, "use_auto_tile", True)
    _set(c, "tile_size", 2048)
    _set(c, "pixel_filter_type", 'BLACKMAN_HARRIS')
    _set(r, "filter_width", 1.5)
    _set(r, "film_transparent", False)
    _set(c, "sample_clamp_direct", 0.0)
    _set(c, "sample_clamp_indirect", 10.0)
    _set(c, "rolling_shutter_type", 'NONE')
    _set(c, "motion_blur_position", 'CENTER')
    r.resolution_x, r.resolution_y = 1920, 1080
    r.fps = 25

    if mode == "lookdev":
        _set(c, "samples", 128)
        _set(c, "adaptive_threshold", 0.05)
        _set(c, "time_limit", 25.0)
        _set(c, "denoiser", 'OPTIX')
        _set(c, "denoising_prefilter", 'FAST')
        _set(c, "max_bounces", 12)
        _set(c, "diffuse_bounces", 2)
        _set(c, "glossy_bounces", 4)
        _set(c, "transmission_bounces", 8)
        _set(c, "volume_bounces", 0)
        _set(c, "transparent_max_bounces", 8)
        _set(c, "blur_glossy", 1.0)
        _set(c, "caustics_reflective", False)
        _set(c, "caustics_refractive", False)
        _set(c, "use_fast_gi", True)
        _set(c, "fast_gi_method", 'REPLACE')
        _set(c, "ao_bounces_render", 1)
        _set(r, "use_motion_blur", False)
        _set(r, "use_persistent_data", False)
        _set(r, "use_simplify", True)
        _set(r, "simplify_subdivision", 1)
        _set(c, "texture_limit", '2048')
        r.resolution_percentage = 50
        r.image_settings.file_format = 'PNG'
        r.image_settings.color_mode  = 'RGBA'
        r.image_settings.color_depth = '8'
        r.image_settings.compression = 15
        scn.frame_start, scn.frame_end = 150, 175        # a slice around the hero beat
        r.filepath = out_dir.rstrip('/') + "_LD/" + basename

    elif mode == "final":
        _set(c, "samples", 1536)
        _set(c, "adaptive_threshold", 0.0035)
        _set(c, "time_limit", 0.0)
        _set(c, "denoiser", 'OPENIMAGEDENOISE')
        _set(c, "denoising_prefilter", 'ACCURATE')
        _set(c, "denoising_use_gpu", True)               # 4.0+ only
        _set(c, "max_bounces", 32)
        _set(c, "diffuse_bounces", 4)
        _set(c, "glossy_bounces", 10)
        _set(c, "transmission_bounces", 20)              # <-- the splash setting
        _set(c, "volume_bounces", 2)
        _set(c, "transparent_max_bounces", 16)
        _set(c, "blur_glossy", 0.5)
        _set(c, "caustics_reflective", True)
        _set(c, "caustics_refractive", True)
        _set(c, "use_fast_gi", False)
        _set(r, "use_motion_blur", True)
        _set(r, "motion_blur_shutter", 0.5)              # 180-degree shutter
        _set(r, "use_persistent_data", True)
        _set(r, "use_simplify", False)
        _set(c, "texture_limit_render", 'OFF')
        r.resolution_percentage = 100
        # --- Multilayer EXR (recommended) ---
        r.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
        r.image_settings.color_mode  = 'RGBA'
        r.image_settings.color_depth = '16'              # half float
        _set(r.image_settings, "exr_codec", 'DWAA')
        # --- or 16-bit PNG instead: -------------------
        # r.image_settings.file_format = 'PNG'
        # r.image_settings.color_depth = '16'
        # r.image_settings.compression = 15
        scn.frame_start, scn.frame_end = 1, 250
        r.filepath = out_dir + basename

        # Passes worth having on a final animation:
        vl = bpy.context.view_layer
        _set(vl.cycles, "denoising_store_passes", True)  # re-denoise in comp later
        _set(vl, "use_pass_z", True)
        _set(vl, "use_pass_combined", True)
        # Vector pass is INCOMPATIBLE with render motion blur - only for the
        # comp-blur workflow (see 7.5):
        # r.use_motion_blur = False; vl.use_pass_vector = True
    else:
        raise ValueError("mode must be 'lookdev' or 'final'")

    r.use_file_extension = True
    r.use_overwrite      = False
    r.use_placeholder    = True
    print("Applied preset:", mode, "->", r.filepath)

# ---------------------------------------------------------------------------
setup_gpu('OPTIX')                 # 'CUDA' | 'HIP' | 'METAL' | 'ONEAPI'
set_color_management(match_36_tutorial=False)
apply_preset("final")
```

---

## 13. Troubleshooting

### 13.1 The splash renders dark / grey / black instead of silver-white

| Cause | Fix |
|---|---|
| **Nothing bright for it to reflect** (most common) | Add the big white emission cards of §1.6, or an HDRI at 0.5–1.0. Water has no diffuse colour: it can only show you what surrounds it. |
| **Transmission bounces exhausted** | Raise `transmission_bounces` to 16–24. Black *patches* with hard edges = this, every time. |
| Water card visibility misconfigured | If you turned Glossy/Transmission visibility off on the cards along with Diffuse, the water can't see them. Only Diffuse + Camera should be off. |
| Backdrop too bright relative to the water cards | The splash is dark **by comparison**. Raise card emission to 6–8 or drop backdrop emission. |
| Normals flipped / non-manifold fluid mesh | The IOR interface is inverted; the shader reads as opaque. Recalculate normals; check *Use Fractions* on the domain. |
| Material IOR / roughness | Out of scope here, but if the *whole* splash is uniformly grey and lighting changes do nothing, it's the shader, not the rig. |
| Light Linking excluded it (4.x) | Check the water objects are actually in the receiver collection. |

### 13.2 Fireflies in the water

In priority order:
1. **`adaptive_threshold` 0.0035 + `samples` 1536.** Most "fireflies" are just under-sampling.
2. **Filter Glossy `blur_glossy = 0.5`.**
3. **Enlarge small bright sources.** A 0.02 m light focused by a droplet is a firefly factory;
   the same power in a 0.12 m strip is not.
4. **`sample_clamp_indirect = 10`** (default). Lower to 5 only if desperate.
5. **Never `sample_clamp_direct`** — it kills the strip-light highlights that define the shot.
6. Turn off **Reflective/Refractive caustics** for a lookdev pass to confirm the fireflies are
   caustics; if they are, decide whether you want them (they're pretty) or not.
7. `light.cycles.max_bounces = 0` on the strips: removes their entire indirect contribution
   and with it a whole class of firefly paths.
8. Check for a stray tiny emissive face in the fluid or a mesh light hidden inside geometry.

### 13.3 Noisy / blotchy caustics under the bottle

- Caustics are the hardest paths to sample. Brute force: samples up, threshold down.
- **Filter Glossy 0.5–1.0** blurs them cheaply — usually invisible and hugely effective.
- Try **Shadow Caustics (MNEE)** with a *small* dedicated light (§2.5) instead of brute force.
- Make the light physically larger — a bigger source produces a softer, lower-variance caustic.
- Last resort: `caustics_refractive = False` and paint the amber pool with a spot light
  carrying a gradient texture. This is what many commercial artists actually ship.

### 13.4 DOF is destroying the splash detail

- Stop down: **f/4 → f/5.6 or f/8**. See the DOF table in §5.4.
- **Move the camera back and use a longer lens** to keep the same framing with more depth:
  135 mm at 2.7 m has slightly *less* DOF than 100 mm at 2.0 m for the same framing, so go the
  other way — **85 mm at 1.7 m** gives noticeably more depth at the same f-stop and framing.
- Put the focus target on the *splash crown* rather than the label for the splash-impact
  frames, and keyframe it back to the label after.
- Do a **DOF-off render + Z pass** and defocus in comp for the client WIP; real DOF for finals.
- Raise samples: defocused bright speculars need *far* more samples than sharp ones. A DOF
  render at the same threshold takes ~1.5–2× longer for the same visual noise.

### 13.5 Render times exploding

Diagnose in this order:

| Check | Typical culprit |
|---|---|
| Turn off motion blur → time drops >40 % | Deformation motion blur on the fluid mesh; reduce `motion_steps` to 1, or use Vector-pass blur for WIP |
| Turn off DOF → time drops >30 % | Aperture too wide for the sample count; stop down or raise samples/threshold together |
| Set `transmission_bounces` to 4 → time drops a lot | You over-raised it; find the minimum that removes black, not a round number like 64 |
| Disable caustics → big drop | Caustic paths; use Filter Glossy or MNEE |
| Enable **Persistent Data** → big drop between frames | You forgot it. This is often the single largest animation win. |
| Volume shaders present | `volume_bounces`, volume step size — volumetrics in a splash are brutally expensive |
| HDRI at 8K/16K | Downsize to 2K–4K; an env map that doesn't fill the frame doesn't need 16K |
| `use_fast_gi` for WIP | 20–40 % off lookdev frames |
| Adaptive threshold too low | 0.0035 → 0.005 is usually invisible and 25–35 % faster |

### 13.6 Out of VRAM on a big fluid mesh

Symptom: `CUDA error: out of memory` / `System is out of GPU memory`, usually mid-sequence when
the splash peaks.

| Fix | Cost |
|---|---|
| **Lower Domain Resolution Divisions** (e.g. 256 → 192) or **Mesh Upres Factor** | Less detail, but a 25 % resolution drop is ~2× fewer mesh triangles |
| Raise **Mesh → Particle Radius**, lower **Concavity Upper/Lower** | Coarser but far lighter mesh |
| `cycles.tile_size` 2048 → **1024 or 512** | Slightly slower; big peak-VRAM saving |
| Turn **Persistent Data OFF** | Slower per frame, but frees the resident BVH |
| `ob.cycles.motion_steps = 1` on the fluid | Motion blur memory scales with steps |
| **Simplify → Texture Limit (render)** 4096/2048 | Reduces texture VRAM |
| Turn off `use_deform_motion` on non-deforming objects | |
| Disable motion blur on the backdrop/cards | |
| Reduce HDRI resolution | Env maps live in VRAM |
| Hide off-camera geometry entirely (`ob.hide_render = True`) | The cards are camera-invisible but still resident; delete unused ones |
| Fall back to **CPU** for the worst frames, or render those frames on a bigger GPU | Slow but it finishes |
| NVIDIA only: system-memory fallback lets CUDA/OptiX spill to host RAM — **massively** slower but avoids an outright failure. Verify it's active rather than relying on it. | |

### 13.7 Quick symptom index

| You see | Go to |
|---|---|
| Splash is sharp and strobes | §7.4 — Speed Vectors |
| Black core inside the bottle | §8.4 — transmission bounces |
| Splash shadow is solid black | §8.4 — `transparent_max_bounces` |
| Bright rectangle floating in the backdrop | §2.4 — object camera visibility on a light/card |
| Orange looks pale/sandy vs the tutorial | §10.3 — AgX vs Filmic |
| Whole image milky and low contrast | §4.2 — backdrop emission too high, or Filmic without a Look |
| Vertical bottle edges converge | §5.1 — focal length too short |
| Noise "boils" between frames | §8.3 — denoiser temporal instability |
| Reflections vanish at the frame edge | §9.2 — you're in EEVEE; screen-space limitation |
| Light changes brightness when you scale it (4.5) | `light.normalize` |

---

## 14. Version-difference quick reference

| Topic | 3.6 LTS | 4.0 | 4.2 LTS | 4.5 |
|---|---|---|---|---|
| Default view transform | **Filmic** | **AgX** | AgX (+ Khronos PBR Neutral available) | AgX |
| Look identifiers | `Filmic - Medium High Contrast` | `AgX - Punchy` etc. | tidied names | tidied names |
| **Light Linking** | ✗ | **✓** `ob.light_linking.receiver_collection` / `.blocker_collection` | ✓ | ✓ |
| Light Groups | ✓ (3.2+) | ✓ | ✓ | ✓ |
| Light Tree | ✓ (3.5+) | ✓ | ✓ | ✓ |
| Shadow Caustics / MNEE | ✓ (3.4+) | ✓ | ✓ | ✓ |
| `cycles.denoising_use_gpu` | ✗ | **✓** | ✓ | ✓ |
| Per-light `use_shadow` | ✗ | ✗ | **✓** | ✓ |
| `light.normalize` | ✗ | ✗ | ✗ | **✓** |
| EEVEE | legacy (`use_ssr`, `use_bloom`, `use_gtao`) | legacy | **EEVEE Next** — `use_raytracing`, `ray_tracing_options`, virtual shadow maps, **no `use_bloom`** | EEVEE Next |
| EEVEE motion blur RNA | `scene.eevee.use_motion_blur` | same | `scene.render.use_motion_blur` | `scene.render.use_motion_blur` |
| Principled BSDF | v1 | **v2 (rewritten)** — affects glass/water look-dev, not this module | v2 | v2 |

**Rule for any script in this module:** wrap every write in the `_set()` helper from §12.2 so a
renamed or removed property prints a warning instead of aborting the whole script.

---

## 15. Build order checklist

```
[ ] 1. Scene units metric, scale 1.0; bottle 0.25 m at origin, base on z=0
[ ] 2. Run 03_render_presets.py -> apply_preset("lookdev"); set colour management NOW
        (decide Filmic-match vs AgX before you judge a single light)
[ ] 3. Run 03_camera.py -> 100 mm, f/4, FOCUS_TGT at (0,0,0.14), CAM_PIVOT
[ ] 4. Backdrop emission only. Set its level with False Color. (~1.8)
[ ] 5. Run 03_light_rig.py. Then solo each light: kicker -> key -> strips -> top -> cards
[ ] 6. Check False Color: label green, backdrop just below, speculars thin yellow/red
[ ] 7. Fluid domain: Mesh ON, Speed Vectors ON, RE-BAKE the mesh
[ ] 8. Object motion blur on the fluid: use_motion_blur + use_deform_motion, steps 1
[ ] 9. Run 03_camera_anim.py; scrub the whole 250 frames in EEVEE for framing/timing
[ ] 10. Test-render frames 150-175 at 50%, lookdev preset. Fix black patches (transmission).
[ ] 11. apply_preset("final"); render frames 160-166 at 100% and inspect at 1:1
[ ] 12. Full range to EXR/PNG sequence, use_overwrite=False + use_placeholder=True
[ ] 13. Assemble the sequence to video LAST, never render straight to MP4
```
