# PolyZamboni — sofa_curved

## Tool
- PolyZamboni (Blender add-on, "Papercraft in Blender"), manifest version **1.3.1** (`blender_manifest.toml`; `bl_info` version (1,3,1)), git commit **a6b880e** (a6b880ef9ea8, 13 Jul 2026, "correct min blender version in __init__.py"), github.com/AntonFlorey/PolyZamboni.
- Licence: **GPL-3.0-or-later** (`blender_manifest.toml`: `license = ["SPDX:GPL-3.0-or-later"]`; LICENSE = GNU GPL v3).
- Host: Blender as a Python module, bpy **5.2.3 LTS**, Python 3.13.17, headless, no window. `gpu.init()` gives an OpenGL context on llvmpipe (software): needed because `shaders.py:179` compiles a GPU shader at import, and the exporter renders face colours off-screen (`exporters.py:303-353`).
- Extra packages installed into the venv for the add-on's `requirements.txt` (`matplotlib>=3.9.0`, `networkx>=3.3`): `uv pip install "matplotlib>=3.9.0" "networkx>=3.3"` -> matplotlib 3.11.2, contourpy 1.4.0, cycler 0.12.1, fonttools 4.67.0, kiwisolver 1.5.1, packaging 26.3, pyparsing 3.3.3, python-dateutil 3.0.0, six 1.17.0, tzdata 2026.5 (networkx 3.7, numpy 2.5.4, pillow 13.0.0 were already present). The add-on ships wheels for matplotlib 3.10.9 / networkx 3.6.1 (manifest); the PyPI versions above were used instead.
- Add-on source loaded unmodified from the pinned clone (`import PolyZamboni; PolyZamboni.register()`).

## Headless automatic use: possible, but not through its operators
- The add-on HAS an automatic cut method: operator **Auto Unfold** `polyzamboni.auto_cuts_op` (operators.py:495-605), algorithm GREEDY (`autozamboni.greedy_auto_cuts`, autozamboni.py:14-93): cut every edge, then remove cuts one by one (edges sorted by alignment with the loop axis) as long as the merged piece stays acyclic, has at most `max_pieces_per_component` faces and does not overlap (mesh pieces, and glue flaps for quality NO_OVERLAPS_ALLOWED). Defaults used: Quality = No overlaps, Loops = Z, Pieces per component = 10 (operators.py:503-534).
- Its operators cannot be called headless as such (tested, errors verbatim):
  - `bpy.ops.polyzamboni.cut_initialization_op('EXEC_DEFAULT')` -> `AttributeError: 'InitializeCuttingOperator' object has no attribute 'selected_mesh_is_manifold'` (the attribute is only set in `invoke`, operators.py:59; `execute` reads it, operators.py:114).
  - `bpy.ops.polyzamboni.auto_cuts_op('INVOKE_DEFAULT')` returns `{'RUNNING_MODAL'}`: the work runs in a modal TIMER handler (operators.py:551-588) that never fires without a window, so no cuts are made.
  - `bpy.ops.polyzamboni.export_operator_svg('EXEC_DEFAULT' or 'INVOKE_DEFAULT', filepath=...)` -> `AttributeError: 'PolyZamboniExportSVGOperator' object has no attribute 'user_defined_page_layout_exists'` (set only in `invoke`, operators.py:742; read in `execute`, operators.py:764).
- So `run_polyzamboni.py` executes the same code those operators run, in the same order, with the add-on's own functions: the `invoke` checks of "Unfold this mesh" (operators.py:59-97) -> `operators_backend.initialize_paper_model` (operators.py:125) -> `PaperModel.from_existing` + `greedy_auto_cuts(...)` drained to the end + `close()` (= AutoCutsOperator.execute/modal, operators.py:546-588) -> `operators_backend.compute_build_step_numbers(mesh, [])` (= "Compute Build Order" with no face selected, operators.py:396-401) -> `PolyZamboniExportSVGOperator.execute` itself, called unbound on a stand-in `self` whose `general_settings` / `line_settings` / `texture_settings` are real instances of the add-on's PropertyGroups (defaults), `user_defined_page_layout_exists=False` (as `invoke` sets it when no page layout was made).
- The cut layout is therefore 100 % the add-on's automatic method; no cut was placed by hand.

## Script
```
. <scratchpad>/rv/bin/activate
python -I research/polyzamboni/run_polyzamboni.py <dir containing the PolyZamboni clone> research/polyzamboni > research/polyzamboni/run_stdout.txt
python3 -I research/polyzamboni/adapt.py <case>/raw_<scale>_page*.svg -o <case>/<case>_<scale>.net.svg --stats <case>/stats_<scale>.json
/usr/local/bin/python3 -I research/polyzamboni/render_png.py <case>/*.net.svg
python -I research/net_judge.py <case>/<case>_<scale>.net.svg research/models/<case>_fold.obj [--mesh-scale 0.5 for 1:20] --json <case>/<case>_<scale>.judge.json
python3 -I research/polyzamboni/make_settings.py
```
Import: `bpy.ops.wm.obj_import(forward_axis='Y', up_axis='Z')`, 1 OBJ unit = 1 Blender unit (BU), coordinates as in the OBJ. Full machine log: `run_log.json` (cut layout = edge constraints, components, overlap/cycle flags, build steps, every export setting value), `run_stdout.txt` (the add-on's own messages).

## Settings changed from the add-on defaults (everything else default)
| Setting | Default | Used | Why |
|---|---|---|---|
| Export "Page Size" `paper_size` | A4 (properties.py:227-245) | A3 | task (A2 only in the marked EXTRA run) |
| Export "Prints inside" `print_on_inside` | True (properties.py:312-316) | False | printed side = face normal = outside, as the target meshes define it (see below) |
| Export `target_model_height` (scaling) | 0.1 BU, and `invoke` overwrites it with a fit-to-page size (operators.py:737-739) | 0.001 × mesh height (1:10), 0.0005 × mesh height (1:20) | the exporter's scale = cm(target height) / mesh height (printprepper.py:217-222, units.py: cm = 100 × BU × unit scale); mesh BU are paper mm at 1:10, so 0.001 × height gives 0.1 cm per BU = exact paper mm; 1:20 = half |
| Mesh "Glue flap height" `glue_flap_height` | 0.15 BU (properties.py:123-129) | 5.0 BU (= 5 mm at 1:10, 2.5 mm at 1:20) | the default is in mesh units and would give 0.15 mm flaps on this mm-scaled mesh; flaps scale with the model |

Kept defaults (relevant): Auto Unfold GREEDY / No overlaps / Z / 10 faces per piece; glue flap angle 45 deg, alternating flaps, smart trimming on; page margin 0.005 BU and gap 0.0025 BU (these are in BU too -> 0.05 mm and 0.025 mm on paper here, not 5 mm); one material per page; line width 0.5 pt; edge numbers and build step numbers on; textures/flap colour on (raster image in the raw SVG, dropped by the adapter); single-sided.

## Manual steps: 2
1. **Add one empty UV map** to the imported mesh (`mesh.uv_layers.new()`). The OBJs have no `vt`; with no UV layer the exporter crashes for any setting: `TypeError: 'NoneType' object is not iterable` at `printprepper.py:47` (`ColoredTriangleData` gets `uvs=None` from printprepper.py:330). Observed on the first run (table, the only case that passed the init check before the Edge Split rule existed).
2. **Edge Split of one edge** [[0.0, 0.0, 42.0], [180.0, 0.0, 42.0]] (SEAT / A1_BACK), the only interior edge whose two faces traverse it in the same direction (bmesh `is_contiguous` = False). Without it "Unfold this mesh" refuses: dialog title "Something went wrong D:", text `Bad normals! Try "Recalculate Outside" (Shift-N)` (operators.py:60-72, 102-104), and its `execute` does nothing (operators.py:113-115). The add-on's suggested fix (Recalculate Outside) was **not** used: it would flip a panel's normal and thus its printed side. Edge Split keeps every vertex position and normal; that edge becomes a plain cut (no glue flap) in the net. Rule: split exactly the interior edges with `is_contiguous == False` (here 1).

UI actions a GUI user would click (not counted as decisions): Unfold this mesh -> Auto Unfold (defaults) -> Compute Build Order (nothing selected) -> Export SVG with the settings above.

## How the add-on encodes fold direction and the printed side (source evidence)
- Fold classes come from Blender's `BMEdge.is_convex` of the mesh edge: `FoldEdgeData(..., curr_edge.is_convex, curr_edge.calc_face_angle())` for folds inside a piece (printprepper.py:293) and `FoldEdgeAtGlueFlapData(..., curr_edge.is_convex, ...)` for the hinge of each glue flap (printprepper.py:286). Convexity is judged from the face normals (= printed side of this mesh set).
- Line styles: `ls = convex_fold_edge_ls if is_convex else concave_fold_edge_ls` (exporters.py:244, flap hinges exporters.py:253); defaults convex = `".."`, concave = `"--."` (properties.py:349-358; patterns exporters.py:63-69: ".." = (0,(2,4,2,4)), "--." = (0,(8,4,8,4,2,4))), both black (properties.py:371-384). Cut edges and glue-flap outlines are solid `"-"` (properties.py:344-348, 359-363). Folds flatter than `hide_fold_edge_angle_th` (default 1 deg, properties.py:337-342) are not drawn (exporters.py:240-241). matplotlib scales dash patterns by the line width 0.5, so in the SVG convex = `stroke-dasharray: 1,2,1,2` and concave = `4,2,4,2,1,2`.
- Drawn side: each face is laid flat in a 2D frame x = edge direction, y = normal x edge (`construct_2d_space_along_face_edge`, geometry.py:140-147), i.e. seen from the normal (printed) side; joins across folds are rotations, `AffineTransform2D(-I, ...)` (unfolding.py:66). Recorded at run time: every unfolded triangle has positive signed area (run_log.json `tri_signed_area_signs = [1]`), so no face is mirrored.
- `print_on_inside` (export setting "Prints inside", default **True**, description "After glueing the pieces together, prints will be on the meshes inside if set to True", properties.py:312-316) mirrors every page about its vertical centre line (`page_flip_transform` diag(-1,1), exporters.py:149-155, applied to all lines exporters.py:377-392). The add-on's default thus prints the drawing on the inside of the model. **Changed to False** here so the printed side of the paper (the side the viewer sees) is the face-normal (outside) side, as the target meshes define it. The adapter would mirror back if True (`--print-on-inside`); not needed.
- Meaning: convex (`..`) = the printed side ends up on the outside of the fold = folds away from the viewer -> **mountain**; concave (`--.`) -> **valley**. adapt.py maps exactly that and keeps the raw class in `data-raw-class`; it never corrects a class. In these meshes every interior edge is convex (90 deg), so only mountain folds occur; the concave mapping is from source only, not exercised by data.
- Independent check: research/net_judge.py (reads only the normalised SVG and the OBJ) places every face printed side out and finds 0 printed-inward faces and 100 % fold-direction agreement on every produced net (see *.judge.json).

## Auto Unfold result (the add-on's own cut layout)
- Mesh: 25 edges, 6 interior; init checks {"manifold": true, "normals_ok": false, "multi_touching_faces": 0, "non_triangulatable_faces": 0, "max_planarity_score": 0.0}; after the Edge Split: {"normals_ok": true, "manifold": true}.
- Cuts kept by Auto Unfold (edge index: constraint): {"19": "auto"} (boundary edges are always cuts).
- Pieces (connected components): **1** — faces [[0, 1, 2, 3, 4]]; cyclic (unfoldable) pieces: none; pieces flagged overlapping: none; glue-flap collisions: none (i.e. all pieces "green" in the add-on's quality feedback).
- Build steps ("Compute Build Order"): {'0': 1} (one piece = step 1).

## Results

| Scale | Status | Raw file(s) | Normalised | Pages | Parts | Folds total (M/V) | Panel folds M/V | Flap-hinge folds M/V | Glue flaps | Outline area mm² | Flap area mm² | Panel area mm² | Mesh area mm² (×¼ at 1:20) | Diff | Seconds (unfold+autocut+build steps + export) | Judge |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-10 | **NO NET** (raw export clipped, adapter refused) | raw_1-10_page1.svg, raw_1-10_page2.svg | none | 2 (1 empty) | – | – | – | – | – | – | – | – | 42746.80 | – | 0.0787 + 3.5552 | – |
| 1-20 | OK | raw_1-20_page1.svg | sofa_curved_1-20.net.svg (+.png) | 1 (0 empty) | 1 | 5 (5/0) | 4/0 | 1/0 | 1 | 10727.95 | 41.25 | 10686.70 | 10686.70 | +0.000 | 0.0787 + 0.9713 | M1 0.0 mm, cov 100.0 %, M2 100.0 %, M3 100.0 %, M4 0, inward 0 |
| 1-10 (A2) | EXTRA (A2, non-default page) OK | raw_1-10_A2_page1.svg | sofa_curved_1-10_A2.net.svg (+.png) | 1 (0 empty) | 1 | 5 (5/0) | 4/0 | 1/0 | 1 | 42911.80 | 165.00 | 42746.80 | 42746.80 | +0.001 | 0.0787 + 1.153 | M1 0.0 mm, cov 100.0 %, M2 100.0 %, M3 100.0 %, M4 0, inward 0 |

Area method: outline area = shoelace area of each closed cut outline (flaps included); flap area = each glue flap polygon (its 2-3 drawn edges closed by its hinge); panel area = outline − flaps. Wall-clock = `time.perf_counter()` around the steps in one bpy process; the export time is dominated by the off-screen colour render on software OpenGL (llvmpipe) at the default texture quality "high" (2048²). Whole run of `run_polyzamboni.py` (3 cases, all exports incl. EXTRA, add-on registration, gpu init): about 19-23 s per full run (three runs made while developing: 18.9 s, 21.2 s, 22.8 s; the last one produced the files here).

Page handling: the exporter writes one SVG per page (`<name>_page<N>.svg`, exporters.py:426-434). The adapter places pages side by side (10 mm gap, frames in `00_PAGES`) and records `data-pages`.

Scale check (fold line lengths in mm, from stats_*.json): 1-20: fold lengths [19.0, 19.0, 21.0, 21.0, 90.0]; 1-10_A2: fold lengths [38.0, 38.0, 42.0, 42.0, 180.0]

## Warnings / messages from the add-on
- stdout: POLYZAMBONI INFO: Greedy Auto Cuts total time: 0.06687164306640625 | POLYZAMBONI INFO: Init time: 0.00s (4.9%) | POLYZAMBONI WARNING: Unfolded connected component does not fit on one page! | POLYZAMBONI INFO: Paper model instruction fits on 2 pages. | POLYZAMBONI INFO: Paper model instructions successfully created! | POLYZAMBONI INFO: Paper model instruction fits on 1 pages.
- **1:10 on A3 gives no usable net.** The add-on warns `POLYZAMBONI WARNING: Unfolded connected component does not fit on one page!` (printprepper.py:462) and still writes the file: page 1 is empty (the piece did not fit on the first page, so a second page was opened, printprepper.py:454-464) and the piece on page 2 runs off the page; matplotlib clips it at the page edge and even writes segments wholly outside as `<path>` without `d`. adapt.py refuses: sofa_curved/raw_1-10_page2.svg: geometry reaches beyond the page (matplotlib clipped it at the page edge; 12 line segment(s) written without path data) | sofa_curved/raw_1-10_page2.svg: 2 open outline chain(s), cut outline does not close. The add-on has no automatic split of a piece across pages; Auto Unfold limits pieces by face count only (max 10), not by page size. The EXTRA A2 run (same 1:10 scale, non-default page) shows the complete 1:10 net.
- `invoke` would also show a planarity warning if a face had planarity error > 0.1 (operators.py:93-97): max error here 0.0.
- EGL messages on stderr at gpu.init (`EGL_BAD_MATCH`, 3 lines) before the llvmpipe context is created; harmless.
