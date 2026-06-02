# RC-RefGS FD-P2 Base-vs-RC i31000 Results Analysis (2026-05-28)

## Executive Summary

- Decision: **NO-GO**
- Completion gate: 28/34 jobs complete (required: 34/34).
- Protocol action: stop analysis upgrade; publish completion failure report only.

## Completion Audit

- Expected jobs: 34
- Completed jobs: 28
- Incomplete jobs: 6
- Base/RC paired scenes complete: 14/17
- Jobs with train/test reflection JSON present: 28/34

## Dataset/Scene Coverage

- shiny_blender_synthetic: ball, car, coffee, helmet, teapot, toaster
- shiny_blender_real: gardenspheres, sedan, toycar
- glossy_synthetic: angel, bell, cat, horse, luyu, potion, tbell, teapot

## Overall Train/Test Result Table

Not computed. Full-dataset completion gate failed.

## Per-dataset Aggregate Table

Not computed. Full-dataset completion gate failed.

## Per-scene Detailed Table

See CSV: `docs/superpowers/logs/rc-refgs-fd-p2-base-rc-i31000-scene-table-2026-05-28.csv` (34 rows; split encoded as metric-presence columns per job).

## Best Improvements and Worst Regressions

Not computed. Full-dataset completion gate failed.

## PSNR Tradeoff Analysis

Not computed. Full-dataset completion gate failed.

## Pair Validity Analysis

Not computed. Full-dataset completion gate failed.

## Missing Jobs (Formal Paths)

- `shiny_blender_real/gardenspheres/base/seed_0` missing: `point_cloud/iteration_31000/point_cloud.ply; reflection_consistency_train.json; reflection_consistency_test.json; launcher_summary.json`
- `shiny_blender_real/gardenspheres/rc/seed_0` missing: `point_cloud/iteration_31000/point_cloud.ply; reflection_consistency_train.json; reflection_consistency_test.json; launcher_summary.json`
- `shiny_blender_real/sedan/base/seed_0` missing: `point_cloud/iteration_31000/point_cloud.ply; reflection_consistency_train.json; reflection_consistency_test.json; launcher_summary.json`
- `shiny_blender_real/sedan/rc/seed_0` missing: `point_cloud/iteration_31000/point_cloud.ply; reflection_consistency_train.json; reflection_consistency_test.json; launcher_summary.json`
- `shiny_blender_real/toycar/base/seed_0` missing: `point_cloud/iteration_31000/point_cloud.ply; reflection_consistency_train.json; reflection_consistency_test.json; launcher_summary.json`
- `shiny_blender_real/toycar/rc/seed_0` missing: `point_cloud/iteration_31000/point_cloud.ply; reflection_consistency_train.json; reflection_consistency_test.json; launcher_summary.json`

## Claim Boundary / Supported vs Unsupported

- Evidence level: **No support** for full-dataset RC claim upgrade in this run state.
- Supported: none beyond confirming partial completion status.
- Unsupported: full-dataset RC superiority, rendering-quality improvement, geometry/material/mesh improvements, multi-seed robustness, external generalization.

## Recommended Next Steps

- Complete missing shiny_blender_real base/rc jobs for gardenspheres/sedan/toycar in formal output paths.
- Re-run completion audit and only then run FD-P2 results deltas/aggregates.
- FD-P3 rendering-quality metrics after FD-P2 completion is verified.
- FD-P4 ablation analysis after ablations complete.
- FD-P5 multi-seed only after single-seed full-dataset evidence is summarized.
- GPT-5.5 claim audit only after complete evidence package exists.
