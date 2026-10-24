"""Writes research/lamina/<case>/settings.md from run.json (Lamina's own messages, verbatim) and adapt_report.json."""
import json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
SRC = "/tmp/claude-0/-home-claude/a08d6e43-68ac-59f1-b38b-18f3d9cee4ba/scratchpad/tools/lamina"
TARGET_AREA = {"chair": 10980.0, "table": 26560.0, "sofa_curved": 42746.8}
NORMALS_FLIPPED = {"chair": "9 of 21", "table": "0 of 14", "sofa_curved": "13 of 21"}

COMMON = f"""# Lamina — {{case}}

| | |
|---|---|
| Tool | Lamina (PyPI name `lamina3d`), "early alpha" (classifier Development Status 3 - Alpha) |
| Version | 0.3.0 (pyproject.toml) |
| Commit | bed1c9a ("Landing-page media recorded from main") |
| Licence | AGPL-3.0-or-later |
| Source | `{SRC}` (pinned clone), installed editable in its own venv (uv, CPython 3.13, trimesh 5.2.0, shapely 2.2.0) |
| Interface | Python core API only: `core.plan.build()` + `core.export.export(fmts=("svg",), labels=True, border=True, key=True)`; no web server |
| Scripts | `research/lamina/run_lamina.py` (runs Lamina, keeps raw output) → `adapt.py` (normalise) → `preview.py` (PNG) → `make_settings.py` (this file) |
| Manual steps | 0 (everything scripted; no GUI, no hand edits of any output) |

## Fold & Glue (`folded` mode)

Input: `research/models/{{case}}_fold.stl`. The STL is used, not the OBJ: trimesh fan-triangulates the OBJ's non-convex
n-gons wrongly (loaded area {{obj_area}} mm² vs 10980 / 26560 / 42746.8), while the pre-triangulated STL loads with exactly the target area.

Settings changed from Lamina's defaults (everything else default: facet 15, strategy auto, tab_h 10, tab_angle 30, margins 5, gap 3, labels on, split on, autofix add):

| parameter | default | used | why |
|---|---|---|---|
| joint | laced | **tab** | brief: glue tab |
| thickness | 1.5 | **0.5** | 0.5 mm Bristol |
| material | "" | **card** | stock name; Lamina's fold check (`FOLDS["card"] = 1.5 mm`, core/modes/folded.py:24) then applies — 0.5 mm passes |
| sheet | [600, 400] | **[297, 420]** | A3 |
| scale | 1.0 | 1.0 (1:10) / **0.5** (1:20) | 1:20 = half size |

Facet 15 (default) does not simplify these meshes: the target face count it gives (≥ 12 · area/(0.433·15²)) exceeds the STL's 14-21 triangles, so every triangle is kept (core/modes/folded.py:40-44, 58-60).

### How Lamina encodes fold direction and the printed side (from source)

* Faces are re-wound first: `core/plan.py:376-377` — `if not mesh.is_winding_consistent: trimesh.repair.fix_normals(mesh)` (and again `core/modes/folded.py:69` inside `simplify`). For an open, non-watertight surface trimesh's `fix_winding` makes the winding consistent by BFS from an arbitrary face per connected component and does **not** orient it outward (`fix_inversion` acts only on watertight meshes). Result here: Lamina's face normals disagree with the file's normals (= our printed side) on **{{flipped}}** triangles. For chair/sofa the side panels are split by a non-manifold edge (the seat's side edge is shared by 3 triangles), so the two halves of one planar side panel end up wound opposite ways.
* Every face is unfolded in its own frame with z = the (re-wound) face normal: `core/unfold.py:29` ("origin = vertex 0, z = outward normal"), `core/unfold.py:33` (`v = np.cross(N, u)`), laid flat by proper rotations only (`core/unfold.py:44`, `R = [[c, -s], [s, c]]`, no reflection). The net is therefore drawn **seen from the normal side**; the SVG export flips y only to keep it y-up on screen (`core/export.py:257`, `height - y`) and nesting only rotates (`core/nest.py:49`) — no mirroring anywhere. The printed side = the side the viewer sees = Lamina's normal side; Lamina has no separate "print" layer.
* Direction: `core/modes/folded.py:138` `convex = mesh.face_adjacency_convex`; `core/modes/folded.py:139` `styles = ("solid", "dashed")  # mountain, valley`; `core/modes/folded.py:150` a fold is `styles[0] if convex[k] else styles[1]`; tab hinges `core/modes/folded.py:488` (`"solid" if convex else "dashed"`). Legend `core/modes/folded.py:93` and export header `core/export.py:8`: "solid = mountain, dashed = valley". SVG: dashed = `stroke-dasharray="1.5,1"` (`core/export.py:170`, `:284`).
* trimesh's "convex" is `face_adjacency_projections < tol.merge` (1e-8): a coplanar pair (dihedral 0°, a triangulation diagonal) counts as convex and is drawn as a **solid (mountain) score line**.
* Adapter rule: solid → `data-fold="mountain"`, dashed → `data-fold="valley"`; no mirroring (Lamina already shows the normal side). Note this is mountain/valley relative to **Lamina's re-wound normals**, which for chair and sofa differ from the target's printed side on part of the surface (see above).

### Results

| | 1:10 | 1:20 |
|---|---|---|
{{fold_rows}}

Score lines per direction come from Lamina's SVG/plan; the split into real folds / 0° diagonals / tab hinges comes from `fold_meta.json` (read-only instrumentation of `Folded.build`, see run_lamina.py), checked line-by-line against plan.json (style and length agree to < 1e-4 mm). `refold_error` is Lamina's own test helper (`core/unfold.py:170`).

Lamina's own messages (verbatim, as its CLI `core.plan.main` prints them):

{{fold_msgs}}

## Waffle (`interlocked` mode)

Input: `research/models/{{case}}_waffle_solid.stl` (watertight; Lamina reports no repair).

| parameter | default | used | why |
|---|---|---|---|
| distribution | count (nx 5, ny 4) | **distance** | Lamina has no per-direction spacing; "distance" = one slice every `spacing` |
| spacing | 30 | **10** | our 10 mm |
| thickness | 1.5 | 1.5 (stated) | 1.5 mm board |
| kerf / compensate | 0 / off | 0 / off (stated) | kerf 0 (`core/plan.py:580`: kerf applied only when compensate is on) |
| slot_offset | 0 | 0 (stated) | slot width = board + offset (`core/notch.py:82`) |
| up | z | z (stated) | families X-n = planes x = const, Y-n = planes y = const, slots half-lap (notch_ratio 0.5) |
| sheet | [600, 400] | **[297, 420]** | A3 |
| scale | 1.0 | 1.0 / **0.5** | 1:20 = solid × 0.5 |

**Spacing vs count.** In distance mode Lamina converts the spacing to a count, `n = max(1, int(L // spacing))` per direction (`core/modes/interlocked.py:45-46`), then places the n slices at bin centres `-L/2 + L(i+0.5)/n` (`core/modes/interlocked.py:55`, `core/modes/__init__.py:308-312`). The real pitch is L/n ≥ 10 mm, the end ribs half a pitch in from the faces. Where L is a multiple of 10 the pitch is exactly 10 with ribs at 5, 15, 25 …; otherwise it is wider (offsets below).

Positions come from Lamina's internal model before nesting: each slice's 4×4 frame `M` (local → world) and each piece's local outline (`kerfed`, kerf 0) in plan.json; the adapter shifts Lamina's centred world frame (`core/plan.py:392`) back by the scaled solid's bbox centre.

### Results

| | 1:10 | 1:20 |
|---|---|---|
{{waffle_rows}}

Slot width: measured on Lamina's exported SVG sheets (U-turn edges of every cut ring; the histogram's other entries are notch-like outline features, not slots): see table. Lamina draws slots as `rect_along(..., b.thickness + slot_offset)` = 1.5 mm.

Lamina's own messages (verbatim):

{{waffle_msgs}}

## Files

* `raw/fold_<s>/`, `raw/waffle_<s>/`: Lamina's SVG sheet(s) (layers OUTER blue / INNER green / SCORE yellow / LABEL red, sheet border and a 10 cm calibration bar on the LABEL/OUTER layers), `assembly-key.txt`, `plan.json` (its plan), `run.json` (settings, timing, all messages), `fold_meta.json` (instrumentation)
* `{{case}}_1-10.net.svg`, `{{case}}_1-20.net.svg`: normalised nets (calibration bar and sheet border dropped; labels as plain text)
* `{{case}}_1-10.waffle.json`, `{{case}}_1-20.waffle.json`: normalised waffles
* `preview/`: PNGs of the normalised nets, raw sheets, and an isometric of the assembled ribs
"""


def msgs(run):
    return "```\n" + "\n".join(run["cli_output"]) + "\n```"


def main():
    rep = json.loads((HERE / "adapt_report.json").read_text())
    obj_area = {"chair": "12123", "table": "26560 (convex panels, correct)", "sofa_curved": "43870.2"}
    for case in ["chair", "table", "sofa_curved"]:
        runs = {(t, s): json.loads((HERE / case / "raw" / f"{t}_{s}" / "run.json").read_text()) for t in ("fold", "waffle") for s in ("1-10", "1-20")}
        R = {s: rep[f"{case}_{s}"] for s in ("1-10", "1-20")}
        tgt = {"1-10": TARGET_AREA[case], "1-20": TARGET_AREA[case] / 4}
        f = lambda s: R[s]["fold"]  # noqa: E731
        w = lambda s: R[s]["waffle"]  # noqa: E731
        fr = [
            ("sheets (A3)", lambda s: f(s)["sheets"]),
            ("parts (separate cut outlines)", lambda s: f(s)["parts"]),
            ("net panel area, no tabs (mm²)", lambda s: f"{f(s)['panel_area_mm2']:.2f}"),
            ("target mesh area (mm²)", lambda s: f"{tgt[s]:g}"),
            ("panel / mesh area", lambda s: f"{f(s)['panel_area_mm2'] / tgt[s]:.6f}"),
            ("cut outline area incl. tabs (mm²)", lambda s: f"{f(s)['outline_area_mm2']:.1f}"),
            ("score lines: mountain / valley / unmarked", lambda s: "{mountain} / {valley} / {unmarked}".format(**f(s)["folds"])),
            ("… real folds (90°) M / V", lambda s: "{mountain} / {valley}".format(**f(s)["real_folds"])),
            ("… 0° triangulation diagonals M / V", lambda s: "{mountain} / {valley}".format(**f(s)["flat_folds_0deg"])),
            ("… tab hinges M / V", lambda s: "{mountain} / {valley}".format(**f(s)["tab_hinges"])),
            ("Lamina refold error (mm)", lambda s: f"{f(s)['refold_error_mm']:.1e}"),
            ("wall-clock build+export (s)", lambda s: runs[("fold", s)]["seconds_total"]),
        ]
        wr = [
            ("sheets (A3)", lambda s: w(s)["sheets"]),
            ("parts", lambda s: w(s)["parts"]),
            ("ribs in x-planes (X family)", lambda s: w(s)["ribs_x_planes"]),
            ("ribs in y-planes (Y family)", lambda s: w(s)["ribs_y_planes"]),
            ("x offsets (mm)", lambda s: ", ".join(f"{v:g}" for v in w(s)["x_offsets"])),
            ("y offsets (mm)", lambda s: ", ".join(f"{v:g}" for v in w(s)["y_offsets"])),
            ("slot widths in export (mm: count)", lambda s: ", ".join(f"{k}: {v}" for k, v in list(w(s)["slot_widths_in_export"].items())[:4])),
            ("assembled rib bbox incl. board (mm)", lambda s: " × ".join(f"{v:g}" for v in w(s)["bbox_with_board_thickness_mm"])),
            ("… z range (mm)", lambda s: f"{w(s)['bbox_min_mm'][2]:g} – {w(s)['bbox_max_mm'][2]:g}"),
            ("solid bbox (mm)", lambda s: " × ".join(f"{v:g}" for v in w(s)["solid_bbox_mm"])),
            ("errors / warnings (Lamina counts)", lambda s: f"{runs[('waffle', s)]['counts']['errors']} / {runs[('waffle', s)]['counts']['warnings']}"),
            ("wall-clock build+export (s)", lambda s: runs[("waffle", s)]["seconds_total"]),
        ]
        rows = lambda spec: "\n".join(f"| {n} | {g('1-10')} | {g('1-20')} |" for n, g in spec)  # noqa: E731
        txt = COMMON.replace("{case}", case).replace("{obj_area}", obj_area[case]).replace("{flipped}", NORMALS_FLIPPED[case])
        txt = txt.replace("{fold_rows}", rows(fr)).replace("{waffle_rows}", rows(wr))
        txt = txt.replace("{fold_msgs}", "1:10\n\n" + msgs(runs[("fold", "1-10")]) + "\n\n1:20\n\n" + msgs(runs[("fold", "1-20")]))
        txt = txt.replace("{waffle_msgs}", "1:10\n\n" + msgs(runs[("waffle", "1-10")]) + "\n\n1:20\n\n" + msgs(runs[("waffle", "1-20")]))
        (HERE / case / "settings.md").write_text(txt, encoding="utf-8")
        print(case, "ok")


if __name__ == "__main__":
    main()
