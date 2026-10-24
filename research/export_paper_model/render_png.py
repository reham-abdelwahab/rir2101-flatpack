"""Render each normalised net SVG to PNG with system Chromium (playwright). Usage: python3 render_png.py <svg>..."""
import sys, re, pathlib
from playwright.sync_api import sync_playwright
PX_PER_MM = 4
with sync_playwright() as p:
    b = p.chromium.launch()
    for f in sys.argv[1:]:
        s = pathlib.Path(f).read_text()
        vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).split()]
        w, h = int(vb[2] * PX_PER_MM), int(vb[3] * PX_PER_MM)
        pg = b.new_page(viewport={"width": w, "height": h})
        body = re.sub(r'width="[^"]+mm" height="[^"]+mm"', f'width="{w}" height="{h}"', s.split("?>", 1)[1], count=1)
        pg.set_content(f'<html><body style="margin:0;background:#fff">{body}</body></html>')
        out = f[:-4] + ".png"
        pg.screenshot(path=out, full_page=False)
        print(out, w, h)
    b.close()
