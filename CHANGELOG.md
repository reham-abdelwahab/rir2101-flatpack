# Changelog

## v4.2.2 — 2026-10-24 (Waffle locked below 1.5 mm board, after the first paper test)
- Why: Reham's first E1 try used 600 gsm card in slots drawn for 1.5 mm board, and the joints were loose. Paper and Bristol card are too thin and too flexible for a waffle; the tool can only size the slot from the thickness chosen in A.
- **Lock.** With material under 1.5 mm, the Waffle button and "Waffle from the outline" are greyed out and refuse with an EN/AR message; a note under the build methods explains why. Choosing Waffle no longer raises the material silently to 1.5 mm.
- **Guard.** While any piece uses Waffle, choosing 0.5 mm Bristol or a custom thickness under 1.5 mm is refused (the board stays as it was). A Waffle piece on thin board (for example from an old Help Code) shows a red check, so it cannot reach printing unnoticed.
- **Guidance.** The material list says "Bristol Card (Fold & Glue only)" and "Maquette Carton (Fold or Waffle)". The Waffle panel names the board to cut ("Cut the ribs from 1.5 mm board … never paper", EN + AR). The printed assembly note reads "▲ = TOP edge · board 1.5 mm, not paper". Guide M-waffle and handout H11 carry the rule; M-waffle no longer says "no glue", which contradicted the H11 tip.
- No geometry changes: all 20 waffle cases (5 types × 1:10/1:20 × laser/hand) give identical cut paths and sheet counts to v4.2.1. The handout is still 3 A4 pages, regenerated under the same filename.
- Tests: `tests/regress.html` replaces "Switching a piece to Waffle sets 1.5 mm board" with 5 lock checks. 90 / 90 pass against the v3.4 baseline.

## v4.2.1 — 2026-10-20 (assembly tip after the independent v4.2 re-audit)
- H11 now carries a bilingual tip, shown in the waffle build strip and on handout page 2: "Table: assemble upside down on a flat bench, with the tabletop edges resting on the bench. Chair: secure the two middle ribs with a small dot of glue at their joints." The Arabic text is next to it.
- Why: the middle X-ribs of the chair (seat band) and the table (tabletop band) do not reach the floor. A Y-rib rests on an X-rib, so these ribs are held only by friction or glue. This is correct geometry, but it needs the tip. Paper test E1 confirms the physical stability.
- No geometry changes. The handout is still 3 A4 pages, and `RIR2101_FlatPack_Student_Handout_v4_0_1.pdf` was regenerated.

## v4.2 — 2026-10-20 (waffle sofa + cabinet; see docs/v4_2_HANDOVER.md)
- **K · Sofa.** The ribs are now exact sections of a union of boxes: seat block, two arms and back. Previously, side × front left a void under the back: the boards collided at 28 crossings at 1:10 and 7 at 1:20, there were windows, and parts hung free. Now 1:10 gives 26 parts and 144 joints, and 1:20 gives 13 parts and 36 joints. `waffleSilhouettes` can return `xSection(x)` / `ySection(y)`, and `waffle()` uses them for the ribs and the crossing table.
- **L · Cabinet.** The toe recess now stops (t + k)/2 + 0.5 mm short of the outer rib positions. At 1:10 it is 3.25 mm (3.15 mm hand-cut), so X1 and X12 stand on the floor and all 60 joints assemble.
- **M · Validation.** `waffleValidate` now checks for drop assembly:
  - it probes the centre and both faces of every slot;
  - in every rib pair, all X material must lie below all Y material ("closed slot at Xi/Yj");
  - a hole that a slot touches is an error ("window at Xi/Yj");
  - an X-part must stand on the floor wherever the solid under its board does ("X3b does not stand on the floor");
  - every part must connect to the rest ("N parts not connected to the rest").
- **M · Tests.** `tests/regress.html` has an independent drop-assembly check, computed from the rib polygons rather than by the tool's own validator, for 5 archetypes × 1:10/1:20 × laser/hand. Its negative cases, the v4.1 sofa and the v4.1 cabinet recess, must fail; they reproduce the audit's 28 / 2 holes and 8 / 2 off the floor. 86 checks.
- **O.** The TA verify dropdown options now read "Furniture sheet" and "Image trace sheet". The values `cut` / `image` are unchanged, so older stamps still verify.
- **P.** Corrected the v4.1 line below (112 of 172 crossings).
- Fold & Glue, From-image, nets, score lines, fold rule, counts and stamps are unchanged. The handout PDF was regenerated under the same filename.

## v4.1 — 2026-10-20 (audit of fold lines and waffle slots + teaching review; see docs/v4_1_AUDIT.md)
- **A · Waffle ribs are sections of the solid.**
  - X-rib_i = S_side ∩ band(z ∈ F(x_i)), and the same for Y-ribs. Before this, legs below a seat or a backrest above it closed the slot into a window. For example, at 1:10 the sofa had 112 of 172 crossings closed. Now 0 slots are closed in 5 archetypes × 1:10/1:20 × laser/hand-cut.
  - A rib that splits becomes parts X3a, X3b …. Parts with no slot are dropped and reported as "N unsupported fragments removed".
  - `waffleValidate` adds the rule "every slot must reach the rib edge" (error: "closed slot at Xi/Yj").
- **B · Fold rule** in English and Arabic on every Fold & Glue sheet and in the H08 caption: printed side out · score on the print · all blue lines fold away from you.
- **C · No change.** The only grey line on the bed and cabinet nets marks where the headboard is glued to the back wall. It is not a fold, and the real folds were already blue. Making it blue would tell students to fold the headboard.
- **D · Tests.** No score line lies outside material (with a negative case). No closed slot in any archetype × scale × kerf. The checker also reproduces the audit's closed slots in the old copy-ribs.
- **E · One scale, one sheet, one output path.** The image tracer follows the project scale and sheet from A, and its separate Print and Laser SVG buttons are removed. Traced pieces print only through PRINT & BUILD.
- **F · Counts.** For example "2 furniture types · 5 models · 13 cut-out parts · 1 A4 sheet", shown in the pieces list, on each sheet and in the parts list. Every part carries its furniture id: CH1-A1 BACK, TB1-…, CH1-X3a.
- **G · Image limits.** H15 says that a traced picture gives one flat profile, not a complete model, and that size comes from the Neufert table. The Prompt B note says that AI-inferred elevations are interpretations to check against measured dimensions. The From-image caption now describes the steps.
- **H.** The help text no longer says "upload to Tab 3"; it says MAKE → Add piece → From image. The broken "prompts" button in the tracer now opens Help · G.
- **I · Defaults.** Fold & Glue starts on 0.5 mm Bristol, so no warning appears on first open. Waffle switches the board to 1.5 mm. The tolerance, simplify and rib-spacing sliders are under "Advanced", and every slider has a numeric box next to it.
- **J · Wording.** Material use is labelled "≈ … % (estimate: parts ÷ sheet area)", and parts are described as "packed", not as an optimal layout.
- The handout PDF `RIR2101_FlatPack_Student_Handout_v4_0_1.pdf` was regenerated from v4.1 under the same filename.

## v4.0.1 — 2026-10-20
- Credits are English only. The Arabic credit line is removed: in `COURSE_TEAM`, `instructorAr` and `tasAr` are empty and `teamLineAr()` returns an empty string, and no empty row is left where it was. The English credits are unchanged.
- Revised Arabic captions:
  - H16: «واجهت مشكلة؟ أرسل رمز المساعدة إلى فريق التدريس.»
  - I1: «للمدرّس: طابق ختم VERIFY مع القيم المطبوعة.»

## v4.0 — 2026-10-20 (redesign after Reham's v3.6 print test)
- **C1 Waffle (laser):** replaces the old table leg-frame slots, which did not work.
  - JavaScript port of `waffle.py`: a grid of X-ribs (side elevation) and Y-ribs (front elevation). Where they cross, the X-rib is slotted half-depth from the top and the Y-rib from the bottom.
  - Rib spacing slider (6–15 mm), laser or hand-cut (+0.2 mm) kerf, an isometric assembly drawing on the sheet, and a ▲ marking the top edge of every rib.
  - Validation must pass before printing: slot = board + kerf, web ≥ 2 × board, top/bottom slots meet at mid-height, rib count × board fits the piece.
  - Silhouettes for chair, sofa, bed, table and cabinet. The bookcase keeps its notches. A traced image can also be built as a waffle.
- **C3 Thin lines:** printed sheets use a 0.2 mm cut line, a 0.15 mm dashed score line, labels of 2 mm or smaller, and no grid. Laser SVGs use the `LASER_STROKE` 0.01 mm hairline with a continuous score line. Measured at 600 dpi: 0.19 mm.
- **C2 Nesting:** all parts of all pieces are packed on as few A4/A3 sheets as possible.
  - The packer places the tallest parts first, with a 3 mm gap. Parts stay upright and turn 90° only when that makes them fit.
  - Every sheet has its number ("Sheet n / N"), a parts list, material use, the 50 mm ruler, a title block and its own stamp.
  - A bed base or cabinet whose cross-shaped net is bigger than the sheet becomes a wall strip plus a separate top, at the same true scale.
  - Acceptance test E2 (bed + 2 bedside tables + wardrobe at 1:20) fits on 2 A4 sheets.
- **B Three tabs:** MAKE / اصنع, PRINT & BUILD / اطبع وابنِ and HELP / مساعدة, with icons T1/T6/T7 and progress dots A–E.
  - Pieces list with a piece editor: type, real cm, quantity, and Fold & Glue / Waffle / From image.
  - The instructor tools are collapsed in Help · I.
  - The Help Code now carries every piece, and the TA verify box checks the stamps of nested sheets.
- **F Picture-led help:** steps show pictures P01–P08 and step icons. Build strips appear only for the methods used. The 3-page picture handout has panels H01–H16 and 6 do/don't pairs, prints as exactly 3 A4 pages, and has one line of English and one of Arabic under every picture. The Neufert table, Prompt A/B and the team credits stay.
- The pictures are inline (the file is 2.9 MB). The shared standalone copy no longer duplicates the pictures (2.95 MB).

## v3.6 — 2026-10-18
- Fully offline: the Font Awesome and Google Fonts links are removed.
  - The 37 icons the tool uses are now inline SVG masks (Font Awesome Free 6.4.0, CC BY 4.0). The `<i class="fa-…">` markup is kept, so the JavaScript did not change.
  - Fonts now fall back to local fonts: Segoe UI / system-ui for text, and Cascadia Mono / Consolas / Menlo for monospace.
- There are no other changes. The geometry, stamp and Help Code are the same as in v3.5.

## v3.5 — 2026-10-18
- Verification stamp `VERIFY: XXXX-XXXX · v3.5` on every Tab 1 and Tab 3 title block, in the `03_LABELS_BLACK` layer.
  - The stamp is the first 8 base32 characters of SHA-256(version | name | ID | piece | dimensions | scale | sheet | board | joinery | salt).
  - The hashed values are printed next to the stamp so that a TA can re-type them from paper.
- The Help Code now carries the stamp and the tool version. Restoring a code warns if the stamp no longer matches.
- New "Verify a sheet" box in Share & Troubleshoot: fill it from a Help Code or type the values from the sheet, and it shows ✔ or ✘.
- The stamp deters tampering but is not cryptographic proof. See the README.

## v3.4 — 2026-10-18
- Course team credits in the header, in both title blocks (2-line credit row) and in the handout footers.
- File copied to the A313 course folder and published on GitHub Pages.
- `TOOL_VERSION` constant added and printed in the app header and the title-block credit row.

## v3.3
- Bilingual EN|AR guidance strips in all 21 sections, with a toggle. Print-fitted: the handout still prints as 3 pages.

## v3.2
- Handout page 3 with Prompt A (generate) and Prompt B (convert my image); copy buttons in Tab 3.

## v3.1
- Tracer retuned for AI renders: background region-growing, shadow rejection, clean-edges slider, colour picker, AI prompt copy.

## v3
- New Image → Cut Sheet tab: calibrate, auto/hand trace, nesting, panels, print/SVG.

## v2
- Fixed all the v1 issues below.
- True-scale geometry with glue tabs, and a real fit check.
- Offline Tailwind.
- New validation rules: thick board on a small fold, and a slot on a non-slot archetype.
- Tests 1 and 4 now use 0.5 mm Bristol.

## v1 — 2026-10-18 (original)
Known issues, all fixed in v2:
- Fold lines hidden under the panels.
- Glue tabs cut into the seat.
- Silent clamping: a 1:20 bed printed at about 1:24.
- Tailwind loaded from a CDN.
- A sample student name in the shipped copy.
- LaTeX in the handout.
- NaN on an empty scale.
- The background grid exported to the laser file.
