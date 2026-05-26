# RC-RefGS GlossySyntheticConverted Root Validation

Date: 2026-05-26  
Window claim: `Validate GlossySyntheticConverted and refresh full-dataset manifest gate.`

## Scope Guardrails

- No training launch
- No metrics run
- No full-dataset i31000 execution
- No ablation
- No multi-seed
- No geometry/mesh work
- No manuscript claim edits
- No scientific claim upgrades

## Converted Root Validation

Validated root:
- `/data/liuly/dataset/3DGS/GlossySyntheticConverted`

Expected scenes:
- `angel`, `bell`, `cat`, `horse`, `luyu`, `potion`, `tbell`, `teapot`

Observed scene directories:
- `angel_blender`, `bell_blender`, `cat_blender`, `horse_blender`, `luyu_blender`, `potion_blender`, `tbell_blender`, `teapot_blender`

Result:
- Scene set matches expected exactly.
- Each scene contains:
  - `transforms_train.json`
  - `transforms_test.json`
  - non-empty `rgb/` (128 files each)
- Frame-path validation passed:
  - train: `112` frames per scene
  - test: `16` frames per scene
  - missing referenced images: `0` for train/test in all scenes
- Raw NeRO marker check in converted root:
  - `*-camera.pkl`: `0`
  - `*-depth.png`: `0`

Conclusion:
- `GlossySyntheticConverted` is valid Blender-style trainable input for Ref-GS loader.

## Full-Dataset Dry-Run (Required Roots)

Required command (as requested):
- `scripts/run_rc_refgs_full_dataset_all_experiments.sh --shiny_blender_synthetic_root /data/liuly/dataset/3DGS/refnerf --shiny_blender_real_root /data/liuly/dataset/3DGS/glossy/GlossyReal --glossy_synthetic_root /data/liuly/dataset/3DGS/GlossySyntheticConverted --output_root /tmp/rc_refgs_full_dataset_dryrun_20260526 --devices 0 --seeds 0 --iterations 31000 --max_pairs 10 --variants base,rc`

Observed result:
- Exit code: `2`
- Error: `Shiny Blender Synthetic root missing: /data/liuly/dataset/3DGS/refnerf`

Diagnostic-only check (not used to pass required-root gate):
- Synthetic root swapped to `/data/liuly/dataset/3DGS/refnerf_real`
- Dry-run exited `0` and expanded successfully with status artifacts in:
  - `/tmp/rc_refgs_full_dataset_dryrun_20260526_altref/full_dataset_run_status.{json,md}`

## Gate Interpretation

- Glossy converted-root validation: **PASS**
- Required-roots full-dataset dry-run gate: **BLOCKED** (synthetic root path mismatch)
- FD-P0 manifest gate in this window: **CONDITIONAL GO**

## Next Task Routing

- Keep `teapot/toaster/car` evidence as subset-only.
- `FD-P2` full-dataset base/RC `i31000` remains the next task only after required-root gate passes.
- Do not start `FD-P2` in this window.
