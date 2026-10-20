# Flat-Pack Maker v4.0.1 — independent audit of fold lines and waffle slots (20 Oct 2026)

Question from Reham: how do we verify that fold lines are in the right position and direction, and that waffle notches have the right size, location and number?

Method: Playwright (Chromium, network blocked) loads the live `index.html` (v4.0.1), calls the tool's own functions (`waffleForPiece`, `waffleSilhouettes`, `#print-test=e2` sheets) and the rib polygons / score lines are checked with an independent Python geometry library (shapely). The checker is NOT the tool's `waffleValidate`, so the tool is not grading itself. Scripts: Cowork container `/home/claude/v401/audit.py, audit4.py, audit7.py`; the reproduction in audit7.py is also the reference for the fix below.

## 1. Fold lines (Fold & Glue method) — PASS
- E2 sheets (bed + 2 bedside + wardrobe, 1:20, 2 × A4): every blue score segment lies inside a red cut face; none lies outside material (0 outside, 0 on an outer edge).
- Score layer prints as 0.15 mm dashed (1.2 / 0.9 mm), cut 0.18–0.2 mm.
- Direction: the tool draws nets with the printed face OUT and all glue tabs outward, so every blue line is a mountain fold: **score on the printed side, fold away from you**. There are no valley folds in the shipped nets. This rule is not yet written anywhere in the tool → task for Code (section 4).
- One cosmetic item carried over: back-wall ↔ top fold on the bed/cabinet strip is drawn as a grey guide in `03_LABELS` instead of blue in `02_SCORE_BLUE`.

## 2. Waffle slots — what is correct in v4.0.1
Checked 5 archetypes × 1:10 / 1:20 × laser (k = 0) / hand (k = 0.2), t = 1.5 mm, s = 10 mm:
- **Width**: every slot measures exactly t + k (1.50 laser / 1.70 hand). ✔
- **Number**: exactly one slot on the X-rib and one on the Y-rib per crossing (e.g. chair 1:10: 16 crossings → 16 + 16 slots; bed 1:10: 320 → 320 + 320). ✔
- **Location**: slot centres sit exactly on the rib positions `xs` / `ys` (margin max(3t, 4) = 4.5 mm, pitch ≈ 10 mm). ✔
- **Depth**: the two slots of a crossing meet exactly at the midpoint of the common z-interval (chair 16/16, table 112/112, bed 320/320). ✔
- **Direction**: X-ribs (side profile) slotted from the top, Y-ribs (front profile) from the bottom, as specified. ✔

## 3. Waffle — one real defect (spec error, inherited from waffle.py)
Ribs are copies of the whole silhouette, but the slots are cut only over the common z-interval of the crossing. Wherever a rib has material beyond that interval (a leg below the seat, a backrest above it), the slot becomes a **closed window** instead of an open notch, and that crossing cannot be assembled by sliding.

Closed slots found in v4.0.1 (t = 1.5, s = 10):
| piece | 1:10 | 1:20 |
|---|---|---|
| chair | 4 of 16 Y-slots | 0 |
| sofa | 112 of 172 X-slots | 28 of 43 X-slots |
| table | 12 of 112 Y-slots | 4 of 28 |
| bed | 0 | 0 |
| cabinet | 12 X + 10 Y of 60 | 0 |

Picture: `waffle_audit_chair.png` (Y2 rib: window at the front legs vs open slot after the fix).

**Fix (verified in Python, 0 closed slots on all 10 cases):** make each rib a *section* of the solid, not a copy of the silhouette.
```
F(x)  = z-intervals of S_front at x          Sd(y) = z-intervals of S_side at y
X-rib_i = S_side  ∩ band(z ∈ F(x_i))          (then slots from top as now)
Y-rib_j = S_front ∩ band(z ∈ Sd(y_j))         (then slots from bottom as now)
```
`band` = union of full-width rectangles over those z-intervals. Consequences to handle in the JS port:
1. A rib may split into several parts (sofa 1:10: 26 ribs → 60 parts). Label them X3a, X3b … and send every part through the nester.
2. A part with zero slots is floating → drop it and count it in the validation report (“N unsupported fragments removed”).
3. `waffleValidate` must add the test that caught this: *every slot must reach the rib's edge at that coordinate* (X: removed interval top == material top; Y: removed bottom == material bottom). Fail = “closed slot at Xi/Yj”.
4. Keep the 3t minimum on common intervals; thin seat strips (chair 1:10 → 5.5 mm strip, 2.75 mm slots) are accepted, at 1:20 they are dropped automatically.
5. Re-run the acceptance print E1 (table 1:10) only after this fix.

## 4. Tasks for Code (v4.1)
Sources: this audit (A–D) + the external teaching review `A313\Flatpack-v4.0.1-test-report.md` (E–J), 20 Oct 2026.
A. Section ribs as above + validation rule + part labels (X3a…) + fragment removal.
B. Print the fold rule on every Fold & Glue sheet and in H08's caption: EN “Printed side out · score on the print · all blue lines fold away from you” · AR “الوجه المطبوع للخارج · خطّ التحزيز على الطباعة · كل الخطوط الزرقاء تُطوى بعيداً عنك”.
C. Move the back-wall↔top fold to `02_SCORE_BLUE`.
D. Add the two checks to `tests/regress.html`: (i) no score segment outside material, (ii) no closed slot in any archetype × scale × kerf.
E. **One scale / one sheet / one output path.** Remove the image editor's own 1:20/A4 setting and its Print / Laser SVG buttons; the traced profile is a normal piece and prints only through PRINT & BUILD at the project scale (or label an image-only export “Separate image-only sheet · 1:20 A4” in red if it must stay).
F. **Counts.** Replace “2 pieces” with “2 furniture types · 5 models · 13 cut-out parts · 1 A4 sheet” everywhere (pieces list, sheet header, parts list). Part labels carry the furniture id: CH1-B1, CH2-B1 … TB1-TOP.
G. **Image limitation line** on the From-image step and in H15's caption: EN “A traced picture gives ONE flat profile (a rib or a panel) — not a complete model. Size comes from the Neufert table, never from the picture.” · AR “الصورة المتتبَّعة تعطي مقطعاً مسطحاً واحداً فقط (ضلع أو لوح) وليس نموذجاً كاملاً. المقاس من جدول نويفرت وليس من الصورة.” In Prompt B's note: AI-inferred elevations are interpretations — check every feature against measured dimensions.
H. Help text “upload to Tab 3” → “MAKE → Add piece → From image”.
I. Fold & Glue default board = 0.5 mm Bristol (no warning on first open); waffle default stays 1.5 mm. Tolerance / simplification / rib-spacing sliders go under “Advanced” with a numeric box next to each slider.
J. Material-use % label → “estimate (parts ÷ sheet area)”; nesting described as “packed”, not “optimal”.
K. Done in Cowork today, no action: Google Sites button now says v4.0.1 and links to `RIR2101_FlatPack_Student_Handout_v4_0_1.pdf` (3-page picture handout generated from the tool's own print view and pushed to `main`, commit bb12cf2). Regenerate the PDF after v4.1 and overwrite the same filename.

## 5. Paper verification protocol (for Reham / TAs, 10 minutes)
1. Print at 100 %, ruler on the 50 mm bar = 50.0 mm.
2. Caliper one slot: width must equal board thickness (+0.2 mm if hand-cut). Width is printed on the sheet as “slot 1.50 mm”.
3. Count: slots on one X-rib = number of Y-ribs, and vice versa (numbers are printed in the sheet header).
4. Dry-fit the first X-rib with the first two Y-ribs (no glue): they must slide fully until the two slot bottoms touch — if a rib stops half-way the slot is closed or too shallow.
5. Fold nets: hold the sheet printed side towards you, score every blue line with the back of the knife, fold every line away from you; tabs end up inside.
