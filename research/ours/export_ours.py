"""Export our v4.3.0 Fold & Glue nets in the normalised format (research/FORMAT.md).

Drives the student build (index.html) through tests/regress.html in headless Chromium, nests each case on A3
exactly as a student would print it, and reads the cut and score layers with FoldVerify.parseModel (a format
reader only: it applies the SVG transforms and assigns each blue line to its part). Our sheets carry no
direction per line: the printed rule "all blue lines fold away from you" applies, so every fold is written
data-fold="unmarked" and judged with --unmarked mountain. Also writes the v4.2 chair net (back folded up from
the seat) as a negative control.
Curve offsets: from v4.3.2 the tool stores them in real cm (F1 fixed), so the same offsets give the same real shape at every
scale; older builds (no CURVE_UNITS_PER_CM) stored paper mm, and the 1:20 sofa then got offsets × 0.5 by hand. Needs the repo
served at http://localhost:8765/.
"""
import json, os, time
from playwright.sync_api import sync_playwright
import sys
HERE = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8765/tests/regress.html?base='
CASES = {'chair': ('chair', 'CH1', [0, 0, 0, 0, 0]), 'table': ('table', 'TB1', [0, 0, 0, 0, 0]), 'sofa_curved': ('sofa', 'SF1', [0, -14, -20, -14, 0])}

def write_svg(path, parts, note):
    xs = [x for p in parts for x, y in p['ring']] or [0]; ys = [y for p in parts for x, y in p['ring']] or [0]
    W, H = max(xs) + 5, max(ys) + 5
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}mm" height="{H:.2f}mm" viewBox="0 0 {W:.2f} {H:.2f}">', f'<!-- {note} -->', '<g id="01_CUT_RED">']
    for p in parts: s.append('<path d="M ' + ' L '.join(f'{x:.4f},{y:.4f}' for x, y in p['ring']) + ' Z"/>')
    s.append('</g><g id="02_SCORE_BLUE">')
    for p in parts:
        for (x1, y1), (x2, y2) in p['scores']: s.append(f'<line x1="{x1:.4f}" y1="{y1:.4f}" x2="{x2:.4f}" y2="{y2:.4f}" data-fold="unmarked"/>')
    s.append('</g><g id="03_LABELS_BLACK">')
    for p in parts:
        for l in p['labels']: s.append(f'<text x="{l["at"][0]:.2f}" y="{l["at"][1]:.2f}">{l["t"].replace("&", "&amp;").replace("<", "&lt;")}</text>')
    s.append('</g></svg>'); open(path, 'w').write('\n'.join(s))

if __name__ == '__main__':
    log = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=os.environ.get('CHROME') or None); pg = b.new_page(); pg.goto(URL); pg.wait_for_function('window.REGRESS', timeout=180000)
        if not pg.evaluate('typeof FoldVerify !== "undefined"'): pg.add_script_tag(url='http://localhost:8765/tests/fold_verify.js')   # older suites (v4.2.4) do not load the reader
        for case, (a, mid, curve) in CASES.items():
            os.makedirs(os.path.join(HERE, case), exist_ok=True)
            for sc in (10, 20):
                t0 = time.time()
                r = pg.evaluate("""([a, mid, curve, sc]) => { const wc = document.getElementById('fc').contentWindow, A = wc.eval('archetypes')[a];
                  const p = { archetype: a, w: A.w, d: A.d, h: A.h, subH: A.subH, qty: 1, method: 'fold', curveOffsets: wc.eval('typeof CURVE_UNITS_PER_CM') !== 'undefined' ? curve : curve.map(v => v * 10 / sc) };   // v4.3.2+: real cm; older builds: paper mm, scaled by hand
                  const n = wc.nestAll([p], { scale: sc, sheetSize: 'A3', thicknessMm: 0.5, name: 'T', id: '1', course: 'RIR2101' });
                  const parts = FoldVerify.parseModel(n.sheets.map(s => s.svg), mid);
                  return { sheets: n.sheets.length, version: wc.eval('TOOL_VERSION'), parts: parts.map(p => ({ sheet: p.sheet, name: p.name, ring: p.ring, scores: p.scores, labels: p.labels.map(l => ({ t: l.t, at: l.at })) })) }; }""", [a, mid, curve, sc])
                off = 0; parts = []
                for si in range(r['sheets']):         # A3 sheets side by side, 10 mm apart
                    for p in [q for q in r['parts'] if q['sheet'] == si]:
                        sh = lambda P: [P[0] + off, P[1]]
                        parts.append({'ring': [sh(q) for q in p['ring']], 'scores': [[sh(q) for q in sg] for sg in p['scores']], 'labels': [{'t': l['t'], 'at': sh(l['at'])} for l in p['labels']]})
                    off += 307
                tag = f'{case}_1-{sc}'
                write_svg(os.path.join(HERE, case, tag + '.net.svg'), parts, f'Studio Flat-Pack Maker v{r["version"]} {case} 1:{sc}, A3, {r["sheets"]} sheet(s); printed rule: all blue lines fold away from you')
                log[tag] = {'version': r['version'], 'sheets': r['sheets'], 'parts': len(parts), 'folds': sum(len(p['scores']) for p in parts), 'seconds': round(time.time() - t0, 2)}
        b.close()
    # negative control: v4.2 chair net, back folded UP from the seat (valley under our rule)
    neg = [{'ring': [[0, 90], [0, 50], [0, 45], [0, 0], [45, 0], [45, 45], [45, 50], [45, 90]], 'scores': [[[0, 45], [45, 45]], [[0, 50], [45, 50]]], 'labels': []}]
    os.makedirs(os.path.join(HERE, 'negative'), exist_ok=True)
    write_svg(os.path.join(HERE, 'negative', 'v4_2_chair_back_seat_front.net.svg'), neg, 'negative control: v4.2 chair strip back-seat-front, printed rule says mountain')
    json.dump(log, open(os.path.join(HERE, 'export_log.json'), 'w'), indent=1); print(json.dumps(log, indent=1))
