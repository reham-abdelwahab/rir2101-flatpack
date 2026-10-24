# Build Steps pages — how they are made and rebuilt

Two pages on the site replay, in 3D, what the tool's own checks compute from the printed sheets:
- `steps/index.html` — **Maquette Build Steps** for students (EN/AR, newest version only).
- `review/index.html` — **Maquette Fold Review** for staff (all versions in `data.json`, pass/fail per net).

Sources here: `student_template.html`, `template.html` (staff), `extract.py`, `build.py`. The built pages and `data.json` are committed so GitHub Pages serves them.

## Rebuild (part of every release that touches nets, side profiles or Waffle code)
1. From the repo root: `git show ba04eee:index.html > _v430.html` and `git show c0d7e37:index.html > _v431.html` (the v4.3.0 and v4.3.1 controls for the staff page; do not commit them).
2. `python3 -m http.server 8765 &`
3. `python3 tools/fold_review/extract.py` → `tools/fold_review/data.json`. Expected (24 Oct, v4.3.2): v4.3.2 and v4.3.1 all ok and both side posts at the back; v4.3.0 and v4.2.4 B2 RIGHT post at the FRONT (F2), so their chair and sofa FAIL; v4.2.4 table FAIL. Curves: the extractor reads real cm when the page defines `CURVE_UNITS_PER_CM` (v4.3.2+), else paper mm.
4. `python3 tools/fold_review/build.py` → `steps/index.html`, `review/index.html`. The student page takes the highest version in `data.json`: add a new version to `extract.py` when you release one.
5. `rm _v430.html _v431.html`; run the regression suites (they check the links and that both pages are built with data).

## What the pages do (and do not) show
- Fold order: the base part's panels in the checker's order (breadth-first from the base panel); then each separate part is placed, followed by the tabs that glue onto it — no tab is glued onto a part that is not there yet.
- Side profiles are placed **printed side out** (since v4.3.2 the checker does the same, T1) and both faces are coloured, so a side drawn the wrong way round shows its post at the front (F2).
- The checker's frame is the mirror image of the paper build (printed side = +Z with the sheet's y down); fold models are shown mirrored back (x → −x). Waffle ribs are real geometry.
- Limits (on both pages): zero card thickness; overlap checked only in the finished shape (no swept-motion check); separate parts placed by a stated rule.
