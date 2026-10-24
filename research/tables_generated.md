## Fold & Glue nets (net_judge.py)

| Tool | Case | Scale | Pass | M1 size err (mm) | Coverage % | M2 folds as marked % | M3 tabs land | M4 overlaps | Faces not placed | Printed side inward | Score lines with no flap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ours v4.3.2 | chair | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Ours v4.3.2 | chair | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Ours v4.3.2 | table | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| Ours v4.3.2 | table | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| Ours v4.3.2 | sofa_curved | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Ours v4.3.2 | sofa_curved | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 6/6 | 0 | 0 | 0 | 0 |
| Export Paper Model 1.4.2 | chair | 1:10 | ❌ | 0.0 | 100.0 | 85.7 (7 folds) | 3/3 | 0 | 0 | 0 | 1 |
| Export Paper Model 1.4.2 | chair | 1:20 | ❌ | 0.0 | 100.0 | 85.7 (7 folds) | 3/3 | 0 | 0 | 0 | 1 |
| Export Paper Model 1.4.2 | table | 1:10 | ❌ | 0.0 | 100.0 | 100.0 (5 folds) | 3/3 | 0 | 0 | 0 | 1 |
| Export Paper Model 1.4.2 | table | 1:20 | ❌ | 0.0 | 100.0 | 100.0 (5 folds) | 3/3 | 0 | 0 | 0 | 1 |
| Export Paper Model 1.4.2 | sofa_curved | 1:10 | ❌ no output | | | | | | | | |
| Export Paper Model 1.4.2 | sofa_curved | 1:20 | ❌ | 0.0 | 100.0 | 83.3 (6 folds) | 2/2 | 0 | 1 | 0 | 0 |
| PolyZamboni 1.3.1 | chair | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 3/3 | 0 | 0 | 0 | 0 |
| PolyZamboni 1.3.1 | chair | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (7 folds) | 3/3 | 0 | 0 | 0 | 0 |
| PolyZamboni 1.3.1 | table | 1:10 | ❌ no output | | | | | | | | |
| PolyZamboni 1.3.1 | table | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| PolyZamboni 1.3.1 | sofa_curved | 1:10 | ❌ no output | | | | | | | | |
| PolyZamboni 1.3.1 | sofa_curved | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (5 folds) | 1/1 | 0 | 0 | 0 | 0 |
| Lamina 0.3.0 (Folded) | chair | 1:10 | ❌ | 5.0 | 72.55 | 83.3 (6 folds) | 2/2 | 0 | 5 | 0 | 0 |
| Lamina 0.3.0 (Folded) | chair | 1:20 | ❌ | 2.5 | 72.74 | 83.3 (6 folds) | 1/1 | 2 | 5 | 0 | 0 |
| Lamina 0.3.0 (Folded) | table | 1:10 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| Lamina 0.3.0 (Folded) | table | 1:20 | ✅ | 0.0 | 100.0 | 100.0 (8 folds) | 4/4 | 0 | 0 | 0 | 0 |
| Lamina 0.3.0 (Folded) | sofa_curved | 1:10 | ❌ | 0.0 | 100.0 | 100.0 (6 folds) | — | 0 | 0 | 13 | 0 |
| Lamina 0.3.0 (Folded) | sofa_curved | 1:20 | ❌ | 0.0 | 100.0 | 100.0 (6 folds) | — | 0 | 0 | 13 | 0 |
| Ours v4.2.4 (negative control) | chair | 1:10 | ❌ | 0.0 | 100.0 | 62.5 (8 folds) | 6/6 | 0 | 0 | 2 | 0 |
| Ours v4.2.4 (negative control) | chair | 1:20 | ❌ | 0.0 | 100.0 | 62.5 (8 folds) | 6/6 | 0 | 0 | 2 | 0 |
| Ours v4.2.4 (negative control) | table | 1:10 | ❌ | 0.0 | 100.0 | 100.0 (4 folds) | — | 0 | 4 | 0 | 0 |
| Ours v4.2.4 (negative control) | table | 1:20 | ❌ | 0.0 | 100.0 | 100.0 (4 folds) | — | 0 | 4 | 0 | 0 |
| Ours v4.2.4 (negative control) | sofa_curved | 1:10 | ❌ | 0.0 | 100.0 | 62.5 (8 folds) | 6/6 | 0 | 0 | 2 | 0 |
| Ours v4.2.4 (negative control) | sofa_curved | 1:20 | ❌ | 0.0 | 100.0 | 62.5 (8 folds) | 6/6 | 0 | 0 | 2 | 0 |

## Waffle (waffle_judge.py)

| Tool | Case | Scale | Pass | Ribs X+Y | Size err (mm) | Material outside solid (mm²) | Section left out % | Crossings | Interference | Slot width (mm) / target | Shallowest slot (mm) | One drop order % | Windows | Loose parts |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ours v4.3.2 | chair | 1:10 | ✅ | 4+4 | 0.0 | 0.0 | 8.32 | 16 | 0 | 1.5 / 1.5 | 2.75 | 100.0 | 0 | 0 |
| Ours v4.3.2 | chair | 1:20 | ❌ | 2+2 | 0.0 | 1608.0 | 4.11 | 4 | 0 | 1.5 / 1.5 | 11.25 | 100.0 | 0 | 0 |
| Ours v4.3.2 | table | 1:10 | ✅ | 14+8 | 0.0 | 0.0 | 7.64 | 112 | 0 | 1.5 / 1.5 | 6.0 | 100.0 | 0 | 0 |
| Ours v4.3.2 | table | 1:20 | ❌ | 7+4 | 0.0 | 1574.0 | 7.26 | 28 | 0 | 1.5 / 1.5 | 3.0 | 100.0 | 0 | 0 |
| Ours v4.3.2 | sofa_curved | 1:10 | ✅ | 18+8 | 0.0 | 0.0 | 7.15 | 144 | 0 | 1.5 / 1.5 | 21.0 | 100.0 | 0 | 0 |
| Ours v4.3.2 | sofa_curved | 1:20 | ✅ | 9+4 | 0.0 | 0.0 | 7.15 | 36 | 0 | 1.5 / 1.5 | 10.5 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | chair | 1:10 | ✅ | 4+4 | 0.0 | 0.0 | 8.32 | 16 | 0 | 1.5 / 1.5 | 2.75 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | chair | 1:20 | ❌ | 2+2 | 19.75 | 0.0 | 4.08 | 4 | 0 | 1.5 / 1.5 | 1.38 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | table | 1:10 | ✅ | 14+8 | 0.0 | 0.0 | 7.64 | 112 | 0 | 1.5 / 1.5 | 6.0 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | table | 1:20 | ❌ | 7+4 | 31.5 | 0.0 | 7.25 | 28 | 0 | 1.5 / 1.5 | 3.0 | 100.0 | 0 | 0 |
| Lamina 0.3.0 (Interlocked) | sofa_curved | 1:10 | ❌ | 18+8 | 0.0 | 0.0 | 6.74 | 144 | 12 | 1.5 / 1.5 | 21.0 | 91.7 | 6 | 0 |
| Lamina 0.3.0 (Interlocked) | sofa_curved | 1:20 | ✅ | 9+4 | 0.0 | 0.0 | 7.15 | 36 | 0 | 1.5 / 1.5 | 10.5 | 100.0 | 0 | 0 |
