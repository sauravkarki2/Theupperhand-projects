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

Set **Settings > Shadow Mode = None** in Cycles material settings? No — in Cycles that panel is EEVEE-only. In Cycles, the correct move for a splash is to leave shadows on and let refraction handle it; if the splash casts an ugly black blob, that is the transmission-bounce problem in §1.3, not a shadow setting.

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
