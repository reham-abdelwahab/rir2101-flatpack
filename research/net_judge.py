"""Generic net judge for the tool comparison (research/, D3).

One judge for every tool, including ours. It reads only
  * a normalised net SVG (research/FORMAT.md): cut outlines, fold lines with data-fold, paper mm;
  * the shared target mesh (research/models/<case>_fold.obj): planar panels, normal = printed side.
It knows nothing about furniture names, labels, archetypes or 90-degree folds.

Method
 1. Each cut outline is a part. Fold lines inside it split it into faces (planar subdivision);
    a fold line shared by two faces is a hinge. Fold lines that do not separate two faces are
    reported as unmatched scores.
 2. Placement is SEARCHED, not assumed: for each part, every face is tried as the root on every
    target panel, at every vertex-to-vertex edge alignment, printed side out (and, separately,
    printed side in, which is reported as a fault). From the root the part is unfolded back onto
    the mesh across its hinges: a child face may only turn about its hinge into a target plane
    that contains that hinge, and must then lie inside a target panel (>= 99 % of its area) or, for
    a glue tab, on a panel (>= 95 %). The placement that lands the most face area wins.
    Parts are placed largest first; ties prefer new coverage, so a mirror-image part goes to
    the other side.
 3. Glue tabs are found by coverage, not by shape: a face whose removal does not reduce the area
    covered is a tab (it lies under or over another face).
 4. Metrics (FORMAT.md, TOOLS_INTEGRATION_PLAN.md section 5)
    M1 size error (mm): max |bbox(placed panels) - bbox(target)| over W, D, H; plus coverage (%).
    M2 folds whose marked direction matches the fold the shape needs (%), folds > 5 degrees only;
       "unmarked" lines take the tool's own printed rule (e.g. ours: mountain).
    M3 tabs that land >= 95 % on a panel covered by another face (%).
    M4 overlapping panels (pairs overlapping > 0.5 mm^2 in the same plane, tabs excluded) and
       faces that cannot be placed at all.
    Also: faces with the printed side inward; unmatched scores.
Limits (stated in the paper): zero thickness; final folded state only (no swept-motion
collision check); a face must lie inside one target panel (a net that bridges two coplanar
panels as one face is placed only if the panels are one polygon in the mesh).

Usage: python net_judge.py <net.svg> <mesh.obj> [--unmarked mountain|valley] [--json out.json]
"""
import sys, json, re, math, argparse
import xml.etree.ElementTree as ET
import numpy as np
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import polygonize, unary_union

TOL = 0.05          # mm, geometric tolerance on paper
FLAT_DEG = 5.0      # folds flatter than this are "flat score lines", not counted in M2

# ---------------------------------------------------------------- SVG
def _num(s): return [float(v) for v in re.findall(r'-?\d*\.?\d+(?:e-?\d+)?', s)]

def parse_net(path):
    root = ET.parse(path).getroot()
    ns = {'s': 'http://www.w3.org/2000/svg'}
    def grp(gid):
        for g in root.iter():
            if g.get('id') == gid: return g
        return None
    cut, score = grp('01_CUT_RED'), grp('02_SCORE_BLUE')
    if cut is None or score is None: raise SystemExit('not a normalised net: missing 01_CUT_RED / 02_SCORE_BLUE')
    rings = []
    for el in cut.iter():
        if el.tag.endswith('path'):
            d = el.get('d', ''); toks = re.findall(r'[MLZmlz]|-?\d*\.?\d+(?:e-?\d+)?', d); pts = []; cur = []
            i = 0; mode = None
            while i < len(toks):
                t = toks[i]
                if t in 'MLZmlz':
                    mode = t.upper()
                    if mode == 'Z':
                        if len(cur) >= 3: pts.append(cur)
                        cur = []
                    i += 1; continue
                x, y = float(toks[i]), float(toks[i + 1]); i += 2
                if mode == 'M' and cur: pts.append(cur); cur = []
                cur.append((x, -y))                    # SVG y-down -> right-handed, printed side = +z
            if len(cur) >= 3: pts.append(cur)
            rings += pts
        elif el.tag.endswith('polygon'):
            v = _num(el.get('points', '')); rings.append([(v[k], -v[k + 1]) for k in range(0, len(v), 2)])
    folds = []
    for el in score.iter():
        if el.tag.endswith('line'):
            x1, y1, x2, y2 = (float(el.get(k)) for k in ('x1', 'y1', 'x2', 'y2'))
            folds.append({'p': (x1, -y1), 'q': (x2, -y2), 'mark': el.get('data-fold', 'unmarked')})
    return rings, folds

# ---------------------------------------------------------------- mesh
def parse_obj(path, scale=1.0):
    V, F = [], []
    for line in open(path):
        if line.startswith('v '): V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith('f '): F.append([int(t.split('/')[0]) - 1 for t in line.split()[1:]])
    V = np.array(V) * scale
    panels = []
    for f in F:
        P = V[f]; n = np.zeros(3)
        for i in range(1, len(P) - 1): n += np.cross(P[i] - P[0], P[i + 1] - P[0])
        area = np.linalg.norm(n) / 2; n = n / np.linalg.norm(n)
        u = P[1] - P[0]; u /= np.linalg.norm(u); v = np.cross(n, u)
        poly2 = Polygon([((p - P[0]) @ u, (p - P[0]) @ v) for p in P]).buffer(0)
        panels.append({'P': P, 'n': n, 'o': P[0], 'u': u, 'v': v, 'poly': poly2, 'area': area, 'd': n @ P[0]})
    return V, panels

# ---------------------------------------------------------------- faces and hinges
def split_part(ring, folds):
    R = Polygon(ring).buffer(0)
    if R.is_empty or R.area < 1e-6: return None
    if isinstance(R, MultiPolygon): R = max(R.geoms, key=lambda g: g.area)
    inner = [f for f in folds if R.buffer(TOL).contains(LineString([f['p'], f['q']]).interpolate(0.5, normalized=True))]
    # the RAW cut outline divides faces too: a slit (zero-width cut into the part) is erased by buffer(0) but still
    # separates the two faces on either side of it
    lines = unary_union([R.exterior, LineString(list(ring) + [ring[0]])] + [LineString([f['p'], f['q']]) for f in inner])
    faces = [p for p in polygonize(lines) if R.buffer(TOL).contains(p.representative_point()) and p.area > 1e-4]
    hinges, unmatched = [], 0
    for f in inner:
        seg = LineString([f['p'], f['q']]); adj = []
        for k, F in enumerate(faces):
            if F.exterior.intersection(seg.buffer(TOL)).length > 0.5 * seg.length: adj.append(k)
        if len(adj) == 2: hinges.append({'a': adj[0], 'b': adj[1], 'p': np.array(f['p']), 'q': np.array(f['q']), 'mark': f['mark'], 'len': seg.length})
        else: unmatched += 1
    return {'ring': R, 'faces': faces, 'hinges': hinges, 'unmatched': unmatched, 'folds': len(inner)}

# ---------------------------------------------------------------- 3D helpers
def rot(axis, ang):
    a = axis / np.linalg.norm(axis); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K

def to3(T, pts):  # T = (R 3x3, t 3) mapping net (x, y, 0) -> 3D
    R, t = T; return np.array([R @ np.array([x, y, 0.0]) + t for x, y in pts])

def land(pts3, panels, need):
    """Best target panel a planar 3D polygon lies in: returns (index, fraction of the polygon inside it)."""
    best = (None, 0.0)
    for j, pn in enumerate(panels):
        if np.max(np.abs(pts3 @ pn['n'] - pn['d'])) > TOL * 4: continue
        q = Polygon([((p - pn['o']) @ pn['u'], (p - pn['o']) @ pn['v']) for p in pts3]).buffer(0)
        if q.area < 1e-6: continue
        fr = q.intersection(pn['poly']).area / q.area
        if fr > best[1]: best = (j, fr)
    return best if best[1] >= need else (None, best[1])

def poly3_area_in_panel(pts3, pn):
    return Polygon([((p - pn['o']) @ pn['u'], (p - pn['o']) @ pn['v']) for p in pts3]).buffer(0)

def root_candidates(face, panels, flip):
    """Rigid maps of a net face onto target panels, vertex to vertex along an edge (printed side out unless flip)."""
    C = list(face.exterior.coords)[:-1]; out = []
    for pn in panels:
        Q = pn['P']
        for i in range(len(C)):
            a, b = np.array(C[i]), np.array(C[(i + 1) % len(C)]); L = np.linalg.norm(b - a)
            if L < 0.5: continue
            for j in range(len(Q)):
                for s in (1, -1):
                    A, B = Q[j], Q[(j + s) % len(Q)]
                    e = B - A; Le = np.linalg.norm(e)
                    if Le < L - TOL * 2: continue
                    ex = e / Le; nz = -pn['n'] if flip else pn['n']; ey = np.cross(nz, ex)
                    d = (b - a) / L; dp = np.array([-d[1], d[0]])
                    # net frame: x along d, y along dp, z = printed normal
                    Rn = np.c_[np.r_[d, 0], np.r_[dp, 0], [0, 0, 1]]
                    Rt = np.c_[ex, ey, nz]
                    R = Rt @ Rn.T; t = A - R @ np.r_[a, 0]
                    out.append((R, t))
    return out

def place_part(part, panels, flip=False, covered=None, unmarked='mountain'):
    F, H = part['faces'], part['hinges']
    order = sorted(range(len(F)), key=lambda k: -F[k].area)
    best = None
    for r in order[:3]:
        for T0 in root_candidates(F[r], panels, flip):
            pts = to3(T0, list(F[r].exterior.coords)[:-1])
            j, fr = land(pts, panels, 0.99)
            if j is None: continue
            T = {r: T0}; where = {r: (j, fr)}; signs = {}; queue = [r]
            g0 = poly3_area_in_panel(pts, panels[j]); mine = {j: g0}            # area this part already covers, per panel
            base = lambda jj: unary_union([(covered or {}).get(jj, Polygon()), mine.get(jj, Polygon())])
            while queue:
                k = queue.pop(0)
                for hi, h in enumerate(H):
                    if k not in (h['a'], h['b']): continue
                    c = h['b'] if h['a'] == k else h['a']
                    if c in T: continue
                    R, t = T[k]; P = R @ np.r_[h['p'], 0] + t; Qp = R @ np.r_[h['q'], 0] + t; ax = Qp - P
                    nparent = R @ np.array([0, 0, 1.0]); cpts = list(F[c].exterior.coords)[:-1]
                    cand = []
                    a_ = ax / np.linalg.norm(ax)
                    for pn in panels:      # exact angle onto every target plane that contains the hinge
                        if abs(P @ pn['n'] - pn['d']) > TOL * 4 or abs(Qp @ pn['n'] - pn['d']) > TOL * 4: continue
                        for tgt in (pn['n'], -pn['n']):
                            x0 = nparent - (nparent @ a_) * a_; x1 = tgt - (tgt @ a_) * a_
                            if np.linalg.norm(x0) < 1e-9 or np.linalg.norm(x1) < 1e-9: continue
                            ang = math.atan2(np.cross(x0, x1) @ a_, x0 @ x1)
                            if abs(abs(math.degrees(ang)) - 180) < 2: continue    # folded flat back onto its own parent: never a placement
                            Rr = rot(ax, ang); T1 = (Rr @ R, Rr @ (t - P) + P)
                            P3 = to3(T1, cpts); jj, f2 = land(P3, panels, 0.95)
                            if jj is not None:
                                gc = poly3_area_in_panel(P3, panels[jj])
                                cand.append((gc.difference(base(jj)).area, f2, abs(ang), ang, T1, jj, gc))
                    if not cand: continue
                    # prefer the fold that covers new target area (a face folded flat onto an already covered
                    # panel is not a placement), then the fuller landing, then the smaller turn
                    cand.sort(key=lambda z: (-round(z[0], 1), -round(z[1], 3), z[2]))
                    _, f2, _, ang, T1, jj, gc = cand[0]
                    T[c] = T1; where[c] = (jj, f2); mine[jj] = unary_union([mine.get(jj, Polygon()), gc])
                    mid = to3(T1, [tuple(np.array(F[c].centroid.coords[0]))])[0]
                    disp = (mid - P) @ nparent
                    deg = math.degrees(abs(ang))
                    signs[hi] = {'deg': deg, 'need': 'mountain' if disp < -TOL else 'valley' if disp > TOL else 'flat'}
                    queue.append(c)
            landed = sum(F[k].area * where[k][1] for k in where)
            newcov = 0.0
            if covered is not None:
                for k in where:
                    pn = panels[where[k][0]]; g = poly3_area_in_panel(to3(T[k], list(F[k].exterior.coords)[:-1]), pn)
                    newcov += g.difference(covered.get(where[k][0], Polygon())).area
            # among placements that cover the same area, prefer the one the printed marks agree with: the question is
            # whether an assembly that FOLLOWS the marks reaches the target (as our own verifier asks)
            agree = 0
            for hi, sg in signs.items():
                mk = H[hi]['mark'] if H[hi]['mark'] in ('mountain', 'valley') else unmarked
                if sg['need'] != 'flat' and sg['deg'] >= FLAT_DEG: agree += (mk == sg['need'])
            key = (round(newcov, 1), round(landed, 1), agree)
            if best is None or key > best['key']: best = {'key': key, 'T': T, 'where': where, 'signs': signs, 'root': r}
    return best

# ---------------------------------------------------------------- judge
def judge(net_svg, mesh_obj, unmarked='mountain', mesh_scale=1.0):
    rings, folds = parse_net(net_svg)
    V, panels = parse_obj(mesh_obj, mesh_scale)
    parts = [p for p in (split_part(r, folds) for r in rings) if p]
    parts.sort(key=lambda p: -p['ring'].area)
    out = {'parts': len(parts), 'faces': sum(len(p['faces']) for p in parts), 'hinges': sum(len(p['hinges']) for p in parts),
           'unmatched_scores': sum(p['unmatched'] for p in parts), 'unplaced_faces': 0, 'unplaced_parts': 0,
           'printed_inward_faces': 0, 'notes': []}
    covered = {}; placed = []   # (part index, face index, panel index, 2D poly in panel frame, 3D pts)
    for pi, part in enumerate(parts):
        b = place_part(part, panels, False, covered, unmarked)
        # printed side inward is tried only when the printed-out placement is incomplete or adds (almost) no new area
        weak = b is None or len(b['where']) < len(part['faces']) or b['key'][0] < 0.5 * part['ring'].area * 0.5
        bf = place_part(part, panels, True, covered, unmarked) if weak else None
        if bf is not None and (b is None or bf['key'] > b['key']):
            b = bf; out['notes'].append(f'part {pi + 1}: placed only with the printed side inward')
        if b is None:
            out['unplaced_parts'] += 1; out['unplaced_faces'] += len(part['faces']); out['notes'].append(f'part {pi + 1}: no placement on the target'); continue
        out['unplaced_faces'] += len(part['faces']) - len(b['where'])
        part['placement'] = b
        for k, (j, fr) in b['where'].items():
            g = poly3_area_in_panel(to3(b['T'][k], list(part['faces'][k].exterior.coords)[:-1]), panels[j])
            placed.append({'part': pi, 'face': k, 'panel': j, 'g': g, 'area': g.area})
            covered[j] = unary_union([covered.get(j, Polygon()), g])
    # tabs by coverage: degree-1 faces, smallest first, removable without losing coverage
    deg = {}
    for pi, part in enumerate(parts):
        for h in part['hinges']: deg[(pi, h['a'])] = deg.get((pi, h['a']), 0) + 1; deg[(pi, h['b'])] = deg.get((pi, h['b']), 0) + 1
    is_tab = set()
    for f in sorted(placed, key=lambda z: z['area']):
        if deg.get((f['part'], f['face']), 0) != 1: continue
        others = unary_union([g['g'] for g in placed if g is not f and g['panel'] == f['panel'] and (g['part'], g['face']) not in is_tab])
        if f['g'].difference(others).area <= max(0.5, 0.01 * f['area']): is_tab.add((f['part'], f['face']))
    pan = [f for f in placed if (f['part'], f['face']) not in is_tab]
    # printed side: every panel face (tabs excluded) must have its printed side on the outside of the model
    inward = 0
    for f in pan:
        R, t = parts[f['part']]['placement']['T'][f['face']]
        if (R @ np.array([0, 0, 1.0])) @ panels[f['panel']]['n'] < 0: inward += 1
    out['printed_inward_faces'] = inward
    # coverage and size (M1)
    cov = {j: unary_union([f['g'] for f in pan if f['panel'] == j]) for j in range(len(panels))}
    cov_area = sum(cov[j].intersection(panels[j]['poly']).area for j in cov); tot = sum(p['area'] for p in panels)
    pts = []
    for j, g in cov.items():
        if g.is_empty: continue
        gs = g.geoms if hasattr(g, 'geoms') else [g]
        for gg in gs:
            for x, y in gg.exterior.coords: pts.append(panels[j]['o'] + x * panels[j]['u'] + y * panels[j]['v'])
    tb = V.max(0) - V.min(0)
    if pts:
        pts = np.array(pts); bb = pts.max(0) - pts.min(0)
        out['size_mm'] = bb.round(2).tolist(); out['target_mm'] = tb.round(2).tolist(); out['M1_size_error_mm'] = round(float(np.max(np.abs(bb - tb))), 2)
    else: out['M1_size_error_mm'] = None
    out['coverage_pct'] = round(100 * cov_area / tot, 2)
    out['missing_panels'] = [j for j in range(len(panels)) if cov[j].intersection(panels[j]['poly']).area < 0.95 * panels[j]['area']]
    # M2 fold directions
    n_ok = n_all = n_flat = 0; wrong = []
    for pi, part in enumerate(parts):
        b = part.get('placement')
        if not b: continue
        for hi, s in b['signs'].items():
            h = part['hinges'][hi]
            if s['need'] == 'flat' or s['deg'] < FLAT_DEG: n_flat += 1; continue
            mark = h['mark'] if h['mark'] in ('mountain', 'valley') else unmarked
            n_all += 1
            if mark == s['need']: n_ok += 1
            else: wrong.append(f"part {pi + 1}: marked {mark}, needs {s['need']} ({s['deg']:.0f} deg)")
    out['folds_counted'] = n_all; out['flat_score_lines'] = n_flat
    out['M2_fold_direction_ok_pct'] = round(100 * n_ok / n_all, 1) if n_all else None; out['fold_direction_faults'] = wrong[:20]
    # M3 tabs
    tabs = [f for f in placed if (f['part'], f['face']) in is_tab]
    mated = 0
    for f in tabs:
        others = unary_union([g['g'] for g in pan if g['panel'] == f['panel'] and not (g['part'] == f['part'] and g['face'] == f['face'])])
        if f['g'].intersection(others).area >= 0.95 * f['area']: mated += 1
    out['tabs'] = len(tabs); out['tabs_mated'] = mated
    out['M3_tabs_land_pct'] = round(100 * mated / len(tabs), 1) if tabs else None
    # M4 overlaps between panels (tabs excluded)
    ov = 0
    for i in range(len(pan)):
        for k in range(i + 1, len(pan)):
            if pan[i]['panel'] == pan[k]['panel'] and pan[i]['g'].intersection(pan[k]['g']).area > 0.5: ov += 1
    out['M4_overlapping_panels'] = ov
    out['ok'] = bool(out['M1_size_error_mm'] is not None and out['M1_size_error_mm'] <= 0.5 and out['coverage_pct'] >= 99 and out['M2_fold_direction_ok_pct'] in (100.0, None)
                 and (out['M3_tabs_land_pct'] in (100.0, None)) and ov == 0 and out['unplaced_faces'] == 0 and out['printed_inward_faces'] == 0 and out['unmatched_scores'] == 0)
    return out

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('net'); ap.add_argument('mesh'); ap.add_argument('--unmarked', default='mountain'); ap.add_argument('--json'); ap.add_argument('--mesh-scale', type=float, default=1.0)
    a = ap.parse_args(); r = judge(a.net, a.mesh, a.unmarked, a.mesh_scale)
    s = json.dumps(r, indent=1); print(s)
    if a.json: open(a.json, 'w').write(s)
