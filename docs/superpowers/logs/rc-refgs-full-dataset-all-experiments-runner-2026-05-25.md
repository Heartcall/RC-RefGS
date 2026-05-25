# RC-RefGS Full-Dataset All-Experiments Runner

Date: 2026-05-25

Scope: script-generation and dry-run verification window. No training, metrics, dataset conversion, manuscript prose edits, scientific claim upgrades, or runtime use of `scripts/run_rc_refgs_ablation.sh` are allowed in this window.

## Artifact

Runner:

```bash
scripts/run_rc_refgs_full_dataset_all_experiments.sh
```

Purpose: generate and optionally execute the complete full-dataset RC-RefGS matrix across Shiny Blender Synthetic, Shiny Blender Real, and Glossy Synthetic, while making dry-run the default and preserving complete-dataset claim boundaries.

## Safety Contract

- Default mode is dry-run.
- Real training requires both:
  - `--execute`
  - `--confirm_full_dataset_execute YES`
- Required roots:
  - `--shiny_blender_synthetic_root`
  - `--shiny_blender_real_root`
  - `--glossy_synthetic_root`
- Required runtime args:
  - `--output_root`
  - `--devices`
- Runtime launcher:
  - uses `scripts/run_rc_refgs_ablation_direct.py`
  - does not set `CUDA_VISIBLE_DEVICES`
  - passes explicit `--cuda_device`
- Prior `teapot/toaster/car` artifacts remain subset evidence only and must not be treated as complete-dataset evidence.

## Dataset Gate

The runner discovers valid scene directories under all three required roots.

Accepted scene forms:

- COLMAP-style scene: contains `sparse/`
- Blender-style scene: contains `transforms_train.json` and `transforms_test.json`

Glossy Synthetic is stricter. If raw NeRO-style scene directories are detected with `*-camera.pkl` and `*-depth.png` files but without converted Blender transforms, the runner fails before planning or training and points to `nero2blender.py` conversion.

## Output Layout

The visible job output path is:

```bash
${output_root}/${dataset_name}/${scene}/${variant}/seed_${seed}/
```

Completion requires all four artifacts:

```bash
point_cloud/iteration_${iterations}/point_cloud.ply
reflection_consistency_train.json
reflection_consistency_test.json
launcher_summary.json
```

The runner skips completed jobs by default. `--force_rerun` reruns completed jobs. `--rerun_failed` only reruns incomplete jobs. `--resume_existing` is an alias for the default skip-complete behavior.

If `--skip_train` is passed, the runner requires an existing point cloud and schedules direct-launcher metric regeneration only for incomplete jobs.

## Status Outputs

Every successful planning pass writes:

```bash
${output_root}/full_dataset_run_status.json
${output_root}/full_dataset_run_status.md
```

The status files include planned, completed, skipped, failed, and missing-artifact counts plus per-job rows.

## Example Dry-Run

```bash
scripts/run_rc_refgs_full_dataset_all_experiments.sh \
  --shiny_blender_synthetic_root /data/liuly/dataset/3DGS/refnerf \
  --shiny_blender_real_root /data/liuly/dataset/3DGS/glossy/GlossyReal \
  --glossy_synthetic_root /data/liuly/dataset/3DGS/GlossySyntheticConverted \
  --output_root /tmp/rc_refgs_full_dataset_all_experiments_dryrun \
  --devices 0
```

This remains a dry-run unless `--execute --confirm_full_dataset_execute YES` is also supplied.

## Current Decision Boundary

GO is only for the runner artifact and dry-run safeguards.

NO-GO remains for claim-bearing full-dataset training until all required dataset roots are valid and Glossy Synthetic conversion is validated. NO-GO also remains for complete-dataset claims, manuscript/scientific claim upgrades, broad rendering/material/geometry/external-superiority/causal/full-ablation/multi-seed claims, and SWITCH MODEL routing for claim-bearing P5 audit.
