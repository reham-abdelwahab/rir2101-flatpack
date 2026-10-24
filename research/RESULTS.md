# Results — tool comparison D2–D7 + D9 (24 Oct 2026; corrected and re-run for v4.3.2 the same evening)

All numbers in the two big tables come from the judge output files (`*.judge.json`, `*.wjudge.json`), assembled by `make_results.py` (no number typed by hand); the tracing figures come from `vtracer/results.md`. Tool versions are pinned in [TOOLS.md](TOOLS.md). Physical builds (D8) have **not** been done: nothing here says a model can be built by a student.

**Re-run for v4.3.2 (24 Oct, evening).** Both judges were re-run on every stored output and reproduced every committed judge file byte for byte. Our nets and waffles were re-exported from v4.3.2: their geometry is identical to the v4.3.1 export (only the version label changed), so every row for our tool is unchanged. The tracing comparison was re-run: one result changed (H14, our default settings, now warns: F3). Section 6 lists every correction to the earlier text.

## 1. Method
Three furniture cases at 1:10 and 1:20 on A3: chair 45 × 45 × 85 cm, table 140 × 80 × 75 cm, curved sofa 180 × 85 × 100 cm with an arched back. The same target went to every tool (`models/`): for Fold & Glue a 5-panel surface mesh (chair 10 980 mm², table 26 560 mm², sofa 42 746.8 mm² at 1:10); for Waffle a closed solid. **The Waffle sofa solid has no arched back** (180 × 85 × 80 cm): our Waffle sofa is built from boxes, so the arch is tested on Fold & Glue only.

Every export was converted by a per-tool adapter to one format ([FORMAT.md](FORMAT.md)) and scored by one judge per method that contains no tool's code. The net judge folds each net back onto the target, searches the placement of every part, and checks size, coverage, fold direction against the printed marks, tab landing, overlaps and the printed side of every panel. The waffle judge rebuilds the assembly from the rib outlines. Negative control: the judge fails the kept v4.2.4 nets for the faults found earlier (back valley fold, table tabs that cannot land) and also found F2, which our own verifier missed at the time (section 5).

How to read the columns: **M3 tabs land** counts each tool's own tabs, so 6/6 and 3/3 are both "all tabs land", not a ranking; a tool with fewer tabs is not worse for that. **Score lines with no flap** are blue lines that end in free space. Flat (0°) score lines are not in the table: Lamina's table net has 9 (judge field `flat_score_lines`).

## 2. Fold & Glue nets (net_judge.py)

| Tool | Case | Scale | Pass | M1 size err (mm) | Coverage % | M2 folds as marked % | M3 tabs land | M4 overlaps | Faces not placed | Printed side inward | Score lines with no flap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ours v4.3.2 | chair | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Ours v4.3.2 | chair | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Ours v4.3.2 | table | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| Ours v4.3.2 | table | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| Ours v4.3.2 | sofa_curved | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Ours v4.3.2 | sofa_curved | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Export Paper Model 1.4.2 | chair | 1:10 | ❌ | 0.0 | 100.0 | 85.7 (7 folds) | 3/3 | 0 | 0 | 0 | 1 |
| Export Paper Model 1.4.2 | chair | 1:20 | ❌ | 0.0 | 100.0 | 85.7 (7 folds) | 3/3 | 0 | 0 | 0 | 1 |
| Export Paper Model 1.4.2 | table | 1:10 | ❌ | 0.0 | 100.0 | 100.0 (5 folds) | 3/3 | 0 | 0 | 0 | 1 |
| Export Paper Model 1.4.2 | table | 1:20 | ❌ | 0.0 | 100.0 | 100.0 (5 folds) | 3/3 | 0 | 0 | 0 | 1 |
| Export Paper Model 1.4.2 | sofa_curved | 1:10 | ❌ no output | | | | | | | | |
| Export Paper Model 1.4.2 | sofa_curved | 1:20 | ❌ | 0.0 | 100.0 | 83.3 (6 folds) | 2/3 | 0 | 1 | 0 | 0 |
| PolyZamboni 1.3.1 | chair | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 3/3 | 0 | 0 | 0 | 0 |
| PolyZamboni 1.3.1 | chair | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 3/3 | 0 | 0 | 0 | 0 |
| PolyZamboni 1.3.1 | table | 1:10 | ❌ no output | | | | | | | | |
| PolyZamboni 1.3.1 | table | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| PolyZamboni 1.3.1 | sofa_curved | 1:10 | ❌ no output | | | | | | | | |
| PolyZamboni 1.3.1 | sofa_curved | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (5 folds) | 1/1 | 0 | 0 | 0 | 0 |
| Lamina 0.3.0 (Folded) | chair | 1:10 | ❌ | 5.0 | 72.55 | 83.3 (6 folds) | 2/7 | 0 | 5 | 0 | 0 |
| Lamina 0.3.0 (Folded) | chair | 1:20 | ❌ | 2.5 | 72.74 | 83.3 (6 folds) | 1/6 | 2 | 5 | 0 | 0 |
| Lamina 0.3.0 (Folded) | table | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| Lamina 0.3.0 (Folded) | table | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| Lamina 0.3.0 (Folded) | sofa_curved | 1:10 | ❌ | 0.0 | 100.0 | 100.0 (6 folds) | — | 0 | 0 | 13 | 0 |
| Lamina 0.3.0 (Folded) | sofa_curved | 1:20 | ❌ | 0.0 | 100.0 | 100.0 (6 folds) | — | 0 | 0 | 13 | 0 |
| Ours v4.2.4 (negative control) | chair | 1:10 | ❌ | 0.0 | 100.0 | 62.5 (8 folds) | 6/6 | 0 | 0 | 2 | 0 |
| Ours v4.2.4 (negative control) | chair | 1:20 | ❌ | 0.0 | 100.0 | 62.5 (8 folds) | 6/6 | 0 | 0 | 2 | 0 |
| Ours v4.2.4 (negative control) | table | 1:10 | ❌ | 0.0 | 100.0 | 100.0 (4 folds) | 0/4 | 0 | 4 | 0 | 0 |
| Ours v4.2.4 (negative control) | table | 1:20 | ❌ | 0.0 | 100.0 | 100.0 (4 folds) | 0/4 | 0 | 4 | 0 | 0 |
| Ours v4.2.4 (negative control) | sofa_curved | 1:10 | ❌ | 0.0 | 100.0 | 62.5 (8 folds) | 6/6 | 0 | 0 | 2 | 0 |
| Ours v4.2.4 (negative control) | sofa_curved | 1:20 | ❌ | 0.0 | 100.0 | 62.5 (8 folds) | 6/6 | 0 | 0 | 2 | 0 |

## 3. Waffle (waffle_judge.py)

| Tool | Case | Scale | Pass | Ribs X+Y | Size err (mm) | Material outside solid (mm²) | Section left out % | Crossings | Interference | Slot width (mm) / target | Shallowest slot (mm) | One drop order % | Windows | Loose parts |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ours v4.3.2 | chair | 1:10 | ✅ | 4+4 | 0.0 | 0.0 | 8.32 | 16 | 0 | 1.5 / 1.5 | 2.75 | 100.0 | 0 | 0 |
| Ours v4.3.2 | chair | 1:20 | ❌ | 2+2 | 0.0 | 1608.0 | 4.11 | 4 | 0 | 1.5 / 1.5 | 11.25 | 100.0 | 0 | 0 |
| Ours v4.3.2 | table | 1:10 | ✅ | 14+8 | 0.0 | 0.0 | 7.64 | 112 | 0 | 1.5 / 1.5 | 6.0 | 100.0 | 0 | 0 |
| Ours v4.3.2 | table | 1:20 | ❌ | 7+4 | 0.0 | 1574.0 | 7.26 | 28 | 0 | 1.5 / 1.5 | 3.0 | 100.0 | 0 | 0 |
| Ours v4.3.2 | sofa_curved | 1:10 | ✅ | 18+8 | 0.0 | 0.0 | 7.15 | 144 | 0 | 1.5 / 1.5 | 21.0 | 100.0 | 0 | 0 |
| Ours v4.3.2 | sofa_curved | 1:20 | ✅ | 9+4 | 0.0 | 0.0 | 7.15 | 36 | 0 | 1.5 / 1.5 | 10.5 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | chair | 1:10 | ✅ | 4+4 | 0.0 | 0.0 | 8.32 | 16 | 0 | 1.5 / 1.5 | 2.75 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | chair | 1:20 | ❌ | 2+2 | 19.75 | 0.0 | 4.08 | 4 | 0 | 1.5 / 1.5 | 1.38 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | table | 1:10 | ✅ | 14+8 | 0.0 | 0.0 | 7.64 | 112 | 0 | 1.5 / 1.5 | 6.0 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | table | 1:20 | ❌ | 7+4 | 31.5 | 0.0 | 7.25 | 28 | 0 | 1.5 / 1.5 | 3.0 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | sofa_curved | 1:10 | ❌ | 18+8 | 0.0 | 0.0 | 6.74 | 144 | 12 | 1.5 / 1.5 | 21.0 | 91.7 | 6 | 0 |
| Lamina 0.3.0 (Interlocked) | sofa_curved | 1:20 | ✅ | 9+4 | 0.0 | 0.0 | 7.15 | 36 | 0 | 1.5 / 1.5 | 10.5 | 100.0 | 0 | 0 |

Our 1:20 chair and table are marked ❌ only because our generator **deliberately thickens** legs and posts to a cuttable minimum (7 mm on paper), which puts material outside the true half-scale solid (1 608 and 1 574 mm²). Lamina keeps the true 3.5 mm legs at 1:20; its ribs then fall between the legs, so the assembled chair is 22.75 mm tall instead of 42.5 mm (size error 19.75 mm) and the table 6 mm instead of 37.5 mm (31.5 mm). Lamina's own log reports only "model coverage 72 %" (chair) and "82 %" (table). Our thickening is a design trade-off; Lamina's result is a failed model.

## 4. Tracing (VTracer 0.6.15 vs ours; `vtracer/results.md`)
- **Clean silhouettes (chair, sofa):** VTracer is more accurate. IoU 0.9993–0.9998 and area error ≤ 0.07 %; ours IoU 0.9945–0.9960 and area error −0.37 to −0.52 %, Hausdorff 0.16–0.25 mm against VTracer's 0.04–0.05 mm. Our consistent under-estimate fits an outline drawn through pixel centres, half a pixel (0.05 mm on paper at 10 px/mm) inside the true edge; the gap on paper is below cutting accuracy, but it is a real accuracy difference.
- **Photo-like chair:** ours (UI default) is best, IoU 0.9942 against 0.9912 (VTracer best effort), area error −0.34 % against +0.89 %.
- **Room picture H14:** VTracer has no gate. Ours with the UI default (Remove background) outlines the card's inner frame; from v4.3.2 the new frame test **warns** (78 % of the outline is paper, 69 separate lines inside). Ours with "Dark on light" outlines the red circle and cross around the chair; no rule fires there. In both runs printing stays blocked until the student ticks "only the furniture", so a human check is still required.

## 5. Decision per case (rule of TOOLS_INTEGRATION_PLAN.md §6, fixed before any result)
Adopt a tool's output only if it is no worse than ours on M1–M4, better on at least one **physical** metric, introduces no new failure type, its licence allows the use, and the version is pinned. A tie keeps ours.

| Case | Best other tool (geometry) | Versus ours | Decision |
|---|---|---|---|
| Chair Fold & Glue | PolyZamboni passes 1:10 and 1:20 | tie on M1–M4; needed 2 manual mesh steps; no physical data | **keep ours** (tie) |
| Table Fold & Glue | Lamina (Folded) passes 1:10 and 1:20; PolyZamboni passes 1:20 | tie; PolyZamboni gives no A3 net at 1:10 (one piece that does not split); Lamina adds 9 flat score lines | **keep ours** |
| Curved sofa Fold & Glue | PolyZamboni passes 1:20; nothing else passes at 1:10 on A3 | no A3 output at 1:10 (Export Paper Model, PolyZamboni) or 13 panels printed side inward (Lamina) | **keep ours** |
| Waffle | Lamina equals ours on chair and table at 1:10 and on the sofa at 1:20; fails chair and table at 1:20 (legs missed) and the sofa at 1:10 (12 interferences, 6 windows) | worse | **keep ours** |
| Tracing | VTracer: more accurate on clean silhouettes (area error ≤ 0.07 % against −0.37 to −0.52 %) | better on one geometry metric; worse on the photo; no gate; no physical metric | **keep ours**; VTracer is a candidate for a staff-side cross-check |

**RQ1–RQ3 for these pinned versions and cases:** no general-purpose generator beat ours; PolyZamboni and Lamina tied with it on some cases. RQ4 (physical buildability) is open until D8.

## 6. Findings and their status
| ID | Finding | Status |
|---|---|---|
| F1 | Curve offsets stored in paper mm: the same preset rose 20 cm at 1:10 and 40 cm at 1:20 | **fixed in v4.3.2** (offsets in real cm). The research export had compensated by hand (× 0.5 at 1:20); v4.3.2 now gives the same geometry without it, file for file |
| F2 | B2 RIGHT not mirrored: one side glued printed side inward | fixed in v4.3.1 |
| F3 | Room/background gate silent on H14 | **fixed in v4.3.2 for a frame around a drawing**; still silent when the outline is a symbol around the furniture (H14, Dark on light) |
| T1 | Our verifier placed side profiles by rule, so it could not see F2 | **fixed in v4.3.2**: sides placed printed side out; fails v4.3.0 and v4.2.4 on F2, passes v4.3.1/v4.3.2 |
| Method | General unfolders assume one consistently oriented surface. Our designs print the seat up and the back to the rear: Export Paper Model mislabels one fold (chair, sofa), Lamina mislabels one fold on the chair and prints 13 sofa panels inward, PolyZamboni refuses until one edge is split | design observation |

**Corrections to the earlier text (24 Oct, afternoon version):**
1. Tracing accuracy: "VTracer more accurate on clean images by < 0.1 % area" (and "0.05 %" in the handover) was wrong. The gap is 0.35–0.45 percentage points of area error (chair 0.44–0.45, sofa 0.35) and 0.004–0.005 in IoU.
2. "Ours under-measures area by 0.4–0.5 %, i.e. about 0.05 mm on paper": the measured range is 0.34–0.52 %, and 0.05 mm is the edge inset that explains it, not the area error itself.
3. Waffle decision: "Lamina … fails at 1:20" was too broad. Lamina's sofa passes at 1:20; it fails chair and table at 1:20 and the sofa at 1:10.
4. Method: the curved sofa's arched back applies to Fold & Glue only; the Waffle sofa target is 80 cm tall with no arch. This was in `models_report.json` but not in the text.
5. "Export Paper Model and Lamina mislabel one fold each": true for the chair; on the sofa Lamina's fault is 13 panels printed inward, with no fold mislabelled.
6. The table's "score lines with no flap" column is not where Lamina's 9 extra lines appear; they are flat (0°) score lines, a separate judge field.
7. F3 was described as open; the frame case is fixed in v4.3.2 (section 4). F1 was described as "changes stamps"; it does not: stamps hash the sheet's contents line, which has no curve.

## 7. Limits (state these in any write-up)
- **Built-in advantage for our tool.** The Fold & Glue targets were made from our own v4.3.0 nets folded by `tests/fold_verify.js`, and the tracing ground truth is our own B1 polygon. Our 0.0 mm size error and 100 % coverage therefore hold by construction; the targets test "can another tool make *this* design", not which tool designs furniture better. A neutral target (for example a measured catalogue chair) is needed before any claim of general superiority.
- **Judges written with knowledge of our faults.** Both judges were written by the team that built our tool, after F1–F2 type faults were known. The negative control shows they catch known faults; it does not show they catch unknown ones.
- **Small sample.** Three cases, two scales, one sheet size, one run per tool (deterministic: re-runs gave identical files). No uncertainty can be attached to pass/fail counts.
- **Geometry only.** Zero card thickness; only the final folded state is checked (no swept-motion or collision check during folding); no glue, tolerance or paper behaviour.
- **Pinned versions only.** Lamina is an early alpha by its author's own description; results may change with later versions.
- **Tracing:** two clean synthetic silhouettes, one synthetic photo-like case and one drawn room picture. The F3 thresholds (fill share ≥ 0.5, ≥ 25 inner lines) were set on 11 cases including H14 itself, so they are not tested on unseen pictures.
- **No physical or student data yet** (D8, B2–B11).
