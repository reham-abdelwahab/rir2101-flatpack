# Lamina — chair

| | |
|---|---|
| Tool | Lamina (PyPI name `lamina3d`), "early alpha" (classifier Development Status 3 - Alpha) |
| Version | 0.3.0 (pyproject.toml) |
| Commit | bed1c9a ("Landing-page media recorded from main") |
| Licence | AGPL-3.0-or-later |
| Source | `/tmp/claude-0/-home-claude/a08d6e43-68ac-59f1-b38b-18f3d9cee4ba/scratchpad/tools/lamina` (pinned clone), installed editable in its own venv (uv, CPython 3.13, trimesh 5.2.0, shapely 2.2.0) |
| Interface | Python core API only: `core.plan.build()` + `core.export.export(fmts=("svg",), labels=True, border=True, key=True)`; no web server |
| Scripts | `research/lamina/run_lamina.py` (runs Lamina, keeps raw output) → `adapt.py` (normalise) → `preview.py` (PNG) → `make_settings.py` (this file) |
| Manual steps | 0 (everything scripted; no GUI, no hand edits of any output) |

## Fold & Glue (`folded` mode)

Input: `research/models/chair_fold.stl`. The STL is used, not the OBJ: trimesh fan-triangulates the OBJ's non-convex
n-gons wrongly (loaded area 12123 mm² vs 10980 / 26560 / 42746.8), while the pre-triangulated STL loads with exactly the target area.

Settings changed from Lamina's defaults (everything else default: facet 15, strategy auto, tab_h 10, tab_angle 30, margins 5, gap 3, labels on, split on, autofix add):

| parameter | default | used | why |
|---|---|---|---|
| joint | laced | **tab** | brief: glue tab |
| thickness | 1.5 | **0.5** | 0.5 mm Bristol |
| material | "" | **card** | stock name; Lamina's fold check (`FOLDS["card"] = 1.5 mm`, core/modes/folded.py:24) then applies — 0.5 mm passes |
| sheet | [600, 400] | **[297, 420]** | A3 |
| scale | 1.0 | 1.0 (1:10) / **0.5** (1:20) | 1:20 = half size |

Facet 15 (default) does not simplify these meshes: the target face count it gives (≥ 12 · area/(0.433·15²)) exceeds the STL's 14-21 triangles, so every triangle is kept (core/modes/folded.py:40-44, 58-60).

### How Lamina encodes fold direction and the printed side (from source)

* Faces are re-wound first: `core/plan.py:376-377` — `if not mesh.is_winding_consistent: trimesh.repair.fix_normals(mesh)` (and again `core/modes/folded.py:69` inside `simplify`). For an open, non-watertight surface trimesh's `fix_winding` makes the winding consistent by BFS from an arbitrary face per connected component and does **not** orient it outward (`fix_inversion` acts only on watertight meshes). Result here: Lamina's face normals disagree with the file's normals (= our printed side) on **9 of 21** triangles. For chair/sofa the side panels are split by a non-manifold edge (the seat's side edge is shared by 3 triangles), so the two halves of one planar side panel end up wound opposite ways.
* Every face is unfolded in its own frame with z = the (re-wound) face normal: `core/unfold.py:29` ("origin = vertex 0, z = outward normal"), `core/unfold.py:33` (`v = np.cross(N, u)`), laid flat by proper rotations only (`core/unfold.py:44`, `R = [[c, -s], [s, c]]`, no reflection). The net is therefore drawn **seen from the normal side**; the SVG export flips y only to keep it y-up on screen (`core/export.py:257`, `height - y`) and nesting only rotates (`core/nest.py:49`) — no mirroring anywhere. The printed side = the side the viewer sees = Lamina's normal side; Lamina has no separate "print" layer.
* Direction: `core/modes/folded.py:138` `convex = mesh.face_adjacency_convex`; `core/modes/folded.py:139` `styles = ("solid", "dashed")  # mountain, valley`; `core/modes/folded.py:150` a fold is `styles[0] if convex[k] else styles[1]`; tab hinges `core/modes/folded.py:488` (`"solid" if convex else "dashed"`). Legend `core/modes/folded.py:93` and export header `core/export.py:8`: "solid = mountain, dashed = valley". SVG: dashed = `stroke-dasharray="1.5,1"` (`core/export.py:170`, `:284`).
* trimesh's "convex" is `face_adjacency_projections < tol.merge` (1e-8): a coplanar pair (dihedral 0°, a triangulation diagonal) counts as convex and is drawn as a **solid (mountain) score line**.
* Adapter rule: solid → `data-fold="mountain"`, dashed → `data-fold="valley"`; no mirroring (Lamina already shows the normal side). Note this is mountain/valley relative to **Lamina's re-wound normals**, which for chair and sofa differ from the target's printed side on part of the surface (see above).

### Results

| | 1:10 | 1:20 |
|---|---|---|
| sheets (A3) | 1 | 1 |
| parts (separate cut outlines) | 1 | 1 |
| net panel area, no tabs (mm²) | 10980.00 | 2745.00 |
| target mesh area (mm²) | 10980 | 2745 |
| panel / mesh area | 1.000000 | 1.000000 |
| cut outline area incl. tabs (mm²) | 11620.5 | 3001.1 |
| score lines: mountain / valley / unmarked | 19 / 3 / 0 | 19 / 3 / 0 |
| … real folds (90°) M / V | 3 / 3 | 3 / 3 |
| … 0° triangulation diagonals M / V | 14 / 0 | 14 / 0 |
| … tab hinges M / V | 2 / 0 | 2 / 0 |
| Lamina refold error (mm) | 2.3e-14 | 1.1e-14 |
| wall-clock build+export (s) | 0.068 | 0.064 |

Score lines per direction come from Lamina's SVG/plan; the split into real folds / 0° diagonals / tab hinges comes from `fold_meta.json` (read-only instrumentation of `Folded.build`, see run_lamina.py), checked line-by-line against plan.json (style and length agree to < 1e-4 mm). `refold_error` is Lamina's own test helper (`core/unfold.py:170`).

Lamina's own messages (verbatim, as its CLI `core.plan.main` prints them):

1:10

```
folded: 1 slices, 1 parts, 1 sheet(s) (9% used), 0 errors, 0 warnings
  note  open surface (not a closed solid): panelled as it is — its boundary edges stay open and carry no joints, and a hole in the surface stays a hole
  note  unfolded 21 triangles into 1 panel(s), 2 seams
```

1:20

```
folded: 1 slices, 1 parts, 1 sheet(s) (2% used), 0 errors, 1 warnings
  note  open surface (not a closed solid): panelled as it is — its boundary edges stay open and carry no joints, and a hole in the surface stays a hole
  note  unfolded 21 triangles into 1 panel(s), 2 seams
  warn  P-1: 2 joint(s) made smaller than asked to fit their triangle — fine for paper, check strength for metal
```

## Waffle (`interlocked` mode)

Input: `research/models/chair_waffle_solid.stl` (watertight; Lamina reports no repair).

| parameter | default | used | why |
|---|---|---|---|
| distribution | count (nx 5, ny 4) | **distance** | Lamina has no per-direction spacing; "distance" = one slice every `spacing` |
| spacing | 30 | **10** | our 10 mm |
| thickness | 1.5 | 1.5 (stated) | 1.5 mm board |
| kerf / compensate | 0 / off | 0 / off (stated) | kerf 0 (`core/plan.py:580`: kerf applied only when compensate is on) |
| slot_offset | 0 | 0 (stated) | slot width = board + offset (`core/notch.py:82`) |
| up | z | z (stated) | families X-n = planes x = const, Y-n = planes y = const, slots half-lap (notch_ratio 0.5) |
| sheet | [600, 400] | **[297, 420]** | A3 |
| scale | 1.0 | 1.0 / **0.5** | 1:20 = solid × 0.5 |

**Spacing vs count.** In distance mode Lamina converts the spacing to a count, `n = max(1, int(L // spacing))` per direction (`core/modes/interlocked.py:45-46`), then places the n slices at bin centres `-L/2 + L(i+0.5)/n` (`core/modes/interlocked.py:55`, `core/modes/__init__.py:308-312`). The real pitch is L/n ≥ 10 mm, the end ribs half a pitch in from the faces. Where L is a multiple of 10 the pitch is exactly 10 with ribs at 5, 15, 25 …; otherwise it is wider (offsets below).

Positions come from Lamina's internal model before nesting: each slice's 4×4 frame `M` (local → world) and each piece's local outline (`kerfed`, kerf 0) in plan.json; the adapter shifts Lamina's centred world frame (`core/plan.py:392`) back by the scaled solid's bbox centre.

### Results

| | 1:10 | 1:20 |
|---|---|---|
| sheets (A3) | 1 | 1 |
| parts | 8 | 4 |
| ribs in x-planes (X family) | 4 | 2 |
| ribs in y-planes (Y family) | 4 | 2 |
| x offsets (mm) | 5.625, 16.875, 28.125, 39.375 | 5.625, 16.875 |
| y offsets (mm) | 5.625, 16.875, 28.125, 39.375 | 5.625, 16.875 |
| slot widths in export (mm: count) | 1.500: 32, 4.875: 10, 0.625: 8 | 2.750: 6, 3.500: 2 |
| assembled rib bbox incl. board (mm) | 45 × 45 × 85 | 22.5 × 22.5 × 22.75 |
| … z range (mm) | 0 – 85 | 19.75 – 42.5 |
| solid bbox (mm) | 45 × 45 × 85 | 22.5 × 22.5 × 42.5 |
| errors / warnings (Lamina counts) | 0 / 8 | 0 / 8 |
| wall-clock build+export (s) | 0.226 | 0.07 |

Slot width: measured on Lamina's exported SVG sheets (U-turn edges of every cut ring; the histogram's other entries are notch-like outline features, not slots): see table. Lamina draws slots as `rect_along(..., b.thickness + slot_offset)` = 1.5 mm.

Lamina's own messages (verbatim):

1:10

```
interlocked: 8 slices, 8 parts, 1 sheet(s) (5% used), 0 errors, 8 warnings
  warn  X-1: part has 2 thin spot(s) — a tip or sliver thinner than the material can take for 41 mm, which would break off: trim thin spots (the part ends blunt there), move the slice (offset), or thicken / round the model
  warn  X-1: part has a bridge thinner than 2.0 mm (splits into 2 pieces when eroded) — fragile: thicken / round the model, move the slice (offset), or accept and handle with care
  warn  X-2: part has 1 thin spot(s) — a tip or sliver thinner than the material can take for 23 mm, which would break off: trim thin spots (the part ends blunt there), move the slice (offset), or thicken / round the model
  warn  X-3: part has 1 thin spot(s) — a tip or sliver thinner than the material can take for 23 mm, which would break off: trim thin spots (the part ends blunt there), move the slice (offset), or thicken / round the model
  warn  X-4: part has 2 thin spot(s) — a tip or sliver thinner than the material can take for 41 mm, which would break off: trim thin spots (the part ends blunt there), move the slice (offset), or thicken / round the model
  warn  X-4: part has a bridge thinner than 2.0 mm (splits into 2 pieces when eroded) — fragile: thicken / round the model, move the slice (offset), or accept and handle with care
  warn  Y-1: part has 2 thin spot(s) — a tip or sliver thinner than the material can take for 23 mm, which would break off: trim thin spots (the part ends blunt there), move the slice (offset), or thicken / round the model
  warn  Y-4: part has 2 thin spot(s) — a tip or sliver thinner than the material can take for 40 mm, which would break off: trim thin spots (the part ends blunt there), move the slice (offset), or thicken / round the model
```

1:20

```
interlocked: 4 slices, 4 parts, 1 sheet(s) (0% used), 0 errors, 8 warnings
  note  model coverage 72%: parts of the model have no geometry — more slices (count / spacing), a different axis, or round/thicken thin features
  warn  X-1: part has 1 thin spot(s) — a tip or sliver thinner than the material can take for 19 mm, which would break off: trim thin spots (the part ends blunt there), move the slice (offset), or thicken / round the model
  warn  X-1: part has a bridge thinner than 2.0 mm (splits into 3 pieces when eroded) — fragile: thicken / round the model, move the slice (offset), or accept and handle with care
  warn  X-2: part has 1 thin spot(s) — a tip or sliver thinner than the material can take for 19 mm, which would break off: trim thin spots (the part ends blunt there), move the slice (offset), or thicken / round the model
  warn  X-2: part has a bridge thinner than 2.0 mm (splits into 3 pieces when eroded) — fragile: thicken / round the model, move the slice (offset), or accept and handle with care
  warn  Y-1: part has 1 thin spot(s) — a tip or sliver thinner than the material can take for 22 mm, which would break off: trim thin spots (the part ends blunt there), move the slice (offset), or thicken / round the model
  warn  Y-1: part has a bridge thinner than 2.0 mm (splits into 3 pieces when eroded) — fragile: thicken / round the model, move the slice (offset), or accept and handle with care
  warn  Y-2: part has 1 thin spot(s) — a tip or sliver thinner than the material can take for 22 mm, which would break off: trim thin spots (the part ends blunt there), move the slice (offset), or thicken / round the model
  warn  Y-2: part has a bridge thinner than 2.0 mm (splits into 3 pieces when eroded) — fragile: thicken / round the model, move the slice (offset), or accept and handle with care
```

## Observations (from the outputs above, not Lamina messages)

- 1:20 waffle: the ribs (x, y = 5.625, 16.875 mm) miss the 3.5 × 3.5 mm legs (at 0–3.5 and 19–22.5 mm), so no rib reaches below z = 19.75 mm: the assembled ribs span 22.5 × 22.5 × 22.75 mm against a 22.5 × 22.5 × 42.5 mm solid. Lamina reports this only as "model coverage 72%" (a note, not an error). At 1:10 the 7 mm legs are hit by the end ribs (5.625 mm), and the bbox matches 45 × 45 × 85.
- Fold: one net (P-1) holds all 5 target panels; the two seams Lamina leaves are the front-panel/side-panel edges. The seat/side join is a non-manifold edge (3 triangles), which Lamina cannot treat as a fold or seam: it stays a cut edge with no tab.

## Files

* `raw/fold_<s>/`, `raw/waffle_<s>/`: Lamina's SVG sheet(s) (layers OUTER blue / INNER green / SCORE yellow / LABEL red, sheet border and a 10 cm calibration bar on the LABEL/OUTER layers), `assembly-key.txt`, `plan.json` (its plan), `run.json` (settings, timing, all messages), `fold_meta.json` (instrumentation)
* `chair_1-10.net.svg`, `chair_1-20.net.svg`: normalised nets (calibration bar and sheet border dropped; labels as plain text)
* `chair_1-10.waffle.json`, `chair_1-20.waffle.json`: normalised waffles
* `preview/`: PNGs of the normalised nets, raw sheets, and an isometric of the assembled ribs
