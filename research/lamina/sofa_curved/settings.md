# Lamina — sofa_curved

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

Input: `research/models/sofa_curved_fold.stl`. The STL is used, not the OBJ: trimesh fan-triangulates the OBJ's non-convex
n-gons wrongly (loaded area 43870.2 mm² vs 10980 / 26560 / 42746.8), while the pre-triangulated STL loads with exactly the target area.

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

* Faces are re-wound first: `core/plan.py:376-377` — `if not mesh.is_winding_consistent: trimesh.repair.fix_normals(mesh)` (and again `core/modes/folded.py:69` inside `simplify`). For an open, non-watertight surface trimesh's `fix_winding` makes the winding consistent by BFS from an arbitrary face per connected component and does **not** orient it outward (`fix_inversion` acts only on watertight meshes). Result here: Lamina's face normals disagree with the file's normals (= our printed side) on **13 of 21** triangles. For chair/sofa the side panels are split by a non-manifold edge (the seat's side edge is shared by 3 triangles), so the two halves of one planar side panel end up wound opposite ways.
* Every face is unfolded in its own frame with z = the (re-wound) face normal: `core/unfold.py:29` ("origin = vertex 0, z = outward normal"), `core/unfold.py:33` (`v = np.cross(N, u)`), laid flat by proper rotations only (`core/unfold.py:44`, `R = [[c, -s], [s, c]]`, no reflection). The net is therefore drawn **seen from the normal side**; the SVG export flips y only to keep it y-up on screen (`core/export.py:257`, `height - y`) and nesting only rotates (`core/nest.py:49`) — no mirroring anywhere. The printed side = the side the viewer sees = Lamina's normal side; Lamina has no separate "print" layer.
* Direction: `core/modes/folded.py:138` `convex = mesh.face_adjacency_convex`; `core/modes/folded.py:139` `styles = ("solid", "dashed")  # mountain, valley`; `core/modes/folded.py:150` a fold is `styles[0] if convex[k] else styles[1]`; tab hinges `core/modes/folded.py:488` (`"solid" if convex else "dashed"`). Legend `core/modes/folded.py:93` and export header `core/export.py:8`: "solid = mountain, dashed = valley". SVG: dashed = `stroke-dasharray="1.5,1"` (`core/export.py:170`, `:284`).
* trimesh's "convex" is `face_adjacency_projections < tol.merge` (1e-8): a coplanar pair (dihedral 0°, a triangulation diagonal) counts as convex and is drawn as a **solid (mountain) score line**.
* Adapter rule: solid → `data-fold="mountain"`, dashed → `data-fold="valley"`; no mirroring (Lamina already shows the normal side). Note this is mountain/valley relative to **Lamina's re-wound normals**, which for chair and sofa differ from the target's printed side on part of the surface (see above).

### Results

| | 1:10 | 1:20 |
|---|---|---|
| sheets (A3) | 1 | 1 |
| parts (separate cut outlines) | 1 | 1 |
| net panel area, no tabs (mm²) | 42746.80 | 10686.70 |
| target mesh area (mm²) | 42746.8 | 10686.7 |
| panel / mesh area | 1.000000 | 1.000000 |
| cut outline area incl. tabs (mm²) | 42746.8 | 10686.7 |
| score lines: mountain / valley / unmarked | 17 / 3 / 0 | 17 / 3 / 0 |
| … real folds (90°) M / V | 3 / 3 | 3 / 3 |
| … 0° triangulation diagonals M / V | 14 / 0 | 14 / 0 |
| … tab hinges M / V | 0 / 0 | 0 / 0 |
| Lamina refold error (mm) | 3.2e-14 | 1.6e-14 |
| wall-clock build+export (s) | 0.114 | 0.053 |

Score lines per direction come from Lamina's SVG/plan; the split into real folds / 0° diagonals / tab hinges comes from `fold_meta.json` (read-only instrumentation of `Folded.build`, see run_lamina.py), checked line-by-line against plan.json (style and length agree to < 1e-4 mm). `refold_error` is Lamina's own test helper (`core/unfold.py:170`).

Lamina's own messages (verbatim, as its CLI `core.plan.main` prints them):

1:10

```
folded: 1 slices, 1 parts, 1 sheet(s) (34% used), 0 errors, 0 warnings
  note  open surface (not a closed solid): panelled as it is — its boundary edges stay open and carry no joints, and a hole in the surface stays a hole
  note  unfolded 21 triangles into 1 panel(s), 0 seams
```

1:20

```
folded: 1 slices, 1 parts, 1 sheet(s) (9% used), 0 errors, 0 warnings
  note  open surface (not a closed solid): panelled as it is — its boundary edges stay open and carry no joints, and a hole in the surface stays a hole
  note  unfolded 21 triangles into 1 panel(s), 0 seams
```

## Waffle (`interlocked` mode)

Input: `research/models/sofa_curved_waffle_solid.stl` (watertight; Lamina reports no repair).

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
| sheets (A3) | 3 | 1 |
| parts | 26 | 13 |
| ribs in x-planes (X family) | 18 | 9 |
| ribs in y-planes (Y family) | 8 | 4 |
| x offsets (mm) | 5, 15, 25, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 135, 145, 155, 165, 175 | 5, 15, 25, 35, 45, 55, 65, 75, 85 |
| y offsets (mm) | 5.3125, 15.9375, 26.5625, 37.1875, 47.8125, 58.4375, 69.0625, 79.6875 | 5.3125, 15.9375, 26.5625, 37.1875 |
| slot widths in export (mm: count) | 1.500: 294, 4.562: 22, 4.250: 16, 4.563: 13 | 1.500: 71, 4.562: 11, 4.250: 8, 4.563: 7 |
| assembled rib bbox incl. board (mm) | 180 × 85 × 80 | 90 × 42.5 × 40 |
| … z range (mm) | 0 – 80 | 0 – 40 |
| solid bbox (mm) | 180 × 85 × 80 | 90 × 42.5 × 40 |
| errors / warnings (Lamina counts) | 24 / 0 | 0 / 0 |
| wall-clock build+export (s) | 1.088 | 0.302 |

Slot width: measured on Lamina's exported SVG sheets (U-turn edges of every cut ring; the histogram's other entries are notch-like outline features, not slots): see table. Lamina draws slots as `rect_along(..., b.thickness + slot_offset)` = 1.5 mm.

Lamina's own messages (verbatim):

1:10

```
interlocked: 26 slices, 26 parts, 3 sheet(s) (39% used), 24 errors, 0 warnings
  ERROR X-2: Y-1 cannot slide into its slot: X-2's material is in its path (21 mm of it) — the crossing line meets X-2 twice (a hollow or concave section): move Y-1 (offset), lower the notch ratio, or delete Y-1
  ERROR X-2: Y-2 cannot slide into its slot: X-2's material is in its path (21 mm of it) — the crossing line meets X-2 twice (a hollow or concave section): move Y-2 (offset), lower the notch ratio, or delete Y-2
  ERROR X-2: Y-3 cannot slide into its slot: X-2's material is in its path (21 mm of it) — the crossing line meets X-2 twice (a hollow or concave section): move Y-3 (offset), lower the notch ratio, or delete Y-3
  ERROR X-2: Y-4 cannot slide into its slot: X-2's material is in its path (21 mm of it) — the crossing line meets X-2 twice (a hollow or concave section): move Y-4 (offset), lower the notch ratio, or delete Y-4
  ERROR X-2: Y-5 cannot slide into its slot: X-2's material is in its path (21 mm of it) — the crossing line meets X-2 twice (a hollow or concave section): move Y-5 (offset), lower the notch ratio, or delete Y-5
  ERROR X-2: Y-6 cannot slide into its slot: X-2's material is in its path (21 mm of it) — the crossing line meets X-2 twice (a hollow or concave section): move Y-6 (offset), lower the notch ratio, or delete Y-6
  ERROR X-17: Y-1 cannot slide into its slot: X-17's material is in its path (36 mm of it) — the crossing line meets X-17 twice (a hollow or concave section): move Y-1 (offset), lower the notch ratio, or delete Y-1
  ERROR X-17: Y-2 cannot slide into its slot: X-17's material is in its path (36 mm of it) — the crossing line meets X-17 twice (a hollow or concave section): move Y-2 (offset), lower the notch ratio, or delete Y-2
  ERROR X-17: Y-3 cannot slide into its slot: X-17's material is in its path (36 mm of it) — the crossing line meets X-17 twice (a hollow or concave section): move Y-3 (offset), lower the notch ratio, or delete Y-3
  ERROR X-17: Y-4 cannot slide into its slot: X-17's material is in its path (36 mm of it) — the crossing line meets X-17 twice (a hollow or concave section): move Y-4 (offset), lower the notch ratio, or delete Y-4
  ERROR X-17: Y-5 cannot slide into its slot: X-17's material is in its path (36 mm of it) — the crossing line meets X-17 twice (a hollow or concave section): move Y-5 (offset), lower the notch ratio, or delete Y-5
  ERROR X-17: Y-6 cannot slide into its slot: X-17's material is in its path (36 mm of it) — the crossing line meets X-17 twice (a hollow or concave section): move Y-6 (offset), lower the notch ratio, or delete Y-6
  ERROR Y-1: X-2 cannot slide into its slot: Y-1's material is in its path (21 mm of it) — the crossing line meets Y-1 twice (a hollow or concave section): move X-2 (offset), lower the notch ratio, or delete X-2
  ERROR Y-1: X-17 cannot slide into its slot: Y-1's material is in its path (44 mm of it) — the crossing line meets Y-1 twice (a hollow or concave section): move X-17 (offset), lower the notch ratio, or delete X-17
  ERROR Y-2: X-2 cannot slide into its slot: Y-2's material is in its path (21 mm of it) — the crossing line meets Y-2 twice (a hollow or concave section): move X-2 (offset), lower the notch ratio, or delete X-2
  ERROR Y-2: X-17 cannot slide into its slot: Y-2's material is in its path (44 mm of it) — the crossing line meets Y-2 twice (a hollow or concave section): move X-17 (offset), lower the notch ratio, or delete X-17
  ERROR Y-3: X-2 cannot slide into its slot: Y-3's material is in its path (21 mm of it) — the crossing line meets Y-3 twice (a hollow or concave section): move X-2 (offset), lower the notch ratio, or delete X-2
  ERROR Y-3: X-17 cannot slide into its slot: Y-3's material is in its path (44 mm of it) — the crossing line meets Y-3 twice (a hollow or concave section): move X-17 (offset), lower the notch ratio, or delete X-17
  ERROR Y-4: X-2 cannot slide into its slot: Y-4's material is in its path (21 mm of it) — the crossing line meets Y-4 twice (a hollow or concave section): move X-2 (offset), lower the notch ratio, or delete X-2
  ERROR Y-4: X-17 cannot slide into its slot: Y-4's material is in its path (44 mm of it) — the crossing line meets Y-4 twice (a hollow or concave section): move X-17 (offset), lower the notch ratio, or delete X-17
  ERROR Y-5: X-2 cannot slide into its slot: Y-5's material is in its path (21 mm of it) — the crossing line meets Y-5 twice (a hollow or concave section): move X-2 (offset), lower the notch ratio, or delete X-2
  ERROR Y-5: X-17 cannot slide into its slot: Y-5's material is in its path (44 mm of it) — the crossing line meets Y-5 twice (a hollow or concave section): move X-17 (offset), lower the notch ratio, or delete X-17
  ERROR Y-6: X-2 cannot slide into its slot: Y-6's material is in its path (21 mm of it) — the crossing line meets Y-6 twice (a hollow or concave section): move X-2 (offset), lower the notch ratio, or delete X-2
  ERROR Y-6: X-17 cannot slide into its slot: Y-6's material is in its path (44 mm of it) — the crossing line meets Y-6 twice (a hollow or concave section): move X-17 (offset), lower the notch ratio, or delete X-17
```

1:20

```
interlocked: 13 slices, 13 parts, 1 sheet(s) (15% used), 0 errors, 0 warnings
```

## Observations (from the outputs above, not Lamina messages)

- 1:10 waffle: Lamina's insertion check reports 24 errors ("cannot slide into its slot") for X-2 and X-17 against Y-1…Y-6 and the reverse; the parts are exported anyway on 3 sheets. Six INNER rings (closed slots/holes) appear on sheet 1. 1:20 has 0 errors.
- Fold: one net, 0 seams, no tabs at all (cut outline area = panel area): with seat/side joins non-manifold, the unfolder connects everything through folds and every remaining edge is an outside cut edge, so Lamina produces no glue tab anywhere.

## Files

* `raw/fold_<s>/`, `raw/waffle_<s>/`: Lamina's SVG sheet(s) (layers OUTER blue / INNER green / SCORE yellow / LABEL red, sheet border and a 10 cm calibration bar on the LABEL/OUTER layers), `assembly-key.txt`, `plan.json` (its plan), `run.json` (settings, timing, all messages), `fold_meta.json` (instrumentation)
* `sofa_curved_1-10.net.svg`, `sofa_curved_1-20.net.svg`: normalised nets (calibration bar and sheet border dropped; labels as plain text)
* `sofa_curved_1-10.waffle.json`, `sofa_curved_1-20.waffle.json`: normalised waffles
* `preview/`: PNGs of the normalised nets, raw sheets, and an isometric of the assembled ribs
