# Hero Frame Forensics — "lets make a beverage commercial in blender 2"

Reverse-engineered from a screen capture of the tutorial showing frame `0163.png`
rendered out to `E:\renders\New Folder(122)\`, with Blender 3.6 LTS behind it and
the Fluid Domain panel fully legible on the right.

This document is the **evidence layer**. Everything asserted here is read directly
off the image or off the Blender UI in the image. Inference is labelled as such.

---

## 1. Direct UI readings (hard evidence)

### 1.1 File / project

| Field | Value |
|---|---|
| Blender build | 3.6 LTS era UI (Layout/Modeling/Sculpting/UV Editing/Texture Paint/Shading/Animation/Rendering/Compositing/Geometry Nodes/Scripting workspace tabs) |
| Blend file | `D:\models\2023\...\water ad1.blend` |
| Render output | `E:\renders\New Folder(122)\0163.png` |
| Output format | **PNG image sequence**, 4-digit frame padding |
| Frame shown | **163** — so the animation is at minimum ~163 frames, realistically 200–250 |
| Title bar shows `*` | unsaved changes at time of capture |

The render is being reviewed in an **external OS image viewer**, not in Blender's
Image Editor. That is the classic "render to disk, flip through frames as they land"
review loop, and it is why the output is a numbered sequence rather than a video file.

### 1.2 Editor layout visible

- Large **Image Editor** (left, showing a greyscale/clay splash preview — an earlier
  or unshaded version of the same sim)
- **Timeline / Dope Sheet** at the bottom with Playback / Keying / View / Marker menus,
  frame ruler showing 0, 10, 20, 30… and a playhead well to the right
- **Outliner** top right
- **Properties → Physics tab** bottom right, expanded

### 1.3 Outliner contents

Partially occluded by the render window, but legible:

```
Scene Collection
├─ Animation            (likely a collection or an animated helper)
├─ Camera
├─ Empty.001
├─ ...e.001             (truncated — likely "Plane.001" / "Sphere.001" / "Cone.001")
├─ Cube.001             ← almost certainly the FLUID DOMAIN
│  └─ Modifiers
├─ mountain dew bottle  ← the product, with modifier + material + physics icons
│  └─ (physics icons: checkbox, camera, render toggles)
├─ ...forces            ← a COLLECTION named something like "forces"
│  ├─ (child 1)
│  ├─ (child 2)
│  └─ (child 3)
```

**Three objects in a `forces` collection.** This is the single most informative
outliner detail — it tells us the splash shape is driven by a *rig of three force
fields*, not by one. See §4.

The product is literally named **"mountain dew bottle"**, confirming the intent:
this is a Mountain Dew–style citrus soda spot.

### 1.4 Physics tab

Buttons row visible: `Force Field | Collision | Cloth | Dynamic Paint |` and
`Soft Body | Fluid | Rigid Body | Rigid Body Constraint`.
**Fluid is enabled and highlighted.** `Type: Domain`.

### 1.5 Fluid Domain settings — read directly off the panel

| Setting | Value in the video | What it means here |
|---|---|---|
| Domain Type | **Liquid** | Not Gas. Mantaflow liquid solver. |
| Resolution Divisions | **100** | A *preview/blocking* resolution. Final beauty would be 200–400. |
| Time Scale | **1.000** | Real-time sim; slow-mo not baked into the solver at this stage. |
| CFL Number | **4.000** | Default. Allows larger timesteps → faster but looser. |
| Use Adaptive Time Steps | **ON** | Timesteps Max **4**, Min **1**. |
| Gravity | **(0, 0, −9.81)** | Real-world gravity, Z-up. Unmodified. |
| Delete In Obstacle | checkbox present | Culls particles trapped inside the bottle. |
| **Border Collisions** | **Front/Back/Right/Left/Top/Bottom ALL UNCHECKED** | **OPEN DOMAIN** — the defining choice. See §3. |
| Simulation Method | **FLIP** | (vs APIC) |
| FLIP Ratio | **0.970** | High = splashy, energetic, low damping. |
| System Maximum | **0** | Uncapped particle count. |
| Particle Radius | **1.000** | Default sampling radius. |
| Sampling | **2** | Particles per grid cell dimension at seeding. |
| Randomness | **0.100** | Slight jitter to break grid artefacts. |
| Particles Maximum | **16** | Resampling ceiling. |
| Particles Minimum | **8** | Resampling floor. |
| Narrow Band Width | **3.000** | Cells of surface band tracked. |
| Fractional Obstacles | checkbox present | Sub-cell obstacle accuracy — matters for a thin bottle wall. |
| Obstacle Distance | **0.500** | Sub-cell offset of the collision surface. |

> **This is Blender's NATIVE Mantaflow liquid domain — NOT the FLIP Fluids
> commercial addon.** The panel layout, the "Resolution Divisions" label, and the
> FLIP Ratio / Narrow Band / Fractional Obstacles grouping are Mantaflow's.
> Anyone recreating this needs no paid addon.

---

## 2. Image forensics — what the render itself tells us

### 2.1 Subject and staging

- **Product:** a translucent PET soda bottle, roughly 500 ml proportions, standing
  upright and near-vertical.
- **Contents:** saturated amber/orange liquid, clearly *transmissive* — it glows
  where light passes through it, brightest in the lower third and through the
  shoulder. That glow is transmitted light, not surface colour.
- **Cap:** opaque orange screw cap, moderate roughness, with a small specular hit
  on its upper-left edge.
- **Neck:** visible thread rings catching a sharp specular.
- **Label:** white wraparound label occupying roughly the middle 40% of the bottle
  height, carrying green leaf/foliage graphics and yellow-green type. The label
  brightness is the **anchor white point** of the frame.
- **Base:** ribbed/fluted petaloid base section, typical of a carbonated PET bottle,
  catching vertical specular streaks.
- **Placement:** bottle centred horizontally, sitting slightly **below frame centre**
  with generous headroom above the cap. Classic product-ad composition — headroom
  reserved for a logo or tagline in the finished spot.

### 2.2 The splash

- A **crown/ring splash** that wraps *around* the bottle: a broad sheet rising and
  flaring outward, breaking the **left and right frame edges**. The bottle is
  visually *inside* the splash, not behind it.
- Water reads **colourless and bright silver-white** against the orange — it is
  almost pure specular and refraction, with essentially no diffuse component.
- The sheet has **thick, bright rims** and **thin, near-transparent membranes**
  between them — the signature of a real FLIP surface mesh with adequate resolution.
- **Hundreds of detached droplets** in the air, of widely varying size, spread well
  beyond the main sheet. Note: at resolution 100 the solver would *not* produce this
  density of fine detached droplets on its own — see §5 inference.
- The splash is **asymmetric**, heavier on the right and rear-left, which is what a
  force-field-driven splash looks like versus a symmetric drop-impact splash.

### 2.3 The fruit

- Multiple **green citrus/apple slices** and **whole green spheres** (limes) flying
  through the frame at different depths and orientations.
- They are **wet** — each carries a sharp specular highlight and a bright rim.
- The slices show **translucency**: the flesh glows where backlit, indicating
  subsurface scattering, not flat diffuse.
- Foreground fruit (bottom-left, bottom-centre) is **clearly defocused** while the
  bottle label is sharp → **real depth of field with the focus plane on the label.**

### 2.4 Backdrop

- A **seamless orange→amber vertical gradient**. No horizon line, no wall/floor seam.
- Brightest around the upper-middle behind the bottle, falling off to a deeper
  burnt orange at the extreme edges and bottom.
- The gradient is smooth enough that it is almost certainly either an **emissive
  plane with a Gradient Texture**, or a **curved sweep lit by two coloured lights** —
  not a flat solid colour.
- The backdrop is also clearly **contributing bounce**: the bottle's shadow side
  and the underside of the splash carry warm orange fill. This is a lit environment,
  not a matte painted behind.

### 2.5 Lighting read

Working backwards from the highlights:

| Light | Evidence |
|---|---|
| **Broad soft key, upper-front-left** | Soft gradient falloff across the cap and shoulder; soft shadow terminator. |
| **Two tall strip/edge lights, rear-left and rear-right** | Long *vertical* specular lines running down both silhouette edges of the bottle and along the splash rims. This is the classic twin-strip bottle rig. |
| **Backlight / kicker through the liquid** | The amber contents glow from within — only transmitted light does that. This is the light that makes the product look like a drink instead of a plastic tube. |
| **Large white reflection card(s)** | The splash's broad bright sheets are reflecting *something large and white*. Water is ~95% specular; it is lit by what it reflects, so there must be big bright emissive planes off-camera. |
| **Low-contrast shadows, no hard cast shadow on backdrop** | Large sources, close in, plus strong backdrop bounce. |

### 2.6 Camera

- Bottle's vertical edges are **near-parallel** with minimal convergence and no
  barrel distortion → **long lens**, estimated **85–135 mm** equivalent.
- Camera height is around the **label's upper edge or slightly below** → mild hero
  low angle.
- Aspect reads **16:9**.
- Visible DOF with the fruit going soft within maybe 10–15 cm of the focus plane →
  fairly wide aperture for a long lens, roughly **f/2.8–f/5.6** at this scale.

---

## 3. Why the OPEN DOMAIN is the key sim decision

All six Border Collisions are **unchecked**. This is deliberate and it is the
single most important solver choice in the shot.

- With borders **on**, the domain is a sealed glass box: liquid hits the wall,
  bounces back, sloshes, and pools. You get an aquarium.
- With borders **off**, liquid that reaches the boundary **leaves and is deleted**.
  Nothing bounces back. Nothing pools.

For an ad splash you want water to fly outward past the frame edge and vanish. You
want no floor pool, no wall slosh, no return waves contaminating the hero moment.
Open borders give you exactly that — and as a bonus, deleting escaped particles
keeps the particle count (and bake time) down.

**Artistic reading:** the splash is meant to feel like it exists only for the
duration of the beauty shot, suspended, with no physical container. Open borders
are how you get "floating splash in a void" instead of "water in a tank".

---

## 4. What the three objects in the `forces` collection are doing

Grouping exactly three force fields into a named collection tells us the splash
silhouette was **art-directed**, not discovered. The most probable rig, in order
of likelihood:

1. **Vortex** — centred on the bottle's vertical axis. This is what makes the sheet
   *wrap around* the bottle rather than blowing straight past it. The rotational
   spiral in the splash is the giveaway.
2. **Force (radial, positive strength)** — at or near the bottle base, pushing
   outward. This is what flares the crown open and drives water off both frame edges.
3. **Turbulence** — low strength, moderate size, to break up the sheet into the
   irregular rims and detached droplets so it doesn't read as a clean CG cone.

A plausible alternative for slot 3 is **Wind** angled upward to lift the sheet, or
**Drag** to decelerate the outer droplets so they hang in air for the hero frame.

All three would be keyframed: strength ramps up at the impact frame, peaks as the
splash blooms, then decays so the water settles rather than accelerating forever.
Keyframing force strength is how you make a sim hit a mark on a specific frame.

---

## 5. Inference: how the fluid was made to follow a curve

The video's own blurb states it teaches **"how to make fluids follow a curve"**.
Combining that with the wrapping splash and the three-force rig, the most likely
construction is:

- A small **Inflow** object (a sphere or plane, low-poly) is constrained to a
  **Bezier curve** that spirals around the bottle, via a **Follow Path** constraint.
- The constraint's **Offset Factor** (or the curve's **Evaluation Time**) is
  keyframed so the emitter travels the spiral over a defined frame range.
- The emitter's **Initial Velocity** is set along its local normal/tangent so the
  liquid is *thrown* outward as the emitter sweeps, rather than dribbling.
- **Use Flow** is keyframed on for a burst of N frames, then off — so you get a
  finite ribbon of water rather than an endless hose.
- The **three force fields** then shape that ribbon into the final crown.

A second, non-exclusive possibility is Mantaflow's **Guides** sub-panel on the
domain (guiding weight / size / velocity source), which lets a moving object's
velocity field steer the liquid. This is the more "correct" tool for literally
guiding fluid along a path, but it is heavier and less commonly taught.

**The droplet density question:** at Resolution 100 the solver alone will not
generate the fine airborne droplet field visible in the render. Either (a) the
final render used a much higher resolution than the 100 shown during the tutorial's
setup phase, (b) **whitewater/spray** was enabled and the spray particles are
instanced as small spheres, or (c) **geometry nodes** scattered extra droplet
instances — which would explain the blurb's mention of "basic geometry nodes".
Most likely: a combination of (a) and (c).

---

## 6. The frame-163 timing clue

Frame 163 shows the splash at or very near its **maximum extent** — the sheet is
fully flared, the fruit is mid-flight through it, and nothing has begun to fall
back yet. That is the **hero frame**.

For a 24 fps spot, frame 163 ≈ **6.8 seconds** in. For 25 fps, ≈ 6.5 s. That places
the money shot roughly two-thirds through a ~10-second commercial, which is exactly
where you'd put it: enough runway to establish the product, enough tail afterwards
for the splash to settle and a logo/endcard to land.

**This is the frame the whole shot is built to deliver.** The camera move, the
force keyframes, the fruit arcs, and the inflow burst are all timed so that
everything peaks simultaneously here. That is the core lesson of an ad sim: you
are not simulating water, you are engineering one specific frame.

---

## 7. Confidence summary

| Claim | Confidence |
|---|---|
| Native Mantaflow liquid, not FLIP Fluids addon | **Certain** — read off the panel |
| Every domain value in §1.5 | **Certain** — read off the panel |
| Open domain / all border collisions off | **Certain** |
| Blender 3.6 LTS | **Certain** — stated by source + UI matches |
| PNG image sequence output, frame 163 | **Certain** |
| Product is a Mountain Dew–style citrus soda bottle | **Certain** — object literally named "mountain dew bottle" |
| Three force fields in a `forces` collection | **Certain** that there are three; **inferred** which types |
| Twin strip/edge light rig | **High** — the vertical specular signature is unambiguous |
| Backlight through the liquid | **High** |
| Emissive gradient backdrop contributing bounce | **High** |
| Long lens 85–135 mm, real DOF | **High** |
| Curve + Follow Path emitter as the "follow a curve" technique | **Medium-High** — consistent with blurb, image, and common practice |
| Whitewater and/or geometry-nodes droplet augmentation | **Medium** |
| Final render used higher resolution than the 100 shown | **Medium-High** |
| Vortex + Force + Turbulence as the specific three fields | **Medium** — reasoned, not observed |
