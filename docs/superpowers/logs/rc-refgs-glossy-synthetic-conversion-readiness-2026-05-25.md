# RC-RefGS Glossy Synthetic Conversion Readiness

Date: 2026-05-25 20:43:09 CST

Scope: FD-P0 docs/status-only conversion-readiness audit. No training, metrics, ablations, multi-seed runs, geometry metrics, training-code edits, metric-code edits, manuscript prose edits, scientific claim upgrades, or dataset conversion were executed.

## Result

- Glossy Synthetic raw root is now discovered at `/data/liuly/dataset/3DGS/GlossySynthetic`.
- Scene list: `angel`, `bell`, `cat`, `horse`, `luyu`, `potion`, `tbell`, `teapot`.
- Each scene has 128 RGB PNGs, 128 depth PNGs, 128 `*-camera.pkl` files, and `eval_pts.ply`.
- No converted Blender-style outputs were found yet:
  - no `transforms_train.json`
  - no `transforms_test.json`
  - no `<scene>_blender` or `rgb/` converted scene directories

## Reader Contract

Ref-GS only routes a scene through the Blender reader when `transforms_train.json` exists in the scene root. The current raw NeRO-style folders therefore are not claim-bearing launch-ready for RC-RefGS training.

## Conversion Tooling

Primary helper:

```bash
python /home/liuly/Surface_Reconstruction/Glossy/GS-2M/scripts/preprocess/nero2blender.py --path /data/liuly/dataset/3DGS/GlossySynthetic --scene <scene>
```

The helper CLI imports and reports `--path` / `--scene` via `--help`. Alternate copies also exist in `GS-2M_new` and `ref-gaussian`.

## Conversion Checklist

1. Run `nero2blender.py` once for each scene: `angel`, `bell`, `cat`, `horse`, `luyu`, `potion`, `tbell`, `teapot`.
2. Verify every converted scene directory contains `transforms_train.json`, `transforms_test.json`, and non-empty `rgb/*.png`.
3. Update the required full-dataset manifest to point claim-bearing runtime at converted Glossy Synthetic paths, not the raw NeRO scene roots.
4. Generate a full-dataset dry-run expansion only after Shiny Blender Synthetic, Shiny Blender Real, and converted Glossy Synthetic are all manifest-locked.

## Gate Status

- Gate A, roots explicit: pass for raw Glossy Synthetic root.
- Gate B, scene discovery complete and non-empty: pass for raw scene discovery.
- Gate C, Glossy Synthetic conversion validated: blocked.
- Claim-bearing launch allowed: no.

## Decision

CONDITIONAL GO for continued FD-P0 conversion validation or FD-P1 manifest dry-run support after converted outputs exist.

NO-GO for claim-bearing full-dataset training, complete-dataset claims, manuscript/scientific claim upgrades, broad rendering/material/geometry/external-superiority/causal/full-ablation/multi-seed claims, or SWITCH MODEL routing for claim-bearing P5 audit.
