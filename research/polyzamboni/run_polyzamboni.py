"""Headless driver for the Blender add-on PolyZamboni (commit a6b880e, v1.3.1, GPL-3.0-or-later).

Usage (bpy 5.2.3 as a Python module, matplotlib + networkx installed):
  python -I run_polyzamboni.py <dir containing the PolyZamboni package> <out_root>

Why not bpy.ops.polyzamboni.*:  in bpy-as-a-module there is no window/event loop.
  * cut_initialization_op / export_operator_svg compute required attributes in invoke() only;
    EXEC_DEFAULT raises AttributeError ('selected_mesh_is_manifold' / 'user_defined_page_layout_exists').
  * auto_cuts_op runs its generator from a modal TIMER handler; INVOKE_DEFAULT returns RUNNING_MODAL and the
    timer never fires without a window.
So this script performs exactly what those operators do, using the add-on's own code:
  1. the checks of InitializeCuttingOperator.invoke (operators.py:47-97), then
     InitializeCuttingOperator.execute body -> operators_backend.initialize_paper_model (operators.py:126)
  2. AutoCutsOperator.execute/modal: PaperModel.from_existing + autozamboni.greedy_auto_cuts drained to the end
     + paper_model.close()  (operators.py:546-588), operator defaults GREEDY / NO_OVERLAPS_ALLOWED / Z / 10
  3. ComputeBuildStepsOperator.execute with no face selected -> operators_backend.compute_build_step_numbers
  4. PolyZamboniExportSVGOperator.execute itself (unbound call) on a stand-in `self` whose
     general/line/texture settings are real instances of the add-on's PropertyGroups (all defaults),
     with only the settings in CHANGED modified.  Add-on files are not modified.
"""
import sys, os, io as _io, json, time, glob, contextlib, types
import bpy, bmesh
import gpu
gpu.init()                       # headless OpenGL (llvmpipe) needed: shaders.py compiles shaders at import
import numpy as np

addon_parent, out_root = sys.argv[1], sys.argv[2]
sys.path.insert(0, addon_parent)
import PolyZamboni
PolyZamboni.register()
from PolyZamboni.polyzamboni import operators as O, operators_backend as OB, io as pzio, geometry, printprepper
from PolyZamboni.polyzamboni.papermodel import PaperModel
from PolyZamboni.polyzamboni.autozamboni import greedy_auto_cuts
from PolyZamboni.polyzamboni.properties import GeneralExportSettings, LineExportSettings, TextureExportSettings
from PolyZamboni.polyzamboni import utils as pzutils

# real PropertyGroup instances carrying the add-on defaults
bpy.types.Scene.rz_gs = bpy.props.PointerProperty(type=GeneralExportSettings)
bpy.types.Scene.rz_ls = bpy.props.PointerProperty(type=LineExportSettings)
bpy.types.Scene.rz_ts = bpy.props.PointerProperty(type=TextureExportSettings)

MODELS = "/root/rir2101-flatpack/research/models"
CASES = ["chair", "table", "sofa_curved"]
SCALES = {"1-10": 1.0, "1-20": 0.5}      # paper mm per model mm (model file is already mm at 1:10)
AUTO = dict(quality_level="NO_OVERLAPS_ALLOWED", target_loop_axis="Z", max_faces_per_component=10)  # operator defaults
GLUE_FLAP_HEIGHT_MODEL_MM = 5.0          # changed from default 0.15 (Blender units, see settings.md)
ADD_UV_MAP = "--no-uv" not in sys.argv
EDGE_SPLIT_FIX = "--no-split" not in sys.argv
EXTRA_A2 = ("table", "sofa_curved")
CHANGED = dict(paper_size="A3", print_on_inside=False)   # see settings.md

class Tee:
    def __init__(self, *s): self.s = s
    def write(self, x):
        for s in self.s: s.write(x)
    def flush(self):
        for s in self.s: s.flush()

def dump_print_data(ao, sizing):
    """Sidecar for verification only (adapter does not use it): fold convexity + 3D ground truth."""
    mesh = ao.data
    comps = printprepper.create_print_data_for_all_components(ao, printprepper.compute_scaling_factor_for_target_model_height(mesh, 100 * sizing * pzutils.compute_mesh_height(mesh) / 1000.0))
    def sarea(t):
        (x0, y0), (x1, y1), (x2, y2) = [np.asarray(p) for p in t]
        return 0.5 * ((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))
    # signed area of the unfolded triangles in the add-on's 2D space (y up, before page transform);
    # > 0 for all => faces are laid out as seen from the face-normal side (geometry.py:140-147)
    for c in comps:
        c._signs = sorted(set(int(np.sign(sarea(t.coords))) for t in c.colored_triangles))
    return [{"tri_signed_area_signs": c._signs, "faces": len(c.colored_triangles), "cut_edges": len(c.cut_edges), "fold_edges": [[bool(f.is_convex), float(np.rad2deg(f.fold_angle))] for f in c.fold_edges],
             "flap_folds": [[bool(f.is_convex), float(np.rad2deg(f.fold_angle)), int(f.edge_index)] for f in c.fold_edges_at_flaps], "glue_flaps": len(c.glue_flaps)} for c in comps]

log = {}
for case in CASES:
    rec = {"case": case}
    buf = _io.StringIO()
    with contextlib.redirect_stdout(Tee(sys.stdout, buf)):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.obj_import(filepath=f"{MODELS}/{case}_fold.obj", forward_axis='Y', up_axis='Z')  # 1 OBJ unit = 1 BU
        ao = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = ao
        ao.select_set(True)
        mesh = ao.data
        # MANUAL STEP (mesh prep): the OBJs have no 'vt'; with no UV layer the exporter crashes at
        # printprepper.py:330/47 (TypeError: 'NoneType' object is not iterable). Add one empty UV map.
        if ADD_UV_MAP and len(mesh.uv_layers) == 0:
            mesh.uv_layers.new(name="UVMap")
        t0 = time.perf_counter()
        # --- 1. InitializeCuttingOperator.invoke checks (same expressions as operators.py:58-66,71,78) ---
        bm = bmesh.new(); bm.from_mesh(mesh)
        checks = {
            "manifold": bool(np.all([e.is_manifold or e.is_boundary for e in bm.edges] + [v.is_manifold for v in bm.verts])),
            "normals_ok": bool(np.all([e.is_contiguous or e.is_boundary for e in bm.edges])),
            "multi_touching_faces": len(OB.get_indices_of_multi_touching_faces(bm)),
            "non_triangulatable_faces": len(OB.get_indices_of_not_triangulatable_faces(bm)),
            "max_planarity_score": float(max(geometry.compute_planarity_score([np.array(v.co, dtype=np.float64) for v in f.verts]) for f in bm.faces)),
        }
        rec["edges_total"] = len(bm.edges); rec["edges_interior"] = sum(1 for e in bm.edges if not e.is_boundary)
        bm.free()
        rec["init_checks"] = checks
        refused = not checks["manifold"] or not checks["normals_ok"] or checks["multi_touching_faces"] or checks["non_triangulatable_faces"]
        rec["refused_by_init_check"] = bool(refused)
        if refused:
            # exact UI text the add-on would show (operators.py:102-109)
            msgs = []
            if not checks["manifold"]: msgs.append("The selected mesh is not manifold!")
            if not checks["normals_ok"]: msgs.append('Bad normals! Try "Recalculate Outside" (Shift-N)')
            if checks["multi_touching_faces"]: msgs.append("Some faces touch at more than one edge!")
            if checks["non_triangulatable_faces"]: msgs.append("Some faces can't be triangulated by PolyZamboni!")
            rec["init_refusal_dialog"] = "Something went wrong D: / " + " / ".join(msgs)
            if not EDGE_SPLIT_FIX or checks["multi_touching_faces"] or checks["non_triangulatable_faces"] or not checks["manifold"]:
                log[case] = rec; continue
            # MANUAL STEP (documented rule): Edge Split every interior edge whose two faces have inconsistent
            # winding (is_contiguous False). Geometry and every face normal (= printed side) are unchanged;
            # the edge becomes a boundary, i.e. a plain cut without glue flap. NOT "Recalculate Outside",
            # which would flip a panel and thus its printed side.
            bm = bmesh.new(); bm.from_mesh(mesh)
            bad = [e for e in bm.edges if not e.is_boundary and not e.is_contiguous]
            rec["manual_edge_split"] = [[list(map(lambda c: round(c, 3), v.co)) for v in e.verts] for e in bad]
            bmesh.ops.split_edges(bm, edges=bad)
            bm.to_mesh(mesh); bm.free(); mesh.update()
            bm = bmesh.new(); bm.from_mesh(mesh)
            rec["init_checks_after_split"] = {"normals_ok": bool(np.all([e.is_contiguous or e.is_boundary for e in bm.edges])),
                                              "manifold": bool(np.all([e.is_manifold or e.is_boundary for e in bm.edges] + [v.is_manifold for v in bm.verts]))}
            bm.free()
        # glue flap height is a mesh property read at PaperModel creation -> set before initialization
        mesh.polyzamboni_general_mesh_props.glue_flap_height = GLUE_FLAP_HEIGHT_MODEL_MM
        OB.initialize_paper_model(mesh)                             # operators.py:126
        # --- 2. AutoCutsOperator (operators.py:546-588) ---
        pm = PaperModel.from_existing(mesh)
        for _ in greedy_auto_cuts(pm, AUTO["quality_level"], AUTO["target_loop_axis"], AUTO["max_faces_per_component"]):
            pass
        pm.close()
        # --- 3. ComputeBuildStepsOperator, nothing selected ---
        OB.compute_build_step_numbers(mesh, [])
        t_cut = time.perf_counter() - t0
        comps = pzio.read_connected_component_sets(mesh)
        rec["components"] = len(comps)
        rec["component_faces"] = [sorted(int(i) for i in s) for s in comps.values()]
        rec["cyclic_components"] = sorted(pzio.read_components_with_cycles_set(mesh) or [])
        rec["overlapping_components"] = sorted(pzio.read_components_with_overlaps(mesh) or [])
        coll = pzio.read_glue_flap_collision_dict(mesh) if hasattr(pzio, "read_glue_flap_collision_dict") else None
        rec["glue_flap_collisions"] = {str(k): {str(e): sorted(list(v)) for e, v in d.items()} for k, d in (coll or {}).items()}
        ec = pzio.read_edge_constraints_dict(mesh)
        rec["edge_constraints"] = {str(k): v for k, v in sorted(ec.items())}
        rec["build_steps"] = {str(k): v for k, v in pzio.read_build_step_numbers(mesh).items()}
        rec["seconds_init_autocut_buildsteps"] = round(t_cut, 4)
        rec["exports"] = {}
        sce = bpy.context.scene
        out_dir = os.path.join(out_root, case); os.makedirs(out_dir, exist_ok=True)
        runs = [(t, z, "A3") for t, z in SCALES.items()]
        if case in EXTRA_A2:
            runs.append(("1-10_A2", 1.0, "A2"))   # EXTRA, non-default page: only to see if a complete 1:10 net exists
        for tag, sizing, paper in runs:
            for old in glob.glob(os.path.join(out_dir, f"raw_{tag}_page*.svg")):
                os.remove(old)
            gs, ls, ts = sce.rz_gs, sce.rz_ls, sce.rz_ts
            for k, v in CHANGED.items():
                setattr(gs, k, v)
            gs.paper_size = paper
            # sizing (operator draw func, operators_backend.py:196-200): SCALE mode, target height = scale * mesh height.
            # scaling factor = cm(target_height)/mesh_height = 100*target/height (BU->cm); mesh BU are mm at 1:10
            # -> paper cm per BU = 0.1*sizing  ->  target_model_height = 0.001*sizing*mesh_height
            h = pzutils.compute_mesh_height(mesh)
            gs.sizing_scale = 0.001 * sizing
            gs.target_model_height = gs.sizing_scale * h
            fake = types.SimpleNamespace(
                properties=types.SimpleNamespace(general_settings=gs, line_settings=ls, texture_settings=ts),
                general_settings=gs, line_settings=ls, texture_settings=ts,
                user_defined_page_layout_exists=False,          # invoke(): no page layout was ever created
                filepath=os.path.join(out_dir, f"raw_{tag}.svg"))
            t1 = time.perf_counter()
            res = O.PolyZamboniExportSVGOperator.execute(fake, bpy.context)
            dt = time.perf_counter() - t1
            files = sorted(glob.glob(os.path.join(out_dir, f"raw_{tag}_page*.svg")))
            rec["exports"][tag] = {"result": sorted(res), "seconds_export": round(dt, 4), "pages": len(files),
                                   "files": [os.path.basename(f) for f in files],
                                   "paper_size": gs.paper_size, "target_model_height_BU": gs.target_model_height, "sizing_scale": gs.sizing_scale,
                                   "stdout_tail": [l for l in buf.getvalue().splitlines()[-4:] if "POLYZAMBONI" in l]}
        rec["print_data_debug"] = dump_print_data(ao, 1.0)
        rec["settings_used"] = {
            "general": {p.identifier: (list(getattr(sce.rz_gs, p.identifier)) if p.type == 'FLOAT' and getattr(p, "array_length", 0) else getattr(sce.rz_gs, p.identifier)) for p in sce.rz_gs.bl_rna.properties if p.identifier not in ("rna_type", "name")},
            "line": {p.identifier: (list(getattr(sce.rz_ls, p.identifier)) if p.type == 'FLOAT' and getattr(p, "array_length", 0) else getattr(sce.rz_ls, p.identifier)) for p in sce.rz_ls.bl_rna.properties if p.identifier not in ("rna_type", "name")},
            "texture": {p.identifier: (list(getattr(sce.rz_ts, p.identifier)) if p.type == 'FLOAT' and getattr(p, "array_length", 0) else getattr(sce.rz_ts, p.identifier)) for p in sce.rz_ts.bl_rna.properties if p.identifier not in ("rna_type", "name")},
            "mesh": {k: getattr(mesh.polyzamboni_general_mesh_props, k) for k in ("glue_flap_height", "glue_flap_angle", "prefer_alternating_flaps", "smart_trim_glue_flaps")},
        }
    rec["stdout"] = [l for l in buf.getvalue().splitlines() if "POLYZAMBONI" in l.upper() or "error" in l.lower() or "warning" in l.lower()]
    log[case] = rec

with open(os.path.join(out_root, "run_log.json"), "w") as f:
    json.dump(log, f, indent=1, default=str)
print("done")
