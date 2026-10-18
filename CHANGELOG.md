# Changelog

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
