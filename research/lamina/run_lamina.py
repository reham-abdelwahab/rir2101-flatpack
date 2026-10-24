"""Run Lamina (core API, no web server) on the shared research meshes and keep its raw exports.

    . <venv>/bin/activate && python -I research/lamina/run_lamina.py [case ...]

Per case and scale it writes, under research/lamina/<case>/raw/<technique>_<scale>/:
  plan.json            Lamina's own plan file (core.plan.build(..., out=...)) - its internal model, before and after nesting
  *.svg                Lamina's sheet export (core.export.export, fmt svg, labels on, border on) + assembly-key.txt
  run.json             settings passed, wall-clock seconds, and every note / error / warning Lamina reported (verbatim)
Nothing here normalises anything: adapt.py does that from these files.
"""
from __future__ import annotations
import json, pathlib, subprocess, sys, time

import core                                  # Lamina, installed editable from the pinned clone
from core.plan import build
from core.export import export

HERE = pathlib.Path(__file__).resolve().parent
MODELS = HERE.parent / "models"
CASES = ["chair", "table", "sofa_curved"]
SCALES = {"1-10": 1.0, "1-20": 0.5}

# Every setting changed from Lamina's defaults (see settings.md for why)
FOLD = {"joint": "tab",              # Lamina's default joint is "laced"; the brief asks for glue tabs
        "thickness": 0.5,            # 0.5 mm Bristol (default 1.5)
        "material": "card",          # names the stock; turns on Lamina's fold-thickness check (card folds up to 1.5 mm)
        "sheet": [297, 420]}         # A3 portrait (default 600x400)
WAFFLE = {"distribution": "distance",  # default "count" (nx=5, ny=4); "distance" = one slice every `spacing`
          "spacing": 10,             # mm (default 30)
          "thickness": 1.5,          # = default, stated explicitly
          "kerf": 0.0, "compensate": False, "slot_offset": 0.0,   # = defaults, stated explicitly
          "up": "z",                 # = default: families X (planes x = const) and Y (planes y = const)
          "sheet": [297, 420]}


def lamina_commit():
    src = pathlib.Path(core.__file__).resolve().parent.parent
    try:
        return subprocess.run(["git", "-C", str(src), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(), str(src)
    except Exception as e:                    # noqa: BLE001
        return f"unknown ({e})", str(src)


def messages(plan):
    out = {"counts": plan["counts"], "sheets": plan["sheets"], "sheet_usage": plan["sheet_usage"], "coverage": plan["coverage"],
           "notes": plan["notes"], "errors": plan["errors"], "fixes": plan["fixes"], "slices": []}
    for sl in plan["slices"] + plan["dropped"]:
        if sl.get("errors") or sl.get("warnings"):
            out["slices"].append({"label": sl["label"], "errors": sl.get("errors", []), "warnings": sl.get("warnings", [])})
    return out


def cli_lines(plan):
    """The same lines Lamina's own CLI (core.plan.main) prints after a build."""
    c = plan["counts"]
    lines = [f"{plan['mode']}: {c['slices']} slices, {c['parts']} parts, {plan['sheets']} sheet(s) ({plan['sheet_usage']:.0%} used), {c['errors']} errors, {c['warnings']} warnings"]
    lines += [f"  note  {n}" for n in plan["notes"]] + [f"  ERROR {e}" for e in plan["errors"]]
    for sl in plan["slices"] + plan["dropped"]:
        lines += [f"  ERROR {sl['label']}: {e}" for e in sl.get("errors", [])]
        lines += [f"  warn  {sl['label']}: {w}" for w in sl.get("warnings", [])]
    return lines


import numpy as np
from core.modes.folded import Folded
from core.unfold import refold_error

_orig_build = Folded.build


def _keep_build(self, ctx):
    """Read-only instrumentation: keep the slices Folded.build returns (Lamina drops them after the plan is written),
    so fold_meta.json can say which score line is which mesh edge. Nothing returned by build is changed."""
    out = _orig_build(self, ctx)
    self._kept = out
    return out


Folded.build = _keep_build


def fold_meta(mode):
    """Per panel, from Lamina's own internal objects: the panel-only area (no tabs), and every score line in the
    panel's own frame (= plan.json `kerfed_lines`, kerf 0) with the mesh dihedral angle and convexity behind it."""
    m = mode.mesh; ang = np.degrees(m.face_adjacency_angles); cv = m.face_adjacency_convex
    panels = []
    for sl in mode._kept:
        if sl.group != "F":
            continue
        pn = sl.pn; lines = []
        for i, (style, ln) in enumerate(sl.lines):
            if i < len(pn.folds):
                k = pn.folds[i]
                lines.append({"style": style, "kind": "fold", "dihedral_deg": round(float(ang[k]), 4), "convex": bool(cv[k]),
                              "coords": np.round(np.asarray(ln.coords), 4).tolist()})
            else:
                lines.append({"style": style, "kind": "tab_hinge", "coords": np.round(np.asarray(ln.coords), 4).tolist()})
        panels.append({"label": sl.label, "faces": len(pn.faces), "panel_area_mm2": float(pn.union.area), "lines": lines})
    return {"note": "instrumentation of Lamina internals (core.modes.folded.Folded.build); not a Lamina output",
            "mesh_faces": int(len(m.faces)), "mesh_area_mm2": float(m.area),
            "refold_error_mm": float(refold_error(m, mode.frames, mode.local, [s.pn for s in mode._kept if s.group == "F"])),
            "panels": panels}


def run(case, tech, scale_key):
    model = MODELS / (f"{case}_fold.stl" if tech == "fold" else f"{case}_waffle_solid.stl")
    params = dict(FOLD if tech == "fold" else WAFFLE)
    if SCALES[scale_key] != 1.0:
        params["scale"] = SCALES[scale_key]
    params["project"] = f"{case}_{tech}_{scale_key}"     # file names / sheet title only
    out = HERE / case / "raw" / f"{tech}_{scale_key}"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*"):
        f.unlink()
    t0 = time.perf_counter()
    plan = build(str(model), "folded" if tech == "fold" else "interlocked", params, out=out / "plan")
    t1 = time.perf_counter()
    files = export(plan, out, fmts=("svg",), labels=True, border=True, key=True)
    t2 = time.perf_counter()
    if tech == "fold":
        from core.plan import MODES
        (out / "fold_meta.json").write_text(json.dumps(fold_meta(MODES["folded"]), indent=1), encoding="utf-8")
    commit, src = lamina_commit()
    log = {"tool": "Lamina (lamina3d)", "commit": commit, "source": src, "model": str(model), "mode": plan["mode"],
           "params_set": params, "seconds_build": round(t1 - t0, 3), "seconds_export": round(t2 - t1, 3),
           "seconds_total": round(t2 - t0, 3), "files": [f.name for f in files], "cli_output": cli_lines(plan), **messages(plan)}
    (out / "run.json").write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n".join([f"== {case} {tech} {scale_key}  ({log['seconds_total']} s)"] + log["cli_output"]))
    return log


if __name__ == "__main__":
    for case in sys.argv[1:] or CASES:
        for tech in ("fold", "waffle"):
            for sk in SCALES:
                run(case, tech, sk)
