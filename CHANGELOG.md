# Changelog

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
