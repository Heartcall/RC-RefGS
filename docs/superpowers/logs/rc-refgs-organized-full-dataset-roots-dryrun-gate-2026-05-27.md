# RC-RefGS Organized Full-Dataset Roots Dry-Run GO Gate

Date: 2026-05-27

Scope: claimed exactly one task "Finalize Shiny Real scene-set policy and full-dataset dry-run GO gate." No training, metrics, ablation, multi-seed, or manuscript/scientific claim upgrade was started.

## Claim-Bearing Scope (Finalized)

- Shiny Blender Synthetic root: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic`
  - Scenes: `ball`, `car`, `coffee`, `helmet`, `teapot`, `toaster` (`6`).
- Shiny Blender Real root: `/data/liuly/dataset/3DGS/Shiny Blender Real`
  - Scenes: `gardenspheres`, `sedan`, `toycar` (`3`).
- Glossy Synthetic Converted root: `/data/liuly/dataset/3DGS/GlossySyntheticConverted`
  - Scenes: `angel`, `bell`, `cat`, `horse`, `luyu`, `potion`, `tbell`, `teapot` (`8`).

Final claim-bearing scene count: `17` scenes (`6+3+8`).

## Optional/Background Scope

- NeRF Synthetic (optional/background only): `/data/liuly/dataset/3DGS/NeRF Synthetic`
  - `chair`, `drums`, `ficus`, `hotdog`, `lego`, `materials`, `mic`, `ship`
- Additional GlossyReal (optional additional real dataset): `/data/liuly/dataset/3DGS/glossy/GlossyReal`
  - `bear`, `bunny`, `coral`, `maneki`, `vase`

Neither optional dataset is included in claim-bearing job expansion unless explicitly requested.

## Dry-Run Gate Result

- Required command rerun (dry-run only, no `--execute`) succeeded.
- Status outputs:
  - `/tmp/rc_refgs_full_dataset_base_rc_i31000_20260527/full_dataset_run_status.json`
  - `/tmp/rc_refgs_full_dataset_base_rc_i31000_20260527/full_dataset_run_status.md`
- Planned jobs: `34`
- Expansion from status JSON:
  - `shiny_blender_synthetic`: 6
  - `shiny_blender_real`: 3
  - `glossy_synthetic`: 8
- Optional dataset checks:
  - no `nerf` dataset key in planned jobs;
  - no optional GlossyReal dataset key in planned jobs;
  - no NeRF scene names under `shiny_blender_synthetic`;
  - no `bear/bunny/coral/maneki/vase` in claim-bearing job scenes.

## Decision

GO.

- Organized 6+3+8 claim-bearing scope is accepted.
- Dry-run expands exactly 34 jobs with zero training launches.
- Future generic prompts should not block on `bear/bunny/coral/maneki/vase` for required Shiny Real scope.
