"""
Waffle (egg-crate) structure generator — prototype for Studio Flat-Pack Maker v4.

Input : a piece defined by two orthogonal silhouettes (all in paper mm, already scaled)
          S_side  : polygon in the (y, z) plane  — the SIDE elevation  (depth D × height H)
          S_front : polygon in the (x, z) plane  — the FRONT elevation (width W × height H)
        board thickness t, rib spacing s, kerf k
Output: ribs along X (copies of the side silhouette, placed at x_i) and ribs along Y
        (copies of the front silhouette, placed at y_j); every crossing gets a pair of
        half-depth slots (X-rib slotted from the TOP, Y-rib slotted from the BOTTOM) so the
        grid assembles without glue. The solid is the intersection of the two extrusions.
"""
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
import math

def _slot_intervals(poly, coord, axis):
    """Vertical (z) intervals where the silhouette contains the line x=coord (axis='x') or y=coord."""
    minx, miny, maxx, maxy = poly.bounds
    line = LineString([(coord, miny - 1), (coord, maxy + 1)])
    inter = poly.intersection(line)
    segs = []
    if inter.is_empty: return segs
    geoms = getattr(inter, 'geoms', [inter])
    for g in geoms:
        if g.geom_type == 'LineString':
            zs = [p[1] for p in g.coords]; segs.append((min(zs), max(zs)))
    return segs

def waffle(S_side, S_front, W, D, t=1.5, s=10.0, k=0.0, margin=None):
    """Return dict with ribs: list of {'name','poly','dir','pos'} (poly in its own 2D plane)."""
    sw = t + k                      # slot width
    if margin is None: margin = max(3.0 * t, 4.0)
    # rib positions: inset by margin from the outer faces, evenly spaced
    def positions(L):
        n = max(2, int(math.floor((L - 2 * margin) / s)) + 1)
        step = (L - 2 * margin) / (n - 1)
        return [margin + i * step for i in range(n)]
    xs = positions(W)   # X-ribs (side silhouettes) stand at x = xs[i]
    ys = positions(D)   # Y-ribs (front silhouettes) stand at y = ys[j]
    ribs = []
    # Pre-compute, for each crossing, the common z-interval where BOTH silhouettes have material
    crossings = {}
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            zi_side  = _slot_intervals(S_side, y, 'y')    # side silhouette evaluated at depth y
            zi_front = _slot_intervals(S_front, x, 'x')   # front silhouette evaluated at width x
            common = []
            for a in zi_side:
                for b in zi_front:
                    lo, hi = max(a[0], b[0]), min(a[1], b[1])
                    if hi - lo > 3 * t: common.append((lo, hi))
            if common: crossings[(i, j)] = common
    # Build X-ribs: side silhouette with slots from the TOP at each y_j
    for i, x in enumerate(xs):
        poly = S_side
        for j, y in enumerate(ys):
            for (lo, hi) in crossings.get((i, j), []):
                mid = (lo + hi) / 2
                poly = poly.difference(box(y - sw / 2, mid, y + sw / 2, hi + 1))
        ribs.append({'name': f'X{i+1}', 'poly': poly, 'dir': 'x', 'pos': x})
    # Build Y-ribs: front silhouette with slots from the BOTTOM at each x_i
    for j, y in enumerate(ys):
        poly = S_front
        for i, x in enumerate(xs):
            for (lo, hi) in crossings.get((i, j), []):
                mid = (lo + hi) / 2
                poly = poly.difference(box(x - sw / 2, lo - 1, x + sw / 2, mid))
        ribs.append({'name': f'Y{j+1}', 'poly': poly, 'dir': 'y', 'pos': y})
    return {'ribs': ribs, 'xs': xs, 'ys': ys, 'crossings': crossings, 'slot_width': sw}

# ---------- validation ----------
def validate(res, t):
    errs = []
    sw = res['slot_width']
    for (i, j), ivs in res['crossings'].items():
        # each crossing must have exactly matching slot depths: top slot on X-rib and bottom slot on Y-rib meet at mid
        for (lo, hi) in ivs:
            if hi - lo < 3 * t: errs.append(f'crossing X{i+1}/Y{j+1} too thin ({hi-lo:.1f} mm)')
    # remaining material between neighbouring slots must be >= 2t
    for r in res['ribs']:
        others = res['ys'] if r['dir'] == 'x' else res['xs']
        for a, b in zip(others, others[1:]):
            if (b - a) - sw < 2 * t: errs.append(f'{r["name"]}: web between slots {b-a-sw:.1f} mm < 2t')
    return errs

# ---------- SVG sheet (same layer convention as the tool) ----------
def poly_to_path(poly, ox, oy, flip_h):
    parts = []
    geoms = getattr(poly, 'geoms', [poly])
    for g in geoms:
        rings = [g.exterior] + list(g.interiors)
        for ring in rings:
            pts = [(ox + p[0], oy + (flip_h - p[1])) for p in ring.coords]
            parts.append('M ' + ' L '.join(f'{x:.2f},{y:.2f}' for x, y in pts) + ' Z')
    return ' '.join(parts)

def sheet_svg(res, sheet=(210, 297), gap=3, title='WAFFLE RIBS'):
    W, H = sheet
    cut, lab = [], []
    x, y, rowh = 10, 30, 0
    for r in res['ribs']:
        minx, miny, maxx, maxy = r['poly'].bounds
        w, h = maxx - minx, maxy - miny
        if x + w > W - 10: x = 10; y += rowh + gap; rowh = 0
        cut.append(f'<path d="{poly_to_path(r["poly"], x - minx, y, maxy)}" fill="#fff"/>')
        lab.append(f'<text x="{x + w/2:.1f}" y="{y + h - 1.5:.1f}" text-anchor="middle" font-size="2.2">{r["name"]}</text>')
        # orientation mark: small triangle at the top edge
        lab.append(f'<path d="M{x + 2:.1f},{y + 0.3:.1f} l1.2,2 l-2.4,0 z" fill="#1E1B18"/>')
        x += w + gap; rowh = max(rowh, h)
    fits = (y + rowh) <= H - 26
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="monospace">
<g id="03_LABELS_BLACK" fill="#1E1B18"><text x="10" y="14" font-size="4" font-weight="bold">{title}</text>
<text x="10" y="19" font-size="2.6">ribs X: {len(res['xs'])}  ribs Y: {len(res['ys'])}  slot {res['slot_width']:.2f} mm  · triangle = TOP edge · X-ribs slotted from top, Y-ribs from bottom</text>
<rect x="{W-62}" y="9" width="50" height="5" fill="none" stroke="#1E1B18" stroke-width="0.3"/><text x="{W-37}" y="13" text-anchor="middle" font-size="2.4">5 cm CHECK</text>
{''.join(lab)}</g>
<g id="01_CUT_RED" fill="none" stroke="#DC2626" stroke-width="0.2" stroke-linejoin="round">{''.join(cut)}</g>
</svg>''', fits

# ---------- quick isometric assembly picture (for the handout / assembly diagram) ----------
def iso_svg(res, W, D, H):
    def P(x, y, z):   # isometric projection
        return (0.866 * (x - y), 0.5 * (x + y) - z)
    paths = []
    ox, oy = 140, 20
    allpts = []
    def rib_path(poly, at, d):
        geoms = getattr(poly, 'geoms', [poly])
        out = []
        for g in geoms:
            for ring in [g.exterior] + list(g.interiors):
                pts = []
                for (u, z) in ring.coords:
                    x, y = (at, u) if d == 'x' else (u, at)
                    px, py = P(x, y, z); pts.append((ox + px, oy + 120 - py)); allpts.append(pts[-1])
                out.append('M ' + ' L '.join(f'{a:.1f},{b:.1f}' for a, b in pts) + ' Z')
        return ' '.join(out)
    # draw back to front
    for r in sorted(res['ribs'], key=lambda r: -(r['pos'] if r['dir']=='y' else -r['pos'])):
        col = '#FDE9B8' if r['dir'] == 'x' else '#FFFFFF'
        paths.append(f'<path d="{rib_path(r["poly"], r["pos"], r["dir"])}" fill="{col}" fill-opacity="0.85" stroke="#242018" stroke-width="0.5" stroke-linejoin="round"/>')
    xs = [p[0] for p in allpts]; ys = [p[1] for p in allpts]
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min(xs)-5:.0f} {min(ys)-5:.0f} {max(xs)-min(xs)+10:.0f} {max(ys)-min(ys)+10:.0f}">{"".join(paths)}</svg>'

if __name__ == '__main__':
    # Example: lounge chair 70 × 80 × 80 cm at 1:10 → 70 × 80 × 80 mm
    W, D, H = 70.0, 80.0, 80.0
    seat_h, back_t, arm_h, seat_t = 42.0, 10.0, 60.0, 10.0
    # side silhouette (y = depth from front, z = height): sled seat + sloped back + arm
    S_side = Polygon([(0, 0), (12, 0), (12, seat_h - seat_t), (D - back_t - 6, seat_h - seat_t), (D - back_t - 6, 0), (D - 6, 0),
                      (D, H), (D - back_t, H), (D - back_t - 4, seat_h), (12, seat_h), (12, arm_h), (0, arm_h)])
    # front silhouette (x = width, z = height): two arms + seat + back
    S_front = Polygon([(0, 0), (W, 0), (W, H), (0, H)]).difference(box(8, seat_h, W - 8, arm_h - 0.01)).difference(box(8, 0, W - 8, seat_h - seat_t))
    res = waffle(S_side, S_front, W, D, t=1.5, s=10.0, k=0.0)
    errs = validate(res, 1.5)
    svg, fits = sheet_svg(res, title='WAFFLE RIBS // LOUNGE CHAIR 1:10')
    open('/home/claude/waffle/chair_waffle_sheet.svg', 'w').write(svg)
    open('/home/claude/waffle/chair_waffle_iso.svg', 'w').write(iso_svg(res, W, D, H))
    print('ribs', len(res['ribs']), 'crossings', len(res['crossings']), 'fits A4:', fits, 'errors:', errs)
