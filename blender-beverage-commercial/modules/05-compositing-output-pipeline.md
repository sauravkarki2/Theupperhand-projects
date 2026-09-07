# Module 05 — Compositing, Output & Production Pipeline

**Scope:** everything *after* the raw Cycles render. Passes, EXR strategy, the compositor graph, the "make CG look real" pass, VSE assembly, encoding, deliverables, project hygiene, render management, hardware reality, troubleshooting, and 3.6 → 4.x differences.

**Out of scope (other modules):** lighting, materials/shading, the Mantaflow solver itself, curve-guided flow, force fields, geometry nodes.

**Source context.** Reconstructed for the workflow shown in *"lets make a beverage commercial in blender 2"* (Blender 3.6 LTS, Oct 2023). The evidence frame is the artist inspecting `E:\renders\New Folder(122)\0163.png` in an external viewer while Blender sits behind — i.e. an animation rendering to a numbered PNG sequence, frames checked as they land. Hero look: saturated orange backdrop, bright specular water splash, green fruit, shallow depth of field.

That PNG-sequence habit is **correct for review and wrong for mastering**. Section 2 explains the hybrid that keeps the habit and fixes the headroom.

**Version note.** Everything below is written for **3.6 LTS** and flagged where **4.x** differs. The single biggest 4.x difference is not a node — it is that **4.0 changed the default view transform from Filmic to AgX**, which re-grades your entire shot. See §12.

---

## Table of contents

1. [Render passes worth enabling](#1-render-passes-worth-enabling)
2. [EXR vs PNG, and the practical hybrid](#2-exr-vs-png-and-the-practical-hybrid)
3. [The compositor graph for a beverage ad](#3-the-compositor-graph-for-a-beverage-ad)
4. [The "make CG look real" checklist](#4-the-make-cg-look-real-checklist)
5. [Video Sequence Editor assembly](#5-video-sequence-editor-assembly)
6. [Encoding](#6-encoding)
7. [Deliverables and aspect variants](#7-deliverables-and-aspect-variants)
8. [Pipeline and project hygiene](#8-pipeline-and-project-hygiene)
9. [Render management](#9-render-management)
10. [Hardware reality check](#10-hardware-reality-check)
11. [Troubleshooting](#11-troubleshooting)
12. [Blender 3.6 vs 4.x compositor differences](#12-blender-36-vs-4x-compositor-differences)

---

## 1. Render passes worth enabling

Passes live in **Properties → View Layer**. Every pass costs memory and file size, nothing else in Cycles (they are byproducts of the same integration) — except **Cryptomatte**, which costs a little render time, and **Vector**, which forbids motion blur.

### 1.1 The pass set for this shot

| Pass | Why, specifically for a beverage/splash shot | Cost |
|---|---|---|
| **Combined** | The beauty. Always on. | — |
| **Z (Depth)** | Comp defocus, depth-based grading, and holdouts. **Not anti-aliased usefully in Cycles** — see §1.3. | 1× float32 ch |
| **Mist** | The *good* depth pass. Normalised 0–1, correctly filtered at edges. Use it for atmospheric haze behind the bottle and for pushing the backdrop back. | 1× ch |
| **Vector** | Comp motion blur / speed data for retimes. **Cycles refuses to output Vector while motion blur is enabled.** For a splash, see §1.4 — you almost certainly want real motion blur instead. | 4× ch |
| **Cryptomatte Object** | Isolate bottle / liquid mesh / fruit / backdrop for selective grades. The single most valuable pass on this list. | 4–12 ch |
| **Cryptomatte Material** | Isolate *the label* vs *the glass* on one object. Essential when the bottle is a single mesh. | 4–12 ch |
| **Cryptomatte Asset** | Only useful if you built proper linked asset hierarchies. Usually skip. | 4–12 ch |
| **Denoising Data** | `Denoising Normal`, `Denoising Albedo`, `Denoising Depth`. Feeds the comp Denoise node. **Without these the denoiser eats splash micro-detail.** | 7× ch |
| **Emission** | Isolates any true emitter (backlit label, practical). Use it as a *glare source mask* so only real emitters bloom. | 3× ch |
| **Glossy Direct / Indirect** | Where the wet specular sparkle lives. Add a scaled copy back on top to make water read "wetter" without re-rendering. | 6× ch |
| **Transmission Direct / Indirect** | The see-through contribution of glass and liquid. A gentle boost makes the drink look juicier and the glass more "optical". | 6× ch |
| **Normal** | Cheap, and useful for relighting hacks and for a Facing/fresnel matte. | 3× ch |
| **Position** (3.0+) | World-space P. Lets you build 3D-space masks in comp (e.g. "everything below the liquid line"). Optional. | 3× ch |
| Diffuse Dir/Ind/Col, Glossy Col, Transmission Col | Only if you intend full light-pass reconstruction. See §1.2. | 12+ ch |
| AO, Shadow Catcher | Skip unless you're compositing onto a plate. | — |

**Skip:** UV, Object/Material Index (Cryptomatte supersedes them *except* in the refraction case, §1.5), Volume passes unless you have actual volumetrics.

### 1.2 The light-pass reconstruction identity

If you enable the direct/indirect passes *and* their colour passes, the Combined is exactly:

```
Combined = (DiffDir  + DiffInd ) * DiffCol
         + (GlossDir + GlossInd) * GlossCol
         + (TransDir + TransInd) * TransCol
         +  VolumeDir + VolumeInd
         +  Emission
```

Rebuild that in the compositor with Mix(Add) and Mix(Multiply) nodes and you can dial each term independently — "10% more specular, 5% less diffuse on the fruit" — without a re-render. It's a heavy graph and it only matters when a client is nitpicking a look at 2am. For most beverage work, just **add a scaled Glossy Direct on top** (Mix → Add, Fac 0.10–0.25) and move on.

### 1.3 Z is a liar (and how to make it honest)

Cycles' Z pass is **averaged over samples**. On any anti-aliased edge you get a depth that is the *mean* of foreground and background — a value that corresponds to nothing in the scene. Defocus that and you get halos around every edge.

Two mitigations:

- **Filter Width.** `scene.cycles.filter_width = 0.01` gives a near-unfiltered, near-correct Z — but it also aliases the beauty. So render Z on a **separate view layer** with tiny filter width, and the beauty on the normal one.
- **Use Mist instead** wherever you can. Mist is a *shaded* quantity, so averaging it across samples is meaningful. Mist is right for atmosphere, depth grades and haze; Z is only right for Defocus, and only grudgingly.

Set Mist in **World → Mist Pass**: `Start` at the front of the bottle, `Depth` to just past the backdrop, `Falloff = Quadratic`. Then in comp, `Mix(Screen)` a desaturated backdrop colour by the Mist value at Fac 0.05–0.15 for cheap, convincing air.

### 1.4 Comp DOF vs in-render DOF — the splash verdict

**Render the DOF in camera. Enable Z anyway.**

| | In-render (Cycles camera DOF) | Comp DOF (Defocus node + Z) |
|---|---|---|
| Correctness through glass/liquid | Correct — every refracted ray gets its own aperture offset | Wrong — Z stores the *glass surface*, not what's behind it |
| Bright specular bokeh | Real. A 200-nit droplet becomes a bright disc | Mushy. Blur spreads energy but reads as a grey blob unless the source is genuinely huge in linear EXR |
| Foreground defocus | Correct — a blurred foreground genuinely reveals what's behind it | Impossible. Single-layer Z has no "behind". Hard-edged foreground blur is the giveaway |
| Anti-aliased edges | Fine | Halos (see §1.3) |
| Cost | +50–150% samples; DOF adds path variance | Nearly free |
| Changeable after render | No | Yes |

A splash is the worst possible case for comp DOF: fast-moving, self-intersecting, transparent, and full of tiny bright highlights that *are* the shot. Every failure mode above lands at once.

**Practical compromise:** render in-camera DOF at a *conservative* aperture (f/4–f/5.6 equivalent, not f/1.4) so you retain enough sharpness to survive a client asking for less blur, then add a *gentle* extra Defocus in comp only on the far background, masked with Mist. Never comp-defocus anything in front of the focal plane.

If you're forced into full comp DOF (fixed render budget, no re-render possible):
- Render Z on its own thin-filter view layer.
- `Defocus`: `Use Z-Buffer` on, `Bokeh = Circle` or `Hexagon`, `f-Stop 5.6–11`, `Blur Max 12–20`, `Threshold 1.0`, and **`Preview` off** for finals.
- Keep `Blur Max` low. It is a hard clamp in pixels; anything above ~25 at 1080p starts sampling wildly wrong depths.

### 1.5 Cryptomatte gotchas that will bite you

- **Cryptomatte does not see through refraction.** Look at the liquid *through* the glass wall and the crypto ID you get is the *glass*. You cannot crypto-isolate the drink inside the bottle. This is a hard limitation, not a settings problem.
  - **Workaround:** render the liquid on its own view layer with the glass set to **Holdout** (or with the glass as an indirect-only object), and use that layer's alpha as your matte. Or use `pass_index` + an `ID Mask` node on a dedicated layer.
- **Levels.** `pass_cryptomatte_depth` defaults to 6 (3 ranks). A glass bottle plus a motion-blurred, DOF-blurred splash stacks many partial coverages per pixel — **raise it to 8, or 12 for hero frames**. Channels ≈ `ceil(levels/2) * 4` per crypto type.
- **Lossy compression destroys Cryptomatte.** DWAA/DWAB quantise floats. Cryptomatte encodes *object hashes* as float values — quantise them and the matte shatters into noise. Blender applies the EXR codec to the whole file, so **if the file contains Cryptomatte, use ZIP or ZIPS, never DWAA.** This is the number-one silent Cryptomatte failure.
- **Cryptomatte is not denoised** and must not be. Branch your Cryptomatte node off the Render Layers node *directly*, never off the Denoise output.

### 1.6 bpy — enable the pass set

```python
# ── passes_beverage.py ─────────────────────────────────────────────────────
# Enables the production pass set for a beverage/splash shot.
# Blender 3.6 LTS; notes inline for 4.x.
import bpy

def setup_passes(view_layer=None, *, crypto_levels=8, want_vector=False,
                 light_passes=True, full_reconstruction=False):
    scene = bpy.context.scene
    vl = view_layer or bpy.context.view_layer

    # --- core -------------------------------------------------------------
    vl.use_pass_combined = True
    vl.use_pass_z        = True
    vl.use_pass_mist     = True
    vl.use_pass_normal   = True
    if hasattr(vl, "use_pass_position"):          # 3.0+
        vl.use_pass_position = True

    # --- vector (comp motion blur / retime data) --------------------------
    # Cycles will NOT output Vector while motion blur is on.
    vl.use_pass_vector = bool(want_vector)
    if want_vector:
        scene.render.use_motion_blur = False
        print("[passes] Vector requested -> motion blur DISABLED. "
              "For a liquid splash this is usually the wrong trade. See 1.4/1.7.")

    # --- cryptomatte ------------------------------------------------------
    vl.use_pass_cryptomatte_object   = True
    vl.use_pass_cryptomatte_material = True
    vl.use_pass_cryptomatte_asset    = False      # only with real linked assets
    vl.pass_cryptomatte_depth        = crypto_levels   # 6 default, 8-12 for glass+DOF

    # --- denoising data (feeds the comp Denoise node) ---------------------
    vl.cycles.denoising_store_passes = True
    # Denoise in COMP, not in render, so it stays tunable.
    scene.cycles.use_denoising = False

    # --- light passes -----------------------------------------------------
    if light_passes:
        vl.use_pass_emit               = True
        vl.use_pass_glossy_direct      = True
        vl.use_pass_glossy_indirect    = True
        vl.use_pass_transmission_direct   = True
        vl.use_pass_transmission_indirect = True
    if full_reconstruction:
        vl.use_pass_diffuse_direct   = True
        vl.use_pass_diffuse_indirect = True
        vl.use_pass_diffuse_color    = True
        vl.use_pass_glossy_color     = True
        vl.use_pass_transmission_color = True

    # --- mist range (tune Start/Depth to your set) ------------------------
    ms = scene.world.mist_settings
    ms.use_mist = True
    ms.start    = 0.5     # metres: front of the bottle
    ms.depth    = 6.0     # metres: just past the backdrop
    ms.falloff  = 'QUADRATIC'
    ms.intensity = 0.0

    n = sum(1 for _ in vl.bl_rna.properties if _.identifier.startswith("use_pass"))
    print(f"[passes] configured on view layer '{vl.name}' "
          f"(crypto levels {crypto_levels}, denoise-in-comp)")

def add_clean_z_layer(name="Z_CLEAN"):
    """Separate view layer with a near-unfiltered Z for comp Defocus."""
    scene = bpy.context.scene
    vl = scene.view_layers.get(name) or scene.view_layers.new(name)
    vl.use_pass_combined = False
    vl.use_pass_z = True
    vl.cycles.denoising_store_passes = False
    vl.use_pass_cryptomatte_object = False
    # Filter width is scene-level in Cycles; render this layer in its own pass
    # or accept that it also thins the beauty AA.
    print(f"[passes] '{name}' created. Set scene.cycles.filter_width = 0.01 "
          f"when rendering it standalone.")
    return vl

if __name__ == "__main__":
    setup_passes(crypto_levels=8, want_vector=False, light_passes=True)
```

### 1.7 Vector pass / Vector Blur — honest verdict

`Vector Blur` is a 2D smear driven by a per-pixel motion vector. It has no idea about:
- geometry that rotates (a tumbling droplet),
- geometry that appears/disappears between frames (a splash sheet tearing),
- self-occlusion,
- the fact that the fluid mesh is **re-meshed from scratch every frame** so vectors are frequently garbage.

For a Mantaflow splash it produces smeared, streaky mush. Use **real Cycles motion blur** (`Render Properties → Motion Blur`, Shutter 0.5 for a 180° shutter, Position `Center on Frame`, Steps 2–3 for deforming geometry) and accept the sample cost. Enable the Vector pass only if a downstream NLE or optical-flow retimer wants it — and then render a second, motion-blur-free pass just for that.

---

## 2. EXR vs PNG, and the practical hybrid

### 2.1 What 8-bit PNG actually throws away

A PNG at 8 bits per channel stores **256 levels per channel, sRGB-encoded, with the view transform (Filmic/AgX) already baked in and everything above display white clipped to 255.**

For this shot that is catastrophic in three specific ways:

1. **The specular splash is the shot, and it lives above 1.0.** A wet highlight on water hits scene-linear values of 20, 50, 200. In an EXR half-float that's stored exactly. In a PNG it is `255,255,255` — indistinguishable from a piece of white paper. You can never make it bloom correctly, never pull it back, never change the highlight roll-off. The energy is gone.
2. **Grading headroom.** Push exposure +1 stop on 8-bit data and you are stretching 256 levels across the same display range — every gradient in that saturated orange backdrop bands visibly. Half-float EXR gives roughly **1024 discrete steps per stop across ~30 stops**; you can push ±3 stops and it holds.
3. **The view transform is baked and irreversible.** Filmic (3.6) and AgX (4.0+) are *aggressive, non-invertible* tone maps. Once in the PNG, you are grading a tone-mapped image. Any further contrast you add compounds on top of a curve that already crushed your blacks and desaturated your highlights. Worse, you cannot ever deliver the same shot in a different transform.

16-bit PNG fixes the *banding* (65,536 levels) but **not** the clipping or the baked transform. It is still display-referred, still clipped at white. It's a fine *intermediate* for encoding, a bad *master*.

### 2.2 File size, with real numbers

At 1920×1080 = **2,073,600 px**. Per-channel sizes: uint8 = 1 B, uint16 = 2 B, half float = 2 B, float32 = 4 B.

| Format | Channels | Raw | Typical on disk | 250 frames |
|---|---|---|---|---|
| PNG 8-bit RGB | 3 | 6.2 MB | **2–4 MB** | 0.5–1 GB |
| PNG 16-bit RGBA | 4 | 16.6 MB | 9–14 MB | 2.2–3.5 GB |
| EXR half RGBA, DWAA | 4 | 16.6 MB | **1–2.5 MB** | 0.25–0.6 GB |
| EXR half RGBA, ZIP | 4 | 16.6 MB | 6–10 MB | 1.5–2.5 GB |
| EXR float32 RGBA, ZIP | 4 | 33.2 MB | 14–22 MB | 3.5–5.5 GB |
| **Multilayer EXR, lean set**, half + float Z/crypto, ZIP | ~26 | ~120 MB | **25–45 MB** | **6–11 GB** |
| **Multilayer EXR, full set** (all light passes + 3 cryptos @ 8 levels), ZIP | ~55 | ~260 MB | **60–110 MB** | **15–28 GB** |
| Same, DWAA (⚠ breaks Cryptomatte) | ~55 | ~260 MB | 20–40 MB | 5–10 GB |

At 4K (3840×2160) multiply every number by **4**. A full-pass 4K multilayer EXR sequence of 250 frames is **60–110 GB**. Plan disk before you plan passes.

The headline: **a half-float DWAA EXR is smaller than an 8-bit PNG and contains vastly more.** There is no size argument for PNG mastering. The only arguments for PNG are "my image viewer opens it instantly" and "I can drag it into Slack" — which are real, and which the hybrid below preserves.

### 2.3 The rules

- **Half float (16-bit) for everything except Z, Position, Vector and Cryptomatte.** Half has ~3 decimal digits of precision and a range to 65,504 — plenty for radiance. Depth in metres and crypto hashes need **float32**. Blender's `color_depth` is per-file, so a `'32'` multilayer file is the safe universal choice at ~2× the size; `'16'` is fine if you're not doing precision depth work.
- **ZIP / ZIPS if the file contains Cryptomatte.** ZIPS (single scanline) is marginally faster to write and much friendlier to streaming readers; ZIP (16-scanline blocks) compresses a bit better. Either is lossless.
- **DWAA only for Cryptomatte-free files.** It's a lossy DCT codec, visually transparent on beauty data at Blender's fixed quality, and 3–8× smaller than ZIP. Great for a beauty-only master. Fatal to crypto and to hard-edged ID/matte data.
- **PIZ** is lossless and beats ZIP on *grainy* (noisy, pre-denoise) data. If you're archiving noisy renders, PIZ. Otherwise ZIP.
- Avoid **B44/B44A** (half-only, fixed 2.3:1, legacy) and **PXR24** (lossy 24-bit float, fine but DWAA is better).

### 2.4 The practical hybrid — one render, two outputs

This is the answer to the evidence frame. Keep the PNG habit for review; add an EXR master alongside it. Blender does this in a single render with **File Output nodes that carry their own colour management override**.

- **Master:** `OPEN_EXR_MULTILAYER`, float32 or half, ZIP, colour management **Override → Standard / no look** (so the file stays scene-linear and un-tone-mapped).
- **Review:** `PNG`, 8-bit RGB, colour management **Override → Filmic (3.6) or AgX (4.0+)** with your look, written from the *end* of the comp graph. This is the file you flick through in an image viewer at 2am.

Both land in the same render, from the same frames, with zero extra render time. Section 3.9 has the code.

**Never** run the review PNGs through the VSE and call it a master — see §11.6 for the double-transform trap.

### 2.5 bpy — output format presets

```python
# ── output_formats.py ──────────────────────────────────────────────────────
import bpy

def set_exr_master(scene=None, *, depth='32', codec='ZIP', multilayer=True):
    """Scene-linear multilayer master. ZIP because Cryptomatte is in the file."""
    scene = scene or bpy.context.scene
    im = scene.render.image_settings
    im.file_format = 'OPEN_EXR_MULTILAYER' if multilayer else 'OPEN_EXR'
    im.color_mode  = 'RGBA'
    im.color_depth = depth              # '16' half, '32' full float
    im.exr_codec   = codec              # ZIP | ZIPS | PIZ | DWAA | DWAB | RLE | NONE
    if codec in {'DWAA', 'DWAB'}:
        print("[out] WARNING: DWAA/DWAB is lossy and CORRUPTS Cryptomatte. "
              "Use ZIP/ZIPS if any crypto pass is enabled.")
    if not multilayer:
        im.use_preview = False
    # Masters are written scene-linear, untouched by the view transform.
    im.color_management = 'OVERRIDE'
    im.view_settings.view_transform = 'Standard'
    im.view_settings.look = 'None'
    im.view_settings.exposure = 0.0
    im.view_settings.gamma = 1.0
    scene.render.use_file_extension = True
    return im

def set_png_review(scene=None, *, depth='8', compression=15):
    """Display-referred review frames with the view transform baked in."""
    scene = scene or bpy.context.scene
    im = scene.render.image_settings
    im.file_format = 'PNG'
    im.color_mode  = 'RGB'              # 'RGBA' only if you need the alpha
    im.color_depth = depth              # '8' review, '16' encode intermediate
    im.compression = compression        # 0-100; 15 is fast, 100 is slow & ~10% smaller
    im.color_management = 'FOLLOW_SCENE'
    scene.render.use_file_extension = True
    scene.render.dither_intensity = 1.0 # kills banding in 8-bit gradients. See 11.3
    return im

def set_png_encode_intermediate(scene=None):
    """16-bit PNG for feeding ffmpeg. Transform baked, banding-free."""
    return set_png_review(scene, depth='16', compression=15)
```

---

## 3. The compositor graph for a beverage ad

### 3.0 The one thing to understand first

**Blender's compositor works in scene-linear space, *before* the view transform.** The view transform (Filmic in 3.6, AgX in 4.0+) is applied at the very end, on write, by the colour management stack.

Consequences you must internalise:

- **Thresholds are in linear scene units, not display units.** A Glare threshold of `1.0` means "brighter than diffuse white". Your splash speculars are at 20–200. Threshold `1.0` catches half the frame; threshold `4.0–8.0` catches only the wet sparkle.
- **Optical effects are physically correct here.** Glare, defocus, motion blur and chromatic aberration all *belong* pre-transform, because that's where a real lens does them. This is a genuine advantage over grading a baked JPEG.
- **Contrast curves feel wrong here.** An S-curve applied in linear then pushed through AgX compounds. Grade *gently* in Blender and let the view transform do the tone mapping, or export linear EXR and do the real grade in Resolve/Fusion/Nuke where you can work post-transform with proper scopes.
- There is **no "apply view transform" node** in 3.6 or 4.x. The only way to get a display-referred image inside the graph is to write it out and read it back, or to use a File Output node's colour management override (§3.9).

### 3.1 The ordered chain

Optical order first (what a photon hits, in order), then sensor, then grade. This is the defensible ordering and it looks right:

```
 1  Render Layers ──────────────────────────────── the beauty + all passes
 2  Despeckle ..................................... optional: kill surviving fireflies
 3  Denoise (Image + Normal + Albedo) ............. prefilter ACCURATE, HDR on
 4  ├─ Cryptomatte branches ...................... tapped from (1), NEVER from (3)
 5  Comp DOF (Defocus + Z) ........................ ONLY if not rendered in-camera
 6  Vector Blur ................................... ONLY if not rendered in-camera
 7  Primary grade — Color Balance (Lift/Gamma/Gain) linear exposure + warmth
 8  Selective grades via Cryptomatte .............. product boost, splash neutralise
 9  Glare A: Fog Glow ............................. broad specular halo
10  Glare B: Streaks (+ optional Ghosts) .......... aperture star on the wet hits
11  Lens Distortion (Dispersion) .................. chromatic aberration, tiny barrel
12  Vignette (Ellipse Mask → Blur → Mix Multiply) . lens falloff
13  RGB Curves ..................................... final contrast + black-point lift
14  Filter: Sharpen ................................ small. Very small.
15  Film grain (Noise Texture → Mix Overlay) ....... sensor, so it goes last
16  Composite  +  File Output (EXR master / PNG review)
```

**Why this order:**

- **Denoise before everything.** Every downstream operation amplifies noise. Glare in particular turns a firefly into a glowing star. Denoise is also the only node that *needs* clean, un-glared, un-graded input to match its training data.
- **Cryptomatte taps the raw Render Layers.** Crypto data is not image data; running it through Denoise or a grade destroys it.
- **Glare after the primary grade, before the lens/sensor stack.** Glare is a *lens* phenomenon so it should sit with lens distortion — but it thresholds on brightness, so it has to see your final exposure. Grade first, then glare, then the rest of the lens.
- **Lens distortion after glare.** A real lens' internal flare gets distorted by the same optics on the way out. Marginal, but free.
- **Vignette after distortion.** Vignetting is the aperture and barrel cutting light at the sensor edge — it happens last in the optical path.
- **Curves after all optics.** You're grading the image the lens delivered, not the scene.
- **Sharpen then grain, both dead last.** Sharpen is a sensor/processing artifact; grain is the film/sensor emulsion. Grain must never be sharpened — that's what makes it read as "noise" instead of "grain".

### 3.2 Denoise

Node: `CompositorNodeDenoise`. Inputs: **Image, Normal, Albedo**.

| Setting | Value | Why |
|---|---|---|
| `use_hdr` | **On** | You're feeding linear data with values >1.0. Off clips your speculars. |
| `prefilter` | **`ACCURATE`** | Your Normal/Albedo passes come straight from Cycles and are themselves noisy. `ACCURATE` prefilters them first. Use `NONE` only if the aux passes are already clean, `FAST` never for finals. |
| Normal input | `Denoising Normal` | From `denoising_store_passes`, **not** the regular Normal pass (wrong space). |
| Albedo input | `Denoising Albedo` | Same. |

**Turn off in-render denoising** (`scene.cycles.use_denoising = False`). Denoising twice mushes the splash. The exception: if you *want* a denoised Combined for quick review, leave it on and accept that your comp Denoise is then a no-op.

**The splash-preservation trick.** OIDN has almost no albedo signal to work with on clear water — the albedo pass is near-flat, so the denoiser can't tell "detail" from "noise" and smooths the droplet edges. Fix it by denoising *selectively*:

```
Render Layers ─┬─ Denoise (full)          ──┐
               │                            ├─ Mix (Fac = Cryptomatte splash matte, inverted)
               └─ Denoise (or raw)        ──┘
```

Feed the **fully denoised** version into the *backdrop* side and the **raw or lightly denoised** version into the *splash* side. The backdrop gets clean; the splash keeps its noise-that-reads-as-spray. Requires enough samples that the splash noise is fine-grained — 512+.

### 3.3 Glare — the wet sparkle

Node: `CompositorNodeGlare`. **One node does one glare type.** For a beverage ad you want at least two.

**Mix semantics (3.6):** `-1.0` = input only, `0.0` = even blend, `+1.0` = glare only. Values near `0` will *visibly dim* your plate because it's a blend, not an add. Live in the `-0.9 … -0.6` range.

**Size (Fog Glow only):** an integer exponent, `6`–`9`. `9` is the largest (halo covers roughly half the frame), `6` the tightest. It's a power-of-two kernel, so each step doubles the radius.

**Iterations:** `2`–`5`. Affects Streaks/Ghosts/Fog Glow quality and spread. `3` is the sane default; `4` for a wider, softer fog glow.

| Setting | Glare A — Fog Glow | Glare B — Streaks | Optional — Ghosts |
|---|---|---|---|
| `glare_type` | `FOG_GLOW` | `STREAKS` | `GHOSTS` |
| `quality` | `HIGH` (finals) / `MEDIUM` (previews) | `HIGH` | `HIGH` |
| `threshold` | **1.0** general bloom · **4.0–8.0** wet-sparkle only | **6.0–12.0** | **8.0–15.0** |
| `mix` | **−0.75** (−0.85 subtle, −0.6 heavy) | **−0.85** | **−0.92** |
| `size` | **8** (7 tight, 9 dreamy) | n/a | n/a |
| `iterations` | **3** (4 for softer) | **3** | **3** |
| `streaks` | n/a | **4** (6 for a busier star; **2** reads anamorphic) | n/a |
| `angle_offset` | n/a | **10–20°** — never 0°, an axis-aligned cross reads synthetic | n/a |
| `fade` | n/a | **0.90** (0.85 short, 0.95 long) | n/a |
| `color_modulation` | 0.0 | **0.15–0.25** — prismatic tint at the tips | **0.25** |

`quality` is a hard cost/precision switch: `LOW` computes at 1/4 resolution, `MEDIUM` at 1/2, `HIGH` at full. Preview on MEDIUM, final on HIGH — and note the *look changes* between them, so lock HIGH before you approve a grade.

#### The two-Glare trick, done properly

Naive stacking (`Glare A → Glare B`) works but Glare B thresholds against the *already bloomed* image, so the streaks originate from soft haloes instead of from hot pixels, and they smear.

**Branch and add instead:**

```
            ┌─→ Glare(Fog Glow,  mix −1.0) ──┐        mix −1.0 = glare-only output
graded ─────┼─→ Glare(Streaks,   mix −1.0) ──┼─→ Mix(Add) ─→ Mix(Add) ─→ out
            └───────────────────────────────────────────┘  (original plate)
```

Set both Glare nodes' `mix` to **−1.0**... except that in 3.6, `mix = -1.0` outputs the *input image only*, not the glare only. So to get a pure glare signal you set `mix = +1.0`, which outputs **glare only**, then `Mix(Add)` it back onto the plate at a small Fac.

Corrected recipe:

| Node | Setting |
|---|---|
| Glare A (Fog Glow) | `mix = 1.0` (glare only), threshold 1.0, size 8, iterations 3, quality HIGH |
| Glare B (Streaks) | `mix = 1.0` (glare only), threshold 8.0, streaks 4, angle 15°, fade 0.9, colour mod 0.2 |
| Mix Add #1 | plate + GlareA, **Fac 0.25–0.45** |
| Mix Add #2 | result + GlareB, **Fac 0.15–0.30** |

Now each glare reads the *original* hot pixels, you have an independent intensity dial per glare, and you can mask either one (multiply the glare branch by an `Emission` pass or a Cryptomatte matte so only the splash sparkles and the label doesn't).

**Mask the glare to the splash.** Multiply the Streaks branch by the Cryptomatte-object matte of the liquid, dilated a few pixels (`Dilate/Erode`, distance 3–6, `Feather`). Result: the water sparkles, the backdrop doesn't wash out, the label stays crisp and legible. This one move is the difference between "nice render" and "commercial".

### 3.4 Bloom vs Glare — which to use

| | EEVEE Bloom | Compositor Glare (Fog Glow) | Compositor Glare (Bloom type, 4.4+) |
|---|---|---|---|
| Available in Cycles | **No** | Yes | Yes |
| Available in EEVEE | 3.6 yes; **removed in 4.2 (EEVEE Next)** | Yes | Yes |
| Works from render passes / masks | No | Yes | Yes |
| Tunable after render (from EXR) | No | Yes | Yes |
| Physically shaped | Crude, blocky mip-chain | Convolution — better falloff | Best falloff, energy-conserving |

**Verdict: always Glare, in the compositor.** Cycles has no Bloom at all, so for this project it isn't even a choice. And EEVEE's Bloom was removed in 4.2 precisely because the compositor does it better. If you're on 4.4+, the new `BLOOM` glare type gives a cleaner, more energy-conserving halo than `FOG_GLOW` — use it for the broad halo and keep `STREAKS` for the star.

### 3.5 Lens Distortion — chromatic aberration that reads as "real lens"

Node: `CompositorNodeLensdist`. Inputs: **Distort**, **Dispersion**.

| Look | Distort | Dispersion |
|---|---|---|
| **Product / commercial default** | `0.000` to `+0.008` | **`0.003`–`0.006`** |
| Slightly wide, handheld feel | `+0.010` to `+0.020` | `0.006`–`0.010` |
| Vintage / anamorphic-ish | `−0.015` (pincushion) | `0.010`–`0.015` |
| **Broken** | `>0.05` | **`>0.020`** — visible colour fringes across the whole frame, reads as a bug |

Dispersion above ~0.02 puts red/blue fringing on *every* edge including the centre, which no real lens does. Real CA is **zero at the optical centre and increases toward the corners** — which is exactly what this node models, so the correct move is a small global value and let the geometry do the work.

Options:
- `use_fit` — **on** when `Distort > 0`, otherwise barrel distortion pulls black wedges into the corners.
- `use_jitter` — **off** for finals. It trades banding for noise; you're adding grain later anyway.
- `use_projector` — off (it's a 1D horizontal-only mode, for anamorphic-style CA; occasionally nice at Dispersion 0.008).

**Half-step upgrade:** for CA that varies with focus (real lenses do), duplicate the Lens Distortion, set the second to a higher dispersion, and Mix between them using the *inverse* of the Mist pass — more fringing on distant, out-of-focus material. Two extra nodes, disproportionate payoff.

### 3.6 Vignette

Built from primitives, because there's no vignette node.

```
Ellipse Mask ─→ Blur (Fast Gauss, large) ─→ [optional Map Range / Curves] ─┐
                                                                           ├→ Mix(Multiply) ─→ out
plate ─────────────────────────────────────────────────────────────────────┘
```

| Node | Setting | Value |
|---|---|---|
| **Ellipse Mask** | `mask_type` | `ADD` |
| | `x`, `y` | `0.5, 0.5` (or off-centre to match an off-centre product) |
| | `width`, `height` | **`0.75`, `0.85`** — wider than the frame so the falloff starts outside it |
| | `rotation` | `0` |
| **Blur** | `filter_type` | `FAST_GAUSS` (cheap, and you want maximum softness anyway) |
| | `use_relative` | **On** — so the vignette scales with resolution instead of breaking at 4K |
| | `factor_x`, `factor_y` | **`0.25`, `0.25`** (25% of frame width/height) |
| **Mix** | `blend_type` | `MULTIPLY` |
| | `Fac` | **`0.15`–`0.30`** — 0.15 barely-there, 0.30 obvious, 0.5+ is a phone filter |

**Do it in linear, and keep it gentle.** A multiply of 0.7 in linear is roughly −0.5 stops, which after AgX/Filmic reads as a *lot* darker than you expect. Start at Fac 0.18 and only raise it after you've seen the tone-mapped result.

**Warm vignette variant** (very effective on an orange-backdrop ad): instead of `Multiply` by a grey mask, use the mask to `Mix` between the plate and a slightly warmer, slightly darker graded copy. Corners go warm and deep instead of just grey-dark. Two extra nodes, much richer.

### 3.7 The grade

Three nodes carry the whole look: **Color Balance**, **RGB Curves**, **Hue/Saturation**.

#### 3.7.1 Color Balance (Lift / Gamma / Gain)

Node: `CompositorNodeColorBalance`, `correction_method = 'LIFT_GAMMA_GAIN'`.

- **Lift** — shadows. `1.0` is neutral in Blender's LGG *for gamma and gain*, but **Lift is centred on 1.0 too** in this node (it's `(color - 1) + input` style). Nudges of ±0.02 are large.
- **Gamma** — midtones. `1.0` neutral.
- **Gain** — highlights / overall multiply. `1.0` neutral.

Beverage-ad starting values, warm orange key, neutral product:

| | R | G | B | Effect |
|---|---|---|---|---|
| **Lift** | `0.995` | `1.000` | `1.015` | Blue-teal shadow lift. Complements the orange, and the *lift itself* is the "black point lift" from §4 — see below. |
| **Gamma** | `1.000` | `0.985` | `0.960` | Warms the midtones without touching the highlight. |
| **Gain** | `1.060` | `1.000` | `0.940` | Pushes the orange backdrop, keeps highlights from going yellow-clipped. |

**The black-point lift, properly.** A true black point lift means "0.0 in becomes ~0.005–0.015 out". Two ways:

1. **Color Balance Lift** raised slightly on all three channels: `(1.006, 1.008, 1.018)`. Blue-heavy = the classic filmic teal shadow.
2. **RGB Curves**, drag the *first* point of the master curve up from `(0.0, 0.0)` to `(0.0, 0.008)`.

In *linear* space, `0.008` looks like nothing on the scope and reads as a huge change on screen after the view transform. Do it, check it after tone mapping, and stop at the point where the blacks stop feeling like a hole. Nothing says "CG" louder than a frame with a genuine 0,0,0 in it.

#### 3.7.2 RGB Curves

Node: `CompositorNodeCurveRGB`. `mapping.curves[0..3]` = **C (combined), R, G, B**.

Two curves, in this order in the chain:

- **Master (C):** a *gentle* S. Points at `(0.0, 0.008)` [black lift], `(0.18, 0.17)` [pull mid-grey down a hair], `(1.0, 1.0)`. That's it. Any more contrast and it fights the view transform.
- **Per-channel split-tone (optional):** R curve lifted very slightly at the top, B curve lifted very slightly at the bottom. Two points each, moved by 0.01. This is the "orange & teal" move; at these magnitudes it reads as *film stock*, not as a look.

After adding points, call `curve_node.mapping.update()` or the curve won't re-evaluate.

#### 3.7.3 Hue/Saturation — the targeted product boost

Node: `CompositorNodeHueSat` (inputs `Hue`, `Saturation`, `Value`, `Fac`).

| Target | Hue | Saturation | Value | Delivered via |
|---|---|---|---|---|
| **Product / label** | `0.500` (neutral) or ±`0.005` to lock a brand colour | **`1.12`** | `1.02` | Cryptomatte object/material matte → Fac |
| **Splash / liquid** | `0.500` | **`0.85`** | `1.00` | Cryptomatte liquid matte → Fac |
| **Backdrop** | `0.500` | **`1.10`** | `0.96` | Cryptomatte backdrop matte → Fac |
| **Global (last resort)** | `0.500` | `1.04` | `1.00` | no mask |

**Why the splash gets *desaturated*.** Water is colourless. If your orange key light and the orange backdrop bleed into the splash — and they will, that's correct light transport — the water reads as *juice*, or worse, as orange soap. A commercial water/soda splash reads **neutral-white to very slightly cool**, because that's what "clean" and "refreshing" look like. Pull saturation on the liquid matte to 0.80–0.88 and, if it's still warm, add a tiny Color Balance on that branch with Gain `(0.98, 1.00, 1.03)`.

This is the single most common failure in amateur beverage renders: everything is one temperature and the splash has no separation from the backdrop.

#### 3.7.4 Cryptomatte-driven selective grades

The pattern, repeated per target:

```
Render Layers ──→ Cryptomatte (source RENDER, layer CryptoObject, pick "Liquid")
                       │ Matte
                       ↓
plate ──┬──────────────────────────────────────┐
        └─→ [Hue/Sat + Color Balance branch] ──┴─→ Mix(blend MIX, Fac ← Matte) ─→ out
```

Rules:
- **Tap Cryptomatte off Render Layers directly** (§1.5).
- Use `CompositorNodeCryptomatteV2` (the "Cryptomatte" node in 3.x/4.x). The old `CompositorNodeCryptomatte` is legacy.
- `source = 'RENDER'` reads from the Render Layers/scene; `'IMAGE'` reads from a loaded EXR sequence. **Use `'IMAGE'` when re-comping from disk** — this is the whole point of writing EXRs.
- Add object names to `matte_id` (comma-separated) or use the eyedropper in the UI which fills `entries`.
- **Feather every matte.** A raw crypto matte has a 1-pixel hard edge; a grade applied through it will show as an outline. `Dilate/Erode` at distance `1–2` with `mode='FEATHER'`, or a `Blur` (Fast Gauss, 1.5 px).
- Chain the mattes with `Math(Maximum)` when you want "bottle OR label", `Math(Minimum)` for intersections, `Math(Subtract)` to cut one out of another.
- Build a **"everything else"** matte with `Math(Subtract)` from a value of 1.0 so you can grade the backdrop without picking it.

### 3.8 Sharpen and grain

#### Sharpen — `CompositorNodeFilter`, `filter_type = 'SHARPEN'`

| Delivery resolution | Safe `Fac` | Starts to crunch at |
|---|---|---|
| 1080p | **0.10–0.25** | ~0.35 |
| 1440p | 0.20–0.35 | ~0.45 |
| 4K (viewed at 4K) | 0.30–0.50 | ~0.60 |
| 4K downscaled to 1080p | 0.05–0.15 *after* the downscale, not before | — |

The tell is a **bright halo on the bottle's silhouette against the backdrop** — a light rim that wasn't in the render. Once you can see it, you are already 2× past the limit. Check at 100% zoom on a high-contrast edge, not on the whole frame.

**Better than the Filter node: unsharp mask.** Halo-free, and you control the radius:

```
plate ─┬───────────────────────────────────→ Mix(Add, Fac 0.20) ─→ out
       ├─→ Blur (Fast Gauss, 3–5 px) ─┐            ↑
       └────────────────────────────  Mix(Subtract) ┘
```

**Best: sharpen only the product.** Multiply the sharpen contribution by the bottle's Cryptomatte matte. The label stays crisp and legible (which is what the client is actually paying for), while the splash and backdrop stay soft and photographic. A real lens is not uniformly sharp; uniform sharpness is a CG tell.

**Do not sharpen before grain.** Sharpening grain turns it into speckle.

#### Film grain — `CompositorNodeTexture` + `Mix`

Blender's legacy **Noise** texture datablock produces a *different random pattern every frame* — which is exactly what grain must do, and why this is the standard trick rather than a static image.

```python
tex = bpy.data.textures.new("GRAIN", type='NOISE')      # animates per-frame, free
```

```
Texture(NOISE) ─→ [Value out] ─→ Mix(OVERLAY or SOFT_LIGHT, Fac 0.02–0.05) ─→ out
plate ───────────────────────────↑
```

| Delivery | Blend | Fac | Notes |
|---|---|---|---|
| Broadcast / cinema | `OVERLAY` | **0.03–0.05** | Survives H.264. |
| Web / social | `OVERLAY` | **0.02–0.035** | Aggressive social encoders eat grain; more than 0.05 costs you bitrate on the *image*. |
| Subtle "sensor" only | `SOFT_LIGHT` | 0.02 | Barely visible, still kills banding. |
| Wrong | `ADD` at high Fac | — | Lifts the blacks as a side effect and makes grain visible only in shadows. |

**Why a tiny amount of grain sells CG.** Three separate mechanisms:

1. **It dithers.** Grain is noise, and noise is dither. A smooth orange gradient that bands at 8-bit stops banding the moment you add 1–2 levels of noise, because the noise pushes pixels across the quantisation boundary stochastically. This alone justifies it.
2. **It unifies.** A CG frame has *zero* noise floor in some regions (a flat backdrop) and denoiser-smoothed texture in others. Grain gives the whole frame one consistent noise floor, which is what a real sensor does, and the eye reads that consistency as "one photographic capture" rather than "assembled elements".
3. **It hides.** Denoiser smearing, slightly plasticky shading, a subdivision seam — grain buries all of it in a way that costs you nothing.

**Resolution caveat.** Grain must be ~1 pixel *at delivery resolution*. If you comp at 4K and deliver 1080p, the downscale averages your grain away to nothing. Either add grain at the end of the VSE/encode step (`ffmpeg -vf noise=alls=6:allf=t+u`) or raise the comp-stage Fac by ~2× and accept it looks coarse in the 4K master.

### 3.9 Dual output — EXR master + PNG review from one graph

`CompositorNodeOutputFile` carries **its own format and its own colour management override**. That's how you get both files from one render.

| Node | Format | Colour management | Path |
|---|---|---|---|
| `Composite` | scene setting | scene | `scene.render.filepath` |
| File Output "MASTER" | `OPEN_EXR_MULTILAYER`, 32-bit, ZIP | Override → **Standard**, look None | `//05_renders/shot010/exr/` |
| File Output "REVIEW" | `PNG`, 8-bit, compression 15 | Override → **Filmic / AgX** + look | `//05_renders/shot010/png/` |

The REVIEW node is fed from the **end** of the graph (post-grain). The MASTER node is fed from wherever you want your recoverable master — usually **post-denoise, pre-grade**, so a re-grade never needs a re-render. Wire a second File Output to the graph's end if you also want a graded linear master.

### 3.10 bpy — build the whole graph

```python
# ── build_comp.py ──────────────────────────────────────────────────────────
# Builds the full beverage-ad compositor graph, Blender 3.6 LTS.
# 4.x notes are inline; run build(dry_check=True) first to see version flags.
import bpy

# ---------------------------------------------------------------------------
CFG = {
    # denoise
    "denoise_prefilter":  'ACCURATE',
    # grade
    "lift":  (0.995, 1.000, 1.015, 1.0),
    "gamma": (1.000, 0.985, 0.960, 1.0),
    "gain":  (1.060, 1.000, 0.940, 1.0),
    "black_lift": 0.008,
    # glare A - fog glow
    "fog_threshold": 1.0, "fog_size": 8, "fog_iters": 3, "fog_add_fac": 0.35,
    # glare B - streaks
    "str_threshold": 8.0, "str_streaks": 4, "str_angle": 15.0,
    "str_fade": 0.90, "str_colmod": 0.20, "str_iters": 3, "str_add_fac": 0.22,
    # lens
    "distort": 0.004, "dispersion": 0.0045,
    # vignette
    "vig_w": 0.75, "vig_h": 0.85, "vig_blur": 0.25, "vig_fac": 0.18,
    # sharpen / grain
    "sharpen_fac": 0.18,
    "grain_fac": 0.030,
    # selective grades: crypto object names -> (sat, val, gain rgb)
    "product_objects": "Bottle,Label,Cap",
    "liquid_objects":  "Liquid,Splash,Droplets",
    "product_sat": 1.12, "product_val": 1.02,
    "liquid_sat":  0.85,
    # outputs
    "exr_dir": "//05_renders/shot010/exr/",
    "png_dir": "//05_renders/shot010/png/",
}
# ---------------------------------------------------------------------------

def _v():
    return bpy.app.version

def _n(tree, idname, name, loc):
    n = tree.nodes.new(idname)
    n.name = n.label = name
    n.location = loc
    return n

def _mix(tree, name, loc, blend='MIX', fac=0.5):
    """MixRGB — still CompositorNodeMixRGB in 3.6 AND 4.x.
    (The Mix-node replacement in 3.4 was shader-only.)"""
    n = _n(tree, 'CompositorNodeMixRGB', name, loc)
    n.blend_type = blend
    n.inputs[0].default_value = fac
    return n

def _hue_sat(tree, name, loc, hue=0.5, sat=1.0, val=1.0):
    n = _n(tree, 'CompositorNodeHueSat', name, loc)
    # 2.81+ exposes these as sockets. Older builds used color_hue/... properties.
    try:
        n.inputs['Hue'].default_value = hue
        n.inputs['Saturation'].default_value = sat
        n.inputs['Value'].default_value = val
    except KeyError:
        n.color_hue, n.color_saturation, n.color_value = hue, sat, val
    return n

def _crypto(tree, name, loc, layer, ids):
    n = _n(tree, 'CompositorNodeCryptomatteV2', name, loc)
    n.source = 'RENDER'          # 'IMAGE' when re-comping from EXRs on disk
    n.scene = bpy.context.scene
    n.layer_name = layer         # 'CryptoObject' | 'CryptoMaterial' | 'CryptoAsset'
    n.matte_id = ids             # comma-separated names
    return n

def build(dry_check=False):
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()
    L = tree.links.new
    C = CFG
    ver = _v()

    if dry_check:
        print(f"[comp] Blender {ver}")
        if ver >= (4, 4, 0):
            print("[comp] 4.4+: Glare node was rewritten (Bloom type, socket "
                  "Threshold/Strength/Size). 'mix'/'quality' may not exist — "
                  "values below are 3.6 semantics, re-tune after upgrade.")
        if ver >= (4, 0, 0):
            print("[comp] 4.0+: default view transform is AgX, not Filmic. "
                  "Your grade WILL look different. See section 12.")
        if ver >= (4, 2, 0):
            print("[comp] 4.2+: set scene.render.compositor_device = 'GPU' "
                  "and compositor_precision = 'AUTO' for speed/VRAM.")

    # ── 1. source ─────────────────────────────────────────────────────────
    rl = _n(tree, 'CompositorNodeRLayers', "RENDER_LAYERS", (-1600, 0))
    rl.scene = scene

    # ── 2. despeckle (fireflies that survived) ────────────────────────────
    desp = _n(tree, 'CompositorNodeDespeckle', "DESPECKLE", (-1400, 0))
    desp.threshold = 0.5
    desp.threshold_neighbor = 0.5
    L(rl.outputs['Image'], desp.inputs['Image'])

    # ── 3. denoise ────────────────────────────────────────────────────────
    dn = _n(tree, 'CompositorNodeDenoise', "DENOISE", (-1200, 0))
    dn.use_hdr = True
    dn.prefilter = C["denoise_prefilter"]
    L(desp.outputs['Image'], dn.inputs['Image'])
    for src, dst in (('Denoising Normal', 'Normal'), ('Denoising Albedo', 'Albedo')):
        if src in rl.outputs:
            L(rl.outputs[src], dn.inputs[dst])
        else:
            print(f"[comp] MISSING '{src}' — enable view_layer.cycles."
                  f"denoising_store_passes. Denoiser will smear the splash.")

    # ── 4. cryptomatte branches (tapped from RENDER LAYERS, not denoise) ──
    cr_prod = _crypto(tree, "CRYPTO_PRODUCT", (-1200, -600),
                      'CryptoObject', C["product_objects"])
    cr_liq  = _crypto(tree, "CRYPTO_LIQUID",  (-1200, -900),
                      'CryptoObject', C["liquid_objects"])
    for cn in (cr_prod, cr_liq):
        L(rl.outputs['Image'], cn.inputs['Image'])

    # feather the mattes so grades don't outline
    def feather(src_node, name, loc):
        d = _n(tree, 'CompositorNodeDilateErode', name, loc)
        d.mode = 'FEATHER'
        d.distance = 2
        L(src_node.outputs['Matte'], d.inputs['Mask'])
        return d
    f_prod = feather(cr_prod, "FEATHER_PRODUCT", (-980, -600))
    f_liq  = feather(cr_liq,  "FEATHER_LIQUID",  (-980, -900))

    # ── 5/6. comp DOF & vector blur: intentionally NOT built. ─────────────
    # Render DOF and motion blur in camera for a splash. See sections 1.4/1.7.
    # If you must: CompositorNodeDefocus (use_zbuffer=True, Z from rl) here,
    # and CompositorNodeVecBlur (needs Z + Speed) immediately after.

    # ── 7. primary grade ──────────────────────────────────────────────────
    cb = _n(tree, 'CompositorNodeColorBalance', "GRADE_LGG", (-950, 0))
    cb.correction_method = 'LIFT_GAMMA_GAIN'
    cb.lift, cb.gamma, cb.gain = C["lift"], C["gamma"], C["gain"]
    L(dn.outputs['Image'], cb.inputs['Image'])

    # ── 8. selective grades via cryptomatte ───────────────────────────────
    hs_prod = _hue_sat(tree, "HS_PRODUCT", (-750, -300),
                       sat=C["product_sat"], val=C["product_val"])
    L(cb.outputs['Image'], hs_prod.inputs['Image'])
    mix_prod = _mix(tree, "MIX_PRODUCT", (-550, -150), 'MIX', 1.0)
    L(cb.outputs['Image'],      mix_prod.inputs[1])
    L(hs_prod.outputs['Image'], mix_prod.inputs[2])
    L(f_prod.outputs['Mask'],   mix_prod.inputs[0])

    hs_liq = _hue_sat(tree, "HS_LIQUID_NEUTRALISE", (-750, -650),
                      sat=C["liquid_sat"], val=1.0)
    L(mix_prod.outputs['Image'], hs_liq.inputs['Image'])
    # nudge the water cool so it reads as water, not juice
    cb_liq = _n(tree, 'CompositorNodeColorBalance', "GRADE_LIQUID_COOL", (-550, -650))
    cb_liq.correction_method = 'LIFT_GAMMA_GAIN'
    cb_liq.gain = (0.980, 1.000, 1.030, 1.0)
    L(hs_liq.outputs['Image'], cb_liq.inputs['Image'])
    mix_liq = _mix(tree, "MIX_LIQUID", (-350, -400), 'MIX', 1.0)
    L(mix_prod.outputs['Image'], mix_liq.inputs[1])
    L(cb_liq.outputs['Image'],   mix_liq.inputs[2])
    L(f_liq.outputs['Mask'],     mix_liq.inputs[0])

    graded = mix_liq

    # ── 9/10. glare: branch-and-add, so each reads the ORIGINAL hot pixels ─
    gl_fog = _n(tree, 'CompositorNodeGlare', "GLARE_FOG_GLOW", (-150, 350))
    gl_str = _n(tree, 'CompositorNodeGlare', "GLARE_STREAKS",  (-150, 700))
    if ver < (4, 4, 0):
        gl_fog.glare_type = 'FOG_GLOW'
        gl_fog.quality    = 'HIGH'
        gl_fog.mix        = 1.0            # 1.0 = glare only (we Add it back)
        gl_fog.threshold  = C["fog_threshold"]
        gl_fog.size       = C["fog_size"]
        gl_fog.iterations = C["fog_iters"]

        gl_str.glare_type       = 'STREAKS'
        gl_str.quality          = 'HIGH'
        gl_str.mix              = 1.0
        gl_str.threshold        = C["str_threshold"]
        gl_str.streaks          = C["str_streaks"]
        gl_str.angle_offset     = C["str_angle"] * 3.14159265 / 180.0
        gl_str.fade             = C["str_fade"]
        gl_str.color_modulation = C["str_colmod"]
        gl_str.iterations       = C["str_iters"]
    else:
        # 4.4+ rewrote Glare. Types include 'BLOOM'; params moved to sockets.
        gl_fog.glare_type = 'BLOOM'
        gl_str.glare_type = 'STREAKS'
        for node, thr in ((gl_fog, C["fog_threshold"]), (gl_str, C["str_threshold"])):
            for sock, val in (("Threshold", thr), ("Strength", 1.0),
                              ("Size", 0.6), ("Saturation", 1.0)):
                if sock in node.inputs:
                    node.inputs[sock].default_value = val
        if "Streaks" in gl_str.inputs:
            gl_str.inputs["Streaks"].default_value = C["str_streaks"]
        print("[comp] 4.4+ Glare params set best-effort — eyeball and re-tune.")

    L(graded.outputs['Image'], gl_fog.inputs['Image'])
    L(graded.outputs['Image'], gl_str.inputs['Image'])

    # mask the streaks to the liquid so only the water sparkles
    str_mask = _mix(tree, "STREAKS_MASKED", (60, 700), 'MULTIPLY', 1.0)
    L(gl_str.outputs['Image'], str_mask.inputs[1])
    L(f_liq.outputs['Mask'],   str_mask.inputs[2])

    add_fog = _mix(tree, "ADD_FOG_GLOW", (250, 150), 'ADD', C["fog_add_fac"])
    L(graded.outputs['Image'],  add_fog.inputs[1])
    L(gl_fog.outputs['Image'],  add_fog.inputs[2])

    add_str = _mix(tree, "ADD_STREAKS", (450, 150), 'ADD', C["str_add_fac"])
    L(add_fog.outputs['Image'],  add_str.inputs[1])
    L(str_mask.outputs['Image'], add_str.inputs[2])

    # ── 11. lens distortion / chromatic aberration ────────────────────────
    ld = _n(tree, 'CompositorNodeLensdist', "LENS_CA", (650, 150))
    ld.use_fit = True
    ld.use_jitter = False
    ld.use_projector = False
    ld.inputs['Distort'].default_value    = C["distort"]
    ld.inputs['Dispersion'].default_value = C["dispersion"]
    L(add_str.outputs['Image'], ld.inputs['Image'])

    # ── 12. vignette ──────────────────────────────────────────────────────
    em = _n(tree, 'CompositorNodeEllipseMask', "VIGNETTE_MASK", (650, -450))
    em.mask_type = 'ADD'
    em.x, em.y = 0.5, 0.5
    em.width, em.height = C["vig_w"], C["vig_h"]
    em.rotation = 0.0
    vb = _n(tree, 'CompositorNodeBlur', "VIGNETTE_BLUR", (850, -450))
    vb.filter_type = 'FAST_GAUSS'
    vb.use_relative = True                 # scales with resolution
    vb.factor_x = vb.factor_y = C["vig_blur"] * 100.0
    L(em.outputs['Mask'], vb.inputs['Image'])
    vig = _mix(tree, "VIGNETTE_MULTIPLY", (1050, 150), 'MULTIPLY', C["vig_fac"])
    L(ld.outputs['Image'],  vig.inputs[1])
    L(vb.outputs['Image'],  vig.inputs[2])

    # ── 13. final curves: gentle S + black point lift ─────────────────────
    cu = _n(tree, 'CompositorNodeCurveRGB', "CURVES_FINAL", (1250, 150))
    m = cu.mapping
    master = m.curves[3]                   # 0=C? -> in compositor: 0..2 = R,G,B, 3 = C
    # NOTE: CurveRGB layout is curves[0]=C, [1]=R, [2]=G, [3]=B in most builds.
    # Verify once in your version; the safe move is to index by len and test.
    master = m.curves[0]
    master.points[0].location = (0.0, C["black_lift"])
    master.points[-1].location = (1.0, 1.0)
    p = master.points.new(0.18, 0.170)     # gentle mid pull
    p.handle_type = 'AUTO_CLAMPED'
    m.update()
    L(vig.outputs['Image'], cu.inputs['Image'])

    # ── 14. sharpen (masked to the product) ───────────────────────────────
    sh = _n(tree, 'CompositorNodeFilter', "SHARPEN", (1450, -200))
    sh.filter_type = 'SHARPEN'
    sh.inputs['Fac'].default_value = 1.0
    L(cu.outputs['Image'], sh.inputs['Image'])
    sh_mix = _mix(tree, "SHARPEN_MIX", (1650, 150), 'MIX', C["sharpen_fac"])
    L(cu.outputs['Image'], sh_mix.inputs[1])
    L(sh.outputs['Image'], sh_mix.inputs[2])
    # To sharpen ONLY the product, drive sh_mix.inputs[0] from f_prod instead:
    #   L(f_prod.outputs['Mask'], sh_mix.inputs[0])   # then set fac via a Math mul

    # ── 15. film grain ────────────────────────────────────────────────────
    tex = bpy.data.textures.get("GRAIN_NOISE") or \
          bpy.data.textures.new("GRAIN_NOISE", type='NOISE')  # re-randomises per frame
    gt = _n(tree, 'CompositorNodeTexture', "GRAIN_TEX", (1650, -500))
    gt.texture = tex
    grain = _mix(tree, "GRAIN_MIX", (1900, 150), 'OVERLAY', C["grain_fac"])
    L(sh_mix.outputs['Image'], grain.inputs[1])
    L(gt.outputs['Color'],     grain.inputs[2])

    # ── 16. outputs ───────────────────────────────────────────────────────
    comp = _n(tree, 'CompositorNodeComposite', "COMPOSITE", (2150, 250))
    view = _n(tree, 'CompositorNodeViewer',    "VIEWER",    (2150, 0))
    L(grain.outputs['Image'], comp.inputs['Image'])
    L(grain.outputs['Image'], view.inputs['Image'])

    # linear master, tapped POST-DENOISE / PRE-GRADE so a re-grade never re-renders
    fo_exr = _n(tree, 'CompositorNodeOutputFile', "OUT_EXR_MASTER", (2150, -350))
    fo_exr.base_path = C["exr_dir"]
    f = fo_exr.format
    f.file_format = 'OPEN_EXR_MULTILAYER'
    f.color_mode, f.color_depth, f.exr_codec = 'RGBA', '32', 'ZIP'   # ZIP: crypto-safe
    f.color_management = 'OVERRIDE'
    f.view_settings.view_transform = 'Standard'
    f.view_settings.look = 'None'
    fo_exr.layer_slots.clear()
    for slot in ("Beauty", "Denoised"):
        fo_exr.layer_slots.new(slot)
    L(dn.outputs['Image'],   fo_exr.inputs['Denoised'])
    L(rl.outputs['Image'],   fo_exr.inputs['Beauty'])

    # display-referred review PNGs, from the END of the graph
    fo_png = _n(tree, 'CompositorNodeOutputFile', "OUT_PNG_REVIEW", (2150, -750))
    fo_png.base_path = C["png_dir"]
    g = fo_png.format
    g.file_format, g.color_mode, g.color_depth, g.compression = 'PNG', 'RGB', '8', 15
    g.color_management = 'OVERRIDE'
    g.view_settings.view_transform = 'AgX' if ver >= (4, 0, 0) else 'Filmic'
    g.view_settings.look = 'None'
    fo_png.file_slots.clear()
    fo_png.file_slots.new("shot010_")
    L(grain.outputs['Image'], fo_png.inputs[0])

    print(f"[comp] built {len(tree.nodes)} nodes on Blender {ver}")
    return tree

if __name__ == "__main__":
    build(dry_check=True)
```

> **`CurveRGB` channel index:** in the compositor `CompositorNodeCurveRGB.mapping.curves` is ordered **C, R, G, B** (index 0 = combined). Verify once in your build by editing index 0 and watching which curve moves in the UI — a wrong index silently grades a single channel.

---

## 4. The "make CG look real" checklist

Product and liquid work is the hardest CG to sell, because the viewer has seen ten thousand real beverage ads and knows exactly what a bottle looks like. Everything below is cheap and every one of them is doing work.

| # | Move | Where | Value | Failure mode if overdone |
|---|---|---|---|---|
| 1 | **Imperfection** — fingerprints, dust, micro-scratches, uneven condensation, a label that isn't perfectly centred, a bevel on every hard edge | Shading (module 03), but *check for it here* | — | Looks dirty / cheap |
| 2 | **Highlight bloom** | Glare Fog Glow | thr 1.0, size 8, add 0.25–0.45 | Hazy, milky, "dream sequence" |
| 3 | **Aperture streaks on wet speculars** | Glare Streaks, masked to liquid | thr 8.0, 4 streaks, 15°, add 0.15–0.30 | J.J. Abrams |
| 4 | **Chromatic aberration** | Lens Distortion Dispersion | **0.003–0.006** | >0.02 = colour fringes everywhere = reads as a bug |
| 5 | **Barrel distortion** | Lens Distortion Distort | 0.000–0.008, `use_fit` on | >0.03 = GoPro |
| 6 | **Vignette** | Ellipse→Blur→Multiply | Fac 0.15–0.25 | >0.35 = Instagram filter |
| 7 | **Black point lift** | Curves point 0 → y=0.008, or Lift (1.006,1.008,1.018) | 0.005–0.015 | >0.03 = washed-out, no contrast |
| 8 | **Film grain** | Noise Texture → Overlay | Fac 0.02–0.05 | >0.08 = "I applied a grain plugin" |
| 9 | **DON'T over-sharpen** | Filter Sharpen | ≤0.25 at 1080p | Bright halo on the bottle silhouette |
| 10 | **Non-uniform sharpness** | Sharpen masked to product only | — | Uniformly crisp frame = CG tell |
| 11 | **Real motion blur** (not vector blur) | Render Properties, Shutter 0.5 | 180° shutter | Strobing splash droplets |
| 12 | **Highlight roll-off, not clipping** | Filmic/AgX view transform, not Standard | — | Blown flat white patches |
| 13 | **Slightly imperfect white balance** | Grade — let the frame lean 100–200 K warm | Gain (1.06, 1.00, 0.94) | A perfectly neutral frame reads as a render, not a photograph |
| 14 | **Splash reads neutral-white against a warm key** | Hue/Sat sat 0.85 on liquid matte | — | Orange water = juice = wrong product |
| 15 | **Micro camera shake** | Camera noise modifier, amplitude ~0.1–0.3% of frame | — | A perfectly locked camera is a tripod; even tripods drift |
| 16 | **Out-of-focus foreground element** | A droplet or fruit slice near the lens, well out of focus | — | Gives the lens a *depth* to have |
| 17 | **Something breaks the frame edge** | Let a droplet or the fruit clip the border | — | Everything perfectly contained = product-render, not commercial |
| 18 | **Consistent noise floor** | Grain (see #8) | — | Some regions mathematically clean, others denoised = uncanny |

**Two anti-patterns specific to liquid:**

- **The splash is too symmetric.** Real splashes are asymmetric because the impact was off-axis. If your Mantaflow crown is radially perfect, offset the emitter or the obstacle.
- **The droplets are all the same size.** Real spray is a power-law distribution — a few big blobs, many tiny ones. If your resolution can't produce the small ones, fake them with a particle/geo-nodes scatter (module 04) or add a subtle out-of-focus droplet plate in comp.

**The single highest-value item on this list is #14.** A neutral splash against a warm backdrop is the entire visual grammar of beverage advertising. It is also the one that is free and that almost nobody does.

---

## 5. Video Sequence Editor assembly

Use a **separate .blend** for the edit (`07_edit/edit_v003.blend`). Reasons: its scene needs a different view transform (§11.6), you don't want the 40 GB fluid cache attached to your cutting file, and it keeps render settings from colliding.

### 5.1 Bringing in the sequence

- **Add → Image/Sequence**, select the *whole* folder of frames (`A` to select all), one strip.
- **Set the edit scene's `fps` to exactly the render fps** *before* adding strips. Adding at the wrong fps stretches strip durations and is annoying to fix afterwards.
- **Colour space per strip:** `strip.colorspace_settings.name`. If you're loading **display-referred PNGs**, set it to `sRGB` and set the edit scene's view transform to **`Standard`**. If you're loading **linear EXRs**, set the strip to `Linear`/`Linear Rec.709` and set the scene's view transform to **AgX/Filmic**. Getting this wrong is the #1 cause of "why is my video washed out" (§11.6).
- **Proxies** for scrubbing on big sequences: `strip.use_proxy = True`, build 50%, `strip.proxy.quality = 90`. Rebuild with `bpy.ops.sequencer.rebuild_proxy()`. Set `Proxy Render Size` to 50% in the preview sidebar; **switch it back to `None`/Full before final render** or you'll deliver a half-res encode.

### 5.2 Endcard / logo

Two options:

1. **Image strip** — export the logo lockup as a PNG **with alpha** at 2× delivery resolution. Add it above the footage on a higher channel, set `blend_type = 'ALPHA_OVER'`. Transform it with the strip's Transform (`strip.transform.scale_x/y`, `offset_x/y`) and keyframe those for a slow 2–4% push-in over the endcard's duration. Static logos read as dead air; a slow scale drift reads as intentional.
2. **Scene strip** — a second Blender scene containing the 3D endcard (bottle + text), added with **Add → Scene**. Renders live at edit time. Heavier, but you can restage the endcard without leaving the file.

Endcard duration: **1.5–2.5 s** minimum for a 15 s spot, held *dead still* on the logo for the last second (broadcast clearance often requires a static, legible logo hold).

### 5.3 Cross-dissolves and cuts

- **Cross:** select two overlapping strips → **Add → Transition → Cross** (or `Gamma Cross`, which blends in a gamma-corrected space and is usually the better-looking one for a bright product shot — it avoids the mid-dissolve dip in perceived brightness).
- **Duration:** 8–12 frames at 24 fps for a soft product dissolve; 4–6 frames for a snappy one; 20+ frames only for the final fade to the endcard.
- **Beverage ads mostly cut, they don't dissolve.** Reserve dissolves for: splash → product hero, and product → endcard. Everything else is a hard cut on the beat.
- **Fade to black:** `Add → Color` strip (black) on a channel above, keyframe its `blend_alpha` 0→1. Or `Shift+F` / the `Fade` operator in the sidebar.

### 5.4 Speed control and the ramp

`Add → Effect Strip → Speed Control`. The Speed effect is a *time remapper* applied to the strip beneath it.

`speed_control` modes:

| Mode | Use |
|---|---|
| `STRETCH` | Retime the source to exactly fill the strip's length. Set the strip's `frame_final_duration` and the source stretches to fit. Simplest constant retime. |
| `MULTIPLY` | Constant multiplier (`speed_factor`). 0.5 = half speed. |
| `LENGTH` | Target a specific output length in frames. |
| `FRAME_NUMBER` | **The ramp.** `speed_frame_number` is keyframeable — you author an explicit "at output frame N, show source frame M" curve. |

**The beverage-ad speed ramp**, in order:

1. Render the splash at **60 fps** (or render 24 fps with sub-frame-accurate motion blur and enough frames that you have footage to stretch). You cannot slow down footage you didn't shoot fast.
2. Add a Speed Control strip over the splash strip, `speed_control = 'FRAME_NUMBER'`.
3. Extend the strip's `frame_final_duration` to the length you want the ramp to occupy.
4. Keyframe `speed_frame_number`: normal rate into the impact, near-flat (slow) across the crown, then accelerating back out. Set the F-curve interpolation to **Bezier** and hand-shape the handles — linear keys give you a speed *step*, not a ramp, and it reads as a glitch.
5. **Turn on frame interpolation** on the underlying strip if you're stretching beyond the source frames — but honestly, Blender's VSE has no optical-flow interpolation. If you need more slow-mo than you rendered, **re-render more frames**. Frame blending on a splash produces ghosting that looks exactly as bad as it sounds.

**Motion blur and retiming fight each other.** Footage rendered at 60 fps with a 180° shutter has 1/120 s of blur. Slowed to 25%, that blur is now "too sharp" for the apparent motion — which is *correct* (that's what a real high-speed camera does) and is part of why slow-mo looks slow-mo. Don't try to fix it.

### 5.5 Audio — the thing a beverage ad actually lives on

A beverage spot is 60% sound design. The pour, the fizz, the crack of the cap, the whoosh into the endcard.

- **Add → Sound**, one strip per element on its own channel. Typical stack:

| Channel | Element | Notes |
|---|---|---|
| A1 | Music bed | Sets the tempo everything else locks to |
| A2 | Whoosh (pre-impact) | Starts 6–10 frames *before* the visual impact — the whoosh is the anticipation |
| A3 | Splash / impact | Lands **exactly** on the impact frame |
| A4 | Fizz / carbonation | Long tail under the hero, low level |
| A5 | Pour / glug | Under the pour section |
| A6 | Cap crack / can tab | One sharp transient |
| A7 | VO / endcard sting | |

- `strip.show_waveform = True` — non-negotiable for syncing.
- `strip.volume` is linear gain (keyframeable). `strip.pan` −1..1 (mono sources only).
- **Duck the music** under the VO: keyframe the music strip's `volume` down ~6 dB (×0.5) 4 frames before the VO and back up 6 frames after.
- **Playback sync:** set `scene.sync_mode = 'AUDIO_SYNC'` so Blender drops video frames to keep audio real-time. Without it, a heavy sequence plays back slow and you'll sync to the wrong frames.
- **Audio scrubbing:** enable it in the Playback popover so you can hear transients while dragging.
- **Blender does not mix.** No EQ, no compression, no limiter, no loudness metering. Do the real mix in Reaper/Audition/Resolve Fairlight and bring back a single stereo stem. Blender's job is sync, not mixing.

### 5.6 Syncing the splash impact to a beat

The technique, precisely:

1. Drop the music strip in, `show_waveform = True`.
2. Find the BPM. At 24 fps: **frames per beat = 24 × 60 / BPM**. At 120 BPM that's **12 frames**. At 128 BPM, 11.25 frames — which means the grid drifts, so mark the actual transients rather than trusting arithmetic.
3. Scrub to each kick transient and drop a **timeline marker** (`M`). Name the downbeats.
4. Slide the *splash strip* so its impact frame lands on a marker. Don't move the marker.
5. **Cut on the beat, land the impact one to two frames *before* it.** Physical impacts read as synced when the visual leads the audio very slightly, because the eye is slower than the ear at this scale. Two frames early at 24 fps is the sweet spot; on the beat exactly feels marginally late.
6. **Bake Sound to F-Curves** (`Graph Editor → Channel → Bake Sound to F-Curves`, or `bpy.ops.graph.sound_bake()`) if you want something *driven* by the audio — e.g. the endcard logo scale pulsing on the kick, or a light intensity throbbing with the bass. Set `low`/`high` filters to isolate the kick band (20–120 Hz) before baking or you'll get mush.

### 5.7 bpy — assemble the edit

```python
# ── build_edit.py ──────────────────────────────────────────────────────────
# VSE assembly. Blender 3.6; 4.4+ renamed .sequences -> .strips (see _seqs()).
import bpy, os

def _seqs(scene):
    """4.4 renamed SequenceEditor.sequences to .strips (Sequence -> Strip)."""
    se = scene.sequence_editor or scene.sequence_editor_create()
    return getattr(se, "strips", None) or se.sequences

def setup_edit_scene(scene=None, *, fps=24, fps_base=1.0, res=(1920, 1080),
                     display_referred_input=True):
    scene = scene or bpy.context.scene
    r = scene.render
    r.fps, r.fps_base = fps, fps_base           # 23.976 -> fps=24, fps_base=1.001
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    scene.sync_mode = 'AUDIO_SYNC'
    # CRITICAL: don't tone-map twice. See section 11.6.
    if display_referred_input:
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'None'
        scene.sequencer_colorspace_settings.name = 'sRGB'
    else:                                        # feeding linear EXRs
        scene.view_settings.view_transform = 'AgX' if bpy.app.version >= (4,0,0) else 'Filmic'
        scene.sequencer_colorspace_settings.name = 'Linear Rec.709'
    return scene

def add_image_sequence(scene, folder, channel=1, frame_start=1,
                       colorspace='sRGB', name="SHOT010"):
    folder = bpy.path.abspath(folder)
    files = sorted(f for f in os.listdir(folder)
                   if f.lower().endswith(('.png', '.exr', '.jpg', '.tif')))
    if not files:
        raise RuntimeError(f"no frames in {folder}")
    s = _seqs(scene).new_image(name=name, filepath=os.path.join(folder, files[0]),
                              channel=channel, frame_start=frame_start)
    for f in files[1:]:
        s.elements.append(f)
    s.colorspace_settings.name = colorspace
    print(f"[edit] {name}: {len(files)} frames @ ch{channel} from {frame_start}")
    return s

def add_sound(scene, filepath, channel, frame_start, volume=1.0, show_wave=True):
    s = _seqs(scene).new_sound(name=os.path.basename(filepath),
                               filepath=bpy.path.abspath(filepath),
                               channel=channel, frame_start=frame_start)
    s.volume = volume
    s.show_waveform = show_wave
    return s

def add_cross(scene, a, b, channel, gamma=True):
    """Gamma Cross avoids the mid-dissolve brightness dip. Strips must overlap."""
    return _seqs(scene).new_effect(
        name="XDISS", type='GAMMA_CROSS' if gamma else 'CROSS',
        channel=channel, frame_start=b.frame_final_start,
        frame_end=a.frame_final_end, seq1=a, seq2=b)

def add_speed_ramp(scene, strip, channel, keys):
    """keys = [(output_frame, source_frame), ...] -> a real, shapeable ramp."""
    sp = _seqs(scene).new_effect(name="SPEED", type='SPEED', channel=channel,
                                 frame_start=strip.frame_final_start,
                                 frame_end=strip.frame_final_end, seq1=strip)
    sp.speed_control = 'FRAME_NUMBER'
    for out_f, src_f in keys:
        sp.speed_frame_number = src_f
        sp.keyframe_insert("speed_frame_number", frame=out_f)
    # Bezier, not linear — linear keys give a speed STEP, not a ramp.
    ad = scene.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if "speed_frame_number" in fc.data_path:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'BEZIER'
                    kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    return sp

def mark_beats(scene, bpm, first_beat_frame, count=32, label="BEAT"):
    fpb = scene.render.fps / scene.render.fps_base * 60.0 / bpm
    for i in range(count):
        f = int(round(first_beat_frame + i * fpb))
        scene.timeline_markers.new(f"{label}{i+1}", frame=f)
    print(f"[edit] {bpm} BPM -> {fpb:.2f} frames/beat, {count} markers")

# --- example --------------------------------------------------------------
if __name__ == "__main__":
    sc = setup_edit_scene(fps=24, res=(1920, 1080), display_referred_input=True)
    hero = add_image_sequence(sc, "//05_renders/shot010/png/", channel=1, frame_start=1)
    add_sound(sc, "//07_edit/audio/music_120bpm.wav", channel=5, frame_start=1)
    add_sound(sc, "//07_edit/audio/whoosh.wav",       channel=6, frame_start=155)
    add_sound(sc, "//07_edit/audio/splash_impact.wav",channel=7, frame_start=163)
    mark_beats(sc, bpm=120, first_beat_frame=1, count=24)
    add_speed_ramp(sc, hero, channel=3, keys=[(1,1), (150,150), (175,163), (250,250)])
```

---

## 6. Encoding

### 6.1 What Blender's FFmpeg panel actually maps to

`Output Properties → Output → File Format: FFmpeg Video`, then the **Encoding** panel.

| Blender control | `bpy` | libx264 equivalent |
|---|---|---|
| Container | `scene.render.ffmpeg.format` | `-f` / file extension |
| Video Codec | `.codec` | `-c:v` |
| **Output Quality** | `.constant_rate_factor` | `-crf` (mapping below) |
| **Encoding Speed** | `.ffmpeg_preset` | `-preset` (`BEST`→`slower`, `GOOD`→`medium`, `REALTIME`→`veryfast`) |
| Keyframe Interval | `.gopsize` | `-g` |
| Max B-frames | `.use_max_b_frames` / `.max_b_frames` | `-bf` |
| Bitrate / Min / Max / Buffer | `.video_bitrate` / `.minrate` / `.maxrate` / `.buffersize` | `-b:v` / `-minrate` / `-maxrate` / `-bufsize` |
| Audio Codec / Bitrate | `.audio_codec` / `.audio_bitrate` | `-c:a` / `-b:a` |

**Output Quality → CRF mapping** (Blender's internal constants):

| Blender label | CRF |
|---|---|
| Lossless | 0 |
| Perceptually Lossless | **17** |
| High Quality | **20** |
| Medium Quality | **23** |
| Low Quality | 26 |
| Very Low Quality | 29 |
| Lowest Quality | 32 |
| None | uses `video_bitrate` instead |

Lower CRF = better = bigger. Each ±6 CRF is roughly ×2 / ÷2 file size.

**What Blender does NOT expose:**
- **H.264 profile/level.** Blender's libx264 defaults are fine (it produces High profile, `yuv420p`) but you cannot force `-profile:v high -level 4.0` for a fussy broadcast QC.
- **ProRes.** Not in the codec list. Use DNxHD in Blender, or encode externally with `prores_ks`.
- **`-movflags +faststart`.** Blender-written MP4s do not have the moov atom at the front, so they buffer badly when streamed from a web server. For any client-review link, **re-mux**: `ffmpeg -i in.mp4 -c copy -movflags +faststart out.mp4`.
- **10-bit H.264/HEVC**, colour VUI tags, closed-GOP enforcement, `-sc_threshold`.

**Conclusion: encode the review copies from Blender, encode the deliverables with standalone ffmpeg.** Blender's encoder is a convenience, not a mastering tool.

### 6.2 Preset table — Blender FFmpeg panel

| Setting | (a) Client review | (b) IG / TikTok 9:16 | (c) YouTube | (d) Broadcast mezzanine |
|---|---|---|---|---|
| Resolution | 1920×1080 | **1080×1920** | 3840×2160 (or 1920×1080) | 1920×1080 |
| FPS | match master (24) | **30** | 24 | **25** (PAL) / 29.97 (NTSC) |
| Container (`format`) | `MPEG4` | `MPEG4` | `MPEG4` | `QUICKTIME` |
| Codec (`codec`) | `H264` | `H264` | `H264` | **`DNXHD`** (no ProRes in Blender) |
| Output Quality | **`MEDIUM`** (CRF 23) | **`HIGH`** (CRF 20) | **`PERC_LOSSLESS`** (CRF 17) | `NONE` + bitrate |
| Encoding Speed | `GOOD` | `BEST` | `BEST` | `BEST` |
| Keyframe Interval | 18 | **30** (= fps, ~closed GOP) | **12** (= fps/2, YouTube's rec.) | 1 (all-intra) |
| Max B-frames | off | off (safer for social) | on, 2 | off |
| Bitrate | — (CRF) | — (CRF) | — (CRF) | ~145000 kb/s (DNxHD 145) |
| Audio codec | `AAC` | `AAC` | `AAC` | `PCM` |
| Audio bitrate | 192 | 192 | 384 | — |
| Audio mixrate | 48000 | 48000 | 48000 | 48000 |
| Burn-in (`use_stamp`) | **On** — frame, filename, note | **Off** | Off | Off |
| Typical size, 15 s | 25–45 MB | 20–35 MB | 180–400 MB (4K) | ~270 MB |

### 6.3 Preset table — standalone ffmpeg (the deliverables)

Encode from **16-bit PNG or TIFF with the view transform already applied**, *not* from EXR. ffmpeg reads EXR as linear and has no idea what AgX is — you will get a dark, wrong image. (`-apply_trc iec61966_2_1` approximates sRGB but cannot reproduce Filmic/AgX.)

**(a) Client review** — small, scrubbable, faststart, burn-in already baked by Blender's stamp:

```bash
ffmpeg -y -framerate 24 -i png/shot010_%04d.png \
  -c:v libx264 -profile:v high -level 4.0 -pix_fmt yuv420p \
  -crf 22 -preset medium -g 24 -bf 2 \
  -vf "scale=1920:1080:flags=lanczos" \
  -movflags +faststart \
  -c:a aac -b:a 192k -ar 48000 \
  -metadata title="SHOT010 v012 REVIEW" \
  deliver/shot010_v012_review.mp4
```

**(b) Instagram / TikTok, 9:16 vertical** — 1080×1920, closed GOP, faststart, conservative for their re-encoder:

```bash
ffmpeg -y -framerate 30 -i png/shot010_%04d.png -i audio/mix.wav \
  -vf "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:flags=lanczos,format=yuv420p" \
  -c:v libx264 -profile:v high -level 4.0 \
  -crf 18 -preset slow -g 30 -keyint_min 30 -sc_threshold 0 -bf 0 \
  -x264-params "colorprim=bt709:transfer=bt709:colormatrix=bt709:range=tv" \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -movflags +faststart \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -af "loudnorm=I=-14:TP=-1.0:LRA=11" \
  -shortest deliver/shot010_v012_9x16.mp4
```

Notes: `-bf 0` and `-sc_threshold 0` give a strictly regular, closed GOP, which social re-encoders handle far better. `loudnorm` to **−14 LUFS / −1.0 dBTP** is the platform target for IG/TikTok/YouTube; ship it hot and they'll turn you down, ship it quiet and you sound weak.

**(c) YouTube** — upload the best master you can; YouTube re-encodes everything anyway, so give it headroom:

```bash
# 4K SDR master
ffmpeg -y -framerate 24 -i png4k/shot010_%04d.png -i audio/mix.wav \
  -c:v libx264 -profile:v high -level 5.1 -pix_fmt yuv420p \
  -crf 16 -preset slower -g 12 -bf 2 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -movflags +faststart \
  -c:a aac -b:a 384k -ar 48000 -ac 2 \
  -af "loudnorm=I=-14:TP=-1.0:LRA=11" \
  -shortest deliver/shot010_v012_yt4k.mp4
```

YouTube's own recommended *bitrate* targets, if you prefer CBR-ish over CRF: **1080p24/30 → 8 Mbps**, 1080p60 → 12, **2160p24/30 → 35–45 Mbps**, 2160p60 → 53–68. Their recommended GOP is **half the frame rate**, closed. CRF 16 will exceed all of those, which is what you want.

**(d) Broadcast / ProRes** — the mezzanine you hand an agency or a post house:

```bash
# ProRes 422 HQ (profile 3). 4444 = profile 4 (+alpha, yuva444p10le).
ffmpeg -y -framerate 25 -i png16/shot010_%04d.png -i audio/mix.wav \
  -vf "scale=1920:1080:flags=lanczos,format=yuv422p10le" \
  -c:v prores_ks -profile:v 3 -vendor apl0 -qscale:v 9 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a pcm_s24le -ar 48000 -ac 2 \
  -shortest deliver/shot010_v012_ProRes422HQ.mov
```

ProRes `-profile:v`: `0` Proxy, `1` LT, `2` 422, **`3` 422 HQ**, `4` 4444, `5` 4444 XQ. `-qscale:v` 9–13 (lower = better; 9 is the usual HQ target). `-vendor apl0` makes some Apple tools happier. DNxHR alternative: `-c:v dnxhd -profile:v dnxhr_hqx -pix_fmt yuv422p10le`.

**Extras worth knowing:**

```bash
# Grain at delivery resolution (see 3.8 resolution caveat)
-vf "...,noise=alls=6:allf=t+u"

# Proper linear-light rescale (better than plain scale for big downscales)
-vf "zscale=t=linear:npl=100,zscale=w=1920:h=1080:f=spline36,zscale=t=bt709,format=yuv420p"

# Re-mux an existing Blender MP4 for web streaming (no re-encode, seconds)
ffmpeg -i in.mp4 -c copy -movflags +faststart out.mp4

# Extract a still for the client deck
ffmpeg -i deliver/shot010.mp4 -ss 00:00:06.5 -frames:v 1 -q:v 1 still_frame163.jpg

# Verify what you actually shipped
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,profile,width,height,r_frame_rate,pix_fmt,color_range,color_space \
  -of default=nw=1 deliver/shot010.mp4
```

### 6.4 bpy — apply any preset

```python
# ── encode_presets.py ──────────────────────────────────────────────────────
import bpy

PRESETS = {
    "review": dict(
        res=(1920,1080), fps=24, container='MPEG4', codec='H264',
        crf='MEDIUM', speed='GOOD', gop=18, bframes=0,
        acodec='AAC', abitrate=192, stamp=True,
        path="//08_deliver/shot010_v012_review.mp4"),
    "social_9x16": dict(
        res=(1080,1920), fps=30, container='MPEG4', codec='H264',
        crf='HIGH', speed='BEST', gop=30, bframes=0,
        acodec='AAC', abitrate=192, stamp=False,
        path="//08_deliver/shot010_v012_9x16.mp4"),
    "social_1x1": dict(
        res=(1080,1080), fps=30, container='MPEG4', codec='H264',
        crf='HIGH', speed='BEST', gop=30, bframes=0,
        acodec='AAC', abitrate=192, stamp=False,
        path="//08_deliver/shot010_v012_1x1.mp4"),
    "youtube_4k": dict(
        res=(3840,2160), fps=24, container='MPEG4', codec='H264',
        crf='PERC_LOSSLESS', speed='BEST', gop=12, bframes=2,
        acodec='AAC', abitrate=384, stamp=False,
        path="//08_deliver/shot010_v012_yt4k.mp4"),
    "broadcast_dnxhd": dict(
        res=(1920,1080), fps=25, container='QUICKTIME', codec='DNXHD',
        crf='NONE', speed='BEST', gop=1, bframes=0, bitrate=145000,
        acodec='PCM', abitrate=0, stamp=False,
        path="//08_deliver/shot010_v012_DNxHD145.mov"),
    # image-sequence outputs
    "png16_for_ffmpeg": dict(image_seq='PNG16', res=(1920,1080), fps=24,
        path="//06_comp/png16/shot010_####"),
    "exr_master": dict(image_seq='EXR', res=(1920,1080), fps=24,
        path="//05_renders/shot010/exr/shot010_####"),
}

def apply_preset(name, scene=None):
    p = PRESETS[name]
    scene = scene or bpy.context.scene
    r = scene.render
    r.resolution_x, r.resolution_y = p["res"]
    r.resolution_percentage = 100
    r.fps, r.fps_base = p["fps"], 1.0
    r.filepath = p["path"]
    r.use_file_extension = True

    if p.get("image_seq") == 'EXR':
        im = r.image_settings
        im.file_format, im.color_mode = 'OPEN_EXR_MULTILAYER', 'RGBA'
        im.color_depth, im.exr_codec = '32', 'ZIP'
        im.color_management = 'OVERRIDE'
        im.view_settings.view_transform, im.view_settings.look = 'Standard', 'None'
        return
    if p.get("image_seq") == 'PNG16':
        im = r.image_settings
        im.file_format, im.color_mode = 'PNG', 'RGB'
        im.color_depth, im.compression = '16', 15
        im.color_management = 'FOLLOW_SCENE'
        r.dither_intensity = 1.0
        return

    r.image_settings.file_format = 'FFMPEG'
    f = r.ffmpeg
    f.format = p["container"]
    f.codec  = p["codec"]
    f.constant_rate_factor = p["crf"]
    f.ffmpeg_preset = p["speed"]          # BEST | GOOD | REALTIME
    f.gopsize = p["gop"]
    f.use_max_b_frames = bool(p["bframes"])
    if p["bframes"]:
        f.max_b_frames = p["bframes"]
    if p.get("bitrate"):
        f.video_bitrate = p["bitrate"]
        f.maxrate = int(p["bitrate"] * 1.2)
        f.buffersize = p["bitrate"] * 2
    f.audio_codec = p["acodec"]
    if p["abitrate"]:
        f.audio_bitrate = p["abitrate"]
    f.audio_mixrate = 48000
    f.audio_channels = 'STEREO'

    r.use_stamp = p["stamp"]
    if p["stamp"]:
        for a in ("use_stamp_frame", "use_stamp_filename", "use_stamp_date",
                  "use_stamp_render_time", "use_stamp_note", "use_stamp_labels"):
            setattr(r, a, True)
        r.stamp_note_text = "SHOT010 v012 — REVIEW ONLY — NOT FOR DELIVERY"
        r.stamp_font_size = 22
        r.stamp_background = (0.0, 0.0, 0.0, 0.55)

    print(f"[encode] '{name}' -> {p['res'][0]}x{p['res'][1]} @{p['fps']} "
          f"{p['codec']}/{p['crf']} -> {p['path']}")
    if p["container"] == 'MPEG4':
        print("[encode] NOTE: Blender writes no +faststart. Re-mux before "
              "sending a link:  ffmpeg -i in.mp4 -c copy -movflags +faststart out.mp4")

if __name__ == "__main__":
    apply_preset("review")
```

---

## 7. Deliverables and aspect variants

### 7.1 The three aspects, and the one render that feeds them

You will be asked for **16:9, 1:1 and 9:16**. Re-rendering three times triples your render bill for no reason. Plan the framing once.

**The math.** Crop a 9:16 out of a 16:9 frame using the full height:

| Master render | 16:9 out | 1:1 out (full height) | 9:16 out (full height) |
|---|---|---|---|
| 1920×1080 | 1920×1080 ✓ | 1080×1080 ✓ | **608×1080** ✗ (below 1080×1920) |
| **3840×2160 (4K)** | 3840×2160 ✓ | 2160×2160 ✓ | **1215×2160** ✓ (upscale 1.11× to 1080×1920 — fine) |
| 4096×2304 | ✓ | ✓ | 1296×2304 ✓ |

**So: master at 4K 16:9 (3840×2160) minimum if you owe a vertical.** From 1080p you cannot produce a legitimate 1080×1920 crop; the 608 px of usable width would need a 1.78× upscale.

**Better still — the open-matte master.** Render *taller* than 16:9 so the vertical crop has real headroom:

- Master: **2560×2560** (1:1) or **2304×3072**. Extract 16:9 by cropping the top/bottom, 9:16 by cropping the sides, 1:1 straight out.
- Cost: ~1.4–1.8× the pixels of a 4K 16:9 render. Cheaper than three renders.

**Framing rules to make it work:**

1. Set up the shot in the **16:9** camera, then add **two more cameras** (or one camera with a passepartout guide) and check the composition in all three before you render a single frame.
2. Keep the **bottle's vertical axis on or near the frame centre**, and never put critical product detail (label, cap) outside the central **56.25%** width band (`9/16` of the width). That band is your 9:16 safe zone.
3. Keep the splash **wide** (it can leave the 9:16 crop, that's fine — a splash cropping off frame reads as energy) but keep the **impact point** inside the vertical band.
4. Reserve **vertical headroom** above the bottle. 9:16 has 1.78× the relative height of 16:9; if the bottle fills the 16:9 frame top to bottom, the 9:16 crop will feel cramped and you'll have nowhere to put the endcard lockup.
5. **Backdrop must extend past every crop.** A gradient that stops just outside the 16:9 frame will show a hard edge in the taller crop.
6. **Enable the camera's Passepartout guides** and use `camera.data.show_safe_areas` (see below) to visualise the crops live.

### 7.2 Safe areas

| Area | Inset from each edge | What goes here |
|---|---|---|
| **Action safe** | ~3.5% (Blender default `0.035`) | Anything the viewer must see happen |
| **Title safe** | ~10% horizontal / 5% vertical (Blender default `0.1, 0.05`) | All text, logo, legal line, price, URL |
| **Social UI safe (9:16)** | **top 14%, bottom 20%, right 12%** | *Nothing.* TikTok/Reels UI (captions, username, buttons, progress bar) sits here |

That last row is the one people forget. On a 1080×1920 Reel, the bottom ~380 px is covered by the caption and CTA, and the right ~130 px by the action rail. Put your endcard lockup in the **middle third** or it will be behind a follow button.

```python
sc = bpy.context.scene
sc.safe_areas.action = (0.035, 0.035)
sc.safe_areas.title  = (0.100, 0.050)
sc.safe_areas.action_center = (0.150, 0.050)   # 4:3 centre-cut, legacy broadcast
sc.safe_areas.title_center  = (0.175, 0.050)
for cam in (o for o in sc.objects if o.type == 'CAMERA'):
    cam.data.show_safe_areas = True
    cam.data.show_safe_center = True
    cam.data.show_passepartout = True
    cam.data.passepartout_alpha = 0.9
```

### 7.3 Resolution and frame rate

| Deliverable | Resolution | FPS | Codec |
|---|---|---|---|
| Master (archive) | 3840×2160 or open-matte 2560×2560 | render fps | Multilayer EXR sequence |
| Broadcast/agency mezzanine | 1920×1080 | **25** (PAL) / 29.97 (NTSC) | ProRes 422 HQ |
| YouTube | 3840×2160 | 24 | H.264 CRF 16 |
| Web / site hero | 1920×1080 | 24 or 30 | H.264 CRF 20, faststart, often muted-autoplay so **must work silent** |
| Instagram Reels / TikTok | 1080×1920 | 30 | H.264 CRF 18, −14 LUFS |
| Instagram feed square | 1080×1080 | 30 | H.264 CRF 18 |
| Client review | 1920×1080 | 24 | H.264 CRF 22 + burn-in |
| Stills pack | 3840×2160 | — | 16-bit PNG + sRGB JPEG q95 |

**Frame rate choice:**
- **24 fps** — cinematic, the default for a premium product ad. Splash motion blur at a 180° shutter looks great.
- **25 fps** — mandatory for EU broadcast delivery. If broadcast is even *possible*, work at 25 from the start; retiming 24→25 later is a real cost.
- **30 fps** — smoother, reads slightly more "commercial/energetic", and is the native rate of most social feeds.
- **60 fps** — only as a *source* for slow-mo (§5.4). Delivering 60 fps doubles your render bill for a look most viewers read as "video, not film".

**Never mix.** Pick one master rate, render everything at it, retime in the edit.

---
