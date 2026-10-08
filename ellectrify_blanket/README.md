# Ellectrify Grounding Blanket – Blender film

A 20-second, 1080×1920 product film, built entirely in Blender from Python scripts. The scripts follow
`Ellectrify_Blanket_Blender_Spec.pdf`, covering modelling, materials, cloth, lighting, cameras, the
Sequencer edit with type and sound, and the H.264/AAC export.

## Run order
Run these from this folder. Swap `python scripts/X.py` (with the `bpy` module) for
`blender -b blend/ellectrify_blanket.blend -P scripts/X.py` if you prefer.

```
python scripts/00_setup.py            # version + GPU check, folders, blend, render settings
python scripts/10_assets.py           # section 6 assets into LIB
python scripts/20_materials.py        # section 7 materials (pulse colour sampled from the logo if present)
python scripts/s1_form.py             # one script per shot (S1, S2 and S5 bake their cloth)
python scripts/s2_unfurl.py
python scripts/s3_exploded.py         # also exports label anchors for the edit
python scripts/s4_snap.py
python scripts/s5_bed.py
python scripts/s6_logo.py
python scripts/80_render.py           # PNG sequences into renders/s1..s6
python scripts/85_placeholder_audio.py   # only needed until real audio is supplied
python scripts/90_edit.py             # EDIT scene -> out/ellectrify_blanket_v01.mp4
```
If you rerun `10_assets.py`, rerun the shot scripts afterwards. The shots share the LIB meshes.

`python scripts/p3_stills.py <SCENE> <frame>...` renders sign-off stills into `previews/stills/`.

### Quality
- **Default (`final`)** follows section 5: 1080×1920, 192 samples, 16-bit PNG and a 12 mm cloth grid.
  It uses OptiX on the RTX 4080.
- **`ELLECTRIFY_QUALITY=preview`** gives 540×960 renders at 16 samples with a 24 mm cloth grid.
  The cloud preview was made this way on CPU only. The edit scales it up to 1080×1920.

## Assets
| Spec item | Status |
|---|---|
| Logo | **Missing.** S6 shows a `LOGO HERE` placeholder; the pulse uses the expected #F2EE8A |
| Product photos / cord image | **Missing.** `assets/ref/instagram_grounding_sheets_lines.jpg` is the sheets post (thread scale reference only) |
| Serif fonts | Playfair Display regular and italic, the spec's stand-in, from Google Fonts |
| Music + 4 SFX | **Placeholders** synthesised by `85_placeholder_audio.py`. Drop real files named `music_bed`, `rustle`, `tones`, `click`, `hum` into `assets/audio/` and they take over |

When the logo arrives, rerun `20_materials.py`, `s4_snap.py`, `s6_logo.py`, then `80_render.py S4_Snap S6_Logo` and `90_edit.py`.

## Deviations from the spec
- **S1:** replaced "Folded on the plinth" with **S1 Form** (client request). Thin threads of light streak in and
  the quilt weaves itself out of nothing: a see-through thread mesh behind a soft glowing front fills in solid.
  The cloth swirls in a circle while the camera orbits the other way. The effect is driven by the object properties
  `build_on`/`build` (shared cotton and silver materials) and `streak_t` (`MAT_thread_streak`). The light is
  soft white, with no sparks or arcs. `BLANKET_folded` and `PLINTH` stay in LIB but are no longer used.
- **Backdrop:** slate blue (`#4E5D6C` wall, `#3E4A56` floor, `#6A7A8A` plinth) instead of cream, at the client's request for more
  contrast. The bedroom wall and floor use the same colours. The S3 labels are off-white to suit it.
  Change the `BACKDROP_WALL`, `BACKDROP_FLOOR` and `PLINTH` values in `20_materials.py` to re-colour every set.
- **S3 lens:** 45 mm instead of 70 mm. At 1.5 m a 70 mm lens frames only 0.43 m across in 9:16, which is narrower than the 0.5 m swatch.
- **S4 fill:** dimmed to 0.3 so the metal reads grey and the soft pulse stays visible. The spec's global fill is 0.6.
- **Pulse radius:** grows linearly, as the spec states.
- **Extra materials:** `MAT_backdrop`, `MAT_backdrop_floor`, `MAT_plinth` and `MAT_sheet_white` (fitted sheet).
- **Leader lines:** the S3 labels are Sequencer text strips. Their 1 px leaders are a transparent PNG
  overlay that follows the orbiting camera; the Sequencer has no line strip.
- **Cloth caches:** they go to `blend/blendcache_ellectrify_blanket/` (Blender's disk cache), not `cache/s2`.
- **Disclaimer:** the optional S6 disclaimer line is included.
