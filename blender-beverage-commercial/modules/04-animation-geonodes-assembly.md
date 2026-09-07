# Module 04 — Animation, Choreography, Geometry Nodes, Rigid Bodies & Scene Assembly

**Source lineage:** reconstruction of *"lets make a beverage commercial in blender 2"* (YouTube `wXVuEPuKO_0`, 2023-10-24, Blender 3.6 LTS). Stated coverage of that video: **fluids following a curve**, **forces**, and **basic geometry nodes**. Verified against Blender 3.6 LTS behaviour and annotated for 4.x / 4.5.

**Scope of this module:** shot choreography, time remapping, product animation, curve-driven emitters, keyframed force fields and flow, geometry nodes, flying-fruit rigid bodies, modifier stack order, scene organisation, production order, troubleshooting.

**Out of scope (owned elsewhere):** Mantaflow solver tuning and resolution/cache strategy (Module 03), materials and shading, lighting, compositing. Where a solver setting is unavoidable (Time Scale, `use_inflow`, effector weights) it is covered only as an *animation control*.

**Evidence base (frame 163 of a rendered PNG sequence, so the shot is 200+ frames):**
amber bottle upright and centred; a translucent crown-splash ribbon **wrapping around** the bottle and blowing out both frame edges; green lime/apple slices and whole spheres flying **through** the splash at multiple depths and rotations, some defocused in the foreground; a field of small airborne droplets; outliner containing `Camera`, `Animation`, `Empty.001`, `Cube.001`, a `Modifiers` entry, `mountain dew bottle`, a `forces` **collection with 3 children**, and 3 further numbered objects; Physics tab showing a Fluid **Domain**, Mantaflow FLIP, Resolution 100, open domain.

---

## 1. Ad choreography — the "why" before the "how"

A beverage spot is not "a splash simulation with a bottle in it". It is a **timed reveal** in which one frame does all the selling. Everything else is runway and taxi.

### 1.1 The three laws

1. **One hero frame.** Pick the single frame that will be the poster. Everything before it is anticipation; everything after it is decay. In the reference, that frame is around **f163** — the splash has fully wrapped, fruit is mid-flight at three depths, droplets are dispersed, and the bottle is dead-centre and sharp.
2. **The camera must already be resolved when the hero frame lands.** If the camera is still moving fast, or still racking focus, or still settling from an ease, the hero frame is soft and the eye reads motion instead of product. Camera settle must complete **10–20 frames before** the splash peak. This is the single most common amateur error: the splash peaks while the push-in is still decelerating.
3. **Read time.** A brand needs roughly **0.8–1.2 s** of clean, sharp, uncluttered product at the end. At 24 fps that is 20–30 frames minimum, and it is *not* negotiable — cut runway, not read time.

### 1.2 Beat sheet — 10 s spot

The canonical structure. Columns give exact frames; use the 24 fps column unless the deliverable is PAL/EU broadcast or a 25 fps edit timeline.

| Beat | Purpose | 24 fps (240 f) | 25 fps (250 f) | What is locked here |
|---|---|---|---|---|
| **A — Dead air / anticipation** | Empty or near-empty frame, slow camera drift, atmosphere only. Buys the eye a baseline. | f1–f24 | f1–f25 | Camera start pose |
| **B — Product enters** | Bottle rises into frame, or camera pushes in on a static bottle. Never both fast at once. | f24–f48 | f25–f50 | Product screen position |
| **C — Compression / anticipation dip** | Bottle settles with a 1–2 frame overshoot. The tiny counter-move that makes the impact read. | f48–f55 | f50–f57 | The "wind-up" |
| **D — IMPACT (single frame)** | The splash contact. Inflow switches on. Force fields fire. | **f55** | **f57** | The sync point everything else hangs off |
| **E — Crown forms** | Sheet lifts, crown ring appears, first droplets shed. | f56–f72 | f58–f75 | Splash silhouette |
| **F — Bloom & wrap** | The ribbon expands, vortex curls it around the bottle, it breaks frame left and right. | f72–f140 | f75–f146 | The signature shape |
| **G — Fruit through frame** | Slices and spheres arc through the splash, staggered, at 3 depths. | f120–f180 | f125–f188 | Foreground/mid/back layering |
| **H — HERO FRAME** | Peak of everything. Camera dead still. Focus locked. | **f163** | **f170** | The poster |
| **I — Settle / decay** | Splash falls out of frame, droplets thin, fruit exits. | f180–f216 | f188–f225 | Return to clean product |
| **J — Endcard / logo** | Clean sharp product, logo/type on. | f216–f240 | f225–f250 | Read time |

### 1.3 Beat sheet — 8 s spot (192 f @ 24 fps)

Compress beats A and J, never F–H. `A f1–18 · B f18–38 · C f38–44 · D f44 · E f45–58 · F f58–112 · G f96–144 · H f130 · I f144–172 · J f172–192`.

### 1.4 Beat sheet — 12 s spot (288 f @ 24 fps)

Extend A (atmosphere), F (let the ribbon breathe), and J. `A f1–36 · B f36–66 · C f66–74 · D f74 · E f75–96 · F f96–180 · G f150–224 · H f196 · I f224–262 · J f262–288`.

### 1.5 Timing and spacing

- **Timing** = how many frames a move takes. **Spacing** = how the distance is distributed across those frames. Spacing is what sells weight; timing alone gives you a metronome.
- A bottle rising 0.9 m in 24 frames with linear spacing looks like an elevator. The same move with **ease-out** spacing (fast start, long decelerating tail) reads as a heavy glass object arriving under its own momentum.
- **Overshoot** is spacing, not timing: the bottle passes its final Z by 4–8 % of the travel distance, then returns over 8–10 frames. Under 3 % nobody sees it; over 12 % it reads as cartoon.
- **Stagger everything.** If four fruit slices all cross the frame between f130 and f150, it reads as a wipe. Offset each by 6–14 frames and vary their arc apex heights by ±20 %.

### 1.6 Why ads slow the splash down

Real liquid at real scale moves too fast to read. A 0.4 m splash resolves in ~0.35 s of real time — 8 frames at 24 fps. You cannot art-direct 8 frames, and the audience cannot parse them.

So every beverage spot runs the fluid at **2×–6× slow motion** while the camera and product move at, or near, real speed. This is the "high-speed Phantom camera" look the whole category is built on. Doing it correctly is Section 2, and doing it *incorrectly* — by slowing playback rather than the simulation — is the number-one reason amateur splashes look like syrup instead of soda.

### 1.7 Camera choreography that supports the beats

- **Push-in (dolly), not zoom.** Animate camera `location` along its local −Y; leave `lens` alone. A focal-length change during the shot reads as a documentary zoom and kills the product.
- **Settle before the hero.** Camera keyframes: start f1, arrive f140, with the last 40 frames carrying ~8 % of the travel. In F-curve terms: `EASE_OUT` on the final key with a long left handle.
- **Focus.** Parent an Empty (`EMPTY_Focus`) to the product controller and set it as `camera.data.dof.focus_object`. Rack focus, if any, must complete by hero − 15 frames.
- **A tiny handheld noise** on camera rotation (±0.15°, Noise modifier on the rotation F-curves, Scale ≈ 40, Strength ≈ 0.003 rad) makes CG splashes feel photographed. Kill it entirely during beat J.
- **Motion blur** is part of choreography, not comp: `scene.render.motion_blur_shutter = 0.5` (180° shutter). If the fluid is running at Time Scale 0.25 the *fluid* will read as slow-mo with a natural short blur, while the camera still blurs at 180° — which is exactly the real high-speed-camera artefact you want.

---

## 2. Time remapping and slow motion

There are four distinct controls and they do not do the same thing. Confusing them is the source of most "my splash looks like honey" complaints.

### 2.1 The four controls

| Control | UI location | Python | What it actually does |
|---|---|---|---|
| **Frame Rate** | Output Properties ▸ Format ▸ Frame Rate | `scene.render.fps`, `scene.render.fps_base` | Declares how many of your frames equal one second at playback. Changes *nothing* about the animation data. |
| **Time Stretching (Old / New)** | Output Properties ▸ Frame Range ▸ Time Stretching | `scene.render.frame_map_old`, `scene.render.frame_map_new` | Global scene-time remap. `Old 100 / New 200` makes the scene take twice as many frames; every animated value, including physics evaluation, is sampled at half speed. |
| **Fluid Time Scale** | Physics ▸ Fluid ▸ Domain ▸ Settings ▸ Time Scale | `dom.modifiers["Fluid"].domain_settings.time_scale` | Scales the solver's simulated `dt` per frame. **This is the correct slow-motion control for a sim.** |
| **Rigid Body Speed** | Scene Properties ▸ Rigid Body World ▸ Settings ▸ Speed | `scene.rigidbody_world.time_scale` | Same idea for the Bullet solver. |

### 2.2 Slow the simulation, not the playback

**Never** achieve slow motion by rendering at 24 fps and conforming to 96 fps in the NLE, or by using Time Stretching alone, if the shot contains a fluid.

Why: a Mantaflow bake produces one solved state per **frame**. If you take 60 frames of a splash and stretch them over 240 frames in playback, you are showing each solved state four times (or interpolating between them). You get:

- **Temporal stepping** — the mesh visibly quantises; droplets teleport between positions.
- **Wrong sub-frame detail** — the solver never computed the thin ligaments and sheet-tearing that exist *between* your original frames, so they simply do not exist. Slow-mo footage looks good precisely because those in-between states are real.
- **Broken motion blur** — vector blur derived from a stretched cache smears across frames that were never adjacent.

Setting **Time Scale 0.25** instead makes the solver advance 1/4 of the physical time per frame. It computes four times as many *distinct* states over the same physical event. The ligaments, the sheet tear, the droplet shedding — all actually simulated. That is the difference.

### 2.3 Worked example — 4× slow motion

Target: a splash whose real-world duration is 0.85 s, shown over 3.4 s of screen time at 24 fps.

1. **Screen frames needed:** 3.4 s × 24 = **82 frames** of splash. Round to 85.
2. **Time Scale:** 1 / 4 = **0.25**.
3. **Extend the frame range.** If the splash previously occupied f55–f76 (21 frames at Time Scale 1.0), at 0.25 it occupies f55–f139. Scene end goes from 240 to whatever accommodates the full beat sheet — re-derive the beat sheet *after* choosing the time scale, not before.
4. **Stretch the non-fluid animation to match.** The bottle rise, the camera push and the fruit arcs must be slowed by the same factor **if they are meant to be in the same slow-motion world**. In practice ads cheat: camera stays at ~0.6–1.0× (so it feels like a real operator) while the fluid runs at 0.25×. That cheat is standard and invisible. Fruit should match the fluid (0.25×) or it will look like it is being fired from a cannon through treacle.
5. **Raise the solver's temporal resolution.** With `time_scale = 0.25`, keep `use_adaptive_timesteps = True`, `timesteps_min = 1`, `timesteps_max = 4` (raise to 8 if you see the emitter beading). Also raise `flow_settings.subframes` to 2–4 for any fast-moving emitter.
6. **Do not scale gravity.** Reducing gravity to fake slow-mo gives the classic "moon-jump" look — the *shape* of the fluid becomes wrong (surface tension to inertia ratio changes), not just the speed. Time Scale keeps gravity physically correct and only slows the clock. This is the single most valuable insight in this section.

**Cache cost.** Cache size scales linearly with frame count. A Resolution-100 FLIP domain with a mesh (Upres 1) and whitewater is roughly **20–90 MB/frame** on disk. So:

| Frames | Approx. cache | Approx. bake wall-time (mid-range 8-core) |
|---|---|---|
| 60 (Time Scale 1.0) | 1.2–5 GB | 20–60 min |
| 240 (Time Scale 0.25) | 5–22 GB | 1.5–5 h |
| 240 @ Res 200 + Upres 2 | 60–200 GB | 12–40 h |

Budget disk **before** you bake. Set `cache_directory` to a fast local drive, never a network share or a synced folder (Dropbox/OneDrive will corrupt a bake mid-write).

### 2.4 When Time Stretching *is* the right tool

Use `frame_map_old` / `frame_map_new` for **retiming an entire already-blocked shot before any bake exists**. Blocking at 120 frames, deciding it is 30 % too fast, and setting `Old 100 / New 130` is a legitimate, five-second fix during layout. Once a fluid or rigid-body cache exists, stop using it — it changes the frame numbers your cache is keyed to.

```python
import bpy
sc = bpy.context.scene
sc.render.fps = 24
sc.render.fps_base = 1.0
# Global retime: everything now takes 30% longer.
sc.render.frame_map_old = 100
sc.render.frame_map_new = 130
# Fluid slow-motion (the correct control):
dom = bpy.data.objects["DOM_Splash"]
ds = dom.modifiers["Fluid"].domain_settings
ds.time_scale = 0.25
ds.use_adaptive_timesteps = True
ds.timesteps_min = 1
ds.timesteps_max = 4
# Rigid body slow-motion, matched, with substeps raised to compensate:
rbw = sc.rigidbody_world
rbw.time_scale = 0.25
rbw.substeps_per_frame = 40   # raise roughly in proportion to 1/time_scale
rbw.solver_iterations = 20
```

> **Trap:** lowering `rigidbody_world.time_scale` without raising `substeps_per_frame` produces tunnelling — fruit passes straight through the bottle. Rule of thumb: `substeps ≈ 10 / time_scale`.

---

## 3. Animating the product

### 3.1 Never keyframe the mesh

Animate an **Empty** that the product mesh is parented to. Reasons, all of which will bite you otherwise:

- The bottle asset will be replaced (higher-res model, client's actual bottle, new label). If the animation lives on the mesh object it dies with it. If it lives on `CTRL_Bottle`, you swap the mesh and the animation survives untouched.
- A linked/appended asset from another `.blend` cannot carry your local animation cleanly; the empty can.
- The fluid domain and any obstacle proxy need to follow the same motion. Parent them all to the same empty and they are locked together by construction.
- You retain the mesh's own local transform as a *rest offset* — so you can nudge the bottle's origin without touching a single keyframe.

This is almost certainly what `Empty.001` in the observed outliner is: a controller null. (`Empty` — unnumbered and not shown — was probably consumed as the emitter or focus target; `.001` implies at least two empties exist.)

### 3.2 The rise

At 24 fps, from the beat sheet: enters at f18, arrives f42, settles f52.

| Frame | `location.z` | Interpolation | Note |
|---|---|---|---|
| 18 | −0.85 | Bezier, `EASE_OUT` on this key | Below frame bottom |
| 42 | +0.055 | Bezier, `AUTO_CLAMPED` | Overshoot ≈ 6 % of travel |
| 52 | 0.0 | Bezier, `EASE_IN` | Settle |

Handle discipline: give the f18 key a **long right handle** (roughly 0.6× the interval to f42) so the departure is fast and the arrival is slow. Give f42 a short handle so the overshoot snaps back.

### 3.3 The hero rotation

**Rotate 10–20° across the entire shot. Not more.**

Why not a full spin: a spinning bottle destroys label readability, and label readability is the deliverable. A slow 14° drift does three things: it reveals the cylinder's form through moving specular highlights, it proves to the eye that the object is 3D and lit, and it never takes the logo off-axis. Every professional beverage spot does exactly this.

| Frame | `rotation_euler.z` | Note |
|---|---|---|
| 18 | −7° (−0.1222 rad) | Label already 95 % readable at entry |
| 240 | +7° (+0.1222 rad) | 14° total, near-linear with soft ends |

Set interpolation to `BEZIER` with `AUTO_CLAMPED` handles and one key at each end — the resulting curve is a very gentle S. Do **not** use `LINEAR`; a constant angular velocity across 220 frames reads as a turntable, not a hero.

Optional micro-detail: a second rotation of ±1.5° on X with a Noise F-Modifier (Scale 60, Strength 0.008) between f55 and f110 sells the splash's impact pressure on the bottle. Kill it before beat J.

### 3.4 Delta transforms

`delta_location`, `delta_rotation_euler` and `delta_scale` are applied *on top of* the animated channels. Use them for:

- **Global repositioning after animation is approved.** Client wants the bottle 4 cm to camera-left: set `delta_location.x = -0.04`. Zero keyframes touched, no risk of clobbering an approved curve.
- **Instancing variation.** Three identical fruit objects sharing one action, each with a different `delta_rotation_euler`.
- They are themselves keyframable, which lets you layer a secondary animation on a channel that already has a primary one — useful when a primary curve is locked by a supervisor.

### 3.5 Copy-pasteable: empty-parent product rig with keyframes

```python
"""
04_product_rig.py — Empty-parent controller for the hero product, with
rise / overshoot / settle and a slow hero rotation.
Blender 3.6 LTS through 4.5. Run from the Text Editor or via --python.
"""
import bpy
import math

FPS          = 24
FRAME_START  = 1
FRAME_END    = 240
F_ENTER      = 18
F_ARRIVE     = 42
F_SETTLE     = 52
RISE_FROM_Z  = -0.85
OVERSHOOT_Z  = 0.055
HERO_DEG     = 14.0        # total rotation across the whole shot
PRODUCT_NAME = "mountain dew bottle"
CTRL_NAME    = "CTRL_Bottle"


# ---------------------------------------------------------------- utilities
def action_fcurves(id_data):
    """F-curves of an ID's active action, across legacy and 4.4+ slotted actions."""
    ad = getattr(id_data, "animation_data", None)
    if not ad or not ad.action:
        return []
    act = ad.action
    fcs = getattr(act, "fcurves", None)
    if fcs is not None and len(fcs):
        return list(fcs)
    out = []                                    # Blender 4.4+ slotted actions
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out.extend(cb.fcurves)
    return out


def shape_keys(id_data, data_path, index=-1, interpolation='BEZIER',
               easing='AUTO', handle='AUTO_CLAMPED'):
    for fc in action_fcurves(id_data):
        if fc.data_path != data_path:
            continue
        if index >= 0 and fc.array_index != index:
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = interpolation
            kp.easing        = easing
            kp.handle_left_type  = handle
            kp.handle_right_type = handle
        fc.update()


def key_at(ob, path, frame, index=-1):
    if index >= 0:
        ob.keyframe_insert(data_path=path, index=index, frame=frame)
    else:
        ob.keyframe_insert(data_path=path, frame=frame)


def parent_keep_transform(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


# ---------------------------------------------------------------- scene setup
sc = bpy.context.scene
sc.render.fps  = FPS
sc.frame_start = FRAME_START
sc.frame_end   = FRAME_END

# ---------------------------------------------------------------- controller
ctrl = bpy.data.objects.get(CTRL_NAME)
if ctrl is None:
    ctrl = bpy.data.objects.new(CTRL_NAME, None)
    sc.collection.objects.link(ctrl)
ctrl.empty_display_type = 'PLAIN_AXES'
ctrl.empty_display_size = 0.25
ctrl.location = (0.0, 0.0, 0.0)
ctrl.rotation_euler = (0.0, 0.0, 0.0)

product = bpy.data.objects.get(PRODUCT_NAME)
if product:
    parent_keep_transform(product, ctrl)

# ---------------------------------------------------------------- rise
ctrl.location.z = RISE_FROM_Z
key_at(ctrl, "location", F_ENTER, index=2)
ctrl.location.z = OVERSHOOT_Z
key_at(ctrl, "location", F_ARRIVE, index=2)
ctrl.location.z = 0.0
key_at(ctrl, "location", F_SETTLE, index=2)

shape_keys(ctrl, "location", index=2, interpolation='BEZIER',
           easing='AUTO', handle='AUTO_CLAMPED')

# Fast departure / slow arrival: lengthen the f18 right handle manually.
for fc in action_fcurves(ctrl):
    if fc.data_path == "location" and fc.array_index == 2:
        kps = sorted(fc.keyframe_points, key=lambda k: k.co.x)
        if len(kps) >= 2:
            k0, k1 = kps[0], kps[1]
            k0.handle_right_type = 'FREE'
            k0.handle_right = (k0.co.x + (k1.co.x - k0.co.x) * 0.62,
                               k0.co.y + (k1.co.y - k0.co.y) * 0.72)
            k1.handle_left_type = 'FREE'
            k1.handle_left = (k1.co.x - (k1.co.x - k0.co.x) * 0.22, k1.co.y)
        fc.update()

# ---------------------------------------------------------------- hero rotation
half = math.radians(HERO_DEG * 0.5)
ctrl.rotation_euler.z = -half
key_at(ctrl, "rotation_euler", F_ENTER, index=2)
ctrl.rotation_euler.z = +half
key_at(ctrl, "rotation_euler", FRAME_END, index=2)
shape_keys(ctrl, "rotation_euler", index=2, interpolation='BEZIER',
           easing='AUTO', handle='AUTO_CLAMPED')

# ---------------------------------------------------------------- delta offset
# Client-note-proof global nudge that never touches a keyframe:
ctrl.delta_location = (0.0, 0.0, 0.0)

print("Product rig built on:", ctrl.name)
```

---

## 4. Animating the emitter along a curve — the headline technique

This is the technique the video is named for: **making fluid follow a curve**. There is no "fluid follows curve" button. What you actually do is move the *inflow emitter* along a curve and let the fluid inherit that motion. The ribbon that wraps around the bottle in the reference frame is the trail of an emitter that has flown a helical path around it.

### 4.1 Choose the right mechanism

| Mechanism | What moves | Use when | Avoid when |
|---|---|---|---|
| **Follow Path constraint** | The whole emitter object rides the curve | Emitter is a small blob/plane you want flying along a path. **This is the one you want.** | You need the emitter *shape* to bend |
| **Curve modifier** | The emitter *mesh* is deformed along the curve | You want a long ribbon-shaped emitter conforming to the curve | Anything animated — the modifier's motion comes from moving the mesh through the deform axis, which is fiddly and produces velocity artefacts |
| **Path Animation (curve `use_path` + parenting)** | Legacy Ctrl+P ▸ Follow Path parenting | Never in new work | Always — the constraint supersedes it |
| **Fluid Guide effector** | Nothing — the *velocity field* is steered | You want the fluid volume itself nudged along a direction without an emitter | You need fine art direction (it is blunt) |

### 4.2 The recipe

**Step 1 — Build the curve.**
`Add ▸ Curve ▸ Bezier`. Model a path that starts below/behind the bottle, spirals up and around it, and exits frame. In edit mode use `Alt+S` on selected control points to change **radius** (this scales a Follow-Path-Radius-enabled child, and controls curve bevel) and `Ctrl+T` to change **tilt** (this rolls the child).

Curve object data settings that matter:
- **Shape ▸ Resolution Preview U** = 24 (low resolution makes the emitter step)
- **Shape ▸ Twist Method** = `Z-Up` for a stable, non-flipping ride; `Minimum` if you need the twist to follow the curve's natural frame; `Tangent` for tightly-coiled helices.
- **Shape ▸ Twist Smooth** = 1.0–2.0 to damp tilt popping between control points.
- **Path Animation ▸ Frames** (`path_duration`) = the number of frames one full traversal takes. Default 100.
- **Path Animation ▸ Evaluation Time** (`eval_time`) = current position, 0 → `path_duration` maps to curve start → end.

**Step 2 — Add the emitter.**
A small UV Sphere (r ≈ 0.03–0.06 m) or a subdivided plane. Keep it *small*: a big emitter dumps a slab of liquid, a small one draws a rope. Name it `EMIT_Ribbon`.

**Step 3 — Constrain it.**
`Object Constraint Properties ▸ Add ▸ Follow Path`.
- **Target** = your curve.
- **Follow Curve** (`use_curve_follow`) = **ON**. Without this the emitter translates along the path but keeps world rotation, so `velocity_normal` sprays in a fixed direction the whole way. With it on, the emitter's forward axis tracks the tangent and the spray fans outward correctly along the whole path.
- **Forward Axis** = `Y`, **Up Axis** = `Z` (adjust so the emitter's normals face where you want liquid thrown).
- **Curve Radius** (`use_curve_radius`) = ON if you want the emitter to scale with the curve radius — a beautiful cheap way to make the ribbon thicken at the crown and thin at the tail.
- **Fixed Position** (`use_fixed_location`) = your choice; see 4.3.

**Step 4 — Drive the motion.** Two mutually exclusive routes, below.

**Step 5 — Add the Fluid Flow modifier.**
`Physics ▸ Fluid ▸ Type: Flow`, `Flow Type: Liquid`, `Flow Behavior: Inflow`.

**Step 6 — Set velocity and subframes** (Section 4.5).

### 4.3 Route A — `Evaluation Time` on the curve (recommended)

Leave **Fixed Position OFF**. The emitter's position along the path is `curve.data.eval_time / curve.data.path_duration`.

Animate `eval_time` on the **curve data**, not the object:

```python
crv.data.eval_time = 0.0
crv.data.keyframe_insert("eval_time", frame=55)
crv.data.eval_time = 100.0
crv.data.keyframe_insert("eval_time", frame=140)
```

Advantages: the F-curve *is* the speed graph of the emitter. Ease it, add a hold, reverse it, add a Noise modifier — you are directly authoring the emitter's velocity profile, which is exactly what determines the shape of the resulting ribbon.

Blender ships an operator that builds this curve for you:

```python
bpy.ops.constraint.followpath_path_animate(
    constraint="Follow Path", owner='OBJECT', frame_start=55, length=85)
```

This adds a linear `eval_time` F-curve from frame 55 over 85 frames. Then go and *ease it* — linear is almost never right.

> **Gotcha:** if `eval_time` has no animation and no keyframes, the emitter sits frozen at whatever static value `eval_time` holds. "My object won't move along the path" is nearly always this.

### 4.4 Route B — `Offset Factor` on the constraint

Turn **Fixed Position ON**. Now the constraint exposes **Offset Factor** (`offset_factor`), a normalised 0–1 position, and ignores `eval_time` entirely.

```python
con.use_fixed_location = True
con.offset_factor = 0.0
con.keyframe_insert("offset_factor", frame=55)
con.offset_factor = 1.0
con.keyframe_insert("offset_factor", frame=140)
```

Advantages: normalised 0–1 is resolution-independent — you can re-model the curve, add control points, change its length, and the animation still runs start-to-end. The animation lives on the *object*, so it travels with the object into another scene.

Use Route B when the curve is still being art-directed. Use Route A when you want fine control of the velocity profile and the curve is locked.

With Fixed Position **off**, the constraint's `offset` field is in **frames** and is subtracted from `eval_time` — that is your per-emitter stagger control when you run three emitters on one shared curve. Set `offset = -12`, `-24` on emitters two and three and you get a braided triple ribbon from a single animated curve.

### 4.5 Making the emitter spray outward — tilt, twist, and initial velocity

The reference ribbon does not merely *travel* around the bottle, it *throws liquid outward*. That comes from combining three velocity sources:

1. **Inherited path velocity** — `flow_settings.velocity_factor` ("Source" in the UI, under Initial Velocity). This multiplies the emitter object's own frame-to-frame motion into the fluid. `1.0` = fluid leaves the emitter at exactly the emitter's speed. Values 1.0–2.0 give the whipping tail. **This is the property that makes "fluid follows a curve" actually work.** Set it to 0 and your liquid just drips out of a moving hole.
2. **Normal velocity** — `flow_settings.velocity_normal`. Ejects liquid along the emitter's surface normals. Because the emitter is rotating with the curve (Follow Curve ON), the normals sweep outward as it travels. Values 1.0–3.0.
3. **Fixed world velocity** — `flow_settings.velocity_coord` (X/Y/Z). A constant world-space push. Use sparingly; it fights the path motion. Good for a single downward bias.

**Tilt is what aims (2).** In edit mode select control points and `Ctrl+T` (or set `bezier_points[i].tilt` in radians). Rolling the curve by 90° over the section that passes behind the bottle throws the sheet outward toward camera instead of into the bottle. This is the specific trick that produces the "wraps around and breaks the frame edges" silhouette.

**Subframes are mandatory.** A fast emitter samples once per frame and leaves a dotted line of blobs. `flow_settings.subframes = 2–5` makes the solver interpolate the emitter transform between frames and emit continuously. Cost is roughly linear in bake time. If your ribbon looks like a string of pearls, this is the fix — every time.

### 4.6 Copy-pasteable: curve + Follow Path emitter

```python
"""
04_curve_emitter.py — Bezier path around the product, an inflow emitter riding it
with Follow Path, and the flow settings that make the liquid inherit path motion.
Blender 3.6 LTS through 4.5.
"""
import bpy
import math
from mathutils import Vector

CURVE_NAME   = "CRV_EmitterPath"
EMIT_NAME    = "EMIT_Ribbon"
F_LAUNCH     = 55
F_LAND       = 140
PATH_FRAMES  = 100
USE_FIXED    = False        # False = Route A (eval_time), True = Route B (offset_factor)

# Helical path around a bottle standing at the origin, radius ~0.42 m.
# (co, tilt_degrees) — tilt rolls the emitter so its normals throw outward.
PTS = [
    (Vector((-0.95, -0.30, -0.35)),   0.0),
    (Vector((-0.42, -0.42,  0.10)),  25.0),
    (Vector(( 0.00, -0.50,  0.42)),  55.0),
    (Vector(( 0.44, -0.36,  0.70)),  80.0),
    (Vector(( 0.52,  0.10,  0.86)), 100.0),
    (Vector(( 0.16,  0.46,  0.95)),  75.0),
    (Vector((-0.40,  0.40,  0.82)),  40.0),
    (Vector((-1.05,  0.16,  0.55)),   0.0),
]

sc = bpy.context.scene

# ------------------------------------------------------------------ the curve
cd = bpy.data.curves.new(CURVE_NAME, 'CURVE')
cd.dimensions      = '3D'
cd.resolution_u    = 24
cd.twist_mode      = 'Z_UP'      # stable ride; 'MINIMUM' / 'TANGENT' also valid
cd.twist_smooth    = 1.5
cd.use_path        = True
cd.path_duration   = PATH_FRAMES

sp = cd.splines.new('BEZIER')
sp.bezier_points.add(len(PTS) - 1)
for bp, (co, tilt_deg) in zip(sp.bezier_points, PTS):
    bp.co = co
    bp.handle_left_type  = 'AUTO'
    bp.handle_right_type = 'AUTO'
    bp.tilt   = math.radians(tilt_deg)
    bp.radius = 1.0

crv = bpy.data.objects.new(CURVE_NAME, cd)
sc.collection.objects.link(crv)

# ------------------------------------------------------------------ emitter
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, segments=16, ring_count=8,
                                     location=(0, 0, 0))
emit = bpy.context.active_object
emit.name = EMIT_NAME
emit.display_type = 'WIRE'          # keep the viewport readable
emit.hide_render  = True            # the emitter is never rendered

# ------------------------------------------------------------------ constraint
con = emit.constraints.new('FOLLOW_PATH')
con.name              = "Follow Path"
con.target            = crv
con.use_curve_follow  = True        # <- rotates emitter to the tangent: essential
con.use_curve_radius  = True        # ribbon thickens/thins with curve radius
con.forward_axis      = 'FORWARD_Y'
con.up_axis           = 'UP_Z'
con.use_fixed_location = USE_FIXED

if USE_FIXED:
    # ---- Route B: normalised 0..1 on the constraint
    con.offset_factor = 0.0
    con.keyframe_insert("offset_factor", frame=F_LAUNCH)
    con.offset_factor = 1.0
    con.keyframe_insert("offset_factor", frame=F_LAND)
    anim_id = emit
    path    = 'constraints["Follow Path"].offset_factor'
else:
    # ---- Route A: Evaluation Time on the curve DATA
    cd.eval_time = 0.0
    cd.keyframe_insert("eval_time", frame=F_LAUNCH)
    cd.eval_time = float(PATH_FRAMES)
    cd.keyframe_insert("eval_time", frame=F_LAND)
    anim_id = cd
    path    = 'eval_time'

# Ease the traversal: fast launch, decelerating tail.
ad = anim_id.animation_data
if ad and ad.action:
    fcs = getattr(ad.action, "fcurves", None) or []
    if not len(fcs):
        fcs = [f for L in ad.action.layers for s in L.strips
                 for cb in s.channelbags for f in cb.fcurves]
    for fc in fcs:
        if fc.data_path != path:
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        kps = sorted(fc.keyframe_points, key=lambda k: k.co.x)
        if len(kps) >= 2:
            kps[0].easing  = 'EASE_OUT'
            kps[-1].easing = 'EASE_IN'
        fc.update()

# ------------------------------------------------------------------ fluid flow
mod = emit.modifiers.new("Fluid", 'FLUID')
mod.fluid_type = 'FLOW'
fs = mod.flow_settings
fs.flow_type            = 'LIQUID'
fs.flow_behavior        = 'INFLOW'
fs.use_inflow           = True
fs.use_initial_velocity = True
fs.velocity_factor      = 1.35      # inherit the PATH motion  <- the key setting
fs.velocity_normal      = 1.80      # throw outward along normals
fs.velocity_coord       = (0.0, 0.0, -0.4)
fs.subframes            = 3         # <- kills the "string of pearls" beading
fs.surface_distance     = 1.5
fs.use_plane_init       = False

# ------------------------------------------------------------------ burst window
# Emit for exactly 26 frames, then shut off. Booleans must be CONSTANT.
BURST = (F_LAUNCH, F_LAUNCH + 26)
fs.use_inflow = False
fs.keyframe_insert("use_inflow", frame=BURST[0] - 1)
fs.use_inflow = True
fs.keyframe_insert("use_inflow", frame=BURST[0])
fs.use_inflow = False
fs.keyframe_insert("use_inflow", frame=BURST[1])

for L_owner in (mod,):
    ad = fs.id_data.animation_data
if emit.animation_data and emit.animation_data.action:
    for fc in (getattr(emit.animation_data.action, "fcurves", []) or []):
        if fc.data_path.endswith("use_inflow"):
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'
            fc.update()

print("Curve emitter built:", emit.name, "->", crv.name)
```

> **Note on the boolean F-curve:** `use_inflow` keyframes are stored on the *object's* animation data with a `modifiers["Fluid"].flow_settings.use_inflow` data path. Always force `CONSTANT` interpolation — a Bezier-interpolated boolean produces a half-open inflow for several frames and a mushy start to the splash.

### 4.7 Alternative — Fluid Guide effectors ("follow a curve" without an emitter)

If you want the *existing* liquid volume steered rather than new liquid injected: set an object to `Physics ▸ Fluid ▸ Effector`, `Effector Type: Guide`, animate that object along the curve, and on the Domain enable `Guides` with `Guide Source: Effector`. `guide_alpha` (Weight) sets how hard the guide overrides the solved velocity; `guide_beta` (Size) sets the influence radius. This is blunt but excellent for "sweep the whole splash left as the camera pans". Detailed parameters are Module 03's territory.

---

## 5. Keyframing force fields and flow

### 5.1 Why force fields at all

Real splashes do not wrap around a bottle. They fall. The wrap in the reference frame is *art direction* — produced by a rotational field pulling the sheet around the product. Every hero splash in the category is force-driven.

Mantaflow FLIP liquids respond to Blender force fields, gated per-type by the **domain's Effector Weights** (`domain_settings.effector_weights`). Both the field's `strength` and the domain's per-type weight are keyframable, giving you two independent handles.

### 5.2 The animation shape that works

Force fields must **ramp on, peak, and ramp off**. A constant-strength vortex spins the fluid into a smooth donut and looks CG. The profile that works:

```
strength
   ^                  ____
   |                 /    \___
   |                /         \____
   |   ___________ /               \______
   +-------------------------------------------> frame
      f55        f70      f110      f150   f190
      (impact)  (bloom)  (peak)   (decay) (settle)
```

Key at 0 before impact, ramp to peak over 30–50 frames, hold ~20 frames through the hero frame, decay to ~15 % by settle. Never return to exactly 0 during the shot — a hard zero causes a visible "release" pop as the fluid snaps back to ballistic motion.

### 5.3 Interpreting the `forces` collection with 3 children

Both readings below are production-valid. Build whichever the shot needs; the reference silhouette (a ribbon that curls around the product and breaks both frame edges) argues strongly for Rig A.

#### Rig A — the classic "bloom rig": Vortex + Force + Turbulence

| Object | Field type | Placement | Animation | Job |
|---|---|---|---|---|
| `FLD_Vortex` | `VORTEX` | Bottle centre, Z-axis aligned | 0 @f55 → 9.0 @f110 → 3.0 @f190 | **Wraps the sheet around the bottle.** This is the shape-maker. |
| `FLD_Push` | `FORCE` | Bottle base, `shape='POINT'` | 0 @f55 → 6.0 @f72 → 0.8 @f120 → −1.2 @f170 | Blows the crown outward, then the negative tail draws the tail back so it does not just leave frame |
| `FLD_Turb` | `TURBULENCE` | Bottle centre, large | 0 @f60 → 3.2 @f140 → 1.0 @f200 | Breaks the sheet into droplets and ligaments; kills the "plastic bag" look |

Critical per-field settings: `use_max_distance = True` and `distance_max ≈ 0.6–1.2 m` on all three, and `falloff_power ≈ 1.5–2.5`. Without a distance limit the vortex spins the *entire domain* and the splash becomes a whirlpool.

For the turbulence: `field.size = 0.4–0.8` (small = fine spray, large = big lobes), `field.flow = 0.2` (adds drag toward the field's velocity, calms explosions), `field.noise = 2.0`, and animate `field.seed` **never** — a changing seed makes the noise field jump.

#### Rig B — three orbiting point Forces

Three `FORCE` empties parented to a single rotating null (`CTRL_ForceOrbit`, keyframed 0° → 140° over f55–f180), placed at 120° intervals at radius 0.35 m, each with `strength = 5.0`, `use_max_distance = True`, `distance_max = 0.45`, `falloff_power = 2.0`.

This produces three discrete lobes on the crown that sweep around the bottle — a more graphic, more "designed" splash than Rig A's continuous ribbon. Use it when the brand board shows a stylised three-petal splash. Animate the *parent's* rotation, not the fields' positions.

### 5.4 Keyframing the flow itself

- **`use_inflow`** ("Use Flow" in the UI, Inflow behaviour only). Keyframe with **CONSTANT** interpolation to emit for exactly N frames. This is how you get one clean slug of liquid instead of a fire-hose.
- **`use_effector`** on a Fluid Effector. Keyframe to `False` before the fruit arrives and `True` on the frame it enters the splash — the fruit then only starts pushing liquid when it should, and does not disturb the crown while it is still off-screen. Also CONSTANT.
- **`effector_weights.force` / `.vortex` / `.turbulence` / `.gravity`** on the domain. Keyframe `gravity` from 1.0 down to 0.55 across f100–f150 to make the splash *hang* at the hero frame — a completely invisible cheat, and the one that gets you a poster frame. Return it to 1.0 by f200 so the settle looks right.
- **`velocity_factor`** on the flow, keyframed 2.0 → 0.6 across the burst, gives a whip-crack: fast leading edge, slower tail.

### 5.5 Copy-pasteable: animated force rig

```python
"""
04_forces.py — Builds a 'FORCES' collection with a keyframed Vortex + Force +
Turbulence bloom rig, plus domain effector-weight keyframes for a hero hang.
Blender 3.6 LTS through 4.5.
"""
import bpy
import math

DOMAIN_NAME = "DOM_Splash"        # or "Cube.001" in the reference file
COLL_NAME   = "FORCES"
F_IMPACT, F_BLOOM, F_PEAK, F_DECAY, F_SETTLE = 55, 72, 110, 150, 190

sc = bpy.context.scene

# ------------------------------------------------------------- collection
coll = bpy.data.collections.get(COLL_NAME)
if coll is None:
    coll = bpy.data.collections.new(COLL_NAME)
    sc.collection.children.link(coll)


def move_to(ob, target_coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    target_coll.objects.link(ob)


def const_bool_curves(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    fcs = getattr(ad.action, "fcurves", None) or []
    for fc in fcs:
        if fc.data_path.endswith(("use_inflow", "use_effector", "kinematic")):
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'
            fc.update()


def add_field(name, ftype, loc, rot=(0, 0, 0)):
    bpy.ops.object.effector_add(type=ftype, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.empty_display_size = 0.25
    move_to(ob, coll)
    return ob


def key_strength(ob, pairs, easing='AUTO'):
    for frame, val in pairs:
        ob.field.strength = val
        ob.field.keyframe_insert("strength", frame=frame)
    ad = ob.animation_data
    if ad and ad.action:
        for fc in (getattr(ad.action, "fcurves", None) or []):
            if not fc.data_path.endswith("strength"):
                continue
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.easing = easing
                kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
            fc.update()


# ------------------------------------------------------------- 1. VORTEX (the wrap)
vort = add_field("FLD_Vortex", 'VORTEX', (0.0, 0.0, 0.45))
vort.field.shape            = 'POINT'
vort.field.use_max_distance = True
vort.field.distance_max     = 0.95
vort.field.falloff_power    = 2.0
vort.field.flow             = 0.15
key_strength(vort, [(F_IMPACT, 0.0), (F_PEAK, 9.0), (F_SETTLE, 3.0)])

# ------------------------------------------------------------- 2. FORCE (the bloom)
push = add_field("FLD_Push", 'FORCE', (0.0, 0.0, 0.05))
push.field.shape            = 'POINT'
push.field.use_max_distance = True
push.field.distance_max     = 0.70
push.field.falloff_power    = 1.5
key_strength(push, [(F_IMPACT, 0.0), (F_BLOOM, 6.0),
                    (F_PEAK + 10, 0.8), (F_DECAY + 20, -1.2)])

# ------------------------------------------------------------- 3. TURBULENCE (breakup)
turb = add_field("FLD_Turb", 'TURBULENCE', (0.0, 0.0, 0.55))
turb.field.size             = 0.55
turb.field.noise            = 2.0
turb.field.flow             = 0.20
turb.field.seed             = 7          # never animate the seed
turb.field.use_max_distance = True
turb.field.distance_max     = 1.30
key_strength(turb, [(F_IMPACT + 5, 0.0), (F_DECAY, 3.2), (F_SETTLE + 10, 1.0)])

# ------------------------------------------------------------- domain weights
dom = bpy.data.objects.get(DOMAIN_NAME)
if dom and "Fluid" in dom.modifiers:
    ds = dom.modifiers["Fluid"].domain_settings
    ew = ds.effector_weights
    ew.force = ew.vortex = ew.turbulence = 1.0
    # The invisible "hero hang": let gravity fall off through the poster frame.
    ew.gravity = 1.00; ew.keyframe_insert("gravity", frame=F_BLOOM)
    ew.gravity = 0.55; ew.keyframe_insert("gravity", frame=F_PEAK + 25)
    ew.gravity = 1.00; ew.keyframe_insert("gravity", frame=F_SETTLE + 15)
    print("Domain effector weights keyed on:", dom.name)
else:
    print("WARNING: domain '%s' not found — skipped effector weights." % DOMAIN_NAME)

const_bool_curves(vort); const_bool_curves(push); const_bool_curves(turb)
print("Force rig built in collection:", coll.name)
```

---

## 6. Geometry Nodes

The video's third stated pillar. Five setups follow, written as explicit node chains with socket names and values, then one full Python build.

### 6.0 Version differences you must know

| Change | 3.6 LTS | 4.0 | 4.2+ | Impact |
|---|---|---|---|---|
| **Node-group interface API** | `ng.inputs.new('NodeSocketGeometry', "Geometry")` | `ng.interface.new_socket(name=..., in_out='INPUT', socket_type=...)` | same as 4.0 | **Breaks every 3.6 GN script.** Branch on `bpy.app.version`. |
| **Modifier input keys** | `mod["Input_2"]` | `mod["Socket_2"]` | `mod["Socket_2"]` | Read `socket.identifier` instead of hard-coding. |
| **Rotation socket type** | Rotation inputs are `Vector` (Euler) | `Vector` | **`Rotation`** socket | A `Random Value → Instance on Points ▸ Rotation` link needs an **Euler to Rotation** node in 4.2+. |
| **Align Euler to Vector** | `FunctionNodeAlignEulerToVector` | same | **Align Rotation to Vector** (`FunctionNodeAlignRotationToVector`) | Rename + socket type change. |
| **Distribute Points on Faces ▸ Rotation output** | Vector | Vector | Rotation | Direct link to Instance on Points still works (both changed together). |
| **Mesh to Volume** | has `Fill Volume`, `Exterior Band Width` | those removed; always fills | same | Remove those from 3.6 scripts when porting up. |
| **Simulation Zone** | **introduced in 3.6** | yes | yes | Safe to use across the whole range. |
| **Bake node / Index Switch / Menu Switch** | — | — | 4.1+ | Don't use if the file must open in 3.6. |
| **For Each Element zone** | — | — | 4.3+ | Same. |
| **Slotted Actions** (`action.fcurves` deprecated) | n/a | n/a | **4.4+** | Affects animation scripts, not GN. |

**Random Value node socket indices** (a classic scripting trap — the node carries every data type's sockets simultaneously and the names collide):

```
inputs[0] Min  (Vector)   inputs[1] Max  (Vector)
inputs[2] Min  (Float)    inputs[3] Max  (Float)
inputs[4] Min  (Int)      inputs[5] Max  (Int)
inputs[6] Probability     inputs[7] ID     inputs[8] Seed
outputs[0] Value (Vector) outputs[1] Value (Float)
outputs[2] Value (Int)    outputs[3] Value (Bool)
```

Always index by number, never by name, on `FunctionNodeRandomValue`.

---

### 6a. Airborne micro-droplets, driven off the fluid mesh

The field of small droplets in the reference frame. The trick is to scatter them **only where the water actually is**, so they appear and disappear with the splash instead of floating in a static cloud.

**Graph (apply on an empty mesh object named `GN_Droplets`, parented to the domain):**

```
Object Info                     ── Object: DOM_Splash
  · As Instance    : OFF          (we need real geometry)
  · Transform Space: RELATIVE
  └ Geometry ─────────────────▶ Distribute Points on Faces
                                  · Distribute Method : RANDOM
                                  · Density  : 900.0
                                  · Seed     : 3
                                  ├ Points ───────────▶ Set Position ▸ Geometry
                                  └ Normal ──▶ Vector Math (SCALE, Scale 0.06)
                                                     └▶ Set Position ▸ Offset
Set Position ▸ Geometry ───────▶ Instance on Points ▸ Points
Ico Sphere (Radius 0.004, Subdivisions 2)
                       ─────────▶ Instance on Points ▸ Instance
Random Value (FLOAT, Min 0.35, Max 1.60, Seed 11)
                       ─────────▶ Instance on Points ▸ Scale
Random Value (VECTOR, Min (-3.14,-3.14,-3.14), Max (3.14,3.14,3.14), Seed 12)
    [4.2+: → Euler to Rotation] ▶ Instance on Points ▸ Rotation
Instance on Points ▸ Instances ▶ Set Material (Material: MAT_Droplet)
                               ▶ Group Output ▸ Geometry
```

**Why `Set Position` with a normal offset:** points sitting exactly on the fluid surface get shaded as part of the water and vanish. Pushing them 4–8 cm along the surface normal lifts them into the air where they read as spray.

**Making them appear only on fast-moving water:** enable `Mesh ▸ Speed Vectors` on the domain (`domain_settings.use_speed_vectors = True`). The fluid mesh then carries a `velocity` vector attribute. Insert:

```
Named Attribute ("velocity", type VECTOR)
  └▶ Vector Math (LENGTH)
       └▶ Map Range (From Min 0.5, From Max 6.0, To Min 0.0, To Max 1.0, Clamp ON)
            └▶ Math (MULTIPLY, second value 1400)
                 └▶ Distribute Points on Faces ▸ Density
```

Now droplets only spawn off crests moving faster than 0.5 m/s, and their count scales with speed. This single addition is the difference between "confetti" and "spray".

**Realize Instances:** append `Realize Instances` **only** if a downstream node needs real geometry (a boolean, an extrude, exporting to Alembic). Cycles and EEVEE render instances natively and *far* more cheaply. Realizing 40,000 icospheres at subdiv 2 is 3.2 M triangles of real mesh; leaving them instanced is 320 triangles plus a transform list.

---

### 6b. Whitewater / spray / foam / bubbles

**Read this before you build it.** Mantaflow whitewater is emitted as **particle systems** on the domain object (named `Spray`, `Foam`, `Bubbles`, `Tracer`). Geometry Nodes in 3.6–4.5 **cannot read particle systems directly** — there is no "Particles to Points" node. Three honest routes:

**Route 1 — native particle rendering (fastest, use this first).**
Select the domain, `Particle Properties ▸ [the whitewater system] ▸ Render ▸ Render As: Object`, pick a low-poly icosphere, set `Scale` 0.006 and `Scale Randomness` 0.7. Zero geometry nodes, near-zero overhead. For 90 % of shots this is the right answer.

**Route 2 — bake particles to a point mesh, then use GN.**
Run this once after the whitewater bake; it produces a mesh whose vertices are the particle positions, per frame, which GN *can* read:

```python
import bpy
dom = bpy.data.objects["DOM_Splash"]
dg  = bpy.context.evaluated_depsgraph_get()
dom_eval = dom.evaluated_get(dg)
psys = dom_eval.particle_systems["Spray"]        # or "Foam" / "Bubbles"

me = bpy.data.meshes.new("WW_Points")
locs = [tuple(p.location) for p in psys.particles if p.alive_state == 'ALIVE']
me.from_pydata(locs, [], [])
me.update()
ob = bpy.data.objects.new("WW_Points", me)
bpy.context.scene.collection.objects.link(ob)
```

Wrap it in a `frame_change_post` handler to rebuild per frame, or export the whole range to an Alembic point cache. Then feed `Object Info(WW_Points) ▸ Geometry` into `Mesh to Points (Mode: Vertices)` and instance as in 6a.

**Route 3 — derive spray from the liquid mesh (no particles at all).**
Exactly the velocity-gated scatter in 6a. Cheaper, fully art-directable, and it never desynchronises from the mesh. In practice this is what most commercial artists ship.

**Graph for Route 2 / 3, once you have points:**

```
[point source] ─▶ Instance on Points ▸ Points
Ico Sphere (Radius 0.0035, Subdivisions 1) ─▶ Instance on Points ▸ Instance
Random Value (FLOAT, Min 0.4, Max 2.2, ID ← Index, Seed 5)
                                           ─▶ Instance on Points ▸ Scale
Instance on Points ▸ Instances ─▶ Set Material (MAT_Whitewater) ─▶ Group Output
```

Feed `Index` into the Random Value `ID` input so each particle keeps a stable size frame to frame — otherwise every droplet flickers in scale as the point order changes.

---

### 6c. Procedural condensation on the bottle

Beads of moisture on cold glass. Apply the modifier **to the bottle**, after the Subdivision but before any Bevel (see Section 9).

```
Group Input ▸ Geometry ──┬──────────────────────────────────▶ Join Geometry (input 1)
                         │
                         └▶ Distribute Points on Faces
                              · Distribute Method : POISSON      (even spacing = real condensation)
                              · Distance Min      : 0.004
                              · Density Max       : 6000.0
                              · Density Factor    : ◀── (see mask below)
                              · Seed              : 21
                              ├ Points   ─────▶ Instance on Points ▸ Points
                              ├ Normal   ─────▶ (optional: Align Rotation to Vector ▸ Vector)
                              └ Rotation ─────▶ Instance on Points ▸ Rotation

UV Sphere (Segments 8, Rings 5, Radius 0.0022)
   └▶ Transform Geometry (Scale (1.0, 1.0, 0.45))   ← squash: beads, not marbles
        └▶ Instance on Points ▸ Instance

Random Value (FLOAT, Min 0.30, Max 1.80, Seed 22) ─▶ Instance on Points ▸ Scale
Instance on Points ▸ Instances ─▶ Set Material (MAT_Condensation)
                               ─▶ Join Geometry (input 0) ─▶ Group Output
```

**The mask (Density Factor) is what makes it look real.** Options, best first:

1. **Vertex group / weight paint.** `Named Attribute("cond", FLOAT)` → `Density Factor`. Paint condensation onto the shoulder and body, off the cap and the label. Full art control, 60 seconds of work.
2. **Height gradient.** `Position ▸ Z` → `Map Range (From 0.0→0.28, To 1.0→0.0, Clamp ON)` → `Density Factor`. Heavy at the base, thinning up. Physically what actually happens.
3. **Normal facing.** `Normal` → `Vector Math (DOT_PRODUCT, second (0,0,1))` → `Map Range` → `Density Factor`. Kills beads on upward-facing surfaces (they would have run off).

Combine 1 and 2 with a `Math (MULTIPLY)`.

Add drips: a second `Distribute Points on Faces` at very low density feeding elongated capsules with `Transform Geometry ▸ Scale (1, 1, 6)`, masked to the same weight group. Five beads' worth of drip sells the whole effect.

---

### 6d. Animated "droplets fly outward" — Scene Time driven

Particles that expand outward from an origin over time, entirely procedurally, no simulation, no cache.

```
Scene Time ▸ Frame ──▶ Math (SUBTRACT, second = 55.0)      ← the impact frame
                        └▶ Math (MAXIMUM, second = 0.0)     ← clamp: nothing before impact
                             └▶ [t]

Group Input ▸ Geometry ─▶ Distribute Points on Faces (Density 400, Seed 4)
     └ Points ─▶ Capture Attribute (Data Type VECTOR, Domain POINT)
                    · Value ◀── Position
                    └ Geometry ─▶ Set Position ▸ Geometry
                      Attribute (= P0, the birth position)

# --- radial direction: away from the bottle axis
Vector Math (SUBTRACT)  A = P0,  B = (0, 0, 0.45)   ← splash origin
   └▶ Vector Math (NORMALIZE)  = [dir]

# --- per-point speed variation
Random Value (FLOAT, Min 0.55, Max 1.90, ID ← Index, Seed 9) = [rndSpd]

# --- ballistic offset:  dir * speed * t   +   (0,0,-1) * 0.5 * g * t^2
Math (MULTIPLY)  [t] x 0.045            = [tt]      ← metres per frame scale
Math (MULTIPLY)  [tt] x [rndSpd]        = [dist]
Vector Math (SCALE)  Vector=[dir]  Scale=[dist]     = [radial]

Math (MULTIPLY) [t] x [t]               = [t2]
Math (MULTIPLY) [t2] x 0.0016           = [drop]
Combine XYZ (0, 0, -[drop])                          = [gravity]

Vector Math (ADD)  [radial] + [gravity] = [offset]
   └▶ Set Position ▸ Offset

Set Position ▸ Geometry ─▶ Instance on Points ▸ Points
Ico Sphere (Radius 0.005, Subdivisions 1) ─▶ Instance on Points ▸ Instance
Random Value (FLOAT, Min 0.4, Max 1.6, ID ← Index, Seed 10) ─▶ ▸ Scale
   └▶ Group Output
```

**Notes.**
- `Scene Time ▸ Frame` is frame-rate independent in the sense that it returns the literal frame number; `Seconds` returns `frame / fps`. Use **Frame** when your constants are tuned in per-frame units (as above), **Seconds** when tuned in SI.
- **Capture Attribute is mandatory.** Without it, `Position` re-evaluates *after* `Set Position` in some graph arrangements and the droplets accelerate exponentially off to infinity. Capture the birth position once, then offset from it.
- In **4.2+**, `Capture Attribute` supports multiple items on one node — capture `Position` and a random seed together.
- To fade droplets out, drive `Instance on Points ▸ Scale` by `Map Range([t], 0→160, 1.0→0.0, Clamp ON)` multiplied into the random scale.
- This whole setup is **free** — no cache, scrubs in real time, and re-renders instantly when the client changes the timing.

---

### 6e. Bubbles rising inside the liquid

For the fill inside the bottle, or fizz in a poured glass.

```
Group Input ▸ Geometry (a closed mesh of the liquid volume)
  └▶ Mesh to Volume
        · Density        : 1.0
        · Resolution Mode: Voxel Amount   (Amount 64)
        · Interior Band Width : 0.02
        · Fill Volume    : ON      ← 3.6 ONLY; the socket is gone in 4.0+
     └▶ Distribute Points in Volume
           · Mode    : Density Random
           · Density : 2200.0
           · Seed    : 31
        └ Points ─▶ Capture Attribute (VECTOR) ◀── Position   = [P0]

Scene Time ▸ Seconds ─▶ Math (MULTIPLY, second = [riseSpeed])
Random Value (FLOAT, Min 0.35, Max 1.0, ID ← Index, Seed 32) = [riseSpeed]
Random Value (FLOAT, Min 0.0, Max 1.0, ID ← Index, Seed 33)  = [phase]

Math (ADD)     [time*speed] + [phase]        = [u]
Math (WRAP)    Value [u], Max 1.0, Min 0.0   = [u01]     ← loops forever, no popping
Math (MULTIPLY) [u01] x [columnHeight = 0.18] = [dz]

# gentle sideways wobble
Math (MULTIPLY) [u01] x 24.0 ─▶ Math (SINE) ─▶ Math (MULTIPLY, 0.004) = [wx]
Math (MULTIPLY) [u01] x 19.0 ─▶ Math (COSINE) ─▶ Math (MULTIPLY, 0.004) = [wy]

Combine XYZ ([wx], [wy], [dz]) ─▶ Set Position ▸ Offset
Set Position ▸ Geometry ─▶ Instance on Points ▸ Points
Ico Sphere (Radius 0.0018, Subdivisions 2) ─▶ ▸ Instance
Random Value (FLOAT, Min 0.4, Max 1.9, ID ← Index, Seed 34) ─▶ ▸ Scale
   ─▶ Set Material (MAT_Bubble) ─▶ Group Output
```

The `Math ▸ Wrap` node is what makes this loop seamlessly: each bubble rises `columnHeight`, wraps to the bottom, and rises again, with the per-bubble `phase` ensuring they do not all reset on the same frame. Bubbles should be **larger as they rise** in reality — multiply the scale by `Map Range([u01], 0→1, 0.6→1.4)`.

---

### 6f. Copy-pasteable: droplet scatter built via Python

```python
"""
04_gn_droplets.py — Builds the 6a velocity-gated airborne droplet scatter
entirely in Python, on both the 3.6 and the 4.0+ node-group interface APIs.
"""
import bpy
import math

V         = bpy.app.version
IS_40     = V >= (4, 0, 0)
IS_42     = V >= (4, 2, 0)
DOMAIN    = "DOM_Splash"
HOST_NAME = "GN_Droplets"
GROUP     = "NG_AirborneDroplets"


# ------------------------------------------------------------ interface helpers
def ng_new(name):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    if IS_40:
        ng.interface.new_socket(name="Geometry", in_out='INPUT',
                                socket_type='NodeSocketGeometry')
        ng.interface.new_socket(name="Geometry", in_out='OUTPUT',
                                socket_type='NodeSocketGeometry')
    else:
        ng.inputs.new('NodeSocketGeometry', "Geometry")
        ng.outputs.new('NodeSocketGeometry', "Geometry")
    return ng


def expose_float(ng, name, default, mn, mx):
    """Add a user-facing float input; returns its identifier for mod[<id>] = ..."""
    if IS_40:
        s = ng.interface.new_socket(name=name, in_out='INPUT',
                                    socket_type='NodeSocketFloat')
        s.default_value, s.min_value, s.max_value = default, mn, mx
        return s.identifier
    s = ng.inputs.new('NodeSocketFloat', name)
    s.default_value, s.min_value, s.max_value = default, mn, mx
    return s.identifier


# ------------------------------------------------------------ host object
host = bpy.data.objects.get(HOST_NAME)
if host is None:
    me = bpy.data.meshes.new(HOST_NAME)
    host = bpy.data.objects.new(HOST_NAME, me)
    bpy.context.scene.collection.objects.link(host)

# ------------------------------------------------------------ node group
ng = bpy.data.node_groups.get(GROUP)
if ng:
    bpy.data.node_groups.remove(ng)
ng = ng_new(GROUP)
nodes, links = ng.nodes, ng.links

id_density = expose_float(ng, "Density",    900.0, 0.0, 100000.0)
id_lift    = expose_float(ng, "Lift",         0.06, 0.0, 1.0)
id_radius  = expose_float(ng, "Drop Radius",  0.004, 0.0001, 0.1)

n_in  = nodes.new('NodeGroupInput');  n_in.location  = (-1200,   0)
n_out = nodes.new('NodeGroupOutput'); n_out.location = ( 1000,   0)

# --- source geometry: the baked fluid mesh
objinfo = nodes.new('GeometryNodeObjectInfo'); objinfo.location = (-1000, 200)
objinfo.transform_space = 'RELATIVE'
dom = bpy.data.objects.get(DOMAIN)
if dom:
    objinfo.inputs["Object"].default_value = dom
objinfo.inputs["As Instance"].default_value = False

# --- velocity gate: only spawn off fast-moving crests
namedattr = nodes.new('GeometryNodeInputNamedAttribute')
namedattr.location = (-1000, -180)
namedattr.data_type = 'FLOAT_VECTOR'
namedattr.inputs["Name"].default_value = "velocity"

vlen = nodes.new('ShaderNodeVectorMath'); vlen.location = (-820, -180)
vlen.operation = 'LENGTH'
links.new(namedattr.outputs["Attribute"], vlen.inputs[0])

maprange = nodes.new('ShaderNodeMapRange'); maprange.location = (-640, -180)
maprange.clamp = True
maprange.inputs['From Min'].default_value = 0.5
maprange.inputs['From Max'].default_value = 6.0
maprange.inputs['To Min'].default_value   = 0.0
maprange.inputs['To Max'].default_value   = 1.0
links.new(vlen.outputs["Value"], maprange.inputs['Value'])

dens_mul = nodes.new('ShaderNodeMath'); dens_mul.location = (-460, -180)
dens_mul.operation = 'MULTIPLY'
links.new(maprange.outputs['Result'], dens_mul.inputs[0])
links.new(n_in.outputs[id_density],  dens_mul.inputs[1])

# --- scatter
dist = nodes.new('GeometryNodeDistributePointsOnFaces'); dist.location = (-260, 120)
dist.distribute_method = 'RANDOM'
dist.inputs["Seed"].default_value = 3
links.new(objinfo.outputs["Geometry"], dist.inputs["Mesh"])
links.new(dens_mul.outputs["Value"],   dist.inputs["Density"])

# --- lift the points off the surface along the normal
scale_n = nodes.new('ShaderNodeVectorMath'); scale_n.location = (-60, -60)
scale_n.operation = 'SCALE'
links.new(dist.outputs["Normal"], scale_n.inputs[0])
links.new(n_in.outputs[id_lift],  scale_n.inputs[3])       # index 3 = 'Scale'

setpos = nodes.new('GeometryNodeSetPosition'); setpos.location = (140, 120)
links.new(dist.outputs["Points"],    setpos.inputs["Geometry"])
links.new(scale_n.outputs["Vector"], setpos.inputs["Offset"])

# --- the instance
ico = nodes.new('GeometryNodeMeshIcoSphere'); ico.location = (140, -220)
ico.inputs["Subdivisions"].default_value = 2
links.new(n_in.outputs[id_radius], ico.inputs["Radius"])

# --- random scale (float) and random rotation (vector)
rnd_s = nodes.new('FunctionNodeRandomValue'); rnd_s.location = (140, -420)
rnd_s.data_type = 'FLOAT'
rnd_s.inputs[2].default_value = 0.35        # Min  (float)
rnd_s.inputs[3].default_value = 1.60        # Max  (float)
rnd_s.inputs[8].default_value = 11          # Seed

rnd_r = nodes.new('FunctionNodeRandomValue'); rnd_r.location = (140, -620)
rnd_r.data_type = 'FLOAT_VECTOR'
rnd_r.inputs[0].default_value = (-math.pi, -math.pi, -math.pi)   # Min (vector)
rnd_r.inputs[1].default_value = ( math.pi,  math.pi,  math.pi)   # Max (vector)
rnd_r.inputs[8].default_value = 12

iop = nodes.new('GeometryNodeInstanceOnPoints'); iop.location = (520, 120)
links.new(setpos.outputs["Geometry"], iop.inputs["Points"])
links.new(ico.outputs["Mesh"],        iop.inputs["Instance"])
links.new(rnd_s.outputs[1],           iop.inputs["Scale"])       # outputs[1] = float

if IS_42:
    # 4.2+ : Instance on Points ▸ Rotation is a Rotation socket, not a Vector.
    e2r = nodes.new('FunctionNodeEulerToRotation'); e2r.location = (340, -620)
    links.new(rnd_r.outputs[0], e2r.inputs["Euler"])
    links.new(e2r.outputs["Rotation"], iop.inputs["Rotation"])
else:
    links.new(rnd_r.outputs[0], iop.inputs["Rotation"])           # outputs[0] = vector

links.new(iop.outputs["Instances"], n_out.inputs[0])

# ------------------------------------------------------------ modifier
for m in list(host.modifiers):
    host.modifiers.remove(m)
mod = host.modifiers.new("GN Droplets", 'NODES')
mod.node_group = ng
mod[id_density] = 900.0
mod[id_lift]    = 0.06
mod[id_radius]  = 0.004

# Keep the viewport usable: show instances as bounds while animating.
host.display_type = 'TEXTURED'
print("Built", GROUP, "on", host.name,
      "| Blender", ".".join(str(x) for x in V[:2]))
```

> If `velocity` does not exist as an attribute the Named Attribute node returns zero, `Map Range` clamps to 0, density becomes 0, and you get **no droplets**. Enable `Physics ▸ Fluid ▸ Domain ▸ Mesh ▸ Speed Vectors` and re-bake the mesh, or temporarily bypass the gate by linking `Group Input ▸ Density` straight into `Distribute Points on Faces ▸ Density`.

---

## 7. The flying fruit

The green slices and spheres crossing the frame at multiple depths. Two valid approaches; professionals use **(a)** for anything the client will comment on and **(b)** for background debris.

### 7.1 Approach A — hand-keyframed arcs (full art direction)

**Why it wins:** the client will say "the lime should hit the top-right of frame at the hero moment, and it should be more sideways-on". With keyframes that is a 20-second fix. With a rigid body sim it is a re-bake and a prayer.

**Recipe per slice:**
1. Parent the slice mesh to an Empty (`CTRL_Lime_A`). Animate the empty's `location` for the arc, and the *mesh's own* `rotation_euler` for the tumble. Separating them means you can retime the arc without re-timing the spin.
2. Three location keys only: **entry**, **apex**, **exit**. More keys and the arc stops being an arc.
3. Location interpolation: `BEZIER` with `AUTO_CLAMPED` — this naturally produces the parabola. Then flatten the apex handle in the Graph Editor so it does not float.
4. Rotation interpolation: **`LINEAR`**. A tumbling object in flight has constant angular velocity. Bezier easing on rotation is the single biggest "floaty CG" tell.
5. Motion blur does the rest. At a 180° shutter a slice crossing 40 % of frame width in 6 frames blurs beautifully.

**Frame-accurate example — one lime slice, 24 fps, crossing at the hero frame:**

| Frame | `CTRL_Lime_A.location` | `Lime_A.rotation_euler` (deg) | Interp | Note |
|---|---|---|---|---|
| 118 | (−1.85, −0.55, 0.10) | (0, 0, 0) | Loc: Bezier / Rot: Linear | Off frame-left, below |
| 152 | (−0.30, −0.42, 0.92) | (168, 0, 96) | — | Rising, entering the splash |
| **163** | **(0.18, −0.38, 1.02)** | **(228, 0, 130)** | — | **HERO FRAME — apex, just past centre** |
| 176 | (0.78, −0.30, 0.88) | (300, 0, 168) | — | Descending, exiting the splash |
| 206 | (2.10, −0.10, 0.05) | (420, 0, 250) | — | Off frame-right, below |

Total tumble: 420° on X over 88 frames = **4.77°/frame**, constant. The Z channel forms a parabola with apex at f163. Note the small negative Y drift — the slice moves *toward camera* very slightly, which sells depth and lets DOF do its job.

**Stagger the layers:**

| Object | Depth (Y) | Entry frame | Apex | Exit | Scale | Read |
|---|---|---|---|---|---|---|
| `Lime_FG` | −1.20 (near) | 132 | 158 | 184 | 1.15 | Heavily defocused, fast, big |
| `Lime_A` | −0.38 (mid) | 118 | 163 | 206 | 1.00 | Sharp, the hero slice |
| `Apple_B` | +0.35 (far) | 106 | 149 | 200 | 0.85 | Slightly soft, slower |
| `Sphere_C` | +0.80 (far) | 124 | 171 | 214 | 0.80 | Background, slowest |

Nearer objects must cross faster (parallax) and be more defocused. Getting these two relationships right is what produces the reference frame's depth.

### 7.2 Approach B — Rigid Body simulation

**Rigid Body World** (`Scene Properties ▸ Rigid Body World`):
- `collection` — a dedicated collection holding *only* the simulated objects. Objects not in it are ignored by the solver, regardless of their rigid body settings. This is the most common "my sim does nothing" cause.
- `substeps_per_frame` — 10 default; raise to **30–60** for fast fruit, and to `10 / time_scale` under slow motion.
- `solver_iterations` — 10 default; 20 for stacked/contacting objects.
- `time_scale` — slow-motion, matched to the fluid's Time Scale.
- `point_cache.frame_start / frame_end` — **must** cover your whole shot. Default is 1–250.

**Collision shapes:**

| Shape | Cost | Use for |
|---|---|---|
| `SPHERE` | trivial | Whole limes, apples, spheres. **Always use this for round fruit.** |
| `BOX` / `CAPSULE` / `CYLINDER` | trivial | Blockers, proxies |
| `CONVEX_HULL` | low | Slices, wedges, anything roughly convex. **The default choice for fruit slices.** |
| `MESH` | high, and unstable for fast-moving bodies | Only for static concave collision (a bowl). Never for a projectile — thin-shell mesh collision tunnels. |
| `COMPOUND` | medium | A parent whose children each carry a primitive shape; the correct way to build a concave *dynamic* body |

**Damping:** `linear_damping` 0.04–0.10 (air drag; higher makes fruit float), `angular_damping` 0.05–0.15 (0 makes fruit spin forever, which reads as a glitch). `restitution` 0.15–0.3 for fruit (they are not superballs). `friction` 0.5.

**Initial velocity.** Blender has no initial-velocity field for rigid bodies. The correct technique:

1. Set the object to Active, and **enable `Animated` (`rigid_body.kinematic = True`)**.
2. Keyframe `kinematic = True` at frame *N−2* and `kinematic = False` at frame *N*, with **CONSTANT** interpolation.
3. Keyframe the object's `location` and `rotation_euler` over frames *N−2 → N* so it is *moving* while still kinematic.
4. At frame *N* the solver takes over and inherits the velocity implied by that animated motion.

The velocity handed over is `(location[N] − location[N−1]) × fps`. So to launch a lime at 6 m/s at 24 fps, place it 0.25 m further along its travel at frame N than at N−1.

**Bake to Keyframes.** Once approved: select the fruit, `Object ▸ Rigid Body ▸ Bake To Keyframes` (`bpy.ops.rigidbody.bake_to_keyframes(frame_start, frame_end, step)`). This converts the sim to plain F-curves. **Always do this before final render.** Benefits: the result is deterministic (a re-render on a farm node cannot resimulate differently), it is scrubbable, and — critically — you can now **hand-edit** the curves to fix the one frame where a slice clipped the bottle. It also removes the rigid body world from the render dependency chain.

### 7.3 Fruit ↔ fluid interaction

**Fruit pushes fluid:** add `Physics ▸ Fluid ▸ Effector` to the fruit, `Effector Type: Collision`.
- `surface_distance` 0.0–0.5 — thickness of the collision shell. Raise it if the fluid leaks through fast-moving fruit.
- `use_effector` — keyframe **False** until the fruit is inside the domain, then **True**. Prevents it disturbing the crown while off-screen. CONSTANT interpolation.
- `velocity_factor` 1.0 — how strongly the effector's own motion is imparted to the liquid. This is what makes the fruit throw a wake through the splash.
- `use_plane_init` — leave OFF for closed solids.

**Fluid pushes fruit:** it does **not**. Mantaflow is one-way coupled — the fluid never applies force to a rigid body. If you need a slice to be visibly deflected by the water, either fake it with keyframes (Approach A, which is why professionals use A) or run the rigid body first, bake to keyframes, then run the fluid against the baked fruit.

**Order of operations, non-negotiable:**
1. Rigid body sim the fruit.
2. Bake to keyframes.
3. *Then* enable the fruit as fluid effectors.
4. *Then* bake the fluid.

Reverse it and every fluid re-bake gives different fruit positions, because the rigid body solver is not frame-deterministic under scrubbing.

### 7.4 Copy-pasteable: rigid body fruit launch

```python
"""
04_fruit_launch.py — Launches a fruit slice with a real initial velocity via the
kinematic-handoff technique, then optionally bakes it to keyframes and turns it
into a fluid effector.
Blender 3.6 LTS through 4.5.
"""
import bpy
import math
from mathutils import Vector

NAME        = "Lime_A"
LAUNCH_F    = 118
LAUNCH_POS  = Vector((-1.85, -0.55, 0.10))
LAUNCH_VEL  = Vector(( 3.20,  0.28, 2.90))    # m/s
SPIN_DPS    = Vector((114.0, 0.0, 66.0))      # degrees per second, X/Y/Z
END_F       = 240
FPS         = bpy.context.scene.render.fps
BAKE_NOW    = True
AS_EFFECTOR = True

sc = bpy.context.scene

# ---------------------------------------------------------- rigid body world
if sc.rigidbody_world is None:
    bpy.ops.rigidbody.world_add()
rbw = sc.rigidbody_world
if rbw.collection is None:
    c = bpy.data.collections.new("RigidBodyWorld")
    rbw.collection = c
rbw.substeps_per_frame  = 40
rbw.solver_iterations   = 20
rbw.point_cache.frame_start = 1
rbw.point_cache.frame_end   = END_F

# ---------------------------------------------------------- the object
ob = bpy.data.objects.get(NAME)
if ob is None:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.055, depth=0.012, vertices=32)
    ob = bpy.context.active_object
    ob.name = NAME

bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob

if ob.rigid_body is None:
    bpy.ops.rigidbody.object_add(type='ACTIVE')
rb = ob.rigid_body
rb.collision_shape  = 'CONVEX_HULL'     # SPHERE for whole fruit
rb.mass             = 0.045
rb.friction         = 0.50
rb.restitution      = 0.22
rb.linear_damping   = 0.06
rb.angular_damping  = 0.10
rb.use_margin       = True
rb.collision_margin = 0.002

# ---------------------------------------------------------- kinematic handoff
# Two animated frames give the solver a velocity to inherit at LAUNCH_F.
per_frame = LAUNCH_VEL / FPS
spin_pf   = Vector([math.radians(d) / FPS for d in SPIN_DPS])

ob.location       = LAUNCH_POS - per_frame * 2.0
ob.rotation_euler = (-spin_pf * 2.0)[:]
ob.keyframe_insert("location",       frame=LAUNCH_F - 2)
ob.keyframe_insert("rotation_euler", frame=LAUNCH_F - 2)

ob.location       = LAUNCH_POS - per_frame
ob.rotation_euler = (-spin_pf)[:]
ob.keyframe_insert("location",       frame=LAUNCH_F - 1)
ob.keyframe_insert("rotation_euler", frame=LAUNCH_F - 1)

ob.location       = LAUNCH_POS
ob.rotation_euler = (0.0, 0.0, 0.0)
ob.keyframe_insert("location",       frame=LAUNCH_F)
ob.keyframe_insert("rotation_euler", frame=LAUNCH_F)

rb.kinematic = True
rb.keyframe_insert("kinematic", frame=LAUNCH_F - 2)
rb.kinematic = True
rb.keyframe_insert("kinematic", frame=LAUNCH_F - 1)
rb.kinematic = False
rb.keyframe_insert("kinematic", frame=LAUNCH_F)     # solver takes over here

# Booleans and the pre-launch motion must be CONSTANT / LINEAR respectively.
ad = ob.animation_data
if ad and ad.action:
    for fc in (getattr(ad.action, "fcurves", None) or []):
        if fc.data_path.endswith("kinematic"):
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'
        elif fc.data_path in ("location", "rotation_euler"):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'   # constant velocity into the handoff
        fc.update()

# ---------------------------------------------------------- bake to keyframes
if BAKE_NOW:
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.rigidbody.bake_to_keyframes(frame_start=LAUNCH_F,
                                            frame_end=END_F, step=1)
        print("Baked", NAME, "to keyframes", LAUNCH_F, "->", END_F)
    except RuntimeError as e:
        print("bake_to_keyframes failed:", e,
              "- run it manually from Object > Rigid Body after a full playback.")

# ---------------------------------------------------------- fluid effector
if AS_EFFECTOR:
    if "Fluid" not in ob.modifiers:
        m = ob.modifiers.new("Fluid", 'FLUID')
    else:
        m = ob.modifiers["Fluid"]
    m.fluid_type = 'EFFECTOR'
    es = m.effector_settings
    es.effector_type    = 'COLLISION'
    es.surface_distance = 0.15
    es.velocity_factor  = 1.0
    es.use_plane_init   = False
    es.use_effector = False
    es.keyframe_insert("use_effector", frame=LAUNCH_F + 20)
    es.use_effector = True
    es.keyframe_insert("use_effector", frame=LAUNCH_F + 24)   # enters the domain
    es.use_effector = False
    es.keyframe_insert("use_effector", frame=LAUNCH_F + 70)
    for fc in (getattr(ob.animation_data.action, "fcurves", None) or []):
        if fc.data_path.endswith("use_effector"):
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'
            fc.update()

print("Fruit launch rig complete:", NAME)
```

> `bake_to_keyframes` needs the simulation to have been played through from frame 1 in the current session (the point cache must be populated). If it errors, scrub from frame 1 to the end once, then re-run.

---

## 8. Scene assembly and organisation

### 8.1 Collection layout

A commercial file that survives client rounds has this structure and no other:

```
Scene Collection
├── 00_CAM              CAM_Main, EMPTY_Focus, CTRL_CamRig
├── 01_PRODUCT          mountain dew bottle, CTRL_Bottle, label mesh, cap
├── 02_SIM              DOM_Splash (the domain), EMIT_Ribbon, CRV_EmitterPath,
│                       OBST_BottleProxy
├── 03_FORCES           FLD_Vortex, FLD_Push, FLD_Turb          [3 children]
├── 04_FX               GN_Droplets, GN_Condensation host, WW_Points
├── 05_FRUIT            Lime_A, Lime_FG, Apple_B, Sphere_C, CTRL_Lime_*
│   └── RigidBodyWorld  (referenced by scene.rigidbody_world.collection)
├── 06_LIGHTS           KEY, RIM_L, RIM_R, FILL, HDRI helper
├── 07_SET              backdrop, floor, reflectors, negative fill
└── 08_UTIL             render guides, safe-area plane, colour chart (all hidden)
```

Numeric prefixes force a stable sort order in the outliner regardless of naming. Every collection can be soloed (`H`/`Alt+H` per collection, or the checkbox) which is how you isolate a problem in 3 seconds.

### 8.2 Naming discipline

`TYPE_Description_Variant`. `DOM_`, `EMIT_`, `OBST_`, `FLD_`, `CTRL_`, `CRV_`, `GN_`, `MAT_`, `NG_` (node group), `CAM_`.

Non-negotiable rule: **there is never an object named `Cube.001` in a delivered file**. Numeric suffixes mean someone duplicated something and did not think about it, and every one of them will cost you thirty seconds later when you are hunting for the domain at 2 a.m.

### 8.3 Reading the observed outliner

| Item | Almost certainly is |
|---|---|
| `Camera` | The scene camera, un-renamed |
| `Animation` | A **collection** (or an empty acting as a master null) holding the animation controllers — the tutorial's grouping of the animated helpers |
| `Empty.001` | The **product controller null** (Section 3) — or the emitter's parent. The `.001` implies an `Empty` also exists, likely the DOF focus target or a force parent |
| `Cube.001` | **The fluid Domain.** A default cube, scaled to enclose the shot. This is the classic signature of a Mantaflow scene |
| `Modifiers` | Not an object — this is the outliner's expanded sub-tree of `Cube.001`, showing its **Fluid** modifier. Confirms the Physics tab reading |
| `mountain dew bottle` | The product mesh (or a collection instance of an appended asset) |
| `forces` (collection, 3 children) | The force-field rig — see Section 5.3 |
| 3 further numbered objects | The emitter, an obstacle proxy of the bottle, and a fruit object — or three fruit. Numbered because they were primitive-added and never renamed |

### 8.4 Linking vs appending the product

| | **Append** | **Link** |
|---|---|---|
| Copies data into your file | Yes | No — reference only |
| Editable locally | Yes | No (until Library Override) |
| Updates when the source changes | No | **Yes, on file open** |
| File size | Grows | Stays small |
| Use for | The bottle, once it is final and you need to attach modifiers and animation | The bottle **during the shot**, while modelling/look-dev is still being revised by someone else |

**The professional pattern:** the product lives in `assets/bottle.blend` as a **collection** called `PRODUCT_Bottle`. Every shot file **links** that collection, producing a **Collection Instance** (an empty with `instance_type='COLLECTION'`). You then parent that empty to `CTRL_Bottle` and animate normally. When modelling ships a new label, every shot updates on next open — zero re-work across a 12-shot campaign.

**Library Override** (`Object ▸ Library Override ▸ Make`) when you need to locally override a transform or modifier on a linked object without breaking the link. Use it sparingly; it is the most fragile part of the pipeline.

**Caveat:** a linked collection instance's geometry **cannot be a fluid Effector directly** — the modifier cannot be added to linked data. Build a local low-poly proxy of the bottle silhouette (`OBST_BottleProxy`), make *that* the effector, and hide it from render. This is standard practice and also 10× faster to simulate against than the real 400 k-triangle bottle.

### 8.5 View Layers

Two view layers pay for themselves immediately:

- **`VL_Work`** — everything visible, Simplify on, fluid mesh disabled in viewport. What you animate in.
- **`VL_Beauty`** — the render layer. `04_FX` and `08_UTIL` configured for render, Simplify off.

Per-collection, the three toggles do different things and everyone confuses them:
- **Checkbox** (`exclude`) — removes the collection from the view layer's depsgraph entirely. **This disables physics, drivers and modifiers** on those objects. Never use it to hide the domain "just for now" — it will silently break your bake.
- **Eye** (`hide_viewport`) — hides in viewport only, still evaluated.
- **Monitor icon** (`hide_viewport` on the object) / **Camera icon** (`hide_render`) — the safe hides.

### 8.6 Keeping the scene workable with a heavy cache

```python
sc = bpy.context.scene
sc.render.use_simplify              = True
sc.render.simplify_subdivision      = 0      # viewport subdiv off
sc.render.simplify_subdivision_render = 3
sc.render.simplify_child_particles  = 0.05
if hasattr(sc.render, "simplify_volumes"):
    sc.render.simplify_volumes      = 0.25   # 3.x+: volume resolution in viewport
```

Plus:
- **Disable the Fluid modifier's viewport display** (`dom.modifiers["Fluid"].show_viewport = False`) while animating the camera and product. Re-enable only to check sync.
- **Turn off the liquid Mesh in viewport** (`domain_settings.use_mesh = False`) — the particle preview is 50× lighter and good enough for timing.
- **`emitter.display_type = 'WIRE'`, `hide_render = True`** for every emitter and force empty.
- **Set the domain's `display_thickness`** and use bounds display (`dom.display_type = 'BOUNDS'`) when you only need its extents.
- **Instances, never Realize.** See 6a.
- **`Is Viewport` node** (`GeometryNodeIsViewport`) → `Switch` to cut GN scatter density by 10× in the viewport while keeping full density at render. This one node keeps a 200 k-instance droplet field interactive.

### 8.7 Copy-pasteable: collection organisation helper

```python
"""
04_organise.py — Creates the standard commercial collection layout and files
existing objects into it by name heuristics. Idempotent; safe to re-run.
"""
import bpy

LAYOUT = [
    ("00_CAM",     ("CAM_", "EMPTY_Focus", "CTRL_Cam")),
    ("01_PRODUCT", ("bottle", "CTRL_Bottle", "label", "cap", "PRODUCT_")),
    ("02_SIM",     ("DOM_", "EMIT_", "CRV_", "OBST_", "Cube")),
    ("03_FORCES",  ("FLD_", "forces")),
    ("04_FX",      ("GN_", "WW_")),
    ("05_FRUIT",   ("Lime", "Apple", "Sphere", "Fruit", "CTRL_Lime")),
    ("06_LIGHTS",  ("KEY", "RIM", "FILL", "LGT_")),
    ("07_SET",     ("SET_", "backdrop", "floor", "reflector")),
    ("08_UTIL",    ("UTIL_", "guide", "safe")),
]

sc = bpy.context.scene


def get_coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    if name not in {ch.name for ch in sc.collection.children}:
        try:
            sc.collection.children.link(c)
        except RuntimeError:
            pass          # already linked somewhere in the tree
    return c


def move_to(ob, coll):
    if coll.name in {c.name for c in ob.users_collection}:
        return
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)


colls = {name: get_coll(name) for name, _ in LAYOUT}

for ob in list(bpy.data.objects):
    lname = ob.name.lower()
    placed = False
    for cname, keys in LAYOUT:
        if any(k.lower() in lname for k in keys):
            move_to(ob, colls[cname])
            placed = True
            break
    if not placed and ob.type == 'CAMERA':
        move_to(ob, colls["00_CAM"])
    elif not placed and ob.type == 'LIGHT':
        move_to(ob, colls["06_LIGHTS"])

# Viewport hygiene
for ob in bpy.data.objects:
    if ob.name.startswith(("EMIT_", "FLD_", "OBST_", "CRV_")):
        ob.display_type = 'WIRE'
        ob.hide_render  = True

sc.render.use_simplify         = True
sc.render.simplify_subdivision = 0
print("Collections organised:", ", ".join(colls))
```

---

## 9. The non-destructive modifier stack on the bottle

Order matters because each modifier consumes the previous one's output. The correct order, top to bottom:

| # | Modifier | Settings | Why here |
|---|---|---|---|
| 1 | **Subdivision Surface** | Viewport 1, Render 2–3, Catmull-Clark, `use_limit_surface` ON | Must be first so everything downstream works on the smooth surface. Keep viewport at 0–1; render at 2–3. Level 4+ on a bottle is wasted — it is already round. |
| 2 | **Shrinkwrap** *(label only, on the label object)* | Target: bottle mesh, Mode: **Project**, Axis: negative Z of the label's local space (or **Nearest Surface Point** for simple cases), Offset 0.0008–0.002 | Conforms a flat label mesh to the bottle's curved body. Must come **after** the bottle's subdivision so it projects onto the final smooth surface, not the cage. The offset lifts it off the glass so it does not z-fight. |
| 3 | **Solidify** *(label)* | Thickness 0.0004, Offset −1, **Even Thickness** ON, **Rim Fill** ON | Gives the label real thickness so its edge catches a specular highlight. Zero-thickness labels look printed-on and fake. |
| 4 | **Bevel** | Amount 0.0012, Segments 2–3, Limit Method **Angle** 30°, **Harden Normals** ON, Miter Outer: Arc, **Clamp Overlap** ON | **Always last.** Bevel must operate on the final topology. A bevel before a subdivision gets smoothed into nothing; a bevel before a solidify produces doubled, overlapping geometry. |
| 5 | *(optional)* **Weighted Normal** | Weight 50, Keep Sharp ON | Only if Harden Normals on the bevel is not enough. Requires Auto Smooth (3.6) or a Smooth by Angle node (4.1+). |
| 6 | *(optional)* **Geometry Nodes — condensation** | Section 6c | After bevel, so beads sit on the final surface. |

**Rules that prevent the classic disasters:**
- **Never apply anything** until final. The whole point is that the client can ask for a fatter bevel on Friday.
- **Bevel needs clean, non-overlapping geometry** with no interior faces. Clamp Overlap ON always; it is the difference between a bevel and a spike field.
- **Scale must be applied** (`Ctrl+A ▸ Scale`) before Bevel and Solidify — both work in absolute units and give wildly wrong results on a non-uniformly-scaled object.
- **`show_in_editmode`** ON for Subdivision and Shrinkwrap so you can model against the real result.
- The **fluid obstacle proxy is a separate low-poly object**, not this stack. Never make a 3-level-subdivided, beveled bottle a fluid effector — the voxelisation cost is enormous and the result is identical to using a 400-triangle proxy.

---

## 10. Production order of operations

Follow this exactly. Each step **locks** something the next step depends on. Re-ordering does not cost hours; it costs days, because it forces a re-bake.

| # | Step | What it locks | Cost of doing it late |
|---|---|---|---|
| 1 | **Blockout** — grey boxes for bottle, floor, backdrop. Camera roughed. Beat sheet written with actual frame numbers. | Shot length, frame numbers, screen composition | Everything downstream is keyed to frame numbers. Changing the beat sheet after a bake means re-baking. |
| 2 | **Camera lock** — final focal length, position keys, DOF target, resolution, frame range. Approved by the client on a playblast. | The frustum | The domain is sized to the frustum. Move the camera and the domain is the wrong shape — re-bake. **This is the single most expensive mistake in the whole pipeline.** |
| 3 | **Product model + modifier stack** — final geometry, final scale, origin at base. Low-poly obstacle proxy built. | Real-world scale | Mantaflow is scale-sensitive. A bottle modelled at 3 m tall simulates like a water tower. Fixing scale after a bake invalidates the bake. |
| 4 | **Domain + low-res sim art-direction loop** — Resolution **60–90**, no mesh, no whitewater, particle display. Iterate emitter curve, forces, timing. **10–30 iterations here.** | The splash *shape* and *timing* | This loop is where the shot is actually designed. Each iteration is 3–8 minutes. Doing this at Resolution 250 means each iteration is 6 hours and you will get three of them. |
| 5 | **Sim approval** — show the client a viewport playblast of the low-res sim with grey materials. Get a written yes. | The performance | A client note on the splash *shape* after a high-res bake is a full re-bake. After sim approval, notes can only be about look, which is cheap. |
| 6 | **Fruit rigid body + bake to keyframes** | Fruit trajectories | Fruit must be baked before the fluid sees them as effectors (Section 7.3). |
| 7 | **Materials / look-dev** | The look | Done on the approved low-res sim, on a handful of still frames. Never look-dev a moving splash. |
| 8 | **Lighting** | Contrast, key direction, rim placement | Lighting decisions depend on the splash silhouette, which step 5 locked. |
| 9 | **High-res bake** — Resolution 200–320, Mesh Upres 1–2, whitewater on, final cache directory, `cache_type='ALL'`, overnight or over a weekend. | The final data | Only ever done **once**. If you have to do it twice, a step above was skipped. |
| 10 | **Geometry nodes FX pass** — droplets, condensation, spray, driven off the *final* cache | Micro-detail | Cheap and non-destructive; safe to iterate right up to the render. |
| 11 | **Final render** — to **EXR multilayer**, not PNG, not MP4. Cryptomatte on. | Pixels | |
| 12 | **Comp** — grade, glow, chromatic aberration, lens dirt, endcard type | Delivery | |

**The two rules that follow from the table:**
- *Never bake high-res until the camera is locked and the sim is approved.*
- *Never look-dev before the sim is approved.* Beautiful materials on a splash the client will reject is the most demoralising way to lose a week.

---

## 11. Troubleshooting

### 11.1 The emitter jitters, stutters, or beads along the curve

| Symptom | Cause | Fix |
|---|---|---|
| Liquid emitted as a string of separate blobs | Emitter moves further than its own diameter per frame; solver samples once per frame | `flow_settings.subframes = 2–5`. This is the fix 95 % of the time. |
| Emitter visibly steps between positions | Curve `resolution_u` too low | Raise `curve.data.resolution_u` to 24–48 |
| Emitter rolls/flips suddenly at one point on the path | Twist frame flip | `curve.data.twist_mode = 'Z_UP'`, raise `twist_smooth` to 1.5–2.5, and check for a control point with an isolated large `tilt` |
| Emitter speed pulses | `eval_time` F-curve has Bezier overshoot between keys | Set the `eval_time` curve to `LINEAR` for the body of the move, easing only the first and last key |
| Emitter accelerates wildly near curve ends | `AUTO_CLAMPED` handles on `eval_time` are undershooting/overshooting | Switch to `VECTOR` handles, or set `EASE_OUT`/`EASE_IN` explicitly |
| Object won't move along the path at all | `eval_time` has no keys, or Fixed Position is on and `offset_factor` is unanimated | Run `bpy.ops.constraint.followpath_path_animate(...)`, or key `offset_factor` |
| Fluid doesn't inherit path motion | `velocity_factor = 0` or `use_initial_velocity = False` | Set `use_initial_velocity = True`, `velocity_factor = 1.0–2.0` |

### 11.2 The sim doesn't match the camera move

**Do not re-bake first.** Try, in order:

1. **`domain_settings.cache_frame_offset`** — slides the *entire baked cache* in time without re-baking. If your splash peaks 12 frames too early, set the offset to +12. This is a free, instant fix and almost nobody knows about it.
2. **Retime the camera**, not the sim. The camera has no cache; moving its keys costs nothing.
3. **Check the domain's own frame range.** `cache_frame_start` / `cache_frame_end` are independent of `scene.frame_start` / `frame_end`. A domain baked 1–250 in a shot that now runs 1–288 will simply freeze after 250.
4. If the *shape* is wrong (not the timing), go back to step 4 of Section 10 at low resolution. Do not try to fix shape with offsets.

### 11.3 Fruit intersects the bottle

| Cause | Fix |
|---|---|
| `collision_shape = 'MESH'` on a fast body | Change to `CONVEX_HULL` (slices) or `SPHERE` (whole fruit) |
| Substeps too low — tunnelling | `rigidbody_world.substeps_per_frame` 40–60; `solver_iterations` 20 |
| Collision margin too small | `use_margin = True`, `collision_margin = 0.002–0.005` |
| The bottle isn't a rigid body at all | Add it as **Passive**, `collision_shape = 'CONVEX_HULL'` (use the *proxy*, not the subdivided hero mesh) |
| Slow motion without compensating substeps | `substeps ≈ 10 / rigidbody_world.time_scale` |
| Hand-keyframed fruit clipping | Bake to keyframes and hand-fix the offending 4 frames in the Graph Editor. This is the standard professional fix and takes 90 seconds. |

### 11.4 Geometry nodes instance count explodes

| Symptom | Fix |
|---|---|
| Viewport dies when the splash blooms | Density is driven by fluid surface area, which grows 10× at the splash peak. **Clamp it:** `Math (MINIMUM)` after your density calculation, capped at your target. |
| Blender freezes on the first frame after adding Realize Instances | Remove `Realize Instances`. It is almost never needed; instances render natively. |
| Memory blows past RAM at render time | Reduce `Ico Sphere ▸ Subdivisions` from 3 to 1. Subdiv 3 = 1280 tris/droplet; subdiv 1 = 80. At 200 k instances that is 256 M vs 16 M. |
| Interactive editing impossible | `Is Viewport` (`GeometryNodeIsViewport`) → `Switch` between a viewport density and a render density (10:1 ratio) |
| Every droplet flickers in scale | `Random Value` has no stable `ID` — the point order changes every frame. Feed `Index` into the `ID` input. |
| Instances vanish entirely | `Density` chain evaluating to 0 — usually a missing `velocity` named attribute. Bypass the gate to confirm. |

### 11.5 The animation looks floaty

Floaty is a spacing problem, essentially never a timing problem. Diagnose in this order:

1. **Rotation is Bezier-eased.** Tumbling objects have *constant* angular velocity. Set all in-flight `rotation_euler` F-curves to `LINEAR`. This alone fixes most cases.
2. **No overshoot.** Objects that stop dead at their target look weightless. Add 4–8 % overshoot with an 8–10 frame settle.
3. **Arcs are too flat.** Real projectiles have pronounced parabolas. If your apex is only 15 % above the entry/exit line, raise it.
4. **Too many keys.** Four location keys on a 90-frame arc = mush. Use three: entry, apex, exit.
5. **Fluid Time Scale mismatched to keyframe speed.** If the fluid runs at 0.25× and the fruit at 1.0×, the *fruit* looks fast and the *fluid* looks floaty. Match them.
6. **No motion blur.** `scene.render.motion_blur_shutter = 0.5`. Without it, fast CG motion strobes and reads as weightless.
7. **Gravity fake.** If someone lowered `scene.gravity` or `effector_weights.gravity` to slow the splash: undo it and use Time Scale instead (Section 2.3).
8. **Turn on motion paths** (`bpy.ops.object.paths_calculate()`) and look at the dot spacing. Even dots = linear = floaty. You want dots bunched at the ends of eases.

### 11.6 The sim baked to the wrong frame range

| Symptom | Cause | Fix |
|---|---|---|
| Sim freezes partway through the shot | `cache_frame_end` < `scene.frame_end` | Set `domain_settings.cache_frame_end = scene.frame_end` and bake the remainder |
| Nothing happens before frame N | `cache_frame_start` > 1, or the inflow's `use_inflow` keys are wrong | Check both; boolean keys must be CONSTANT |
| Cache appears empty after moving the .blend | `cache_directory` is an absolute path to the old location | Set a relative path (`//cache_fluid`) *before* baking. After the fact, re-point it and Blender will find the files if they moved with the project. |
| Bake restarts from scratch every time | `cache_type = 'REPLAY'` | Set `cache_type = 'MODULAR'` (bake stages separately, resumable) or `'ALL'` (one final bake). Never leave a hero shot on Replay. |
| Frames present on disk but not displaying | Frame offset, or a partially-written frame from a crashed bake | Check `cache_frame_offset`; delete the last few `.bobj/.vdb` files and re-bake from there |
| Re-bake needed but timing is right | — | Use `Free Data` on the specific stage only (Mesh / Particles), not `Free All`. Re-meshing is minutes; re-simulating is hours. |

```python
# Sanity-check any domain against the scene before you commit to an overnight bake.
import bpy
sc = bpy.context.scene
for ob in bpy.data.objects:
    m = ob.modifiers.get("Fluid")
    if not m or m.fluid_type != 'DOMAIN':
        continue
    ds = m.domain_settings
    print(f"{ob.name}: scene {sc.frame_start}-{sc.frame_end} | "
          f"cache {ds.cache_frame_start}-{ds.cache_frame_end} "
          f"offset {ds.cache_frame_offset} | type {ds.cache_type} | "
          f"time_scale {ds.time_scale} | res {ds.resolution_max} | "
          f"dir {ds.cache_directory}")
    assert ds.cache_frame_start <= sc.frame_start, "cache starts too late"
    assert ds.cache_frame_end   >= sc.frame_end,   "cache ends too early"
```

---

## Quick reference — properties this module touches

| Purpose | Python path |
|---|---|
| Scene fps / range | `scene.render.fps`, `scene.frame_start/end` |
| Global retime | `scene.render.frame_map_old / frame_map_new` |
| Fluid slow-mo | `dom.modifiers["Fluid"].domain_settings.time_scale` |
| Rigid body slow-mo | `scene.rigidbody_world.time_scale`, `.substeps_per_frame` |
| Cache window | `domain_settings.cache_frame_start / _end / _offset / cache_type / cache_directory` |
| Effector weights | `domain_settings.effector_weights.force / vortex / turbulence / gravity` |
| Inflow on/off | `emit.modifiers["Fluid"].flow_settings.use_inflow` |
| Inherit emitter motion | `flow_settings.velocity_factor` |
| Spray along normals | `flow_settings.velocity_normal` |
| Anti-beading | `flow_settings.subframes` |
| Effector on/off | `ob.modifiers["Fluid"].effector_settings.use_effector` |
| Follow Path | `con.target`, `use_curve_follow`, `use_fixed_location`, `offset_factor`, `offset` |
| Curve path | `curve.data.use_path`, `path_duration`, `eval_time`, `twist_mode`, `twist_smooth` |
| Curve tilt | `spline.bezier_points[i].tilt` (radians) |
| Force field | `ob.field.type / strength / size / noise / flow / seed / use_max_distance / distance_max / falloff_power` |
| Rigid body | `ob.rigid_body.collision_shape / mass / kinematic / linear_damping / angular_damping / restitution / collision_margin` |
| Bake RB | `bpy.ops.rigidbody.bake_to_keyframes(frame_start, frame_end, step)` |
| Path animate op | `bpy.ops.constraint.followpath_path_animate(constraint, owner, frame_start, length)` |
| GN interface (4.0+) | `ng.interface.new_socket(name, in_out, socket_type)` |
| GN interface (3.6) | `ng.inputs.new(socket_type, name)` |
| Simplify | `scene.render.use_simplify`, `simplify_subdivision`, `simplify_child_particles` |
