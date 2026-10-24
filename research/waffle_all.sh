#!/bin/sh
# usage: waffle_all.sh <tool dir> — judges every <case>_1-10/_1-20 waffle in research/<tool>/
T=$1
for c in chair table sofa_curved; do for sc in 10 20; do m=1; [ $sc = 20 ] && m=0.5
  f=$T/$c/${c}_1-$sc.waffle.json; [ -f "$f" ] || { echo "$c 1:$sc: no waffle"; continue; }
  python waffle_judge.py "$f" models/${c}_waffle_solid.stl --mesh-scale $m --json $T/$c/${c}_1-$sc.wjudge.json > /dev/null && python -c "import json;d=json.load(open('$T/$c/${c}_1-$sc.wjudge.json'));print('$c 1:$sc', {k:d.get(k) for k in ['ok','ribs_x','ribs_y','size_mm','size_error_mm','material_outside_solid_mm2','section_left_out_pct','crossings','interference','slot_width_mm','slot_width_target_mm','shallowest_slot_mm','drop_assembly_pct','windows','loose_parts']})"
done; done
