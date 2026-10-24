"""Export our v4.3.1 Waffle ribs (assembled positions) in the normalised format (research/FORMAT.md).
Calls the student build's own waffleForPiece in headless Chromium: board 1.5 mm, laser (kerf 0), slot fit 0, spacing default.
Needs the repo served at http://localhost:8765/."""
import json, os, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
CASES = {'chair': 'chair', 'table': 'table', 'sofa_curved': 'sofa'}
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(); pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(3000)
    for case, a in CASES.items():
        for sc in (10, 20):
            r = pg.evaluate("""([a, sc]) => { const A = archetypes[a]; const p = { ...newPiece(a), archetype: a, w: A.w, d: A.d, h: A.h, subH: A.subH, method: 'waffle', kerf: 'laser', slotAdj: 0 };
                const wf = waffleForPiece(p, { scale: sc, thicknessMm: 1.5, sheetSize: 'A3' });
                const n = nestAll([p], { scale: sc, sheetSize: 'A3', thicknessMm: 1.5, name: 'T', id: '1', course: 'RIR2101' });
                return { version: TOOL_VERSION, sheets: n.sheets.length, spacing: p.spacing || WAFFLE_SPACING_DEFAULT, valid: wf.validation, ribs: wf.res.ribs.map(r => ({ name: r.name, plane: r.dir, offset_mm: r.pos,
                  outline_mm: r.poly[0][0].slice(0, -1), holes_mm: r.poly[0].slice(1).map(h => h.slice(0, -1)), multi: r.poly.length })) }; }""", [a, sc])
            assert all(x['multi'] == 1 for x in r['ribs']), 'multi-polygon rib'
            os.makedirs(os.path.join(HERE, case), exist_ok=True)
            out = {'tool': f'Studio Flat-Pack Maker v{r["version"]}', 'board_mm': 1.5, 'kerf_mm': 0.0, 'sheets_A3': r['sheets'], 'spacing_mm': r['spacing'], 'own_validation': r['valid'],
                   'ribs': [{k: v for k, v in x.items() if k != 'multi'} for x in r['ribs']]}
            json.dump(out, open(os.path.join(HERE, case, f'{case}_1-{sc}.waffle.json'), 'w'))
            print(case, sc, len(r['ribs']), 'ribs', r['sheets'], 'A3 sheets', 'own validation ok' if (r['valid'] or {}).get('ok', r['valid']) else r['valid'])
    b.close()
