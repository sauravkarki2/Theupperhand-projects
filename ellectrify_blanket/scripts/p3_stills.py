"""Preview stills for sign-off: python scripts/p3_stills.py <SCENE> <frame> [<frame> ...]
(or blender -b blend/... -P scripts/p3_stills.py -- <SCENE> <frames>). Writes previews/stills/."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from _common import open_blend, render_still, PREVIEWS  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
open_blend()
sc = bpy.data.scenes[args[0]]
out = os.path.join(PREVIEWS, "stills")
os.makedirs(out, exist_ok=True)
for f in map(int, args[1:]):
    render_still(sc, os.path.join(out, f"{sc.name}_f{f:03d}.png"), frame=f)
