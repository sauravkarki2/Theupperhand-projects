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
