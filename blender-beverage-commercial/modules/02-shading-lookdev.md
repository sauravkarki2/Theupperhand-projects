# Module 02 — Shading & Look-Dev

**Beverage commercial / hero product splash. Blender 3.6 LTS baseline, with 4.x deltas flagged inline.**

Source shot being reconstructed: an amber PET soda bottle standing upright, wrapped in a colourless crown-splash water ribbon, green lime/apple slices and whole green fruit flying past, airborne micro-droplets, on a seamless saturated orange→amber backdrop. Native Mantaflow FLIP liquid, Cycles, rendered to a PNG sequence.

This module owns **materials, shaders, texturing and look-dev only**. Simulation, lighting rigs, camera and comp live in their own modules — but shading decisions constantly leak into lighting, so where that happens it is called out explicitly.

---

## 0. The look-dev thesis (read this first)

A beverage ad is not a realism exercise. It is a **contrast machine**. Everything in the frame exists to make one object — the bottle — the brightest, sharpest, most saturated thing on screen.

Four rules drive every shader decision in this module:

1. **The splash is a light-transport object, not a colour object.** It has almost no albedo. Everything you see in it is refracted backdrop, reflected key light, and edge Fresnel. So the way you make the splash look good is by fixing *light paths and the environment*, not by tweaking the water's own colour.
2. **Colourless water reads brightest.** Against a saturated orange field, a tinted or absorbing splash goes muddy brown. Keep the splash near-neutral so its thick rims pick up orange, its thin sheets go white, and it separates from the background as silver.
3. **Wet beats clean.** The single biggest "this looks like an ad" upgrade is not the splash — it is that every surface (bottle, cap, fruit, label) carries a coat layer, roughness break-up, and residual droplets. Dry hero product looks like a CAD render.
4. **Look-dev is bounce, not just BSDFs.** The orange backdrop *lighting the product* is what integrates the shot. An emissive backdrop mesh does that for free; a world-shader gradient does not. This decides section 8 for you.

**Render setting prerequisites** — none of the shaders below behave correctly until these are set. Do this before you judge any material:

| Setting | Location | Value | Why |
|---|---|---|---|
| Max Bounces (Total) | Render > Light Paths | 32 | Splash sheets stack many interfaces |
| Transmission | Render > Light Paths | 24–32 | The single most important number in the file |
| Transparent | Render > Light Paths | 16 | Alpha-cut label art, transparent shadows |
| Filter Glossy | Render > Light Paths | 0.5–1.0 | Kills caustic fireflies, softens sharp glossy |
| Caustics Reflective/Refractive | Render > Light Paths > Caustics | ON for hero, OFF for turntables | Off = flat dead shadows |
| Clamp Indirect | Render > Light Paths > Clamping | 8–10 (never 0.1) | Clamping low murders splash sparkle |
| Blue-noise / Scrambling Distance | Render > Sampling > Advanced | on | Cheaper clean-up on glass |
| View Transform | Render > Colour Management | 3.6: Filmic. 4.x: AgX | See §9.3 — this changes your backdrop hex values |

---

## 1. The water / splash shader

This is the material the shot lives or dies on. Budget more look-dev time here than on everything else combined.

### 1.1 Glass BSDF vs Principled BSDF (Transmission 1.0)

They are not equivalent, and the difference matters for a splash.

| | Glass BSDF | Principled, Transmission 1.0 |
|---|---|---|
| Lobes | one dielectric refraction+reflection lobe | full layered stack: diffuse, specular, sheen, coat, transmission |
| Cost per bounce | cheapest | ~15–30% heavier |
| Shadow behaviour | fully transparent to shadow rays via refraction only | same, but the extra lobes add sampling noise |
| Extra controls | none but colour/roughness/IOR | coat, sheen, thin-film, absorption via base colour, emission |
| Noise on thin sheets | lower | higher |

**Recommendation for this shot:**

- **Splash / FLIP liquid mesh → Glass BSDF.** It is the cheapest, cleanest, least noisy option, and the splash needs zero of Principled's extra lobes. Millions of thin, chaotic faces × extra lobes = render time you will never get back.
- **Bottle plastic and liquid inside the bottle → Principled.** Those need coat, slight roughness, tint, and a metallic/label mix, so the layered stack earns its cost.

The one reason to use Principled on the splash: you want the **Coat** layer to add a second, tighter specular highlight on the rims so the splash sparkles harder under a strip light. It is a real look. It is also expensive. If you want it, do it via a *separate* Glass + Glossy add rather than switching the whole splash to Principled (see §1.6).

### 1.2 The physically correct baseline

```
Glass BSDF
  Color      = (1.0, 1.0, 1.0)   pure white — see 1.4
  Roughness  = 0.0
  IOR        = 1.33
→ Material Output (Surface)
```

That is the whole material. Water at 20 °C is IOR 1.333. Roughness 0.0 is correct — real water surfaces are optically smooth; the "roughness" you perceive in a splash is *geometric* (bubbles, sub-droplet detail, sheet curvature), not microfacet. If your splash looks too sharp, add geometry detail or motion blur, do **not** raise roughness. Roughness > 0.05 on a splash turns it into frosted glass and instantly reads as CG.

Note: `Settings > Shadow Mode` is an **EEVEE-only** panel — it does nothing in Cycles. In Cycles, leave shadows on and let refraction handle it; if the splash casts an ugly black blob, that is the transmission-bounce problem in §1.3, not a shadow setting.

### 1.3 Why a Glass splash renders BLACK (and every fix)

This is *the* failure everyone hits with a Mantaflow splash, and it has six independent causes. Diagnose in this order.

**Cause A — ray budget exhaustion (90% of cases).**
A crown splash is not one glass surface. A single camera ray crossing a splash rim can hit 10–20 glass interfaces (enter sheet, exit sheet, enter droplet, exit droplet, enter main body…). When a ray exceeds **Transmission bounces**, Cycles terminates it and returns **black**. Default Transmission in 3.6 is 12 — nowhere near enough.

Fix: `Render > Light Paths > Max Bounces`:
- Transmission: **24** minimum, **32** for a thick crown splash.
- Total: **32–48** (Total is a hard cap; if Total < Transmission, Total wins).
- Glossy: 4–8 is fine.
- Volume: 0 unless you are actually using Volume Absorption (§1.5) — then 2–4.

Verification trick: render a test frame with Transmission = 4, then 12, then 32. If black regions shrink each time, this was your problem. If they do not change, go to cause B.

**Cause B — flipped / inconsistent normals on the fluid mesh.**
Mantaflow usually outputs correct normals, but after any mesh op (remesh, decimate, boolean, imported Alembic with a negative scale) you can get inverted faces. A glass surface with a backwards normal makes Cycles think the ray is *leaving* a medium it never entered, and total internal reflection swallows it.

Fix: select the fluid mesh, Edit Mode > `A` > `Shift+N` (Recalculate Outside). For a cached/animated mesh you cannot edit, add a **Normal Edit** or just check `Object > Normals > Auto Smooth` and enable **Overlays > Face Orientation** to see red faces. Also check the object has **no negative scale** (`Ctrl+A > Scale`).

**Cause C — the object is inside another closed transmissive volume.**
If your splash mesh is intersecting the bottle's glass/plastic and both are solid (non-thin) transmissive, Cycles nests IORs and the interface maths goes wrong — you get black seams exactly where they interpenetrate. Same class of bug as §3.2's liquid-mesh rule.

Fix: make sure the splash does not co-planar-intersect the bottle wall. A 0.2–0.5 mm gap is enough. Or make the bottle **thin-walled** (Principled with no interior volume, see §3.1).

**Cause D — Clamp Indirect set too low.**
Clamping at 0.5 or 1.0 (a common "kill the fireflies" reflex) removes exactly the high-energy specular events that make a splash sparkle, leaving a dull grey blob that reads as "muddy" rather than black.

Fix: Clamp Indirect **8–10**, or 0 (off) plus Filter Glossy 1.0 and more samples. Never clamp below ~4 on a splash shot.

**Cause E — the splash has nothing to refract.**
Glass is a mirror for its environment. If your world is dark grey and there is no visible backdrop behind the splash from the splash's point of view, refracted rays go looking for light and find nothing. The render is *correctly* black.

Fix: this is a lighting fix. The emissive backdrop from §8 solves it. Rule of thumb: a splash needs a **big bright thing behind and above it**. In a beverage ad that is typically a large soft top light plus the backdrop itself.

**Cause F — you are in EEVEE and forgot Screen Space Refraction.** See §1.8.

### 1.4 Fixes that trade physics for speed and cleanliness

Once the black is gone you will still be fighting **noise** and **render time**. These are the standard production cheats, in ascending order of how much they lie.

**Cheat 1 — Filter Glossy.**
`Render > Light Paths > Filter Glossy = 1.0`. Blurs sharp glossy/caustic paths as ray depth increases. Costs almost nothing, removes most white fireflies from droplets. Always on for a splash. 0.5 for a hero close-up, 1.0–2.0 for wide/motion-blurred frames where nobody can see the softening.

**Cheat 2 — the "IOR 1.1" cheat.**
Lower the IOR from 1.33 to **1.1–1.2**. Lower IOR bends rays less, which means:
- fewer total-internal-reflection events → fewer black paths,
- shorter average path length → faster render,
- less extreme lensing → the backdrop reads through the splash instead of scrambling into noise.

Cost: the splash looks thinner and less "watery" — glass magnification of whatever is behind it collapses. It is a great cheat for a **thin, fast, motion-blurred splash** and a bad one for a **slow hero pour** where you want the lens effect. Practical range for ads: 1.20–1.33. Below 1.1 it stops reading as liquid.

The reverse is also useful: on a static hero glass, push IOR to **1.45** to exaggerate the lensing and get that thick, expensive-looking distortion.

**Cheat 3 — Refraction BSDF instead of Glass BSDF.**
`Refraction BSDF (Beckmann/GGX, IOR 1.33)` is Glass with the *reflection* lobe removed. Half the path branching, dramatically less noise, much faster. The splash loses its bright rim reflections, so it goes dull.

The good version is to **rebuild Glass manually** so you control the mix:

```
Fresnel (IOR 1.33) ─┐
Glossy BSDF (Rough 0.0) ──→ Mix Shader (Fac = Fresnel) ─→ Material Output
Refraction BSDF (Rough 0.0, IOR 1.33) ─┘
        (Refraction into the *bottom* / first socket, Glossy into the second)
```

This is mathematically what Glass BSDF does, but now you can cheat each half: drop the Refraction IOR to 1.15 for speed while keeping the Fresnel node at 1.33 so the rim reflections still look right. That combination — **correct-looking Fresnel, cheap refraction** — is the single best quality/speed trade for a big splash.

**Cheat 4 — Glass + Transparent by ray type (the fake-glass rig).**
Swap in a cheap shader for rays the viewer cannot scrutinise.

```
Light Path ─ (Is Shadow Ray) ──────────────┐
Glass BSDF (IOR 1.33, Rough 0.0) ──────────→ Mix Shader ─→ Material Output
Transparent BSDF (white) ──────────────────┘
```
Wiring: `Is Shadow Ray` → Mix `Fac`; Glass into socket 1, Transparent into socket 2. Result: the splash still refracts to camera, but casts a **clean transparent shadow** instead of a black one. This is how you stop a splash from dropping a dead black silhouette on the backdrop when you have not got caustics working.

Extend it with `Is Camera Ray` to use full Glass only on primary rays and a cheap Transparent or low-IOR Refraction on secondary bounces:

```
Light Path (Is Camera Ray) → Mix Shader.Fac
  socket 1: Refraction BSDF (IOR 1.1)      # what other rays see
  socket 2: Glass BSDF (IOR 1.33)          # what the camera sees
```
Can cut splash render time 30–50%. Breaks reflections-of-reflections; nobody notices in a 24 fps ad.

You can also use `Ray Depth` → `Math (Greater Than, 3)` → Mix to Transparent, which hard-terminates deep paths into "just let the background through" rather than into black. This is the most direct anti-black fix of all, and looks better than raising bounces to 64.

**Cheat 5 — Transparent Shadows.**
In Cycles, material `Settings > Transparent Shadows` should be **on** for the splash (it is by default). Off gives you opaque black shadows.

### 1.5 Volume Absorption — tint, and why you mostly should not

Real water absorbs red light; a 2 m tank is cyan, a 3 cm splash is optically colourless. To tint:

```
Glass BSDF ──→ Material Output (Surface)
Volume Absorption (Color = (0.75, 0.92, 1.0), Density = 2.0) ──→ Material Output (Volume)
```

Notes that matter:
- Absorption **Color is the colour that survives**, not the colour removed. A cyan-tinted colour with density 2 gives a subtle blue-green in the thick parts.
- Density is per Blender unit. A splash at real-world scale (bottle ≈ 0.25 m) needs density **1–5** to be visible at all. If you scaled your sim up, density must scale down.
- Volume Absorption only works on **closed manifold** geometry. Mantaflow sheets that are thin and open will show absorption inconsistently or not at all — this is the main practical reason the splash stays colourless.
- Requires Volume bounces ≥ 2 in Light Paths and is a real render-time cost.

**For this shot: skip it on the splash.** The reference frame has a colourless white/silver splash precisely because the backdrop is saturated orange. A tinted splash would go brown where it is thick. Save Volume Absorption for §3.3 where it is doing the real work — the amber liquid inside the bottle.

If you want *any* splash tint, the cheap version is to put a very slight cool colour into the **Glass BSDF Color** input, e.g. `(0.92, 0.97, 1.0)`. That tints per-interface rather than per-distance, so it is physically wrong but stable on thin sheets and costs nothing.

### 1.6 Dispersion, thin film, iridescence

**Dispersion** (IOR varying with wavelength → rainbow fringing on refracted edges).
- **Blender 4.5+**: Glass BSDF and Refraction BSDF have a native **Dispersion** input. Values 0.02–0.05 are plausible for water; 0.1+ is jewellery.
- **3.6 / 4.0–4.4**: no native support. Fake it with three Glass BSDFs at IOR 1.330 / 1.333 / 1.336, each fed through a `Combine Color`-masked path, or the standard node group: three Glass shaders → `Add Shader` chain, each multiplied by a pure R/G/B `Emission`-free mask using `Mix Color (Multiply)` on the Glass `Color` input set to (1,0,0), (0,1,0), (0,0,1). Triples your glass cost.

Water's dispersion is genuinely tiny. On a splash it is invisible; on a **thick, slow, hero pour into a glass** you will see it on rim edges. **Verdict: not worth it for this shot.** Add it in comp instead — a chromatic-aberration node on the splash's cryptomatte reads identically to the audience for 0% render cost.

**Thin film / iridescence** (soap-bubble colour on very thin sheets).
- **Blender 4.2+**: Principled BSDF has `Thin Film Thickness` (nm) and `Thin Film IOR`. Thickness 300–800 nm, IOR 1.33 gives a bubble look. Requires Principled, so you pay the layered-stack cost on the splash.
- **3.6**: fake with `Layer Weight (Facing) → ColorRamp (rainbow stops) → Glass Color` or add a weak `Emission` through a Fresnel mask.

Real water films this thin only exist in bubble/foam. **Verdict: only use it on a deliberate soap/foam pass, or dialled to ~5% as an edge tint to make thin sheets shimmer.** At full strength it reads as "soap advert", not "soda advert".

### 1.7 Cycles 4.x Principled v2 — translating the 3.6 setup

If you are on 4.0+ the Principled BSDF was rebuilt. Anything below that touches Principled needs socket-name translation. The **Glass BSDF is unchanged**, which is another reason to use it on the splash.

| 3.6 socket | 4.x socket | Behaviour change |
|---|---|---|
| `Transmission` (0–1 blend) | `Transmission Weight` | Now a proper **layer weight**, not a blend to a separate lobe. At 1.0 the base diffuse is fully replaced. Values in the middle behave differently — a 0.5 in 3.6 is *not* a 0.5 in 4.x. |
| `Transmission Roughness` | **removed** | Transmission now shares the main `Roughness`. If your 3.6 material used separate values, pick one. |
| `Specular` | `Specular IOR Level` | Still 0–1, default 0.5 = IOR 1.45. It now *modulates* the IOR-derived specular rather than defining it. Leave at 0.5 unless art-directing. |
| `Specular Tint` (float) | `Specular Tint` (**Color**) | Was a 0–1 float, now RGB. A 3.6 value of 0.0 maps to white (1,1,1) in 4.x, **not** black. Auto-converted files usually get this right; hand-built scripts do not. |
| `Clearcoat` | `Coat Weight` | Same idea, better model. Also new: `Coat Roughness`, `Coat IOR` (default 1.5), `Coat Tint`, `Coat Normal`. |
| `Sheen` | `Sheen Weight` | New microfibre model; also `Sheen Roughness`. |
| `Subsurface` | `Subsurface Weight` | Radius is now multiplied by the new **`Subsurface Scale`** — this is the one that silently breaks fruit materials on upgrade (§7). |
| `Subsurface Color` | **removed** | SSS colour now comes from `Base Color`. |
| `Emission` | `Emission Color` | Renamed only. |
| `IOR` | `IOR` | Default changed 1.45 → **1.5**. |
| — | `Thin Film Thickness`, `Thin Film IOR` | New in 4.2. |

**Script-safety pattern.** Never hard-code a socket name if the file may open in either version:

```python
def sock(node, *names):
    """Return the first input socket that exists, by name. 3.6/4.x safe."""
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    raise KeyError(f"none of {names} on {node.bl_idname}")

sock(bsdf, "Transmission Weight", "Transmission").default_value = 1.0
sock(bsdf, "Coat Weight", "Clearcoat").default_value      = 0.4
sock(bsdf, "Subsurface Weight", "Subsurface").default_value = 0.6
```

Every script in this module uses that helper.

### 1.8 EEVEE equivalent (and why you probably will not ship it)

You will still want EEVEE for **previz, sim review, and playblasts**, so the splash needs an EEVEE-viable version even if the final is Cycles.

**EEVEE Legacy (3.6):**
1. `Render Properties > Screen Space Reflections` → **enable**, then tick its **Refraction** sub-checkbox. Nothing refracts until this is on.
2. Material > `Settings > Screen Space Refraction` → **enable** (per material).
3. Material > `Settings > Blend Mode` = **Alpha Blend** (or Alpha Hashed for correct-ish sorting), `Shadow Mode` = **Alpha Hashed** or None.
4. Material > `Settings > Refraction Depth` — this is EEVEE's fake for object thickness. Set it to roughly the average thickness of your splash sheets (e.g. **0.005 m**). 0.0 means "infinitely thin". Getting this wrong is why EEVEE water looks like a soap bubble.
5. Turn **Show Backface** off (Settings > Show Backface) so you do not see interior faces through the surface.

**Compromises, unavoidable:** screen-space refraction can only refract what is **already on screen**. Anything outside the frame, or hidden behind the splash itself, simply is not there — so the edges of your splash will smear or go flat, and the bottle behind the splash may vanish. There are **no self-refractions** (a splash cannot refract itself), no real caustics, and no correct multi-interface stacking. Which is to say: EEVEE cannot render this shot properly. It can preview it.

**EEVEE Next (4.2+):** substantially better but still screen-space at heart.
- `Screen Space Refraction` is now **`Raytraced Transmission`** in material settings (`mat.use_raytrace_refraction` in Python).
- Blend Mode is replaced by **Render Method: Dithered / Blended**. Use **Dithered** for the splash — it supports raytraced transmission and correct depth; Blended does not.
- Enable `Render Properties > Raytracing`. Set **Screen Tracing** + a decent **Resolution** (1:1 for finals). Enable the **Fast GI Approximation** fallback so off-screen rays get *something*.
- New **Thickness** handling: material `Settings > Thickness` plus the **Thickness** input in the shader replaces Refraction Depth. `Thickness from Shadow` sampling gives surprisingly good automatic thickness on a fluid mesh — turn it on for the splash.
- Add a **Volume Probe** (formerly Irradiance Volume) and a **Sphere Probe** around the product; without probes, off-screen refraction/reflection falls back to the world and the splash goes flat orange.

Even at its best, EEVEE Next splash ≈ 80% of the read at 5% of the render time. Use it to lock the animation, then switch to Cycles for the beauty.

### 1.9 bpy — the splash material

```python
import bpy

def sock(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    raise KeyError(names)

def make_splash_water(name="M_Water_Splash", ior=1.33, cheat_ior=None,
                      transparent_shadow=True, tint=(1.0, 1.0, 1.0, 1.0)):
    """Glass splash with optional shadow-ray transparency cheat.
    cheat_ior: if set, secondary (non-camera) rays use a cheaper low-IOR
               Refraction BSDF instead of full Glass."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out   = nt.nodes.new("ShaderNodeOutputMaterial"); out.location   = (600, 0)
    glass = nt.nodes.new("ShaderNodeBsdfGlass");      glass.location = (0, 100)
    glass.inputs["Color"].default_value     = tint
    glass.inputs["Roughness"].default_value = 0.0
    glass.inputs["IOR"].default_value       = ior
    # Blender 4.5+ only:
    if "Dispersion" in glass.inputs:
        glass.inputs["Dispersion"].default_value = 0.0   # raise to 0.03 for fringing

    surface = glass.outputs["BSDF"]

    if cheat_ior:
        refr = nt.nodes.new("ShaderNodeBsdfRefraction"); refr.location = (0, -160)
        refr.inputs["Roughness"].default_value = 0.0
        refr.inputs["IOR"].default_value       = cheat_ior
        lp   = nt.nodes.new("ShaderNodeLightPath"); lp.location = (0, 380)
        mixc = nt.nodes.new("ShaderNodeMixShader"); mixc.location = (300, -60)
        nt.links.new(lp.outputs["Is Camera Ray"], mixc.inputs["Fac"])
        nt.links.new(refr.outputs["BSDF"],  mixc.inputs[1])   # Fac = 0 -> cheap
        nt.links.new(glass.outputs["BSDF"], mixc.inputs[2])   # Fac = 1 -> full
        surface = mixc.outputs["Shader"]

    if transparent_shadow:
        lp2  = nt.nodes.new("ShaderNodeLightPath");   lp2.location  = (300, 400)
        tr   = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.location = (300, 200)
        mixs = nt.nodes.new("ShaderNodeMixShader");   mixs.location = (450, 0)
        nt.links.new(lp2.outputs["Is Shadow Ray"], mixs.inputs["Fac"])
        nt.links.new(surface,               mixs.inputs[1])
        nt.links.new(tr.outputs["BSDF"],    mixs.inputs[2])
        surface = mixs.outputs["Shader"]

    nt.links.new(surface, out.inputs["Surface"])

    # EEVEE-side settings so previews are not garbage
    try:                       # 4.2+ EEVEE Next
        mat.use_raytrace_refraction = True
        mat.render_method = 'DITHERED'
    except AttributeError:     # 3.6 EEVEE Legacy
        mat.use_screen_refraction = True
        mat.blend_method = 'HASHED'
        mat.shadow_method = 'HASHED'
        mat.refraction_depth = 0.005
    mat.use_backface_culling = False
    return mat


def set_splash_render_settings(scene=None):
    s = scene or bpy.context.scene
    s.render.engine = 'CYCLES'
    c = s.cycles
    c.max_bounces          = 32
    c.transmission_bounces = 24
    c.glossy_bounces       = 8
    c.diffuse_bounces      = 4
    c.transparent_max_bounces = 16
    c.volume_bounces       = 2
    c.blur_glossy          = 1.0     # Filter Glossy
    c.sample_clamp_indirect = 8.0
    c.caustics_reflective  = True
    c.caustics_refractive  = True

# usage
set_splash_render_settings()
mat = make_splash_water(cheat_ior=1.15)
obj = bpy.data.objects.get("liquid_domain_mesh") or bpy.context.object
if obj:
    obj.data.materials.clear()
    obj.data.materials.append(mat)
```

---

## 2. Caustics

### 2.1 Why beverage ads live on caustics

Look at any real drinks photograph: the pool of light under the glass, the bright kidney-shaped smear the liquid throws onto the table, the ribbons of light dancing inside the bottle's shadow. That is caustics — light focused by a curved refractive surface. It is the visual signature of "there is real liquid here". Without it, glass and water render as grey holes with black shadows, and no amount of splash detail rescues the shot.

There are three ways to get them, in ascending order of reliability and descending order of physical honesty.

### 2.2 Brute-force path-traced caustics (Cycles default)

Cycles' path tracer *can* find caustic paths: `Render > Light Paths > Caustics > Reflective / Refractive` (both on by default).

Why it barely works: a caustic path is Light → Specular → Diffuse → Camera (an "SDS"-adjacent path). Bidirectional path tracers handle these; Cycles' unidirectional integrator can only find them by *randomly* hitting the light through a refractive surface. The probability is tiny, so the estimator variance is enormous — you get **white fireflies**, not caustics. Cranking samples from 512 to 8192 barely helps; the noise falls as 1/√N against an enormous variance.

Practical brute-force settings if you insist:
- Light size **large** (a big area light produces softer, findable caustics; a tiny point light produces the sharpest and noisiest).
- `Filter Glossy` 1.0–2.0 — blurs the caustic paths, which is exactly what you want here.
- `Clamp Indirect` 10 — clips the worst fireflies without killing the effect.
- Denoise, but be aware caustics are the first thing OIDN smears into mush. Render a separate **caustics-only light group** and denoise it gently.

### 2.3 Cycles Shadow Caustics (MNEE) — the real feature

Blender 3.2+ ships **Shadow Caustics**, powered by **Manifold Next Event Estimation**. Instead of randomly hoping to find a light through glass, MNEE *solves* for the refracted path that connects a shadowed receiver point to the light — a deterministic, near-noise-free caustic.

Setup is three flags and they must all be set:

1. **Light** — select the light, `Object Data Properties > Light > Shadow Caustics` → **on**. (Python: `light_obj.data.cycles.is_caustics_light = True`.)
2. **Caster** — the refractive object (bottle glass, liquid, splash): `Object Properties > Shading > Caustics > Cast Shadow Caustics` → **on**. (Python: `obj.is_caustics_caster = True`.)
3. **Receiver** — the surface the caustic lands on (backdrop, table, the bottle's own label): `Object Properties > Shading > Caustics > Receive Shadow Caustics` → **on**. (Python: `obj.is_caustics_receiver = True`.)

Hard requirements — violate one and you get nothing, silently:
- The caster must be **Shade Smooth** with smooth, continuous normals. MNEE solves on a smooth manifold; a faceted or hard-edged caster fails. `Shade Smooth` + Auto Smooth, no sharp-edge splits in the caustic-forming region.
- The caster should be reasonably **dense and clean**. Mantaflow output is usually fine; low-poly boolean geometry is not.
- Works with point, spot and area lights. **Sun lights and world/HDRI lighting produce no shadow caustics** — the caustic must come from a flagged light.
- It replaces the *shadow* contribution only. It will not produce reflected caustics from a metal cap, and it will not produce caustics visible *through* another refractive surface.
- Roughness on the caster should be ~0. A rough caster has no manifold to solve.
- CPU and GPU both supported; it is not free but it is orders of magnitude cheaper than brute force for the same result.

**For this shot:** flag the **key light** as a caustics light, the **bottle + inner liquid + splash** as casters, and the **backdrop sweep** as receiver. You get the bright orange caustic smear behind and beneath the bottle that makes the whole frame feel lit by real liquid.

```python
import bpy

def enable_shadow_caustics(light_names, caster_names, receiver_names):
    for n in light_names:
        ob = bpy.data.objects.get(n)
        if ob and ob.type == 'LIGHT':
            ob.data.cycles.is_caustics_light = True
    for n in caster_names:
        ob = bpy.data.objects.get(n)
        if ob:
            ob.is_caustics_caster = True
            # MNEE needs smooth normals
            if ob.type == 'MESH':
                for p in ob.data.polygons:
                    p.use_smooth = True
    for n in receiver_names:
        ob = bpy.data.objects.get(n)
        if ob:
            ob.is_caustics_receiver = True

enable_shadow_caustics(
    light_names   = ["KEY_strip"],
    caster_names  = ["mountain dew bottle", "bottle_liquid", "liquid_domain_mesh"],
    receiver_names= ["BACKDROP_sweep", "FLOOR"],
)
```

### 2.4 The practical fake (use this 80% of the time)

Even MNEE is slow and fussy on a 300-frame splash sequence where the caster changes every frame. Commercial work fakes caustics constantly, and it looks better because it is **art-directable**.

**Fake A — gobo/cookie texture on a spot light.**
Point a Spot or Area light at the product and put a caustic texture in its node tree:

```
Texture Coordinate (Normal) → Mapping (Scale 2,2,2)
  → Image Texture ["caustic_pattern.exr", Extension: Extend, Non-Color]
  → ColorRamp [pos 0.0 black → pos 1.0 white, Ease]
  → Math (Multiply, 6.0)
  → Emission (Color = warm orange #FFB061, Strength = 1.0)
  → Light Output
```
For a light, feed the result into the light's **Emission** node colour/strength. Animate the `Mapping > Location` X/Y slowly (a few cm over 100 frames) and the caustics crawl exactly like real ones. Free caustic animation.

Source textures: any "caustics" EXR/PNG sequence, or generate one in Blender by rendering an actual MNEE caustic once and reusing it.

**Fake B — pure procedural, no texture file.**
```
Texture Coordinate (Object) → Mapping
  → Noise Texture (Scale 8, Detail 6, Roughness 0.6, Distortion 1.5)
  → ColorRamp [black at 0.48, white at 0.55]        # thin bright veins
  → Math (Power, 3.0)                                # sharpen into filaments
  → Math (Multiply, 8.0)
  → Emission (Strength 1.0) → Light Output
```
Animate by driving `Noise Texture > W` (set noise to 4D) with `#frame * 0.01`. That gives shimmering, non-repeating caustic motion. This is the fastest caustic you will ever render.

**Fake C — comp it.** Render a caustics-only pass (a plane with the caustic texture, emissive, rendered as its own light group or a separate layer) and Add it in the compositor. Total control over intensity, colour and timing, zero re-render cost.

**Fake D — bake real caustics once.** Render 1 frame with MNEE at high quality, save the caustic pattern as an EXR, then project it as a gobo for the whole sequence. Physically motivated, art-directable, cheap.

### 2.5 Where caustics should land in this shot

- A bright **orange-amber pool** on the backdrop behind and below the bottle, roughly the width of the bottle, slightly stretched by the sweep's curvature.
- **Bright filaments inside the bottle's shadow**, because the amber liquid focuses light.
- **Small hot spots** thrown by individual splash droplets onto the bottle label — this is the detail that sells "in-camera".
- The splash's own shadow should be **light and warm**, never a black silhouette. If it is black, revisit §1.4 Cheat 4.

---

## 3. The bottle

Three separate materials on (at least) three separate meshes: **PET wall**, **liquid inside**, **cap**. Plus the label (§4). Never one material.

### 3.1 Clear PET plastic

PET (polyethylene terephthalate) is IOR **1.575** in reality but everyone shades it at **1.46–1.50** because it looks better and refracts less aggressively. Bottle walls are 0.3–0.6 mm — optically thin.

**The thin-walled vs solid decision.** This is the most important call.

| | Thin-walled (single-surface, no Solidify) | Solid (walls with real thickness) |
|---|---|---|
| Geometry | one shell, no interior | Solidify 0.4 mm, or modelled walls |
| Refraction | one interface — cheap, clean | two interfaces per wall — 4 per bottle crossing |
| Ray cost | low | high, and stacks with the liquid |
| Realism | slightly too clean | correct, shows edge thickness at the bottle silhouette and the cut-off ring at the neck |
| Nesting problems | none | must not intersect liquid mesh (§3.2) |

**Recommendation:** model the bottle as a **single shell with a Solidify modifier at 0.4 mm**, and set the Solidify to **Even Thickness** with **Rim: Fill** off at the top so the mouth reads open. That gives you visible glass thickness on the silhouette — which is what makes a bottle look real — without hand-modelling walls. If render time explodes, delete the Solidify and go thin-walled; you will lose the edge-thickness read but nothing else.

For a bottle *behind* a splash and *behind* a label, thin-walled is genuinely fine.

**Node setup:**
```
Principled BSDF
  Base Color         = (1.0, 1.0, 1.0)      pure white, no tint — the amber comes from the liquid
  Metallic           = 0.0
  Roughness          = 0.03 – 0.08          NOT 0.0; PET has faint moulding texture
  IOR                = 1.46
  Transmission       = 1.0                  (4.x: "Transmission Weight")
  Coat Weight        = 0.0                  (PET does not need clearcoat; wetness adds it later, §5)
  Alpha              = 1.0
  Normal ← Bump (Strength 0.05) ← Noise Texture (Scale 300, Detail 2)   # micro moulding grain
→ Material Output
```

The 0.03–0.08 roughness is the single detail that separates "plastic bottle" from "crystal glass". Push it to 0.12 with a subtle noise-driven variation if you want a cheaper, recycled-PET look. Also consider a **Roughness ramp**: bottles are rougher near the ribbed base and the moulding seam.

**The moulding seam.** Real blow-moulded bottles have two vertical seams 180° apart. A thin vertical roughness stripe (Object coords → Separate XYZ → Math on angle, or a simple UV-space stripe) at roughness 0.25 is a 3-node detail that adds enormous believability. Optional but cheap.

### 3.2 The liquid inside — the separate-mesh rule

**Rule: the liquid must be its own mesh, and its surface must NOT be coincident with the bottle's inner wall.**

Why. When two transmissive surfaces are exactly coplanar, the renderer cannot decide which one a ray hits first. You get z-fighting in ray space: black speckle, random bright dots, a hard dark ring at the liquid line, and completely wrong IOR nesting (the ray thinks it went air→plastic→air→liquid when physically it went air→plastic→liquid). It never renders correctly and it is not fixable in comp.

**The correct build:**
1. Duplicate the bottle mesh (`Shift+D`, Esc).
2. Rename to `bottle_liquid`.
3. **Shrink it inward** so it sits just inside the bottle's inner wall. Two options:
   - Alt+S (Shrink/Fatten) by **−0.001 m (1 mm)** in Edit Mode, or
   - a **Shrinkwrap** modifier (Mode: Nearest Surface, Offset **−0.001**) targeting the bottle.
4. Delete the faces above the fill line, then `F` / grid-fill a **flat cap** at the liquid surface. That flat disc is the meniscus — the visible liquid line. Give it a tiny inset ring pushed up 0.5 mm to fake surface tension against the wall if you want to be precise.
5. Make sure it is **manifold and closed** (`M > By Distance`, then check with `Select > All by Trait > Non Manifold`). Volume Absorption requires a closed volume.

**The tiny-offset trick, quantified.** 1 mm at real scale, or ~0.5% of the bottle's radius, is enough. Smaller than 0.1 mm and you are back to precision errors at render float precision; bigger than 3 mm and you can see a visible air gap ring at the shoulder. If your scene is scaled (a common Mantaflow habit is to build the sim at 10× scale), scale the offset with it.

**IOR nesting note.** Physically the ray goes air(1.0) → PET(1.46) → liquid(1.35). Cycles does not track nested media by default — each interface uses its own IOR against air. This means the liquid's *inner* surface refracts as if the ray came from air, which over-bends slightly. Nobody will ever see it. If you care, drop the liquid IOR to ~1.33/1.46 ≈ 0.91... — do not; just use 1.35 and move on.

### 3.3 The amber liquid — density, not base colour

**The mistake:** setting Principled Base Color to orange with Transmission 1.0. Result is a flat, plasticky, evenly-orange fluid that looks like tinted acrylic. Base colour on a transmissive surface tints *per interface*, so the thin edges and the thick middle are the same colour. Real liquid gets darker where it is deeper. That depth gradient is the entire read of "dense syrupy soda".

**The correct way — Volume Absorption inside a closed liquid mesh:**

```
Glass BSDF (Color white, Roughness 0.0, IOR 1.35) ─→ Material Output (Surface)
Volume Absorption (Color = amber, Density = 60–180) ─→ Material Output (Volume)
```

Volume Absorption's **Color is what survives** the medium. For amber soda you want red and green to survive and blue to be eaten:

| Look | Absorption Color (hex / linear-ish RGB) | Density (bottle ≈ 0.25 m tall) |
|---|---|---|
| Pale ginger ale | `#FFC98A` — (1.00, 0.79, 0.54) | 25 |
| Amber / apple soda (**this shot**) | `#FF9A2E` — (1.00, 0.60, 0.18) | 90 |
| Deep orange | `#FF6A00` — (1.00, 0.42, 0.00) | 140 |
| Cola | `#7A2E00` — (0.48, 0.18, 0.00) | 220 |

Density is per Blender unit of path length. If the liquid column is ~0.2 m and you want it noticeably dark, you need density in the tens-to-hundreds. Start at 90, render, and adjust by eye — **density is scale-dependent, so these numbers assume a real-world-scale bottle**. If your bottle is 2.5 m tall because you never applied scale, divide density by 10.

Requirements: **Volume bounces ≥ 2** in Light Paths, and the liquid mesh must be **closed and manifold**, else the volume leaks and renders inconsistently.

**Cheap alternative if volumes are too slow:** `Glass BSDF` with Color = a saturated amber, plus a **second Glass** at a darker amber mixed by `Layer Weight (Facing)` so the thick centre reads darker. Fast, ~70% of the look, no volume cost. Use this for the airborne fruit or background bottles; use the real volume on the hero.

**Bubbles.** A soda without bubbles reads as juice. Two cheap approaches:
- Geometry Nodes: `Distribute Points in Volume` inside the liquid mesh → `Instance on Points` (Ico Sphere, radius 0.4–1.2 mm) → tiny Glass BSDF at IOR **1.0/1.33 inverted** (an air bubble in water is IOR 1/1.33 ≈ 0.75 — actually set the bubble Glass IOR to **0.75** to get the correct inside-out refraction).
- Or a fine **Voronoi bump** on the liquid's inner surface where it meets the glass, which fakes clinging carbonation for zero geometry.

### 3.4 The cap

Orange screw cap, injection-moulded polypropylene. It is the one **opaque** part of the bottle and the shot needs it: a solid, saturated colour block gives the eye somewhere to land.

```
Principled BSDF
  Base Color   = #E8580F  (saturated orange, slightly darker than the backdrop so it separates)
  Metallic     = 0.0
  Roughness    = 0.35     ← the key value. Moulded PP is satin, not glossy.
  Specular IOR Level = 0.5
  Coat Weight  = 0.15     ← thin factory gloss; also carries the wet layer later
  Normal ← Bump (Strength 0.15, Distance 0.0005) ← the knurled ridge pattern
```
Knurling: model the vertical ridges as real geometry (an Array/Simple-Deform ring, or a Screw modifier) rather than bumping them — at hero scale the silhouette matters and a bump-only cap looks flat at the edges. Add the **tamper-evident ring** below the cap with a thin bridge of geometry; it is a 30-second detail that reads as "real product".

### 3.5 bpy — bottle plastic, amber liquid, cap

```python
import bpy

def sock(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    raise KeyError(names)

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, m.node_tree


def make_pet_plastic(name="M_Bottle_PET", roughness=0.05, ior=1.46, grain=True):
    mat, nt = new_mat(name)
    out  = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (400, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Metallic"].default_value   = 0.0
    bsdf.inputs["Roughness"].default_value  = roughness
    bsdf.inputs["IOR"].default_value        = ior
    sock(bsdf, "Transmission Weight", "Transmission").default_value = 1.0
    sock(bsdf, "Coat Weight", "Clearcoat").default_value = 0.0

    if grain:
        noise = nt.nodes.new("ShaderNodeTexNoise"); noise.location = (-560, -260)
        noise.inputs["Scale"].default_value  = 300.0
        noise.inputs["Detail"].default_value = 2.0
        bump  = nt.nodes.new("ShaderNodeBump");  bump.location = (-280, -260)
        bump.inputs["Strength"].default_value = 0.05
        bump.inputs["Distance"].default_value = 0.0002
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    try:
        mat.use_raytrace_refraction = True; mat.render_method = 'DITHERED'
    except AttributeError:
        mat.use_screen_refraction = True; mat.blend_method = 'HASHED'
        mat.refraction_depth = 0.0004
    return mat


def make_amber_liquid(name="M_Liquid_Amber",
                      absorb=(1.0, 0.60, 0.18, 1.0), density=90.0, ior=1.35):
    """Glass surface + Volume Absorption. Mesh MUST be closed/manifold and
    offset ~1mm inside the bottle wall."""
    mat, nt = new_mat(name)
    out   = nt.nodes.new("ShaderNodeOutputMaterial");   out.location   = (400, 0)
    glass = nt.nodes.new("ShaderNodeBsdfGlass");        glass.location = (0, 120)
    glass.inputs["Color"].default_value     = (1.0, 1.0, 1.0, 1.0)
    glass.inputs["Roughness"].default_value = 0.0
    glass.inputs["IOR"].default_value       = ior
    vol   = nt.nodes.new("ShaderNodeVolumeAbsorption");  vol.location  = (0, -180)
    vol.inputs["Color"].default_value   = absorb
    vol.inputs["Density"].default_value = density
    nt.links.new(glass.outputs["BSDF"],   out.inputs["Surface"])
    nt.links.new(vol.outputs["Volume"],   out.inputs["Volume"])
    return mat


def make_cap(name="M_Cap_Orange", color=(0.78, 0.16, 0.02, 1.0)):
    mat, nt = new_mat(name)
    out  = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (400, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value  = 0.35
    sock(bsdf, "Coat Weight", "Clearcoat").default_value = 0.15
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def assign(obj_name, mat, slot=0):
    ob = bpy.data.objects.get(obj_name)
    if not ob: return
    if len(ob.data.materials) <= slot:
        ob.data.materials.append(mat)
    else:
        ob.data.materials[slot] = mat

assign("mountain dew bottle", make_pet_plastic())
assign("bottle_liquid",       make_amber_liquid())
assign("bottle_cap",          make_cap())
bpy.context.scene.cycles.volume_bounces = 2
```

---

## 4. The label

The label is where a "nice render" becomes "a product shot". It is also the fastest way to make it look fake.

### 4.1 Separate geometry vs texturing onto the bottle

**Separate geometry — do this.** A real label is a printed film wrapped around the bottle with visible thickness, a seam, an edge highlight, and it is *not* transmissive while the bottle is. Trying to do that inside a single transmissive material means mixing a Diffuse/Principled-opaque shader against a Transmission-1.0 shader through an alpha mask, which produces soft, wrong edges and breaks the bottle's refraction where the label sits.

**Build:**
1. Select the bottle, Edit Mode, select the band of faces the label covers (box-select a horizontal ring; the label sits between the shoulder and the ribbed base).
2. `Shift+D` `Esc` then `P > Selection` to make it a separate object `bottle_label`.
3. **Shrinkwrap** modifier on `bottle_label`: Target = bottle, Mode = **Nearest Surface Point**, Offset = **0.0003** (0.3 mm proud of the wall).
4. **Solidify** modifier: Thickness **0.00015** (0.15 mm), Offset −1, **Even Thickness** on. This gives the label an actual edge you can catch a highlight on.
5. Optional: cut the seam — delete one column of faces so the label has a visible overlap join, then duplicate a narrow strip over it. This one detail is a giveaway of a real bottle.

The `Shrinkwrap` matters even though you duplicated the faces: if you later change the bottle (a Subdivision level, a shape tweak, a Cast modifier), the label follows automatically instead of sinking into the wall.

**Texturing straight onto the bottle** is acceptable only when the label is a **printed-on**, no-thickness graphic (some sports drinks, some cans) or when the bottle is 30 px tall in the background. Then: one material, `Image Texture (Alpha)` → `Mix Shader` between the transmissive PET and an opaque Principled.

### 4.2 UV unwrapping the label band

A cylinder needs exactly one vertical seam.

1. In Edit Mode on `bottle_label`, select one vertical edge loop running top-to-bottom → `Ctrl+E > Mark Seam`.
2. Also mark the **top and bottom boundary loops** as seams (they are already open boundaries if you separated the band, so this is usually automatic).
3. `A` then `U > Unwrap` (Angle Based). You will get a clean rectangle.
4. In the UV editor, `A` then `S` to scale so the UV island **fills 0–1 in U**, and set V to the label's aspect. Use `UV > Align` / `Follow Active Quads` if the unwrap is skewed.
5. **Check for stretching**: UV Editor > Overlays > **Display Stretch: Area**. It should be uniformly blue. Any green/red means your label art will distort.

Alternative when the surface is not a clean cylinder (tapered shoulder, ribbed base): `U > Cylinder Projection` with **Direction: View on Equator**, camera looking down the bottle's axis in orthographic front view, **Align: Polar ZX**. Fast and often good enough.

### 4.3 The UV Project modifier (the pro move)

When you want a **flat, non-distorting projection** of label art regardless of the underlying UVs — and you want to art-direct it interactively — use the **UV Project** modifier.

1. Add an **Empty** or a **Camera** (orthographic) in front of the label, looking at it.
2. On `bottle_label`: `Modifier > UV Project`. Set **UV Map** = the label's map, **Projectors: 1**, **Object** = your empty/camera, **Aspect X/Y** to the label art's aspect ratio.
3. Move/scale the projector object and watch the label slide around the bottle in real time.

Why it beats plain UVs: repositioning a printed graphic becomes an object transform (keyframeable, driver-able, art-director-friendly) instead of a UV editing session. It projects **planar**, so the label stretches at the extreme left/right of a cylinder — which is why you use it on the *front-facing* label panel and let a plain cylindrical unwrap handle the wrap-around.

For a full 360° wrap: use the cylindrical unwrap (§4.2), not UV Project.

### 4.4 The label material

Reference: white wraparound, green leaf-like graphics, yellow/green type. So: white paper-ish base, semi-gloss finish, printed colour, sharp type.

```
Image Texture ["label_art.png", Color Space: sRGB, Extension: Clip]
    ├─ Color ──────────────────→ Principled  Base Color
    └─ Alpha ──────────────────→ Mix Shader Fac  (Transparent | Principled)

Image Texture ["label_rough.png", Color Space: Non-Color] → Principled Roughness
Image Texture ["label_height.png", Color Space: Non-Color] → Bump (Strength 0.2, Distance 0.0002) → Principled Normal

Principled BSDF
  Base Color   ← label art
  Roughness    = 0.42 base (paper/matte film), 0.08 for gloss-varnished areas
  Metallic     = 0.0  (see foil note below)
  Coat Weight  = 0.25  ← the printed varnish layer. This is what makes it read "printed", not "painted"
  Coat Roughness = 0.10
  Specular IOR Level = 0.5
```

**Alpha-cut PNG.** If the label art has transparency (a die-cut shape, or you want the bottle to show through around it), you must:
- set the Image Texture **Extension = Clip** (not Repeat — Repeat tiles the art around the bottle and you get a repeating logo band),
- route **Alpha → Mix Shader Fac** with a `Transparent BSDF` in socket 1 and the label Principled in socket 2, **or** simply wire Alpha → Principled `Alpha` and set material `Blend Mode: Alpha Clip` for EEVEE. In Cycles, Alpha on Principled works directly; just raise **Transparent bounces** to 16.
- If you get dark fringes on the alpha edges, your PNG is not premultiplied correctly — set the Image Texture node's **Alpha: Straight** vs **Premultiplied** to match, or fix the source.

**Paper vs glossy-foil finish** — a real decision that changes the shot:

| Finish | Roughness | Metallic | Coat | Reads as |
|---|---|---|---|---|
| Uncoated paper | 0.65 | 0 | 0.0 | craft/artisan, absorbs light, goes flat in a splash shot |
| Matte film (typical soda) | 0.40 | 0 | 0.15 | clean, modern, safe |
| **Gloss film (recommended here)** | 0.15 | 0 | 0.35 / rough 0.08 | catches the strip light, looks wet-adjacent, premium |
| Metallic foil accent | 0.20 | **1.0** (masked) | 0.3 | premium/energy-drink; mask Metallic with a greyscale foil map so *only* the foil areas are metal |

For the foil: `Image Texture ["label_foil_mask.png", Non-Color] → Principled Metallic`, and feed the same mask into a `Mix Color` to darken roughness in those regions. Never set Metallic to a global 1.0 — a fully metallic label goes black everywhere the environment is dark.

**Bump on the label edge.** Two separate bumps, do not confuse them:
- **Print emboss** — the raised ink/varnish of the graphics. `Label art (Color) → Color Ramp → Bump (Strength 0.05, Distance 0.00005)`. Very subtle. 
- **The label's physical edge** — that comes from the Solidify in §4.1, as real geometry. Do not try to bump it; a bumped edge has no silhouette and looks pasted on.

### 4.5 Making it look genuinely wrapped

The tells that a label is wrapped and not a decal:

1. **It follows the bottle's curvature** — Shrinkwrap handles this. Verify by hiding the bottle: the label should be a curved shell, not a flat card.
2. **The graphics distort at the wrap edges.** A cylindrical unwrap does this for free. If you used UV Project, the front reads correctly but the sides do not compress — add a slight `Mapping` node warp or switch to cylindrical.
3. **There is an air-bubble / wrinkle micro-relief.** Add a very low-frequency noise to the label's normal: `Noise Texture (Scale 6, Detail 2) → Bump (Strength 0.08, Distance 0.0005) → Normal`. Breaks the perfect specular of a CG cylinder, which is the #1 giveaway.
4. **A Displace modifier for the ribbed sections beneath.** If the label crosses the bottle's ribbed base area, the ribs push through the label. Add a **Displace** modifier on the label driven by the same rib pattern (or just let the Shrinkwrap follow the ribbed geometry).
5. **The seam.** One narrow vertical strip with a slightly different roughness where the label overlaps itself.
6. **A soft, contact-shadow-like darkening at the label's top and bottom edge** — comes for free if you have AO/GI, but check it is there. Without it the label floats.
7. **The label gets wet too.** Whatever wetmap you build in §5 must include the label, or you get a dry label on a wet bottle, which reads instantly as fake.

### 4.6 Faking label art fast

You need art before you can look-dev. Fastest paths:
- Design a flat 2048×1024 PNG in Figma/Affinity/Inkscape (30 min).
- Import an **SVG** directly into Blender (`File > Import > SVG`), extrude, and use it as real geometry on the label — infinitely crisp at any zoom, no texture resolution limit. Best for logos and type.
- Use Blender's **Text object** on a curved surface with a Shrinkwrap + Curve modifier for a placeholder.
- Generate placeholder art with an image model at 2048², then clean up the type. Do **not** ship generated brand marks; replace with the real logo before delivery.

Whatever you do: type must be **crisp**. Blurry label type kills the shot faster than a bad splash. See §10 for texel density.

---

## 5. Wet surfaces

The highest-value technique in this module. A dry hero bottle in a splash shot is the single most common failure in amateur beverage renders — the splash is flying past a bone-dry product and the composite falls apart.

Wetness does three optical things, and you must do all three:
1. **Roughness drops.** A water film smooths microsurface. Roughness 0.35 → 0.05.
2. **A second specular layer appears.** The water film has its own IOR-1.33 interface on top of the object's surface. That is what a **Coat** layer models.
3. **Base colour darkens and saturates.** Wet materials are darker because light enters, scatters, and less comes back. Multiply base colour by ~0.6–0.8 in wet areas.

### 5.1 Level 1 — the global wet coat (2 minutes)

On the cap, fruit and label:
```
Principled BSDF
  Coat Weight    = 0.6        (3.6: "Clearcoat")
  Coat Roughness = 0.03       (3.6: "Clearcoat Roughness")
  Coat IOR       = 1.33       (4.x only; 3.6's clearcoat is fixed at 1.5)
```
Uniform wetness everywhere. Fast, and better than nothing, but wrong: real splash-wetting is **directional and patchy** — the side facing the splash is soaked, the far side is dry.

### 5.2 Level 2 — a procedural wetness mask (10 minutes)

Drive Coat Weight and Roughness from a mask instead of a constant. Cheapest useful mask is a **directional gradient plus noise**:

```
Texture Coordinate (Object) → Separate XYZ
   ├─ X → Map Range (From -0.05..0.05 → To 0..1)    # wet on the +X side, dry on -X
   └────────────────────────────────────────────┐
Noise Texture (Scale 12, Detail 8, Roughness 0.7) ┤
   → Mix Color (Multiply, Fac 0.6) ───────────────┘
   → ColorRamp [pos 0.35 black → pos 0.55 white]   # sharpen into runnels
   ├→ Principled  Coat Weight
   ├→ Map Range (0..1 → 0.35..0.04) → Principled Roughness
   └→ Mix Color (Multiply) with Base Color, factor 0.35   # darken where wet
```
Combine with a **Pointiness** or **Geometry > Normal Z** term so water pools in crevices and runs off convex tops:
`Geometry (Pointiness) → Map Range (0.44..0.5 → 0..1)` → add into the mask.

### 5.3 Level 3 — Dynamic Paint wetmap (the real technique)

This is the one that makes it look shot, not rendered. You let the actual splash geometry paint a wetness map onto the bottle, then drive roughness/coat/bump from it. Because the splash animates, the bottle **gets progressively wetter as the splash hits it, and dries afterwards.**

**Step 0 — prepare the brush geometry.**
Dynamic Paint needs a stable, evaluable animated mesh. A live Mantaflow liquid mesh re-generated from cache each frame usually works but is slow and occasionally unstable. **Bake the fluid mesh to Alembic first** (`File > Export > Alembic`, frame range = your sim range, then re-import), and use the Alembic-driven mesh as the brush. This also lets you paint the wetmap without re-simulating.

Alternatively, and often better: use the splash's **particle system** (Mantaflow spray/foam/bubble particles) as the brush source. Particle-based painting gives you speckled, droplet-shaped wetting instead of a blobby proximity smear.

**Step 1 — make the bottle a canvas.**
1. Select `mountain dew bottle` (and `bottle_label`, and any fruit you want wet).
2. `Physics Properties > Dynamic Paint > Add > Canvas`.
3. `Surface Type: Paint`.
4. `Format: Vertex` — paints into vertex colour attributes. Requires **dense geometry**: subdivide the bottle to ~150k–400k verts, or Dynamic Paint will paint chunky blobs. (Choose `Image Sequence` format instead if you want a UV-space bakeable map and your UVs are clean — better quality, more setup, and it writes PNG sequences to disk.)
5. Open **Output** sub-panel. You get two outputs:
   - **Paint Output** → default attribute name `dp_paintmap` (the colour, permanent).
   - **Wetmap Output** → tick it; default attribute name `dp_wetmap` (0–1, **fades as it dries**).
6. Open **Dissolve** sub-panel → enable **Dry**, set **Dry Time** to e.g. 120 frames, and enable **Slow** for a non-linear dry curve. Without Dry enabled, the wetmap never decays and you just get a permanent mask.
7. Set **Frame Start/End** to cover the splash, and **Sub-Steps 2–4** so a fast splash does not skip past the bottle between frames.

**Step 2 — make the splash a brush.**
1. Select the splash mesh (or the particle-emitting object).
2. `Physics Properties > Dynamic Paint > Add > Brush`.
3. **Source**:
   - `Mesh Volume + Proximity` with **Proximity Distance ≈ 0.01 m** — paints where the mesh is near or overlapping. Good for the main splash body.
   - `Particle System` — pick the Mantaflow spray/foam system. Use **Solid Radius** ≈ particle size and **Smooth Radius** 0.005 for soft-edged droplet marks. Better for speckle.
4. **Paint Color** = pure white (1,1,1). You are painting a mask, not a colour.
5. **Absolute Alpha** on, **Paint Alpha** 1.0, **Wetness** 1.0.
6. Optional: **Use Object Velocity** to make fast-moving splash paint harder.

**Step 3 — bake.**
`Dynamic Paint > Canvas > Cache > Bake`. Baking is required for reliable playback and rendering; without it, you get correct results only when the timeline plays linearly from the start frame.

**Step 4 — read the wetmap in the shader.**

Blender 3.6+:
```
Color Attribute node  [Name: "dp_wetmap"]     (or Attribute node, Type: Geometry, Name: dp_wetmap)
   → (use the Fac / Alpha output; the wetmap is greyscale)
   → ColorRamp [pos 0.02 black → pos 0.30 white]     # tighten the falloff
   → WET  (0..1)
```
Then fan `WET` out to four places:
```
WET → Principled  Coat Weight                                    (0 → 0.85)
WET → Map Range [0..1 → 0.42..0.05] → Principled Roughness
WET → Mix Color (Multiply, Fac = WET*0.4) on Base Color          # darken
WET → Math (Multiply, 0.4) → Bump Strength   ←  Voronoi droplets (§6)
```
That last line is the important one: use the wetmap to **mask where droplets exist**, so condensation/spray droplets only appear where the splash actually hit. Dry side = clean, wet side = beaded. That is the detail that makes people ask what renderer you used.

**Gotchas:**
- **Vertex format needs vertex density.** If your wetmap looks like low-poly triangles, subdivide.
- Dynamic Paint runs on the **evaluated** mesh, but modifier order matters — put Subdivision *before* Dynamic Paint in the stack.
- The attribute name is case-sensitive: `dp_wetmap`, not `dp_wetMap`.
- In Blender 4.x use the **Color Attribute** node; the old `Attribute` node still works but the Color Attribute node is explicit about domain.
- If nothing paints: check the brush and canvas have overlapping **Frame Start/End**, check the brush's Proximity Distance is bigger than the actual gap, and check the canvas object's scale is applied.
- Wetmap + motion blur: the wetmap changes per frame, so it is motion-consistent. Good.

**Step 5 — bake it down (optional but recommended for a long sequence).**
Once happy, `Canvas > Format: Image Sequence` and bake the wetmap to a PNG sequence in UV space. Then swap the Color Attribute node for an `Image Texture` reading the sequence (Image node > Source: Image Sequence, auto-refresh on). Render time drops and you can paint fixes in Photoshop.

---

## 6. Condensation droplets

Three approaches, ranked by cost and by where each belongs.

### 6.1 Geometry-nodes scattered droplet instances

**Best quality; use on the hero bottle in close-up.** Real geometry means real refraction, real caustics, real silhouette on the bottle's edge — droplets that break the profile of the glass are a massive realism cue that a bump map can never give you.

```
Group Input (Geometry)
 → Distribute Points on Faces  [Poisson Disk, Distance Min 0.002, Density 8000,
                                Density Factor ← wetmap / vertex group]
 → Instance on Points  [Instance ← a squashed UV Sphere, ~8 verts, scaled 0.4 in Z]
      Scale ← Random Value (Float, 0.0006 .. 0.004)
      Rotation ← Align Euler to Vector (Z ← Normal)
 → Realize Instances (only if you need per-droplet shading variation)
 → Set Material  [M_Water_Droplet: Glass BSDF, IOR 1.33, Rough 0.0]
 → Group Output
```
Notes:
- **Squash the sphere in Z to ~0.35** and push it slightly into the surface so it reads as a bead sitting on glass with a contact meniscus, not a floating ball.
- Drive **Density Factor** from the `dp_wetmap` attribute (§5.3) so droplets only appear on the wet side. Sample it with a `Named Attribute` node (Float, "dp_wetmap").
- Add a second, sparser distribution of **large runnel droplets** (scale 0.004–0.012, elongated in −Z) with vertical streaks — condensation runs down.
- Cost: 20–80k tiny glass instances is fine; a million is not. Use a Density Factor that falls off away from camera.

### 6.2 Procedural Voronoi/noise bump droplets

**Best cost/benefit; use everywhere else** — the far side of the bottle, background bottles, the fruit. No geometry, no silhouette, but at any distance beyond a tight close-up the read is identical.

**Working recipe, with numbers:**

```
Texture Coordinate (Object)          # Object, not UV — avoids seam stretching
 → Mapping (Scale 1, 1, 1.6)         # slight Z stretch = drips run down

 ── A. DROPLET SHAPE ────────────────────────────────────────────
 → Voronoi Texture  [Feature: F1, Distance Metric: Euclidean,
                     Scale 55, Randomness 1.0]        (use .Distance output)
 → Color Ramp   [interpolation: Ease
                   pos 0.000  → white (1,1,1)
                   pos 0.085  → black (0,0,0)]        # only near cell centres survive
 → Math (Power, 0.5)                                  # rounds the profile into a dome
      = DROPS

 ── B. RANDOM DELETION MASK  (real condensation is patchy) ──────
 → (from Mapping) Noise Texture [Scale 5.0, Detail 3, Roughness 0.5]
 → Color Ramp   [Constant:  pos 0.42 black → pos 0.43 white]
      = MASK

 ── C. SIZE VARIATION ───────────────────────────────────────────
 → (from Mapping) Noise Texture [Scale 18, Detail 2] → Color Ramp [0.30 → 0.70]
      = SIZEVAR
 → Math (Multiply)  DROPS × SIZEVAR

 ── D. COMBINE + WETMAP GATE ────────────────────────────────────
 Math (Multiply): (DROPS×SIZEVAR) × MASK  → Math (Multiply) × dp_wetmap
      = D  (final 0..1 droplet field)

 ── E. DRIVE THE SHADER ─────────────────────────────────────────
 D → Bump [Strength 0.35, Distance 0.0006] → Principled Normal
 D → Map Range [0..1 → 0.30 .. 0.02]       → Principled Roughness
 D → Math (Multiply, 0.25) → Mix Color (Multiply) on Base Color   # droplets darken
 D → Math (Multiply, 0.5)  → Principled Coat Weight
```

Tuning cheatsheet:
| Want | Change |
|---|---|
| More droplets | Voronoi Scale 55 → 90 |
| Bigger droplets | ColorRamp black stop 0.085 → 0.14 |
| Fewer, sparser | MASK ColorRamp threshold 0.42 → 0.55 |
| Elongated drips | Mapping Scale Z 1.6 → 3.5 |
| Softer, condensation-y | Bump Strength 0.35 → 0.18, Voronoi Scale 120 |
| Rain-hit, chunky | Voronoi Scale 25, Bump Strength 0.6 |

Two important refinements:
- **Layer two Voronois at different scales** (55 and 130) and `Math (Maximum)` them. Real droplet fields are bimodal — a few big beads among many tiny ones. One Voronoi always reads as a regular pattern.
- **Use "Smooth F1"** (Voronoi Feature: Smooth F1, Smoothness 0.1) if you want droplets that merge where they touch. That merging is characteristic of condensation and Distance-metric F1 will not give it to you.

### 6.3 Droplet normal map

A tiling droplet normal map (from ambientCG, Poliigon, or baked from your own Voronoi setup) plugged into `Image Texture (Non-Color) → Normal Map → Principled Normal`. Fastest to render, zero node cost, but: it tiles visibly on a cylinder, it has no wetmap gating unless you mask it, and it carries no roughness variation unless the pack ships one. **Use for background/mid-ground props only.** For the hero, bake your own §6.2 setup to a texture instead — same speed, custom look.

### 6.4 Airborne micro-droplets (the frame-wide sparkle)

The reference frame has droplets scattered across the *whole image*, not just on surfaces. These are **not** part of the fluid sim mesh — resolving them in Mantaflow would need an absurd resolution.

Build them as instanced geometry (a Geometry Nodes `Distribute Points in Volume` inside a big cube around the product, `Instance on Points` an 8-vert ico sphere, random scale 0.3–2 mm), shaded with the **same Glass BSDF as the splash**. Key look-dev points:
- They must be **in the depth of field**. The ones near camera go to big soft bokeh circles — that is 70% of the "commercial" feel. Make sure some sit at 0.15–0.3 m from the lens.
- They need something bright to reflect. They will be almost invisible against a dark area and blaze against the emissive backdrop — which is the correct behaviour and another argument for §8's emissive sweep.
- Give a *few* of them a slightly higher IOR (1.45) so they catch harder highlights and the field does not look uniform.
- Motion blur: animate the point positions slightly so they streak. Static airborne droplets in a motion-blurred frame read as dust on the lens.

---

## 7. The fruit — limes / green apples

Fruit is the shot's colour accent and the only thing in frame doing real subsurface scattering. It also has the highest fake-to-real ratio: get SSS wrong and it looks like painted rubber.

### 7.1 Why SSS + a backlight is the whole trick

Citrus flesh is a bundle of translucent juice vesicles. Light entering the cut face travels several millimetres and exits somewhere else, glowing. **You only see that if light is coming from behind or from a grazing angle.** SSS lit purely from the front is indistinguishable from diffuse. So the fruit shader and the fruit lighting are one decision:

> Every fruit slice in frame should have a light **behind it, relative to camera**, even if it is a small dedicated area light that only that slice sees (use Light Linking in 4.0+, or a light with a small radius placed just out of frame).

That is the single highest-leverage note in this section.

### 7.2 Citrus flesh (the cut face)

```
Principled BSDF
  Base Color         = #B6D64A  (lime flesh, yellow-green)  / #E8F0B8 for a pale apple flesh
  Subsurface Weight  = 0.75          (3.6: "Subsurface")
  Subsurface Radius  = (0.004, 0.010, 0.003)  metres — R, G, B
  Subsurface Scale   = 0.02          ** 4.x ONLY ** — multiplies Radius. See warning below.
  Roughness          = 0.30
  Specular IOR Level = 0.5
  Coat Weight        = 0.55          ← the wet juice film. Essential.
  Coat Roughness     = 0.05
  Normal ← Bump (Strength 0.4) ← Voronoi (Scale 90, F1) → ColorRamp   # juice vesicles
```

**The radius numbers, explained.** Radius is per-channel scattering distance in scene units (metres). For a green fruit you want **green to travel furthest**, so the transmitted glow is green:
- Lime / green apple: `(0.004, 0.010, 0.003)` — G dominant.
- Orange / grapefruit: `(0.012, 0.006, 0.002)` — R dominant, the classic warm glow.
- Human skin (for reference, so you recognise the pattern): `(1.0, 0.2, 0.1)` scaled to ~0.01.

A lime slice is ~6 mm thick, so a green radius of 10 mm means light crosses the whole slice — which is exactly the backlit glow you want. If the fruit looks like plastic, your radius is **too small**, not too large.

**The 4.x upgrade trap.** Blender 4.0 added `Subsurface Scale` (default **0.05**), which *multiplies* the Radius. A 3.6 material with Radius (0.004, 0.010, 0.003) opened in 4.x effectively becomes (0.0002, 0.0005, 0.00015) — SSS vanishes and your fruit goes rubber. Fix: either set `Subsurface Scale = 1.0` and keep your 3.6 radii, or keep Scale at 0.05 and multiply your radii by 20. Also note `Subsurface Color` was **removed** in 4.0 — SSS now takes its colour from `Base Color`, so any 3.6 material relying on a differently-coloured Subsurface Color needs manual rework.

**Method.** Cycles offers Random Walk / Random Walk (Skin) / Christensen-Burley. Use **Random Walk** for fruit — it respects geometry thickness, so thin slice edges glow and thick sections do not. Burley ignores thickness and looks flat on a slice. Random Walk needs the mesh to be a **closed volume** — a single-sided slice with no thickness will render wrong.

**Alternative for very thin slices:** skip SSS entirely and use `Principled (Transmission 0.3)` or a `Translucent BSDF` added under a Diffuse. Cheaper, and for a slice tumbling past at speed it is indistinguishable.

### 7.3 The rind

The rind is the contrast element — opaque, saturated, textured, with a distinctive pitted surface.

```
Principled BSDF
  Base Color        = #3E8E1E (lime) / #6DBE2C (green apple)
     ← modulated by:  Voronoi (Scale 200, F1) → ColorRamp → Mix Color (Multiply, 0.25)
  Roughness         = 0.45
     ← varied by:     same Voronoi → Map Range [0.30 .. 0.60]
  Subsurface Weight = 0.15        # a little, at the very edge, keeps it from going dead
  Subsurface Radius = (0.002, 0.004, 0.001)
  Coat Weight       = 0.7         # citrus skin is naturally waxy AND it is wet in this shot
  Coat Roughness    = 0.06
  Normal ← Bump (Strength 0.6, Distance 0.0004)
     ← Voronoi [Feature: F1, Scale 220] → ColorRamp [Ease, 0.0 white → 0.25 black]  # pits
```
The pitted Voronoi bump is what makes citrus recognisable at a glance. Scale it to your fruit size: a 60 mm lime wants Voronoi Scale ~200–260 in Object coordinates. If the pits look like a regular grid, raise **Randomness** to 1.0 and add a low-scale Noise into the Voronoi's vector via a `Mapping` + `Noise` distortion.

**The albedo/pith layer.** Real citrus has a white pith between rind and flesh. Model it as a thin geometry ring with `Base Color #F2F0E2, Roughness 0.75, Subsurface Weight 0.5, Radius (0.006,0.006,0.006)`. It is a 3-minute detail that is highly visible on a cut face and almost always missing in CG fruit.

### 7.4 The wet coat on the fruit

Apply §5.1's coat plus §6.2's procedural droplets to *both* rind and flesh. Fruit in a splash shot must be beaded. Additional notes:
- On the **flesh**, wetness should read as a continuous juice film (high Coat Weight, near-zero Coat Roughness, no droplet bump) — juice wets the surface completely.
- On the **rind**, waxy skin beads (droplet bump on, Coat masked by droplets) — water does not wet wax.

That difference — sheet on the flesh, beads on the rind — is a genuinely advanced-looking detail for two extra nodes.

### 7.5 Whole green spheres

The reference also shows whole green fruit. Same rind shader, plus:
- A **stem divot** with a darker, rougher patch and an AO-style darkening (`Geometry > Pointiness → ColorRamp → Mix into Base Color`).
- Colour variation between individual fruits: `Object Info > Random → ColorRamp (green ramp) → Mix into Base Color, Fac 0.25`. A dozen identically-coloured apples read as instances; randomised ones read as fruit.
- A faint **bloom/wax haze** on apples: add a `Sheen Weight 0.15` with a pale sheen tint. Very characteristic and almost never done.

---

## 8. The backdrop

The saturated orange→amber vertical gradient with no visible seam or horizon. Three ways to build it, and the choice is **not** aesthetic — it determines whether your product is lit by the backdrop.

### 8.1 Option A — a curved sweep/cyclorama lit by coloured lights

A physical infinity cove: a plane that curves up into a vertical wall with a large-radius fillet, so there is no horizon line.

**Build:** a 4×4 m plane, extrude the back edge up 3 m, bevel that corner with **Segments 12–24, Width ~1.0 m**, Shade Smooth. Material: plain white or light grey diffuse (`Base Color 0.8, Roughness 0.6`).
Then light it with two coloured lights: a warm orange area light low and behind the product aimed at the lower sweep (`#FF6A00`, strength high), and a paler amber/yellow light aimed at the upper wall (`#FFB347`). The gradient comes from **falloff**, exactly like a real studio.

- **Pros:** completely physical. Bounce, contact shadows, caustic receiver (§2.3), correct inverse-square falloff, and the product genuinely sits in the environment. Colours can be changed by moving lights, which is how a real photographer works.
- **Cons:** slowest to set up, needs real lighting skill, and getting a *perfectly even* saturated gradient takes iteration. Colour is limited by what the lights + white surface can produce (you cannot exceed the surface's albedo).

### 8.2 Option B — an emission plane with a gradient (recommended)

A large plane or a curved sweep whose **material is emissive**, carrying the gradient directly.

```
Texture Coordinate (Object)        # Object, not Generated — survives object scaling predictably
 → Separate XYZ  →  Z
 → Map Range  [From Min -1.5, From Max 1.5 → To 0, 1]     # fit to the sweep's height
 → Color Ramp  [interpolation: B-Spline  (smoother than Linear, no visible banding)
       pos 0.00  #FFB43C     (bright amber, top)
       pos 0.45  #FF7A18     (mid orange)
       pos 1.00  #C43C00     (deep burnt amber, bottom)]
 → Emission  [Strength 4.0]
 → Material Output
```

If you prefer a true `Gradient Texture` node (useful when you want to rotate the gradient axis freely):
```
Texture Coordinate (Object) → Mapping (Rotation X 90°) → Gradient Texture (Linear)
 → Color Ramp [as above] → Emission (Strength 4.0) → Material Output
```

**Why this is the recommended option:** an emissive plane is a **light**. It lights the product, it fills the splash with something to refract (§1.3 cause E), it puts a huge soft orange gradient reflection down the side of the bottle, and it gives the airborne droplets something to blaze against. You get the exact gradient you designed *and* real bounce. Best of both.

Practical notes:
- **Strength 3–8.** Above ~10 the backdrop clips to white in the highlights and the gradient disappears under the view transform.
- Turn OFF `Object Properties > Visibility > Ray Visibility > **Shadow**` on the backdrop so it does not shadow itself, and consider turning off **Diffuse** ray visibility on a *second* copy if you want to decouple "what the camera sees" from "what lights the product". Advanced version: **two** backdrops — one camera-visible (Emission, no light contribution) and one invisible-to-camera emissive panel that does the lighting. Total independent control of look vs light.
- Put the backdrop in its own **Light Group** (`View Layer > Passes > Light Groups`, then `Object > Shading > Light Group`). Then you can regrade the backdrop's contribution in comp without re-rendering. Do this. Always.
- **Add a slight vignette in the shader**, not just in comp: multiply the emission by a radial `Gradient Texture (Spherical)` → ColorRamp so the edges fall off. Real coves do this and it focuses the eye on the product.

### 8.3 Option C — world shader gradient

```
World > Surface:
Texture Coordinate (Generated) → Separate XYZ → Z
 → Map Range [0..1 → 0..1]
 → Color Ramp [same stops as 8.2]
 → Background (Strength 1.0) → World Output
```
Or the classic sky-style version using `Texture Coordinate (Window)` for a screen-space gradient that never moves with the camera.

- **Pros:** zero geometry, instant, always seamless, lights the whole scene from every direction, and the splash always has something to refract.
- **Cons:** it is **infinitely far away**. There is no falloff, no contact, no caustic receiver, and — critically — **no surface for the caustics or the splash shadow to land on**. Your product floats in a void. The bottle will also pick up an unrealistically uniform ambient wash that flattens it.

**Verdict:** use the world gradient as a *supplement* (a low-strength ambient tint, Strength 0.3–0.8) underneath Option B, never as the only backdrop for a hero product shot.

### 8.4 Colour values that actually work

Values are sRGB hex, which is what Blender's colour picker Hex field takes (it converts to linear for you). If you set values via Python you must supply **linear** floats — see the conversion helper in the script below.

| Role | Hex | Notes |
|---|---|---|
| Backdrop top (bright amber) | `#FFB43C` | keeps the upper frame open and airy |
| Backdrop mid | `#FF7A18` | the dominant note; matches the reference |
| Backdrop bottom (deep) | `#C43C00` | grounds the product, gives the splash something dark to read against |
| Optional hot spot behind bottle | `#FFD98A` | a soft radial hotspot behind the neck separates the bottle silhouette |
| Key light | `#FFF4E8` | near-white, very slightly warm |
| Rim / kicker | `#FFE0A8` | warm amber, from behind, catches the splash rims |
| Fill (cool, subtle) | `#BFD8FF` | 5–10% strength; the tiny cool bounce that keeps the splash from going all-orange |

**The one cool light matters.** With an all-orange environment, a colourless splash still turns orange because everything it refracts is orange. Adding one weak cool fill or a small cool-tinted reflector card just out of frame is what keeps the splash reading **silver-white** as in the reference. Look-dev decision, executed with a light.

### 8.5 bpy — emissive gradient backdrop

```python
import bpy

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_rgba(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), a)


def make_backdrop_gradient(name="M_Backdrop_Amber",
                           stops=(("#FFB43C", 0.00),
                                  ("#FF7A18", 0.45),
                                  ("#C43C00", 1.00)),
                           strength=4.0, z_min=-1.5, z_max=3.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out  = nt.nodes.new("ShaderNodeOutputMaterial"); out.location  = (700, 0)
    emis = nt.nodes.new("ShaderNodeEmission");       emis.location = (500, 0)
    emis.inputs["Strength"].default_value = strength

    ramp = nt.nodes.new("ShaderNodeValToRGB");  ramp.location = (200, 0)
    cr = ramp.color_ramp
    cr.interpolation = 'B_SPLINE'          # avoids visible banding on a big gradient
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = stops[0][1]
    cr.elements[0].color    = hex_rgba(stops[0][0])
    for hexcol, pos in stops[1:]:
        e = cr.elements.new(pos)
        e.color = hex_rgba(hexcol)

    mr = nt.nodes.new("ShaderNodeMapRange");  mr.location = (0, 0)
    mr.inputs["From Min"].default_value = z_min
    mr.inputs["From Max"].default_value = z_max
    mr.inputs["To Min"].default_value   = 0.0
    mr.inputs["To Max"].default_value   = 1.0

    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-200, 0)
    tex = nt.nodes.new("ShaderNodeTexCoord");    tex.location = (-400, 0)

    nt.links.new(tex.outputs["Object"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"],      mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"],  ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], emis.inputs["Color"])
    nt.links.new(emis.outputs["Emission"], out.inputs["Surface"])
    return mat


def build_backdrop(width=6.0, depth=6.0, height=3.5, bevel_segments=16):
    """Curved cyclorama sweep with the gradient material."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.object
    ob.name = "BACKDROP_sweep"
    ob.scale = (width, depth, 1)
    bpy.ops.object.transform_apply(scale=True)
    # extrude back edge upward, then bevel the corner -> seamless cove
    import bmesh
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    back = [v for v in bm.verts if v.co.y > 0]
    ret  = bmesh.ops.extrude_vert_indiv(bm, verts=back)
    for v in ret['verts']:
        v.co.z += height
    bm.to_mesh(me); bm.free()
    bev = ob.modifiers.new("Cove", 'BEVEL')
    bev.width = min(width, height) * 0.45
    bev.segments = bevel_segments
    bev.limit_method = 'ANGLE'
    for p in me.polygons:
        p.use_smooth = True

    mat = make_backdrop_gradient(z_min=-0.2, z_max=height)
    ob.data.materials.append(mat)
    ob.visible_shadow = False          # do not let the cove shadow itself
    return ob

build_backdrop()
```

---

## 9. Colour strategy

### 9.1 Why orange + colourless + green

The palette in the reference is a deliberate, textbook choice, not an accident.

- **Orange backdrop (≈30° hue)** — the brand colour, and a warm advancing colour that pushes forward and reads as energy/citrus/sugar. It occupies the largest area, so it sets the shot's emotional temperature before anything else registers.
- **Green fruit (≈100° hue)** — roughly 70° from orange on the wheel. Not a true complement (that would be blue), but a **split/triadic** relationship: enough separation to pop hard, close enough to stay in the warm-natural family. Green also carries "fresh / natural / real fruit", which is the ad's claim.
- **Colourless silver-white splash** — the achromatic element. Against a saturated field, *neutral is the loudest colour you can use*. The splash reads as pure luminance contrast, which is the strongest kind. If the splash were tinted orange it would merge with the background; if tinted blue it would fight the palette and look like a different product.
- **Amber liquid in the bottle** — the same hue family as the backdrop but **darker and more saturated**, so the product separates from its environment by *value*, not hue. That is the trick: same colour story, different brightness.

The result is a **two-hue-plus-neutral** palette. Two hues is a design constraint that reads as "art-directed"; four hues reads as "assets from different packs".

### 9.2 Letting brand colour drive everything

Working method: take the brand's primary colour, then derive the whole scene from it.

1. **Brand primary** → the bottle's liquid/cap colour and the backdrop's mid-tone (backdrop desaturated ~15% and lightened, so the product stays the most saturated).
2. **Backdrop gradient** → brand primary lightened +25% at the top, darkened −35% and slightly hue-rotated toward red at the bottom. A hue shift across a gradient (orange→red-amber) looks vastly more expensive than a pure lightness ramp.
3. **Accent (fruit, garnish)** → 60–120° from the brand hue. Pick the one that matches the flavour claim.
4. **Lights** → near-neutral warm key, one cool low-strength fill to keep neutrals neutral.
5. **Splash** → neutral, always.

Every colour in the frame should be derivable from step 1. If a colour cannot be justified from the brand hue, remove it.

### 9.3 Keeping the product the brightest, most saturated thing

Two mechanisms, both look-dev:

- **Value hierarchy.** The backdrop's brightest point should be *below* the product's brightest specular. Ensure this by pinning the backdrop emission strength (3–8) and then lighting the product with a key that puts real specular hits above it. Check it by switching the View Transform to **Standard** momentarily and looking at where things clip — the product's highlights should clip first.
- **Saturation hierarchy.** The backdrop is a mid-saturation field; the cap and liquid are high-saturation points. Because saturation reads as "importance", a slightly desaturated backdrop makes a small saturated cap dominate a frame it occupies 2% of.

**View transform warning.** This section's hex values assume you know which transform you are on.
- **Blender 3.6 default: Filmic.** Desaturates and rolls off highlights heavily. A `#FF7A18` backdrop at emission 4 will render noticeably paler and less orange than the swatch. Compensate by picking *more* saturated source colours, or use the **Filmic > High Contrast** look.
- **Blender 4.0+ default: AgX.** Rolls off even harder and aggressively desaturates bright saturated colours (that is its purpose — it prevents the neon-clipping that Filmic and Standard produce). A saturated orange backdrop under AgX will render distinctly muted. Fixes: raise source saturation, use `Look: AgX - Punchy`, or add a Hue/Saturation node after the ramp with Saturation 1.2–1.4.
- **Standard** gives you exactly your hex values but will clip and posterise anywhere the splash gets hot. Do not ship a splash shot on Standard.

Decide the transform **before** you pick backdrop colours, and never change it after look-dev is approved.

Finally: put the backdrop, the product, the splash and the fruit into separate **Light Groups** or at minimum separate **Cryptomatte** objects, so the grade can adjust the hierarchy without touching the render.

---

## 10. Texel density, procedural vs baked, and fast assets

### 10.1 Texel density

Texel density = texture pixels per unit of surface. Consistency matters more than the absolute number — mismatched density is why one object looks softer than its neighbour.

| Surface | Density | Practical map size |
|---|---|---|
| Hero label (fills 25% of a 4K frame) | **4096 px/m** | 4096×2048 for a 24 cm × 12 cm label |
| Bottle body (mostly refractive, low detail) | 1024 px/m | 2048² |
| Fruit (hero, in focus) | 2048 px/m | 2048² per fruit type |
| Fruit (defocused foreground) | 512 px/m | 1024² |
| Backdrop sweep | 256 px/m or **procedural** | do not texture it at all |

Rule of thumb for the label specifically: **the label art should have at least 1.5× the pixels it occupies on screen at the tightest shot.** If the label is 900 px wide in a 4K frame, ship 1400+ px of label width. Underrun this and type goes mushy, which is the most visible possible failure.

Use the **TexTools** addon (`Texel Density` panel) or measure manually: apply a checker texture and confirm the squares are the same size across objects.

### 10.2 Procedural vs baked

| Use procedural when | Use baked/image when |
|---|---|
| Detail is non-representational (droplets, roughness break-up, noise, moulding grain) | Detail is designed (label art, logos, type) |
| The surface has bad or no UVs (Mantaflow output, boolean geometry) | You need artist control per pixel |
| You need it to work at any scale/zoom | You need render speed on a long sequence |
| You are still iterating | The look is locked |

**Bake when the sequence gets long.** A 250-frame render re-evaluates every procedural node on every sample of every frame. Baking your Voronoi droplets + wetmap + roughness break-up to 2K textures (Cycles > Bake > Diffuse/Roughness/Normal, or use the Node Wrangler / SimpleBake addon) can cut per-frame time 10–20% on a heavy shader. Keep the procedural version in a disabled node group so you can rebake after a note.

**Do not bake:** anything on the splash (its topology changes every frame — there are no stable UVs to bake to). The splash must stay procedural/constant-colour forever.

### 10.3 Getting or faking assets fast

- **HDRIs** (for a reflection environment behind the emissive backdrop): Poly Haven (CC0). A **studio softbox** HDRI plugged into the world at low strength gives the bottle credible rectangular highlights for free. Set world Ray Visibility > Camera **off** so it lights but does not show.
- **PBR textures**: ambientCG, Poly Haven, texture.ninja (all CC0). You need almost none for this shot — it is a procedural-heavy scene.
- **Droplet/condensation maps**: search ambientCG for "waterdrops"; or bake your own from §6.2 (better, and matched to your look).
- **Caustic textures**: render one MNEE frame (§2.4 Fake D), or grab any free caustics EXR loop.
- **Label art**: Figma/Inkscape → PNG at 4K, or import SVG for resolution-independent type.
- **Fruit models**: modelling a lime slice properly takes 20 minutes (cylinder, radial segments for segments/pith, inset for the rind) and is better than any free model, because you control where the SSS geometry is closed. Do not download fruit.
- **The bottle**: model it. A bottle is a profile curve + Screw modifier. Downloaded bottles come with terrible topology that breaks Shrinkwrap, MNEE and Dynamic Paint.

Time budget that works: **1 hour bottle, 30 min label art, 45 min fruit, 30 min backdrop, 3+ hours splash look-dev.** The splash is the job.

---

## 11. Shader debug checklist

Symptom → cause → fix. In diagnosis order.

### "The splash renders BLACK"
1. `Light Paths > Transmission` is at the default 12. → Set **24–32**, and Total ≥ that. *(fixes it 90% of the time)*
2. `Light Paths > Total` is lower than Transmission. → Total is a hard cap. Raise Total to 32–48.
3. Fluid mesh normals are inverted. → Edit Mode `A`, `Shift+N`. Check Overlays > Face Orientation for red faces. Apply scale (`Ctrl+A`).
4. Splash geometry is co-planar with / inside the bottle glass. → Nudge it out, or make the bottle thin-walled.
5. There is nothing bright behind the splash for it to refract. → Build the emissive backdrop (§8.2). Add a big top light.
6. You are in EEVEE without Screen Space Refraction. → Enable it in Render Properties *and* on the material (§1.8).
7. Still black in patches after all that. → Add the Ray Depth cutoff: `Light Path (Ray Depth) → Math (Greater Than, 4) → Mix Shader → Transparent BSDF`. Deep paths return background instead of black.

### "The splash renders GREY, DULL, MUDDY"
1. **Clamp Indirect is too low** (0.5–2.0). → Set 8–10, or 0 with Filter Glossy 1.0. This is the most common cause.
2. Roughness on the Glass BSDF is above 0. → Set **0.0**. Frosted water = grey water.
3. You added Volume Absorption to a splash. → Remove it (§1.5). Thin sheets + absorption = brown mush.
4. Glass Color is not white. → Set (1,1,1) or at most (0.92, 0.97, 1.0).
5. Filter Glossy is at 2.0+. → Drop to 0.5–1.0. Over-filtering blurs away the sparkle.
6. The denoiser is eating the highlights. → Lower denoise strength, or denoise a light group separately, or raise samples and use OIDN with **prefilter: Accurate** and Albedo/Normal passes on.
7. There is no hard specular source. → A splash needs at least one **small, bright** light (a thin strip or a small area light) to produce sharp rim highlights. Large soft lights alone make a grey splash.
8. No caustics. → §2. A splash with a flat, unbroken shadow always looks dead.

### "The bottle liquid looks like coloured plastic"
1. You tinted **Base Color** instead of using Volume Absorption. → Rebuild per §3.3: white Glass surface + Volume Absorption inside a closed mesh.
2. `Light Paths > Volume` is 0. → Set **2–4**. Volume Absorption does nothing at 0.
3. The liquid mesh is not closed/manifold. → `M > By Distance`, `Select > All by Trait > Non Manifold`, cap the top.
4. Absorption Density is too low for the scene scale. → Density is per unit. A 0.25 m bottle needs density in the tens-to-hundreds (start 90). If you scaled the scene 10×, divide by 10.
5. No visible **liquid line / meniscus**. → The flat cap disc at the fill level is what tells the eye "this is a liquid with a surface". Without it, the amber looks like tinted plastic all the way up.
6. There is no darkening gradient with depth. → That is the Volume Absorption signature. If you have absorption and still no gradient, the mesh is probably open (see 3) so rays never accumulate path length.
7. Black speckle at the liquid/wall boundary. → Coplanar surfaces. Offset the liquid mesh 1 mm inward (§3.2).

### "The label looks pasted on"
1. It is a texture on the bottle rather than separate geometry. → Separate it, Shrinkwrap + Solidify (§4.1). Real thickness catches a real edge highlight.
2. No edge/contact darkening at the label boundary. → Solidify gives geometry for AO to work on; also check you have GI (not just direct lighting).
3. The specular is too perfect. → Add the low-frequency wrinkle noise into the label's Normal (`Noise Scale 6 → Bump Strength 0.08`).
4. The label is dry while the bottle is wet. → Include the label in the Dynamic Paint canvas / apply the same droplet mask (§5, §6).
5. Blurry type. → Texel density (§10.1). Increase label map resolution, or import the logo as SVG geometry.
6. The art repeats around the bottle. → Image Texture `Extension` is set to **Repeat**. Set **Clip** or **Extend**.
7. Dark fringing on alpha edges. → Alpha mode mismatch (Straight vs Premultiplied) on the Image Texture node, or Transparent bounces too low (raise to 16).
8. UV stretching distorts the graphics. → UV Editor > Overlays > Display Stretch: Area. Re-unwrap with a single clean vertical seam.
9. It sits perfectly flat over a curved surface. → The Shrinkwrap target or mode is wrong; use **Nearest Surface Point** with a small positive offset.

### "The fruit looks like rubber"
1. **Subsurface Radius is too small.** → Lime flesh wants `(0.004, 0.010, 0.003)` metres. Increase until light visibly crosses the slice.
2. **You are on 4.x and `Subsurface Scale` is 0.05.** → It multiplies Radius, so your 3.6 values collapsed. Set Scale to 1.0, or ×20 your radii.
3. **There is no backlight.** → SSS is invisible without light behind or grazing. Add a small light behind each slice relative to camera (§7.1). This is usually the real problem.
4. Subsurface Method is Christensen-Burley. → Switch to **Random Walk** so thin slice edges glow correctly.
5. The slice has no thickness (single-sided plane). → Random Walk needs a closed volume. Solidify it.
6. No coat / it is dry. → Fruit in a splash shot must have `Coat Weight 0.5+` and droplets. Dry fruit reads as plastic regardless of SSS.
7. No surface detail. → Rind needs a Voronoi pit bump (Scale ~220, Bump Strength 0.6); flesh needs a vesicle bump (Voronoi Scale ~90).
8. Every fruit is the same colour. → `Object Info > Random → ColorRamp → mix into Base Color` at Fac 0.25.
9. Colour is flat and even. → Add the white pith ring and darken the rind's inner edge. Uniform albedo is a CG tell.

### "Everything is orange, including the splash"
Correct behaviour — the environment is orange and the splash is a mirror. Fix with a **cool fill**: one weak light at `#BFD8FF`, 5–10% of key strength, from the opposite side, plus optionally a neutral bounce card just out of frame. See §8.4.

### "The render is noisy specifically around the splash"
Filter Glossy 1.0 → Clamp Indirect 8 → Refraction-BSDF-with-manual-Fresnel rebuild (§1.4 Cheat 3) → lower the refraction IOR to 1.15 → more samples last. In that order; the first three are free.

### "Render times exploded when I added the splash"
Transmission bounces above ~32 are almost pure cost. Use §1.4 Cheat 4 (`Is Camera Ray` mix to a cheap Refraction BSDF) and the Ray Depth cutoff instead of raising bounces further. Also confirm the splash mesh is not carrying an unnecessary Subdivision modifier at render level — Mantaflow output is already dense.

---

## 12. Quick reference — every number in one place

| Material | Key values |
|---|---|
| Splash water | Glass BSDF, white, Roughness **0.0**, IOR **1.33** (cheat 1.15–1.25) |
| Bottle PET | Principled, white, Roughness **0.05**, IOR **1.46**, Transmission **1.0**, wall 0.4 mm |
| Amber liquid | Glass IOR **1.35** + Volume Absorption `#FF9A2E`, Density **90**, mesh offset **1 mm** inside |
| Cap | Base `#E8580F`, Roughness **0.35**, Coat **0.15** |
| Label | Roughness **0.15** gloss film, Coat **0.35**/rough 0.08, geometry 0.15 mm thick, 0.3 mm proud |
| Lime flesh | SSS Weight **0.75**, Radius **(0.004, 0.010, 0.003)**, Random Walk, Coat **0.55** |
| Lime rind | Base `#3E8E1E`, Roughness **0.45**, Coat **0.7**, Voronoi pits Scale **220**, Bump **0.6** |
| Droplets (procedural) | Voronoi F1 Scale **55**, ramp black at **0.085**, Bump Strength **0.35**, Distance **0.0006** |
| Backdrop | Emission **4.0**, ramp `#FFB43C` → `#FF7A18` @0.45 → `#C43C00`, B-Spline interpolation |
| Light Paths | Total **32**, Transmission **24**, Transparent **16**, Volume **2**, Filter Glossy **1.0**, Clamp Indirect **8** |

---

## 13. Look-dev sign-off checklist

Before you call shading done, confirm every one of these in a rendered frame (not the viewport):

- [ ] Splash has **bright rims and dark cores** — not uniform grey.
- [ ] Splash reads **silver/white**, not orange, despite the orange environment.
- [ ] Splash shadow on the backdrop is **light and warm**, with visible caustic structure.
- [ ] Bottle silhouette shows **wall thickness** at the edges.
- [ ] Amber liquid is **darker at the bottom than the top**.
- [ ] There is a visible **liquid line** with a meniscus.
- [ ] Label has an **edge highlight** and a soft contact shadow at its top and bottom.
- [ ] Label type is **crisp** at the tightest framing.
- [ ] Bottle is **wetter on the splash side** than the far side.
- [ ] **Droplets break the bottle's silhouette** in the close-up (real geometry, not bump).
- [ ] Fruit **glows where it is backlit** and has a wet coat.
- [ ] Rind **beads** water; flesh carries a **continuous film**. Different behaviours.
- [ ] Backdrop has a **smooth gradient with no banding** and no visible horizon.
- [ ] Backdrop is **lighting the product** (kill it and confirm the product goes dark).
- [ ] The **product's specular is the brightest thing** in frame.
- [ ] Only **two hues plus neutral** are present.
- [ ] Foreground droplets/fruit are **defocused with real bokeh**.
- [ ] Every element is in a **Light Group** or has a **Cryptomatte ID** for comp.
