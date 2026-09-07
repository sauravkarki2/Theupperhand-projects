# The Curve-Ribbon Technique — liquid that wraps a product

The single highest-value discovery from building the MR LEMON spot against a
real reference. It is **not** in the original Mountain Dew tutorial, and it
replaces fluid simulation for the shot type that beverage ads use most.

---

## 1. The realisation

The reference (a Costa Coffee "Classic Latte" vertical spot) has a liquid band
spiralling around the can with ice cubes riding it. The instinct is to reach for
Mantaflow — the tutorial's whole subject is making fluid follow a curve.

Look closer at the reference and the band is:

- **uniform in cross-section** along its whole length,
- **perfectly smooth**, with no droplet break-up, no ligaments, no surface noise,
- **closed and continuous**, looping cleanly with no thinning where it turns.

No FLIP solver produces that. Surface tension, sub-cell noise and particle
resampling guarantee irregularity. That band is **swept geometry**: a profile
curve extruded along a path curve.

**This matters enormously for cost.** A resolution-300 liquid bake is hours and
tens of GB, and every art-direction change means re-baking. A swept curve
updates instantly, is fully deterministic, and re-renders with zero bake.

---

## 2. When to use which

| Look | Tool | Why |
|---|---|---|
| Smooth band wrapping a product | **Curve + bevel object** | Uniform, controllable, instant |
| Crown splash, impact, break-up | **Mantaflow FLIP** | You want the chaos |
| Pour stream landing in a splash | **Both** — curve for the stream, sim for the crown | Each does what it's good at |
| Droplets, spray, mist | **Geometry nodes scatter** | Cheaper and more directable than whitewater |

The mistake is treating "liquid" as one problem. An ad splash is three different
problems that happen to share a shader.

---

## 3. Construction

Three curve objects, not one.

### 3.1 The path

A Bezier spiral around the product. The parametrisation that works:

```python
for i in range(NPT):
    t    = i / float(NPT - 1)
    ang  = math.radians(-40.0 + t * 480.0)        # ~1.33 turns
    hook = math.exp(-t * 11.0)                    # entry lift, decays fast
    rad  = 0.078 + 0.016 * math.sin(t * math.pi) + 0.058 * hook
    z    = (0.235 * (1 - t) + 0.115 * t
            - 0.085 * math.sin(t * math.pi) + 0.105 * hook)
```

Three separate shaping terms, each doing one job:

- **`480 degrees`** — 1.33 turns. More than one full turn is what makes the band
  cross in *front* of the product as well as behind it. At exactly 360 degrees it
  reads as a hoop the product is standing inside.
- **`sin(t*pi)` on radius** — bulges the loop at its midpoint so it doesn't read
  as a mechanical helix.
- **`exp(-t*11)` hook** — lifts and swings out only the first ~20% so the band
  *enters from above* like a pour. Without it the ribbon tops out below the
  product's rim and the shot has no origin for the liquid.

### 3.2 The profile (bevel object)

A **flattened ellipse**, never a circle:

```python
RW, RH = 0.030, 0.011        # width, thickness — ~2.7:1
```

A circular profile gives a tube — reads as a hose. The flat band presents a broad
face to the lights, which is what produces the long specular streaks along its
length. That streak is most of the read.

### 3.3 The taper

```python
shape = [0.34, 0.72, 1.0, 0.88, 0.22]     # entry -> full -> tail
```

Narrow where the stream enters, full through the wrap, thin at the tail. A pour
widens as it lands; a band that starts and ends at full width reads as a solid
object, not liquid.

```python
path.bevel_mode    = "OBJECT"
path.bevel_object  = profile_obj
path.taper_object  = taper_obj
path.use_fill_caps = True
path.resolution_u  = 12
```

---

## 4. Animating it

Two channels, and they do different things.

### 4.1 Draw-on — `bevel_factor_end`

```python
key(rib.data, "bevel_factor_end", [(1, 0.0), (52, 1.0)])
```

Sweeps the swept-tube along the path. **This is what makes static geometry read
as pouring liquid.** The band grows along its own path exactly as a stream would.

Note `bevel_factor_end` lives on the **curve data**, not the object. Animating
`scene.objects` will never reach it — a retime that walks objects silently drops
this channel.

### 4.2 Flow — object Z rotation

```python
key(rib, "rotation_euler", [(1, 0.0), (300, math.radians(-38))], index=2)
```

Linear, not eased. A constant slow rotation about the product's axis reads as
continuous flow. Ease it and the liquid appears to decelerate, which looks wrong.

### 4.3 Ice must be parented, not keyed

Parent riding objects to the ribbon so they inherit the flow:

```python
ob.parent = rib
ob.matrix_parent_inverse = rib.matrix_world.inverted()
```

Keyframing ice positions separately guarantees drift out of contact within a few
dozen frames. Give each cube a small independent tumble on top.

---

## 5. Measuring it — the checks that matter

Screenshots may be unavailable (remote sessions, headless). These projections are
objective and catch the real failures:

```python
from bpy_extras.object_utils import world_to_camera_view
co = world_to_camera_view(scene, cam, obj.matrix_world @ vert.co)
# co.x, co.y in 0..1 are inside the frame; co.z is distance in front of the lens
```

| Check | Target | What it catches |
|---|---|---|
| `ribbon.x` spans past 0 and 1 | both true | Band breaks frame edges like the reference |
| `ribbon top world_z > lid top` | true | Liquid arrives from above, not a hoop |
| `ribbon.y max < 1.0` | true | Entry hook didn't fly out of frame |
| product width frac | ~0.5 | Product reads as hero |
| ribbon radius − product radius | 25-35 mm | Wraps rather than orbits at a distance |

**Do not project `bound_box` on a bevelled curve.** It reports a stale, un-bevelled
box and yields nonsense (observed: +/-15 in NDC for a 0.2 m object). Project the
**evaluated mesh vertices** instead — `obj.evaluated_get(depsgraph).to_mesh()`.

Equally, do not read `obj.dimensions` in the same script that built the curve —
it has not re-evaluated yet and will report the pre-bevel extent.

---

## 6. Why the reference is dark

Worth recording as art direction, not just technique. The reference puts a
mid-tone product on a near-black stage with a warm radial halo behind it.

- A translucent product **glows** against dark; against a bright background the
  same transmission reads as washed-out.
- The halo does the job a gradient backdrop does in a bright ad — it separates
  the silhouette — but costs almost no light in the rest of the frame, so the
  specular hits on the liquid stay the brightest thing in shot.
- A glossy dark floor doubles the product for free and gives the frame a base.

Applied to a **yellow** drink this is stronger still: yellow is the brightest
hue at full saturation, so it separates from black with no help. The reverse —
yellow product on a yellow brand background — needs dark accents and hard rim
light to survive, and is the harder shot to light.
