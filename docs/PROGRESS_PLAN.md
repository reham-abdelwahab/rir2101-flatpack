# Progress plan — Studio Flat-Pack Maker (from 24 Oct 2026)

Two versions are open (see [README](../README.md)). This plan says what must happen before v4.3 replaces the student release, who does it, what counts as a pass, and when we check.

**Baseline at closing (commit `2bcdc74`, 24 Oct 2026)**

| | Student `/` | Testing `/testing/` |
|---|---|---|
| Version | v4.2.4 | v4.3.0-preview.2 |
| Regression (re-run headless, Chromium 153) | 104 / 104 | 112 / 112 |
| Net-folding verifier (22 nets) | 8 / 22 (chair, sofa, table: exceptions printed on the sheet) | 22 / 22 |
| Waffle assembly plan (20 cases) | — | 20 / 20 = target size |
| Physical builds | E1 v4.2 only (loose on 600 gsm → Waffle lock) | none yet |

**Modification list v4.3 (38 items):** 31 closed in code · 5 waiting for the studio (P1-1, P1-2, P1-6, P2-5, P3-7 → B2–B7) · P4-1 waits for E1 (B3) · P3-6 closed in the course folder (A4).

Status key: ⬜ open · 🟡 in progress · ✅ passed · ❌ failed (→ fix, re-test)

## Track A — Teaching (keep the student release safe)

| # | Action | Owner | Due | Pass when | Status |
|---|---|---|---|---|---|
| A1 | Tell the class the exceptions (now printed in red on every chair, sofa and table sheet, EN/AR): chair/sofa back and its side tabs fold **toward** you; table tabs — glue the top, trim the rest | Reham / TAs | Sun 25 Oct | said in studio; sheets carry it (v4.2.4) | 🟡 sheets ✅, class briefing ⬜ |
| A2 | Collect every chair, sofa and table that needed a corrective cut (photo + student ID) | TAs | Sun 25 Oct | list with count n / class size | ⬜ |
| A3 | Hotfix v4.2.4: exceptions printed on chair/sofa/table sheets | Claude | 24 Oct | 104/104; v4.2.3 stamps still verify | ✅ |
| A4 | Course folder (P3-6): v4.2.4 tool + handout in `Week 06/2 Studio/FlatPack Tool`, preview in its `TESTING ONLY` subfolder; v4.2.1, old handouts, old `studio_flat_pack_maker_1_20_1_10.html`, 7 raw Gemini images and the 4 audit files from the course root moved to `Week 06/9 Superseded/before-flatpack-v4_2_4-2026-10-24` | Claude | 24 Oct | nothing deleted; `_README.txt` logged | ✅ |

## Track B — Promotion gates for v4.3 (all must pass)

| # | Gate | Evidence | Owner | Target | Pass criterion | Status |
|---|---|---|---|---|---|---|
| B1 | Geometry | `testing/tests/regress.html` | Claude | done | 112 / 112, fold verifier 22 / 22 | ✅ |
| B2 | FIT TEST strip | slots A–D (−0.1 / 0 / +0.1 / +0.2 mm) on 1.5 mm board, laser and hand-cut, 3 repeats | TA | Week 6 studio | one slot holds a rib by friction, no forcing; value recorded per cutter | ⬜ |
| B3 | E1 table 1:10 Waffle | `testing/tests/prints/E1_table_1-10_waffle_{LASER,HANDCUT}_v4_3.pdf` | TA | Week 6 studio | assembled upside down, turned upright, 5 lift-and-place cycles, glued X2–X13 hold; size within ±1 mm of 140 × 80 × 75 | ⬜ |
| B4 | 1:20 hand-cut slot depth | table/chair 1:20 Waffle from the tool | TA | Week 6 | web under a 3 mm slot does not split in 3 of 3 tries → lower the 4 mm warning; else keep it | ⬜ |
| B5 | Class trial Fold & Glue | `testing/tests/prints/TRIAL_4chairs_1table_1-20_fold_v4_3.pdf` | TAs + 5 students | Week 6–7 | ≥ 4 of 5 models built with no corrective cut; every back tab lands on a post | ⬜ |
| B6 | Curved backs (P3-7) | `testing/tests/prints/P3-7_curved_backs_chair_1-20_A4.pdf` | TA | Week 6–7 | flat, arched, sloped: tabs reach and hold | ⬜ |
| B7 | Glue timing (P2-5) | class glue, stopwatch | TA | Week 6–7 | minutes to handling strength recorded; H10 text matches | ⬜ |
| B8 | Usability (first-year) | 5 students, think-aloud, task: one chair + one table to print | Reham | after B5 | each finishes alone in ≤ 20 min; no student prints from the wrong version | ⬜ |
| B10 | Template transfer (P2-1) | glue stick vs spray mount on 1.5 mm board; re-measure the 50 mm ruler after 5 min | TA | Week 6–7 | spray mount ≤ 0.2 mm change; wet glue result recorded | ⬜ |
| B11 | Score coupon (P2-4) | 0.5 mm Bristol, both grain directions, light vs deep score | TA | Week 6–7 | no cracking or spring-back on the H08 method; result in the H08 tip | ⬜ |
| B9 | Image path | 3 cases: clean elevation with size; same, hand-checked outline; room photo | Reham + 3 students | after B8 | room photo is stopped by the gate; the other two print at Neufert size | ⬜ |

**Promotion step (Claude, after B2–B11 pass):** copy `testing/index.html` → root, remove the banner and sheet watermark, set `TOOL_VERSION = '4.3.0'`, change `VERIFY_SALT` only if a new semester, merge `testing/tests/` into `tests/`, regenerate the handout, re-run both regressions, tag `v4.3.0`, keep `testing/` for the next preview.

## Track C — Research (paper)

Detailed protocol, decision rule and integration path: [TOOLS_INTEGRATION_PLAN.md](TOOLS_INTEGRATION_PLAN.md) (steps D0–D10; C1 = D4–D7, C2 = scoring inside D4–D7, C3 = D8, C4 = D10). Status 24 Oct: nothing run yet.

| # | Step | Output | Status |
|---|---|---|---|
| C1 | Same 3 cases (chair, table, curved sofa) in Export Paper Model (Blender) and PolyZamboni; Lamina for Waffle; VTracer for tracing | exported SVG nets per tool | ⬜ |
| C2 | Score every net with `fold_verify.js` (size, fold direction, tab landing, overlap) — the common, independent judge | table: tool × case × 4 metrics | ⬜ |
| C3 | Add student time and corrective-cut counts from B5/B8 | builds per tool | ⬜ |
| C4 | Methods + results section; limits stated (zero thickness, final-state overlap only, one side profile cannot describe arms/seat/back sections that differ) | draft in project docs | ⬜ |

## Check-in rhythm
- **After every studio session:** TAs send photos + the pass/fail line for each gate run that day. Reham updates the Status column (or asks Claude to).
- **Every Saturday:** Claude re-runs both regressions, reads this file, reports open gates and the next three actions. Any ❌ gets a fix ticket in the CHANGELOG under the testing version.
- **Promotion review:** when B2–B11 are ✅, before the next coursework print.
