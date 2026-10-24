
## How each number was obtained

- **Ground truth.** The `B1 LEFT` polygon from `research/models/targets_from_v4_3_0.json`, (y, z) in paper mm at 1:10, drawn at exactly 10 px/mm with per-pixel area coverage (`make_cases.py`). The chair polygon has 6 vertices and an area of 2565.0 mm². The sofa_curved polygon has 6 vertices and an area of 5443.4 mm².
- **IoU and area error.** Computed with shapely in mm after px ÷ 10. Holes are combined by even-odd.
- **VTracer region choice.** In `colormode='binary'`, VTracer 0.6.15 emits only foreground clusters, meaning pixels whose **red channel** is below 128 (`cmdapp/src/converter.rs`, `binary_image_to_svg`, tag 0.6.15). Every path is filled `#000000`, so "the dark region" is the union of all paths. results.json also stores the largest single path. On cases 1, 2 and 4 there is exactly one path, so the two are identical. Spline (`C`) segments were flattened at 24 points per cubic.
- **Our tool** was not reimplemented. `run_compare.py` opens the page in headless Chromium and calls the page's own functions:
  - `setScale(10)`, `setPieceMethod('image')`, `imgLoadSrc`
  - calibration points p1/p2 across the piece's known width (equivalent to the student's two clicks), then `imgSetCalibCm`
  - `imgAutoTrace()`, then `renderTraceGate()`, `refreshV4()` and `collectV4Checks()`

  Controls are left at their HTML defaults, except `img-method='dark'` for the second run. With calibration, the simplify tolerance is 0.6 mm on paper (6 px).
- **Node counts.** For VTracer, nodes = one per `M`/`L`/`C` endpoint in the SVG. For ours, nodes = the vertices in `imgState.shapes`.
- **Background leak.** A leak is any connected piece of (traced − GT buffered by 0.5 mm) larger than 1 mm². The 0.5 mm band absorbs edge placement and blur.
- **Repeatability.** Two full runs gave identical metrics and node counts. Only the wall-clock times differed.

## Findings (from the tables above)

1. **Clean silhouettes (cases 1 and 4).** Both pipelines trace the right shape, with no leak and one path each.
   - VTracer: IoU 0.9993–0.9998, |area error| ≤ 0.07 %.
   - Ours: IoU 0.9945–0.9960, with a consistent area **under**-estimate of −0.37 to −0.52 %.
   - Probable cause, consistent but not proven: `imgTraceBoundary` walks pixel **centres** (`x + 0.5`). That puts the outline half a pixel (0.05 mm) inside the true edge. A 0.05 mm mitred inset of the GT alone gives −0.503 % (chair) and −0.300 % (sofa). That is close to the measured −0.516 % and −0.366 %, and the remainder fits RDP simplification. At the 1:10 test scale this is 0.05 mm on paper, below cutting accuracy.
   - Ours returns the true 6 vertices. VTracer returns 27 / 19 spline nodes by default and 8 / 8 polygon nodes in best effort.
2. **Photo-like (case 2).**
   - Our UI default ("Remove background", with drop-shadow removal) has the best IoU, 0.9942, with an area error of −0.34 % and 6 nodes.
   - VTracer gives IoU 0.9903 by default and 0.9912 in best effort. It over-estimates area by about 0.9 % (the blurred edge and shadow fall below its fixed R < 128 cut) and returns 120 / 28 nodes.
   - Our "Dark on light" method has the lowest IoU, 0.9828, and is the only run with a measured background leak (one piece of 2.26 mm²; see `out/chair_photo__overlay.png`).
3. **Room picture H14 (case 3).** In the first run (v4.3.1) **neither pipeline stopped or warned automatically**. From v4.3.2 our default run warns (frame test, finding F3); the Dark-on-light run still does not.
   - VTracer outlined everything dark: 107 paths by default and 6 in best effort, including page frames, pencil, ruler, the chair and the red X. It has no notion of "furniture" and no warning.
   - Our v4.3 automatic room/background warning (`traceQA.suspect`: outline bbox > 85 % of the picture or touching ≥ 3 edges) **did not fire** on its own teaching picture:
     - The default method kept the inner rounded card frame. Its bbox is 52 % of the picture and it touches 0 edges, after "largest only" dropped 3 fragments.
     - "Dark on light" kept the red circle with the X. Its bbox is 9 % and it touches 0 edges.
   - Our gate's rule would have fired on VTracer's union output: bbox 0.925 and 3 edges.
   - v4.3.2 adds a frame test: the share of the kept outline that is background-coloured (not ink) and the number of separate ink pieces inside it. Default run on H14: 0.78 and 69, so the warning fires ("the outline is a frame around a whole drawing"). Furniture line drawings measured for the thresholds (chair, cabinet, wardrobe with 4 doors and 3 drawers, sofa with 6 cushions) have at most 11 inner pieces; the rule is fill share ≥ 0.5 and ≥ 25 pieces. The Dark-on-light outline (red circle around the chair) has 1 inner piece and is not caught.
   - What did stop our pipeline in v4.3.1 is the human step. In every case, `collectV4Checks` blocks printing until the student ticks "the red outline is ONLY the furniture". The gate message on H14 was only "Check the red outline over your picture. 3 fragments were removed (grey boxes)."
4. **Is a human outline check still needed?** **Yes, for both tools and every case.**
   - On the clean and photo-like cases, the geometry is right to ≤ 0.75 mm Hausdorff, but neither tool can tell whether the picture is a true side elevation of the right piece.
   - On H14, both produced confident non-furniture outlines; from v4.3.2 ours warns in one of its two methods.
   - So only the student's confirmation, which our tool requires and VTracer lacks, stood between the room outline and the print.
5. **Speed.** VTracer is a native Rust library: 0.026–0.079 s per call including Python I/O (v4.3.2 re-run; first run 0.025–0.063 s). Our trace runs in page JavaScript: 0.20–0.58 s per call including the Playwright round-trip and re-render (v4.3.2 re-run, with the frame test; the v4.3.1 run gave 0.16–0.39 s). Both are fast enough to feel instant to a student.

## Limits

- The three ground-truth cases are synthetic, all straight-edged, and made from our own targets. The sofa's "curved" back is not part of its `B1 LEFT` side profile.
- There is one room picture, and it is a drawing, not a camera photograph.
- The best-effort VTracer setting was fixed once before metrics were seen, not tuned per case.
- VTracer was driven only in binary mode. Its colour or watershed modes, which would segment rather than threshold, were not tested here.
