// =============================================================================
// FoldVerify — P4-2 net-folding verifier for Studio Flat-Pack Maker (v4.3)
// Independent of the tool's own geometry code: it reads ONLY the exported, printed
// sheet SVGs (red cut paths, blue score lines, part labels), then
//   1. splits every cut outline into faces along its score lines (hinges),
//   2. finds the fold directions that turn the main part into the target W × D × H
//      (90° per hinge; "mountain" = fold away from the printed side, as the sheet rule says),
//   3. places the separate parts by the stated assembly rule and checks that every glue tab
//      lands flat inside a face it can be glued to (≥ 95 % of the tab area),
//   4. checks that no two panels overlap in the folded state (collision-free final state).
// Zero board thickness is assumed (geometric validity, not physical validity).
// Usage: FoldVerify.verifyModel(svgStrings, modelId, spec, polygonClipping)
//   spec = { archetype, W, D, H, sub }  (paper mm)
// =============================================================================
(function (root) {
  'use strict';
  const E = 1e-3;

  // ---------- 2D / 3D helpers ----------
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], (a[2] || 0) - (b[2] || 0)];
  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const norm = a => { const l = Math.hypot(a[0], a[1], a[2]); return l ? mul(a, 1 / l) : a; };
  const area2 = r => { let s = 0; for (let i = 0; i < r.length; i++) { const p = r[i], q = r[(i + 1) % r.length]; s += p[0] * q[1] - q[0] * p[1]; } return s / 2; };
  const centroid = r => { const a = area2(r); let cx = 0, cy = 0; for (let i = 0; i < r.length; i++) { const p = r[i], q = r[(i + 1) % r.length], f = p[0] * q[1] - q[0] * p[1]; cx += (p[0] + q[0]) * f; cy += (p[1] + q[1]) * f; } return Math.abs(a) < 1e-12 ? r[0] : [cx / (6 * a), cy / (6 * a)]; };
  function inside(r, x, y) { let c = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const a = r[i], b = r[j]; if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; }
  const segDist = (p, a, b) => { const ab = [b[0] - a[0], b[1] - a[1]], l2 = ab[0] ** 2 + ab[1] ** 2; let t = l2 ? ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / l2 : 0; t = Math.max(0, Math.min(1, t)); return Math.hypot(p[0] - a[0] - t * ab[0], p[1] - a[1] - t * ab[1]); };
  const onRing = (r, p, tol = 0.02) => r.some((a, i) => segDist(p, a, r[(i + 1) % r.length]) < tol);

  // ---------- SVG parsing with nested transforms (translate / rotate / scale / matrix) ----------
  const I = [1, 0, 0, 1, 0, 0];
  const mmul = (m, n) => [m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1], m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3], m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5]];
  const app = (m, p) => [m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5]];
  function parseTransform(s) {
    let m = I; if (!s) return m;
    for (const [, fn, args] of s.matchAll(/(\w+)\s*\(([^)]*)\)/g)) {
      const v = args.split(/[\s,]+/).filter(Boolean).map(Number);
      let n = I;
      if (fn === 'translate') n = [1, 0, 0, 1, v[0], v[1] || 0];
      else if (fn === 'scale') n = [v[0], 0, 0, v.length > 1 ? v[1] : v[0], 0, 0];
      else if (fn === 'rotate') { const a = v[0] * Math.PI / 180, c = Math.cos(a), s2 = Math.sin(a); n = [c, s2, -s2, c, 0, 0]; if (v.length === 3) n = mmul(mmul([1, 0, 0, 1, v[1], v[2]], n), [1, 0, 0, 1, -v[1], -v[2]]); }
      else if (fn === 'matrix') n = v;
      m = mmul(m, n);
    }
    return m;
  }
  function walk(el, m, cb) { const mm = mmul(m, parseTransform(el.getAttribute && el.getAttribute('transform'))); cb(el, mm); [...el.children].forEach(c => walk(c, mm, cb)); }
  const pathRings = d => d.split(/[Zz]/).map(s => [...s.matchAll(/(-?\d*\.?\d+(?:e-?\d+)?)\s*,\s*(-?\d*\.?\d+(?:e-?\d+)?)/g)].map(q => [+q[1], +q[2]])).filter(r => r.length >= 3);

  // all parts of one model (CH1, TB1 …) from the printed sheets
  function parseModel(svgStrings, modelId) {
    const parts = [];
    svgStrings.forEach((s, si) => {
      const doc = new DOMParser().parseFromString(s, 'image/svg+xml'), svg = doc.documentElement;
      const layer = id => svg.querySelector(`[id="${id}"]`);
      const local = [];
      // ring = sheet coordinates (for folding); localRing = the part's own drawing frame (upright, before the packer's 90° turn)
      walk(layer('01_CUT_RED'), I, (el, m) => { if (el.tagName === 'path') pathRings(el.getAttribute('d')).forEach(r => local.push({ sheet: si, ring: r.map(p => app(m, p)), localRing: r, scores: [], labels: [] })); });
      const segs = [];
      walk(layer('02_SCORE_BLUE'), I, (el, m) => {
        const a = k => +el.getAttribute(k);
        if (el.tagName === 'line') segs.push([app(m, [a('x1'), a('y1')]), app(m, [a('x2'), a('y2')])]);
        else if (el.tagName === 'rect') { const c = [[a('x'), a('y')], [a('x') + a('width'), a('y')], [a('x') + a('width'), a('y') + a('height')], [a('x'), a('y') + a('height')]].map(p => app(m, p)); for (let i = 0; i < 4; i++) segs.push([c[i], c[(i + 1) % 4]]); }
        else if (el.tagName === 'path') { const pts = pathRings(el.getAttribute('d') + 'Z')[0] || []; for (let i = 0; i + 1 < pts.length; i++) segs.push([app(m, pts[i]), app(m, pts[i + 1])]); }
      });
      const labels = [];   // part labels only (the header and title block sit directly in the layer)
      walk(layer('03_LABELS_BLACK'), I, (el, m) => { if (el.tagName === 'text' && el.parentNode && el.parentNode.getAttribute('id') !== '03_LABELS_BLACK') { const t = el.textContent.trim(); if (t) labels.push({ t, at: app(m, [+el.getAttribute('x') || 0, (+el.getAttribute('y') || 0) - 0.6]), bold: el.getAttribute('font-weight') === 'bold' }); } });
      const owner = (x, y) => local.filter(p => inside(p.ring, x, y) || onRing(p.ring, [x, y], 0.05)).sort((a, b) => Math.abs(area2(a.ring)) - Math.abs(area2(b.ring)))[0];
      segs.forEach(sg => { const o = owner((sg[0][0] + sg[1][0]) / 2, (sg[0][1] + sg[1][1]) / 2); if (o) o.scores.push(sg); });
      labels.forEach(l => { const o = owner(l.at[0], l.at[1]); if (o) o.labels.push(l); });
      local.forEach(p => { const id = (p.labels.find(l => l.bold && /^[A-Z]{2}\d+-/.test(l.t)) || {}).t; p.model = id ? id.split('-')[0] : null; p.name = id ? id.replace(/^[A-Z]{2}\d+-/, '') : ''; });
      parts.push(...local.filter(p => p.model === modelId));
    });
    return parts;
  }

  // ---------- faces & hinges ----------
  function insertPoint(r, p) {
    for (let i = 0; i < r.length; i++) if (Math.hypot(r[i][0] - p[0], r[i][1] - p[1]) < 0.02) return i;
    for (let i = 0; i < r.length; i++) { const a = r[i], b = r[(i + 1) % r.length]; if (segDist(p, a, b) < 0.02) { r.splice(i + 1, 0, [p[0], p[1]]); return i + 1; } }
    return -1;
  }
  function splitFaces(ring, segs) {
    let faces = [ring.map(p => [p[0], p[1]])]; const unmatched = [];
    segs.forEach(sg => {
      const mid = [(sg[0][0] + sg[1][0]) / 2, (sg[0][1] + sg[1][1]) / 2];
      const k = faces.findIndex(f => inside(f, mid[0], mid[1]) && onRing(f, sg[0]) && onRing(f, sg[1]));
      if (k < 0) { if (!faces.some(f => onRing(f, sg[0]) && onRing(f, sg[1]) && onRing(f, mid))) unmatched.push(sg); return; }
      const f = faces[k].map(p => [...p]); let i = insertPoint(f, sg[0]), j = insertPoint(f, sg[1]); if (i < 0 || j < 0) { unmatched.push(sg); return; }
      j = f.findIndex(p => Math.hypot(p[0] - sg[1][0], p[1] - sg[1][1]) < 0.02); i = f.findIndex(p => Math.hypot(p[0] - sg[0][0], p[1] - sg[0][1]) < 0.02);
      const [a, b] = i < j ? [i, j] : [j, i];
      faces.splice(k, 1, f.slice(a, b + 1), [...f.slice(b), ...f.slice(0, a + 1)]);
    });
    faces = faces.filter(f => Math.abs(area2(f)) > 1e-4);
    const hinges = [];
    segs.forEach(sg => {
      const L = Math.hypot(sg[1][0] - sg[0][0], sg[1][1] - sg[0][1]);
      const share = faces.map((f, k) => { let ov = 0; for (let i = 0; i < f.length; i++) { const a = f[i], b = f[(i + 1) % f.length]; if (segDist(a, sg[0], sg[1]) < 0.02 && segDist(b, sg[0], sg[1]) < 0.02) ov += Math.hypot(b[0] - a[0], b[1] - a[1]); } return ov > L - 0.05 ? k : -1; }).filter(k => k >= 0);
      if (share.length === 2) hinges.push({ a: share[0], b: share[1], p: sg[0], q: sg[1] });
    });
    return { faces, hinges, unmatched };
  }

  // ---------- folding ----------
  const rotAbout = (P, u, th) => x => { const v = sub(x, P), c = Math.cos(th), s = Math.sin(th); return add(P, add(add(mul(v, c), mul(cross(u, v), s)), mul(u, dot(u, v) * (1 - c)))); };
  // maps: face index → function (x, y) → [X, Y, Z]; printed side of the sheet = +Z at the root
  function fold(F, rootIdx, signs) {
    const maps = new Array(F.faces.length).fill(null), order = [rootIdx], dirs = [];
    maps[rootIdx] = p => [p[0], p[1], 0];
    const normalOf = k => { const f = F.faces[k], c = centroid(f), A = maps[k]([c[0], c[1]]), B = maps[k]([c[0] + 1, c[1]]), C = maps[k]([c[0], c[1] + 1]); return norm(cross(sub(B, A), sub(C, A))); };
    for (let qi = 0; qi < order.length; qi++) {
      const k = order[qi];
      F.hinges.forEach((h, hi) => {
        const other = h.a === k ? h.b : h.b === k ? h.a : -1; if (other < 0 || maps[other]) return;
        const pm = maps[k], P = pm(h.p), u = norm(sub(pm(h.q), P)), n = normalOf(k), c = centroid(F.faces[other]), C = pm(c);
        const s = signs[hi] ?? 1;   // +1 = mountain (away from the printed side), −1 = valley
        let th = Math.PI / 2; if (dot(sub(rotAbout(P, u, th)(C), P), n) * s > 0) th = -th;
        const R = rotAbout(P, u, th); maps[other] = p => R(pm(p)); order.push(other); dirs.push({ hinge: hi, from: k, to: other, sign: s });
      });
    }
    return { maps, order, dirs, normalOf };
  }
  const face3 = (F, maps, k) => F.faces[k].map(p => maps[k](p));

  function bboxOf(pts) { const b = [0, 1, 2].map(i => [Math.min(...pts.map(p => p[i])), Math.max(...pts.map(p => p[i]))]); return { b, size: b.map(([lo, hi]) => hi - lo) }; }
  const sortedEq = (a, b, tol) => { const x = [...a].sort((p, q) => p - q), y = [...b].sort((p, q) => p - q); return x.every((v, i) => Math.abs(v - y[i]) <= tol); };

  // a face in 3D → its plane and 2D coordinates in that plane
  function planeOf(P3) { const o = P3[0]; let n = [0, 0, 0]; for (let i = 1; i + 1 < P3.length; i++) n = add(n, cross(sub(P3[i], o), sub(P3[i + 1], o))); n = norm(n); const u = norm(sub(P3[1], o)), v = cross(n, u); return { o, n, u, v }; }
  const to2 = (pl, X) => { const d = sub(X, pl.o); return [dot(d, pl.u), dot(d, pl.v)]; };
  function overlapArea(pc, A3, B3) {
    const pa = planeOf(A3), pb = planeOf(B3);
    if (Math.abs(Math.abs(dot(pa.n, pb.n)) - 1) > 1e-4 || Math.abs(dot(sub(B3[0], pa.o), pa.n)) > 0.05) return 0;
    const a = A3.map(X => to2(pa, X)), b = B3.map(X => to2(pa, X)), close = r => [...r, r[0]];
    try { const x = pc.intersection([[close(a)]], [[close(b)]]); return x.reduce((s, poly) => s + poly.reduce((t, r, i) => t + (i ? -1 : 1) * Math.abs(area2(r.slice(0, -1))), 0), 0); } catch (e) { return 0; }
  }

  // ---------- one model ----------
  function verifyModel(svgStrings, modelId, spec, pc) {
    const parts = parseModel(svgStrings, modelId);
    const out = { model: modelId, archetype: spec.archetype, parts: parts.length, faces: 0, hinges: 0, folds: [], valley: [], tabs: 0, tabsMated: 0, tabsUnmated: [], unmatchedScores: 0, sizeOk: false, size: null, target: null, collisions: 0, notes: [] };
    if (!parts.length) { out.notes.push('no parts found on the sheets'); return out; }
    const name = (P, k) => { const f = P.F.faces[k], l = P.labels.find(l => inside(f, l.at[0], l.at[1])); return l ? l.t.replace(/^[A-Z]{2}\d+-/, '').replace(/^[A-Z]\d\s*/, '').replace(/\s*\(.*/, '').replace(/^A\d:\s*/, '') : null; };
    parts.forEach(P => { P.F = splitFaces(P.ring, P.scores); out.faces += P.F.faces.length; out.hinges += P.F.hinges.length; out.unmatchedScores += P.F.unmatched.length; });
    // tabs: a face with one hinge, small, no deeper than 8 mm from that hinge
    parts.forEach(P => {
      const deg = P.F.faces.map((_, k) => P.F.hinges.filter(h => h.a === k || h.b === k));
      P.isTab = P.F.faces.map((f, k) => { if (deg[k].length !== 1) return false; const h = deg[k][0], other = h.a === k ? h.b : h.a; const depth = Math.max(...f.map(p => segDist(p, h.p, h.q)));
        const far = f.filter(p => segDist(p, h.p, h.q) > depth - 0.02), farLen = far.length >= 2 ? Math.hypot(far[0][0] - far[1][0], far[0][1] - far[1][1]) : 0, hl = Math.hypot(h.q[0] - h.p[0], h.q[1] - h.p[1]);
        return depth <= 8 && farLen < hl - 0.5 && Math.abs(area2(f)) < 0.6 * Math.abs(area2(P.F.faces[other])) && !name(P, k); });
      out.tabs += P.isTab.filter(Boolean).length;
    });
    const A = spec.archetype, W = spec.W, D = spec.D, H = spec.H, S = spec.sub;
    // the main folded part, its root face, and its target
    const rootName = { chair: /SEAT/, sofa: /SEAT/, table: /TABLE TOP/, bed: /MATTRESS TOP|^FRONT$/, cabinet: /CABINET TOP|^FRONT$/ }[A];
    const main = parts.find(P => P.F.hinges.some(h => !P.isTab[h.a] && !P.isTab[h.b]) && P.F.faces.some((_, k) => rootName.test(name(P, k) || '')));
    if (!main) { out.notes.push('main folded part not found'); return out; }
    const rootIdx = main.F.faces.findIndex((_, k) => rootName.test(name(main, k) || ''));
    const ring = /^FRONT$/.test(name(main, rootIdx) || '');
    const rise = Math.max(0, -Math.min(0, ...(spec.curve || [0])));   // a designed top curve may rise above H (paper mm)
    const target = ring ? [W, D, A === 'bed' ? S : H] : [W, D, (A === 'bed' ? S : (A === 'chair' || A === 'sofa') ? H + rise : H)];
    const rootZ = { chair: S, sofa: S, table: H, bed: S, cabinet: H }[A];
    if ((A === 'chair' || A === 'sofa') && !main.F.faces.some((_, k) => /BACK/.test(name(main, k) || ''))) target[2] = S;   // v4.3: seat + front strip only
    out.target = target;
    // search fold directions of the panel hinges (tabs folded later)
    const panelH = main.F.hinges.map((h, i) => (!main.isTab[h.a] && !main.isTab[h.b]) ? i : -1).filter(i => i >= 0);
    let best = null;
    for (let mask = 0; mask < (1 << panelH.length); mask++) {
      const signs = {}; panelH.forEach((hi, j) => { signs[hi] = (mask >> j) & 1 ? -1 : 1; });
      const f = fold(main.F, rootIdx, signs), pts = main.F.faces.flatMap((_, k) => main.isTab[k] || !f.maps[k] ? [] : face3(main.F, f.maps, k));
      const bb = bboxOf(pts); let ok = sortedEq(bb.size, target, 0.05);
      if (ok && !ring) ok = Math.abs(-bb.b[2][0] - rootZ) <= 0.05;          // the base panel sits at its height above the floor
      if (ok && ring) { const c = [(bb.b[0][0] + bb.b[0][1]) / 2, (bb.b[1][0] + bb.b[1][1]) / 2, 0];   // printed side out: wall normals point away from the centre
        ok = main.F.faces.every((_, k) => main.isTab[k] || dot(f.normalOf(k), sub(face3(main.F, f.maps, k)[0], [c[0], c[1], face3(main.F, f.maps, k)[0][2]])) > 0); }
      if (ok && (!best || panelH.filter(hi => signs[hi] < 0).length < best.valley)) best = { signs, f, bb, valley: panelH.filter(hi => signs[hi] < 0).length };
    }
    if (!best) { out.notes.push('no fold-direction assignment reaches the target size'); return out; }
    out.sizeOk = true; out.size = best.bb.size.map(v => +v.toFixed(2));
    const shift = [-best.bb.b[0][0], -best.bb.b[1][0], -best.bb.b[2][0]];
    const place = X => add(X, shift);
    // record panel folds
    panelH.forEach(hi => { const h = main.F.hinges[hi]; const nm = `${name(main, h.a) || 'face'}–${name(main, h.b) || 'face'}`; out.folds.push({ part: main.name, hinge: nm, dir: best.signs[hi] > 0 ? 'mountain' : 'valley' }); if (best.signs[hi] < 0) out.valley.push(`${main.name}: ${nm}`); });
    // mating surfaces: panels of the main part + separate parts placed by the assembly rule
    const panels3 = main.F.faces.map((_, k) => main.isTab[k] ? null : face3(main.F, best.f.maps, k).map(place));
    const surfaces = panels3.map((p, k) => p && { part: main.name, face: name(main, k) || 'panel', P3: p }).filter(Boolean);
    const others = parts.filter(P => P !== main);
    const backY = (() => { const k = main.F.faces.findIndex((_, i) => /BACK/.test(name(main, i) || '')); if (k < 0) return null; const p = panels3[k]; return p ? p.reduce((s, X) => s + X[1], 0) / p.length : null; })();
    others.forEach(P => {
      const LR = P.localRing, bb = { x0: Math.min(...LR.map(p => p[0])), x1: Math.max(...LR.map(p => p[0])), y0: Math.min(...LR.map(p => p[1])), y1: Math.max(...LR.map(p => p[1])) };
      if (/LEFT|RIGHT/.test(P.name) && (A === 'chair' || A === 'sofa')) {
        // side profile: stands in the plane x = 0 (B1) or x = W (B2); its tall post goes under the back panel
        const x = /LEFT/.test(P.name) ? 0 : W, postLeft = (() => { const tallAt = LR.filter(p => Math.abs(p[1] - bb.y0) < 0.05).map(p => p[0]); return Math.min(...tallAt) - bb.x0 < (bb.x1 - bb.x0) / 2; })();
        const backAtMax = backY != null && backY > D / 2, flip = postLeft === backAtMax;
        surfaces.push({ part: P.name, face: P.name, P3: LR.map(p => [x, flip ? bb.x1 - p[0] : p[0] - bb.x0, bb.y1 - p[1]]) });
      } else if (/HEADBOARD/.test(P.name)) {
        out.headboard = { width: +(bb.x1 - bb.x0).toFixed(2), height: +(bb.y1 - bb.y0).toFixed(2) };
        surfaces.push({ part: P.name, face: P.name, glue: true, P3: LR.map(p => [p[0] - bb.x0, backY != null && backY > D / 2 ? D : 0, bb.y1 - p[1]]) });
      } else if (/BACK/.test(P.name) && (A === 'chair' || A === 'sofa')) {
        // separate back panel: stands on the seat's rear edge, printed side to the REAR (outside), bottom at seat height
        const k = P.F.faces.findIndex((_, i) => !P.isTab[i]), f = fold(P.F, k, {}), fb = P.F.faces[k];
        const seatK = main.F.faces.findIndex((_, i) => /SEAT/.test(name(main, i) || '')), frontK = main.F.faces.findIndex((_, i) => /FRONT/.test(name(main, i) || ''));
        const seat = panels3[seatK], yF = panels3[frontK].reduce((s2, X) => s2 + X[1], 0) / panels3[frontK].length;
        const ys = seat.map(X => X[1]), yR = Math.abs(Math.min(...ys) - yF) > Math.abs(Math.max(...ys) - yF) ? Math.min(...ys) : Math.max(...ys);
        const sg = Math.sign(yR - yF) || 1, x0 = Math.min(...fb.map(p => p[0])), yBot = Math.max(...fb.map(p => p[1])), zS = Math.max(...seat.map(X => X[2]));
        const T = X => [sg > 0 ? X[0] - x0 : W - (X[0] - x0), yR + sg * X[2], zS + (yBot - X[1])];   // local x → ±X, local y (down) → −Z, printed normal → outward
        P.placed = { f, k, top: T };
        const B3 = face3(P.F, f.maps, k).map(T); surfaces.push({ part: P.name, face: P.name, P3: B3 });
        if (spec.curve) { const zAt = x => Math.max(...B3.filter(X => Math.abs(X[0] - x) < 0.02).map(X => X[2]));
          const want0 = zS + (H - S) - spec.curve[0], wantW = zS + (H - S) - spec.curve[4];
          out.curveOk = Math.abs(zAt(0) - want0) < 0.05 && Math.abs(zAt(W) - wantW) < 0.05; if (!out.curveOk) out.notes.push(`back curve mirrored: z(0) ${zAt(0).toFixed(2)} vs ${want0.toFixed(2)}`); }
      } else if (P.F.hinges.length) {
        // separate top with tabs on all edges (strip style): sits on the walls, printed side up, tabs fold down
        const k = P.F.faces.findIndex((_, i) => !P.isTab[i]), f = fold(P.F, k, {}), pts = face3(P.F, f.maps, k), b2 = bboxOf(pts);
        const swap = Math.abs(b2.size[0] - W) > 0.05;
        const top = X => { let x = X[0] - b2.b[0][0], y = X[1] - b2.b[1][0]; if (swap) [x, y] = [y, x]; return [x, y, target[2] + X[2]]; };
        P.placed = { f, k, top };
        P.F.faces.forEach((_, i) => { if (!P.isTab[i]) surfaces.push({ part: P.name, face: P.name, P3: face3(P.F, f.maps, i).map(top) }); });
      }
    });
    // tabs: try fold away from the printed side first, then toward it; must land flat inside a surface (≥ 95 %)
    const tabJobs = [];
    main.F.faces.forEach((_, k) => { if (main.isTab[k]) tabJobs.push({ P: main, k, sign0: best.signs, map: place }); });
    others.forEach(P => { if (P.placed) P.F.faces.forEach((_, k) => { if (P.isTab[k]) tabJobs.push({ P, k, sign0: {}, map: P.placed.top, root: P.placed.k }); }); });
    tabJobs.forEach(j => {
      const hi = j.P.F.hinges.findIndex(h => h.a === j.k || h.b === j.k), parent = j.P.F.hinges[hi].a === j.k ? j.P.F.hinges[hi].b : j.P.F.hinges[hi].a;
      let mated = null;
      for (const s of [1, -1]) {
        const f = fold(j.P.F, j.root ?? rootIdx, { ...j.sign0, [hi]: s }), T = face3(j.P.F, f.maps, j.k).map(j.map), At = Math.abs(area2(j.P.F.faces[j.k]));
        const hit = surfaces.find(sf => !(sf.part === j.P.name && sf.face === (name(j.P, parent) || 'panel')) && overlapArea(pc, T, sf.P3) >= 0.95 * At);
        if (hit) { mated = { s, onto: `${hit.part}${hit.face !== hit.part ? ' ' + hit.face : ''}` }; break; }
      }
      const tag = `${j.P.name} tab on ${name(j.P, parent) || 'panel'}`;
      if (mated) { out.tabsMated++; out.folds.push({ part: j.P.name, hinge: tag, dir: mated.s > 0 ? 'mountain' : 'valley', onto: mated.onto }); if (mated.s < 0) out.valley.push(tag + ' → ' + mated.onto); }
      else out.tabsUnmated.push(tag);
    });
    // headboard: its glue band must lie on the back wall
    const hb = surfaces.find(s => s.glue);
    if (hb) { const wall = surfaces.filter(s => !s.glue && /BACK/.test(s.face)); const ov = wall.reduce((m, w) => Math.max(m, overlapArea(pc, hb.P3, w.P3)), 0); out.headboardGlue = +ov.toFixed(2); if (ov < 1) out.notes.push('headboard band does not meet the back wall'); }
    // collisions: two panels of the folded model overlapping flat (zero thickness)
    const pan = surfaces.filter(s => !s.glue);
    for (let i = 0; i < pan.length; i++) for (let k = i + 1; k < pan.length; k++) if (overlapArea(pc, pan[i].P3, pan[k].P3) > 0.5) { out.collisions++; out.notes.push(`overlap: ${pan[i].part} ${pan[i].face} / ${pan[k].part} ${pan[k].face}`); }
    // the whole assembled model (all panels and separate parts, zero thickness) must be the target W × D × H
    { const all = surfaces.flatMap(s2 => s2.P3), bb = bboxOf(all), rise = Math.max(0, -Math.min(0, ...(spec.curve || [0])));
      const Hfull = (A === 'chair' || A === 'sofa' || A === 'bed') ? H + rise : H;
      out.assembled = bb.size.map(v => +v.toFixed(2)); out.assembledTarget = [W, D, Hfull];
      if (!sortedEq(bb.size, [W, D, Hfull], 0.05)) { out.sizeOk = false; out.notes.push(`assembled ${out.assembled.join(' × ')} ≠ ${[W, D, Hfull].map(v => +v.toFixed(2)).join(' × ')}`); } }
    out.ruleOk = out.valley.length === 0;   // the printed rule: every blue line folds away from the printed side
    out.ok = out.ruleOk && out.sizeOk && out.curveOk !== false && out.tabsUnmated.length === 0 && out.unmatchedScores === 0 && out.collisions === 0 && !out.notes.some(n => /headboard/.test(n));
    out.order = best.f.order.map(k => name(main, k) || (main.isTab[k] ? 'tab' : 'face'));
    return out;
  }

  root.FoldVerify = { verifyModel, parseModel, splitFaces };
})(typeof window !== 'undefined' ? window : globalThis);
