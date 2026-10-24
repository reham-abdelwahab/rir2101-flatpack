#!/bin/sh
# usage: judge_all.sh <tool dir> [unmarked rule]  — judges every <case>_1-10/_1-20 net in research/<tool>/
T=$1; U=${2:-mountain}
for c in chair table sofa_curved; do for sc in 10 20; do m=1; [ $sc = 20 ] && m=0.5
  f=$T/$c/${c}_1-$sc.net.svg; [ -f "$f" ] || { echo "$c 1:$sc: no net"; continue; }
  python net_judge.py "$f" models/${c}_fold.obj --mesh-scale $m --unmarked $U --json $T/$c/${c}_1-$sc.judge.json > /dev/null && python -c "import json;d=json.load(open('$T/$c/${c}_1-$sc.judge.json'));print('$c 1:$sc', {k:d.get(k) for k in ['ok','parts','faces','M1_size_error_mm','coverage_pct','M2_fold_direction_ok_pct','folds_counted','tabs','M3_tabs_land_pct','M4_overlapping_panels','unplaced_faces','printed_inward_faces','unmatched_scores']}, d['notes'][:2], d['fold_direction_faults'][:2])"
done; done
