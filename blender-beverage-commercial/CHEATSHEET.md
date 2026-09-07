# Cheat Sheet — keep this open while building

One page. Every number you need, no lookup.

---

## Fluid Domain (Mantaflow, Liquid)

Against a **fresh** domain, change only the two rows marked ⚑. Everything else is
already correct at default — leave it alone.

| Setting | Value | Note |
|---|---|---|
| Domain Type | Liquid | |
| **Resolution Divisions** | **100** ⚑ | default is 32. Preview value. Final: 200-400 |
| Time Scale | 1.000 | default |
| CFL Number | 4.000 | default |
| Adaptive Time Steps | ON, max 4 / min 1 | default |
| Gravity | 0, 0, −9.81 | default |
| **Border Collisions** | **ALL SIX OFF** ⚑ | default is all on. *The* look-defining change |
| Simulation Method | FLIP | default |
| FLIP Ratio | 0.970 | default. High = splashy |
| System Maximum | 0 | default = uncapped |
| Particle Radius | 1.000 | default |
| Sampling | 2 | default |
| Randomness | 0.100 | default |
| Particles Max / Min | 16 / 8 | default |
| Narrow Band Width | 3.000 | default |
| Fractional Obstacles | ON, Distance 0.500 | needed for a thin bottle wall |
| Delete In Obstacle | ON | culls particles trapped inside the product |
| Mesh | ON, Upres Factor 2, Use Speed Vectors ON | speed vectors = motion blur works |
| Cache | Modular, on disk, **not in a synced folder** | |

---

## The splash rig

**Emitter** — a *disc*, not a sphere (sphere normals cancel the throw):

| Setting | Value |
|---|---|
| Fluid type | Flow → Liquid → **Inflow** |
| Initial Velocity | ON, **Normal ≈ 1.6 m/s** |
| Subframes | **2** — kills stuttering on a fast-moving emitter |
| Use Flow | keyed ON at impact, OFF at impact+45. **CONSTANT interpolation** |

**Path** — Bezier spiral around the bottle, ~1.25 turns, r ≈ 0.14 m, z 0.02 → 0.26.
Emitter rides it with a **Follow Path** constraint (`use_curve_follow`,
`use_fixed_location`), `offset_factor` keyed 0 → 1, LINEAR.

> Do **not** use the Curve Guide force field. Broken for Mantaflow (T97172).
> The domain Guides panel has its own regression (#97264). Follow Path is the
> only stock method that works.

**Three force fields**, all keyed: 0 → peak at impact+8 → 85% at hero → 0 at end.

| Field | Position | Peak | Job |
|---|---|---|---|
| Vortex | (0, 0, 0.10) | 6.0 | spins the sheet *around* the bottle |
| Force (radial +) | (0, 0, 0.05) | 9.0 | flares the crown out of frame |
| Turbulence | (0, 0, 0.16) | 3.0, size 0.6 | breaks the sheet into rims + droplets |

All three: Max Distance ON ≈ 0.45 m, Falloff Power 1.5.

**Product** = Fluid → Effector → Collision, Surface Distance 0.5.

---

## Timing (24 fps, 250 frames)

| Frame | Beat |
|---|---|
| 1 | start; camera begins slow push-in |
| 60 | **impact** — inflow on, forces ramp |
| 68 | forces peak |
| 105 | inflow off (45-frame burst) |
| **163** | **HERO FRAME** — splash at max extent, fruit mid-flight |
| 250 | settled; forces at zero |

---

## Lighting rig

| Light | Position | Rot | Size | Power |
|---|---|---|---|---|
| KEY_soft | (−0.75, −0.85, 0.95) | 52°, 0, −42° | 1.2 sq | 300 W |
| STRIP_left | (−0.55, 0.45, 0.28) | 90°, 0, −125° | 0.05 × 1.1 | 220 W |
| STRIP_right | (0.55, 0.45, 0.28) | 90°, 0, 125° | 0.05 × 1.1 | 220 W |
| BACK_through_liquid | (0, 0.95, 0.14) | 90°, 0, 180° | 0.7 sq | 400 W |
| TOP_cap | (0, −0.1, 1.05) | 0 | 0.6 sq | 150 W |

Plus **two white emissive reflection cards** at (±0.85, −0.15, 0.45), 1.6 m,
strength 60, **camera visibility OFF**. Water is ~95% specular — without these it
renders dark no matter the sample count.

Backdrop: emissive plane, Gradient → ColorRamp `#C43C00` → `#FF7A18`, strength 4.

---

## Camera

105 mm · sensor 36 mm · at (0, −1.05, 0.14) · rot (88°, 0, 0)
DOF ON · **f/3.2** · focus on an empty at the label (z ≈ 0.14)
Push-in: y −1.05 → −0.93 across the full range.

---

## Render — the two settings people get wrong

| | Look-dev | Final |
|---|---|---|
| Resolution % | 50 | 100 |
| Samples | 64 | 1024 |
| Adaptive threshold | 0.05 | 0.01 |
| **Transmission bounces** | 12 | **24** ⚠ |
| *(stock default is 12)* | | *module 03 works at 16-24* |
| Total bounces | 12 | 32 |
| Transparent bounces | — | 16 |
| Filter Glossy | — | 1.0 |
| Clamp Indirect | — | 10.0 |
| Motion blur | off | on, shutter 0.5 |
| Persistent Data | ON | ON |

⚠ **Transmission bounces is the #1 cause of a black splash.** Light must survive
water → water → bottle wall → amber liquid → bottle wall → camera. That's 8-12
transmission events. The default is marginal.

Output: **PNG/EXR sequence**, 16-bit, Overwrite **OFF** + Placeholders **ON**
(so a crashed render resumes and you can split it across machines).

Colour: 3.6 = Filmic · 4.x = AgX. **They do not match.** AgX will desaturate that
orange noticeably.

---

## The loop

```
set forces/timing → bake Data @ res 100 (~1-3 min) → judge THROUGH THE CAMERA
   → wrong? free cache, change ONE thing, re-bake
   → right? lock it, move on
```

Fifteen to twenty iterations is normal. Never raise resolution "to see it better" —
resolution is a solver parameter, it changes the result, not just the detail.

---

## Five failures, ranked

1. **Splash renders black** → Transmission bounces 24.
2. **Splash renders dull** → no reflection cards. Water shows you what it reflects.
3. **Water passes through the bottle** → Fractional Obstacles ON, raise effector
   Surface Distance, or use a solid proxy collider.
4. **Result changes on re-bake at new resolution** → expected. Resolution is a
   solver parameter. Direct low, confirm medium, commit high.
5. **Colours don't match the tutorial** → Filmic (3.6) vs AgX (4.x).
