# Ellectrify Grounding Blanket – Blender build

Built to `Ellectrify_Blanket_Blender_Spec.pdf` (20 s, 1080×1920, Cycles). Every step is a
script under `scripts/`, so you can rebuild it. Run the scripts in order from this folder:

```
blender -b -P scripts/00_setup.py                                   # step 1: creates blend/
blender -b blend/ellectrify_blanket.blend -P scripts/10_assets.py
blender -b blend/ellectrify_blanket.blend -P scripts/20_materials.py
blender -b blend/ellectrify_blanket.blend -P scripts/p2_material_board.py   # step 2 sign-off
```

(With the `bpy` pip module you can also run `python scripts/<name>.py`.)

## Status
| Step | State |
|---|---|
| 1 Setup | Done. Built on Blender 5.2.2 LTS on CPU (no GPU in the cloud container). On the RTX 4080 the scripts switch to OptiX automatically. `previews/step1_report.txt` |
| 2 Assets + materials | Built. **Waiting for sign-off:** `previews/step2_material_board.png` |
| 3–7 | Not started (the spec says to stop at each sign-off) |

## Missing assets (section 3)
None of these are in `assets/` yet: the logo, the reference photos, the serif fonts, and the audio.
The pulse colour uses the spec's expected `#F2EE8A` until `20_materials.py` can sample it from the logo.

## Notes on adaptations
- `MAT_stone` (pale stone floor) and `MAT_sheet_white` (fitted sheet on the mattress) are additions. The bedroom needs them, but section 7 doesn't list them.
- The pulse is driven by object custom properties `pulse_R`, `pulse_strength` and `snap_pos`, read by Attribute nodes in `MAT_silver_layer`.
