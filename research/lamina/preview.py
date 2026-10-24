"""PNG previews (system python3 + Playwright Chromium):
  <case>/preview/<case>_<s>.net.png            the normalised net (red cut, blue score: solid = mountain, dashed = valley)
  <case>/preview/raw_<tech>_<s>_sheetN.png     each raw Lamina sheet SVG as exported
  <case>/preview/<case>_<s>.waffle_iso.png     the normalised waffle JSON drawn in its assembled 3D position (isometric)
"""
from __future__ import annotations
import json, math, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
CASES = ["chair", "table", "sofa_curved"]
SCALES = ["1-10", "1-20"]


def iso_svg(wj):
    a = math.radians(30)
    P = lambda x, y, z: ((x - y) * math.cos(a), -(x + y) * math.sin(a) - z)   # noqa: E731
    polys = []
    for r in wj["ribs"]:
        for ring, hole in [(r["outline_mm"], False)] + [(h, True) for h in r["holes_mm"]]:
            pts = [P(r["offset_mm"], u, z) if r["plane"] == "x" else P(u, r["offset_mm"], z) for u, z in ring]
            polys.append((r["plane"], pts, hole, r["offset_mm"]))
    xs = [p[0] for _, ps, _, _ in polys for p in ps]; ys = [p[1] for _, ps, _, _ in polys for p in ps]
    x0, y0, w, h = min(xs) - 5, min(ys) - 12, max(xs) - min(xs) + 10, max(ys) - min(ys) + 17
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.2f} {y0:.2f} {w:.2f} {h:.2f}" width="{w * 6:.0f}" height="{h * 6:.0f}">',
           f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#fff"/>',
           f'<text x="{x0 + 2}" y="{y0 + 6}" font-size="4" font-family="sans-serif">Lamina {wj["case"]} {wj["scale"]}: {len(wj["ribs"])} ribs (blue x-planes, orange y-planes), assembled</text>']
    for plane, pts, hole, _ in sorted(polys, key=lambda q: -q[3]):
        col = "#2563eb" if plane == "x" else "#ea580c"
        out.append(f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in pts)}" fill="{"#fff" if hole else col}" fill-opacity="{1 if hole else 0.25}" stroke="{col}" stroke-width="0.25"/>')
    return "\n".join(out + ["</svg>"])


def shoot(page, svg_path, png_path, scale=4):
    txt = svg_path.read_text(encoding="utf-8")
    page.set_content(f'<html><body style="margin:0;background:#fff">{txt}</body></html>')
    el = page.query_selector("svg")
    bb = el.bounding_box()
    page.set_viewport_size({"width": max(200, int(bb["width"]) + 2), "height": max(200, int(bb["height"]) + 2)})
    el.screenshot(path=str(png_path))


def main():
    made = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(device_scale_factor=3)
        for case in CASES:
            d = HERE / case / "preview"; d.mkdir(exist_ok=True)
            for s in SCALES:
                net = HERE / case / f"{case}_{s}.net.svg"
                # dashed valleys for the eye only (a copy; the normalised file itself carries data-fold, no dashes)
                tmp = d / f"_{case}_{s}.net.view.svg"
                tmp.write_text(net.read_text().replace('data-fold="valley"', 'data-fold="valley" stroke-dasharray="2,1.2"'), encoding="utf-8")
                shoot(pg, tmp, d / f"{case}_{s}.net.png"); tmp.unlink(); made.append(d / f"{case}_{s}.net.png")
                wj = json.loads((HERE / case / f"{case}_{s}.waffle.json").read_text())
                tmp = d / f"_{case}_{s}.iso.svg"; tmp.write_text(iso_svg(wj), encoding="utf-8")
                shoot(pg, tmp, d / f"{case}_{s}.waffle_iso.png"); tmp.unlink(); made.append(d / f"{case}_{s}.waffle_iso.png")
                for tech in ("fold", "waffle"):
                    for f in sorted((HERE / case / "raw" / f"{tech}_{s}").glob("*.svg")):
                        n = f.stem.split("sheet")[-1].split()[0]
                        out = d / f"raw_{tech}_{s}_sheet{n}.png"
                        # Lamina's sheet is 297 x 420 mm in physical units; show it at ~3 px/mm
                        pg.set_viewport_size({"width": 1200, "height": 1700})
                        pg.set_content(f'<html><body style="margin:0;background:#fff"><div style="width:891px">{f.read_text(encoding="utf-8").split("?>", 1)[-1].replace("width=\"297.0000mm\" height=\"420.0000mm\"", "width=\"891\" height=\"1260\"")}</div></body></html>')
                        pg.query_selector("svg").screenshot(path=str(out)); made.append(out)
        b.close()
    print("\n".join(str(m) for m in made))


if __name__ == "__main__":
    main()
