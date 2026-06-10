# RC-RefGS Geometry Signal Inventory - 2026-06-05

## Executive Summary

Inspected `14` non-Shiny-Real scenes across Shiny Blender Synthetic and Glossy Synthetic converted roots. No Shiny Blender Real paths were included. Converted Glossy paths such as `/data/liuly/dataset/3DGS/GlossySyntheticConverted/luyu_blender` are used for scene discovery; raw Glossy Synthetic is not used as a train source.

Current result: true depth, normal, and mesh/surface quality metrics are **not computable from existing completed outputs**. Existing outputs support only artifact proxy diagnostics from final PLY point clouds plus correlation against reflection/RGB JSON metrics.

## Availability Counts

| signal | count |
| --- | ---: |
| Shiny scenes with GT normal PNGs | 6/6 |
| Glossy scenes with GT normal PNGs | 0/8 |
| scenes with saved rendered depth outputs | 0/14 |
| scenes with saved rendered normal outputs | 0/14 |
| scenes with accepted GT mesh/reference point cloud | 0/14 |
| scenes with completed final model point clouds | 14/14 |

## Possible Now

- Proxy-only artifact diagnostics from final `point_cloud/iteration_31000/point_cloud.ply` files: vertex count and bounding-box extent.
- Correlations between reflection-consistency JSON values and fixed render-quality JSON values.
- Reflection metric metadata such as `valid_pair_count`, `pair_mode`, and `max_angle_deg` when present.

## Not Possible Yet

- Depth MAE/RMSE/AbsRel: no GT depth and no saved rendered depth buffers in the inspected completed outputs.
- Normal MAE/cosine: Shiny scenes have GT normal PNGs, but completed outputs do not save rendered normals; Glossy converted scenes do not expose GT normal PNGs. Coordinate-space validation is also required before any normal comparison.
- Chamfer/F-score: completed Ref-GS outputs have final Gaussian PLY point clouds, but no extracted predicted meshes and no accepted GT mesh/eval point-cloud references for these datasets.
- Reflective-region geometry metrics: render-quality JSON stores reflective aggregate metrics but not reusable reflective masks.

## Required Next Instrumentation

- Save or evaluate rendered depth and normal buffers under fixed camera/split alignment.
- Verify normal coordinate space before comparing to Shiny GT normals.
- Extract meshes or define an accepted geometry reference protocol before Chamfer/F-score.
- Save reflective masks and RC-valid correspondence masks if region-specific geometry evaluation is needed.

## Claim Boundary

Inventory only. No geometry metric values and no mesh/surface improvement claim are supported.
