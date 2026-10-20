# Handover for Claude Code: Flat-Pack v4.2 (waffle sofa + cabinet), 20 Oct 2026

**Repo:** `reham-abdelwahab/rir2101-flatpack`, base = tag `v4.1` (commit 7600639).
**Source of findings:** Cowork independent audit, project doc `claude/flatpack-v4-1-independent-audit-2026-10-20.md`.
**Scope:** waffle geometry only. Fold & Glue and From-image passed the audit and must not change.

## 1. What the audit found (v4.1)

Check used: **drop assembly across the full board width.** X-parts stand on the table; each Y-rib is lowered from above. In the column of width t around each crossing (u = c ± (t/2 − 0.02)), all X material must lie below all Y material. Also: no interior rings, every part connected to the rest, every X-part touching z = 0.

| Case | Parts | Joints OK | Interference | Windows | Connected | Tool says |
|---|---|---|---|---|---|---|
| Sofa 1:10 (laser, hand) | 40 | 144 / 172 | 28 | 2 | no, 14 parts hang | valid |
| Sofa 1:20 (laser, hand) | 20 | 36 / 43 | 7 | 1 | no, 7 parts hang | valid |
| Cabinet 1:10 (laser, hand) | 17 | 52 / 60 | 8 | 0 | yes, but X1/X12 start at z = 15 | valid |
| Chair, table, bed (both scales), cabinet 1:20 | – | all | 0 | 0 | yes | valid |

`waffleValidate` misses both because it samples only the rib centre line, and for the sofa the "edge" probe lands inside the window and reads as open.

## 2. Tasks

### K · Sofa = exact sections of a box solid (not side × front)
The sofa front silhouette has a hole (seat recess between arms), so side × front leaves a void under the backrest and the middle X-ribs split into a floating back part.

Build the sofa as a union of boxes in (x, y, z), paper mm:
- seat block: x 0..W, y 0..D, z 0..S
- left arm: x 0..armW, y 0..D, z 0..armZ; right arm: x W−armW..W, same
- back: x 0..W, y D−backT..D, z 0..H

Sections (same `memb`/`slab` sizes as now):
- `Xsec(x)` in (y, z) = seat ∪ back ∪ (arm block if x ≤ armW or x ≥ W−armW)
- `Ysec(y)` in (x, z) = seat ∪ both arms ∪ (full W×H if y ≥ D−backT)

Feed these as the rib bases instead of `band(side, …)` / `band(front, …)`. The crossing table must be computed from the sections themselves (`wfIntervals(Xsec(x_i), y_j)` ∩ `wfIntervals(Ysec(y_j), x_i)`), not from side/front.

Suggested shape: let `waffleSilhouettes` optionally return `{ xSection(x), ySection(y) }`; `waffle()` uses them when present, otherwise the current band method. Chair/table/bed/cabinet keep the band method.

**Proven in Python (Cowork):** 1:10 → 26 parts, 144 joints; 1:20 → 13 parts, 36 joints; 0 interference, 0 holes, connected, every X-part on the floor, k = 0 and 0.2.

### L · Cabinet toe-recess must not sit under a rib board
At 1:10 the outer ribs are at x = margin = 4.5 mm, the recess edge rW = 5.0 mm; the 1.5 mm board spans 3.75–5.25, leaving a 0.25 mm lip under the slot (and X1/X12 start at plinth height).

Fix in `waffleSilhouettes('cabinet')`:
```
const lim = m - (t + k) / 2 - 0.5;   // m = max(3t, 4)
rD = Math.min(rD, lim); rW = Math.min(rW, lim);
```
1:10 gives rW = rD = 3.25 (k = 0) / 3.15 (k = 0.2). 1:20 unchanged (2.5).
**Proven:** 60 / 60 joints, 0 interference, X1/X12 on the floor.

General rule worth enforcing in validation (task M): no vertical silhouette edge within (t+k)/2 + 0.5 mm of any rib position.

### M · Validation + regression tests
- (a) `waffleValidate`: test slot openness / interference at u = c − (sw/2 − 0.02), c, c + (sw/2 − 0.02), not only at c. Error text: `closed slot at Xi/Yj`.
- (b) Error if a rib part has an interior ring that a slot touches (`window at Xi/Yj`).
- (c) Error if an X-part does not reach z = 0 (`X3b does not stand on the floor`), and if the parts graph is not connected (`N parts not connected to the rest`).
- (d) `tests/regress.html`: drop-assembly check for 5 archetypes × 1:10/1:20 × laser/hand. Expected 0 interference, 0 windows, connected, all X on floor. Keep the negative case: run it on v4.1 sofa geometry (or `section:false`) and require it to fail.
- (e) Existing 80 checks must still pass.

### N–P · Small items
- N: (Cowork does this) Google Sites button text → v4.2 after release.
- O: TA verify dropdown `vf-type` options "Tab 1 cut sheet / Tab 3 image trace" → "Furniture sheet / Image trace sheet". Keep the option values `cut` / `image` so old stamps still verify.
- P: CHANGELOG v4.1 line says "sofa 112 of 144 X-slots closed" → "112 of 172 crossings".

## 3. Do not change
- Fold & Glue geometry, nets, score lines, fold rule, counts line, stamps for fold sheets.
- Single-file offline HTML; layers 01_CUT_RED / 02_SCORE_BLUE / 03_LABELS_BLACK; never shrink silently.
- Task C stays as is (grey line = glue band).

## 4. Release
- `TOOL_VERSION = '4.2'`, CHANGELOG entry, tag `v4.2`, push.
- Regenerate the handout PDF under the same filename `RIR2101_FlatPack_Student_Handout_v4_0_1.pdf` (3 A4 pages).
- Course folder: `Studio_FlatPack_Maker_RIR2101_v4_2.html`; move v4.1 to `9 Superseded\before-flatpack-v4_2-2026-10-20\` + line in `00 Course Admin\Moves_2026-10-15.csv`.
- Report back: the table in section 1 re-run for v4.2. Cowork then re-audits independently.
