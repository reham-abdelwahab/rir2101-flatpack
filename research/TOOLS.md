# Pinned tools (D1) — results are valid only for these versions

Checked 24 Oct 2026 in the cloud container (Linux, Python 3.13). Licences read from each repository's own LICENSE / manifest.

| Tool | Role | Version / commit | Licence | Runs offline? | How it was run |
|---|---|---|---|---|---|
| **Studio Flat-Pack Maker** (ours) | baseline, all methods | v4.3.1, `index.html` at repo commit `29ce619` | course tool (repo) | yes (single HTML) | headless Chromium 153 through Playwright, calling the page's own functions (`research/ours/`) |
| Export Paper Model | Fold & Glue nets | add-on 1.4.2, commit `d688dcd` (github.com/addam/Export-Paper-Model-from-Blender) | GPL-3.0-or-later | yes (needs Blender) | `bpy` 5.2.3 (Blender as a Python module, PyPI) |
| PolyZamboni | difficult nets | add-on 1.3.1, commit `a6b880e` (github.com/AntonFlorey/PolyZamboni) | GPL-3.0 | yes (needs Blender) | `bpy` 5.2.3 |
| Lamina | Waffle (interlocked) and Folded | 0.3.0, commit `bed1c9a` (github.com/marcelfarres/lamina), "early alpha" by its author | AGPL-3.0-or-later | yes (local Python or browser build) | its Python core in its own venv |
| VTracer | image tracing | PyPI `vtracer` 0.6.15; repo commit `e71343f` (github.com/visioncortex/vtracer) | MIT | yes | Python binding |

## What the licences allow here (integration path, TOOLS_INTEGRATION_PLAN.md section 7)
- **GPL-3.0 / AGPL-3.0 (Export Paper Model, PolyZamboni, Lamina):** their *code* must not be copied into `index.html` unless the tool itself is released under a compatible licence. Their *output* (an SVG net made from our own model) is not covered by their licence, so an approved template can be stored as data (SVG + JSON) with the source credited. AGPL also covers network use of the code: we never host Lamina.
- **MIT (VTracer):** code could be bundled with the licence notice kept. A WebAssembly build exists in its repo; not attempted here.

## Environment
`bpy==5.2.3`, `vtracer==0.6.15`, `trimesh`, `shapely`, `manifold3d`, `mapbox_earcut`, `scipy` in a uv venv; Lamina in its own venv. Network: PyPI and GitHub only. No GPU.
