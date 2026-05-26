# RC-RefGS Shiny Blender Real Schema Fix and Dry-Run Gate

Date: 2026-05-26  
Window claim: `Fix Shiny Blender Real maneki/vase discovery and rerun full-dataset dry-run gate.`

## Scope Guardrails

- No training launch
- No metrics run
- No full-dataset i31000 execution
- No ablation
- No multi-seed
- No geometry/mesh work
- No manuscript claim edits
- No scientific claim upgrades

## Shiny Blender Real Schema Comparison

Root inspected:
- `/data/liuly/dataset/3DGS/glossy/GlossyReal`

Expected scenes:
- `bear`, `bunny`, `coral`, `maneki`, `vase`

Observed schema:
- All five scenes are COLMAP-style (`transforms_train.json`/`transforms_test.json` absent, `images/` present, `colmap/sparse/0` present).
- `bear`, `bunny`, `coral` additionally provide top-level `sparse` symlink.
- `maneki`, `vase` do not provide top-level `sparse` and only expose nested `colmap/sparse/0`.

Schema delta conclusion:
- Previous runner discovery recognized only top-level `sparse`, which excluded `maneki` and `vase`.
- The scene data are not ambiguous; they are the same COLMAP family with a different sparse nesting layout.

## Runner Fix

Patched:
- `scripts/run_rc_refgs_full_dataset_all_experiments.sh`

Changes:
- COLMAP discovery now accepts either:
  - `<scene>/sparse/`
  - `<scene>/colmap/sparse/`
- Blender discovery hardened with a generic trainability check:
  - requires `transforms_train.json` + `transforms_test.json`
  - requires frame file references to resolve to real files (`.png`/`.jpg`/`.jpeg`)

No scene-name hardcoding was introduced.

## Test Updates

Updated:
- `tests/test_rc_refgs_full_dataset_runner_static.py`

Added/updated coverage:
- Shiny Blender Real schema variant with nested `colmap/sparse/0` for `maneki`/`vase`.
- Dry-run expansion includes all five real scenes.
- Dry-run remains planning-only (no training launch behavior change).

## Full-Dataset Dry-Run (Required Roots)

Executed command:
- `scripts/run_rc_refgs_full_dataset_all_experiments.sh --shiny_blender_synthetic_root /data/liuly/dataset/3DGS/refnerf_synthetic --shiny_blender_real_root /data/liuly/dataset/3DGS/glossy/GlossyReal --glossy_synthetic_root /data/liuly/dataset/3DGS/GlossySyntheticConverted --output_root /tmp/rc_refgs_full_dataset_dryrun_20260526 --devices 0 --seeds 0 --iterations 31000 --max_pairs 10 --variants base,rc`

Result:
- exit code: `0`
- status files written:
  - `/tmp/rc_refgs_full_dataset_dryrun_20260526/full_dataset_run_status.json`
  - `/tmp/rc_refgs_full_dataset_dryrun_20260526/full_dataset_run_status.md`
- planned jobs: `42`

Expanded scenes:
- Shiny Blender Synthetic: 8 (`chair`, `drums`, `ficus`, `hotdog`, `lego`, `materials`, `mic`, `ship`)
- Shiny Blender Real: 5 (`bear`, `bunny`, `coral`, `maneki`, `vase`)
- Glossy Synthetic converted: 8 (`angel`, `bell`, `cat`, `horse`, `luyu`, `potion`, `tbell`, `teapot`)

## Gate Interpretation

- Full required dataset dry-run expansion: **PASS**
- FD-P0 manifest gate: **GO**

## Next Task Routing

- `FD-P2` full-dataset base/RC `i31000` execution is now the next task.
- Keep `teapot/toaster/car` evidence as subset-only.
- Do not claim complete-dataset experimental results in this window.
