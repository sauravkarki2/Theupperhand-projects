# Module 01 — Fluid Simulation (Mantaflow Liquid) for a Beverage Commercial

**Target:** Blender 3.6 LTS (settings verified against the source shot), with 4.x deltas flagged in §14.
**Source shot:** "lets make a beverage commercial in blender 2" (wXVuEPuKO_0, 2023-10-24). Amber soda bottle
(`mountain dew bottle`) inside a crown-splash water ribbon, lime slices and green spheres flying through it,
orange gradient backdrop, PNG image sequence output (frame 0163). Outliner shows a `forces` collection with
3 children, an `Animation` object, `Empty.001`, `Cube.001`, and a `Modifiers` object.
**Solver:** native Mantaflow liquid domain. **Not** the FLIP Fluids addon — every panel name and value in the
screenshot is stock Blender.

---

## 0. Ground truth read off the screenshot

These are the values the artist actually shipped. Everything in this module is anchored to them.

| Panel | Setting | Screenshot value |
|---|---|---|
| Fluid | Type | **Domain** |
| Settings | Domain Type | **Liquid** |
| Settings | Resolution Divisions | **100** |
| Settings | Time Scale | **1.000** |
| Settings | CFL Number | **4.000** |
| Settings | Use Adaptive Time Steps | **ON** — Timesteps Maximum **4**, Minimum **1** |
| Settings | Gravity | **(0, 0, −9.81)** |
| Settings | Delete In Obstacle | present (checkbox) |
| Border Collisions | Front / Back / Right / Left / Top / Bottom | **ALL UNCHECKED** (open domain) |
| Liquid | Simulation Method | **FLIP** |
| Liquid | FLIP Ratio | **0.970** |
| Liquid | System Maximum | **0** (unlimited) |
| Liquid | Particle Radius | **1.000** |
| Liquid | Sampling | **2** |
| Liquid | Randomness | **0.100** |
| Liquid | Particles Maximum / Minimum | **16 / 8** |
| Liquid | Narrow Band Width | **3.000** |
| Liquid | Fractional Obstacles | checkbox — Obstacle Distance **0.500** |

**Exactly two things were changed from stock Blender defaults: `Resolution Divisions` (32 → 100) and
`Border Collisions` (all on → all off).** Every other value in the table above is the default a fresh
Mantaflow liquid domain ships with.

That is the single most useful fact in this document. The artist did not tune the solver. One change opened
the domain, one change set the working resolution, and everything else that makes the shot was done with
**domain size, emitter animation, and force fields** — the physics was left alone.

This is the correct order of effort for an ad splash, and this module is weighted accordingly: the solver
sections exist so you understand what the defaults are doing and when to deviate, not because you should
start by turning knobs. If your splash is the wrong shape, the fix is almost never in this panel.

---

## 1. Mental model — what Mantaflow liquid actually is

Mantaflow liquid is a **hybrid FLIP/PIC solver on a uniform voxel grid**.

- The domain object's bounding box is diced into cubic **voxels**. Voxel edge length = `longest domain
  dimension / Resolution Divisions`. Nothing outside the box exists.
- Each voxel stores a **signed-distance level set** (where the water surface is) and a **MAC velocity grid**.
- **FLIP particles** are seeded in and near the water (`Sampling` per cell) and carry velocity between frames.
  Particles are only kept inside a **narrow band** around the surface — the deep interior is grid-only.
- Per substep: particles → grid, solve pressure/incompressibility on the grid, grid → particles, advect.
- The **render mesh is not the simulation.** It is a separate marching-cubes surface rebuilt from the particles
  in the Mesh bake, at its own resolution (`Upres Factor`) and its own `Particle Radius`. Blobbiness, holes and
  crawl are usually *mesh* problems, not *sim* problems. Fix them in the Mesh panel first.
- **Whitewater (spray/foam/bubbles) is also not the simulation.** It is a post-pass that reads the baked data
  cache and emits secondary particles where the surface is energetic. It is baked separately and can be
  re-baked without touching the liquid.

Consequence for scheduling your day: **Data bake** is the expensive, art-directable part. **Mesh** and
**Particles** are cheap re-bakes you iterate on afterwards without re-simulating.

> **WHY THIS, ARTISTICALLY** — a beverage splash is a *shape*, not a physics result. Ninety percent of the
> look comes from where the water is launched from, how fast, and what bends it. The solver settings only
> decide whether that shape survives to the render.

---

## 2. Domain setup

### 2.1 The domain object must be a plain cube

Create it with `Add > Mesh > Cube`. Requirements, in order of how badly they bite:

1. **Apply scale.** `Ctrl+A > Scale`, so `object.scale == (1, 1, 1)`. Mantaflow reads voxel size and effector
   distances in a space that assumes unit scale. A domain left at `scale = (4, 4, 8)` produces distorted
   advection, wrong `Obstacle Distance`, and a sim that silently changes the moment you touch the scale again.
   Resize the domain in **Edit Mode**, or scale in Object Mode and immediately apply.
2. **Zero rotation.** A rotated domain is not supported in any useful way — the solver grid is axis-aligned to
   the object's local axes and rotating it desynchronises the bake from world-space gravity and force fields.
   Rotate the *scene*, never the domain.
3. **8 vertices, no modifiers, no shape keys.** Blender uses the bounding box, but a subdivided or
   non-convex "domain" mesh is a reliable source of confusion later.
4. **Non-cubic is fine.** A 0.6 × 0.6 × 1.1 m box for a standing bottle is correct and efficient — voxels stay
   cubic, `Resolution Divisions` applies to the **longest** axis. What is not fine is *scale* that is not applied.
5. Set viewport display to **Bounds > Box** and turn off render visibility (camera icon) once you are working.

### 2.2 Sizing and placing it around the product

- The domain must contain **the bottle plus the entire volume the splash will ever occupy**, including the
  frames where it is falling away out of frame. Anything crossing the border on an open domain is **deleted**,
  permanently, at bake time.
- But make it **as tight as you can get away with**. Voxel size is `longest_axis / resolution`. A domain twice
  as long needs twice the resolution for identical detail, which is 8× the memory and roughly 16× the bake.
- Practical for a 25 cm bottle hero: bottle centred, domain roughly **0.8 m wide × 0.8 m deep × 1.3 m tall**,
  bottom sitting a little below the bottle base, top well above the crown of the splash.
- Look through the **render camera** and shrink the domain until the splash silhouette just clears frame. If a
  side of the domain is off-camera anyway, cut it back — free performance.
- Leave the domain **stationary**. Do not animate or parent it. Moving a domain invalidates the cache.

### 2.3 Domain scale vs "real world size" — the most important artistic dial

Mantaflow simulates in **metres**, with **gravity fixed at −9.81 m/s²**. There is no "real world size" override
for liquid — the domain object's actual dimensions *are* the physical scale.

This means **domain size is a look control, not just a container.**

| Domain longest dimension | Reads on screen as |
|---|---|
| 0.2 – 0.5 m | Tight, fast, fizzy — droplets, condensation, pour into a glass |
| **0.8 – 1.5 m** | **Product-scale hero splash. Correct for a bottle crown splash.** |
| 3 – 6 m | Heavy, slow, syrupy — reads as a large body of water in slow motion |
| 10 m+ | Ocean/miniature. Water looks like it weighs a tonne, sheets do not break up |

If your splash looks lazy and rubbery, your domain is too big. If it looks like a spraying garden hose with no
weight, it is too small. **Fix the look by resizing the domain before touching FLIP Ratio.**

> **WHY THIS, ARTISTICALLY** — big-brand beverage splashes are shot with real water at real scale and then
> **overcranked** (high-speed camera). They read heavy and slow *because of the frame rate*, not because the
> water is large. Reproduce that: keep the domain physically honest at ~1 m, keep `Time Scale = 1.0`, and buy
> your slow motion in the timeline (§3.4), not in the solver.

### 2.4 Border Collisions — why ALL OFF is correct here

`Border Collisions` turns each of the 6 domain faces into a solid wall.

| State | Behaviour | Use for |
|---|---|---|
| All ON | Sealed tank. Liquid bounces off invisible walls and sloshes back into shot | Glass fills, tanks, pools |
| **All OFF (this shot)** | **Open box. Anything that touches a face is deleted and never returns** | **Ad splashes, pours, throws** |
| Bottom only | Invisible floor, open sides | Water hitting a surface where you do not want a floor mesh |

For a crown splash the open domain is the only correct choice: droplets that leave frame must **leave**. With
borders on you get a visible, physically nonsensical bounce off nothing, water piling in the lower corners of
the box, and a slow drift of the whole splash back toward centre. It also wastes solver time on liquid you will
never see.

Note the two consequences:

- **There is no floor.** Liquid falls out the bottom of the box and vanishes. If you want it to pool or
  splash off a surface, you need a real **effector object**, not a border.
- **You cannot recover deleted liquid.** Size the domain generously in the direction the splash is thrown.

Python names: `use_collision_border_front / _back / _left / _right / _top / _bottom`.

---

## 3. Every setting in the screenshot

### 3.1 Settings panel

| Setting | Shot value | What it does | Sane range | Raise it when | Lower it when |
|---|---|---|---|---|---|
| **Resolution Divisions** | 100 | Voxels along the domain's longest axis. The master detail/cost dial | 64–120 preview, 200–400+ final | Final render | Blocking |
| **Time Scale** | 1.000 | Multiplies simulated time per frame. 0.5 = half speed | 0.2–1.0 | Never above 1.0 without raising timesteps | You want in-solver slow motion — see 3.4 |
| **CFL Number** | 4.000 | Max distance (in voxels) fluid may travel per substep before the solver subdivides the step | 1.0–4.0 | Sim is slow but stable and you want speed | Sim explodes, jitters, or leaks through obstacles → 2.0, then 1.0 |
| **Use Adaptive Time Steps** | ON | Lets the solver pick substep count per frame instead of a fixed one | Always ON | — | — |
| **Timesteps Maximum** | 4 | Ceiling on substeps per frame | 4–16 | Fast liquid, thin obstacles, explosions → 8 or 16 | Bake too slow and stable |
| **Timesteps Minimum** | 1 | Floor on substeps per frame | 1–2 | Jitter on slow frames | — |
| **Gravity** | (0, 0, −9.81) | World gravity for this domain, independent of scene gravity | Keep real | — | Fake low-g "hero float" — try −4 for a dreamier hang time |
| **Delete In Obstacle** | checkbox | Kills liquid particles that end up inside an effector volume | ON for closed colliders | Liquid is trapped/leaking inside the bottle | You are using a thin/planar collider and losing water |

**CFL 4 + adaptive 1–4 explained.** CFL is the stability contract: no parcel of fluid may cross more than
`CFL` voxels in a single substep. The solver estimates the fastest velocity in the domain, divides, and asks
for that many substeps — then clamps the answer to `[Timesteps Min, Timesteps Max]`. With CFL 4 and a max of 4
you are telling Blender *"be fast and permissive; I accept that a genuinely violent frame will be under-solved."*

That is fine for a splash that lives for 60 frames and is half-hidden in whitewater. It is not fine when:

- liquid **tunnels through the bottle** (a particle crossed the wall inside one substep) → CFL **2.0**, max timesteps **8**;
- the sim **explodes** into a spray of stray particles → CFL **1.0–2.0**, max timesteps **8–16**;
- you are using **strong force fields** (§7), which push velocities far above what gravity alone produces.

Cost is close to linear in substeps: CFL 4 → 2 roughly doubles bake time.

**Gravity −9.81 and the Z-up assumption.** Keep it real. Gravity is what makes the crown fall back and form
the classic thick lip; faking it low makes the splash hang like foam. If you want hang time, buy it with
Time Scale or frame rate, not by lying about g.

### 3.2 Liquid panel

| Setting | Shot value | What it does | Sane range |
|---|---|---|---|
| **Simulation Method** | FLIP | FLIP vs APIC. FLIP = energetic, noisy, splashy. APIC = swirlier, more stable, less chaotic | FLIP for splashes; APIC for smooth vortices/whirlpools |
| **FLIP Ratio** | 0.970 | Blend between PIC (0 = smooth, damped, viscous-looking) and FLIP (1 = energetic, noisy, unstable) | 0.90–0.99 |
| **System Maximum** | 0 | Hard cap on total FLIP particles. 0 = unlimited | 0, or set a real cap as a RAM safety net at high res |
| **Particle Radius** | 1.000 | Radius of each FLIP particle in voxel units — how much volume a particle "counts as" | 1.0–2.5 |
| **Sampling** | 2 | Particles seeded per grid cell (per axis-ish). The single biggest particle-count multiplier | 2 (default), 3 for hero detail |
| **Randomness** | 0.100 | Jitter on initial particle placement | 0.1–0.3 |
| **Particles Maximum** | 16 | Resampling ceiling — cells with more than this get pruned | 16–32 |
| **Particles Minimum** | 8 | Resampling floor — sparse cells get re-seeded | 8–16 |
| **Narrow Band Width** | 3.000 | Thickness in voxels of the particle band kept around the surface | 3–5 |
| **Fractional Obstacles** | on | Sub-voxel obstacle representation — obstacles no longer snap to whole voxels | ON for any product shot |
| **Obstacle Distance** | 0.500 | How far (in voxels) fluid is held off an obstacle surface | 0.2–1.0 |

**FLIP Ratio 0.97 — the splashiness dial.** This is *the* look control inside the Liquid panel.

| Value | Result |
|---|---|
| 0.80–0.90 | Damped, cohesive, honey-ish. Sheets stay whole, few droplets. Reads as syrup or cream |
| 0.93–0.95 | Controlled. Splashes but does not shatter. Good for a *pour* |
| **0.97 (default, this shot)** | **Water. Sheets thin out and break into droplets. The crown-splash look** |
| 0.98–0.99 | Very energetic, very noisy. Great droplets, higher risk of stray flyers and instability |
| 1.00 | Pure FLIP. Do not — the solver loses its damping and will misbehave |

For a beverage ad you want the droplets: they catch specular highlights and are what makes the frame read as
"cold, fresh, wet." 0.97 is right. If you need it *more* aggressive, go 0.98 **and** drop CFL to 2, because
higher energy means higher velocities means more tunnelling risk.

**Particle Radius 1.0.** This is the *simulation* particle radius (there is a second, separate one in the Mesh
panel — do not confuse them). It controls how much space each particle claims when reconstructing the level
set. Raise it toward 1.5–2.0 if the sim **loses volume** — thin streams vanishing, water evaporating over the
shot. Lower it (or keep 1.0) when you want maximum detail and thin, ripped sheets. 1.0 is correct here because
the splash is a thin ribbon and volume loss over 60 frames is not a concern.

**Sampling 2.** Particles per cell. Going 2 → 3 gives noticeably finer breakup and thinner sheets — and roughly
**triples** particle count, memory and bake time. Keep 2 through art direction. Consider 3 only on the final
bake, and only if the render still looks mushy after you have already raised Resolution Divisions (raising
resolution is almost always the better spend).

**Randomness 0.1.** Without jitter, particles seed on a perfect lattice and you get faint grid-aligned patterns
in the surface and in the way sheets tear. 0.1 breaks that up for free. 0.2–0.3 adds a little extra organic
noise to droplet distribution; above that you start seeding particles into places they should not be.

**Particles Max 16 / Min 8.** Per-cell resampling bounds. Each substep, cells with fewer than `Min` particles
get re-seeded and cells with more than `Max` get pruned. This is what keeps particle count from exploding where
the fluid compresses, and keeps holes from opening where it stretches. Raise both proportionally (32/16) at very
high resolution if you see the surface thinning out in fast-stretching regions. Leaving them at 16/8 is right
for a 100–300 res product shot.

**Narrow Band Width 3.0.** How many voxels deep the FLIP particle band extends inward from the surface. The
interior below that is solved on the grid only. For a splash — which is nearly *all* surface — 3 is plenty and
cheap. Raise to 4–5 if you have a deep body of water (a filled glass) and you see the deep liquid behaving
mushily or losing volume. Every extra voxel of band width costs real particles and real memory.

**Fractional Obstacles + Obstacle Distance 0.5 — the bottle setting.** Without fractions, an obstacle is
rasterised to whole voxels: a bottle at res 100 becomes a lumpy staircase and liquid either leaks through the
thin parts or catches on invisible stair steps. `Fractional Obstacles` gives sub-voxel accuracy so a curved
bottle wall is a curved wall. **Turn this on for every product shot.**

`Obstacle Distance` (0.5 voxels) is the offset the solver holds fluid off the obstacle surface.

- **Raise toward 0.8–1.0** if liquid still leaks through the bottle, or sticks/streaks unnaturally on it.
- **Lower toward 0.2–0.3** if you can see a visible gap — a halo of empty space between the water and the glass
  — which is the classic tell of too much obstacle distance at low resolution.
- 0.5 is the balanced default and is correct while the water is *wrapping* the bottle rather than sheeting
  down it.

**System Maximum 0.** Unlimited. Set this to a real number (e.g. 20,000,000) before a big overnight bake if you
are memory-constrained; the sim will degrade rather than OOM-kill Blender at 3am.

### 3.3 What is NOT in the screenshot but sits nearby

- **Adaptive Domain** — gas only. It does not exist for liquid. Do not go looking for it.
- **Diffusion** panel — Viscosity Base/Exponent, Surface Tension, and presets (Water / Oil / Honey). Leave at
  water. Surface tension above ~0.1 will noticeably slow the bake and turn droplets into beads; a *tiny* amount
  (0.05) can help droplets stay round for macro shots, but it is a stability risk.
- **Viscosity** (separate checkbox panel) — for genuinely thick liquids. Off for soda. Turning it on is a
  large bake-time increase.

### 3.4 Slow motion: do it in the timeline, not the solver

Three ways to get hero slow-mo, best first:

1. **Simulate at 1.0, render at high fps.** Set scene fps to 60 or 120, bake and render, then interpret the
   footage at 24 fps in the edit. Physics stays correct, motion blur stays correct, and you get true overcranked
   footage. Costs more frames of bake.
2. **`Time Scale` 0.4–0.6.** Cheap and effective. The solver takes smaller time slices per frame so it also
   gets *more accurate* — but the physics of breakup change slightly (surface tension and gravity get relatively
   more time to act per frame), so the splash reads a little more cohesive.
3. **Retime the cache in the modifier's frame offset.** Fiddly, causes stepping. Last resort.

Never raise Time Scale above 1.0 without also raising `Timesteps Maximum` — you are asking the solver to cross
more voxels per frame with the same substep budget, which is exactly how sims explode.

---

## 4. Resolution strategy

### 4.1 Why 100 is a blocking value

At res 100 on a ~1 m domain, a voxel is **1 cm**. A 1 cm voxel cannot resolve a droplet, a thin sheet edge, or
the lip of a crown splash. What res 100 *can* do, and does well, is answer the questions that matter first:

- Does the ribbon wrap the bottle in the right place?
- Does it arrive at the right frame?
- Does the crown bloom and fall at the right rhythm?
- Does anything leak through the bottle or fly out of frame?

Those are staging questions and they are resolution-independent-*ish*. So: **100 for the art direction loop.**

### 4.2 The cost curve

Voxel count scales with res³. Substep count scales with velocity/voxel-size, i.e. roughly res. So **bake time
scales ≈ res⁴** and **memory ≈ res³**.

| Resolution | Relative voxels | Relative memory | Relative bake time | Role |
|---|---|---|---|---|
| 64 | 0.26× | 0.26× | 0.17× | Ultra-fast staging |
| **100** | **1×** | **1×** | **1×** | **Blocking / art direction (this shot)** |
| 150 | 3.4× | 3.4× | 5× | Confirm bake |
| 200 | 8× | 8× | 16× | Minimum credible final for a wide product shot |
| 300 | 27× | 27× | 81× | Hero final. Droplets read properly |
| 400 | 64× | 64× | 256× | Macro / close-up hero. Overnight-to-multi-day, big disk |

Rules of thumb that survive contact with reality:

- **Doubling resolution = 8× disk, ~16× time.** Plan the disk before you plan the time.
- Measure, do not guess. Bake frames 1–10 at your target resolution, look at the cache folder size, multiply
  by frame count, and add 40%. §11 has the numbers.
- If a res-300 bake will not fit in the schedule, **shrink the domain** instead of dropping resolution. Same
  voxel size, fewer voxels.

### 4.3 Changing resolution changes the SIMULATION, not just the detail

This is the single most misunderstood thing about Mantaflow and it has a hard workflow consequence.

Resolution changes voxel size, which changes: the pressure solve, where sheets are thin enough to tear, how
many particles exist, how the obstacle is rasterised, and how many substeps CFL demands. **A res-300 bake is a
different simulation from a res-100 bake, not a sharper one.** Your ribbon will wrap slightly differently, the
crown will bloom a few frames off, and droplets will fly to different places.

Workflow implications:

1. **Art-direct at low res, but re-check at final res.** Never go straight from a 100 preview to a 400 overnight
   final. Do a mid-res confirm bake (§11) and expect to nudge timings by a few frames.
2. **Lock your resolution as early as you can.** Once you like a bake, treat resolution as frozen; change
   emitters and forces, not resolution.
3. **Higher resolution generally means *more* breakup and *thinner* sheets**, because the solver can now resolve
   features it previously smoothed over. If your preview looks slightly too cohesive, that is normal — it will
   loosen up. If your preview already looks shredded, the final will look like mist.
4. Timing shifts up-res are usually small (1–5 frames on a 60-frame splash) but real. Keyframe your camera and
   your fruit *after* the final bake, or be ready to re-time them.

---

## 5. Inflow and flow objects

Any mesh can become a flow object: `Physics > Fluid > Type: Flow`, `Flow Type: Liquid`.

### 5.1 Flow Behavior

| Behavior | What it does | Use in this shot |
|---|---|---|
| **Inflow** | Continuously *adds* liquid where the mesh is, every frame it is enabled | The travelling emitter that draws the ribbon |
| **Outflow** | Deletes any liquid entering it | Kill box under the bottle; cleaning up water you do not want in frame |
| **Geometry** | Converts the mesh to liquid **once**, on the frame the sim starts, then the mesh is inert | A pre-made blob or a "column" of water that gets thrown; the liquid inside the bottle at frame 1 |

**Inflow vs Geometry vs both.** The classic ad splash is *both*:

- a **Geometry** object gives you an instant, controllable mass of liquid at frame 1 (a torus around the bottle,
  a sphere below it, a slab that gets launched) — deterministic, no ramp-up;
- an **Inflow** feeds the ribbon over time so the wrap has continuity and does not thin out.

Geometry flow objects only convert on the domain's **cache start frame**. If nothing appears, your start frame
is wrong or the object is outside the domain.

### 5.2 Key flow settings

| Setting (UI) | Python | Default | Notes |
|---|---|---|---|
| Flow Type | `flow_type` | `'SMOKE'` | Set to `'LIQUID'` |
| Flow Behavior | `flow_behavior` | `'GEOMETRY'` | `'INFLOW'` for the emitter |
| Use Flow / Use Inflow | `use_inflow` | True | **Keyframe this.** The burst switch |
| Surface Emission | `surface_distance` | 1.5 | Voxels of liquid emitted around the surface. Raise for a fatter stream |
| Volume Emission | `volume_density` | 0.0 | Set to 1.0 to fill a closed mesh's interior with liquid |
| Is Planar | `use_plane_init` | False | For flat/open emitter meshes (a plane or disc). Fixes "nothing emits from my plane" |
| Subframes | `subframes` | 0 | **Critical for moving emitters.** See §5.4 |
| Initial Velocity | `use_initial_velocity` | False | Master switch for the two below |
| — Normal | `velocity_normal` | 0.0 | Velocity along the emitter's face normals. m/s |
| — Random | `velocity_random` | 0.0 | Random jitter added to initial velocity |
| — Initial Velocity X/Y/Z | `velocity_coord` | (0,0,0) | Additional velocity vector, **world space** |
| Source | `flow_source` | `'MESH'` | `'PARTICLES'` to emit from a particle system |

### 5.3 Bursting liquid for N frames then stopping

Keyframe `use_inflow` (the "Use Flow" checkbox). Because it is a boolean, Blender writes CONSTANT
interpolation automatically — it snaps.

```
Frame 1   : use_inflow = False    (nothing yet)
Frame 12  : use_inflow = True     (burst starts)
Frame 34  : use_inflow = True
Frame 35  : use_inflow = False    (burst ends; existing liquid keeps flying)
```

The liquid already emitted is **not** deleted when you switch off — it continues under gravity and forces.
This is the entire trick behind a splash that blooms and then falls away cleanly: emit for ~20–25 frames,
stop, let the last 30–40 frames be pure ballistics.

You can also ramp with `surface_distance` (keyframable, float) for a soft fade-in of stream thickness, which
avoids the hard "a wall of water appeared" pop on frame 12.

> **WHY THIS, ARTISTICALLY** — a continuous inflow reads as a *hose*. A finite burst reads as an *impact*.
> The shape you want is the one water makes after it has stopped being pushed.

### 5.4 Initial velocity is how you seed a splash — and moving the emitter is NOT

**Gotcha, and it is the important one for §6:** a moving Mantaflow inflow does **not** automatically impart its
own motion to the liquid. Fly an emitter around a bottle at 5 m/s and, without initial velocity set, you get a
trail of water gently dropping out of it under gravity — a dribbling smoke trail, not a ribbon.

So:

- Turn on **Initial Velocity**.
- Use **Normal** as the primary dial and build your emitter so its **face normals point in the direction you
  want the water thrown** — a disc, a shallow cone, or a single-sided plane. Normal velocity travels with the
  object's rotation, so on a curve-following emitter it stays **tangential automatically**. This is the whole
  reason the curve technique works.
- Use **Initial Velocity X/Y/Z** only for a constant world-space push (e.g. a global upward bias of `+2` on Z to
  loft the ribbon), because it does **not** rotate with the object.
- **Random** 0.2–0.5 breaks up the stream so it does not look extruded.

Rough velocity scale for a ~1 m domain:

| Normal velocity | Look |
|---|---|
| 0.5–1.5 | Gentle pour |
| **2–5** | **Thrown stream. Correct for a wrapping ribbon** |
| 6–12 | Jet / high-pressure spray. Needs CFL 2 and timesteps 8 |
| 15+ | Will tunnel through the bottle unless you drop CFL |

**Subframes** (`flow_settings.subframes`) fixes the "beads on a string" artefact where a fast emitter deposits
discrete blobs, one per frame, instead of a continuous stream. Set it to **2–4** for a moving emitter, **6–8**
for a very fast one. Cost is roughly linear. This is the #1 cause of stuttery, sausage-link fluid streams and
almost nobody sets it.

---

## 6. THE CURVE-GUIDED FLUID TECHNIQUE

This is the headline of the video: *"making fluids follow a curve."* There are three ways to do it in stock
Blender. Two are practical, one is a trap.

### 6.1 The three candidate implementations

**(a) Emitter on a Follow Path constraint — the one you should build.**
A small inflow object is constrained to a Bezier curve drawn as a spiral around the bottle, animated along it,
throwing liquid tangentially via Initial Velocity → Normal. The *emitter* follows the curve; the water is
launched off it and then behaves ballistically.

**(b) Force fields shaping an existing stream.**
Empties carrying Vortex / Force / Turbulence fields, placed around the bottle, bending water that is already
in flight. Does not by itself make water follow a path — it *biases* it. Essential as a second layer.

**(c) Mantaflow Guides (domain `Guides` sub-panel).**
Real velocity guiding: the domain's `Guides` panel takes a velocity source (`Effector` objects with
`Effector Type: Guide`, or a second, lower-res `Domain` set as Guide Parent) and blends that velocity field into
the solve with `Weight` (`guide_alpha`), `Size` (`guide_beta`) and `Velocity Factor`. This is powerful and it
genuinely does force liquid along a path.

### 6.2 Which one did this video most likely use — and why

**(a) plus (b).** Confidence: high on (a)+(b), low on (c).

Evidence and reasoning:

1. **Every solver setting in the screenshot is stock default.** Guides is a solver feature and a fussy one —
   an artist using it would almost certainly have been tuning Weight/Size/Velocity Factor, and would likely have
   dropped CFL for stability. Nothing was touched.
2. **The outliner shows a `forces` collection with exactly 3 children.** That is the signature of (b): three
   force-field empties. Mantaflow Guides driven by effectors would put those objects in the modifier stack as
   Fluid *Effectors*, not naturally in a collection called "forces."
3. **The `forces` collection name matters technically.** The fluid domain has a `Field Weights` panel with an
   **Effector Collection** slot (`domain_settings.effector_weights.collection`). Dropping a collection there
   restricts which force fields in the scene affect this domain. Naming a collection `forces` and having exactly
   3 members is precisely how you'd set that up. This is very likely what that collection is for.
4. **The video's own description pairs "making fluids follow a curve" with "using force fields."** Two separate
   techniques, listed separately — consistent with a curve-driven *emitter* plus force fields shaping the result,
   not one unified guiding system.
5. `Empty.001` in the outliner is consistent with a Follow Path / parent rig empty. `Animation` is plausibly the
   emitter or the object carrying the path animation.

**Where I am genuinely uncertain:** whether the curve drives an *emitter* (a) or drives a **Guide effector**
swept along the path (a hybrid of a and c). The hybrid is a real, known technique and would also explain three
objects. But (a) is far more common in tutorials, far cheaper to bake, and far more art-directable — and it
matches the untouched solver settings. Build (a); §6.6 has the (c) recipe if you want to try the other road.

### 6.3 Step-by-step: curve-driven emitter (the build)

**Step 1 — Draw the path.**
`Add > Curve > Bezier Circle`. Scale it a little larger than the bottle (bottle radius ~0.05 m → circle radius
~0.12 m). In Edit Mode, pull the control points up in Z as you go round so the circle becomes a **rising
spiral** — 1 to 1.5 turns, starting below the bottle's midpoint and finishing above its shoulder. Add a short
tail that flies off away from camera so the ribbon has somewhere to exit to.

Curve object settings that matter:
- `Object Data > Shape > Resolution Preview U`: **24–32**. A low-res curve makes the emitter step and jitter.
- Do **not** give the curve a bevel; it is a path, not geometry. Leave it unrendered.
- **Apply scale on the curve too** (`Ctrl+A > Scale`) — Follow Path offsets misbehave on scaled curves.

**Step 2 — Build the emitter.**
`Add > Mesh > Circle`, radius **0.02–0.035 m**, fill type **N-Gon**. Rotate it in *Edit Mode* so its normal
points along **+Y** (the Follow Path forward axis). Verify with overlay `Face Orientation` / normals display —
the normal direction is what throws the water, so get it right.

Why a disc and not a sphere: a disc's normals all point one way, so `velocity_normal` becomes a clean
directional jet. A sphere sprays in all directions and gives you a cloud, not a ribbon.

**Step 3 — Constrain the emitter to the curve.**
On the emitter: `Object Constraint Properties > Add > Follow Path`.

| Constraint field | Value | Why |
|---|---|---|
| Target | the spiral curve | — |
| **Follow Curve** | **ON** | Rotates the emitter to face along the path. This is what keeps the throw tangential |
| Forward Axis | **Y** | Must match the axis your disc normal points down |
| Up Axis | Z | — |
| **Fixed Position** | **ON** | Switches control to `Offset Factor`, a clean 0→1 range |
| Offset Factor | keyframed | 0.0 at the start frame, 1.0 at the end frame |

**Important:** with Follow Path, the emitter's own `location` acts as an **offset from the path**. Set the
emitter's location to `(0,0,0)` (`Alt+G`) or it will float away from the curve. If you need it offset radially,
do it in Edit Mode or via a parent empty — *this is very likely what `Empty.001` in the outliner is.*

**Step 4 — Animate along the path.**
Keyframe `Offset Factor`:

```
Frame 10 : offset_factor = 0.00
Frame 40 : offset_factor = 1.00
```

Then open the Graph Editor and shape the F-curve. **Do not leave it linear.** An ease-in that ramps to a fast
middle and holds is what makes the ribbon *whip* around the bottle. A linear pass reads mechanical.

(Alternative: leave `Fixed Position` off and animate the curve's own `Eval Time` — `curve.data.eval_time`, with
`curve.data.path_duration` set. Same result, one more level of indirection. `Offset Factor` is easier.)

**Step 5 — Make it a fluid inflow.**

| Setting | Value |
|---|---|
| Type | Flow |
| Flow Type | Liquid |
| Flow Behavior | **Inflow** |
| Use Flow | **keyframed** — off, on at frame 12, off at frame 34 |
| Surface Emission | 1.5 (raise to 2.5 for a fatter ribbon) |
| **Subframes** | **3** (raise to 6 if the stream beads) |
| Initial Velocity | ON |
| — **Normal** | **3.0** (range 2–5) |
| — Random | 0.3 |
| — Initial Velocity Z | +1.0 (optional loft so the ribbon rises as it wraps) |

**Step 6 — Time the emitter against the burst.**
The emitter should already be moving *before* `Use Flow` turns on, and should keep moving after it turns off.
Water only appears while the flow is on, but you want the motion to be at speed at the moment of the burst so
the first water out is already travelling.

**Step 7 — Add the forces (§7) and bake at res 100.**

### 6.4 What that gives you, and what it does not

You get a **ribbon of water thrown tangentially in a helix around the bottle**, arriving and departing on your
schedule. What you do **not** get is water that *stays* on the path — once emitted, it is ballistic. Gravity
pulls the tail of the ribbon down while the head is still climbing. That is the correct, desirable look: a real
splash is exactly this.

If you want the ribbon to hold its arc longer, that is what the force fields are for.

### 6.5 The 3 objects in the `forces` collection — most likely contents

| # | Object | Field | Role in this shot |
|---|---|---|---|
| 1 | Empty at bottle centre, vertical | **Vortex** | Spins the water *around* the bottle axis. This is what makes the ribbon wrap rather than fall straight past |
| 2 | Empty at bottle centre | **Force**, negative strength | Repels water off the bottle so it bulges outward into a crown rather than sticking to the glass |
| 3 | Empty in the splash volume | **Turbulence** | Breaks the ribbon into strands and droplets so it does not read as extruded tube |

Alternates for #3: **Wind** (a constant directional push to blow the splash toward or away from camera — very
common for the "spray coming at you" look), or **Drag** (to settle the splash into a controlled hang at the end
of the shot). Assign the whole collection into `Field Weights > Effector Collection` on the domain so nothing
else in the scene leaks into the sim.

### 6.6 If you want to try real Mantaflow Guides (option c)

On the **domain**, `Fluid > Guides` (`use_guide = True`):

| Setting | Python | Meaning | Start value |
|---|---|---|---|
| Velocity Source | `guide_source` | `'EFFECTOR'` (guide effector objects) or `'DOMAIN'` (a second domain) | `'EFFECTOR'` |
| Guide Parent | `guide_parent` | The other domain object, when source is `'DOMAIN'` | — |
| Weight | `guide_alpha` | How strongly guiding overrides the solve. Higher = more obedient, less natural | 2.0 |
| Size | `guide_beta` | Spatial extent over which guide velocity is blended | 5 |
| Velocity Factor | `guide_vel_factor` | Multiplier on the guide velocity | 2.0 |

Then make a mesh (e.g. a sphere) a **Fluid Effector** with `Effector Type: Guide`, set its `Velocity Factor`
and `Guide Mode` (`Maximum` / `Minimum` / `Override` / `Averaged`), and animate that object along your curve
with the same Follow Path rig. The moving guide drags the liquid with it.

Honest assessment: it works, it is fiddly, it slows the bake, and `Weight` past ~4 makes water look like it is
on rails. Reach for it only when a curve-driven *emitter* genuinely cannot produce the shape — e.g. you need
existing water to be pulled along a path rather than new water thrown along one.

---

## 7. Force fields in depth

Add with `Add > Force Field > …`, or select an Empty and enable `Physics > Force Field`. Mantaflow liquid
responds to force fields; smoke and liquid both read the domain's `Field Weights`.

### 7.1 The five that matter

| Field | What it does to liquid | Use it for |
|---|---|---|
| **Force** | Pushes radially out from (positive) or pulls in toward (negative) the empty | Repelling water off the product; a "blast" origin; gathering a splash into a tight core |
| **Vortex** | Rotates fluid around the empty's local Z axis | **The wrap.** Spiral ribbons, whirlpools, swirl around a bottle |
| **Wind** | Constant push along the empty's local +Z | Blowing spray toward camera; biasing the splash to one side of frame |
| **Turbulence** | Procedural noise field that varies in space and time | Breaking sheets into strands and droplets; killing the "CG extrusion" look |
| **Drag** | Damps velocity — a viscosity you can localise and animate | Settling a splash into a hero hang; stopping stray flyers; slowing water near camera |

Also present but rarely useful here: Magnetic, Harmonic, Charge, Lennard-Jones (particle-only in practice),
Texture (interesting for hand-shaping flow with an image, expensive), **Curve Guide** — *note: Curve Guide
force fields drive particle systems and soft bodies, **not** Mantaflow liquid. Do not build the curve technique
on a Curve Guide field; it will do nothing to your water.*

### 7.2 The controls

| Control | Python | What it does |
|---|---|---|
| **Strength** | `field.strength` | The magnitude. Sign matters on Force (negative = attract) |
| **Flow** | `field.flow` | Converts the field toward a *velocity target* rather than an acceleration. Fluid is pulled to move **at** the field's speed rather than being accelerated forever. Values 1–5 give much more controllable, less runaway motion |
| **Noise / Seed** | `field.noise`, `field.seed` | Adds variation. On Turbulence, `size` is the more important dial |
| **Max Distance** | `field.use_max_distance`, `field.distance_max` | Hard cutoff radius. **Always enable this.** |
| **Min Distance** | `field.use_min_distance`, `field.distance_min` | Full-strength radius before falloff begins |
| **Falloff Type** | `field.falloff_type` | `SPHERE` (radial), `TUBE` (cylindrical around local Z — ideal for a bottle), `CONE` |
| **Falloff Power** | `field.falloff_power` | How fast strength drops with distance. 0 = no falloff, 2 = inverse-square-ish |
| **Shape** | `field.shape` | `POINT`, `LINE`, `PLANE`, `SURFACE`, `EVERY_POINT`. `LINE` on a Vortex/Force is excellent around a bottle — the field emanates from the empty's Z axis rather than a single point |

### 7.3 Restricting which fields hit the sim — the `forces` collection

On the **domain**: `Fluid > Settings > Field Weights`:

- `effector_weights.collection` — **Effector Collection.** Set it to your `forces` collection and only those
  objects influence this domain. Everything else in the scene (the fruit's fields, another sim's fields) is
  ignored. This is what makes a scene with multiple sims tractable.
- Per-type multipliers: `effector_weights.force`, `.vortex`, `.wind`, `.turbulence`, `.drag`, `.gravity`,
  and `.all` (global). **These are keyframable**, which is a second, cleaner place to animate influence: leave
  each field's own Strength as a fixed "look" value, and animate the domain's weight for a global bloom.

Fields also only affect the sim if they are **in the same scene** and **in a visible/enabled collection**
(a collection excluded from the View Layer is excluded from the sim).

### 7.4 Recipes

**A wrapping ribbon (this shot).**

| Field | Placement | Strength | Flow | Falloff | Max Dist |
|---|---|---|---|---|---|
| Vortex | Empty at bottle centre, local Z = bottle's up axis, Shape `LINE` | 4–8 | 2 | Tube, power 1 | 0.35 m |
| Force (negative) | Same empty position, Shape `LINE` | −1 to −3 | 1 | Tube, power 2 | 0.2 m |
| Turbulence | Empty in the splash volume | 1–3, `size` 0.5–1.5 | 0 | Sphere, power 0 | 0.5 m |

The Vortex does the wrapping; the negative Force keeps the water from collapsing onto the glass; the Turbulence
stops it looking like a machined tube. Keep total strength modest — the ribbon's shape should come mostly from
the emitter path, with the fields *finishing* it.

**A chaotic burst.** One strong positive **Force** (strength 15–40, Max Distance small, falloff power 2) fired
for 2–4 frames at the moment of impact, plus **Turbulence** at strength 5–10, size 0.3. Everything flies outward
and shatters. Keyframe the Force strength to zero immediately after — a sustained blast just deletes your splash
out of the domain.

**A crown splash.** Do **not** build the crown with force fields. A crown is what water does naturally when a
mass hits a surface: a `Geometry` blob or fast downward inflow striking an effector plane, at FLIP ratio 0.97,
res 200+. Use a *weak* upward **Wind** (strength 1–3) only to hold the crown open a few frames longer, and a
**Drag** (strength 1–2) on the outer radius to stop the tips flying off frame.

### 7.5 Keyframing the bloom-then-settle

The single most useful animation in the whole module:

```
Frame 10 : Vortex.strength     = 0     Turbulence.strength = 0    Drag.strength = 0
Frame 16 : Vortex.strength     = 7     Turbulence.strength = 2.5  Drag.strength = 0
Frame 34 : Vortex.strength     = 7     Turbulence.strength = 2.5  Drag.strength = 0
Frame 46 : Vortex.strength     = 1     Turbulence.strength = 0.5  Drag.strength = 3
Frame 60 : Vortex.strength     = 0     Turbulence.strength = 0    Drag.strength = 4
```

Ramp up with the burst, hold through the wrap, then bleed the shaping fields out and bring **Drag** in to
settle. The result: the splash blooms, holds a readable hero silhouette, and then decelerates into a graceful
fall instead of continuing to churn.

> **WHY THIS, ARTISTICALLY** — an ad splash has to hold a *pose* for the hero frame. Real water does not pose.
> Drag is how you cheat a pose without freezing time: it removes energy so the shape stops changing, while
> gravity still reads as real. This is the "settle" every high-end beverage spot has and most amateur sims lack.

**Stability warning:** force fields raise velocities far beyond gravity's contribution. If you go above ~10
strength, drop **CFL to 2.0** and raise **Timesteps Maximum to 8**, or you will get tunnelling and stray
particles. Use **Flow** (1–5) instead of huge Strength wherever you can — it clamps to a velocity target rather
than accelerating without limit, and it is dramatically more stable.

---

## 8. Obstacles and effectors

`Physics > Fluid > Type: Effector` on the bottle.

| Setting | Python | Default | Notes |
|---|---|---|---|
| Effector Type | `effector_type` | `'COLLISION'` | `'COLLISION'` = obstacle. `'GUIDE'` = velocity guide (§6.6) |
| Surface Thickness | `surface_distance` | 0.0 | Thickens the collision shell outward, in **voxels**. 0.05–0.3 is the leak fix |
| Is Planar | `use_plane_init` | False | For open/flat colliders (a plane floor, a single-sided card). Off for a closed bottle |
| Use Effector | `use_effector` | True | **Keyframable.** Turn a collider on/off mid-shot |
| Velocity Factor | `velocity_factor` | 1.0 | How much a *moving* effector's velocity is transferred to the fluid |
| Subframes | `subframes` | 0 | Raise to 2–4 for a fast-moving collider |
| Guide Mode | `guide_mode` | `'MAXIMUM'` | Guide effectors only: how guide velocity combines |

### 8.1 The bottle needs a proxy collider

Do **not** use the render mesh. Reasons:

- **Glass is thin and double-walled.** A bottle modelled with real wall thickness gives the solver two surfaces
  ~2 mm apart. At res 100 (1 cm voxels) that is *sub-voxel* — even with Fractional Obstacles it is unreliable,
  and liquid leaks into the cavity between the walls and gets stuck there forever.
- **High poly counts slow the voxelisation** of every frame.
- **The label, cap threads, and embossing** are detail the fluid cannot resolve and will only cause artefacts.

Build a proxy:

1. Duplicate the bottle, name it `bottle_collider`.
2. Delete interior geometry so it is a **single closed manifold shell** — the *outside* silhouette only, solid.
   A lathe/screw of the profile curve is ideal.
3. **Decimate to ~2–5k tris.** Smooth silhouette matters; detail does not.
4. Slightly **inflate** it (Shrink/Fatten +0.5–1 mm, or Solidify then apply) so the water sits *just* off the
   render mesh rather than intersecting it. Intersection is far more visible than a 1 mm gap.
5. Hide from render (camera icon off), keep visible in viewport.
6. Make **this** the Effector. Leave the render bottle out of the physics entirely.

Also make an effector for anything else water touches: the table/ground plane (a real plane with
`Is Planar` ON), and simplified proxies for the lime slices if you want the water to interact with them.

### 8.2 Surface Thickness and Delete In Obstacle

- **Surface Thickness 0** is default and correct when the collider is comfortably thicker than a voxel.
- Raise it to **0.1–0.3** the moment you see liquid tunnelling through the bottle. It costs nothing and it is
  the first thing to try, before dropping CFL.
- Too high (>0.5) and you get a visible standoff halo of empty space around the product.
- **Delete In Obstacle** (domain setting) removes any particle that ends up inside a collider. Turn it **ON**
  with a closed proxy: it cleans up the handful of particles that inevitably squeeze in and would otherwise
  sit inside the bottle forever, or worse, erupt out later. Turn it **OFF** if you use planar/open colliders,
  because "inside" is ill-defined and it will eat liquid.

### 8.3 Moving products

If the bottle rises, rotates, or is dropped into frame:

- Keep `Velocity Factor` at 1.0 so the motion actually pushes the water.
- Raise the effector's `Subframes` to 2–4 — a collider that moves more than a voxel per frame will tunnel just
  as badly as fast liquid.
- Consider `Use Effector` keyframed OFF before the object enters, so the solver is not voxelising it needlessly.

> **WHY THIS, ARTISTICALLY** — a proxy that is *slightly larger* than the hero mesh is not a compromise, it is
> the intended look. Water clinging exactly to a glass surface renders as a muddy double-refraction mess.
> A hair of separation reads as a clean, wet highlight edge, which is what the product shot is selling.

---

## 9. Whitewater — spray, foam, bubbles

`Fluid > Liquid > Particles`. **This is what sells a beverage splash.**

### 9.1 Why it matters more than the mesh

The liquid mesh gives you a smooth refractive surface. Real high-speed footage of a splash is not smooth — it is
a cloud of atomised droplets and aerated foam. Those droplets are what:

- catch **specular highlights** and produce the sparkle that reads as "cold" and "fresh";
- give the splash **volume and softness** against a hard product silhouette;
- hide the fact that your mesh resolution is finite — whitewater covers the polygonal edges and the crawl;
- read as **carbonation**, which is the whole point for a soda ad.

Skipping whitewater is the most common reason a technically-fine sim looks like CG.

### 9.2 Setup

| Setting | Python | Suggested | Notes |
|---|---|---|---|
| Spray | `use_spray_particles` | ON | Airborne droplets. The sparkle |
| Foam | `use_foam_particles` | ON | Particles on the surface. The white lace |
| Bubbles | `use_bubble_particles` | ON | Below the surface. Carbonation |
| Tracer | `use_tracer_particles` | off | Debug/advection only |
| Particles In Boundary | `sndparticle_boundary` | `'DELETE'` | `'PUSHOUT'` keeps them in the domain — wrong for an open domain |
| Combined Export | `sndparticle_combined_export` | `'OFF'` | Merges systems for simpler shading. `'SPRAY_FOAM_BUBBLE'` gives you one system to render |
| **Upres Factor** | `particle_scale` | **2** | Whitewater is generated on a grid `particle_scale ×` the sim resolution. 2 at sim-res 200 = whitewater detail of 400. Cheap detail. 3 for hero |

### 9.3 Potential settings — where particles are born

Whitewater is emitted where the liquid's *potential* exceeds a threshold. Three independent potentials, each
with a Min and a Max that define a normalised ramp:

| Potential | Detects | Effect of lowering Min |
|---|---|---|
| **Wave Crest** | Sharp curvature — the tips of crests and thin sheet edges | More foam along every edge |
| **Trapped Air** | Fluid folding over itself, enclosing air | More bubbles, especially at impact |
| **Kinetic Energy** | Fast-moving fluid | More spray everywhere the water is quick |

The rule: **`Min` is the "birth threshold" — lower it to get more particles.** `Max` is where the potential
saturates. Blender's defaults are conservative because they are tuned for oceans, not ad splashes.

Practical starting point for a product splash:

| Setting | Python | Ocean-ish default | **Ad splash** |
|---|---|---|---|
| Wave Crest Potential Min | `sndparticle_potential_min_wavecrest` | ~1.0 | **0.3** |
| Wave Crest Potential Max | `sndparticle_potential_max_wavecrest` | ~2.0 | 2.0 |
| Trapped Air Potential Min | `sndparticle_potential_min_trappedair` | ~1.0 | **0.3** |
| Trapped Air Potential Max | `sndparticle_potential_max_trappedair` | ~2.0 | 2.0 |
| Kinetic Energy Potential Min | `sndparticle_potential_min_energy` | ~1.0 | **0.5** |
| Kinetic Energy Potential Max | `sndparticle_potential_max_energy` | ~5.0 | 5.0 |
| Wave Crest Sampling | `sndparticle_sampling_wavecrest` | ~100 | **150–250** |
| Trapped Air Sampling | `sndparticle_sampling_trappedair` | ~150–200 | **200–400** |

Sampling is *how many* particles are spawned per unit of potential. This is your density dial and it is the one
to push for an ad. Watch particle counts: 5–20 million whitewater particles is normal for a hero splash and it
is entirely a memory/disk problem, not a physics one.

### 9.4 Behaviour settings

| Setting | Python | Default | Notes |
|---|---|---|---|
| **Bubble Buoyancy** | `sndparticle_bubble_buoyancy` | ~−3 | How fast bubbles rise through liquid. More negative = rises faster. Push it for fizzy carbonation |
| **Bubble Drag** | `sndparticle_bubble_drag` | ~2 | How strongly bubbles are dragged by the surrounding liquid. Higher = they follow the flow tightly |
| **Life Minimum / Maximum** | `sndparticle_life_min` / `_max` | ~10 / 10000 | Frames a particle survives. Set Max to ~30–60 for spray that dissipates like real mist instead of hanging forever |

For a 60-frame splash, `life_min` 8 / `life_max` 40 with `boundary = 'DELETE'` gives spray that appears,
sparkles, and fades out of the shot rather than accumulating into a permanent haze.

### 9.5 Rendering whitewater

Baking whitewater creates up to three **particle systems on the domain object** (`Spray`, `Foam`, `Bubbles`).
They render like any particle system.

**Route 1 — Particle system instancing (reliable, do this first).**

For each system, in `Particle Properties > Render`:

| Field | Value |
|---|---|
| Render As | **Object** |
| Instance Object | an Ico Sphere, subdivisions **1**, radius **1.0**, shade smooth |
| Scale | **0.0015 – 0.004** (for a ~1 m domain) |
| Scale Randomness | **0.4 – 0.6** |

Then in `Viewport Display`, set Display As **Rendered** with a low **Display Percentage** (2–5%) so the viewport
stays usable. Cycles instances the mesh, so 10 million tiny spheres is memory-cheap — but keep the instanced
mesh at the absolute minimum poly count, because instancing amplifies any complexity.

**Route 2 — Point cloud (cheapest, Cycles).**
Cycles renders native point primitives far more cheaply than mesh instances. Bring the whitewater in as points
via a Geometry Nodes instancer rather than mesh instancing where you can: the important part is that whatever
you instance is a single low-poly primitive with a shared material, and that you are not asking Cycles to
subdivide 10 million spheres.

**Route 3 — Geometry Nodes instancer (most control).**
Once the whitewater exists as points/instances, a Geometry Nodes modifier lets you:
- **Instance on Points** with size driven by a random value, so the droplet size distribution is art-directable;
- **Delete Geometry** to cull particles that are behind the bottle or outside the camera frustum — a huge render
  saving;
- drive **scale by velocity**, so fast spray stretches and slow spray beads;
- **separate spray / foam / bubbles into different materials** on the same instancer.

This is almost certainly what the `Modifiers` object in the outliner is for, and it is the "basic geometry
nodes" the video advertises — GN is also the natural way to scatter the flying lime slices and green spheres.

**Shading, briefly (full treatment in the look-dev module).** Spray droplets: Glass BSDF, IOR 1.33, tiny
roughness — they need to catch a hot rim light to sparkle. Foam: white diffuse with high roughness and a touch
of translucency, **not** glass. Bubbles: Glass with a thin-film / high-IOR feel. Rendering all three as one
grey glass material is the fastest way to make whitewater look like sand.

> **WHY THIS, ARTISTICALLY** — the hero frame of a beverage ad is judged on *sparkle count*. Every droplet is a
> specular highlight. Increase whitewater density and add a hard, small key light behind/above the splash before
> you increase sim resolution — it buys far more perceived quality per hour.

---

## 10. Mesh settings

`Fluid > Liquid > Mesh` (`use_mesh = True`). This is the surface that actually renders. It is a **separate,
cheap bake** — iterate here freely.

| Setting | Python | Default | What it does |
|---|---|---|---|
| **Upres Factor** | `mesh_scale` | 2 | Meshing grid = sim resolution × this. Detail without re-simulating. **The best value in the whole panel** |
| **Particle Radius** | `mesh_particle_radius` | 2.0 | Radius each particle contributes to the surface. **The blobbiness dial** |
| Use Speed Vectors | `use_speed_vectors` | on | Writes velocity vectors for **vector motion blur**. Essential |
| Mesh Generator | `mesh_generator` | `'IMPROVED'` | `'IMPROVED'` (smoother, has concavity controls) vs `'UNION'` (raw metaball union, blobbier) |
| Smoothing Positive | `mesh_smoothen_pos` | 1 | Smooths outward-bulging detail. Raise to calm a noisy surface |
| Smoothing Negative | `mesh_smoothen_neg` | 1 | Smooths inward detail (pits, creases). Raise to remove pocking |
| Concavity Upper | `mesh_concave_upper` | 3.5 | `IMPROVED` only. Controls how aggressively concave regions are filled |
| Concavity Lower | `mesh_concave_lower` | 0.4 | `IMPROVED` only. Lower = thinner sheets survive |

### 10.1 Upres Factor is the cheapest quality in Blender

A sim at res 200 with `Upres Factor 2` meshes at an effective 400. You get a surface with detail the sim did not
have to pay for, because the particles carry sub-voxel position information the grid discards.

- **Upres 2** — default, good.
- **Upres 3** — hero. Noticeably crisper droplet silhouettes. Mesh cache gets big.
- **Upres 4** — diminishing returns; you are now inventing detail that is not in the particles, and cache size
  is brutal.

Always try raising Upres before raising Resolution Divisions. It is 8×–16× cheaper for a similar perceived gain.

### 10.2 Mesh Particle Radius — the blobbiness dial

This is **not** the sim's Particle Radius. It only affects surface reconstruction.

| Value | Result |
|---|---|
| 1.0–1.4 | Stringy, thin, **holes appear** in sheets, individual particles visible as separate beads |
| **1.6–2.0** | **Correct for a splash.** Thin sheets survive but stay connected |
| 2.5–3.5 | Blobby, fat, marshmallow water. Fills every hole. Reads as thick liquid or as low-res CG |

Diagnosis: if your splash looks like a lava lamp, **lower** this. If it looks like it is shattering into gravel
and the sheets have holes, **raise** it — or raise sim `Sampling`/`Resolution` so there are more particles to
reconstruct from.

### 10.3 Smoothing and speed vectors

- Positive/negative smoothing at 1/1 is fine. If the mesh **boils** — surface detail crawling frame to frame —
  raise both to 2 or 3. That crawl is very visible on a refractive material and very ugly.
- **Use Speed Vectors ON** is non-negotiable for an ad. Fluid moving 3 m/s across a 24 fps frame travels 12 cm
  per frame; without motion blur it strobes. Speed vectors let Cycles produce correct vector blur on a mesh
  whose topology changes every frame (normal geometry motion blur cannot, because vertex counts differ).
  Enable scene **Render > Motion Blur** as well, or the vectors go unused.

> **WHY THIS, ARTISTICALLY** — motion blur is the difference between "a 3D water sculpture" and "footage of
> water." It is also what makes 24 fps splashes readable. Never render a splash without it.

---

## 11. Caching

`Fluid > Settings > Cache`.

| Cache Type | Python | Behaviour | Use |
|---|---|---|---|
| **Replay** | `'REPLAY'` | Simulates on the fly as you scrub. No explicit bake. Invalidates constantly | Only for the first 30 seconds of exploration. **Never for production** |
| **Modular** | `'MODULAR'` | Bake Data / Mesh / Particles **independently**. Re-bake mesh without re-baking data | **The production choice.** Use this |
| **Final** | `'ALL'` | One "Bake All" button, everything at once | Overnight final only, when nothing will change |

### 11.1 Non-negotiables

- **Set a real cache directory.** `//cache_fluid_hero/` (relative to the .blend) or an absolute path on your
  fastest large drive. The default in the temp folder *will* be deleted by the OS, at the worst moment.
- **One directory per sim.** Two domains sharing a cache folder will corrupt each other silently.
- **Set Frame Start / End explicitly** (`cache_frame_start`, `cache_frame_end`). Do not bake 250 frames when
  the splash lives for 70.
- **Is Resumable** (`cache_resumable`) ON. Stores extra data so a cancelled bake can continue from where it
  stopped instead of restarting. Costs disk. Worth it for anything over ~20 minutes. Turn it OFF for the final
  overnight bake if you are disk-constrained and confident.
- **Format:** `OpenVDB` for the data cache, with compression. Set `openvdb_data_depth` to **Half** (16-bit) for
  liquid — you will not see the difference and it halves the cache.
- **Free the cache before changing the domain.** Resizing, rescaling, or moving a domain with a live cache
  produces garbage, not an error.

### 11.2 Bake order

The panel lists them in dependency order:

1. **Data** — the simulation itself. Everything depends on this. Slowest.
2. **Mesh** — surface reconstruction from the data cache. Fast-ish, but the **biggest on disk**.
3. **Particles** — whitewater from the data cache. Independent of Mesh.

Practical order: **Data → Particles → Mesh.** Bake Data, then whitewater (so you can judge density), then Mesh
last because it is the disk hog and the thing you are most likely to re-do.

Re-bake rules:
- Change a solver/emitter/force setting → **free and re-bake Data** (mesh and particles are invalidated).
- Change Mesh panel settings → **free and re-bake Mesh only.** Data survives.
- Change whitewater settings → **free and re-bake Particles only.** Data survives.

That separation is exactly why Modular is mandatory.

### 11.3 Disk budgeting

Cache size is dominated by particle counts, which vary enormously with how much liquid is in the domain. Do not
trust anyone's table, including this one — but for order of magnitude, on a ~1 m domain with a splash filling a
modest fraction of the box:

| Resolution | Data / frame | Mesh / frame | Whitewater / frame | ~100 frames total |
|---|---|---|---|---|
| 100 | 2–15 MB | 2–10 MB | 5–30 MB | **1–5 GB** |
| 200 | 20–100 MB | 20–80 MB | 50–250 MB | **10–40 GB** |
| 300 | 80–400 MB | 80–300 MB | 150–800 MB | **30–150 GB** |
| 400 | 250 MB–1.5 GB | 200 MB–1 GB | 400 MB–2 GB | **80–400 GB** |

**The reliable method:** bake 10 frames at your intended final resolution, `du -sh` the cache folder, divide by
10, multiply by your frame count, add 40%. Do this *before* you start the overnight bake, not after it fills
the drive at frame 63.

---

## 12. Bake strategy — keeping the sim art-directable

The goal is a splash you **designed**, not one you **found**. Three passes.

### Pass 1 — Art direction loop (resolution 64–100)

- Resolution **100**, Cache Type **Modular**, Mesh **OFF**, Particles **OFF**.
- Bake **Data only**. Look at the FLIP particles directly in the viewport — they show you the shape.
- Iterate on: domain size, emitter path, emitter speed, `Use Flow` in/out frames, Initial Velocity Normal,
  force field strengths and their keyframes.
- Target **2–5 minutes per bake**. If a bake takes longer than 5 minutes at this stage, shrink the domain or
  drop to res 64. The value here is **number of iterations**, not fidelity.
- Do 10–20 of these. This is where the shot is made.
- **Keep the camera in the viewport the whole time.** You are designing a silhouette against a specific frame,
  and a splash that looks great from a 3/4 orbit can read as nothing from the hero angle.

### Pass 2 — Confirm bake (resolution 150–200)

- Same setup, resolution 150 or 200, Mesh ON at Upres 2, Particles ON at conservative sampling.
- **Expect the timing to shift by 1–5 frames** and the shape to loosen. This is the pass where you find out
  whether the design survives real resolution.
- Fix what breaks: leaks (§13), stray flyers, the crown blooming late.
- Nudge — do not redesign. If the shape has genuinely changed character, go back to Pass 1 *at the new
  resolution* rather than fighting it at high cost.
- Render a **20-frame test at final quality** from the hero angle. Look at it as an image, not a viewport.

### Pass 3 — Final (resolution 250–400)

- Free all caches. Set final resolution, Upres 3, whitewater sampling pushed up, `cache_resumable` off if
  disk-tight, OpenVDB Half.
- Bake **Data** overnight. Check it in the morning before committing to Mesh and Particles.
- Bake **Particles**, then **Mesh**.
- **Do not change anything after this point.** A one-value tweak is a full re-bake.

### Keeping it art-directable rather than random

- **Change one thing per iteration.** Fluid sims are chaotic; two simultaneous changes teach you nothing.
- **Keep a text block or a filename log** of what each bake was: `res100_v07_vortex7_burst12-34.blend`.
  You *will* want to go back two versions.
- **Prefer emitter and timing changes over solver changes.** Emitter changes are predictable. Solver changes
  are not.
- **Save incremental .blend files** (`Ctrl+Alt+S`), not overwrites.
- If you get a bake you love, **immediately save the .blend and back up the cache folder.** A great splash is
  not reproducible from settings alone once you have touched anything.

---

## 13. Failure modes and fixes

### Liquid leaks through the bottle
In order of what to try:
1. Domain `Fractional Obstacles` **ON**, `Obstacle Distance` 0.5 → **0.8**.
2. Effector `Surface Thickness` 0.0 → **0.15–0.3**.
3. Replace the render mesh collider with a **closed, single-walled, slightly inflated proxy** (§8.1).
4. `CFL` 4 → **2.0**, `Timesteps Maximum` 4 → **8**. (Tunnelling = a particle crossed the wall in one substep.)
5. Raise resolution. An obstacle thinner than ~2 voxels cannot be represented reliably no matter what.
6. `Delete In Obstacle` ON to clean up whatever still gets inside.

### Sim explodes / stray particles fly everywhere
- Force field strengths too high → use **Flow** 1–5 instead of Strength 30+.
- `CFL` → 1.0–2.0, `Timesteps Maximum` → 8–16.
- Emitter intersecting the collider, or inside it. Move it out.
- `Time Scale` above 1.0. Put it back.
- Overlapping/self-intersecting effector geometry, or an effector with flipped normals.
- FLIP Ratio at 1.0. Drop to 0.97.

### Liquid sticks to / clings to the bottle unnaturally
- `Obstacle Distance` **up** to 0.7–1.0.
- Add a weak **negative Force** field at the bottle centre (Shape `LINE`, Tube falloff) to push water off.
- Reduce Surface Tension in the Diffusion panel if you enabled it.
- Raise FLIP Ratio toward 0.98 so the water has enough energy to leave the surface.
- Check resolution — at low res everything looks sticky because sheets are voxel-thick.

### The sim disappears at the domain edge
Working as designed on an open domain (§2.4). Either enlarge the domain in that direction, or accept it and
frame so the deletion happens off-camera. Enabling that border collision is almost always the wrong fix — it
replaces "vanishing" with "bouncing off nothing."

### Jittery / boiling / crawling mesh
- Mesh `Smoothing Positive` and `Negative` → 2–3.
- Mesh `Particle Radius` → up (1.8–2.2) to bridge gaps between frames.
- Mesh `Upres Factor` → 2 or 3; too low a meshing grid makes detail pop in and out.
- Sim `Sampling` 2 → 3 for more particles to reconstruct from.
- Sim `Narrow Band Width` 3 → 4 if the boiling is on a deeper body of water.
- Check `Use Speed Vectors` + scene motion blur; some perceived jitter is just missing blur.

### The sim changes when I rescale the domain
It is supposed to. Domain size **is** the physical scale (§2.3) and gravity is absolute. Rescaling is a
different simulation. Free the cache, apply the scale, re-bake. Never rescale a domain you like.

### Non-uniform scale problems
Symptoms: distorted advection, obstacle distances that behave differently on different axes, effectors that do
not line up with their meshes, a sim that changes when you merely enter Edit Mode. Fix: `Ctrl+A > Scale` on the
**domain, every flow object, every effector, and the curve**. Then free the cache and re-bake. Make applying
scale a habit before every bake.

### Emitter stutters / liquid comes out in beads
Flow `Subframes` 0 → **3** (fast emitter: 6–8). The emitter is teleporting more than its own size per frame.
Also raise the curve's `Resolution Preview U` to 32 so the *path* is smooth, and check your Offset Factor
F-curve for a step or a sudden slope change.

### Nothing emits at all
- Flow Type is still `Smoke`, not `Liquid`.
- Emitter is outside the domain box.
- `Use Flow` is keyframed off at the current frame.
- Emitter is a flat plane and `Is Planar` is off.
- For a `Geometry` behavior object: the current frame is past `cache_frame_start`; scrub back to the start.
- The domain has a stale cache. Free Data and re-bake.

### Whitewater bakes but nothing renders
- The particle systems' `Render As` is set to `None` or `Halo`. Set to **Object** with an instance object.
- Instance object `Scale` is at default 1.0 — you have 10 million 1-metre spheres filling the frame. Set it to
  0.002.
- The domain object's render visibility is disabled, which also hides its particle systems.

### Bake is unbearably slow
- Domain too large for the resolution — shrink it.
- Whitewater sampling too high; bake Data alone first.
- `Sampling` at 3 when 2 would do.
- CFL dropped to 1.0 when 2.0 was sufficient.
- Viscosity or Surface Tension enabled unnecessarily.
- Cache format not OpenVDB / not compressed, so you are I/O bound.

---

## 14. Blender 3.6 vs 4.x

The fluid system itself is **remarkably stable** from 3.6 through the 4.x LTS releases. Panel names, property
names, and the Mantaflow solver are essentially unchanged, so everything above transfers directly. The things
that actually bite are around it:

| Area | 3.6 | 4.x | Impact |
|---|---|---|---|
| **Python operator context** | `bpy.ops.fluid.bake_data({'scene': s, 'object': o})` dict-override still works (deprecated) | **Dict override removed.** Must use `with bpy.context.temp_override(...)` | **Breaks old bake scripts.** All snippets in this module use `temp_override`, which works in 3.2+ and 4.x |
| Fluid panel layout | Physics > Fluid | Same | None |
| `domain_settings` / `flow_settings` / `effector_settings` | Same names | Same names | None |
| Force field types and properties | Same | Same | None |
| `effector_weights.collection` | Present | Present | None |
| Whitewater particle systems | Same | Same | None |
| **Principled BSDF sockets** | `Subsurface`, `Specular`, `Transmission`, `Emission` | Renamed/restructured in 4.0: `Specular IOR Level`, `Emission Color`+`Emission Strength`, subsurface reorganised | Breaks water/glass **shader scripts** and appended materials. A look-dev issue, not a sim issue |
| **EEVEE** | EEVEE (legacy) | **EEVEE Next** from 4.2 — different refraction, screen-space settings renamed | Preview renders of refractive water look different. Use Cycles for anything you judge |
| Vector motion blur | Cycles, works with Use Speed Vectors | Same | None |
| Cycles point cloud primitive | Available (since 3.1) | Available, improved | Whitewater rendering is cheaper on 4.x |
| Node group interfaces (Geometry Nodes) | `node_group.inputs` | **`node_group.interface`** from 4.0 | Breaks GN scripts — relevant to the whitewater/fruit instancer, not the sim |
| Menu location of Force Fields | `Add > Force Field` | Same | None |

**Practical guidance:** if the user is on 4.2+, everything in §§1–13 applies verbatim. Only the Python snippets'
context handling and any *shading* scripts need attention. Do not go hunting for renamed fluid settings — there
are none worth mentioning.

---

## 15. Python — copy-pasteable bpy

All snippets target **Blender 3.6 through 4.x**. Fluid settings live on
`modifier.domain_settings` / `modifier.flow_settings` / `modifier.effector_settings`.

Two rules that save an hour:
- **Apply scale before every bake.** The helper below does it.
- **Bake operators are job operators.** Running them from the Text Editor launches a background job and returns
  immediately. For a deterministic script bake, run headless: `blender -b hero.blend -P bake.py`.

### 15.1 Helpers

```python
import bpy, math
from mathutils import Vector

def apply_scale(obj):
    """Mantaflow assumes unit scale. Call this on every domain, flow, effector and curve."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)

def add_fluid_modifier(obj, fluid_type):
    """fluid_type in {'DOMAIN', 'FLOW', 'EFFECTOR'}. Returns the modifier."""
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.get("Fluid")
    if mod is None:
        bpy.ops.object.modifier_add(type='FLUID')
        mod = obj.modifiers["Fluid"]
    mod.fluid_type = fluid_type
    return mod

def try_enum(owner, prop, candidates):
    """Set an enum whose identifier differs across Blender builds."""
    for ident in candidates:
        try:
            setattr(owner, prop, ident)
            return ident
        except TypeError:
            continue
    return None
```

### 15.2 Create the domain and set every screenshot value

```python
BOTTLE_HEIGHT = 0.25          # metres - drives the whole physical scale
DOM_XY        = 0.80
DOM_Z         = 1.30
FRAME_START, FRAME_END = 1, 90

# --- domain object: a plain cube, unit scale, no rotation -------------------
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, DOM_Z * 0.5 - 0.1))
dom = bpy.context.active_object
dom.name = "FluidDomain"
dom.scale = (DOM_XY * 0.5, DOM_XY * 0.5, DOM_Z * 0.5)
apply_scale(dom)                          # <-- non-negotiable
dom.rotation_euler = (0.0, 0.0, 0.0)
dom.display_type = 'BOUNDS'
dom.hide_render = True

mod = add_fluid_modifier(dom, 'DOMAIN')
ds  = mod.domain_settings
ds.domain_type = 'LIQUID'                 # set FIRST - it resets dependent defaults

# --- Settings panel (screenshot values) ------------------------------------
ds.resolution_max         = 100           # PREVIEW value. 200/300/400 for final
ds.time_scale             = 1.0
ds.cfl_condition          = 4.0
ds.use_adaptive_timesteps = True
ds.timesteps_max          = 4
ds.timesteps_min          = 1
ds.gravity                = (0.0, 0.0, -9.81)
ds.delete_in_obstacle     = True          # ON, because we use a closed proxy collider

# --- Border Collisions: OPEN DOMAIN (all off) ------------------------------
ds.use_collision_border_front  = False
ds.use_collision_border_back   = False
ds.use_collision_border_left   = False
ds.use_collision_border_right  = False
ds.use_collision_border_top    = False
ds.use_collision_border_bottom = False

# --- Liquid panel (screenshot values) --------------------------------------
ds.simulation_method    = 'FLIP'
ds.flip_ratio           = 0.97            # splashiness. 0.90 damped .. 0.99 wild
ds.sys_particle_maximum = 0               # 0 = unlimited
ds.particle_radius      = 1.0
ds.particle_number      = 2               # "Sampling"
ds.particle_randomness  = 0.1
ds.particle_max         = 16
ds.particle_min         = 8
ds.particle_band_width  = 3.0             # "Narrow Band Width"
ds.use_fractions        = True            # "Fractional Obstacles" - ON for products
ds.fractions_distance   = 0.5             # "Obstacle Distance"

# --- Cache -----------------------------------------------------------------
ds.cache_type        = 'MODULAR'          # NEVER 'REPLAY' for production
ds.cache_directory   = "//cache_fluid_hero/"
ds.cache_frame_start = FRAME_START
ds.cache_frame_end   = FRAME_END
ds.cache_resumable   = True
ds.cache_data_format = 'OPENVDB'
try_enum(ds, "openvdb_data_depth", ("16", "HALF"))   # half float halves the cache

# --- Mesh (the surface that actually renders) ------------------------------
ds.use_mesh              = True
ds.mesh_generator        = 'IMPROVED'
ds.mesh_scale            = 2              # "Upres Factor" - cheapest quality in Blender
ds.mesh_particle_radius  = 2.0            # blobbiness. 1.6-2.0 for a splash
ds.mesh_smoothen_pos     = 1
ds.mesh_smoothen_neg     = 1
ds.mesh_concave_upper    = 3.5
ds.mesh_concave_lower    = 0.4
ds.use_speed_vectors     = True           # required for vector motion blur

bpy.context.scene.frame_start = FRAME_START
bpy.context.scene.frame_end   = FRAME_END
bpy.context.scene.render.use_motion_blur = True
```

### 15.3 Curve-guided inflow emitter (the headline technique)

```python
import bpy, math

TURNS       = 1.35        # how far round the bottle the ribbon wraps
RADIUS      = 0.12        # metres from the bottle axis
Z_START     = 0.05
Z_END       = 0.32
POINTS      = 10

# --- 1. build the rising spiral as a Bezier curve --------------------------
cu = bpy.data.curves.new("SplashPath", 'CURVE')
cu.dimensions   = '3D'
cu.resolution_u = 32           # low res here = a stuttering emitter
cu.use_path     = True
spl = cu.splines.new('BEZIER')
spl.bezier_points.add(POINTS - 1)
for i, bp in enumerate(spl.bezier_points):
    t = i / (POINTS - 1)
    a = t * TURNS * 2.0 * math.pi
    bp.co = (RADIUS * math.cos(a), RADIUS * math.sin(a), Z_START + t * (Z_END - Z_START))
    bp.handle_left_type = bp.handle_right_type = 'AUTO'
path = bpy.data.objects.new("SplashPath", cu)
bpy.context.collection.objects.link(path)
path.hide_render = True
apply_scale(path)

# --- 2. the emitter: a disc whose normal points along +Y -------------------
bpy.ops.mesh.primitive_circle_add(vertices=16, radius=0.028, fill_type='NGON',
                                  rotation=(math.radians(90.0), 0.0, 0.0))
emit = bpy.context.active_object
emit.name = "SplashEmitter"
apply_scale(emit)
emit.location = (0.0, 0.0, 0.0)   # MUST be zero - location offsets from the path

# --- 3. Follow Path constraint --------------------------------------------
con = emit.constraints.new('FOLLOW_PATH')
con.target             = path
con.use_curve_follow   = True      # rotates the emitter tangentially -> normal velocity follows
con.forward_axis       = 'FORWARD_Y'
con.up_axis            = 'UP_Z'
con.use_fixed_location = True      # switches control to offset_factor (0..1)

con.offset_factor = 0.0
con.keyframe_insert("offset_factor", frame=10)
con.offset_factor = 1.0
con.keyframe_insert("offset_factor", frame=40)
# shape this F-curve by hand in the Graph Editor - linear reads mechanical

# --- 4. make it a liquid inflow -------------------------------------------
fmod = add_fluid_modifier(emit, 'FLOW')
fs   = fmod.flow_settings
fs.flow_type            = 'LIQUID'
fs.flow_behavior        = 'INFLOW'
fs.surface_distance     = 1.5      # stream thickness, in voxels
fs.use_plane_init       = False
fs.subframes            = 3        # THE fix for beaded/stuttering streams
fs.use_initial_velocity = True
fs.velocity_normal      = 3.0      # tangential throw. 2-5 for a wrapping ribbon
fs.velocity_random      = 0.3
fs.velocity_coord       = (0.0, 0.0, 1.0)   # world-space loft, does NOT rotate

# --- 5. burst: on for frames 12-34, then ballistic -------------------------
for frame, state in ((FRAME_START, False), (11, False), (12, True),
                     (34, True), (35, False)):
    fs.use_inflow = state
    fs.keyframe_insert("use_inflow", frame=frame)   # booleans get CONSTANT interp
```

### 15.4 Force fields + the `forces` collection

```python
import bpy

forces = bpy.data.collections.new("forces")
bpy.context.scene.collection.children.link(forces)

def add_field(name, ftype, location, strength, flow=0.0, shape='POINT',
              falloff='SPHERE', power=1.0, max_dist=None, size=None):
    bpy.ops.object.effector_add(type=ftype, location=location)
    ob = bpy.context.active_object
    ob.name = name
    f = ob.field
    f.strength     = strength
    f.flow         = flow            # velocity target instead of raw acceleration - MUCH safer
    f.shape        = shape
    f.falloff_type = falloff
    f.falloff_power = power
    if size is not None:
        f.size = size                # turbulence feature scale
    if max_dist is not None:
        f.use_max_distance = True
        f.distance_max     = max_dist
    # move into the forces collection
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    forces.objects.link(ob)
    return ob

# 1) VORTEX - this is what makes the ribbon WRAP the bottle
vortex = add_field("F_Vortex", 'VORTEX', (0.0, 0.0, 0.15), strength=7.0, flow=2.0,
                   shape='LINE', falloff='TUBE', power=1.0, max_dist=0.35)

# 2) NEGATIVE FORCE - pushes water off the glass so it bulges into a crown
repel  = add_field("F_Repel", 'FORCE', (0.0, 0.0, 0.15), strength=-2.0, flow=1.0,
                   shape='LINE', falloff='TUBE', power=2.0, max_dist=0.20)

# 3) TURBULENCE - breaks the ribbon into strands and droplets
turb   = add_field("F_Turbulence", 'TURBULENCE', (0.0, 0.0, 0.25), strength=2.5,
                   shape='POINT', falloff='SPHERE', power=0.0, max_dist=0.50, size=0.8)

# optional 4th: DRAG for the settle (see the keyframe block below)
drag   = add_field("F_Drag", 'DRAG', (0.0, 0.0, 0.25), strength=0.0,
                   shape='POINT', falloff='SPHERE', power=0.0, max_dist=0.60)

# --- restrict the domain to ONLY these fields ------------------------------
ds.effector_weights.collection = forces
ds.effector_weights.all        = 1.0
# per-type multipliers, all keyframable:
# ds.effector_weights.force / .vortex / .wind / .turbulence / .drag / .gravity

# --- bloom then settle -----------------------------------------------------
schedule = {
    #  frame : (vortex, turbulence, drag)
    10: (0.0, 0.0, 0.0),
    16: (7.0, 2.5, 0.0),
    34: (7.0, 2.5, 0.0),
    46: (1.0, 0.5, 3.0),
    60: (0.0, 0.0, 4.0),
}
for frame, (v, t, d) in schedule.items():
    vortex.field.strength = v; vortex.field.keyframe_insert("strength", frame=frame)
    turb.field.strength   = t; turb.field.keyframe_insert("strength",   frame=frame)
    drag.field.strength   = d; drag.field.keyframe_insert("strength",   frame=frame)
```

> If you raise any field strength above ~10, also set `ds.cfl_condition = 2.0` and
> `ds.timesteps_max = 8` or the sim will tunnel and explode.

### 15.5 The bottle as an effector (with a proxy collider)

```python
bottle_proxy = bpy.data.objects["bottle_collider"]   # closed, ~3k tris, slightly inflated
apply_scale(bottle_proxy)
bottle_proxy.hide_render = True

emod = add_fluid_modifier(bottle_proxy, 'EFFECTOR')
es   = emod.effector_settings
es.effector_type   = 'COLLISION'
es.surface_distance = 0.15     # raise to 0.3 if liquid still leaks through
es.use_plane_init   = False    # False for a closed solid; True for planes/cards
es.use_effector     = True     # keyframable - turn colliders on/off mid-shot
es.velocity_factor  = 1.0      # transfers a MOVING product's motion to the fluid
es.subframes        = 2        # raise for a fast-moving product

# ground / table plane
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0.0, 0.0, 0.0))
ground = bpy.context.active_object
ground.name = "GroundEffector"
gmod = add_fluid_modifier(ground, 'EFFECTOR')
gmod.effector_settings.effector_type    = 'COLLISION'
gmod.effector_settings.use_plane_init   = True    # planar collider
gmod.effector_settings.surface_distance = 0.1
```

### 15.6 Whitewater

```python
ds.use_spray_particles  = True
ds.use_foam_particles   = True
ds.use_bubble_particles = True
ds.use_tracer_particles = False

ds.particle_scale             = 2          # "Upres Factor" for whitewater
ds.sndparticle_boundary       = 'DELETE'   # correct for an OPEN domain
ds.sndparticle_combined_export = 'OFF'     # or 'SPRAY_FOAM_BUBBLE' for one system

# potentials: lower the MIN to get MORE particles
ds.sndparticle_potential_min_wavecrest  = 0.3
ds.sndparticle_potential_max_wavecrest  = 2.0
ds.sndparticle_potential_min_trappedair = 0.3
ds.sndparticle_potential_max_trappedair = 2.0
ds.sndparticle_potential_min_energy     = 0.5
ds.sndparticle_potential_max_energy     = 5.0

# sampling = density. This is the dial to push for an ad.
ds.sndparticle_sampling_wavecrest  = 200
ds.sndparticle_sampling_trappedair = 300

ds.sndparticle_bubble_buoyancy = -4.0      # more negative = bubbles rise faster (fizz)
ds.sndparticle_bubble_drag     = 2.0
ds.sndparticle_life_min        = 8
ds.sndparticle_life_max        = 40        # spray that dissipates instead of hanging
```

Rendering the whitewater particle systems (run AFTER the Particles bake exists):

```python
import bpy

# one tiny droplet primitive, shared by all three systems
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(0, 0, -100))
droplet = bpy.context.active_object
droplet.name = "DropletInstance"
bpy.ops.object.shade_smooth()
droplet.hide_render = True

for psys in dom.particle_systems:            # "Spray", "Foam", "Bubbles"
    st = psys.settings
    st.render_type       = 'OBJECT'
    st.instance_object   = droplet
    st.particle_size     = 0.0025            # for a ~1 m domain
    st.size_random       = 0.5
    st.display_method    = 'RENDER'
    st.display_percentage = 3                # keep the viewport usable
```

### 15.7 Mantaflow Guides (only if the emitter approach cannot get the shape)

```python
ds.use_guide        = True
ds.guide_source     = 'EFFECTOR'   # or 'DOMAIN' + ds.guide_parent = other_domain_object
ds.guide_alpha      = 2.0          # "Weight"  - >4 makes water look like it is on rails
ds.guide_beta       = 5            # "Size"
ds.guide_vel_factor = 2.0          # "Velocity Factor"

# a guide effector swept along the same Follow Path curve:
guide_obj = bpy.data.objects["GuideSphere"]
gm = add_fluid_modifier(guide_obj, 'EFFECTOR')
gm.effector_settings.effector_type  = 'GUIDE'
gm.effector_settings.velocity_factor = 2.0
gm.effector_settings.guide_mode      = 'MAXIMUM'   # MAXIMUM / MINIMUM / OVERRIDE / AVERAGED
```

### 15.8 Baking

```python
import bpy

def bake(dom, what):
    """what in {'data', 'mesh', 'particles'}. Run headless for a blocking bake:
       blender -b hero.blend -P bake.py"""
    scene = bpy.context.scene
    op = {'data':      bpy.ops.fluid.bake_data,
          'mesh':      bpy.ops.fluid.bake_mesh,
          'particles': bpy.ops.fluid.bake_particles}[what]
    with bpy.context.temp_override(scene=scene, object=dom,
                                   active_object=dom, selected_objects=[dom]):
        op()

def free(dom, what):
    scene = bpy.context.scene
    op = {'data':      bpy.ops.fluid.free_data,
          'mesh':      bpy.ops.fluid.free_mesh,
          'particles': bpy.ops.fluid.free_particles,
          'all':       bpy.ops.fluid.free_all}[what]
    with bpy.context.temp_override(scene=scene, object=dom,
                                   active_object=dom, selected_objects=[dom]):
        op()

# Production order: Data -> Particles -> Mesh (mesh is the disk hog, do it last)
free(dom, 'all')
bake(dom, 'data')
bake(dom, 'particles')
bake(dom, 'mesh')
```

> **Blender 3.6 vs 4.x:** `bpy.context.temp_override(...)` above works in both. The old
> `bpy.ops.fluid.bake_data({'scene': s, 'object': o})` dict-override form was **removed in 4.0** — if you
> inherit a script that uses it, this is the fix.

### 15.9 Resolution ladder helper

```python
LADDER = {
    'block':   dict(res=100, mesh=False, particles=False, upres=2),
    'confirm': dict(res=200, mesh=True,  particles=True,  upres=2),
    'final':   dict(res=320, mesh=True,  particles=True,  upres=3),
}

def set_quality(ds, level):
    cfg = LADDER[level]
    ds.resolution_max = cfg['res']
    ds.use_mesh       = cfg['mesh']
    ds.mesh_scale     = cfg['upres']
    for p in ('use_spray_particles', 'use_foam_particles', 'use_bubble_particles'):
        setattr(ds, p, cfg['particles'])
    # high energy needs more substeps
    if cfg['res'] >= 250:
        ds.cfl_condition = 2.0
        ds.timesteps_max = 8
    print(f"[fluid] quality={level} res={cfg['res']} — FREE THE CACHE AND RE-BAKE")

set_quality(ds, 'block')
```

---

## 16. Working checklist

**Before every bake**
- [ ] Scale applied on domain, emitter, curve, and every effector (`Ctrl+A > Scale`)
- [ ] Domain rotation is zero
- [ ] Domain is a plain 8-vertex cube, display as Bounds, render visibility off
- [ ] Domain longest dimension is ~0.8–1.5 m for a product-scale splash
- [ ] Border Collisions all **off** (open domain)
- [ ] Cache Type = **Modular**, cache directory set to a real path, frame range set
- [ ] Bottle uses a **closed, decimated, slightly inflated proxy** collider, not the render mesh
- [ ] Fractional Obstacles **on**
- [ ] Emitter `Subframes` ≥ 3
- [ ] `Use Flow` keyframed to a finite burst
- [ ] Initial Velocity **on** with a Normal value (emitter motion alone imparts nothing)
- [ ] `forces` collection assigned to `Field Weights > Effector Collection`
- [ ] One thing changed since the last bake

**Blocking pass (res 100)** — Data only, no mesh, no whitewater, 2–5 min per bake, 10–20 iterations,
judged through the render camera.

**Confirm pass (res 200)** — expect 1–5 frames of timing drift. Fix leaks and flyers. Render 20 frames
at final quality and look at them as images.

**Final pass (res 250–400)** — free all, bake Data overnight, then Particles, then Mesh. Save the .blend and
back up the cache the moment you like it.

**If it looks wrong, in this order**
1. Domain size (physical scale) — 2.3
2. Emitter path, speed, burst timing — 6.3 / 5.3
3. Initial Velocity Normal — 5.4
4. Force field strengths and their keyframes — 7.4 / 7.5
5. Mesh Particle Radius and Upres — 10.1 / 10.2
6. Whitewater sampling — 9.3
7. Resolution — 4
8. FLIP Ratio — 3.2

The solver is the last thing on that list for a reason.
