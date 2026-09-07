# 00 — Source reconstruction: "lets make a beverage commercial in blender 2" (`wXVuEPuKO_0`)

Research date: 2026-09-07. Method: WebSearch only for most sources — `WebFetch` was blocked by
the egress proxy for youtube.com, blendernation.com / bazaar.blendernation.com, gumroad.com
subdomains, docs.blender.org, blenderartists.org, projects.blender.org, lesterbanks.com,
superhivemarket.com, flipfluids.com, noxinfluencer.com and blender.tekriss.com. Exactly one
third-party fetch succeeded (github.com). So most of what follows comes from search-result
snippets, and I flag below where a snippet is a *quote from a page* versus a *search engine's
synthesis of a page*. Synthesised summaries are treated as weaker evidence.

---

## Verified facts

**The two videos exist with the stated IDs and titles.** Both were returned as direct results
with matching titles.
- https://www.youtube.com/watch?v=wXVuEPuKO_0 — "lets make a beverage commercial in blender 2"
- https://www.youtube.com/watch?v=T2r6imiurWo — "lets make a beverage commercial in blender"

**Project files for part 2 are sold on Gumroad at `esmiles.gumroad.com/l/vedukp`, and there is a
matching Patreon post at `patreon.com/posts/89273851`.** Both URLs were surfaced by search
*from the video page itself* (the search index returned them as page content of
`youtube.com/watch?v=wXVuEPuKO_0`), which is the strongest description-text evidence I obtained.
- Product: "beverage commercial - blender project file", **$3**, **49.9 MB**.
- https://esmiles.gumroad.com/l/vedukp
- https://www.patreon.com/posts/89273851

**Project files for part 1 are a separate Gumroad product, `esmiles.gumroad.com/l/lenyz`.**
- Product: "lets make a beverage commercial in blender", **$3**, **82.8 MB**.
- https://esmiles.gumroad.com/l/lenyz

**`esmiles.gumroad.com` is the Gumroad storefront of "topchannel1on1".** The storefront page
title itself is "Subscribe to topchannel1on1 on Gumroad".
- https://esmiles.gumroad.com/

**TopChannel1on1 is a real, active Blender-tutorial creator with a consistent cross-platform
identity.** All of these resolved:
- YouTube: https://www.youtube.com/c/TopChannel1on1 — channel ID **`UClUvUh2AoIhJRezjduP3xcQ`**
  (https://www.youtube.com/channel/UClUvUh2AoIhJRezjduP3xcQ/videos); channel blurb per snippet:
  "Learning blender and having fun :D"
- Patreon: https://www.patreon.com/topchannel1on1
- Gumroad: https://esmiles.gumroad.com/
- Sketchfab: https://sketchfab.com/topchannel1on1
- Instagram: https://www.instagram.com/topchannel1on1/ (display name **"esmilevfx"**)
- Facebook: https://www.facebook.com/topchannel1on1/
- Discord: https://discord.com/invite/KbBw3ydArS (snippet reported ~829 members)
- Superhive / Blender Market store: https://superhivemarket.com/creators/topchannel1on1

**A BlenderNation Bazaar listing exists for this tutorial, dated 2023-10-24 — the same date as
the target video.** Its blurb, per snippet, is about "Blender's fluid simulation system" and
using "Manta flow" to make a beverage commercial. The Bazaar listing states Blender **3.6 LTS**
and lists it as free (tutorial) with a full project available.
- https://bazaar.blendernation.com/listing/making-a-beverage-commercial-in-blender/

**Blender's Mantaflow domain has a built-in "Guides" panel.** Documented settings include a
velocity **Source** (Effector / Domain), a **guiding size** (blur radius / "beta"), a **velocity
factor** multiplying every cell of a guiding grid the same size as the domain object, and a
**Bake Guides** step that "writes vertex velocities of effector objects to drive the simulation"
and is meant to be run *before* baking the fluid.
- https://docs.blender.org/manual/en/latest/physics/fluid/type/domain/guides.html
- https://docs.blender.org/manual/en/latest/physics/fluid/type/effector.html
- Release notes where Mantaflow landed: https://developer.blender.org/docs/release_notes/2.82/physics/

**Blender's stock Curve Guide force field does NOT correctly guide Mantaflow fluid along a
curve.** This is a filed bug: *"In fluid simulations, the Curve Guide force field does not work
along the curve (just a single direction)."* A snippet from the report reads: "Normal particles
can be guided in a curve, while liquid simulation particles are only sprayed in a random
direction… This might end up a Known Limitation/Issue since no one is actively maintaining
Mantaflow or its integration in blender atm." Reported against 3.2.0 Alpha.
- https://developer.blender.org/T97172
- Related: https://developer.blender.org/T74060 (smoke flow force field not working with Mantaflow gas)
- Related: https://developer.blender.org/T73422 (Mantaflow liquid inflow initial-velocity settings have no effect)
- Related regression: https://projects.blender.org/blender/blender/issues/97264 — "Regression:
  mantaflow Domain 'Guides' (velocity source) not working"

**The FLIP Fluids commercial addon has a purpose-built Curve Guide force field that does work.**
(This is the one page I fetched directly, so this is first-hand.) It "directs fluid along a
curve", takes a Blender Curve object as input, and exposes **Flow Strength** (positive pushes
fluid from first vertex toward last; negative reverses), **Spin Strength** (rotation around the
curve, right-hand rule), **Enable End Caps**, **Gravity Scale** (0.0 = local zero-g), and
**Max/Min Distance**. The docs warn that force is *acceleration*, so speed grows without bound
unless you keyframe strength back to zero. A straight-line curve plus spin strength makes a
vortex.
- https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Force-Field-Object-Settings
- https://flipfluids.com/weekly-development-notes-32-curve-guided-force-fields/

**TopChannel1on1 also sells a "Blender for Advertising Masterclass" on Superhive** which per
snippet covers "fluid product shots including credit card and beverage-style scenes with splashes
and motion".
- https://superhivemarket.com/products/blender-for-advertising-masterclass
- Also: "Mastering Geometry Nodes in Blender" on Patreon —
  https://www.patreon.com/topchannel1on1/shop/mastering-geometry-nodes-in-blender-593237

---

## Strong inferences

**1. The creator of both videos is TopChannel1on1 — real name given as Businge Ismail, alias
"esmiles". Confidence: high (~90%).**
Reasoning: (a) the description of `wXVuEPuKO_0` links to `esmiles.gumroad.com/l/vedukp`;
(b) `esmiles.gumroad.com` is titled as topchannel1on1's storefront; (c) a search synthesis
explicitly attributed the tutorial to "tophchannel1on1"; (d) the Instagram handle
`topchannel1on1` displays as "esmilevfx", tying "esmiles" to "topchannel1on1". The real name
"Businge Ismail" came only from a search-engine synthesis of the Gumroad/Patreon about pages,
never from a snippet I could see quoted — treat the *name* as lower confidence (~70%) than the
*channel attribution*.

**2. The BlenderNation Bazaar listing dated 2023-10-24 is the listing for this exact video.
Confidence: high (~85%).**
Reasoning: exact date match with the stated publish date of `wXVuEPuKO_0`, matching subject
(beverage commercial + Mantaflow), and matching Blender version (3.6 LTS).

**3. Part 1 (`T2r6imiurWo`) is the modelling / scene / look-dev half and part 2 is the
simulation half. Confidence: moderate (~60%).**
Reasoning: part 2's own blurb is entirely simulation-focused (fluid-follows-curve, forces,
geometry nodes), and its project file is *smaller* (49.9 MB) than part 1's (82.8 MB), which is
consistent with part 1 carrying the modelled/textured scene and part 2 carrying a sim setup
without baked caches. No source stated the split directly.

**4. The "make fluid follow a curve" step in part 2 is not the stock Curve Guide force field.
Confidence: moderate-high (~75%).**
Reasoning: the stock Curve Guide force field is documented-broken for Mantaflow liquid
(T97172), and Blender 3.6 predates any fix. That leaves the plausible options listed in the
technique section below. The blurb's pairing of "fluids follow a curve" *with* "how to use
forces" *and* "some basic geometry nodes" is most consistent with either (a) an inflow/emitter
animated along the curve via a Follow Path constraint while force-field empties shape the
splash, or (b) a geometry-nodes-generated mesh on the curve used as a Mantaflow effector/guide.
I could not determine which.

---

## Unknown / could not determine

- **The full verbatim description text of `wXVuEPuKO_0`.** I recovered only the two store links
  and the known blurb sentence. YouTube is proxy-blocked and no aggregator quoted the rest.
- **Chapter list / timestamps.** Not found anywhere. No aggregator, Pinterest pin, or blog
  reproduced them.
- **Video duration and view count** for either part. Not found.
- **The exact publish dates from a primary source.** Search syntheses variously claimed part 1
  = 2023-09-09 and part 2 = 2023-09-17, which *contradicts* the given 2023-10-24 for part 2 and
  the 2023-10-24 BlenderNation Bazaar date. Search-engine date guesses are unreliable here;
  treat the brief's 2023-10-24 as authoritative over these.
- **What the finished shot actually is** — brand, bottle vs can, camera move, splash shape. No
  source described the render.
- **Any community discussion of this specific tutorial.** I found **none**: no Reddit thread, no
  BlenderArtists thread, no X/Twitter post, no Discord recap referencing either video ID or
  title. This is a small-audience tutorial; the Pinterest pins
  (https://www.pinterest.com/pin/lets-make-a-beverage-commercial-in-blender-2--83738874315411176/
  and https://in.pinterest.com/pin/lets-make-a-beverage-commercial-in-blender-2-in-2024--689261918004948274/)
  are the only third-party references I could find, and they carry no substantive text.
- **Whether the Gumroad products are still live today.** Both `/l/vedukp` and `/l/lenyz` still
  appear in the search index with price and file size, and the `esmiles.gumroad.com` storefront
  resolves — but gumroad.com is proxy-blocked so I could not confirm current availability. Best
  answer: **almost certainly still purchasable at esmiles.gumroad.com for $3 each**, plus the
  Patreon post `patreon.com/posts/89273851` for patrons.
- **Which Mantaflow technique part 2 actually teaches.** See inference 4 — genuinely undetermined.
- **Whether "Businge Ismail" is the creator's real name.** Only search-synthesis evidence.

---

## Corroborating sources for the curve-guided-fluid technique

There is no single canonical way to make Mantaflow liquid follow a curve. Four distinct methods
are documented in the wild; here they are with what each is actually good for.

### A. Animate the inflow/emitter along the curve (Follow Path constraint) — the common one
The emitter object is parented to a Bézier curve with a **Follow Path** constraint (or an
Evaluate-Time keyframe), so the liquid is *emitted* along the path rather than *steered* along
it. Inertia carries the stream; the curve only decides where the source is each frame.
- **Blender MantaFlow Liquid particle system follow a path** — explicitly uses "curves and
  object constraint properties": https://www.youtube.com/watch?v=LC1SF7JvoMI
- **Blender Tutorial – Fluid Follow Path**: https://www.youtube.com/watch?v=-5S3o7HI3kA
- **Fluid on PATH: Blender Tutorial**: https://www.youtube.com/watch?v=6xsGdEvZGoQ
- Forum thread where this problem is posed directly, "Liquid inflow dosen't follow curve":
  https://blenderartists.org/t/liquid-inflow-dosent-follow-curve/535385
- Caveat that bites people: Mantaflow liquid **inflow initial-velocity settings have no effect**
  in some versions — https://developer.blender.org/T73422 — so you cannot always just dial in a
  velocity vector; you have to move the emitter.

**Why this is the one used for a bottle-wrapping splash:** it is the only stock-Blender method
that reliably gets liquid to *trace a specific silhouette* around a product. You draw the ribbon
you want around the bottle as a curve, run the emitter along it fast, and the mesh is the
resulting stream. Guides and force fields nudge; the emitter path *dictates*.

### B. Mantaflow Domain → Guides (guiding weight / size / velocity factor)
The Mantaflow-native answer. A guide object (a fluid modifier of type **Guide**, or an effector
whose vertex velocities are baked) draws a low-res velocity field over the whole domain; the
real sim is then nudged toward it. **Bake Guides** must run before the fluid bake, and guiding
objects **must actually be animated and have velocity** — a static guide does nothing.
- https://docs.blender.org/manual/en/latest/physics/fluid/type/domain/guides.html
- https://docs.blender.org/manual/en/latest/physics/fluid/type/effector.html
- **Effectors and Guides | Blender Mantaflow Part 6**: https://www.youtube.com/watch?v=KLwdEQvJ0-I
- **Blender Tutorial – Mantaflow Guides Smoke & Fluid Simulations**:
  https://www.youtube.com/watch?v=ldUwslQJ9NQ
- Known regression, guides velocity-source broken:
  https://projects.blender.org/blender/blender/issues/97264
- Parameter reference (blocked to me, but indexed):
  https://blender.tekriss.com/mantaflow-field-guide-what-every-parameter-actually-does/

**Reality check:** guides are a *bias*, not a rail. They shape large-scale flow direction, and
larger guiding size means larger vortices. They will not make a stream trace a tight ribbon
around a bottle. Plus the feature has an open regression report.

### C. Stock Curve Guide force field — documented as broken for Mantaflow
The Curve Guide force field forces *particles* along a curve object (veins, motor flow, etc.).
It does **not** work for Mantaflow liquid: the force resolves to a single direction and liquid
particles spray randomly.
- Bug: https://developer.blender.org/T97172
- Manual: https://docs.blender.org/manual/en/latest/physics/forces/force_fields/types/curve_guide.html
- General force fields index: https://docs.blender.org/manual/en/latest/physics/forces/force_fields/index.html

Do not build a shot on this in 3.6.

### D. FLIP Fluids addon Curve Guide force field — the one that actually rails fluid
Third-party (paid) addon. Purpose-built curve-guided force with Flow Strength along the curve,
Spin Strength around it, end caps, local gravity scale, and min/max distance. This is the
closest thing to "fluid on a rail" that exists for Blender.
- https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Force-Field-Object-Settings
- https://flipfluids.com/weekly-development-notes-32-curve-guided-force-fields/
- Live demo: **BSLIVE / Controlling Flip Fluid Flow Using Curve in Blender**:
  https://m.youtube.com/live/4GhhgAVefkM

### E. Don't simulate at all — geometry nodes "liquid on a curve"
For product ads the ribbon of liquid wrapping a bottle is very often **not simulated**. A
geometry-nodes setup sweeps a profile along the curve with noise/taper, giving frame-accurate
art direction, instant iteration, and no bake.
- **Max Edge – Liquid on Curve** (free, geometry nodes, Blender 3.1+):
  https://maxedge.gumroad.com/l/liquidcurves — write-up:
  https://80.lv/articles/a-free-blender-add-on-for-creating-fake-liquids
- Max Edge water splash setup: https://maxedge.gumroad.com/l/watersplash
- **Fake Liquid addon** (Superhive): https://superhivemarket.com/products/fakeliquid-addon
- **Fake Liquid Simulation with Geometry Nodes (3.6 simulation nodes)**:
  https://www.nodegroup.xyz/blog/fake-liquids-with-simulation-nodes-in-blender-3-6
- **[Blender 3.1] Fake Liquid With Geometry Nodes**: https://www.youtube.com/watch?v=-mAmjkauErU
- **Fake Crown Splash – Geometry Nodes 3.6+**: https://www.youtube.com/watch?v=E7nuWsjTOh8
- Free project file: https://chong3d.gumroad.com/l/vbdex

### F. Hybrid: Mantaflow (APIC) + geometry nodes for the path
The best-documented "fluid follows a path" tutorial on BlenderArtists uses geometry nodes to
*build the path geometry* and Mantaflow APIC for the water itself.
- https://blenderartists.org/t/blender-fluid-follows-a-path-mantaflow-simulation-apic-simple-geometry-nodes-4k-tutorial/1286452
- Companion "Dark Fluid" preview:
  https://blenderartists.org/t/blender-dark-fluid-liquid-simulation-in-mantaflow-apic-simple-geometry-nodes-4k-preview/1286051
  / https://www.youtube.com/watch?v=g7VWGbZhdZI
- Write-up: https://lesterbanks.com/2023/07/how-to-simulate-water-along-a-path-with-blender/
- **Liquid Follows Curve – Blender Mantaflow** by Aria Faith Jones:
  https://www.youtube.com/watch?v=hFr3y2S8nTw (blend file:
  https://ariafaithjones.gumroad.com/l/darkfluid)
- **MantaFlow Liquids follow curve — force field method**:
  https://www.youtube.com/watch?v=2s6cJKuSeIo

**Bottom line for a bottle-wrapping splash:** the community reaches for **A** (emitter on a
Follow Path constraint, shaped by force-field empties) when it must be a real sim, and **E**
(geometry nodes ribbon) when it must be art-directable and hit a mark. **B** is a soft bias only,
**C** is broken, **D** requires a paid addon. Given the part-2 blurb names curve-following,
forces, *and* geometry nodes together, the tutorial most likely combines A and E.

---

## Related tutorials and artists (corroboration for the same pipeline)

**Same creator, adjacent projects**
- `esmiles.gumroad.com/l/aaoyco` — "Make company commercial animations in blender" project file
  (April 2024); video: https://www.youtube.com/watch?v=B25miVy5_08
- Blender for Advertising Masterclass:
  https://superhivemarket.com/products/blender-for-advertising-masterclass
- Patreon post index: https://www.patreon.com/topchannel1on1/posts
- Related Patreon project file: https://www.patreon.com/posts/84014848 ("straw berry commercial
  like animation - project file")

**Other beverage / product-splash tutorials**
- **Smeaf — Blender 3.0: Masterclass in Product Animation** (Skillshare), builds a liquid
  product ad end to end:
  https://www.skillshare.com/en/classes/blender-3-0-masterclass-in-product-animation/1979672850
- **Polygon Runway — Blender Glass and Liquid Animation Tutorial**:
  https://www.youtube.com/watch?v=6X0NPEFZa_U
- **CG Cookie — Let's Make Coffee: Mantaflow fluid sim for beginners** (best plain-English
  explanation of inflow-as-faucet):
  https://blog.cgcookie.com/posts/let-s-make-coffee-blender-fluid-sim-mantaflow-tutorial-for-beginners/
- **KennyPhases — Product Can Liquid-Splash Effect (Fluid)**:
  https://kennyphases.gumroad.com/l/ldexo ; geometry-nodes fluid video:
  https://www.youtube.com/watch?v=ce848ZR5IrY
- **Ryan King Art — drink scene**: https://ryankingart.gumroad.com/l/drink
- **Fattu Tutorials — Coke commercial ads**: https://fattututorials.gumroad.com/l/cokecommercialads
  (video https://www.youtube.com/watch?v=SjdMx6LfanA)
- **MadLab VFX — Coke ad splash FX**: https://madlabvfx.gumroad.com/l/coke_ad_splashs_fx
- **NG3D Studio — Packshot tutorial in Blender**:
  https://ng3dstudio.gumroad.com/l/PackshotTutorialinBlender
- **Crossmind Studio — Blender Special Projects / Motion and Simulations**:
  https://crossmindstudio.gumroad.com/l/motionandsimulations
- **Sweaty Grease — Kentucky Bourbon**: https://sweatygrease.gumroad.com/l/kentuckybourbon
- **Product water splash simulation in Blender**: https://www.youtube.com/watch?v=DbewtqTrzgo
- **GameDev.tv — Blender Product Commercials** (paid course):
  https://gamedev.tv/courses/blender-product-commercials
- **Aria Faith Jones** — the reference artist for Mantaflow art-direction on ArtStation:
  https://www.artstation.com/artwork/3dbPWm , https://www.artstation.com/artwork/48aQ1Y

**Other videos with confusingly similar titles — do NOT mistake these for the target**
- https://www.youtube.com/watch?v=ZfYVRFOTwoc — "making a beverage commercial in blender"
- https://www.youtube.com/watch?v=9HDKMsyjZNo — "I Made a Beverage Commercial in Blender"
- https://www.youtube.com/watch?v=W7NL38KPrPE / https://www.youtube.com/watch?v=k1BQcVtl7hY —
  "Making an EXPENSIVE Beverage Commercial using Blender!" (Liquid Death spec ad)
- https://www.youtube.com/watch?v=jqzHfAVWfxQ — "How to animate an EPIC beverage commercial
  (Blender Beginner Tutorial) – Part 1 – Modelling"

---

## Search log

| # | Query | Productive? |
|---|---|---|
| 1 | `"lets make a beverage commercial in blender"` | Yes — found both video IDs + BlenderNation Bazaar listing |
| 2 | `wXVuEPuKO_0 youtube` | No — raw video ID is not indexed |
| 3 | `bazaar.blendernation.com "Making a beverage commercial in blender" mantaflow` | Yes — 2023-10-24 date, Mantaflow blurb |
| 4 | WebFetch bazaar.blendernation.com listing | Blocked (EGRESS_BLOCKED) |
| 5 | `"how to make fluids follow a curve" blender "forces" "geometry nodes" tutorial` | Yes — surfaced BlenderArtists APIC thread, maxedge/warcat3d curve tools |
| 6 | `blendernation "beverage commercial" blender mantaflow October 2023 tutorial part 2` | Partly — confirmed Bazaar date, lots of general Mantaflow |
| 7 | `"beverage commercial in blender" youtube channel tutorial "3.6" fluid curve patreon gumroad project files` | **Best hit** — named "tophchannel1on1", confirmed 3.6 LTS, Patreon+Gumroad |
| 8 | `pinterest "lets make a beverage commercial in blender 2"` | Weak — pins exist, no text |
| 9 | `"tophchannel1on1"` | Yes — full cross-platform identity, channel/Patreon/Gumroad/Discord |
| 10 | `tophchannel1on1 blender youtube gumroad patreon` | Yes — esmiles.gumroad.com = topchannel1on1; "Businge Ismail / esmiles" |
| 11 | `esmiles.gumroad.com beverage commercial blender project files` | Yes — `/l/vedukp` $3 49.9MB, `/l/lenyz` $3 82.8MB |
| 12 | WebFetch esmiles.gumroad.com | Blocked |
| 13 | `"esmiles.gumroad.com/l/vedukp" OR "/l/lenyz" OR "/l/aaoyco"` | Yes — mapped products to videos; aaoyco = company commercials |
| 14 | `TopChannel1on1 "beverage commercial" blender 2 fluid follow curve forces geometry nodes` | Partly — surfaced Blender manual Curve Guide page |
| 15 | `patreon topchannel1on1 "beverage commercial" blender project files` | Yes — Advertising Masterclass, Patreon post index |
| 16 | `"lets make a beverage commercial in blender 2" description "project files" patreon gumroad timestamps` | **Yes** — extracted `patreon.com/posts/89273851` + `/l/vedukp` from the video page |
| 17 | WebFetch youtube.com/watch?v=wXVuEPuKO_0 | Blocked |
| 18 | `patreon.com/posts/89273851 beverage commercial blender` | Weak — confirmed the post is the part-2 files |
| 19 | `"lets make a beverage commercial in blender" T2r6imiurWo … part 1 what it covers` | No — part 1 content not documented anywhere |
| 20 | `TopChannel1on1 beverage commercial blender 2 video length minutes 2023` | No duration; gave (unreliable) 2023-09-09 date for part 1 |
| 21 | `"TopChannel1on1" youtube "beverage commercial"` | Partly — got channel ID UClUvUh2AoIhJRezjduP3xcQ |
| 22 | WebFetch superhivemarket creator page | Blocked |
| 23 | WebFetch noxinfluencer channel page | Blocked |
| 24 | `"UClUvUh2AoIhJRezjduP3xcQ" beverage commercial blender` | No — channel ID not indexed as text |
| 25 | `Blender Mantaflow make liquid follow a curve inflow follow path constraint tutorial` | Yes — Follow Path method sources |
| 26 | `Blender fluid simulation "guides" guiding weight mantaflow domain guide fluid velocity` | Yes — Guides manual + regression #97264 |
| 27 | WebFetch docs.blender.org guides + curve_guide | Blocked (both) |
| 28 | `Blender manual Curve Guide force field "does not affect" fluid mantaflow particles only` | **Yes** — bug T97172, the key technical finding |
| 29 | `Blender mantaflow liquid inflow animated along curve "follow path" splash wrapping bottle product ad` | Yes — BlenderArtists "Liquid inflow dosen't follow curve", T73422 |
| 30 | WebFetch blenderartists thread | Blocked |
| 31 | `blenderartists "Fluid Follows a Path" Mantaflow APIC geometry nodes tutorial method explanation` | Yes — APIC + geo-nodes hybrid method |
| 32 | WebFetch lesterbanks water-along-a-path | Blocked |
| 33 | `reddit r/blender make fluid simulation follow curve path mantaflow how` | No — no Reddit results surfaced at all |
| 34 | `"Liquid Follows Curve" Blender Mantaflow tutorial … force field` | Yes — Aria Faith Jones + force-field-method video 2s6cJKuSeIo |
| 35 | `Blender mantaflow "bake guides" effector velocity source moving object guide fluid direction tutorial` | Yes — Bake Guides semantics, "guides must be animated" |
| 36 | WebFetch blender.tekriss.com Mantaflow field guide | Blocked |
| 37 | `blender force field empty animated follow path constraint drag liquid mantaflow splash around bottle` | Yes — pointed to FLIP Fluids force field wiki |
| 38 | **WebFetch github.com/rlguy/Blender-FLIP-Fluids wiki** | **Yes — the only successful fetch**; full Curve Guide force spec |
| 39 | `reddit blender "beverage commercial" tutorial topchannel1on1 discussion` | No Reddit; did surface Advertising Masterclass blurb |
| 40 | WebFetch projects.blender.org issue 97172 | Blocked |
| 41 | `best blender product splash liquid commercial tutorial channels …` | Yes — Smeaf, Polygon Runway, KennyPhases, etc. |
| 42 | `"T97172" … "just a single direction"` | Yes — confirmed bug title + FLIP Fluids dev-notes page |
| 43 | `"lets make a beverage commercial in blender" 2023 … "part 1" description blender 3.6` | No — part 1/part 2 split still undetermined |
| 44 | WebFetch flipfluids.com weekly dev notes 32 | Blocked |
| 45 | `blender mantaflow liquid follow curve "doesn't work" force field workaround community advice` | Partly — reinforced that this is a known pain point |
| 46 | `"Aria Faith Jones" liquid follows curve blender mantaflow how method blend file` | Yes — ariafaithjones.gumroad.com/l/darkfluid |
| 47 | `geometry nodes fake liquid wrap around bottle curve blender product ad splash no simulation` | **Yes** — Max Edge "Liquid on Curve", fake-liquid ecosystem |
| 48 | `"Liquid on Curve" Max Edge blender addon geometry nodes fake liquid free 80.lv` | Yes — free, 3.1+, ~3,800 downloads, 97% 5-star |
| 49 | `topchannel1on1 "Blender for Advertising Masterclass" superhive blender market beverage splash` | Yes — course covers beverage splash shots |
| 50 | `"beverage commercial" gumroad esmiles vedukp … contents` | No — file contents not indexed |
| 51 | `"beverage commercial in blender 2" TopChannel1on1 views comments 2023 … reaction` | No — search drifted to kitchen appliances |
