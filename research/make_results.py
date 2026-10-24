"""Build research/RESULTS.md tables from the judge outputs (no number is typed by hand).
Nets: research/<tool>/<case>/<case>_1-<s>.judge.json (net_judge.py). Waffle: *.wjudge.json (waffle_judge.py).
Settings and sheet counts are read from each tool's settings.md / export logs where available."""
import json, os, glob
HERE = os.path.dirname(os.path.abspath(__file__))
CASES = ['chair', 'table', 'sofa_curved']; SCALES = ['1-10', '1-20']
NET_TOOLS = [('ours', 'Ours v4.3.2'), ('export_paper_model', 'Export Paper Model 1.4.2'), ('polyzamboni', 'PolyZamboni 1.3.1'), ('lamina', 'Lamina 0.3.0 (Folded)'), ('ours_v4_2_4', 'Ours v4.2.4 (negative control)')]
WAF_TOOLS = [('ours', 'Ours v4.3.2'), ('lamina', 'Lamina 0.3.0 (Interlocked)')]

def load(p):
    try: return json.load(open(p))
    except Exception: return None

def fmt(v, suf=''):
    return '—' if v is None else f'{v}{suf}'

def net_rows():
    rows = ['| Tool | Case | Scale | Pass | M1 size err (mm) | Coverage % | M2 folds as marked % | M3 tabs land | M4 overlaps | Faces not placed | Printed side inward | Score lines with no flap |', '|' + '---|' * 12]
    for t, name in NET_TOOLS:
        for c in CASES:
            for s in SCALES:
                d = load(os.path.join(HERE, t, c, f'{c}_{s}.judge.json'))
                if d is None:
                    if os.path.isdir(os.path.join(HERE, t)): rows.append(f'| {name} | {c} | 1:{s[2:]} | ❌ no output | | | | | | | | |')
                    continue
                tabs = f"{d['tabs_mated']}/{d['tabs']}" if d['tabs'] else '—'   # tabs that land / the tool's own tabs (unplaced faces have their own column)
                rows.append(f"| {name} | {c} | 1:{s[2:]} | {'✅' if d['ok'] else '❌'} | {fmt(d['M1_size_error_mm'])} | {fmt(d['coverage_pct'])} | {fmt(d['M2_fold_direction_ok_pct'])} ({d['folds_counted']} folds) | {tabs} | {d['M4_overlapping_panels']} | {d['unplaced_faces']} | {d['printed_inward_faces']} | {d['unmatched_scores']} |")
    return '\n'.join(rows)

def waffle_rows():
    rows = ['| Tool | Case | Scale | Pass | Ribs X+Y | Size err (mm) | Material outside solid (mm²) | Section left out % | Crossings | Interference | Slot width (mm) / target | Shallowest slot (mm) | One drop order % | Windows | Loose parts |', '|' + '---|' * 15]
    for t, name in WAF_TOOLS:
        for c in CASES:
            for s in SCALES:
                d = load(os.path.join(HERE, t, c, f'{c}_{s}.wjudge.json'))
                if d is None:
                    if os.path.isdir(os.path.join(HERE, t)): rows.append(f'| {name} | {c} | 1:{s[2:]} | ❌ no output |' + ' |' * 11)
                    continue
                sw = '—' if not d['slot_width_mm'] else (f"{d['slot_width_mm'][0]}" if d['slot_width_mm'][0] == d['slot_width_mm'][1] else f"{d['slot_width_mm'][0]}–{d['slot_width_mm'][1]}")
                rows.append(f"| {name} | {c} | 1:{s[2:]} | {'✅' if d['ok'] else '❌'} | {d['ribs_x']}+{d['ribs_y']} | {d['size_error_mm']} | {d['material_outside_solid_mm2']} | {fmt(d['section_left_out_pct'])} | {d['crossings']} | {d['interference']} | {sw} / {d['slot_width_target_mm']} | {fmt(d['shallowest_slot_mm'])} | {fmt(d['drop_assembly_pct'])} | {d['windows']} | {d['loose_parts']} |")
    return '\n'.join(rows)

def trace_rows():
    p = os.path.join(HERE, 'vtracer', 'results.md')
    return open(p).read() if os.path.exists(p) else '(no tracing results)'

if __name__ == '__main__':
    open(os.path.join(HERE, 'tables_generated.md'), 'w').write('## Fold & Glue nets (net_judge.py)\n\n' + net_rows() + '\n\n## Waffle (waffle_judge.py)\n\n' + waffle_rows() + '\n')
    print(net_rows()); print(); print(waffle_rows())
