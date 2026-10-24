# Normalised output format (research/, D3)

Every tool's export is converted to this format by a per-tool adapter (`research/<tool>/adapt.py`). The raw export is kept beside it, unchanged. The judge (`research/net_judge.py`) reads only this format and the shared target mesh. It never reads a tool's internal data.

## Fold & Glue nets — `<case>_<scale>.net.svg`

- One SVG per case and scale (all sheets of that case may be combined on one large canvas; sheet count is recorded separately in `settings.md`).
- Units: millimetres on paper. `viewBox` in mm, `width`/`height` with `mm`. No transforms on the three groups below (bake them into coordinates).
- `<g id="01_CUT_RED">`: one closed `<path>` per separate part (its full outline, tabs included). `M`, `L` and `Z` only; curves flattened to ≤ 0.05 mm chord error.
- `<g id="02_SCORE_BLUE">`: one `<line>` per fold segment, with `data-fold="mountain"`, `"valley"` or `"unmarked"`.
  - **mountain** = folds away from the viewer of this SVG (the printed side ends up on the outside of the fold).
  - **valley** = folds toward the viewer.
  - **unmarked** = the tool draws no direction; the judge then applies that tool's own printed rule (stated in `settings.md`), e.g. ours: "all blue lines fold away from you" → mountain.
  - The printed side is the side the viewer sees. If a tool prints the other side, the adapter mirrors the drawing so the viewer sees the printed side, and says so in `settings.md`.
- `<g id="03_LABELS_BLACK">`: labels (optional for the judge).

## Waffle — `<case>_<scale>.waffle.json`

```json
{ "board_mm": 1.5, "kerf_mm": 0.0,
  "ribs": [ { "name": "X1", "plane": "x", "offset_mm": 5.0,
              "outline_mm": [[u, z], ...], "holes_mm": [[[u, z], ...]] } ] }
```
`plane` "x" = rib in a plane x = offset (u = y); "y" = rib in a plane y = offset (u = x); z up, all in paper mm in the assembled position. Slots are part of the outline (cut-outs).

## settings.md (one per tool and case)

Tool, version, commit, licence; every setting changed from the default; sheet size and count; the command or script that produced the export; wall-clock time; manual steps (count and description); anything the tool warned about.
