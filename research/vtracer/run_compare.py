#!/usr/bin/env python3
"""Measured comparison: VTracer (pip vtracer==0.6.15) vs the FlatPack v4.3.x "From image" auto-trace.

Run (after make_cases.py), with the venv that has vtracer + shapely + numpy + pillow:
    <venv>/bin/python research/vtracer/run_compare.py [--url http://localhost:8765/index.html]

Our tracer is NOT reimplemented: the page is opened in headless Chromium (system Playwright) and its own
functions are called (imgLoadSrc -> calibration -> imgAutoTrace -> renderTraceGate / collectV4Checks).

Outputs (research/vtracer/out/): raw VTracer SVGs, our tool's raw shapes (JSON, image px),
per-run flattened outlines in mm (JSON); research/vtracer/results.json.
"""
import argparse, base64, json, platform, re, sys, time
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union

sys.path.append("/usr/local/lib/python3.13/site-packages")      # system Playwright
from playwright.sync_api import sync_playwright  # noqa: E402
from playwright._repo_version import version as PW_VERSION  # noqa: E402
import vtracer  # noqa: E402

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases"
OUT = HERE / "out"
PX_PER_MM = 10
LEAK_BAND_MM = 0.5      # edge-placement tolerance: traced area outside GT.buffer(0.5 mm) counts as a leak candidate
LEAK_MIN_MM2 = 1.0      # a leak = one connected piece of that outside area larger than 1 mm^2

CASE_LIST = [  # name, file, has ground truth
    ("chair_clean", "chair_clean.png", True),
    ("chair_photo", "chair_photo.jpg", True),
    ("room_h14", "room_h14.jpg", False),
    ("sofa_clean", "sofa_clean.png", True),
]

VT_SETTINGS = {
    "vtracer_default_binary": dict(colormode="binary"),
    # Best effort, chosen from the task (furniture side profiles are straight-edged; small specks are never furniture),
    # set ONCE before looking at any metric and not tuned per case:
    #   mode='polygon'       straight segments instead of splines (laser / hand cut lines are straight)
    #   filter_speckle=16    drop clusters smaller than 16x16 = 256 px (2.56 mm^2 at 10 px/mm)
    "vtracer_best_effort": dict(colormode="binary", mode="polygon", filter_speckle=16),
}

# our tool: controls are set by element id exactly as a student would set them in the UI
OUR_SETTINGS = {
    "ours_default": {},                                   # UI defaults: Remove background, tol 70, clean 4, simplify 0.6, fill, largest
    "ours_dark_on_light": {"img-method": "dark"},         # the UI's other method (threshold 140 default)
}


# ---------------------------------------------------------------- geometry helpers
def ring_area_signed(pts):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return a / 2


def rings_to_geom(rings):
    """Even-odd union of closed rings (mm) -> shapely geometry (holes handled by symmetric difference)."""
    g = Polygon()
    for r in rings:
        if len(r) < 3:
            continue
        p = shapely.make_valid(Polygon(r))
        g = g.symmetric_difference(p)
    return shapely.make_valid(g)


def parse_vtracer_svg(svg, samples=24):
    """vtracer 0.6.x SVG: <path d="M.. L.. C.. Z" fill=".." transform="translate(tx,ty)"/>, absolute commands only.
    Returns list of paths: {fill, rings:[[(x,y)...]], nodes, segments}. Cubics flattened with `samples` points each."""
    out = []
    for m in re.finditer(r'<path d="([^"]*)" fill="([^"]*)" transform="translate\(([-\d.]+),([-\d.]+)\)"/>', svg):
        d, fill, tx, ty = m.group(1), m.group(2), float(m.group(3)), float(m.group(4))
        toks = re.findall(r"[MLCZ]|-?\d+(?:\.\d+)?(?:e-?\d+)?", d.replace(",", " "))
        rings, cur, i, cmd, nodes, segs = [], [], 0, None, 0, 0
        while i < len(toks):
            t = toks[i]
            if t in "MLCZ":
                cmd = t; i += 1
                if t == "Z":
                    if cur: rings.append(cur); cur = []
                continue
            if cmd == "M":
                if cur: rings.append(cur)
                cur = [(float(toks[i]) + tx, float(toks[i + 1]) + ty)]; i += 2; nodes += 1; cmd = "L"
            elif cmd == "L":
                cur.append((float(toks[i]) + tx, float(toks[i + 1]) + ty)); i += 2; nodes += 1; segs += 1
            elif cmd == "C":
                c = [float(v) for v in toks[i:i + 6]]; i += 6
                p0 = np.array(cur[-1]); p1 = np.array([c[0] + tx, c[1] + ty]); p2 = np.array([c[2] + tx, c[3] + ty]); p3 = np.array([c[4] + tx, c[5] + ty])
                for k in range(1, samples + 1):
                    s = k / samples
                    q = (1 - s) ** 3 * p0 + 3 * (1 - s) ** 2 * s * p1 + 3 * (1 - s) * s ** 2 * p2 + s ** 3 * p3
                    cur.append((float(q[0]), float(q[1])))
                nodes += 1; segs += 1
            else:
                raise ValueError(f"unexpected token {t!r} after {cmd!r}")
        if cur: rings.append(cur)
        # drop duplicated closing point
        rings = [r[:-1] if len(r) > 1 and r[0] == r[-1] else r for r in rings]
        out.append({"fill": fill, "rings": rings, "nodes": nodes, "segments": segs})
    return out


def px_to_mm(rings):
    return [[(x / PX_PER_MM, y / PX_PER_MM) for x, y in r] for r in rings]


def edge_qa(geom, W, H):
    """The same rule as our tool's gate (index.html imgAutoTrace, v4.3 P1-12), applied in px: bbox fills > 85 %
    of the picture or the bbox touches >= 3 picture edges (2 px margin). Used to ask: would VTracer's output
    have tripped OUR gate? (VTracer itself has no such gate.)"""
    if geom.is_empty:
        return {"bboxFrac": 0, "edges": 0, "suspect": False}
    x0, y0, x1, y1 = [v * PX_PER_MM for v in geom.bounds]
    m = 2
    edges = sum([x0 <= m, y0 <= m, x1 >= W - 1 - m, y1 >= H - 1 - m])
    frac = (x1 - x0) * (y1 - y0) / (W * H)
    return {"bboxFrac": round(frac, 4), "edges": int(edges), "suspect": bool(frac > 0.85 or edges >= 3)}


def metrics(geom, gt):
    if gt is None:
        return {}
    inter = geom.intersection(gt).area
    uni = geom.union(gt).area
    outside = geom.difference(gt)
    out_band = geom.difference(gt.buffer(LEAK_BAND_MM, join_style="mitre"))
    pieces = [g for g in getattr(out_band, "geoms", [out_band]) if not g.is_empty]
    leak_pieces = [round(g.area, 3) for g in pieces if g.area > LEAK_MIN_MM2]
    missing = gt.difference(geom)
    hd = geom.boundary.hausdorff_distance(gt.boundary) if not geom.is_empty else None
    return {
        "iou": round(inter / uni, 5) if uni else 0.0,
        "area_mm2": round(geom.area, 3),
        "gt_area_mm2": round(gt.area, 3),
        "area_error_pct": round(100 * (geom.area - gt.area) / gt.area, 3),
        "outside_gt_mm2": round(outside.area, 3),
        "missing_gt_mm2": round(missing.area, 3),
        "outside_beyond_band_mm2": round(out_band.area, 3),
        "leak_pieces_mm2": sorted(leak_pieces, reverse=True)[:10],
        "background_leak": bool(leak_pieces),
        "hausdorff_boundary_mm": round(hd, 3) if hd is not None else None,
    }


# ---------------------------------------------------------------- VTracer
def run_vtracer(case, path, gt, W, H):
    res = {}
    raw = path.read_bytes()
    fmt = path.suffix.lstrip(".").replace("jpg", "jpeg")
    for sname, kw in VT_SETTINGS.items():
        t0 = time.perf_counter()
        try:
            svg = vtracer.convert_raw_image_to_svg(raw, img_format=fmt, **kw)
        except Exception as e:  # record, never invent
            res[sname] = {"error": repr(e)}; continue
        wall = time.perf_counter() - t0
        (OUT / f"{case}__{sname}.svg").write_text(svg)
        paths = parse_vtracer_svg(svg)
        fills = sorted({p["fill"] for p in paths})
        # Region selection: in binary mode VTracer 0.6.15 emits ONLY foreground clusters (pixels with R < 128,
        # cmdapp/src/converter.rs binary_image_to_svg), every one filled #000000. So the "dark region" = every path.
        # A user cutting VTracer's output gets the union of all paths ("all"); we also report the single largest
        # path ("largest") = what a user would keep after deleting everything else by hand.
        geoms = [rings_to_geom(px_to_mm(p["rings"])) for p in paths]
        allg = unary_union(geoms) if geoms else Polygon()
        li = int(np.argmax([g.area for g in geoms])) if geoms else None
        larg = geoms[li] if geoms else Polygon()
        (OUT / f"{case}__{sname}.outline_mm.json").write_text(json.dumps({
            "units": "mm, image frame (y down), 10 px/mm", "paths": [px_to_mm(p["rings"]) for p in paths]}, separators=(",", ":")))
        res[sname] = {
            "settings": kw, "wall_s": round(wall, 4), "n_paths": len(paths), "fills": fills,
            "nodes_all": sum(p["nodes"] for p in paths),
            "nodes_largest": paths[li]["nodes"] if geoms else 0,
            "rings_largest": len(paths[li]["rings"]) if geoms else 0,
            "warns_or_stops": False,
            "warning_text": None,
            "would_trip_our_gate": edge_qa(allg, W, H),
            "metrics_all_paths": metrics(allg, gt),
            "metrics_largest_path": metrics(larg, gt),
        }
    return res


# ---------------------------------------------------------------- our tool (headless)
JS_TRACE = r"""
async ([dataUrl, controls, calib]) => {
  // project at 1:10 so paper mm = image px / 10 (matches the ground-truth frame)
  setScale(10); imgSetScale(10);
  setPieceMethod('image');                       // piece #1 becomes a "From image" piece (gate + checks active)
  imgState.loaded = false;
  imgLoadSrc(dataUrl);
  const t0 = performance.now();
  while (!imgState.loaded) await new Promise(r => setTimeout(r, 10));
  const loadMs = performance.now() - t0;
  // calibration as a student would click it: two points on a known horizontal dimension
  if (calib) { imgState.calib.p1 = calib.p1; imgState.calib.p2 = calib.p2; imgSetCalibCm(calib.cm); }
  // reset every trace control to its HTML default, then apply this run's changes (by element id)
  ['img-method','img-bgtol','img-thr','img-clean','img-tol'].forEach(id => { const el = document.getElementById(id);
    el.value = el.tagName === 'SELECT' ? [...el.options].find(o => o.defaultSelected).value : el.defaultValue; });
  ['img-shadow','img-fill','img-invert','img-largest'].forEach(id => { const el = document.getElementById(id); el.checked = el.defaultChecked; });
  for (const [id, v] of Object.entries(controls)) { const el = document.getElementById(id); if (el.type === 'checkbox') el.checked = !!v; else el.value = v; }
  imgMethodUI();
  const toasts = []; const _t = window.showToast; window.showToast = m => { toasts.push(m); _t(m); };
  const t1 = performance.now();
  imgAutoTrace();
  const traceMs = performance.now() - t1;
  window.showToast = _t;
  renderTraceGate(); refreshV4();
  const gate = document.getElementById('img-trace-gate');
  const p = pieces[activePiece];
  const checks = collectV4Checks(v4Cfg(), v4Nest).filter(i => i.cls === 'err').map(i => i.en);
  const ctl = {}; ['img-method','img-bgtol','img-thr','img-clean','img-tol','img-shadow','img-fill','img-invert','img-largest'].forEach(id => {
    const el = document.getElementById(id); ctl[id] = el.type === 'checkbox' ? el.checked : el.value; });
  return {
    W: imgState.W, H: imgState.H, mmPerPxPaper: imgMmPerPx(), loadMs, traceMs, toasts, controls: ctl,
    shapes: imgState.shapes.map(s => ({ kind: s.kind, closed: s.closed, pts: s.pts })),
    traceQA: imgState.traceQA || null,
    traceInfo: document.getElementById('img-trace-info').textContent,
    gateVisible: !gate.classList.contains('hidden'), gateIsInfoOnly: gate.classList.contains('v4-info'),
    gateText: document.getElementById('img-trace-gate-msg').textContent,
    traceOk: !!p.traceOk, printBlockingChecks: checks, toolVersion: TOOL_VERSION,
  };
}
"""


def run_ours(page, case, path, gt, gtj, W, H):
    res = {}
    mime = "image/png" if path.suffix == ".png" else "image/jpeg"
    data = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
    calib = None
    if gtj is not None:
        # known width of the piece's ground line in px (exact from the GT): x from min to max of the polygon
        xs = [p[0] for p in gtj["polygon_img_mm"]]
        calib = {"p1": [min(xs) * PX_PER_MM, 0], "p2": [max(xs) * PX_PER_MM, 0], "cm": (max(xs) - min(xs)) * 10 / 10}
        # (max-min) mm on paper at 1:10 = (max-min) cm real -> paper mm per px = (cm*10/10)/px = 0.1
    for sname, controls in OUR_SETTINGS.items():
        t0 = time.perf_counter()
        try:
            r = page.evaluate(JS_TRACE, [data, controls, calib])
        except Exception as e:
            res[sname] = {"error": repr(e)}; continue
        wall = time.perf_counter() - t0
        (OUT / f"{case}__{sname}.shapes_px.json").write_text(json.dumps(r, separators=(",", ":")))
        cuts = [s["pts"] for s in r["shapes"] if s["kind"] == "cut"]
        geom = rings_to_geom(px_to_mm([[tuple(q) for q in c] for c in cuts])) if cuts else Polygon()
        (OUT / f"{case}__{sname}.outline_mm.json").write_text(json.dumps({
            "units": "mm, image frame (y down), 10 px/mm", "paths": px_to_mm(cuts)}, separators=(",", ":")))
        qa = r["traceQA"] or {}
        res[sname] = {
            "settings": r["controls"], "wall_s": round(wall, 4), "trace_ms_in_page": round(r["traceMs"], 1),
            "image_px": [r["W"], r["H"]], "paper_mm_per_px": r["mmPerPxPaper"],
            "n_paths": len(cuts), "nodes_all": sum(len(c) for c in cuts),
            "nodes_largest": max((len(c) for c in cuts), default=0),
            "toasts": r["toasts"], "trace_info": r["traceInfo"],
            "traceQA": {k: qa.get(k) for k in ("bboxFrac", "edges", "suspect", "keptArea")} | {"n_dropped": len(qa.get("dropped") or [])},
            "warns_or_stops": bool(qa.get("suspect")) or not cuts,
            "warning_text": r["gateText"] if qa.get("suspect") else (r["toasts"][-1] if not cuts and r["toasts"] else None),
            "gate_visible": r["gateVisible"], "gate_text": r["gateText"],
            "print_blocked_until_student_confirms": any("ONLY the furniture" in c for c in r["printBlockingChecks"]),
            "print_blocking_checks": r["printBlockingChecks"],
            "metrics_all_paths": metrics(geom, gt),
            "tool_version": r["toolVersion"],
        }
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8765/index.html")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    results = {"meta": {"python": platform.python_version(), "shapely": shapely.__version__, "numpy": np.__version__,
                        "playwright": PW_VERSION, "url": a.url, "px_per_mm": PX_PER_MM,
                        "leak_rule": f"connected piece of (traced - GT.buffer({LEAK_BAND_MM} mm, mitre)) with area > {LEAK_MIN_MM2} mm^2",
                        "run_started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}, "cases": {}}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        results["meta"]["chromium"] = br.version
        page = br.new_page(viewport={"width": 1400, "height": 1000})
        console = []
        page.on("console", lambda m: console.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: console.append(f"pageerror: {e}"))
        page.goto(a.url)
        page.wait_for_function("typeof v4Ready !== 'undefined' && v4Ready === true")
        for case, fname, has_gt in CASE_LIST:
            path = CASES / fname
            if not path.exists():
                results["cases"][case] = {"error": f"missing {path}"}; continue
            gtj = json.loads((CASES / f"{case}.gt.json").read_text())
            gt = Polygon(gtj["polygon_img_mm"]) if has_gt else None
            from PIL import Image
            W, H = Image.open(path).size
            entry = {"image": f"cases/{fname}", "image_px": [W, H], "ground_truth": f"cases/{case}.gt.json" if has_gt else None}
            entry["runs"] = run_vtracer(case, path, gt, W, H)
            entry["runs"].update(run_ours(page, case, path, gt, gtj if has_gt else None, W, H))
            results["cases"][case] = entry
            print(case, {k: (v.get("metrics_all_paths", {}).get("iou"), v.get("n_paths"), v.get("warns_or_stops")) for k, v in entry["runs"].items()})
        results["meta"]["browser_console_errors"] = console
        br.close()
    (HERE / "results.json").write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
