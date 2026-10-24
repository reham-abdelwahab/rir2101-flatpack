"""Lamina → normalised research format (research/FORMAT.md).

    python3 research/lamina/adapt.py            # plain python3 + stdlib only; reads research/lamina/<case>/raw/

Inputs per case/scale (written by run_lamina.py, unchanged Lamina outputs except fold_meta.json):
  raw/fold_<s>/plan.json        Lamina's plan: every piece's outline and score lines as nested on the sheet
                                ("placed", "lines", y up, sheet mm) — the same numbers its SVG export writes
  raw/fold_<s>/fold_meta.json   per score line: fold edge or tab hinge, and the mesh dihedral angle behind it
  raw/waffle_<s>/plan.json      every slice's 4x4 frame M (local → world, mesh centred at the origin) and each
                                piece's outline in that local frame BEFORE nesting ("kerfed", kerf 0 = the profile)
Outputs per case: <case>_<1-10|1-20>.net.svg, <case>_<1-10|1-20>.waffle.json, adapt_report.json (sanity numbers).

Fold direction (see settings.md for the source lines): Lamina draws a fold "solid" when trimesh calls the edge convex
and "dashed" otherwise; solid = mountain, dashed = valley, with every face laid out seen from its outward normal and
the SVG drawn so the viewer sees that side. So: solid → data-fold="mountain", dashed → "valley". No mirroring.
"""
from __future__ import annotations
import json, math, pathlib, re

HERE = pathlib.Path(__file__).resolve().parent
CASES = ["chair", "table", "sofa_curved"]
SCALES = {"1-10": 1.0, "1-20": 0.5}
# the shared solids' bounding boxes at 1:10 (models_report.json): the assembled ribs are put back in these coordinates
SOLID_BBOX_1_10 = {"chair": (45, 45, 85), "table": (140, 80, 75), "sofa_curved": (180, 85, 80)}
SHEET_GAP = 20.0     # mm between sheets when several are laid side by side on one canvas
STYLE_TO_FOLD = {"solid": "mountain", "dashed": "valley", "dotted": "unmarked"}


def ring_area(r):
    return 0.5 * sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


# ------------------------------------------------------------------------------------------- Fold & Glue
def adapt_fold(case, sk):
    raw = HERE / case / "raw" / f"fold_{sk}"
    plan = json.loads((raw / "plan.json").read_text())
    meta = json.loads((raw / "fold_meta.json").read_text())
    W, H = plan["sheet"]; n_sheets = plan["sheets"]
    CW = n_sheets * W + (n_sheets - 1) * SHEET_GAP
    by_label = {p["label"]: p for p in meta["panels"]}
    cut, score, lab = [], [], []
    stats = {"parts": 0, "outline_area_mm2": 0.0, "panel_area_mm2": 0.0,
             "folds": {"mountain": 0, "valley": 0, "unmarked": 0}, "flat_folds_0deg": {"mountain": 0, "valley": 0},
             "real_folds": {"mountain": 0, "valley": 0}, "tab_hinges": {"mountain": 0, "valley": 0}, "fold_length_check_max_mm": 0.0}

    def X(si, x):
        return si * (W + SHEET_GAP) + x

    def Y(y):
        return H - y                                            # Lamina's own export flip (core/export.py:257)
    for sl in plan["slices"]:
        for pc in sl["pieces"]:
            si = pc["place"][0]
            for region in pc["placed"]:
                ext = region[0]
                d = "M" + " L".join(f"{X(si, x):.4f},{Y(y):.4f}" for x, y in ext) + " Z"
                cut.append(f'<path data-part="{esc(pc["label"])}" d="{d}"/>')
                stats["parts"] += 1
                stats["outline_area_mm2"] += abs(ring_area(ext)) - sum(abs(ring_area(h)) for h in region[1:])
                for h in region[1:]:                            # none in these nets; kept so nothing is dropped silently
                    cut.append(f'<path data-part="{esc(pc["label"])}" data-hole="1" d="M' + " L".join(f"{X(si, x):.4f},{Y(y):.4f}" for x, y in h) + ' Z"/>')
            mp = by_label.get(sl["label"])
            if mp is not None:
                stats["panel_area_mm2"] += mp["panel_area_mm2"]
            for i, (style, pts) in enumerate(pc["lines"]):
                info = mp["lines"][i] if mp is not None and i < len(mp["lines"]) else {"kind": "unknown"}
                if info.get("style", style) != style:
                    raise SystemExit(f"{case} {sk}: line {i} style mismatch between plan.json and fold_meta.json")
                if "coords" in info:                            # same line in the panel frame: lengths must agree
                    (a, b), (c, e) = pts, info["coords"]
                    stats["fold_length_check_max_mm"] = max(stats["fold_length_check_max_mm"], abs(math.dist(a, b) - math.dist(c, e)))
                fold = STYLE_TO_FOLD.get(style, "unmarked")
                stats["folds"][fold] += 1
                extra = f' data-kind="{info["kind"]}" data-lamina-style="{style}"'
                if info["kind"] == "fold":
                    extra += f' data-dihedral-deg="{info["dihedral_deg"]:g}"'
                    (stats["flat_folds_0deg"] if info["dihedral_deg"] < 1e-3 else stats["real_folds"])[fold] += 1
                elif info["kind"] == "tab_hinge":
                    stats["tab_hinges"][fold] += 1
                for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                    score.append(f'<line x1="{X(si, x0):.4f}" y1="{Y(y0):.4f}" x2="{X(si, x1):.4f}" y2="{Y(y1):.4f}" data-fold="{fold}"{extra}/>')
            for m in pc["marks"]:                               # seam numbers
                lab.append(f'<text x="{X(si, m[0]):.3f}" y="{Y(m[1]):.3f}" font-size="2.4" text-anchor="middle" '
                           f'transform="rotate({-m[3]:g} {X(si, m[0]):.3f} {Y(m[1]):.3f})">{esc(m[2])}</text>')
            if pc.get("label_pos"):
                x, y, r = pc["label_pos"]
                lab.append(f'<text x="{X(si, x):.3f}" y="{Y(y):.3f}" font-size="4" text-anchor="middle">{esc((plan.get("label_tag") or "") + " " + pc["label"])}</text>')
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW:g}mm" height="{H:g}mm" viewBox="0 0 {CW:g} {H:g}" '
           f'data-tool="Lamina 0.3.0 (bed1c9a)" data-case="{case}" data-scale="{sk}" data-sheets="{n_sheets}">',
           '<rect class="no-export" x="0" y="0" width="%g" height="%g" fill="#ffffff"/>' % (CW, H)]
    for si in range(n_sheets):
        svg.append(f'<rect class="no-export sheet" x="{X(si, 0):g}" y="0" width="{W:g}" height="{H:g}" fill="none" stroke="#bbbbbb" stroke-width="0.3"/>')
    svg += ['<g id="01_CUT_RED" fill="none" stroke="#dc2626" stroke-width="0.25">', *cut, "</g>",
            '<g id="02_SCORE_BLUE" fill="none" stroke="#2563eb" stroke-width="0.25">', *score, "</g>",
            '<g id="03_LABELS_BLACK" fill="#000000" font-family="sans-serif">', *lab, "</g>", "</svg>"]
    (HERE / case / f"{case}_{sk}.net.svg").write_text("\n".join(svg), encoding="utf-8")
    stats["mesh_area_mm2_lamina"] = meta["mesh_area_mm2"]; stats["refold_error_mm"] = meta["refold_error_mm"]
    stats["sheets"] = n_sheets; stats["scale_check_bar_omitted"] = True
    return stats


# ------------------------------------------------------------------------------------------- Waffle
def apply(M, u, v):
    return [M[r][0] * u + M[r][1] * v + M[r][3] for r in range(3)]


def adapt_waffle(case, sk):
    raw = HERE / case / "raw" / f"waffle_{sk}"
    plan = json.loads((raw / "plan.json").read_text())
    s = SCALES[sk]
    centre = [s * e / 2 for e in SOLID_BBOX_1_10[case]]        # Lamina centres the (scaled) mesh: core/plan.py:392
    ribs, lo, hi, lo_t, hi_t = [], [1e9] * 3, [-1e9] * 3, [1e9] * 3, [-1e9] * 3
    for sl in plan["slices"]:
        M = sl["M"]; n = [M[0][2], M[1][2], M[2][2]]
        axis = max(range(3), key=lambda i: abs(n[i]))
        if abs(abs(n[axis]) - 1) > 1e-9 or axis == 2:
            raise SystemExit(f"{case} {sk}: slice {sl['label']} is not in an x or y plane (normal {n})")
        plane = "xy"[axis]; ui = 1 if plane == "x" else 0     # u = y for x-planes, u = x for y-planes (FORMAT.md)
        t = sl["thickness"]
        for pc in sl["pieces"]:
            for region in pc["kerfed"]:                         # local frame, before nesting; kerf 0 → the profile itself
                def to_uz(ring):
                    out = []
                    for u, v in ring:
                        w = [a + c for a, c in zip(apply(M, u, v), centre)]
                        out.append([round(w[ui], 4), round(w[2], 4)])
                        for i in range(3):
                            lo[i] = min(lo[i], w[i]); hi[i] = max(hi[i], w[i])
                            lo_t[i] = min(lo_t[i], w[i] - (t / 2 if i == axis else 0)); hi_t[i] = max(hi_t[i], w[i] + (t / 2 if i == axis else 0))
                    return out
                off = apply(M, *region[0][0])[axis] + centre[axis]
                ribs.append({"name": pc["label"], "plane": plane, "offset_mm": round(off, 4), "thickness_mm": t,
                             "outline_mm": to_uz(region[0]), "holes_mm": [to_uz(h) for h in region[1:]],
                             "lamina_label": pc["label"], "lamina_family": sl["group"], "lamina_sheet": pc["place"][0] + 1})
    p = plan["params"]
    out = {"board_mm": p["thickness"], "kerf_mm": plan["kerf"], "slot_offset_mm": p["slot_offset"],
           "tool": "Lamina 0.3.0 (lamina3d, commit bed1c9a)", "case": case, "scale": sk,
           "coordinates": "paper mm; Lamina's centred world frame shifted back by the scaled solid's bbox centre, so the solid spans [0,0,0]-scale*[W,D,H]",
           "ribs": ribs}
    (HERE / case / f"{case}_{sk}.waffle.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return {"ribs_x_planes": sum(r["plane"] == "x" for r in ribs), "ribs_y_planes": sum(r["plane"] == "y" for r in ribs),
            "x_offsets": sorted({r["offset_mm"] for r in ribs if r["plane"] == "x"}), "y_offsets": sorted({r["offset_mm"] for r in ribs if r["plane"] == "y"}),
            "bbox_rib_midplanes_mm": [round(h - l, 3) for l, h in zip(lo, hi)],
            "bbox_with_board_thickness_mm": [round(h - l, 3) for l, h in zip(lo_t, hi_t)],
            "bbox_min_mm": [round(v, 3) for v in lo_t], "bbox_max_mm": [round(v, 3) for v in hi_t],
            "solid_bbox_mm": [s * e for e in SOLID_BBOX_1_10[case]], "sheets": plan["sheets"], "parts": plan["counts"]["parts"],
            "slot_widths_in_export": slot_widths(raw)}


def slot_widths(raw):
    """Slot widths measured on the exported cut file itself (Lamina's SVG sheets, OUTER + INNER layers): a slot's
    bottom is a short edge whose two neighbours are anti-parallel, perpendicular to it and longer than it (a U turn).
    Returns {width rounded to 0.001 mm: count} over every ring of every sheet."""
    hist = {}
    for f in sorted(raw.glob("*.svg")):
        txt = f.read_text()
        for g in re.findall(r'<g class="(?:OUTER|INNER)"[^>]*>(.*?)</g>', txt, flags=re.S):
            for d in re.findall(r'<path data-label="(?!scale-check)[^"]*" d="([^"]+)"', g):
                pts = [tuple(map(float, q.split(","))) for q in re.findall(r"[ML]([-\d.]+,[-\d.]+)", d)]
                n = len(pts)
                for i in range(n):
                    a, b, c, e = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
                    L = math.dist(b, c); L0 = math.dist(a, b); L2 = math.dist(c, e)
                    if L < 1e-6 or L > 5 or L0 < L or L2 < L:
                        continue
                    d0 = ((b[0] - a[0]) / L0, (b[1] - a[1]) / L0); d1 = ((c[0] - b[0]) / L, (c[1] - b[1]) / L); d2 = ((e[0] - c[0]) / L2, (e[1] - c[1]) / L2)
                    if d0[0] * d2[0] + d0[1] * d2[1] < -0.9999 and abs(d0[0] * d1[0] + d0[1] * d1[1]) < 1e-3:
                        k = f"{L:.3f}"; hist[k] = hist.get(k, 0) + 1
    return dict(sorted(hist.items(), key=lambda kv: -kv[1]))


if __name__ == "__main__":
    report = {}
    for case in CASES:
        for sk in SCALES:
            report[f"{case}_{sk}"] = {"fold": adapt_fold(case, sk), "waffle": adapt_waffle(case, sk)}
    (HERE / "adapt_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))
