# Beverage / Product Splash Commercials in Blender

A complete working knowledge base for building photoreal beverage and product
commercials with liquid simulation in Blender — reconstructed from
*"lets make a beverage commercial in blender 2"* (Blender 3.6 LTS, native
Mantaflow FLIP), and generalised into a repeatable method.

---

## The doctrine

Nine principles. Everything else in this repo is detail hanging off these.

### 1. You are not simulating water. You are engineering one frame.

The reference render is frame **163** of a ~250-frame sequence. At that frame the
splash is at maximum extent, the fruit is mid-flight through it, and nothing has
started falling back. Every other decision in the scene — the inflow burst timing,
the force-field keyframes, the fruit arcs, the camera push — exists to make that
one frame land.

Amateurs simulate water and then look for a good frame. Professionals decide the
frame first and then build a sim that delivers it.

### 2. Lock the camera before you art-direct the sim.

The splash only has to look right from one angle. Every hour spent perfecting
water that ends up out of frame or hidden behind the product is an hour burned.
Frame the shot, lock it, *then* shape the splash to it.

### 3. Open the domain.

All six Border Collisions **off**. This is the defining solver choice in the
reference and it is not a detail.

- Borders **on** = a sealed glass tank. Water hits the wall, bounces, sloshes,
  pools. You get an aquarium.
- Borders **off** = an open window. Water that reaches the boundary leaves and is
  deleted. No bounce-back, no pooling, no return waves.

An ad splash must feel suspended in a void. Open borders are how you get that —
and deleting escaped particles keeps particle count and bake time down as a bonus.

### 4. Force fields are the art direction. Gravity is not enough.

The reference groups **three** force fields in a collection named `forces`. That
grouping is the tell: the splash silhouette was *designed*, not discovered.

- **Vortex** spins the sheet *around* the bottle — this is what makes water wrap
  the product instead of blowing past it.
- **Force** (radial, positive) flares the crown outward so it breaks frame.
- **Turbulence** breaks the sheet into irregular rims and detached droplets so it
  doesn't read as a clean CG cone.

Keyframe their strength — ramp at impact, peak at the hero frame, decay after.
Keyframed force strength is how you make a physics sim hit a mark. Without it you
are rolling dice and re-baking.

### 5. Make the fluid follow a curve.

This is the technique the source video is built around, and it is what separates a
designed splash from a random one. A small inflow rides a **Bezier spiral** wrapped
around the bottle via a **Follow Path** constraint, throwing liquid outward along
its normal as it travels, with **Use Flow** keyed on for a finite burst.

Three things must combine or it doesn't read:
1. the emitter **travels** (keyed `offset_factor`),
2. it **throws** (initial velocity along normal),
3. it **stops** (Use Flow keyed off, with CONSTANT interpolation so it snaps).

> **Do not reach for the Curve Guide force field.** It is documented-broken for
> Mantaflow liquid — liquid particles spray in a single or random direction
> instead of following the curve (Blender bug T97172), and Mantaflow is
> effectively unmaintained, so it is not getting fixed. The domain's own
> **Guides** sub-panel has a separate open regression (#97264). The Follow Path
> emitter above is not a workaround for the "proper" tool — with stock Blender it
> **is** the tool. Only the paid FLIP Fluids addon genuinely rails liquid along
> a curve.

### 6. Water is lit by what it reflects.

Water has almost no diffuse response — it is ~95% specular and refractive. A
physically correct splash in a dark environment renders as a dark, muddy,
unreadable blob no matter how many samples you throw at it.

The fix is not more light. It is **large white emissive planes off-camera**, set
invisible to camera but visible to reflection and refraction. Those cards are what
produce the bright silver sheets in the reference frame.

### 7. Raise your transmission bounces or your splash renders black.

Light entering the shot has to survive: water surface → water interior → water
surface → bottle wall → bottle interior → amber liquid → bottle wall → camera.
That is easily 8-12 transmission events before a ray reaches the lens.

Cycles' default is marginal for this stack. **Transmission: 24, Total: 32.** This
single setting is the number one reason beginner splash renders look dead, and it
costs nothing to get right.

### 8. Colour comes from absorption, not base colour.

The bottle's amber contents get their saturation from **Volume Absorption**, whose
colour deepens with thickness — which is why a real bottle is pale at the neck and
rich through the belly. Base-colour tinting cannot produce that gradient and always
reads as plastic.

Same logic for the palette overall: saturated orange backdrop, colourless white
splash, green fruit. Complementary, with the product as the brightest and most
saturated thing in frame.

### 9. Direct at low resolution. Commit at high.

Resolution is a **solver parameter**, not a display setting. Changing it changes
the result, not just the detail.

So: art-direct the gross shape at resolution 100 where a bake takes minutes, run
one confirm bake at medium resolution, then commit to final. Expect fifteen or
twenty low-res iterations. That is not thrashing — that is the work.

---

## Production order

Each step locks something. Re-ordering costs days, because a change upstream
invalidates everything downstream.

```
  1. Scaffold        collections, units, frame range
  2. Product         bottle / cap / interior liquid  ── locks silhouette + scale
  3. Camera          focal length, height, DOF       ── LOCKS THE SHOT
  4. Set             backdrop + reflection cards     ── locks palette + reflections
  5. Lights          key, twin strips, backlight     ── locks the product's read
  6. Domain          + product as collision effector
  7. Splash rig      curve, emitter, three forces
  8. ART-DIRECTION LOOP  ←──────── the bulk of the work
  9. Look-dev        materials, wetness, caustics
 10. High-res bake                                    ── unattended, hours
 11. Final render                                     ── unattended, hours
 12. Comp            grade, glare, grain, encode
```

---

## Repository map

| Path | What's in it |
|---|---|
| `RUNBOOK.md` | The live-session script: what to check before starting, the ordered plan, the art-direction loop, and the five failure modes ranked by frequency. **Start here when opening Blender.** |
| `reference/01-shot-breakdown.md` | Forensic read of the source frame. Every Fluid Domain value transcribed off the UI, the lighting rig derived from the specular signature, and a confidence table separating what was observed from what was inferred. |
| `reference/hero-frame-163.jpg` | The source reference frame. |
| `reference/00-source-reconstruction.md` | What could be verified about the tutorial and its creator, plus corroborating sources for the curve-guided-fluid technique. |
| `modules/01-fluid-simulation.md` | Mantaflow domain, FLIP settings, curve-guided inflow, force fields, whitewater, meshing, caching, bake strategy, failure modes. |
| `modules/02-shading-lookdev.md` | Water, PET plastic, amber liquid, label, wetness via Dynamic Paint, condensation, fruit SSS, gradient backdrop, caustics. |
| `modules/03-lighting-camera-render.md` | Studio product rig, twin strips, reflection cards, camera and DOF, motion blur with speed vectors, Cycles settings, colour management. |
| `modules/04-animation-geonodes-assembly.md` | Shot choreography with frame numbers, time remapping, follow-path emitter, keyed forces, geometry-nodes droplets, rigid-body fruit, scene organisation. |
| `modules/05-compositing-output-pipeline.md` | Passes, EXR vs PNG, the comp graph, encoding presets, render management, hardware reality, troubleshooting. |
| `scripts/build_beverage_ad.py` | Parametric, staged, version-tolerant scene builder. All art-directable numbers in one `CONFIG` dict at the top. Every stage callable on its own. |

---

## Provenance and honesty

The source video could not be watched — YouTube is blocked from the environment
this was assembled in. What this knowledge base is built from:

1. **A high-resolution screen capture of the tutorial** which happened to include
   the entire Fluid Domain panel, legibly. Every value in the "Certain" rows of
   `reference/01-shot-breakdown.md` was read directly off that panel.
2. **The video's own published description** of what it teaches: "how to make
   fluids follow a curve, how to use forces, and also touches on some basic
   geometry nodes", Blender 3.6 LTS, published 2023-10-24.
3. **Domain knowledge**, applied to reconstruct the rest.

Inference is labelled as inference throughout, with confidence levels. The build
script has not yet been executed against a live Blender; it parses clean and every
risky property write is guarded, so a version mismatch yields a warning list rather
than a traceback.
