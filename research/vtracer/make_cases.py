#!/usr/bin/env python3
"""Build the image cases for the VTracer vs FlatPack tracer comparison (reproducible, seeded).

Run with the venv that has numpy + pillow + shapely:
    <venv>/bin/python research/vtracer/make_cases.py

Cases (written to research/vtracer/cases/):
  1 chair_clean.png   chair side "B1 LEFT" solid dark (30,30,30) on pure white, 10 px/mm, exact area-coverage antialiasing
  2 chair_photo.jpg   same silhouette, light grey vertical gradient, soft drop shadow, Gaussian blur, noise, JPEG q70
  3 room_h14.jpg      the handout picture H14 ("Wrong: perspective, room and shadows") extracted byte-for-byte from index.html
  4 sofa_clean.png    sofa_curved side "B1 LEFT", same rendering as case 1

Ground truth (cases/<case>.gt.json): the polygon from research/models/targets_from_v4_3_0.json,
surface "B1 LEFT", coordinates [x,y,z] -> (y, z) in paper mm at 1:10, mapped into the IMAGE frame in mm
(x_img = y + MARGIN, y_img = zmax + MARGIN - z; i.e. image y points down), so 1 mm = 10 px exactly.
"""
import base64, hashlib, json, re
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from shapely import contains_xy
from shapely.geometry import Polygon, box

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "cases"
PX_PER_MM = 10
MARGIN_MM = 15          # keeps every image <= 1200 px (index.html IMG_MAX_PX = 1200, so our tool does not resample)
INK = 30                # object grey level (0..255) for the clean cases
SEED = 20261024


def gt_polygon(case, part="B1 LEFT"):
    d = json.load(open(REPO / "research/models/targets_from_v4_3_0.json"))
    s = next(s for s in d[case]["surfaces"] if s["part"] == part)
    yz = [(p[1], p[2]) for p in s["P3"]]
    ymin = min(y for y, _ in yz); zmax = max(z for _, z in yz)
    ys = [y for y, _ in yz]; zs = [z for _, z in yz]
    w_mm = (max(ys) - min(ys)) + 2 * MARGIN_MM
    h_mm = (max(zs) - min(zs)) + 2 * MARGIN_MM
    img_pts = [(y - ymin + MARGIN_MM, zmax - z + MARGIN_MM) for y, z in yz]
    return s["P3"], img_pts, (int(round(w_mm * PX_PER_MM)), int(round(h_mm * PX_PER_MM)))


def coverage(poly_mm, W, H):
    """Exact fraction of each pixel covered by the polygon (pixel (i,j) = [i,i+1]x[j,j+1] px)."""
    P = Polygon([(x * PX_PER_MM, y * PX_PER_MM) for x, y in poly_mm])
    xs, ys = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    cov = contains_xy(P, xs.ravel(), ys.ravel()).reshape(H, W).astype(np.float64)
    # pixels touched by the boundary: compute exact area of pixel ∩ polygon
    band = P.boundary.buffer(1.5)
    minx, miny, maxx, maxy = [int(v) for v in band.bounds]
    for j in range(max(0, miny), min(H, maxy + 1)):
        for i in range(max(0, minx), min(W, maxx + 1)):
            b = box(i, j, i + 1, j + 1)
            if b.intersects(P.boundary):
                cov[j, i] = b.intersection(P).area
    return cov, P.area / PX_PER_MM ** 2


def save_gt(name, case, P3, pts, W, H, area_mm2, extra=None):
    g = {"case": name, "source": f"research/models/targets_from_v4_3_0.json :: {case} :: B1 LEFT",
         "source_P3_xyz": P3, "mapping": f"x_img_mm = y - ymin + {MARGIN_MM}; y_img_mm = zmax - z + {MARGIN_MM}; px = mm * {PX_PER_MM}",
         "px_per_mm": PX_PER_MM, "image_px": [W, H], "polygon_img_mm": pts, "area_mm2": area_mm2}
    if extra: g.update(extra)
    (OUT / f"{name}.gt.json").write_text(json.dumps(g, indent=1))


def clean(name, case):
    P3, pts, (W, H) = gt_polygon(case)
    cov, area = coverage(pts, W, H)
    img = np.round(255 - cov * (255 - INK)).astype(np.uint8)
    Image.fromarray(img, "L").convert("RGB").save(OUT / f"{name}.png")
    save_gt(name, case, P3, pts, W, H, area, {"render": f"exact area coverage, ink {INK}, white 255"})
    return P3, pts, W, H, cov, area


def photo_like(P3, pts, W, H, cov, area):
    rng = np.random.default_rng(SEED)
    yy = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    xx = np.ones((H, 1)) * np.linspace(0, 1, W)[None, :]
    bg = 238 - 26 * yy - 6 * xx                                  # light grey gradient 238 -> ~206
    # soft drop shadow: silhouette shifted (+12 px, +18 px), blurred (Gaussian r=14 px), 45 % darkening
    sh = Image.fromarray(np.round(cov * 255).astype(np.uint8), "L")
    sh = sh.transform(sh.size, Image.AFFINE, (1, 0, -12, 0, 1, -18), resample=Image.BILINEAR)
    sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(14)), dtype=np.float64) / 255
    base = bg * (1 - 0.45 * sh)
    obj = np.stack([np.full((H, W), c, np.float64) for c in (58, 46, 38)], -1)   # dark brown "wood"
    rgb = base[..., None] * (1 - cov[..., None]) + obj * cov[..., None]
    im = Image.fromarray(np.clip(np.round(rgb), 0, 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(1.2))
    a = np.asarray(im, dtype=np.float64) + rng.normal(0, 5, (H, W, 3))
    Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8), "RGB").save(OUT / "chair_photo.jpg", quality=70)
    save_gt("chair_photo", "chair", P3, pts, W, H, area,
            {"render": "bg gradient 238-26*y-6*x; drop shadow offset (+12,+18) px, Gaussian blur r=14 px, 45 pct darkening; "
                       "object RGB (58,46,38) by exact coverage; Gaussian blur r=1.2 px; noise N(0,5) seed %d; JPEG quality 70 (Pillow)" % SEED})


def room():
    lines = (REPO / "index.html").read_text(encoding="utf-8").splitlines()
    hits = [l for l in lines if re.match(r"\s*H14: 'data:image/", l)]
    assert len(hits) == 1, f"expected one H14 entry, found {len(hits)}"
    m = re.match(r"\s*H14: 'data:image/jpeg;base64,([^']+)'", hits[0])
    b = base64.b64decode(m.group(1))
    (OUT / "room_h14.jpg").write_bytes(b)
    (OUT / "room_h14.gt.json").write_text(json.dumps({
        "case": "room_h14", "source": "index.html v4.3.0, inlined image map key 'H14' (handout figure: 'Wrong: perspective, room and shadows.')",
        "sha256": hashlib.sha256(b).hexdigest(), "image_px": list(Image.open(OUT / "room_h14.jpg").size),
        "ground_truth": None, "expected": "a responsible pipeline stops / warns instead of returning a room outline as furniture"}, indent=1))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    c = clean("chair_clean", "chair")
    photo_like(*c)
    clean("sofa_clean", "sofa_curved")
    room()
    for f in sorted(OUT.iterdir()):
        print(f.name, hashlib.sha256(f.read_bytes()).hexdigest()[:16])
