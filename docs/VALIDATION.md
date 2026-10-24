# Validation — Studio Flat-Pack Maker v4.3.0-preview.1 (testing version)

*RIR2101 Interior Design 1 · 24 October 2026 · for the paper on the tool*

A convincing picture proves nothing on its own. Each build method needs three separate proofs. This file states what is proven, how, and what is still open.

| Proof | Fold & Glue | Waffle | Status (v4.3) |
|---|---|---|---|
| **1 · Geometry** | score lines inside material; nets fit the sheet; 1:1 print | no interference, no closed slots, slot = board + kerf + fit, connected parts | ✅ both |
| **2 · Assembly** | the **exported** net folds to the target W × D × H; every tab lands on a face; no overlap; one fold rule | an insertion order for every rib; every part that would hang has a retention method; finished size | ✅ both (zero board thickness) |
| **3 · Physical build** | students build the printed sheet without corrective cuts | E1, FIT TEST, lift-and-place cycles | 🧪 studio tests pending |

## 1. Geometry (unchanged method, re-run on v4.3)
- Waffle: 20 cases (chair, sofa, table, bed, cabinet × 1:10 / 1:20 × laser / hand-cut). `waffleValidate` plus the independent drop-assembly check in `testing/tests/regress.html` (polygon-clipping only): 0 interference, 0 holes, one connected grid, X-parts on the floor. Rib geometry is byte-identical to v4.2.2 in 20 / 20 cases.
- Fold & Glue: score lines inside material and not on cut edges; true scale kept by the packer; 1:1 print checked by the 50 mm ruler, a vertical 50 mm ruler and the ID-card edge (85.6 mm).
- Regression: 112 / 112 checks (Chromium, Linux, v3.4 baseline hosted in `testing/tests/`).

## 2a. Assembly proof — Fold & Glue (`testing/tests/fold_verify.js`)
**Method.** The verifier reads only the printed sheet SVGs: red cut paths, blue score lines and part labels, with all packer transforms. For each part it (1) splits the outline into faces along the score lines, (2) builds the hinge graph, (3) searches the fold directions (±90° per hinge) that bring the main part to its target size, with the base panel at its height above the floor, (4) places separate parts by the stated rule (side profiles in the planes x = 0 and x = W with the tall post under the back; the chair back on the seat's rear edge, printed side to the rear; a separate top on the walls; the bed headboard on the back wall), (5) folds every glue tab and requires ≥ 95 % of its area to lie flat on a face of the model, and (6) checks that no two panels overlap. "Mountain" means away from the printed side, as the sheet rule says; a net passes only if **every** fold is a mountain fold. Zero board thickness is assumed.

**Results.** 22 nets: 5 types × 1:10 / 1:20, plus arched and sloped tops for chair, sofa and bed.

| Net | Parts | Hinges | Tabs mated | Assembled size (mm) | v4.3 | v4.2.3 (same test) |
|---|---|---|---|---|---|---|
| chair 1:10 · flat | 4 | 7 | 6/6 | 45 × 45 × 85 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK → B1 LEFT |
| chair 1:10 · arched | 4 | 7 | 6/6 | 45 × 45 × 105 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK → B1 LEFT |
| chair 1:10 · sloped | 4 | 7 | 6/6 | 45 × 45 × 100 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK → B2 RIGHT |
| chair 1:20 · flat | 4 | 7 | 6/6 | 22.5 × 22.5 × 42.5 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK → B1 LEFT |
| chair 1:20 · arched | 4 | 7 | 6/6 | 22.5 × 22.5 × 62.5 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK → B1 LEFT |
| chair 1:20 · sloped | 4 | 6 | 5/5 | 22.5 × 22.5 × 57.5 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK |
| sofa 1:10 · flat | 4 | 7 | 6/6 | 180 × 85 × 80 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK → B1 LEFT |
| sofa 1:10 · arched | 4 | 7 | 6/6 | 180 × 85 × 100 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK → B1 LEFT |
| sofa 1:10 · sloped | 4 | 7 | 6/6 | 180 × 85 × 95 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK → B2 RIGHT |
| sofa 1:20 · flat | 4 | 7 | 6/6 | 90 × 42.5 × 40 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK → B1 LEFT |
| sofa 1:20 · arched | 4 | 7 | 6/6 | 90 × 42.5 × 60 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK → B1 LEFT |
| sofa 1:20 · sloped | 4 | 6 | 5/5 | 90 × 42.5 × 55 | ✅ | ❌ A1 BACK: BACK–SEAT; A1 BACK tab on BACK |
| table 1:10 · flat | 1 | 8 | 4/4 | 80 × 140 × 75 | ✅ | ❌ TABLE TOP (140.0×80.0 mm) tab on RIGHT LEG; TABLE TOP (140.0×80.0 mm) tab on RIGHT LEG |
| table 1:20 · flat | 1 | 8 | 4/4 | 70 × 40 × 37.5 | ✅ | ❌ TABLE TOP (70.0×40.0 mm) tab on RIGHT LEG; TABLE TOP (70.0×40.0 mm) tab on RIGHT LEG |
| bed 1:10 · flat | 2 | 8 | 4/4 | 160 × 200 × 110 | ✅ | ✅ |
| bed 1:10 · arched | 2 | 8 | 4/4 | 160 × 200 × 130 | ✅ | ✅ |
| bed 1:10 · sloped | 2 | 8 | 4/4 | 160 × 200 × 125 | ✅ | ✅ |
| bed 1:20 · flat | 2 | 8 | 4/4 | 80 × 100 × 55 | ✅ | ✅ |
| bed 1:20 · arched | 2 | 8 | 4/4 | 80 × 100 × 75 | ✅ | ✅ |
| bed 1:20 · sloped | 2 | 8 | 4/4 | 80 × 100 × 70 | ✅ | ✅ |
| cabinet 1:10 · flat | 1 | 8 | 4/4 | 120 × 50 × 80 | ✅ | ✅ |
| cabinet 1:20 · flat | 1 | 8 | 4/4 | 60 × 25 × 40 | ✅ | ✅ |

v4.3: **22 / 22** pass (162 hinges, 110 / 110 tabs). v4.2.3: **8 / 22** pass.

**What the verifier found and what changed.**
1. *Chair and sofa back.* Folding the back up from the seat is a valley fold, so the printed rule ("all blue lines fold away from you") was false for every chair and sofa, and the back's tabs had to fold toward the print. → The back is now a separate panel A1, drawn mirrored and glued with its printed side to the rear; its side tabs fold away from the print onto the posts.
2. *Sloped back.* A raised corner made the back tab longer than the post, so it hung in the air. → Back tabs stop at the post top.
3. *Table.* Tabs along the full leg edges met the apron only near the top. → Tabs on the four apron ends glue fully onto the legs.
A synthetic negative case (a back folded up from the seat) is reported as a valley fold in every regression run.

**Limits.** Zero thickness; only the final folded state is checked for overlap (the fold order is the breadth-first order from the base panel, not a swept-motion check); placement rules of separate parts are stated, not searched.

## 2b. Assembly proof — Waffle (`waffleAssemblyPlan`)
Pairwise drop assembly is already proven (section 1). v4.3 adds an explicit order for every rib. Parallel ribs never meet, so an order exists when every X-part is placed before the Y-ribs that cross it (upright) or the reverse (upside down). The plan picks the mode with fewer glued parts (a tie goes upside down) and names every part that would hang, with its retention method (glue at its joints). The finished size includes the outer ribs' thickness.

| Case | Parts | Joints | Mode | Parts to glue | Finished size (mm) | Shallowest slot (mm) |
|---|---|---|---|---|---|---|
| chair 1:10 laser | 8 | 16 | upright | X2–X3 | 45.0×45.0×85.0 | 2.75 |
| chair 1:10 hand | 8 | 16 | upright | X2–X3 | 45.0×45.0×85.0 | 2.75 |
| chair 1:20 laser | 4 | 4 | upright | — | 22.5×22.5×42.5 | 11.25 |
| chair 1:20 hand | 4 | 4 | upright | — | 22.5×22.5×42.5 | 11.25 |
| sofa 1:10 laser | 26 | 144 | upright | — | 180.0×85.0×80.0 | 21.00 |
| sofa 1:10 hand | 26 | 144 | upright | — | 180.0×85.0×80.0 | 21.00 |
| sofa 1:20 laser | 13 | 36 | upright | — | 90.0×42.5×40.0 | 10.50 |
| sofa 1:20 hand | 13 | 36 | upright | — | 90.0×42.5×40.0 | 10.50 |
| table 1:10 laser | 22 | 112 | upside-down | X2–X13 | 140.0×80.0×75.0 | 6.00 |
| table 1:10 hand | 22 | 112 | upside-down | X2–X13 | 140.0×80.0×75.0 | 6.00 |
| table 1:20 laser | 11 | 28 | upside-down | X2–X6 | 70.0×40.0×37.5 | 3.00 |
| table 1:20 hand | 11 | 28 | upside-down | X2–X6 | 70.0×40.0×37.5 | 3.00 |
| bed 1:10 laser | 36 | 320 | upright | — | 160.0×200.0×110.0 | 19.00 |
| bed 1:10 hand | 36 | 320 | upright | — | 160.0×200.0×110.0 | 19.00 |
| bed 1:20 laser | 18 | 80 | upright | — | 80.0×100.0×55.0 | 9.50 |
| bed 1:20 hand | 18 | 80 | upright | — | 80.0×100.0×55.0 | 9.50 |
| cabinet 1:10 laser | 17 | 60 | upright | — | 120.0×50.0×80.0 | 40.00 |
| cabinet 1:10 hand | 17 | 60 | upright | — | 120.0×50.0×80.0 | 40.00 |
| cabinet 1:20 laser | 8 | 12 | upright | — | 60.0×25.0×40.0 | 20.00 |
| cabinet 1:20 hand | 8 | 12 | upright | — | 60.0×25.0×40.0 | 20.00 |

Every part has a step; every part that would hang has a stated retention method; the finished size equals the target W × D × H in all 20 cases. Hand-cut slots under 4 mm deep (table 1:20, chair 1:10 seat band) carry a warning.

## 3. Physical validity — still open (studio)
| Test | Answers | Sheet |
|---|---|---|
| **FIT TEST strip** (every Waffle / bookcase sheet) | which slot (−0.1 / 0 / +0.1 mm) fits the real board and cutter | on the sheet |
| **E1** table 1:10, laser and hand-cut; upside down; turn upright; 5 lift-and-place cycles | do glued X2–X13 hold? real kerf? | `testing/tests/prints/E1_table_1-10_waffle_*_v4_3.pdf` |
| **1:20 hand-cut** table / chair | does the web under a 3 mm slot split? (sets the 4 mm threshold) | from the tool |
| **Class trial** 4 chairs + 1 table, 1:20, 0.5 mm Bristol | do students build the new chair back and the table tabs without corrective cuts? | `testing/tests/prints/TRIAL_4chairs_1table_1-20_fold_v4_3.pdf` |
| **Curved backs** (P3-7) flat / arched / sloped chair 1:20 | do the tabs reach and hold? | `testing/tests/prints/P3-7_curved_backs_chair_1-20_A4.pdf` |
| **Template transfer**, **score coupon**, **glue timing** | paper stretch; cracking; minutes to handling strength for the class glue | — |

## Image-derived outlines
Tested: a clean elevation traces to one shape; a room-like picture is flagged ("outline fills the picture / touches three edges") with the removed fragment shown; parts cannot print until the student confirms the outline and, for a Waffle interpretation, its Neufert width. Still open: the three image cases with students (clean elevation with known size; the same with a hand-checked outline; a perspective/room photo).

## Reproduce
- Browser: `testing/tests/regress.html` (all checks, including the fold verifier).
- Headless (Linux, Chromium via Playwright): load `testing/index.html`, add `testing/tests/fold_verify.js`, call `FoldVerify.verifyModel(nestAll([piece], cfg).sheets.map(s => s.svg), id, spec, polygonClipping)`.
