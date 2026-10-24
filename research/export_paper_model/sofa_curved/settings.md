# Export Paper Model — sofa_curved

## Tool
- Export Paper Model (Blender add-on), manifest version **1.4.2** (`blender_manifest.toml`), git commit **d688dcd** ("Merge pull request #115 from stariluz/master").
- Licence: **GPL-3.0-or-later** (`blender_manifest.toml`: `license = ["SPDX:GPL-3.0-or-later"]`).
- Host: Blender as a Python module, bpy **5.2.3 LTS**, Python 3.13.17, headless (no UI).
- Add-on loaded unmodified from the pinned clone via a symlink named `io_export_paper_model`; registered with `io_export_paper_model.register()`.

## Script (fully scripted, manual steps = 0)
```
. <scratchpad>/rv/bin/activate
python -I research/export_paper_model/run_export.py <dir with io_export_paper_model symlink> research/export_paper_model
python3 -I research/export_paper_model/adapt.py <case>/raw_<scale>.svg -o <case>/<case>_<scale>.net.svg --stats <case>/stats_<scale>.json
/usr/local/bin/python3 -I research/export_paper_model/render_png.py <case>/*.net.svg
python -I research/export_paper_model/diagnose_orientation.py <addon dir> research/export_paper_model   # evidence only
```
Operators used (the add-on's own): `bpy.ops.mesh.unfold()` (Unfold, unfold_operator.py:31-116) then `bpy.ops.export_mesh.paper_model(...)` (ExportPaperModel, unfold_operator.py:235-403). Import: `bpy.ops.wm.obj_import(forward_axis='Y', up_axis='Z')` so coordinates are kept as in the OBJ (1 OBJ unit = 1 Blender unit = 1 m to the add-on).

## Settings changed from the add-on defaults (everything else default)
| Setting | Default | Used | Why |
|---|---|---|---|
| Export `file_format` | PDF (unfold_operator.py:308-314) | SVG | task |
| Export `page_size_preset` | A4 (unfold_operator.py:249-251) | A3 | task |
| Export `output_size_x/y` | 0.210/0.297 m (unfold_operator.py:252-257) | 0.297/0.420 m | A3 = 297 × 420 mm |
| Export `scale` (divisor) | 1 (unfold_operator.py:328-330) | 1000 for 1:10, 2000 for 1:20 | the exporter writes Blender metres × 1000 as mm (svg.py:22, unfolder.py:202-216); mesh unit = paper mm at 1:10, so ÷1000 gives exact paper mm, ÷2000 gives half |
| Scene `paper_model.use_auto_scale` | True (unfold_operator.py:758-760) | False | otherwise `prepare()` overwrites the scale with an auto fit (unfold_operator.py:365-366) |
| Scene `paper_model.scale` | 1 | same as export scale | consistency (only used by Unfold when limit_by_page is on, unfold_operator.py:84) |

Defaults kept (relevant ones): margin 5 mm; tabs = STICKER, width 5 mm (paper size, **not** scaled with the model, so tabs are 5 mm at both 1:10 and 1:20); numbers INSIDE; paper thickness 0; hidden-edge angle π/360; texture NONE; nesting BOX; Unfold priorities default; `limit_by_page` False.

Scale verification: the table top edge is a fold line in the net; measured fold lengths include **140.0 mm** at 1:10 and **70.0 mm** at 1:20 (see table/stats_*.json `fold_lengths_mm`). Panel areas reproduce the mesh areas exactly (below), so paper mm are exact.

## How the add-on encodes fold direction and the printed side (source evidence)
- Fold lines are written as `<path class='convex'>` and `<path class='concave'>`, one `M a L b` segment per fold (svg.py:155-181; PDF does the same, pdf.py:161-201). Defaults: both black, convex = DASH, concave = DASHDOT (unfold_operator.py:189-206; dash patterns svg.py:29-32). Only the dash style tells them apart on paper.
- Classification: `edge_group = data_convex if edge.is_convex() else data_concave` (svg.py:168-170). `Edge.is_convex()` = `(self.angle > 0) ^ self.uvedges[0].uvface.flipped` (unfolder.py:654-655); `angle` is the signed dihedral between the two faces from their normals (`calculate_angle`, unfolder.py:647-652). For islands marked inside-out the two classes are swapped before writing (svg.py:171-172; flag set in unfolder.py:365-371 when an island contains mirrored faces and more concave than convex edges).
- Drawn side: every face is laid flat with `z_up_matrix(face normal)` (unfolder.py:59-71, 1142), i.e. viewed from its normal side; `UVFace.flipped` marks a face drawn mirrored (unfolder.py:1140, set during joins at 999). The SVG writer only converts y-up to y-down (svg.py:22), which does not mirror the picture. So the raw SVG shows the **normal (= printed/outside) side** to the viewer unless a face is flipped. In all exports here no face was flipped and no island was inside-out (orientation_diag.json), and each face's SVG polygon is counter-clockwise on screen (normal side toward the viewer).
- Meaning: "convex" = the fold makes a convex angle seen from the drawn (printed) side = the printed side ends up outside = folds away from the viewer → **mountain**; "concave" → **valley**. The adapter maps exactly that and records the raw class in `data-raw-class`. No mirroring was needed (printed side = viewer side).
- Independent check (diagnose_orientation.py, runtime wrapper around `Svg.write`, add-on unchanged): for every **panel** fold (two panels joined in the net), the 3D dihedral seen from the viewer side agrees with the add-on's class (all mountain).
- Fold lines also include the **hinge line of each glue tab** (the add-on draws a convex/concave line on cut edges that carry a sticker, svg.py:158-159). The adapter keeps them in 02_SCORE_BLUE and tags them `data-kind="tab-hinge"` (panel folds: `data-kind="panel"`).
- Caveat found: in chair and sofa_curved the SEAT and A1_BACK faces traverse their shared edge in the same direction (inconsistent winding across that edge in the target OBJ; bmesh reports the edge as non-contiguous, while the mesh spec says each face normal is the printed side). The add-on's `calculate_angle` assumes opposite traversal, so that edge's angle sign is inverted; it is a cut edge here, and its tab hinge is written as **concave → valley**, while the 3D dihedral between the two printed sides at that edge is convex. This is the single `valley` in those nets. The adapter does not correct it.


## Results

| Scale | Status | Raw file(s) | Normalised | Pages (A3) | Parts | Seams marked | Folds total (mountain/valley) | Panel folds M/V | Tab-hinge folds M/V | Tabs (degenerate <0.001 mm²) | Outline area mm² | Tab area mm² | Panel area mm² | Mesh area mm² | Diff | Unfold+export s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1:10 | **FAILED** | none | none | – | – | 2 | – | – | – | – | – | – | – | 42746.8 | – | 0.0041 |
| 1:20 | OK | raw_1-20.svg | sofa_curved_1-20.net.svg (+.png) | 1 | 1 | 2 | 6 (5/1) | 4/0 | 1/1 | 2 (0) | 11174.33 | 487.62 | 10686.70 | 10686.7 | +0.002 | 0.0045 |

Area method: `outline area` = shoelace area of the closed cut outline (tabs included); `tab area` = sum of the add-on's own tab polygons (`path.sticker`); panel area = outline − tabs. Wall-clock = `time.perf_counter()` around `mesh.unfold()` + `export_mesh.paper_model()` in one bpy process (file write included; OBJ import and add-on registration excluded).

Page handling: the add-on writes one SVG per page, named `<name>_page<N>.svg` when there is more than one page (svg.py:65); all successful exports here are single-page, so no page combination was needed (adapter supports it: pages side by side, 10 mm gap, frames in group `00_PAGES`).

## Warnings / failures

- 1:10 default export failed: `RuntimeError: Invalid Input Error: An island is too big to fit onto page of the given size. Either downscale the model or find and split that island manually. Export failed, sorry.` (raised by `paginate_islands`, unfolder.py:113-119). Unfold kept the whole mesh as one island; at 1:20 that island measures 174.97 × 249.96 mm on the page, so at 1:10 it is about 349.9 × 499.9 mm, larger than the A3 printable area 287 × 410 mm (A3 minus 2 × 5 mm margin). The add-on does not split or tile an island by itself: it stops.
- Extra attempt (non-default, only to see whether the add-on can split the net itself): scene `limit_by_page=True`, scene page preset A3, same export settings. Result: **add-on crash**, no file. Error text: `TypeError: '>' not supported between instances of 'NoneType' and 'int'` at `unfolder.py:369` (`balance = sum((+1 if edge.angle > 0 else -1) ...)`), raised inside `MESH_OT_unfold.execute` (`unfold_operator.py:85`). The same crash occurs when calling the export operator alone with limit_by_page on. Cause in source: with a size limit some faces get joined mirrored (`flipped`), and `calculate_angle()` is re-run only for edges with `main_faces` (unfolder.py:350-353), while `Edge.angle` stays `None` for boundary edges (unfolder.py:629, 281-282) that line 369 still iterates over.
- Python SyntaxWarning on add-on import: `unfold_operator.py:28: invalid escape sequence '\w'` (harmless).
- Tabs: some tabs are zero-area slivers (count in the table): the add-on shortens a tab to at most half its edge length and narrows its angles to the target face's corner angles (`class Sticker`, unfolder.py:1163-1220), which on short 90° edges collapses the tab to a line.
