#!/usr/bin/env python3
"""Adapter: Export Paper Model (Blender add-on, v1.4.2 @ d688dcd) raw SVG -> normalised net SVG (research/FORMAT.md).

Usage:  python3 adapt.py <raw.svg | raw_page1.svg ...> -o <case>_<scale>.net.svg [--stats stats.json]

Raw format facts (from the add-on source, see settings.md for file:line):
  * One <svg> per page, viewBox in mm (svg.py:201-203); multi-page output is written as
    <name>_page1.svg, <name>_page2.svg ... (svg.py:65).
  * Per island a <g> with <path class='outer'> (one 'M ... Z' loop per boundary loop, tabs included,
    svg.py:137-153,185), <path class='convex'> / <path class='concave'> (one 'M a L b' segment per fold,
    svg.py:155-181), <path class='sticker'> (tab fills, svg.py:108-135), <text> labels with a
    transform matrix (svg.py:196-199). Path data uses absolute M/L/Z only, coordinates already in page mm.
  * The drawing shows each face from its normal side (UVFace.flatten = z_up_matrix(normal), unfolder.py:1143;
    y is mirrored only to SVG y-down, svg.py:22, which is not a mirror of the picture). In this mesh set no
    face is 'flipped', so the viewer of the raw SVG sees the printed (normal) side: no mirroring is applied.
  * class 'convex' = edge folded to a convex angle seen from the drawn side = folds away from the viewer
    -> data-fold="mountain"; class 'concave' -> "valley". The add-on already swaps the two classes for
    inside-out islands before writing (svg.py:171-172), so the classes are relative to the drawn side.
The adapter only re-encodes what the tool drew; it never corrects the tool's fold classes.
"""
import argparse, json, math, re, sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
PAGE_GAP_MM = 10.0
NUM = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"


def subpaths(d):
    """Split absolute M/L/Z path data into lists of points; returns [(points, closed)]."""
    toks = re.findall(r"[MLZmlz]|" + NUM, d)
    out, cur, cmd, closed = [], None, None, False
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in "MLZ":
            cmd = t
            if t == "M":
                if cur:
                    out.append((cur, closed))
                cur, closed = [], False
            elif t == "Z":
                closed = True
                out.append((cur, closed))
                cur = None
            i += 1
            continue
        if t in "mlz":
            raise ValueError("relative path commands are not expected in Export Paper Model output")
        x, y = float(toks[i]), float(toks[i + 1])
        cur.append((x, y))
        i += 2
    if cur:
        out.append((cur, closed))
    return out


def dedupe(pts, eps=1e-6):
    res = []
    for p in pts:
        if not res or abs(p[0] - res[-1][0]) > eps or abs(p[1] - res[-1][1]) > eps:
            res.append(p)
    if len(res) > 1 and abs(res[0][0] - res[-1][0]) <= eps and abs(res[0][1] - res[-1][1]) <= eps:
        res.pop()
    return res


def shoelace(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def tag(el):
    return el.tag.split("}")[-1]


def parse_page(path):
    root = ET.parse(path).getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    w, h = vb[2], vb[3]
    for k in ("width", "height"):
        if not root.get(k, "").endswith("mm"):
            raise ValueError(f"{path}: {k} is not in mm")
    page = {"w": w, "h": h, "islands": []}
    # island groups: <g> elements that directly contain a path.outer
    for g in root.iter():
        if tag(g) != "g":
            continue
        kids = list(g)
        if not any(tag(k) == "path" and k.get("class") == "outer" for k in kids):
            continue
        isl = {"outlines": [], "folds": [], "tabs": [], "labels": []}
        for k in kids:
            t, cls = tag(k), k.get("class")
            if t == "path" and cls == "outer":
                isl["outlines"] += [dedupe(p) for p, c in subpaths(k.get("d"))]
            elif t == "path" and cls in ("convex", "concave"):
                for p, c in subpaths(k.get("d")):
                    if len(p) != 2:
                        raise ValueError("fold subpath with %d points" % len(p))
                    isl["folds"].append((p[0], p[1], "mountain" if cls == "convex" else "valley", cls))
            elif t == "path" and cls == "sticker":
                isl["tabs"] += [dedupe(p) for p, c in subpaths(k.get("d"))]
            elif t == "path" and cls == "freestyle":
                for p, c in subpaths(k.get("d")):
                    isl["folds"].append((p[0], p[1], "unmarked", cls))
            elif t == "text":
                m = re.match(r"\s*(matrix|translate)\(([^)]*)\)", k.get("transform", ""))
                vals = [float(v) for v in re.findall(NUM, m.group(2))] if m else []
                mat = vals if m and m.group(1) == "matrix" else [1, 0, 0, 1] + (vals + [0, 0])[:2]
                text = "".join(k.itertext())
                size = re.search(r"font-size:\s*(" + NUM + ")", k.get("style", ""))
                isl["labels"].append((mat, text, float(size.group(1)) if size else 3.0))
            elif t == "g":
                # arrow markers are nested <g><path class=arrow/><text/></g>
                for kk in k:
                    if tag(kk) == "text":
                        m = re.match(r"\s*translate\(([^)]*)\)", kk.get("transform", ""))
                        vals = [float(v) for v in re.findall(NUM, m.group(1))] if m else [0, 0]
                        size = re.search(r"font-size:\s*(" + NUM + ")", kk.get("style", ""))
                        isl["labels"].append(([1, 0, 0, 1] + vals[:2], "".join(kk.itertext()),
                                              float(size.group(1)) if size else 3.0))
        page["islands"].append(isl)
    return page


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="+", help="raw page SVG(s) in page order")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--stats")
    a = ap.parse_args()

    pages = [parse_page(p) for p in a.pages]
    cut, score, labels = [], [], []
    x_off = 0.0
    stats = {"pages": len(pages), "parts": 0, "outline_loops": 0, "folds": {"mountain": 0, "valley": 0, "unmarked": 0},
             "tab_count": 0, "degenerate_tabs": 0, "outline_area_mm2": 0.0, "tab_area_mm2": 0.0,
             "fold_lengths_mm": []}
    part = 0
    for pi, pg in enumerate(pages):
        for isl in pg["islands"]:
            part += 1
            for loop in isl["outlines"]:
                pts = [(x + x_off, y) for x, y in loop]
                d = "M " + " L ".join(fmt(x) + " " + fmt(y) for x, y in pts) + " Z"
                cut.append(f'<path data-part="{part}" data-page="{pi + 1}" d="{d}"/>')
                stats["outline_loops"] += 1
                stats["outline_area_mm2"] += abs(shoelace(loop))
            tab_vertex_sets = [t for t in isl["tabs"]]
            def is_tab_hinge(p, q):
                # a tab's polygon starts and ends on the edge it hangs from (unfolder.py Sticker.points)
                for t in tab_vertex_sets:
                    if any(math.dist(p, v) < 1e-3 for v in t) and any(math.dist(q, v) < 1e-3 for v in t):
                        return True
                return False
            for p, q, fold, cls in isl["folds"]:
                L = math.dist(p, q)
                kind = "tab-hinge" if is_tab_hinge(p, q) else "panel"
                stats.setdefault("folds_by_kind", {}).setdefault(kind, {"mountain": 0, "valley": 0, "unmarked": 0})[fold] += 1
                score.append(f'<line data-part="{part}" data-fold="{fold}" data-kind="{kind}" data-raw-class="{cls}" '
                             f'x1="{fmt(p[0] + x_off)}" y1="{fmt(p[1])}" x2="{fmt(q[0] + x_off)}" y2="{fmt(q[1])}"/>')
                stats["folds"][fold] += 1
                stats["fold_lengths_mm"].append(round(L, 4))
            for t in isl["tabs"]:
                ar = abs(shoelace(t)) if len(t) >= 3 else 0.0
                stats["tab_count"] += 1
                stats["tab_area_mm2"] += ar
                if ar < 1e-3:
                    stats["degenerate_tabs"] += 1
            for mat, text, size in isl["labels"]:
                m = mat[:4] + [mat[4] + x_off, mat[5]]
                labels.append(f'<text transform="matrix({" ".join(fmt(v) for v in m)})" font-size="{fmt(size)}" '
                              f'text-anchor="middle">{text}</text>')
        x_off += pg["w"] + (PAGE_GAP_MM if pi < len(pages) - 1 else 0)
    stats["parts"] = part
    stats["panel_area_mm2"] = stats["outline_area_mm2"] - stats["tab_area_mm2"]
    W, H = x_off, max(p["h"] for p in pages)
    frames = "".join(f'<rect x="{fmt(sum(pp["w"] + PAGE_GAP_MM for pp in pages[:i]))}" y="0" width="{fmt(p["w"])}" '
                     f'height="{fmt(p["h"])}" fill="none" stroke="#bbb" stroke-width="0.2"/>' for i, p in enumerate(pages))
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="{SVG_NS}" version="1.1" width="{fmt(W)}mm" height="{fmt(H)}mm" viewBox="0 0 {fmt(W)} {fmt(H)}"
     data-tool="Export Paper Model 1.4.2 (d688dcd)" data-pages="{len(pages)}" data-printed-side="viewer">
<g id="00_PAGES">{frames}</g>
<g id="01_CUT_RED" fill="none" stroke="#e00000" stroke-width="0.25">
{chr(10).join(cut)}
</g>
<g id="02_SCORE_BLUE" stroke="#0050ff" stroke-width="0.25">
{chr(10).join(score)}
</g>
<g id="03_LABELS_BLACK" fill="#000">
{chr(10).join(labels)}
</g>
</svg>
'''
    with open(a.out, "w") as f:
        f.write(svg)
    if a.stats:
        with open(a.stats, "w") as f:
            json.dump(stats, f, indent=1)
    print(json.dumps({k: v for k, v in stats.items() if k != "fold_lengths_mm"}))


if __name__ == "__main__":
    main()
