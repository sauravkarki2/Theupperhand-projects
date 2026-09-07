# Live Session Runbook — recreating the beverage commercial

This is the script for when you open Blender on your machine and we build the
shot together. It is ordered so nothing gets redone.

---

## 0. Before we start — what I need from you

### 0.1 Connect Blender to me

I can drive Blender directly, but only through the **Higgsfield bridge plugin**.
Right now the bridge reports Blender as **not connected**. So:

1. Open Blender.
2. Make sure the Higgsfield bridge add-on is installed and enabled
   (`Edit > Preferences > Add-ons`), and that its connection is live.
3. Tell me, and I'll verify the host status from my side.

If the bridge won't connect, we have a clean fallback: I hand you
`scripts/build_beverage_ad.py`, you paste it into Blender's **Scripting**
workspace and run it, then paste the console output back to me. That works fine —
it's just a slower loop.

### 0.2 Tell me four things

| Question | Why it matters |
|---|---|
| **Blender version?** | 3.6 vs 4.x changes Principled BSDF socket names, the default view transform (Filmic → AgX, which will visibly desaturate the orange), and some geometry-nodes sockets. I need to know before we write a single material. |
| **GPU and VRAM?** | Sets the realistic sim resolution ceiling and render times. A splash at resolution 300+ with a transmissive bottle is genuinely heavy. |
| **Free disk space, and on which drive?** | Fluid caches are large. A 250-frame liquid bake at production resolution can run tens of GB. The cache must NOT live in OneDrive/Dropbox/iCloud — the sync client fights the solver. |
| **Your product, or the reference bottle?** | If you have a real client product, we model to that and the whole palette changes. If not, we build the citrus-soda bottle from the reference. |

---

## 1. The plan, in order

We follow production order. Each step **locks** something, and re-ordering costs
days because a change upstream invalidates everything downstream.

| # | Step | What it locks | Rough time |
|---|---|---|---|
| 1 | Scene scaffold + collections | naming, units, frame range | minutes |
| 2 | Product blockout (bottle, cap, liquid) | silhouette and scale | 20-40 min |
| 3 | Camera + framing | **the shot** | 15 min |
| 4 | Set: backdrop + reflection cards | the palette and the water's reflections | 15 min |
| 5 | Lighting rig | the read of the product | 30 min |
| 6 | Fluid domain + bottle as effector | the sim volume | 10 min |
| 7 | Curve + emitter + force rig | **the splash shape** | 30 min |
| 8 | **Low-res art-direction loop** | the choreography | *the bulk of the work* |
| 9 | Materials / look-dev | the finish | 45 min |
| 10 | High-res bake | the final sim | hours, unattended |
| 11 | Final render | the frames | hours, unattended |
| 12 | Comp + grade + encode | the deliverable | 45 min |

**Step 8 is where the shot is actually made.** Everything before it is setup;
everything after it is polish. Expect to re-bake at low resolution ten or twenty
times. That is not a sign anything is wrong — that is the job.

---

## 2. Why the camera gets locked at step 3

The sim only has to look right **from one angle**. If you art-direct a splash
before you've framed the shot, you will spend hours perfecting water that ends up
outside the frame or behind the bottle.

Lock the camera. Then shape the splash to that camera.

---

## 3. The low-res art-direction loop (step 8, expanded)

This is the loop we will spend most of our time in:

```
  set force strengths / emitter timing
        ↓
  bake Data at resolution 100      (~1-3 min)
        ↓
  scrub to the hero frame, look at it THROUGH THE CAMERA
        ↓
  is the silhouette right?  →  no  →  adjust, free the cache, re-bake
        ↓ yes
  lock it. move on.
```

**Rules for this loop:**

- Always judge through the camera, never from a viewport orbit.
- Change **one** thing per iteration. Two changes and you learn nothing.
- Do not raise resolution to "see it better". Higher resolution does not just
  add detail — it changes the simulation result. What you approve at 100 will
  not be what you get at 300, but the *gross shape* carries over, and gross
  shape is what you're directing here.
- Free the cache before every re-bake, or you'll be looking at stale frames and
  wondering why nothing changed.

---

## 4. The five things most likely to go wrong

Ranked by how often they bite people, with the fix.

### 4.1 The splash renders black or dark grey
**Cause:** not enough transmission bounces. Light has to survive water surface →
water interior → water surface → bottle wall → amber liquid → bottle wall → camera.
That's easily 8-12 transmission events. Cycles' default is marginal.
**Fix:** Render Properties → Light Paths → **Transmission: 24**, Total: 32.

### 4.2 The splash renders dull and lifeless even when lit
**Cause:** nothing for it to reflect. Water is ~95% specular — it shows you what's
around it, and if that's a dark void, the water is dark.
**Fix:** large white emissive planes off-camera (`REFLECT_CARD_L/R` in the build
script), set invisible to camera but visible to reflection and refraction.

### 4.3 Water passes straight through the bottle
**Cause:** thin collider + fast particles tunnelling, or the effector's surface
distance is too small.
**Fix:** enable **Fractional Obstacles** on the domain, raise the effector's
Surface Distance, and if it persists, give the bottle a simplified solid proxy
collider instead of colliding against the real modelled wall.

### 4.4 Everything changes when you re-bake at a different resolution
**Cause:** this is expected behaviour, not a bug. Resolution is a solver
parameter, not a display setting.
**Fix:** direct the shape at low res, accept that the fine detail will differ,
and budget one confirm bake at medium resolution before committing to final.

### 4.5 Your render doesn't match the tutorial's colours
**Cause:** the tutorial is Blender 3.6, whose default view transform is **Filmic**.
Blender 4.0+ defaults to **AgX**, which handles saturated colour very differently
and will visibly desaturate that orange backdrop.
**Fix:** know which you're on and compensate deliberately. This one catches
almost everyone following a 2023 tutorial on a current Blender.

---

## 5. Scope honesty

A few things worth saying plainly before we start:

- **The full shot is not a one-session build.** Steps 1-8 are very doable
  together in a working session. The high-res bake and the final render are
  hours of unattended machine time — we set them running, we don't watch them.
- **I have not run the build script against a live Blender.** It parses clean and
  every risky property write is guarded so a version mismatch produces a warning
  list rather than a crash. The first run is a smoke test; I expect to fix a
  handful of property names against your specific version, and that's normal.
- **I could not watch the video.** YouTube is blocked from this container. What
  I have is the reference frame you sent — which contained the entire Fluid
  Domain panel, legibly — plus the video's own published description of what it
  teaches, plus the domain knowledge. The settings in `reference/01-shot-breakdown.md`
  marked "Certain" were read directly off your screenshot. The ones marked
  "Inferred" are reasoned, and I've flagged every one. If you can get me the
  video's chapter list or description text, I'll tighten the inferences.

---

## 6. First five minutes

When you're ready:

1. Open Blender, connect the bridge, tell me your version + GPU.
2. I'll verify the connection and check the scene state.
3. I'll build the scaffold, product blockout, and camera.
4. We look at the framing together and you tell me what to change.
5. Then we go into the art-direction loop.
