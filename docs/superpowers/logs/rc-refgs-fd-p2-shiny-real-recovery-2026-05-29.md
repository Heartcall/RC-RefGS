# RC-RefGS FD-P2 Shiny Real Recovery - 2026-05-29

## Task
Recover FD-P2 Shiny Real base/RC cells after metric RGB/RGBA patch.

## Scope
- Output root: `/tmp/rc_refgs_full_dataset_base_rc_i31000_20260527`
- Dataset: `shiny_blender_real`
- Scenes: `gardenspheres`, `sedan`, `toycar`
- Variants: `base`, `rc`
- Seed: `0`, Iterations: `31000`

## Runtime Actions Executed
- Smoke `gardenspheres/base` `-r 2`, i100: failed with CUDA OOM at iteration 0.
- Smoke `gardenspheres/base` `-r 4`, i100 + densify-pressure controls: completed; no RGB channel crash, no OOM; persistent `Loss=nan` observed.
- Full `gardenspheres/base` `-r 4`, i31000 + densify-pressure controls: completed.
- Metrics generated for `gardenspheres/base`: `reflection_consistency_train.json`, `reflection_consistency_test.json`.
- `launcher_summary.json` written for `gardenspheres/base` formal path.

## Current Six-Cell Inventory (Formal Paths)
- complete: 1
- metrics-only recoverable: 0
- training-needed: 0
- OOM/NaN failed: 5

| Scene | Variant | Classification | Missing Artifacts |
|---|---|---|---|
| gardenspheres | base | complete | - |
| gardenspheres | rc | OOM/NaN failed | point_cloud/iteration_31000/point_cloud.ply, reflection_consistency_train.json, reflection_consistency_test.json, launcher_summary.json |
| sedan | base | OOM/NaN failed | point_cloud/iteration_31000/point_cloud.ply, reflection_consistency_train.json, reflection_consistency_test.json, launcher_summary.json |
| sedan | rc | OOM/NaN failed | point_cloud/iteration_31000/point_cloud.ply, reflection_consistency_train.json, reflection_consistency_test.json, launcher_summary.json |
| toycar | base | OOM/NaN failed | point_cloud/iteration_31000/point_cloud.ply, reflection_consistency_train.json, reflection_consistency_test.json, launcher_summary.json |
| toycar | rc | OOM/NaN failed | point_cloud/iteration_31000/point_cloud.ply, reflection_consistency_train.json, reflection_consistency_test.json, launcher_summary.json |

## Decision
- CONDITIONAL GO: one cell recovered end-to-end (`gardenspheres/base`), remaining five cells are isolated with OOM/NaN risk and require bounded per-cell recovery runs.
- NO-GO for FD-P2 claim upgrade until all 34/34 formal jobs are complete.

## Remaining Per-Cell Command Pattern
- Training (per remaining cell, GPU0, bounded settings):
  - `conda run -n ref_gs python train.py --cuda_device 0 -s "/data/liuly/dataset/3DGS/Shiny Blender Real/<scene>" -m /tmp/rc_refgs_full_dataset_base_rc_i31000_20260527/shiny_blender_real/<scene>/<variant>/seed_0 --eval --iterations 31000 --test_iterations 31000 --save_iterations 31000 --seed 0 --quiet -r 4 --densify_until_iter 8000 --densify_grad_threshold 0.0005 --opacity_cull 0.08`
- Metrics after each completed training cell:
  - train split: `conda run -n ref_gs python metrics/reflection_consistency_eval.py --cuda_device 0 --model_path <model_path> --source_path "/data/liuly/dataset/3DGS/Shiny Blender Real/<scene>" --iteration 31000 --split train --max_pairs 10 --max_angle_deg 20 --gamma 2.0 --output_json <model_path>/reflection_consistency_train.json`
  - test split: `conda run -n ref_gs python metrics/reflection_consistency_eval.py --cuda_device 0 --model_path <model_path> --source_path "/data/liuly/dataset/3DGS/Shiny Blender Real/<scene>" --iteration 31000 --split test --max_pairs 10 --max_angle_deg 20 --gamma 2.0 --output_json <model_path>/reflection_consistency_test.json`
