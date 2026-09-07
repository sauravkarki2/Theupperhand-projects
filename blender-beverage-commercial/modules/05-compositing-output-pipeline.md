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
