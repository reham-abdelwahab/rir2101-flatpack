"""Headless export of fold-and-glue nets with Blender add-on "Export Paper Model".

Usage (bpy 5.2.3 as a module):
  python -I run_export.py <dir containing io_export_paper_model package> <out_root>

Uses the add-on's own operators: bpy.ops.mesh.unfold() then bpy.ops.export_mesh.paper_model().
All add-on defaults are kept except the settings listed in CHANGED below.
"""
import sys, os, json, time, glob
import bpy, bmesh

addon_parent, out_root = sys.argv[1], sys.argv[2]
sys.path.insert(0, addon_parent)
bpy.context.preferences.addons.new().module = "io_export_paper_model"
import io_export_paper_model as addon
addon.register()

MODELS = "/root/rir2101-flatpack/research/models"
CASES = ["chair", "table", "sofa_curved"]
# scale divisor: OBJ imports 1 unit = 1 Blender metre; exporter writes metres*1000 = mm.
# mesh unit is already paper-mm at 1:10, so divisor 1000 -> 1:10, 2000 -> 1:20.
SCALES = {"1-10": 1000.0, "1-20": 2000.0}
CHANGED = dict(file_format='SVG', page_size_preset='A3', output_size_x=0.297, output_size_y=0.420)

reports = []
def capture_reports():
    # operator reports are printed to stdout by bpy in background mode; we also keep return values
    pass

results = {}
for case in CASES:
    for tag, divisor in SCALES.items():
        # fresh scene each run
        bpy.ops.wm.read_homefile(use_empty=True)
        bpy.ops.wm.obj_import(filepath=f"{MODELS}/{case}_fold.obj", forward_axis='Y', up_axis='Z')
        ob = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = ob
        sce = bpy.context.scene
        # scene-level add-on setting: auto scale must be off, otherwise prepare() overrides the scale
        sce.paper_model.use_auto_scale = False
        sce.paper_model.scale = divisor
        out_dir = os.path.join(out_root, case)
        os.makedirs(out_dir, exist_ok=True)
        for old in glob.glob(os.path.join(out_dir, f"raw_{tag}*.svg")):
            os.remove(old)
        path = os.path.join(out_dir, f"raw_{tag}.svg")
        rec = {"case": case, "scale": tag, "divisor": divisor}
        t0 = time.perf_counter()
        try:
            r1 = bpy.ops.mesh.unfold()
            r2 = bpy.ops.export_mesh.paper_model(filepath=path, scale=divisor, **CHANGED)
            rec["unfold_result"] = sorted(r1)
            rec["export_result"] = sorted(r2)
        except Exception as e:  # RuntimeError carries the operator's error report text
            rec["error"] = f"{type(e).__name__}: {e}"
        rec["seconds"] = round(time.perf_counter() - t0, 4)
        rec["islands"] = len(ob.data.paper_island_list)
        rec["island_names"] = [i.name for i in ob.data.paper_island_list]
        rec["seams"] = sum(1 for e in ob.data.edges if e.use_seam)
        rec["files"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(out_dir, f"raw_{tag}*.svg")))
        results[f"{case}_{tag}"] = rec
        print("RESULT", json.dumps(rec))

# VARIANT (non-default, run only because the default sofa_curved 1:10 export failed):
# scene setting "Limit Island Size" (limit_by_page=True) with page preset A3, so the add-on's own
# unfold splits islands to fit the page. Output kept separate: raw_1-10_limit.svg.
for case, tag, divisor in [("sofa_curved", "1-10", 1000.0)]:
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.wm.obj_import(filepath=f"{MODELS}/{case}_fold.obj", forward_axis='Y', up_axis='Z')
    ob = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = ob
    pm = bpy.context.scene.paper_model
    pm.use_auto_scale = False
    pm.scale = divisor
    pm.limit_by_page = True
    pm.page_size_preset = 'A3'   # update callback sets output_size 0.297 x 0.420
    out_dir = os.path.join(out_root, case)
    for old in glob.glob(os.path.join(out_dir, f"raw_{tag}_limit*.svg")):
        os.remove(old)
    path = os.path.join(out_dir, f"raw_{tag}_limit.svg")
    rec = {"case": case, "scale": tag, "divisor": divisor, "variant": "limit_by_page=True, scene page_size_preset=A3",
           "scene_cage_m": [pm.output_size_x, pm.output_size_y]}
    t0 = time.perf_counter()
    try:
        rec["unfold_result"] = sorted(bpy.ops.mesh.unfold())
        rec["export_result"] = sorted(bpy.ops.export_mesh.paper_model(filepath=path, scale=divisor, **CHANGED))
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["seconds"] = round(time.perf_counter() - t0, 4)
    rec["islands"] = len(ob.data.paper_island_list)
    rec["island_names"] = [i.name for i in ob.data.paper_island_list]
    rec["seams"] = sum(1 for e in ob.data.edges if e.use_seam)
    rec["files"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(out_dir, f"raw_{tag}_limit*.svg")))
    results[f"{case}_{tag}_limit"] = rec
    print("RESULT", json.dumps(rec))

with open(os.path.join(out_root, "export_log.json"), "w") as f:
    json.dump(results, f, indent=1)
