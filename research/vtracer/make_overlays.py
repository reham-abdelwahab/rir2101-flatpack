#!/usr/bin/env python3
"""Evidence images: each run's traced outline (red) over the case image, ground truth (green, dashed-less thin) where known.
Reads out/<case>__<run>.outline_mm.json written by run_compare.py; writes out/<case>__overlay.png (2x2 grid)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
RUNS = ["vtracer_default_binary", "vtracer_best_effort", "ours_default", "ours_dark_on_light"]
res = json.loads((HERE / "results.json").read_text())
for case, e in res["cases"].items():
    base = Image.open(HERE / e["image"]).convert("RGB")
    W, H = base.size
    gt = json.loads((HERE / "cases" / f"{case}.gt.json").read_text()).get("polygon_img_mm")
    tiles = []
    for run in RUNS:
        im = base.copy(); d = ImageDraw.Draw(im)
        if gt:
            d.line([(x * 10, y * 10) for x, y in gt + gt[:1]], fill=(0, 170, 0), width=2)
        f = OUT / f"{case}__{run}.outline_mm.json"
        if f.exists():
            for path in json.loads(f.read_text())["paths"]:
                for ring in path if path and isinstance(path[0][0], list) else [path]:
                    if len(ring) > 1:
                        d.line([(x * 10, y * 10) for x, y in ring + ring[:1]], fill=(220, 0, 0), width=3)
        d.rectangle([0, 0, W, 34], fill=(255, 255, 255)); d.text((6, 8), f"{case} / {run}", fill=(0, 0, 0))
        tiles.append(im)
    g = Image.new("RGB", (W * 2, H * 2), "white")
    for i, t in enumerate(tiles):
        g.paste(t, ((i % 2) * W, (i // 2) * H))
    g.thumbnail((1600, 1600)); g.save(OUT / f"{case}__overlay.png")
    print("wrote", OUT / f"{case}__overlay.png")
