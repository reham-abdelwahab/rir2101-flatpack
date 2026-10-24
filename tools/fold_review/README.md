# Maquette Fold Review — how to regenerate

A 3D step-by-step replay of (1) how each Fold & Glue net folds and (2) how each Waffle model is assembled, built only from what the tool's own checks compute:
- nets: `tests/fold_verify.js` with `spec.trace = true` returns the faces, hinges, fold order (breadth-first from the base panel), angle and direction of every fold, and the placement of each separate part;
- waffle: the rib polygons from `waffleForPiece()` and the order from `waffleAssemblyPlan()` (the steps printed on the sheet).

Regenerate after any change to the nets or the waffle code:
1. `python3 -m http.server 8765` in the repo root.
2. `python3 tools/fold_review/extract.py` → `data.json` (v4.3.0 root + v4.2.4 kept version; fold cases at 1:20, waffle at 1:10 and 1:20).
3. Replace `/*DATA*/null` in `template.html` with the JSON and republish the artifact.

Display notes: the checker counts the printed side as +Z with the sheet's y running down, so its fold models are the mirror image of the paper build; the viewer mirrors them back (x → −x). Waffle ribs are real geometry and are not mirrored.

Limits (also on the page): zero card thickness; overlap checked only in the finished shape (no swept-motion check); separate parts placed by a stated rule; the net order is the checker's valid order, not necessarily the easiest order for a student's hands.
