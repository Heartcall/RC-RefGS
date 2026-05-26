# RC-RefGS Full-Dataset Root Fix and Dry-Run Gate

Date: 2026-05-26  
Window claim: `Fix Shiny Blender Synthetic root and rerun full-dataset manifest dry-run gate.`

## Scope Guardrails

- No training launch
- No metrics run
- No full-dataset i31000 execution
- No ablation
- No multi-seed
- No geometry/mesh work
- No manuscript claim edits
- No scientific claim upgrades

## Root Fix Validation

Corrected Shiny Blender Synthetic root:
- `/data/liuly/dataset/3DGS/refnerf_synthetic`

Discovered scenes:
- `chair`, `drums`, `ficus`, `hotdog`, `lego`, `materials`, `mic`, `ship`

Per-scene trainability indicators:
- `transforms_train.json`: present in all 8 scenes
- `transforms_test.json`: present in all 8 scenes
- non-empty accepted image directories: `train/` and `test/` in all 8 scenes
- frame reference checks: train/test referenced images missing = `0` for all scenes

Conclusion:
- Corrected Shiny Blender Synthetic root is valid and trainable.

## Glossy Synthetic Converted Status (Preserved)

Preserved validated root:
- `/data/liuly/dataset/3DGS/GlossySyntheticConverted`
- source artifact: `docs/superpowers/logs/rc-refgs-glossy-synthetic-converted-root-validation-2026-05-26.json`

Status remains:
- expected 8 scenes present (`angel/bell/cat/horse/luyu/potion/tbell/teapot` as `*_blender`)
- `transforms_train.json` + `transforms_test.json` + non-empty `rgb/` verified
- root has no raw NeRO markers (`*-camera.pkl` / `*-depth.png`)

## Full-Dataset Dry-Run (Required Roots)

Executed command:
- `scripts/run_rc_refgs_full_dataset_all_experiments.sh --shiny_blender_synthetic_root /data/liuly/dataset/3DGS/refnerf_synthetic --shiny_blender_real_root /data/liuly/dataset/3DGS/glossy/GlossyReal --glossy_synthetic_root /data/liuly/dataset/3DGS/GlossySyntheticConverted --output_root /tmp/rc_refgs_full_dataset_dryrun_20260526 --devices 0 --seeds 0 --iterations 31000 --max_pairs 10 --variants base,rc`

Observed result:
- exit code: `0`
- status files written:
  - `/tmp/rc_refgs_full_dataset_dryrun_20260526/full_dataset_run_status.json`
  - `/tmp/rc_refgs_full_dataset_dryrun_20260526/full_dataset_run_status.md`
- planned jobs: `38`
- expanded scenes by dataset:
  - Shiny Blender Synthetic: `8`
  - Shiny Blender Real: `3` (`bear`, `bunny`, `coral`)
  - Glossy Synthetic: `8`

Coverage gap found:
- Shiny Blender Real directories under root are `bear`, `bunny`, `coral`, `maneki`, `vase`.
- Current runner expanded only 3 scenes because `maneki` and `vase` do not expose top-level `sparse/`; they store COLMAP under `colmap/sparse/0`.

## Gate Interpretation

- Shiny Blender Synthetic root fix: **PASS**
- GlossySyntheticConverted preservation: **PASS**
- Full required-scene expansion gate: **BLOCKED by Shiny Blender Real schema mismatch (`maneki`, `vase`)**
- FD-P0 manifest gate in this window: **CONDITIONAL GO**

## Next Task Routing

- Keep `teapot/toaster/car` evidence classified as subset-only.
- `FD-P2` full-dataset base/RC `i31000` remains the next execution task, but only after FD-P0 gate is fully unambiguous across all required scenes.
- Do not start `FD-P2` in this window.
