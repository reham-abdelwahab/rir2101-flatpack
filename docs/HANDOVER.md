# Handover to Claude Code — Studio Flat-Pack Maker (RIR2101) → GitHub Pages + verification stamp

Date: 18 Oct 2026 · Owner: Reham Ahmed Abdelwahab (AASTMT, RIR2101 Interior Design 1) · Written by the Cowork session that built v3.4.

## 1. What the tool is
One self-contained HTML file (≈230 KB, no CDN, works offline) that first-year interior-design students use to print 1:10 / 1:20 maquette cut sheets or export laser SVGs.
Three tabs:
1. **Make & Test Cut Sheet** — 6 furniture archetypes → true-scale fold/cut net on A4/A3, 3D fold preview, validation modal with auto-fix, Help Code (base64 state) for remote troubleshooting, Share/Download standalone copy.
2. **Student Handout** — 3 printed A4 pages (workflow, craft/laser, AI-image prompts A/B). Bilingual EN|AR strips in every section (toggle button "ع" in header, saved in localStorage).
3. **Image → Cut Sheet** — upload/paste any image → calibrate 2 points → auto-trace (background region-growing from borders, cast-shadow rejection, morphological opening, Moore boundary trace, RDP simplify) or hand-trace → nested pieces + extra panels → print / layered SVG.

Layer convention in every SVG: `01_CUT_RED`, `02_SCORE_BLUE`, `03_LABELS_BLACK` (`00_BACKGROUND_GRID` is `.no-export` and stripped on download).

## 2. Files
- **Master file (v3.4):** `C:\Users\archr\OneDrive\Study\TEACH\A313\Week 06 - Living Area, Bathroom and Maquettes\2 Studio\FlatPack Tool\Studio_FlatPack_Maker_RIR2101_v3_4_team.html`
  SHA-256 starts `0b491f42df5aedd8`. Also attached in the Cowork chat (18 Oct, 12:54).
- Printed handout PDF (3 pp): same folder, `RIR2101_FlatPack_Student_Handout_v3_4.pdf`.
- Project doc with this handover: `claude/flatpack-tool-handover-2026-10-18.md`.

Key constants at the top of the script (edit here only):
- `COURSE_TEAM` — instructor + 2 TAs, EN and AR. (Dr. Reham Ahmed Abdelwahab; Eng. Mariam Thamarat, MSc.; Eng. Mariam Emad, BSc.)
- `BI_GUIDES` — the 21 bilingual guidance strips (selector + en + ar).
- `archetypes` — furniture presets (cm) from Neufert.

## 3. What is already verified (automated Playwright, Chromium 141, network blocked)
- 72-combination sweep (6 archetypes × 6 scales × A4/A3): every drawn part is exactly to scale; overflow is reported, never shrunk.
- Tests 1–5 pass; Auto-Fix leaves only "Missing Student Name or ID" (identity must be typed; sample names removed).
- Print → 1 page on A4 and A3; the 50 mm check ruler measures 50.0 mm in the PDF. Handout prints as exactly 3 pages.
- Help Code round-trips state exactly. Standalone download opens clean (no modal, no photo, no names).
- Image tab: synthetic silhouette, line sketch, noisy photo and AI-render-like image (shading, highlight, vignette, soft shadow) all trace a 35×85 cm chair to 35.1–35.3 × 85.0–85.3 mm at 1:10.
- Test scripts live only in the Cowork container (`/home/claude/test/t1.py … t4.py`) — recreate if needed; they are short Playwright scripts.

## 4. Tasks for Claude Code (in order)

### Task A — GitHub repo + Pages (canonical host)
1. Create repo `rir2101-flatpack` (private is fine; Pages works on private repos for paid plans — if her plan is free, make it public; the file contains no student data).
2. Commit the master file as `index.html` (exact copy, no edits) + `README.md` (one paragraph, link to this handover) + `CHANGELOG.md` (start at v3.4, list v2→v3.4 from section 6).
3. Enable GitHub Pages from `main` / root. Report the URL (`https://<user>.github.io/rir2101-flatpack/`).
4. Add a `VERSION` constant in the HTML header (`const TOOL_VERSION = '3.4'`) and print it in the title block credit row and the app header; bump it on every release.
5. Tag the release `v3.4`.

### Task B — Verification stamp (anti-manipulation for submitted sheets)
Goal: a TA can confirm that a printed sheet came from the official tool with the values printed on it.
1. Compute `stamp = base32(sha256(TOOL_VERSION | name | id | archetype | w | d | h | subH | scale | sheet | thickness | joinery | SALT)).slice(0, 8)` formatted `XXXX-XXXX`. Use Web Crypto (`crypto.subtle.digest`) — note it is async, so compute it on state change and cache it in `state.stamp`; the SVG renders the cached value.
2. Print it in the title block (both Tab 1 and Tab 3 sheets) as `VERIFY: XXXX-XXXX · v3.4`, and include it in the Help Code and the SVG labels layer.
3. Add a small "Verify a sheet" box inside the **Share & Troubleshoot** modal (instructor side): paste the sheet's values (or the Help Code) → recompute → ✔/✘. Also add an optional QR (inline, no library — use a tiny QR encoder or skip QR if it adds a dependency).
4. Be explicit in the UI copy and in the README that this deters tampering but is not cryptographic proof (the salt is inside the file). Document the salt location; Reham may change it per semester.
5. Run the regressions: A4/A3 print still 1 page, ruler 50 mm, no console errors, Help Code round-trip, image tab trace unchanged.

### Task C — Hand-off to Vivo EnviR (LearnWorlds)
- In the course "Interior Design 1: Foundations (RIR2101)" add a **Link** activity (opens in new tab) pointing to the Pages URL, in the Week 6 section, plus the handout PDF as a downloadable file. Do not iframe-embed (print/download are blocked in iframes). Reham does this herself in LearnWorlds; Claude Code just supplies the URL and the PDF.

### Task D (optional, later)
- Perspective warning in the image tab (detect non-vertical edges in the trace and warn).
- Serve the Arabic strips from a JSON so the TAs can edit wording without touching code.

## 5. Rules Reham set
- Never shrink parts silently; the tool must say "does not fit" instead.
- Dimensions come from the Neufert table / measured pieces, never from an image; AI images are drawing aids only and students must cite the tool + prompt.
- Student identity is typed by the student; no sample names in shipped copies.
- Back up before overwriting in `A313` (copy to that week's `9 Superseded\` + a line in `00 Course Admin\Moves_2026-10-15.csv`).
- Keep the file single-file and offline-capable (no CDN links).

## 6. Version history (for CHANGELOG)
- v1 (original, 18 Oct): fold lines hidden under panels; tabs cut into seat; silent clamping (1:20 bed printed ≈1:24); CDN Tailwind; sample student name; LaTeX in handout; NaN on empty scale; grid exported to laser.
- v2: all of the above fixed; true-scale geometry with glue tabs; real fit check; offline Tailwind; new validation rules (thick board on small fold, slot on non-slot archetype); Tests 1/4 on 0.5 mm Bristol.
- v3: Image → Cut Sheet tab (calibrate, auto/hand trace, nesting, panels, print/SVG).
- v3.1: tracer retuned for AI renders (background region-growing, shadow rejection, clean-edges slider, colour picker, AI prompt copy).
- v3.2: handout page 3 with Prompt A (generate) and Prompt B (convert my image); copy buttons in Tab 3.
- v3.3: bilingual EN|AR guidance strips in all 21 sections; toggle; print-fitted (handout still 3 pages).
- v3.4: course team credits in header, both title blocks (2-line credit row) and handout footers; file copied to A313.
