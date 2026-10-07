# Ellectrify Grounding Blanket – 20 s Blender film

Build follows `Ellectrify_Blanket_Blender_Spec.pdf`. Every scene is built by a script in `scripts/`, so any shot can be rebuilt.

Run a script headless:

    blender -b -P scripts/00_setup.py

or with the `bpy` module (`pip install bpy==5.2.1`, Python 3.13, matching the local Blender 5.2.1):

    python scripts/00_setup.py

## Status
| Step | Work | State |
|---|---|---|
| 1 | Version, device, folders, `00_setup.py`, test render | Done – awaiting sign-off |
| 2 | Assets + materials, material board | Not started |
| 3 | Six scenes, cameras, lights, 48-sample stills | Not started |
| 4 | Animation, cloth bakes, playblasts | Not started |
| 5 | One final-quality frame per shot, time budget | Not started |
| 6 | Full render (RTX 4080) | Not started |
| 7 | Sequencer edit, sound, MP4 | Not started |

## Assets still missing (section 3)
- `assets/logo/`: yellow-on-transparent logo (supplied file is a 264×75 dark wordmark on cream)
- `assets/ref/`: two more blanket product photos
- `assets/fonts/`: Playfair Display regular + italic
- `assets/audio/`: music bed + four sound effects
