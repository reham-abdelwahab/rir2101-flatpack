# Results — tool comparison D2–D7 (24 Oct 2026)

All numbers in the tables below come from `net_judge.py` / `waffle_judge.py` output files (`*.judge.json`, `*.wjudge.json`), assembled by `make_results.py`; the tracing table is `vtracer/results.md`. Tool versions are pinned in [TOOLS.md](TOOLS.md). Physical builds (D8) have **not** been done: nothing below says a model can be built by a student.

## Method in one paragraph
Three furniture cases (chair 45×45×85, table 140×80×75, curved sofa 180×85×100 incl. the arched back) at 1:10 and 1:20, A3. The same target mesh went to every tool (`models/`, built from our v4.3.0 nets folded by `tests/fold_verify.js`, checked by hand: chair 10 980 mm², table 26 560 mm²). Every export was converted by a per-tool adapter to one format ([FORMAT.md](FORMAT.md)) and scored by **one judge that knows no tool**: it folds each net back onto the target, searches the placement of every part, and checks size, coverage, fold direction against the printed marks, tab landing, overlaps and printed side on every panel. The judge was validated on a negative control: it fails the kept v4.2.4 nets for exactly the faults found earlier (back valley fold, table tabs that cannot land), and it found one fault our own verifier could not see (F2, below).

## Fold & Glue nets (net_judge.py)

| Tool | Case | Scale | Pass | M1 size err (mm) | Coverage % | M2 folds as marked % | M3 tabs land | M4 overlaps | Faces not placed | Printed side inward | Score lines with no flap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ours v4.3.1 | chair | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Ours v4.3.1 | chair | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Ours v4.3.1 | table | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| Ours v4.3.1 | table | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| Ours v4.3.1 | sofa_curved | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Ours v4.3.1 | sofa_curved | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
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

## Waffle (waffle_judge.py)

| Tool | Case | Scale | Pass | Ribs X+Y | Size err (mm) | Material outside solid (mm²) | Section left out % | Crossings | Interference | Slot width (mm) / target | Shallowest slot (mm) | One drop order % | Windows | Loose parts |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ours v4.3.1 | chair | 1:10 | ✅ | 4+4 | 0.0 | 0.0 | 8.32 | 16 | 0 | 1.5 / 1.5 | 2.75 | 100.0 | 0 | 0 |
| Ours v4.3.1 | chair | 1:20 | ❌ | 2+2 | 0.0 | 1608.0 | 4.11 | 4 | 0 | 1.5 / 1.5 | 11.25 | 100.0 | 0 | 0 |
| Ours v4.3.1 | table | 1:10 | ✅ | 14+8 | 0.0 | 0.0 | 7.64 | 112 | 0 | 1.5 / 1.5 | 6.0 | 100.0 | 0 | 0 |
| Ours v4.3.1 | table | 1:20 | ❌ | 7+4 | 0.0 | 1574.0 | 7.26 | 28 | 0 | 1.5 / 1.5 | 3.0 | 100.0 | 0 | 0 |
| Ours v4.3.1 | sofa_curved | 1:10 | ✅ | 18+8 | 0.0 | 0.0 | 7.15 | 144 | 0 | 1.5 / 1.5 | 21.0 | 100.0 | 0 | 0 |
| Ours v4.3.1 | sofa_curved | 1:20 | ✅ | 9+4 | 0.0 | 0.0 | 7.15 | 36 | 0 | 1.5 / 1.5 | 10.5 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | chair | 1:10 | ✅ | 4+4 | 0.0 | 0.0 | 8.32 | 16 | 0 | 1.5 / 1.5 | 2.75 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | chair | 1:20 | ❌ | 2+2 | 19.75 | 0.0 | 4.08 | 4 | 0 | 1.5 / 1.5 | 1.38 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | table | 1:10 | ✅ | 14+8 | 0.0 | 0.0 | 7.64 | 112 | 0 | 1.5 / 1.5 | 6.0 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | table | 1:20 | ❌ | 7+4 | 31.5 | 0.0 | 7.25 | 28 | 0 | 1.5 / 1.5 | 3.0 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | sofa_curved | 1:10 | ❌ | 18+8 | 0.0 | 0.0 | 6.74 | 144 | 12 | 1.5 / 1.5 | 21.0 | 91.7 | 6 | 0 |
| Lamina 0.3.0 (Interlocked) | sofa_curved | 1:20 | ✅ | 9+4 | 0.0 | 0.0 | 7.15 | 36 | 0 | 1.5 / 1.5 | 10.5 | 100.0 | 0 | 0 |

Notes on the Waffle rows: our 1:20 chair and table are marked ❌ only because our generator **deliberately thickens** legs and posts to a cuttable minimum (7 mm on paper), which puts material outside the true half-scale solid. Lamina keeps the true thin legs at 1:20, its ribs then fall between them, and the assembled chair is 22.75 mm tall instead of 42.5 mm (table 6 mm instead of 37.5 mm); Lamina reports only "model coverage 72 % / 82 %". Our thickening is a design trade-off to state in the paper; Lamina's result is a failed model.

## Tracing (VTracer 0.6.15 vs ours) — from `vtracer/results.md`
Clean silhouettes: VTracer IoU 0.999+, ours 0.994–0.996 (ours under-measures area by 0.4–0.5 %, i.e. about 0.05 mm on paper at 1:10, below cutting accuracy). Photo-like: ours (UI default) best, IoU 0.994 vs 0.991. Room picture H14: **neither pipeline stops by itself**; ours blocks printing only through the student's "only the furniture" tick (finding F3). A human outline check stays necessary for both.

## Decision per case (rule of TOOLS_INTEGRATION_PLAN.md §6, fixed before any result)
Adopt a tool's output only if it is no worse than ours on M1–M4, better on at least one **physical** metric, introduces no new failure type, its licence allows the use, and the version is pinned. A tie keeps ours.

| Case | Best other tool (geometry) | Versus ours | Decision |
|---|---|---|---|
| Chair Fold & Glue | PolyZamboni: passes at 1:10 and 1:20 | tie on M1–M4; needed 1–2 manual mesh steps; no physical data | **keep ours** (tie) |
| Table Fold & Glue | Lamina (Folded) and PolyZamboni 1:20 pass | tie; PolyZamboni has no A3 net at 1:10 (one piece, does not split); Lamina adds 9 flat diagonal score lines | **keep ours** |
| Curved sofa Fold & Glue | PolyZamboni 1:20 passes; nothing passes at 1:10 on A3 | others: no A3 output at 1:10 (Export Paper Model, PolyZamboni) or 13 panels printed inward (Lamina) | **keep ours** |
| Waffle (all) | Lamina equals ours at 1:10 (chair, table), fails at 1:20 and on the sofa 1:10 (12 interferences, 6 windows) | worse | **keep ours** |
| Tracing | VTracer more accurate on clean images by < 0.1 % area | better on one geometry metric, but no physical metric and no gate | **keep ours**; VTracer is a candidate for a staff-side cross-check only |

**Answer to RQ1–RQ3 for these pinned versions and cases:** no general-purpose generator beat ours; two tied on some cases. RQ4 (physical) is open until D8.

## Findings that changed our tool or our method
- **F2 (fixed in v4.3.1):** B2 RIGHT was not mirrored; one side glued printed side inward. Found by the judge, confirmed by the build-steps viewer, now in both regression suites (fails on v4.3.0).
- **F1 (open, testing):** arched-back curve offsets are stored in paper mm, so the same preset is twice as tall at 1:20.
- **F3 (open, testing):** the room/background warning did not fire on our own teaching picture H14 (outline stays inside the card frame, so neither "fills > 85 %" nor "touches 3 edges" holds).
- **Method:** `fold_verify.js` places side parts by rule; a judge must check the printed side of every panel. General unfolders assume one consistently oriented surface: our designs print the seat up and the back to the rear, which Export Paper Model and Lamina mislabel (one fold each) and PolyZamboni refuses until the edge is split.

## Limits (state in the paper)
Zero thickness; final folded state only (no swept-motion check); one target mesh per case built from our own design (fair for "given this furniture", not for free-form shapes); results only for the pinned versions; synthetic straight-edged tracing cases and one drawn room picture; no physical builds yet.
