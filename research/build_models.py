"""Build the shared target meshes for the tool comparison (research/, D2).

Fold & Glue targets (*_fold.obj): the assembled panels of our own v4.3.0 nets at 1:10, read from
tests/fold_verify.js (out.surfaces). They are the designed furniture (open surface models, zero
thickness), so every tool unfolds exactly the shape our tool makes. Units: mm at 1:10 (= cm real).
Each panel is one planar n-gon; vertices are welded and every edge is split where another
panel's vertex lies on it, so neighbouring panels share edges. Face orientation = printed side
(outside): seats/tops face +Z, every other panel faces away from the model's centre.

Waffle targets (*_waffle_solid.stl): the closed solids our Waffle generator sections at 1:10,
1.5 mm board, laser (waffleSilhouettes in index.html): chair and table = side prism ∩ front prism;
sofa = union of seat block, two arms and back.

Usage: python build_models.py models.json  (models.json from research/extract_targets.py)
"""
import json, sys, os
import numpy as np, trimesh, manifold3d as m3

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
os.makedirs(OUT, exist_ok=True)

def weld_and_conform(polys, tol=1e-3):
    V = []
    def vid(p):
        for i, q in enumerate(V):
            if np.linalg.norm(np.subtract(p, q)) < tol: return i
        V.append(list(p)); return len(V) - 1
    faces = [[vid(p) for p in poly] for poly in polys]
    faces = [[v for k, v in enumerate(f) if v != f[k - 1]] for f in faces]
    changed = True
    while changed:              # split edges at T-junctions
        changed = False
        for f in faces:
            for k in range(len(f)):
                a, b = np.array(V[f[k]]), np.array(V[f[(k + 1) % len(f)]])
                L = np.linalg.norm(b - a)
                for i, p in enumerate(V):
                    if i in (f[k], f[(k + 1) % len(f)]): continue
                    t = np.dot(np.array(p) - a, b - a) / L ** 2
                    if 1e-6 < t < 1 - 1e-6 and np.linalg.norm(a + t * (b - a) - p) < tol:
                        f.insert(k + 1, i); changed = True; break
                if changed: break
            if changed: break
    return np.array(V, dtype=float), faces

def ear_clip(V, f):
    """Triangulate one planar n-gon (convex or not) keeping its orientation."""
    import mapbox_earcut as ec
    P = V[f]; n = np.zeros(3)
    for i in range(1, len(P) - 1): n += np.cross(P[i] - P[0], P[i + 1] - P[0])
    n /= np.linalg.norm(n); u = P[1] - P[0]; u /= np.linalg.norm(u); v = np.cross(n, u)
    uv = np.c_[(P - P[0]) @ u, (P - P[0]) @ v]
    T = ec.triangulate_float64(uv, np.array([len(f)], dtype=np.uint32)).reshape(-1, 3)
    out = []
    for a, b, c in T:
        tn = np.cross(P[b] - P[a], P[c] - P[a]); out.append([f[a], f[b], f[c]] if np.dot(tn, n) > 0 else [f[a], f[c], f[b]])
    return out

def orient(V, faces, names, centre):
    out = []
    for f, nm in zip(faces, names):
        P = V[f]; n = np.zeros(3)
        for i in range(1, len(P) - 1): n += np.cross(P[i] - P[0], P[i + 1] - P[0])
        n /= np.linalg.norm(n)
        if abs(n[2]) > 0.9: want = 1 if P[:, 2].mean() > 0.01 else -1      # seats and tops: printed side up
        else:
            c = P.mean(axis=0) - centre; c[2] = 0
            want = np.sign(np.dot(n, c)) or 1
            out.append(f if want > 0 else f[::-1]); continue
        out.append(f if np.sign(n[2]) == want else f[::-1])
    return out

def write_obj(path, V, faces, names, header):
    with open(path, 'w') as fh:
        fh.write(f'# {header}\n# units: mm at 1:10 (= cm real); one planar n-gon per panel; printed side = face normal\n')
        for v in V: fh.write('v %.4f %.4f %.4f\n' % tuple(v))
        for f, nm in zip(faces, names): fh.write(f'g {nm.replace(" ", "_")}\nf ' + ' '.join(str(i + 1) for i in f) + '\n')

def fold_targets(models):
    rep = {}
    for case, r in models.items():
        polys = [s['P3'] for s in r['surfaces']]; names = [s['face'] if s['face'] != 'panel' else s['part'] + ' APRON' for s in r['surfaces']]
        V, faces = weld_and_conform(polys)
        if abs((V.max(0) - V.min(0))[0] - r['spec']['W']) > 0.01:       # put the model's width W along x
            V = V[:, [1, 0, 2]]
        V = V - V.min(0)
        lo, hi = V.min(0), V.max(0); centre = (lo + hi) / 2
        faces = orient(V, faces, names, centre)
        write_obj(os.path.join(OUT, f'{case}_fold.obj'), V, faces, names, f'{case} Fold & Glue target, from v4.3.0 nets folded by tests/fold_verify.js; spec {r["spec"]}')
        tri = trimesh.Trimesh(vertices=V, faces=[t for f in faces for t in ear_clip(V, f)], process=False)
        tri.export(os.path.join(OUT, f'{case}_fold.stl'))
        rep[case] = {'bbox_mm': (hi - lo).round(2).tolist(), 'panels': len(faces), 'vertices': len(V), 'area_mm2': round(float(tri.area), 1)}
    return rep

def box(x0, y0, z0, x1, y1, z1): return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
def extrude(profile, length, axis):
    """profile in the (u, z) plane, extruded along x (axis='x', u = y) or along y (axis='y', u = x); returns a Manifold."""
    M = m3.CrossSection([[(u, z) for u, z in profile]]).extrude(length).to_mesh()   # (u, z) in XY, extrusion along +Z
    P, T = np.array(M.vert_properties)[:, :3], np.array(M.tri_verts)
    if axis == 'x': Q = np.c_[P[:, 2], P[:, 0], P[:, 1]]                 # cyclic axis swap keeps orientation
    else: Q, T = np.c_[P[:, 0], P[:, 2], P[:, 1]], T[:, ::-1]            # odd swap: reverse triangles
    return m3.Manifold(m3.Mesh(vert_properties=np.ascontiguousarray(Q, dtype=np.float32), tri_verts=np.ascontiguousarray(T, dtype=np.uint32)))

def to_tri(man):
    M = man.to_mesh(); return trimesh.Trimesh(np.array(M.vert_properties)[:, :3], np.array(M.tri_verts))

def waffle_targets():
    f, t = 1.0, 1.5; m = max(3 * t, 4); sw = t
    memb = lambda cm: max(cm * f, m + sw + 1); slab = lambda cm: max(cm * f, 3 * t + 1)
    rep = {}
    def solid_from(side, front, W, D):
        return to_tri(extrude(side, W, 'x') ^ extrude(front, D, 'y'))
    # chair 45 × 45 × 85, seat 45
    W, D, H, S = 45, 45, 85, 45; leg, seatT, backT = memb(4), slab(4), memb(5); seatZ = max(S, seatT + 1)
    side = [(0, 0), (leg, 0), (leg, seatZ - seatT), (D - leg, seatZ - seatT), (D - leg, 0), (D, 0), (D, H), (D - backT, H), (D - backT, seatZ), (0, seatZ)]
    front = [(0, 0), (leg, 0), (leg, seatZ - seatT), (W - leg, seatZ - seatT), (W - leg, 0), (W, 0), (W, H), (0, H)]
    sol = {'chair': solid_from(side, front, W, D)}
    # table 140 × 80 × 75, apron 12
    W, D, H = 140, 80, 75; apron, legD, legW = min(H - 1, slab(12)), memb(5), memb(5)
    side = [(0, 0), (legD, 0), (legD, H - apron), (D - legD, H - apron), (D - legD, 0), (D, 0), (D, H), (0, H)]
    front = [(0, 0), (legW, 0), (legW, H - apron), (W - legW, H - apron), (W - legW, 0), (W, 0), (W, H), (0, H)]
    sol['table'] = solid_from(side, front, W, D)
    # sofa 180 × 85 × 80, seat 42 (union of boxes, as xSection/ySection)
    W, D, H, S = 180, 85, 80, 42; backT, armW = memb(20), memb(15); armZ = min(H - slab(4), S + (H - S) * 0.45)
    parts = [box(0, 0, 0, W, D, S), box(0, D - backT, 0, W, D, H), box(0, 0, 0, armW, D, armZ), box(W - armW, 0, 0, W, D, armZ)]
    u = parts[0]
    for p in parts[1:]: u = u + p
    sol['sofa_curved'] = to_tri(u)
    for k, s in sol.items():
        s.export(os.path.join(OUT, f'{k}_waffle_solid.stl'))
        rep[k] = {'bbox_mm': s.extents.round(2).tolist(), 'watertight': bool(s.is_watertight), 'volume_mm3': round(float(s.volume), 1)}
    rep['note'] = 'sofa Waffle solid has no arched back (our Waffle sofa is boxes); the arched back applies to Fold & Glue only'
    return rep

if __name__ == '__main__':
    models = json.load(open(sys.argv[1]))
    rep = {'fold': fold_targets(models), 'waffle': waffle_targets()}
    json.dump(rep, open(os.path.join(OUT, 'models_report.json'), 'w'), indent=1); print(json.dumps(rep, indent=1))
