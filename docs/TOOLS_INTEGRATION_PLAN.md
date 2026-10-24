# Handover 3 of 3 — Flat-Pack Maker: GIT TOOLS COMPARISON & INTEGRATION workflow

*Start a new chat with this file. Written 24 Oct 2026, 18:50 Cairo. Owner: Reham Ahmed Abdelwahab, RIR2101 Interior Design 1, AASTMT. Related: Handover 1 (student release v4.2.4), Handover 2 (testing v4.3 + paper).*

## 1. What this workflow is
Find out, with measurements, whether established open-source tools make better maquette templates than our own generator — and, only where one clearly does, bring its output into the tool **on the instructor side**. Students keep the same simple bilingual interface; they never need Blender.

**Research questions (for the paper)**
- RQ1 — Do general-purpose net generators (Export Paper Model, PolyZamboni) produce furniture nets that fold to the target size with correct, printable fold marking more often than our parametric nets?
- RQ2 — Does a general rib generator (Lamina) produce waffle sets that assemble, at 1:10 and 1:20, as reliably as our section-rib generator?
- RQ3 — Does a general vectoriser (VTracer) trace furniture outlines from student images more accurately than our tracer — and does any tracer remove the need for the human outline check?
- RQ4 — Which of these differences survive a physical build by first-year students?

## 2. Status on 24 Oct 2026
**Nothing has been run.** The four tools were chosen from their documentation only (ChatGPT review, 24 Oct). No tool installed, no case generated, no output scored, no code integrated. The testing site `/testing/` (v4.3.0-preview.2) is where integrated templates would appear; today it contains only our own v4.3 work.

## 3. Candidates (facts to verify in step D1 — do not quote as checked)
| Tool | Repo | Role here | Expected input → output | Known limits (from its docs) | Check before use |
|---|---|---|---|---|---|
| Export Paper Model | github.com/addam/Export-Paper-Model-from-Blender (also extensions.blender.org) | Fold & Glue nets | mesh → SVG/PDF net with tabs, edge labels, fold styles | needs Blender + a clean mesh | licence; how it marks mountain vs valley; thick-paper option |
| PolyZamboni | github.com/AntonFlorey/PolyZamboni | Difficult nets (curved sofa/chair) | mesh → editable cuts, overlap and unfoldability warnings, build steps | needs Blender; no material/glue proof | licence; export format |
| Lamina | github.com/marcelfarres/lamina | Waffle comparison | mesh → interlocking ribs, slot fit, kerf | **early alpha** by its author's own statement | licence; runs offline?; export format |
| VTracer | github.com/visioncortex/vtracer | Tracing comparison | raster → vector paths | no true size, no perspective correction, does not know which region is furniture | licence; Python binding |
| *(optional)* Rhino `UnrollSrf` / Grasshopper | Reham's own Rhino (rhino MCP is connected) | Baseline any designer already has | Brep → unrolled surfaces | no tabs, no fold marking by default | — |

Pin the exact version/commit of every tool in `research/TOOLS.md`; results are only valid for that version.

## 4. The fixed test set (same for every tool)
| Case | Size W × D × H (cm) | Variants | Scales | Board |
|---|---|---|---|---|
| Chair | 45 × 45 × 85 | flat, arched, sloped back | 1:10, 1:20 | 0.5 mm Bristol (fold) · 1.5 mm (waffle) |
| Table | 140 × 80 × 75 | flat | 1:10, 1:20 | same |
| Curved sofa | 180 × 85 × 80 | curved back + arms (sections that change along the length) | 1:10, 1:20 | same |

One dimensioned 3D model per case, built once (Rhino → OBJ, metres → cm stated) and given identically to every tool. Our tool gets the same W × D × H. Store models in `research/models/`.

## 5. Protocol
1. **Generate** each case in each tool; record every setting (`research/<tool>/<case>/settings.md`).
2. **Normalise** the export to our layer convention with one adapter (`research/adapt_svg.py`): cut → `01_CUT_RED`, fold → `02_SCORE_BLUE`, labels → `03_LABELS_BLACK`, units in mm. **Critical:** other tools print *both* mountain and valley folds (by dash style). Our verifier currently demands mountain-only, which is our sheet rule, not a universal truth. The adapter must keep the fold sign, and the verifier must be extended to check "every fold goes the way its marking says" — otherwise the comparison is unfair to the other tools.
3. **Score geometry and assembly** with the same judge: `testing/tests/fold_verify.js` (nets) and the independent drop-assembly check from `testing/tests/regress.html` (waffle).
4. **Score tracing** on 3 image cases (clean elevation with known size; same, hand-checked; room/perspective photo) against a hand-drawn reference outline.
5. **Build** only the nets that pass steps 3–4, in the studio, by TAs then 5 students.
6. **Record** everything in `research/RESULTS.md` (one row per tool × case × scale).

**Metrics**
| Group | Metric |
|---|---|
| Nets | M1 size error (mm, max of W/D/H) · M2 folds whose direction matches the marking (%) · M3 tabs that land ≥ 95 % on a face (%) · M4 overlapping panels (count) · M5 sheets and material use · M6 instructor preparation time (min) |
| Waffle | slot width = board + kerf + fit · closed slots · windows · unsupported parts · finished size · shallowest slot depth |
| Tracing | IoU with the reference outline · area error (%) · path nodes · background leak (yes/no) · student check still needed (always yes unless proven otherwise) |
| Physical | corrective cuts per model · build time · lift-and-place survival (waffle) · TA notes |

## 6. Decision rule (agreed before any result is seen)
A tool's output is adopted for one furniture case only if it is **no worse than ours on M1–M4** (or the waffle equivalents), **better on at least one physical metric**, introduces **no new failure type**, its licence allows the use, and the version is pinned. Otherwise our generator stays. A tie keeps ours (simpler for students, works offline).

## 7. Integration path (only for adopted cases)
**Dimensioned 3D model → tool (pinned version) → normalised SVG → verifier pass → physical build pass → "Approved template" in our tool.**
- Approved templates live as data (SVG + JSON with case, size, scale, source tool, version, licence, test record), not as bundled third-party code. Do not copy GPL or unlicensed code into `index.html` without checking the licence.
- Students pick an approved template exactly as they pick a furniture type today; the sheet credits the source tool.
- Every approved template becomes a regression fixture (exported sheet + expected verifier result).
- First appears in `/testing/` with a new preview number; reaches students only through the normal promotion gates (Handover 2, B2–B11).

## 8. Step tracker
| # | Step | Output | Status |
|---|---|---|---|
| D0 | Agree this protocol and the decision rule (section 6) | Reham's yes | ⬜ |
| D1 | Install and pin the four tools (cloud container: Blender headless / `bpy`, `pip install vtracer`, Lamina as documented); check licences | `research/TOOLS.md` | ⬜ |
| D2 | Build the 3 dimensioned models (Rhino) | `research/models/*.obj` | ⬜ |
| D3 | Adapter + signed-fold extension of `fold_verify.js`; re-run our 22 nets to prove nothing changed | adapter + tests green | ⬜ |
| D4 | Export Paper Model: chair, table, curved sofa × 1:10/1:20 → scored | rows in RESULTS | ⬜ |
| D5 | PolyZamboni: same, focus curved sofa/chair | rows | ⬜ |
| D6 | Lamina vs our Waffle: same cases | rows | ⬜ |
| D7 | VTracer vs our tracer: 3 image cases | rows | ⬜ |
| D8 | Studio builds of the passing nets (links to B5/B8) | physical columns | ⬜ |
| D9 | Decision per case (section 6); integrate adopted templates (section 7) | `/testing/` preview | ⬜ |
| D10 | Paper: methods, results table, limits | draft in project docs | ⬜ |

**Open question to Reham:** start D1–D4 with Export Paper Model on the chair, table and curved sofa?

## 9. Known limits to state in the paper
Zero board thickness in the verifier; only the final folded state is checked for overlap (no swept-motion check); placement of separate parts is stated, not searched; one traced side profile cannot describe a sofa whose arms, seat and back sections differ (a limit of the method, not of any tracer); results hold only for the pinned tool versions and the three cases.

## 10. Where things are
- Repo `reham-abdelwahab/rir2101-flatpack` (`main` = `4a94e63`); new work goes in a `research/` folder, never in the site root.
- Plan: Track C in `docs/PROGRESS_PLAN.md` = project doc `claude/flatpack-progress-plan-2026-10-24.md` (C1–C4 = D4–D10 here).
- Verifier and fixtures: `testing/tests/`.
- Constraints: tag pushes refused by the proxy; Reham's laptop has no Python/Node (heavy runs in the cloud container); Rhino reachable through the rhino MCP when her desktop app is open.

## 11. First message to paste in the new chat
"Continue the Flat-Pack Git-tools comparison and integration workflow from `claude/handover-flatpack-git-tools-integration-2026-10-24.md`. Start with D0–D1: confirm the protocol, install and pin the tools, check their licences, then [D2 / D4 Export Paper Model …]."
