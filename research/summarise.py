import sys, re
for l in sys.stdin:
    m = re.match(r"(\S+ 1:\d+) (\{.*?\})(.*)", l.strip())
    if not m: print(l.strip()); continue
    d = eval(m.group(2)); print(m.group(1), d['ok'], 'M1', d['M1_size_error_mm'], 'cov', d['coverage_pct'], 'M2', d['M2_fold_direction_ok_pct'], 'M3', d['M3_tabs_land_pct'], 'M4', d['M4_overlapping_panels'], 'unpl', d['unplaced_faces'], 'inw', d['printed_inward_faces'], 'unm', d['unmatched_scores'], m.group(3)[:160])
