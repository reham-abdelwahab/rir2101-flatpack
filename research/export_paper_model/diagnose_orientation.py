"""Diagnostic (not part of the export): wraps the add-on's Svg.write at runtime to dump, per island and face,
the face's 3D vertices, its SVG-page coordinates, uvface.flipped and island.is_inside_out, and for every
drawn fold the add-on's class (convex/concave) plus an independent 3D ground truth of the fold direction
as seen by the viewer of the raw SVG. Writes orientation_diag.json. Add-on files are not modified.
Usage: python -I diagnose_orientation.py <addon_parent> <out_root>
"""
import sys, os, json
import bpy
addon_parent, out_root = sys.argv[1], sys.argv[2]
sys.path.insert(0, addon_parent)
bpy.context.preferences.addons.new().module = "io_export_paper_model"
import io_export_paper_model as addon
addon.register()
from io_export_paper_model import svg as svgmod

DUMP = {}
orig_write = svgmod.Svg.write
def wrapped_write(self, mesh, filename):
    out = []
    for p, page in enumerate(mesh.pages):
        for island in page.islands:
            isl = {"page": p, "is_inside_out": island.is_inside_out, "faces": [], "folds": []}
            mw = bpy.context.active_object.matrix_world
            for face, uvf in island.faces.items():
                pts = []
                for loop in face.loops:
                    s = self.format_vertex(uvf.vertices[loop].co + island.pos).split()
                    pts.append([float(s[0]), float(s[1])])
                a = sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))/2
                isl["faces"].append({"index": face.index, "flipped": uvf.flipped,
                    "co3d": [list(mw @ l.vert.co) for l in face.loops], "normal": list((mw.to_3x3() @ face.normal).normalized()),
                    "svg": pts, "shoelace_svg_ydown": a,
                    # visual CCW in y-down coords => negative shoelace => viewer sees the normal (front) side
                    "viewer_sees_normal_side": a < 0})
            seen = set()
            for loop, uvedge in island.edges.items():
                edge = mesh.edges[loop.edge]
                if edge.is_cut(uvedge.uvface.face) and not uvedge.sticker:
                    continue
                key = frozenset((uvedge.va, uvedge.vb))
                if key in seen or abs(edge.angle) <= self.angle_epsilon:
                    continue
                seen.add(key)
                cls = "convex" if edge.is_convex() else "concave"
                if island.is_inside_out:
                    cls = {"convex": "concave", "concave": "convex"}[cls]
                fA = uvedge.uvface.face
                others = [l.face for l in loop.edge.link_loops if l.face is not fA]
                fB = others[0]
                mw3 = bpy.context.active_object.matrix_world
                nA = (mw3.to_3x3() @ fA.normal).normalized()
                # viewer-side normal of face A: sign from its svg orientation
                fa_rec = next(f for f in isl["faces"] if f["index"] == fA.index)
                if not fa_rec["viewer_sees_normal_side"]:
                    nA = -nA
                p = mw3 @ loop.edge.verts[0].co
                cB = mw3 @ fB.calc_center_median()
                d = (cB - p).dot(nA)
                truth = "mountain" if d < 0 else "valley"   # B bends away from viewer-side normal => mountain
                isl["folds"].append({"edge_verts": [list(mw3 @ v.co) for v in loop.edge.verts],
                    "is_tab_line": bool(edge.is_cut(fA)), "addon_class": cls,
                    "truth_seen_from_raw_viewer": truth, "angle": edge.angle,
                    "svg": [self.format_vertex(v.co + island.pos) for v in (uvedge.va, uvedge.vb)]})
            out.append(isl)
    DUMP[filename] = out
    return orig_write(self, mesh, filename)
svgmod.Svg.write = wrapped_write

for case in ["chair", "table", "sofa_curved"]:
    for tag, div in {"1-10": 1000.0, "1-20": 2000.0}.items():
        bpy.ops.wm.read_homefile(use_empty=True)
        bpy.ops.wm.obj_import(filepath=f"/root/rir2101-flatpack/research/models/{case}_fold.obj", forward_axis='Y', up_axis='Z')
        ob = bpy.context.selected_objects[0]; bpy.context.view_layer.objects.active = ob
        bpy.context.scene.paper_model.use_auto_scale = False
        bpy.context.scene.paper_model.scale = div
        tmp = os.path.join(out_root, "_diag_tmp.svg")
        try:
            bpy.ops.mesh.unfold()
            bpy.ops.export_mesh.paper_model(filepath=tmp, scale=div, file_format='SVG', page_size_preset='A3',
                                            output_size_x=0.297, output_size_y=0.420)
        except Exception as e:
            print("DIAG-FAIL", case, tag, e)
        if tmp in DUMP:
            DUMP[f"{case}_{tag}"] = DUMP.pop(tmp)
        for f in os.listdir(out_root):
            if f.startswith("_diag_tmp"):
                os.remove(os.path.join(out_root, f))
with open(os.path.join(out_root, "orientation_diag.json"), "w") as f:
    json.dump(DUMP, f, indent=1)
for k, v in DUMP.items():
    for isl in v:
        print(k, "inside_out", isl["is_inside_out"],
              "faces(idx,flipped,viewer_sees_normal):", [(f["index"], f["flipped"], f["viewer_sees_normal_side"]) for f in isl["faces"]])
        for fo in isl["folds"]:
            print("   ", "TAB " if fo["is_tab_line"] else "FOLD", fo["addon_class"], "truth(raw viewer):", fo["truth_seen_from_raw_viewer"], [[round(c,1) for c in v] for v in fo["edge_verts"]])
