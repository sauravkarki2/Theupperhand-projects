# Blender 5.1.2 Reconciliation — verified against the live session

The knowledge base was reconstructed from a Blender **3.6 LTS** tutorial, with 4.x
deltas flagged. The target machine runs **Blender 5.1.2 (Windows, RTX 4060 Laptop)**.

Rather than assume, every API the build depends on was probed inside the live
session. This file records what actually holds. **Verified by execution, not memory.**

---

## Verdict: the fluid pipeline survives 5.x intact

This was the real risk — Mantaflow is effectively unmaintained upstream, so it was
plausible it had been removed or reworked. It has not.

| Area | Result |
|---|---|
| `FLUID` modifier | **Present** |
| `FluidDomainSettings` | **162 properties; all 38 the build uses exist.** Zero missing |
| `FluidFlowSettings` | All used properties present |
| `FluidEffectorSettings` | All used properties present |
| Simulation methods | `FLIP`, `APIC` — FLIP available |
| Whitewater (spray/foam/bubble) props | All present |
| Force field types | `FORCE`, `VORTEX`, `TURBULENCE`, `WIND`, `DRAG`, `GUIDE`, + others |
| Geometry nodes ids used by module 04 | All present |
| Camera DOF props | All present |
| Area light props (incl. `spread`) | All present |
| Object ray visibility (`visible_camera` etc.) | All present |
| Shader nodes (Principled, Glass, Volume Absorption, Gradient, ColorRamp, Voronoi, Bump, Refraction) | All present |

**Conclusion:** modules 01 (fluid), 02 (shading), 03 (lighting/camera/render) and
04 (animation/geonodes) are valid as written on 5.1.2. The build script's guarded
`_set()` helper found nothing to warn about in these areas.

---

## Deltas that DO matter

### 1. `cache_type` enum renamed: `FINAL` → `ALL`

| Blender 3.6 | Blender 5.1.2 |
|---|---|
| `REPLAY`, `MODULAR`, `FINAL` | `REPLAY`, `MODULAR`, **`ALL`** |

Any 3.6-era instruction saying "set cache type to Final" must be read as **All**.
The build script uses `MODULAR`, which is unchanged and correct.

### 2. Cycles is registered but absent from the static engine enum

`bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items` lists only
`BLENDER_EEVEE`. That is **not** evidence Cycles is missing — the static enum does
not include dynamically-registered engines. Assigning `scene.render.engine =
'CYCLES'` succeeds, and `bpy.types.RenderEngine.__subclasses__()` reports `CYCLES`.

**Lesson: test the assignment, don't read the enum.**

### 3. Cycles was configured for CPU rendering — fixed

Found: `compute_device_type = NONE`, `scene.cycles.device = CPU`. On a machine with
an RTX 4060 that is a very large, silent performance loss.

Set to `compute_device_type = OPTIX` with the GPU device enabled and CPU disabled,
and `scene.cycles.device = 'GPU'`. OptiX over CUDA for the hardware denoiser and
RT-core traversal.

### 4. The compositor was restructured — module 05's graph needs rework

This is the one place the knowledge base is **genuinely out of date**.

| 3.6 / 4.x | 5.1.2 |
|---|---|
| `scene.node_tree` | **`scene.compositing_node_group`** — `Scene.node_tree` no longer exists |
| `CompositorNodeComposite` (output) | **Gone.** The tree is a node group; output goes through **`NodeGroupOutput`** against the tree's `interface` |
| `CompositorNodeMixRGB` | **Gone.** Use the unified **`ShaderNodeMix`**, which works inside a compositor tree |
| `CompositorNodeMath` | **Gone** |

Still present and usable: `RLayers`, `Denoise`, `Glare`, `Lensdist`,
`ColorBalance`, `CurveRGB`, `HueSat`, `Blur`, `BokehBlur`, `VecBlur`,
`EllipseMask`, `Exposure`, `Filter`, `Cryptomatte` / `CryptomatteV2`,
`AlphaOver`, `Zcombine`, `OutputFile`, `Viewer`. 86 compositor node types usable
in total.

**So module 05's node *selection* and *ordering* remain correct; its
*wiring code* does not.** Treat its Python as 3.6/4.x reference and rebuild the
graph against `compositing_node_group` + `NodeGroupOutput` + `ShaderNodeMix`.

### 5. `Action.fcurves` is gone — the slotted animation system

Blender 5.x replaced the flat action with layers, strips and slots. Any 3.6/4.x
code that reaches for `action.fcurves` raises
`AttributeError: 'Action' object has no attribute 'fcurves'`.

```python
# 3.6 / 4.x — BREAKS on 5.x
for fc in obj.animation_data.action.fcurves:
    ...

# 5.x
def iter_fcurves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    for layer in ad.action.layers:
        for strip in layer.strips:
            for slot in ad.action.slots:
                cb = strip.channelbag(slot)
                if cb:
                    for fc in cb.fcurves:
                        yield fc
```

This bites the moment you set keyframe interpolation in Python — which this
build does for the emitter's `offset_factor` (LINEAR) and `use_inflow`
(CONSTANT). Note `keyframe_insert()` itself is unchanged; only *reading back*
the curves moved.

Useful incidental: boolean keys such as `use_inflow` already default to
CONSTANT interpolation, so that half needs no correction.

### 6. `Object.field` is None until a field is actually enabled

Creating a plain empty and assigning `obj.field.type` fails with
`'NoneType' object has no attribute 'type'`. `field` is a pointer that does
not exist until a force field is turned on, and there is no data-API way to
turn it on.

```python
# BREAKS
ob = bpy.data.objects.new("FLD_vortex", None)
ob.field.type = "VORTEX"          # AttributeError: field is None

# WORKS — the operator creates the empty and enables the field together
bpy.ops.object.effector_add(type="VORTEX", location=(0, 0, 0.10))
ob = bpy.context.object
ob.name = "FLD_vortex"
ob.field.strength = 6.0
```

This is one of the few places where the operator is genuinely required rather
than merely convenient.

---

## Confirmed Cycles defaults on 5.1.2

Read off the live scene, settling the earlier question about what you raise *from*:

| Property | Default |
|---|---|
| `max_bounces` | 12 |
| **`transmission_bounces`** | **12** |
| `glossy_bounces` | 4 |
| `diffuse_bounces` | 4 |
| `transparent_max_bounces` | 8 |
| `samples` | 4096 |

Confirms the correction made earlier: transmission defaults to **12**, not 8.

---

## Hardware constraints (this machine)

| | |
|---|---|
| GPU | NVIDIA RTX 4060 **Laptop** — typically **8 GB VRAM** |
| CPU | 13th Gen Intel Core i7-13620H |
| Disk | C:\ — 994 GB total, **641 GB free** (ample for fluid cache) |
| Backend | OptiX |

**8 GB VRAM is the binding constraint,** not disk. Implications:

- A transmissive splash + bottle + liquid stack is memory-hungry in Cycles. If a
  render fails with out-of-memory, the fluid mesh is almost always the cause.
- Domain resolution 100 is comfortable. 200 is fine. **300+ needs watching** — the
  meshed splash can become a very heavy object.
- Laptop thermals throttle sustained renders. A long animation bake plus render is
  an overnight job, not an afternoon one.
- Enable Persistent Data for the animation render, but note it *increases* peak
  memory — if it OOMs, that is the first thing to turn off.

---

## Probe method

Everything above came from read-only `bl_execute` probes against the live session:
enumerating `bl_rna.properties` on the relevant classes, attempting
`nodes.new(<id>)` for every node type used, and reading enum items. Two mutations
were made deliberately (Cycles backend → OptiX, device → GPU); one scratch node
group was created and removed per probe, and a final check confirmed **zero
leftover probe datablocks** in the file.
