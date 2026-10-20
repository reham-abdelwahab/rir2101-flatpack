# Studio Flat-Pack Maker v4 — redesign spec from Reham's print test (18 Oct 2026, 22:35)

Source: Reham printed v3.6 and reviewed it. Measurements on paper are correct (ruler and part sizes). Everything below is what must change. This supersedes the "optional later" list in `flatpack-tool-status-2026-10-18.md`.

## A. Defects found in the print test
1. **Slot (notch) joinery is wrong.** The two "leg frames" with half-slots do not form a joint that works, and they are not geometrically related to the table top they come with (the top has no slots/mortises to receive them; frame lengths do not match the top). The whole slot joinery module must be re-derived, not patched.
2. **Line weight too heavy on paper.** Cut (red) and score (blue) lines print thick, which blurs the cut edge. Target: cut 0.18–0.2 mm, score 0.15 mm dashed, labels ≤ 2 mm text, grid not printed. (Laser SVG keeps hairline 0.01 mm or "0.001 pt" per laser convention; add a `LASER_STROKE` constant.)
3. **One element per sheet wastes material.** Students must be able to select several pieces (e.g. bed + 2 bedside tables + wardrobe) and get them nested on as few A4/A3 sheets as possible, with a parts list per sheet.
4. **Interface is messy.** Too many controls in one column; test lab, share, pilot, tracer and inputs all compete. Re-organise into clear tabs with one job each, and give every tab an English + Arabic label.
5. **Instructions must be pictures, not paragraphs.** Each step gets one illustration (see section D for the prompts); text is reduced to one line EN + one line AR under each picture.

## B. New tab structure (EN | AR labels on the tab itself)
1. **Start / ابدأ** — name & ID, scale, sheet size, board type. Picture-strip of the 4-step workflow.
2. **Pieces / القطع** — a furniture list: add as many pieces as needed (chair ×4, table ×1, bed ×1…), each with real cm from the Neufert table, archetype, quantity. A running "sheets needed" counter.
3. **Fold & Glue / طيّ ولصق** — the fold-net preview (current Tab 1 geometry minus the slot code), per piece.
4. **Slot & Laser / تعشيق وليزر** — the re-derived slot joinery, separate from fold nets, with its own preview and its own rules (board thickness drives slot width; kerf setting for laser; hand-cut adds +0.2 mm).
5. **Image → Piece / صورة ← قطعة** — current Tab 3, unchanged logic, re-skinned.
6. **Sheets & Print / اللوحات والطباعة** — the nested sheets (all pieces from tab 2 packed), page-by-page preview, print at 100 %, laser SVG per sheet, parts list + stamp on every sheet.
7. **Help / مساعدة** — handout pages (pictures), Help Code, Verify sheet (TA), Pilot Protocol, Share. Everything "instructor" lives here, out of the students' way.

## C. Engineering requirements
### C1. WAFFLE (egg-crate) structure — the laser method (replaces the old "slot joinery")
**Concept.** A laser maquette is not one pair of crossing legs. It is a **grid of ribs**: parallel *side-elevation* ribs (X-ribs) and parallel *front-elevation* ribs (Y-ribs), every crossing joined by two half-depth slots — the X-rib slotted from the **top**, the Y-rib slotted from the **bottom** — so the grid assembles without glue and the stacked sections reproduce the 3D form. The solid being built is the intersection of the two silhouette extrusions.

**Reference implementation:** `FlatPack Tool\waffle\waffle.py` (Python + shapely, 120 lines) — port it to JS inside the tool. It is verified on a lounge chair at 1:10 (7 X-ribs + 8 Y-ribs, 56 crossings, 0 validation errors; preview `chair_waffle_preview.png`).

**Algorithm (as in waffle.py):**
1. Inputs (paper mm): side silhouette `S_side` (depth × height), front silhouette `S_front` (width × height), overall W, D, H, board thickness `t`, rib spacing `s` (default 10 mm, min 3t), kerf `k` (0 laser, +0.2 hand-cut), edge margin `m` = max(3t, 4 mm).
2. Rib positions: X-ribs at x_i evenly spaced from m to W−m (n = floor((W−2m)/s)+1); Y-ribs at y_j likewise across D.
3. For every crossing (i, j): find the common z-intervals where BOTH silhouettes have material (side silhouette evaluated at y_j, front silhouette evaluated at x_i). Skip intervals shorter than 3t.
4. For each common interval [lo, hi], mid = (lo+hi)/2: cut a slot of width t+k into the X-rib from **hi (top) down to mid**, and into the Y-rib from **lo (bottom) up to mid**.
5. Output: each rib as a closed polygon (with holes allowed), named X1…Xn / Y1…Ym, with a small triangle marking the TOP edge; plus an isometric assembly diagram drawn from the same data (back-to-front) printed on the sheet.
6. Validation (must pass before printing): slot width = t+k everywhere; web between neighbouring slots ≥ 2t; every crossing has exactly one top-slot and one bottom-slot meeting at mid; rib count × thickness ≤ W (and D).
7. Nesting: all ribs go through the common packer (C2); a 1:10 chair needs 2 A4 sheets or 1 A3.

**Where the silhouettes come from:** the archetype presets provide both elevations (chair: side profile with seat/back/arm, front: arms + seat + back; sofa, bed, table, cabinet likewise). In the Image tab the traced outline is `S_side` and `S_front` defaults to a rectangle (plain extrusion) unless a second image is traced. Hollow pieces (bookcase) keep the existing shelf-notch design.

**Student-facing rules:** rib spacing slider (6–15 mm) with live rib count and sheet count; thicker board → wider slots automatically; a note that waffle models are open lattices (for solid-looking surfaces students skin them with paper or use the fold-net method).

### C2. Nesting (multi-piece sheets)
- Collect all parts from all pieces into one list of polygons with labels.
- Pack with a simple guillotine/shelf packer sorted by height, rotation allowed 0/90°, 3 mm gap, honoring printable area and the title block. Fill sheet 1, then 2, …; show "Sheet 2 of 3".
- Every sheet: title block, stamp, parts list (piece name · part · qty), and the 50 mm ruler.
- Report material use: used area / sheet area %.

### C3. Line weights
- Screen preview may stay thicker; print CSS and SVG export use the thin values above. Verify by rasterising the PDF at 600 dpi and measuring stroke width in pixels.

### C4. Bilingual tabs and picture steps
- Tab labels: `EN / AR` in one chip. Keep the existing `BI_GUIDES` table but reduce each strip to one line EN + one line AR under the step picture.
- Pictures: 8 PNGs (section D) stored inline as base64 (≈ 60–120 KB each at 800 px) so the file stays offline. Total file size target < 2 MB.

### C5. Keep
- Everything verified in v3.6: true scale, fit check, ruler, stamp, Help Code, verify box, image tracer, offline build, team credits.

## D. Illustration set (8 pictures) — see the prompts in the chat reply / `claude/flatpack-v4-image-prompts.md`

## E. Acceptance test for v4 (Reham prints)
1. Table at 1:10 with 1.5 mm board: slots fit on the first try, legs cross and lock, top sits on tabs.
2. Three pieces (bed, 2 bedside tables, wardrobe) at 1:20 nest on ≤ 2 A4 sheets.
3. Cut lines on paper measure ≤ 0.25 mm wide.
4. A first-year student finds every step from the pictures alone (TA observes one student without helping).

## F. Help & handout become picture-led (added 22:43)
- Help tab and printed handout = comic strips: 2 × 3 panels per page, one line EN + one line AR per panel, no paragraphs. 16 panels (H01–H16) + 6 do/don't pairs, prompts in `flatpack-v4-image-prompts.md`.
- Each input panel in the tool shows its step picture (01–08) at the top.
- Text that stays: Neufert dimension table, the two Gemini prompts (as copy buttons), the team credits.
- Images inlined as base64 PNG ≤ 120 KB each (≈ 30 images ≈ 3 MB); if the file passes 4 MB, load images from `images/` next to index.html on GitHub Pages and keep the offline standalone download without them (the tool still works, only the pictures are missing offline).
