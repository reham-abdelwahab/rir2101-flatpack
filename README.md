# Studio Flat-Pack Maker — RIR2101 Interior Design 1

A single, self-contained HTML tool that works offline. First-year interior-design students at AASTMT use it to make true-scale maquette sheets: they list their furniture pieces, pack all the parts onto A4/A3 sheets (a shelf packer, not a guaranteed minimum), and print them at 100 % or export layered laser SVGs (`01_CUT_RED`, `02_SCORE_BLUE`, `03_LABELS_BLACK`).

## Two versions

| | Student release | Testing version |
|---|---|---|
| URL | https://reham-abdelwahab.github.io/rir2101-flatpack/ | https://reham-abdelwahab.github.io/rir2101-flatpack/testing/ |
| Version | **v4.2.3** (`index.html`) | **v4.3.0-preview.1** (`testing/index.html`) |
| Use | coursework | studio trials only — red "Experimental — not for coursework production" banner (EN/AR) and the same warning on every printed sheet |
| Regression | `tests/regress.html` — 97 / 97 | `testing/tests/regress.html` — 112 / 112, incl. the net-folding verifier |
| Handout | `RIR2101_FlatPack_Student_Handout_v4_0_1.pdf` | `testing/RIR2101_FlatPack_Student_Handout_PREVIEW.pdf` |
| Browser setting key | `bi-guide-hidden` | `preview:bi-guide-hidden` (no student projects are stored in the browser; the Help Code holds them) |

Both suites were re-run headless (Chromium 153, Linux) on 24 Oct 2026 at commit `b972c85`: 97 / 97 and 112 / 112.

**Known limit of the student release (v4.2.3), fixed only in testing:** the net-folding verifier passes 8 of 22 v4.2.3 nets. Bed and cabinet are correct. In the **chair and sofa** nets the back folds *up* from the seat, which is a valley fold, so the printed rule "all blue lines fold away from you" is wrong for that one line: **fold the back and its two side tabs toward you**. In the **table** net the tabs run along the full leg edge and meet the apron only near the top: glue the top part of each tab and trim the rest. Tell students this in class until v4.3 is promoted. See [docs/VALIDATION.md](docs/VALIDATION.md) §2a.

**Promotion.** The testing version replaces the root only when the gates in [docs/PROGRESS_PLAN.md](docs/PROGRESS_PLAN.md) are closed: geometry (done), physical builds (E1, FIT TEST, class trial, curved backs) and a first-year usability test.

Open either version in its own browser tab, not in an iframe, because printing and downloads are blocked in iframes. You can also download `index.html` and open it locally. The version history is in [CHANGELOG.md](CHANGELOG.md), the v4 specification in [docs/v4_SPEC.md](docs/v4_SPEC.md) and the original handover in [docs/HANDOVER.md](docs/HANDOVER.md). Sections below marked **(v4.3, testing only)** are not in the student release.

Course team: Dr. Reham Ahmed Abdelwahab (Instructor) · Eng. Mariam Thamarat, MSc. · Eng. Mariam Emad, BSc. (TAs).

## How it is organised (v4)

There are three tabs, each with an English and an Arabic label. Every step shows a picture with one line of English and one line of Arabic under it.

1. **MAKE / اصنع**
   - **A · Who & scale:** name, ID, scale, A4/A3 and board.
   - **B · Pieces:** the pieces list. Each piece opens a piece editor for its type, real size in cm, quantity, and build method: **Fold & Glue**, **Waffle** (cut by laser or by hand) or **From image** (profile study, waffle interpretation or folded approximation).
   - **C · Check:** warnings, Auto-fix, and the button to go to the sheets.
2. **PRINT & BUILD / اطبع وابنِ**
   - **D · Sheets:** every part of every piece, nested on numbered sheets. Each sheet has a parts list, a VERIFY stamp, the 50 mm ruler and thin lines. From here students print at 100 % or download the laser SVG.
   - **E · Build:** picture strips, shown only for the build methods the student's pieces use.
3. **HELP / مساعدة**
   - **F:** the 3-page picture handout (prints as exactly 3 A4 pages).
   - **G:** AI image help, Prompt A/B copy buttons and the Neufert table.
   - **H:** Help Code.
   - **I:** the instructor section, collapsed by default. It holds sheet verification, test cases 1–5, the pilot protocol, sharing, credits and the version.

**Waffle:** this is a JavaScript port of [`docs/waffle_reference.py`](docs/waffle_reference.py).
- The model is a grid of side-elevation ribs (X-ribs) and front-elevation ribs (Y-ribs). Where they cross, the X-rib is slotted half-depth from the top and the Y-rib from the bottom.
- Since v4.1 each rib is a *section* of the solid: X-rib_i = S_side ∩ band(z ∈ F(x_i)), and the same for Y. Material outside the shared height range can no longer turn a slot into a closed window. A rib that splits becomes parts X3a, X3b …, and parts with no slot are dropped and counted. The audit is in [docs/v4_1_AUDIT.md](docs/v4_1_AUDIT.md).
- Since v4.2 the sofa uses the exact sections of its boxes (seat, arms, back). Validation also checks drop assembly: every Y-rib can be lowered onto the standing X-ribs, there are no windows, the X-ribs stand on the floor, and the grid is one connected piece.
- Validation must pass before printing. It checks that every slot is board + kerf wide, that the web between slots is at least 2 × board, that every crossing has its top/bottom slot pair meeting at mid-height, that every slot reaches the rib edge (no closed slots), and that rib count × board fits inside the piece.
- The bookcase keeps its notched shelves (board ≥ 1.5 mm, like Waffle).
- **(v4.3, testing only)** Every Waffle and bookcase sheet carries a **FIT TEST** strip (slots at base − 0.1, base, base + 0.1 mm). Students cut it first and set the result in A ("Slot fit"); the correction moves every slot and is part of the VERIFY stamp. Each Waffle sheet prints an explicit **assembly order** for every rib (upright or upside down, chosen by the fewest glued parts), the ribs that need glue, and the finished size, in English and Arabic.

**Fold rule:** printed on every Fold & Glue sheet and under picture H08, in English and Arabic: *printed side out · score on the print · all blue lines fold away from you*. **(v4.3, testing only)** Every fold in the nets is a mountain fold — proven by the net-folding verifier (`testing/tests/fold_verify.js`), which folds the exported sheets in 3D. It found that the v4.2 chair/sofa back was a valley fold; in v4.3 the back is a separate panel glued to the posts, printed side to the rear. In the student release v4.2.3 the rule still has that one exception (see above).

**Counts:** for example "2 furniture types · 5 models · 13 cut-out parts · 1 A4 sheet". Every part carries its model's id (CH1-A1, TB1-…).

**Line weights** are set in `PRINT_STROKE` and `LASER_STROKE`. Printed sheets use a 0.2 mm cut line, a 0.15 mm dashed score line, labels of 2 mm or smaller, and no grid. Laser SVG files use a 0.01 mm hairline.

**Pictures:** the `IMG` map is inlined as base64, about 2.6 MB from `images/web` of the v4 image set. The file stays under 4 MB, so no external image folder is needed.

## Verification stamp

Every printed sheet carries `VERIFY: XXXX-XXXX · vX.Y` in its title block.
- **Single-piece and image sheets:** the stamp hashes the values printed next to it.
- **v4 nested sheets:** the stamp hashes the sheet's number and its contents.

To check a sheet, a TA opens **Help → I · Instructor → Verify a Printed Sheet**. They either paste the student's Help Code, which carries every piece, or type the values from the paper. A ✔ means the printed values were not edited after the sheet left the tool.

**This deters tampering; it is not cryptographic proof.** The salt is inside the HTML file. It is `VERIFY_SALT`, next to `TOOL_VERSION` near the top of the main script. Change it to any new text each semester. Sheets stamped with an earlier salt then show ✘, so verify those with the tagged release they were made with.

## Regression checks

The laptop has no Python or Node, so the tests run in a browser.
- **Student release:** `tests/regress.html` (97 checks against the hosted v3.4 baseline).
- **Testing version:** `testing/tests/regress.html` (112 checks, including the fold verifier).
- Online, prefix either with https://reham-abdelwahab.github.io/rir2101-flatpack/. Offline, start `pwsh -NoProfile -File tests/serve.ps1` (port 8765, or `$env:PORT`). `?base=` (empty) runs the self-checks only.

Validation for the paper (geometry, assembly, physical) is in [docs/VALIDATION.md](docs/VALIDATION.md). Studio test prints are in `testing/tests/prints/`.

The page runs these checks:
- **v3 behaviour:** the archetype × scale × sheet sweep must match the baseline exactly for bed, cabinet and bookcase; chair, sofa and table changed on purpose in v4.3 and are proven by the fold verifier. It also covers fit, ruler, stamp, Help Code and verify box, the image trace, offline loading and the icons.
- **C1 waffle:** the reference chair must come out as 7 + 8 ribs with 56 crossings and 0 errors, with rib areas matching shapely within 0.09 mm², plus negative tests.
- **C2 nesting:** acceptance test E2 (bed + 2 bedside tables + wardrobe at 1:20 on 2 A4 sheets), no overlaps, nothing scaled, and a stamp on every sheet.
- **C3 line weights:** the cut line is rasterised at 600 dpi and must measure ≤ 0.25 mm.
- **B/F interface:** tabs, steps, piece editor, Help Code with pieces, nested-sheet verification, the handout, and file size.

To check page counts, use headless Edge: `msedge --headless=new --virtual-time-budget=10000 --print-to-pdf=out.pdf "http://localhost:8765/#print-test=e2"`. That should give 2 A4 pages; `#print-test=handout` should give 3.
