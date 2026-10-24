"""Generic Waffle (egg-crate) judge for the tool comparison (research/, D6).

Reads a normalised waffle file (research/FORMAT.md: every rib outline in its assembled plane, paper mm) and the
shared target solid (research/models/<case>_waffle_solid.stl). Knows nothing about how the ribs were made.

Metrics (TOOLS_INTEGRATION_PLAN.md section 5, Waffle row)
  size_error_mm     max |bbox(assembled ribs as boards of thickness t) - bbox(solid)|
  fidelity          per rib: area of the rib outside the solid's true section at that plane (mm^2, should be ~0)
                    and section area the rib leaves out (slots excluded), summed over ribs, as % of section area
  crossings         X/Y rib pairs whose boards meet inside the solid
  interference      crossings where the two boards occupy the same space (material of both in the shared band
                    at the same height) - the parts cannot be assembled without cutting
  slot_width_mm     measured gap at every slotted crossing (min / max), to compare with board + kerf
  shallowest_slot   smallest slot depth (mm)
  drop_assembly     % of crossings consistent with ONE global order (one family lowered onto the other)
  windows           closed holes inside ribs (a slot that does not reach an edge is a window)
  loose_parts       rib parts that touch no crossing (nothing holds them in the grid)
Limits: zero clearance tolerance beyond 0.02 mm; boards are ideal slabs; no friction or glue model; physical fit
is the FIT TEST (B2), not this check.
Usage: python waffle_judge.py <case.waffle.json> <solid.stl> [--mesh-scale 0.5] [--json out.json]
"""
import json, argparse
import numpy as np, trimesh
from shapely.geometry import Polygon, MultiPolygon, box, LineString
from shapely.ops import unary_union

EPS = 0.02

def rib_poly(r):
    P = Polygon(r['outline_mm'], [h for h in r.get('holes_mm', []) if len(h) >= 3]).buffer(0)
    return P

def section(mesh, plane, off):
    n = np.array([1.0, 0, 0]) if plane == 'x' else np.array([0, 1.0, 0])
    o = n * off
    s = mesh.section(plane_origin=o, plane_normal=n)
    if s is None: return Polygon()
    pl, _ = s.to_2D(to_2D=np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -off], [0, 0, 0, 1]]) if plane == 'x' else np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, -off], [0, 0, 0, 1]]))
    polys = [p for p in pl.polygons_full]
    return unary_union(polys).buffer(0) if polys else Polygon()

def zintervals(geom):
    """union of z-ranges covered by a (multi)polygon"""
    if geom.is_empty: return []
    gs = geom.geoms if hasattr(geom, 'geoms') else [geom]
    iv = sorted((g.bounds[1], g.bounds[3]) for g in gs if g.area > 1e-6)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1] + EPS: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return out

def overlap_len(A, B):
    return sum(max(0, min(a1, b1) - max(a0, b0)) for a0, a1 in A for b0, b1 in B)

def judge(path, stl, mesh_scale=1.0):
    W = json.load(open(path)); t = W['board_mm']; k = W.get('kerf_mm', 0.0)
    mesh = trimesh.load(stl, force='mesh'); mesh.apply_scale(mesh_scale)
    ribs = [dict(r, poly=rib_poly(r)) for r in W['ribs']]
    X = [r for r in ribs if r['plane'] == 'x']; Y = [r for r in ribs if r['plane'] == 'y']
    out = {'ribs_x': len(X), 'ribs_y': len(Y), 'parts': len(ribs), 'board_mm': t, 'kerf_mm': k}
    # size
    lo, hi = [], []
    for r in ribs:
        b = r['poly'].bounds
        if r['plane'] == 'x': lo.append([r['offset_mm'] - t / 2, b[0], b[1]]); hi.append([r['offset_mm'] + t / 2, b[2], b[3]])
        else: lo.append([b[0], r['offset_mm'] - t / 2, b[1]]); hi.append([b[2], r['offset_mm'] + t / 2, b[3]])
    bb = np.max(hi, 0) - np.min(lo, 0); tb = mesh.extents
    out['size_mm'] = bb.round(2).tolist(); out['target_mm'] = tb.round(2).tolist(); out['size_error_mm'] = round(float(np.max(np.abs(bb - tb))), 2)
    # fidelity
    outside = missing = secA = 0.0
    for r in ribs:
        S = section(mesh, r['plane'], r['offset_mm'])
        outside += r['poly'].difference(S.buffer(EPS)).area
        filled = Polygon(r['poly'].exterior) if isinstance(r['poly'], Polygon) and not r['poly'].is_empty else unary_union([Polygon(g.exterior) for g in getattr(r['poly'], 'geoms', [])])
        missing += S.difference(filled.buffer(EPS)).area; secA += S.area
    out['material_outside_solid_mm2'] = round(outside, 1); out['section_left_out_pct'] = round(100 * missing / secA, 2) if secA else None
    # crossings
    cross = interf = 0; widths = []; depths = []; order = {'x_below': 0, 'y_below': 0, 'mixed': 0}; touched = set()
    for rx in X:
        for ry in Y:
            yj, xi = ry['offset_mm'], rx['offset_mm']
            bx = box(yj - t / 2 + EPS, -1e4, yj + t / 2 - EPS, 1e4); by = box(xi - t / 2 + EPS, -1e4, xi + t / 2 - EPS, 1e4)
            # does the crossing exist (both boards reach this line)?
            inX = rx['poly'].intersection(box(yj - t, -1e4, yj + t, 1e4)); inY = ry['poly'].intersection(box(xi - t, -1e4, xi + t, 1e4))
            if inX.is_empty or inY.is_empty or overlap_len(zintervals(inX), zintervals(inY)) <= EPS: continue
            cross += 1; touched.add(id(rx)); touched.add(id(ry))
            zx, zy = zintervals(rx['poly'].intersection(bx)), zintervals(ry['poly'].intersection(by))
            if overlap_len(zx, zy) > EPS: interf += 1
            # order: which family's material in the shared band lies lower
            if zx and zy:
                if max(b for a, b in zx) <= min(a for a, b in zy) + EPS: order['x_below'] += 1
                elif max(b for a, b in zy) <= min(a for a, b in zx) + EPS: order['y_below'] += 1
                else: order['mixed'] += 1
            # slot width/depth measured in each rib at mid-height of its gap
            for r, u0, band in ((rx, yj, zx), (ry, xi, zy)):
                env = zintervals(r['poly'].intersection(box(u0 - t * 3, -1e4, u0 + t * 3, 1e4)))
                if not env: continue
                zlo, zhi = env[0][0], env[-1][1]
                gaps = []; prev = zlo
                for a, b in band:
                    if a - prev > EPS: gaps.append((prev, a))
                    prev = b
                if zhi - prev > EPS: gaps.append((prev, zhi))
                for g0, g1 in gaps:
                    zm = (g0 + g1) / 2; ln = LineString([(u0 - 3 * t, zm), (u0 + 3 * t, zm)]).difference(r['poly'])
                    segs = ln.geoms if hasattr(ln, 'geoms') else [ln]
                    for sgm in segs:
                        (a0, _), (a1, _) = sgm.coords[0], sgm.coords[-1]
                        if min(a0, a1) - EPS <= u0 <= max(a0, a1) + EPS and abs(a1 - a0) < 3 * t: widths.append(abs(a1 - a0)); depths.append(g1 - g0)
    out['crossings'] = cross; out['interference'] = interf
    out['slot_width_mm'] = [round(min(widths), 3), round(max(widths), 3)] if widths else None
    out['slot_width_target_mm'] = round(t + k, 3)
    out['shallowest_slot_mm'] = round(min(depths), 2) if depths else None
    one = max(order['x_below'], order['y_below'])
    out['drop_assembly_pct'] = round(100 * one / cross, 1) if cross else None; out['order_counts'] = order
    out['windows'] = sum(len(r['poly'].interiors) if isinstance(r['poly'], Polygon) else sum(len(g.interiors) for g in r['poly'].geoms) for r in ribs)
    out['loose_parts'] = sum(1 for r in ribs if id(r) not in touched)
    out['ok'] = bool(out['size_error_mm'] <= 0.5 and interf == 0 and out['windows'] == 0 and out['loose_parts'] == 0 and out['drop_assembly_pct'] == 100.0
                     and out['material_outside_solid_mm2'] <= 1.0)
    return out

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('waffle'); ap.add_argument('stl'); ap.add_argument('--mesh-scale', type=float, default=1.0); ap.add_argument('--json')
    a = ap.parse_args(); r = judge(a.waffle, a.stl, a.mesh_scale); s = json.dumps(r, indent=1); print(s)
    if a.json: open(a.json, 'w').write(s)
