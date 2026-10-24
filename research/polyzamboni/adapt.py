#!/usr/bin/env python3
"""Adapter: PolyZamboni (Blender add-on, v1.3.1 @ a6b880e) raw SVG pages -> normalised net SVG (research/FORMAT.md).

Usage:  python3 -I adapt.py <raw_page1.svg> [raw_page2.svg ...] -o <case>_<scale>.net.svg [--stats stats.json]
                            [--print-on-inside]   (only if the export used the add-on default print_on_inside=True)

Raw format facts (from the add-on source; file:line in settings.md):
  * The exporter is matplotlib (exporters.py:118-445). One SVG per page, `<prefix>_page<N>.svg` (exporters.py:431).
    Page = one figure of paper size in inches, axes limits = paper size in cm (exporters.py:132-147), so the
    SVG user unit is the point (1/72 in): mm = pt * 25.4/72. matplotlib writes y-down (y flipped from the
    y-up axes), which is not a mirror of the picture.
  * Every line is its own <g id="line2d_N"><path d="M x y L x y" style=...> (exporters.py:182-188).
      - cut edges: line style cut_edge_ls (default "-", solid), clipped to the axes rectangle (exporters.py:224-227)
      - fold edges: convex -> convex_fold_edge_ls (default ".."), concave -> concave_fold_edge_ls (default "--.")
        (exporters.py:239-255, properties.py:349-358); this includes the hinge line of every glue flap
        (fold_edges_at_flaps, printprepper.py:283-286)
      - glue flap outline edges: glue_flap_ls (default "-", solid) clipped by a compound mask path
        (page rectangle + the component's triangles) (exporters.py:165-180, 276-280).
    matplotlib scales dash patterns by the line width (0.5 by default, properties.py:333-336), e.g. ".." =
    (0,(2,4,2,4)) -> stroke-dasharray "1,2,1,2".
  * Text (edge numbers, build step) is drawn as glyph <path>s inside <g id="text_N"> with an XML comment
    holding the string and a translate/rotate/scale transform.
  * A raster <image> (texture/colour render, exporters.py:303-353) and filled glue-flap <path>s are dropped here.
  * Fold class -> direction: is_convex comes from bmesh BMEdge.is_convex (printprepper.py:286,293), i.e. relative
    to the face normals (= printed/outside side). With print_on_inside=False the faces are drawn as seen from the
    normal side (2D frame x = edge, y = n x edge, geometry.py:140-147; not flipped, exporters.py:149-155,360,377),
    so the viewer sees the printed side and convex = printed side outside = folds away from viewer = mountain;
    concave = valley. With print_on_inside=True (add-on default) the page is mirrored about x = W/2 so the viewer
    sees the inside: the adapter then mirrors it back (--print-on-inside) and the mapping stays the same.
The adapter only re-encodes what the tool drew. It refuses (exit 2) when a page is clipped (geometry beyond the
page) or the cut outline does not close, instead of inventing missing geometry.
"""
import argparse, json, math, re, sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
PT = 25.4 / 72.0
PAGE_GAP_MM = 10.0
EPS = 1e-3            # mm, endpoint matching
NUM = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
LW = 0.5              # LineExportSettings.line_width default
STYLES = {"-": None, "..": (2, 4, 2, 4), "-.": (8, 4, 2, 4), "--.": (8, 4, 8, 4, 2, 4), "-..": (8, 4, 2, 4, 2, 4)}
CONVEX_LS, CONCAVE_LS = "..", "--."   # defaults used in the export


def dash_key(ls):
    pat = STYLES[ls]
    return None if pat is None else ",".join(("%g" % (v * LW)) for v in pat)


def tag(el):
    return el.tag.split("}")[-1]


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def count_subpaths(d):
    return len(re.findall(r"[Mm]", d))


def parse_page(path, mirror):
    root = ET.parse(path).getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    W, H = vb[2] * PT, vb[3] * PT
    clips = {}
    for el in root.iter():
        if tag(el) == "clipPath":
            p = [k for k in el if tag(k) == "path"]
            clips[el.get("id")] = count_subpaths(p[0].get("d")) if p else 0
    conv, conc = dash_key(CONVEX_LS), dash_key(CONCAVE_LS)

    def X(x):
        x = float(x) * PT
        return W - x if mirror else x

    page = {"w": W, "h": H, "cut": [], "flap": [], "folds": [], "labels": [], "clipped": False, "file": path}
    for g in root.iter():
        if tag(g) != "g":
            continue
        gid = g.get("id", "")
        if gid.startswith("line2d_"):
            for p in g:
                if tag(p) != "path":
                    continue
                if p.get("d") is None:
                    # matplotlib writes a path without data when the whole segment lies outside the axes clip
                    page["clipped"] = True
                    page["omitted_segments"] = page.get("omitted_segments", 0) + 1
                    continue
                pts = [(X(a), float(b) * PT) for a, b in re.findall(r"[ML]\s*(" + NUM + r")\s+(" + NUM + ")", p.get("d"))]
                if len(pts) != 2:
                    raise ValueError(f"{path} {gid}: expected 2-point segment, got {len(pts)}")
                for x, y in pts:
                    if x < -EPS or y < -EPS or x > W + EPS or y > H + EPS:
                        page["clipped"] = True
                st = p.get("style", "")
                m = re.search(r"stroke-dasharray:\s*([^;]+)", st)
                dash = m.group(1).strip().replace(" ", "") if m else None
                cm = re.search(r"url\(#([^)]+)\)", p.get("clip-path", ""))
                clip_n = clips.get(cm.group(1), 1) if cm else 1
                if dash is None:
                    (page["flap"] if clip_n > 1 else page["cut"]).append(tuple(pts))
                elif dash == conv:
                    page["folds"].append((pts[0], pts[1], "convex"))
                elif dash == conc:
                    page["folds"].append((pts[0], pts[1], "concave"))
                else:
                    raise ValueError(f"{path} {gid}: unknown dash pattern {dash}")
    # labels: ElementTree drops XML comments (which hold the label strings) -> regex over the file text
    s = open(path, encoding="utf-8").read()
    labels = []
    for m in re.finditer(r'<g id="text_\d+">\s*<!--\s*(.*?)\s*-->\s*<g transform="([^"]*)"', s):
        text, tr = m.group(1), m.group(2)
        t = re.search(r"translate\((" + NUM + r")[ ,]+(" + NUM + r")\)", tr)
        r = re.search(r"rotate\((" + NUM + r")\)", tr)
        sc = re.search(r"scale\((" + NUM + r")", tr)
        x, y = X(t.group(1)), float(t.group(2)) * PT
        ang = float(r.group(1)) if r else 0.0
        if mirror:
            ang = -ang
        size_mm = (float(sc.group(1)) * 100.0) * PT if sc else 2.0   # DejaVu glyph units: scale = fontsize/100
        labels.append((x, y, ang, text, size_mm))
    page["labels"] = labels
    return page


def key(p):
    return (round(p[0] / EPS), round(p[1] / EPS))


def chain_loops(segs):
    """Chain undirected segments into closed loops. Returns (loops, open_chains)."""
    adj = {}
    for i, (a, b) in enumerate(segs):
        adj.setdefault(key(a), []).append((i, b))
        adj.setdefault(key(b), []).append((i, a))
    used, loops, opens = set(), [], []
    for i, (a, b) in enumerate(segs):
        if i in used:
            continue
        used.add(i)
        loop, cur, start = [a, b], b, key(a)
        closed = False
        while True:
            if key(cur) == start:
                closed = True
                loop.pop()
                break
            nxt = [(j, q) for j, q in adj.get(key(cur), []) if j not in used]
            if not nxt:
                break
            j, q = nxt[0]
            used.add(j)
            loop.append(q)
            cur = q
        (loops if closed else opens).append(loop)
    return loops, opens


def flap_groups(segs):
    """Glue flaps in emission order: the exporter draws each flap's 2-3 edges consecutively, each starting where the
    previous one ended (exporters.py:276-280, printprepper.py:339-342). Group consecutive connected segments.
    (Chaining by shared vertices alone would merge two flaps that meet at a corner.)"""
    out = []
    for a, b in segs:
        if out and key(out[-1][-1]) == key(a) and len(out[-1]) < 4:
            out[-1].append(b)
        else:
            out.append([a, b])
    return out, [g for g in out if len(g) < 3]


def open_chains(segs):
    """Chain flap edges into open polylines (each glue flap = 2 or 3 edges from hinge end to hinge end)."""
    loops, opens = chain_loops(segs)
    # chain_loops starts mid-chain sometimes; rebuild from degree-1 nodes
    deg = {}
    for a, b in segs:
        deg[key(a)] = deg.get(key(a), 0) + 1
        deg[key(b)] = deg.get(key(b), 0) + 1
    adj = {}
    for i, (a, b) in enumerate(segs):
        adj.setdefault(key(a), []).append((i, a, b))
        adj.setdefault(key(b), []).append((i, b, a))
    used, out = set(), []
    for k0, d in deg.items():
        if d != 1:
            continue
        for i, p, q in adj[k0]:
            if i in used:
                continue
            used.add(i)
            poly = [p, q]
            while deg.get(key(poly[-1]), 0) == 2:
                nxt = [(j, qq) for j, pp, qq in adj[key(poly[-1])] if j not in used]
                if not nxt:
                    break
                used.add(nxt[0][0])
                poly.append(nxt[0][1])
            out.append(poly)
    return out, [segs[i] for i in range(len(segs)) if i not in used]


def shoelace(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--stats")
    ap.add_argument("--print-on-inside", action="store_true")
    a = ap.parse_args()

    pages = [parse_page(p, a.print_on_inside) for p in a.pages]
    stats = {"pages": len(pages), "empty_pages": 0, "parts": 0, "folds": {"mountain": 0, "valley": 0, "unmarked": 0},
             "folds_by_kind": {}, "glue_flaps": 0, "outline_area_mm2": 0.0, "flap_area_mm2": 0.0, "fold_lengths_mm": [],
             "cut_edge_lengths_mm": [], "labels": 0, "mirrored": a.print_on_inside, "refused": None}
    problems = []
    for pg in pages:
        if pg["clipped"]:
            problems.append(f"{pg['file']}: geometry reaches beyond the page (matplotlib clipped it at the page edge; "
                            f"{pg.get('omitted_segments', 0)} line segment(s) written without path data)")
        if not (pg["cut"] or pg["flap"] or pg["folds"]):
            stats["empty_pages"] += 1
    cut, score, labels = [], [], []
    x_off, part = 0.0, 0
    for pi, pg in enumerate(pages):
        outline_segs = pg["cut"] + pg["flap"]
        stats["cut_edge_lengths_mm"] += [round(math.dist(*s), 4) for s in pg["cut"]]
        loops, opens = chain_loops(outline_segs)
        if opens:
            problems.append(f"{pg['file']}: {len(opens)} open outline chain(s), cut outline does not close")
        flaps, stray = flap_groups(pg["flap"])
        if stray:
            problems.append(f"{pg['file']}: {len(stray)} glue flap(s) with fewer than 2 edges")
        hinges = {frozenset((key(f[0]), key(f[-1]))): f for f in flaps}
        stats["glue_flaps"] += len(flaps)
        for f in flaps:
            stats["flap_area_mm2"] += abs(shoelace(f))      # polygon closed by its hinge
        # parts: outer loops; a loop inside another loop would be a hole (none expected; reported)
        loop_areas = [abs(shoelace(l)) for l in loops]
        for li, loop in enumerate(loops):
            part += 1
            stats["outline_area_mm2"] += loop_areas[li]
            d = "M " + " L ".join(fmt(x + x_off) + " " + fmt(y) for x, y in loop) + " Z"
            cut.append(f'<path data-part="{part}" data-page="{pi + 1}" d="{d}"/>')
        for p, q, cls in pg["folds"]:
            fold = "mountain" if cls == "convex" else "valley"
            kind = "tab-hinge" if frozenset((key(p), key(q))) in hinges else "panel"
            stats["folds"][fold] += 1
            stats["folds_by_kind"].setdefault(kind, {"mountain": 0, "valley": 0, "unmarked": 0})[fold] += 1
            stats["fold_lengths_mm"].append(round(math.dist(p, q), 4))
            score.append(f'<line data-page="{pi + 1}" data-fold="{fold}" data-kind="{kind}" data-raw-class="{cls}" '
                         f'x1="{fmt(p[0] + x_off)}" y1="{fmt(p[1])}" x2="{fmt(q[0] + x_off)}" y2="{fmt(q[1])}"/>')
        for x, y, ang, text, size in pg["labels"]:
            stats["labels"] += 1
            labels.append(f'<text transform="translate({fmt(x + x_off)} {fmt(y)}) rotate({fmt(ang)})" '
                          f'font-size="{fmt(size)}" text-anchor="middle" dominant-baseline="central">{text}</text>')
        x_off += pg["w"] + (PAGE_GAP_MM if pi < len(pages) - 1 else 0)
    stats["parts"] = part
    stats["panel_area_mm2"] = stats["outline_area_mm2"] - stats["flap_area_mm2"]
    if problems:
        stats["refused"] = problems
        if a.stats:
            json.dump(stats, open(a.stats, "w"), indent=1)
        print("REFUSED: " + " | ".join(problems), file=sys.stderr)
        sys.exit(2)
    W, H = x_off, max(p["h"] for p in pages)
    frames = "".join(f'<rect x="{fmt(sum(pp["w"] + PAGE_GAP_MM for pp in pages[:i]))}" y="0" width="{fmt(p["w"])}" '
                     f'height="{fmt(p["h"])}" fill="none" stroke="#bbb" stroke-width="0.2"/>' for i, p in enumerate(pages))
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="{SVG_NS}" version="1.1" width="{fmt(W)}mm" height="{fmt(H)}mm" viewBox="0 0 {fmt(W)} {fmt(H)}"
     data-tool="PolyZamboni 1.3.1 (a6b880e)" data-pages="{len(pages)}" data-printed-side="viewer">
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
    open(a.out, "w").write(svg)
    if a.stats:
        json.dump(stats, open(a.stats, "w"), indent=1)
    print(json.dumps({k: v for k, v in stats.items() if k not in ("fold_lengths_mm", "cut_edge_lengths_mm")}))


if __name__ == "__main__":
    main()
