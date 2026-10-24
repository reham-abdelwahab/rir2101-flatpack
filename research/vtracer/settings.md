# Settings — VTracer vs FlatPack tracer (run 2026-10-24)

## Tools

| | VTracer | FlatPack "From image" auto-trace |
|---|---|---|
| Package / file | PyPI `vtracer==0.6.15`, wheel `cp313-cp313-manylinux_2_17_x86_64` (built with maturin 1.12.6) | `/root/rir2101-flatpack/index.html`, served at `http://localhost:8765/index.html` |
| Version reported | dist-info 0.6.15. **The SVG header comment it writes says "VTracer 0.6.12"**; this is recorded as observed. | `TOOL_VERSION = '4.3.1'` |
| Source / commit | Clone at scratchpad `tools/vtracer`, HEAD `e71343fbcbf469b8a72a255030408a39939162eb` (2026-10-22, master = 1.0.0-alpha.4). The tag `0.6.15` = `fd9cdb08e622f237eb05be553a020ddc9e4c47a1`; its `cmdapp/src/{python,converter,config}.rs` were read for the defaults and the binary rule. The wheel was not rebuilt from source. | Commit `29ce619` ("v4.3.1 student release: mirror B2 RIGHT side profile"), committed by the project at 19:04:44 +0300 during this session. The served file's sha256 `fa1d23d5bbd8ccc424d38ff01f3391194dd358df61a270c48d135bdbf82c1d0d` equals `git show 29ce619:index.html`. The tracer functions `imgAutoTrace` / `imgTraceBoundary` / `imgTraceHoles` / `imgRDP` / `renderTraceGate` are unchanged from v4.3.0 `ba04eee`, whose diff touches only the version constants and the B2 side profile. |
| Licence | MIT (`LICENSE`, © 2024 TSANG, Hao Fung). PyPI metadata: `License-Expression: MIT`. The 1.0 alpha crates on master state "MIT OR Apache-2.0". | The project's own code. |
| Language | Rust (native extension) | JavaScript in the page |

The Python environment was a venv with Python 3.13.17, shapely 2.2.0, numpy 2.5.4 and Pillow 13.0.0. The page was driven by system Playwright 1.63.0 with headless Chromium 153.0.8010.12. The machine has 2 vCPU on Linux 6.18.

## VTracer settings

These are called through `vtracer.convert_raw_image_to_svg(bytes, img_format, **kw)`. Every unspecified option takes the 0.6.15 default: `hierarchical='stacked'`, `mode='spline'`, `filter_speckle=4`, `color_precision=6`, `layer_difference=16`, `corner_threshold=60`, `length_threshold=4.0`, `max_iterations=10`, `splice_threshold=45`, `path_precision=8`. In binary mode the threshold is fixed in code as `R < 128`; it cannot be changed through the 0.6.15 Python API.

| Run | Settings |
|---|---|
| `vtracer_default_binary` | `colormode='binary'` |
| `vtracer_best_effort` | `colormode='binary', mode='polygon', filter_speckle=16` |

The best-effort setting was chosen once, before any metric was seen:
- `polygon` because cut lines are straight.
- Speckle 16 (256 px, which is 2.56 mm² at 10 px/mm) because fragments that small are never furniture.

It was not tuned per case.

## Our tool's settings

All settings are made through the page's own UI elements and functions.

| Run | Settings |
|---|---|
| `ours_default` | HTML defaults: method "Remove background", bg tolerance 70, drop cast shadow on, clean 4, simplify 0.6 mm on paper, fill on, largest only on (dark threshold 140 and invert off are unused) |
| `ours_dark_on_light` | Same, but with method "Dark on light" (threshold 140) |

The project and image scale are both 1:10 (`setScale(10)`, `imgSetScale(10)`).

Calibration is set for the cases with ground truth:
- `p1` and `p2` are set at the piece's known horizontal extent (45 mm chair, 85 mm sofa; 450 / 850 px).
- `imgSetCalibCm` is called with that length in cm at 1:10, which gives exactly 0.1 paper mm per px.
- This is the same value as a student's two clicks on a known dimension.

H14 has no calibration, so the tool used its fallback `210 / W` mm per px for the simplify tolerance.

Images are ≤ 1200 px on their longer side, so `IMG_MAX_PX = 1200` did not resample them.

## Wall-clock

Per-trace times are in `results.json` (`wall_s`, and for ours also `trace_ms_in_page`) and in the results.md table. A whole run of `run_compare.py` took about 4.5 s, including browser start. `make_cases.py` took about 6 s.

## Reproduce

```
V=/tmp/claude-0/-home-claude/a08d6e43-68ac-59f1-b38b-18f3d9cee4ba/scratchpad/rv/bin/python   # any venv with vtracer==0.6.15 shapely numpy pillow
cd /root/rir2101-flatpack
python3 -m http.server 8765 &            # if not already serving
$V research/vtracer/make_cases.py
$V research/vtracer/run_compare.py       # writes out/ and results.json (adds /usr/local/lib/python3.13/site-packages for Playwright)
$V research/vtracer/make_overlays.py     # evidence PNGs in out/
python3 research/vtracer/make_report.py  # results.md (tables + notes.md)
```

## Manual steps

There were none in the measurement. One analyst step is in results.md: the "What was outlined" column for H14 is a visual reading of `out/room_h14__overlay.png`. It is labelled as such in `make_report.py`.
