# RC-RefGS Geometry Prerequisite Refresh

Date: 2026-05-22 19:39:29 CST

## Scope

This refresh rechecks the current blocker state for SMVP3D/reference-mesh geometry evaluation. It does not launch training, run new experiments, edit training code, edit metric code, or upgrade any geometry/reconstruction claims.

## Prior State

The prior geometry feasibility artifact is `docs/superpowers/logs/rc-refgs-geometry-feasibility-2026-05-18.md`. Its active blockers were:

- RefNeRF `points3d.ply` is random Blender initialization data, not ground-truth geometry.
- SMVP3D has OBJ references and `cameras.npz`, but the repo loader supports only COLMAP `sparse/` and Blender `transforms_train.json`.
- Plain `open3d` import fails unless `LD_LIBRARY_PATH=$CONDA_PREFIX/lib` is exported first.
- `trimesh` is missing from `ref_gs`.
- `utils.mesh_utils` import fails because `utils.render_utils` is missing.
- No root `extract_mesh.py` entrypoint exists.

## Fresh Probes

| Probe | Result |
| --- | --- |
| `conda run -n ref_gs python -c "import importlib.util; ... find_spec('trimesh')"` | `trimesh_spec= None`; still missing. |
| `conda run -n ref_gs python -c "import open3d; ..."` | Fails with `GLIBCXX_3.4.29` missing through `libLerc.so.4`; plain import still broken. |
| `conda run -n ref_gs bash -lc 'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"; python -c "import open3d; ..."'` | `open3d ok 0.17.0`; documented library-path workaround still works. |
| `conda run -n ref_gs python -c "import utils.mesh_utils; ..."` | Fails with `ModuleNotFoundError: No module named 'utils.render_utils'`; mesh utility path still broken before `trimesh` usage. |
| `rg --files \| rg '(^extract_mesh\.py$|mesh.*eval|geometry|chamfer|fscore|smvp)'` | Only prior geometry feasibility artifacts were found; no mesh extraction/evaluation entrypoint is present. |
| `rg -n "transforms_train|sparse|cameras\.npz|Blender|COLMAP" scene/dataset_readers.py scene/__init__.py` | `Scene` still dispatches only COLMAP `sparse/` or Blender `transforms_train.json`; no `cameras.npz`/SMVP3D loader is present. |
| `find /data/liuly/dataset -maxdepth 4 -iname '*smvp*' -o -iname '*SMVP*'` | `/data/liuly/dataset/3DGS/glossy/SMVP3D` and its zip are present. |
| `find /data/liuly/dataset/3DGS/glossy/SMVP3D -mindepth 1 -maxdepth 1 -type d -printf '%f\n' \| sort` | Scenes present: `david`, `dragon`, `hedgehog`, `snail`, `squirrel`. |
| Per-scene image count probe | Each SMVP3D scene has 48 PNG images under `image/`. |
| OBJ/camera probe | Each scene has `<scene>.obj` and `cameras.npz`. |

## Code Anchors

- `scene/__init__.py` recognizes `sparse/` or `transforms_train.json` only; otherwise it raises `Could not recognize scene type!`.
- `scene/dataset_readers.py` writes Blender `points3d.ply` from random points in `[-1, 1]`, confirming it is unsuitable as geometry GT.
- `utils/mesh_utils.py` imports `utils.render_utils`, `open3d`, and `trimesh` at module import time, so missing `utils.render_utils` and missing `trimesh` must be resolved before the mesh extractor path can be used directly.

## Decision

**CONDITIONAL GO** for a future bounded geometry-prerequisite implementation task that first adds or restores the missing runtime plumbing:

1. Restore/replace the missing `utils.render_utils` dependency or isolate mesh utilities from image-save helpers.
2. Add the missing mesh dependency path (`trimesh`) or remove that dependency if unused by the selected extraction/evaluation route.
3. Preserve the Open3D import workaround in any geometry runner environment until the base environment is repaired.
4. Add or restore a mesh extraction entrypoint and smoke-test it on an existing output.
5. Add SMVP3D `cameras.npz` loader support or a deterministic SMVP3D-to-RefGS transform conversion before Chamfer/F-score.

**NO-GO** remains for immediate RefNeRF Chamfer/F-score, SMVP3D geometry metrics, geometry-quality claims, reconstruction-quality claims, and any manuscript/scientific claim upgrade.

## Follow-up: Import Isolation

Date: 2026-05-22 20:14:04 CST

The first bounded prerequisite implementation isolated `utils.mesh_utils` from two avoidable import blockers:

- `utils.render_utils` is no longer required at module import time; `export_image` now fails explicitly if image-save helpers are unavailable.
- The unused top-level `trimesh` import was removed.
- With `LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH`, `import utils.mesh_utils` now succeeds.

Remaining blockers:

- Plain `open3d` import still needs the documented library-path workaround in this environment.
- SMVP3D `cameras.npz` loader or transform conversion remains missing.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: Root Extraction Entrypoint

Date: 2026-05-22 22:04:05 CST

The second bounded prerequisite implementation added a smoke-testable root `extract_mesh.py` entrypoint:

- Supports `--dry_run` and `--check_imports` without launching training.
- Writes a JSON summary with expected `point_cloud/iteration_<N>/point_cloud.ply` inputs, missing inputs, output mesh path, split, and mesh mode.
- Uses `GaussianExtractor.extract_mesh_bounded`/`extract_mesh_unbounded` only in non-dry-run mode.
- Keeps actual mesh extraction separate from geometry-quality claims.

Remaining blockers:

- A real extraction runtime smoke on an existing model has not been run in this window.
- SMVP3D `cameras.npz` loader or deterministic transform conversion remains missing.
- OBJ-based Chamfer/F-score metrics remain missing.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: Existing-Artifact Dry-Run Smoke

Date: 2026-05-22 22:55:53 CST

The third bounded prerequisite step ran the root `extract_mesh.py` entrypoint against an existing corrected i300 model artifact without training or mesh extraction:

- Command target: `/tmp/rc_refgs_i300_validation_base_rc_20260520/teapot_base`, iteration `300`.
- Summary artifact: `docs/superpowers/logs/rc-refgs-extract-mesh-teapot-base-dryrun-smoke-2026-05-22.json`.
- Result: `--dry_run --check_imports` exited 0, loaded the existing `cfg_args`, found `point_cloud/iteration_300/point_cloud.ply`, reported `missing_inputs=[]`, and imported `GaussianExtractor` plus `post_process_mesh`.
- Dry-run guard: `/tmp/rc_refgs_i300_validation_base_rc_20260520/teapot_base/mesh_iter300_dryrun.ply` remained absent.

Remaining blockers:

- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window and Open3D environment handling.
- SMVP3D `cameras.npz` loader or deterministic transform conversion remains missing.
- OBJ-based Chamfer/F-score metrics remain missing.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: SMVP3D Transform Conversion Support

Date: 2026-05-22 23:10:13 CST

The fourth bounded prerequisite step added deterministic SMVP3D `cameras.npz` to Ref-GS transform conversion support:

- Helper: `utils/smvp3d_utils.py`.
- CLI: `scripts/convert_smvp3d_transforms.py`.
- Tests: `tests/test_smvp3d_transform_support.py`.
- Real-scene dry-run summary: `docs/superpowers/logs/rc-refgs-smvp3d-dragon-transform-dryrun-2026-05-22.json`.

Behavior covered:

- Reads DTU-style `world_mat_<i>` / `scale_mat_<i>` matrices.
- Decomposes each projection with OpenCV and writes Blender-reader-compatible `transform_matrix` entries.
- Supports train/test split with `--eval --llffhold`.
- Can run in summary-only mode without writing into the dataset directory.

Real `dragon` dry-run result:

- `camera_count=48`
- `converted_count=48`
- `train_count=42`
- `test_count=6`
- `missing_images=[]`

Remaining blockers:

- All-scene SMVP3D transform dry-run coverage is still pending.
- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window and Open3D environment handling.
- OBJ-based Chamfer/F-score metric plumbing remains missing.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: All-Scene SMVP3D Transform Dry-Run Coverage

Date: 2026-05-23 01:29:46 CST

The fifth bounded prerequisite step dry-ran the SMVP3D transform converter across all five available scenes without writing into the dataset:

- Scenes: `david`, `dragon`, `hedgehog`, `snail`, and `squirrel`.
- Per-scene summaries: `docs/superpowers/logs/rc-refgs-smvp3d-<scene>-transform-dryrun-2026-05-23.json`.
- Aggregate summary: `docs/superpowers/logs/rc-refgs-smvp3d-all-scene-transform-dryrun-summary-2026-05-23.json`.

Aggregate result:

- `scene_count=5`
- `camera_count=240`
- `converted_count=240`
- `train_count=210`
- `test_count=30`
- `missing_images=0`

Dataset-write guard:

- A probe for SMVP3D `transforms_train.json` and `transforms_test.json` returned no paths.

Remaining blockers:

- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window and Open3D environment handling.
- OBJ-based Chamfer/F-score metric plumbing remains missing.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: OBJ-Reference Dry-Run Scaffolding

Date: 2026-05-23 02:54:01 CST

The sixth bounded prerequisite step added SMVP3D OBJ-reference geometry-evaluation dry-run scaffolding:

- Helper: `utils/smvp3d_geometry_plan.py`.
- CLI: `scripts/prepare_smvp3d_geometry_eval.py`.
- Tests: `tests/test_smvp3d_geometry_eval_plan.py`.
- Real dry-run summary: `docs/superpowers/logs/rc-refgs-smvp3d-obj-reference-dryrun-plan-2026-05-23.json`.

Real SMVP3D dry-run result:

- `scene_count=5`
- `reference_obj_count=5`
- `ready_count=0`
- `missing_reference_count=0`
- `missing_mesh_count=5`
- `metrics_computed=false`

This confirms all five SMVP3D OBJ references are addressable and the current blocker is missing predicted/extracted meshes, not missing references.

Remaining blockers:

- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window and Open3D environment handling.
- OBJ-based Chamfer/F-score metric-value computation remains blocked until predicted meshes exist.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: Extract-Mesh Open3D Preflight

Date: 2026-05-23 04:05:01 CST

The seventh bounded prerequisite step added a non-crashing Open3D runtime preflight to the root mesh extraction entrypoint:

- Entry point: `extract_mesh.py --check_open3d`.
- Regression test: `tests/test_extract_mesh_static.py`.
- Plain-environment dry-run summary: `docs/superpowers/logs/rc-refgs-extract-mesh-open3d-preflight-2026-05-23.json`.
- Library-path dry-run summary: `docs/superpowers/logs/rc-refgs-extract-mesh-open3d-preflight-ldpath-2026-05-23.json`.

Existing corrected i300 `teapot_base` dry-run result:

- `missing_inputs=[]`
- plain Open3D preflight: `ok=false`, `error_type=ImportError`, `GLIBCXX_3.4.29` missing through `libLerc.so.4`
- recommended prefix: `/home/liuly/anaconda3/envs/ref_gs/lib`
- `LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH` preflight: `ok=true`, `version=0.17.0`

The same update fixed the `cfg_args` merge path for mesh-only CLI fields such as `output_mesh`, so dry-run checks on existing model directories with saved configs no longer fail before writing their summary.

Remaining blockers:

- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window.
- OBJ-based Chamfer/F-score metric-value computation remains blocked until predicted meshes exist.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: Geometry Metric Gate Dry-Run Checker

Date: 2026-05-23 05:52:05 CST

The current bounded prerequisite step added a dry-run gate that combines the extraction post-run smoke report and the SMVP3D OBJ-reference dry-run plan:

- Checker: `scripts/check_geometry_metric_gate.py`.
- Tests: `tests/test_geometry_metric_gate.py`.
- Current gate report: `docs/superpowers/logs/rc-refgs-geometry-metric-gate-current-nogo-2026-05-23.json`.

Gate contract:

- Reads the post-run extraction smoke report and SMVP3D geometry input plan.
- Reports whether geometry metric computation is allowed.
- Reports `metrics_computed=false`.
- Does not report Chamfer/F-score or any geometry metric values.

Current report:

- Metrics allowed: `false`.
- Status: `blocked`.
- Post-run status: `summary_is_dry_run`.
- Missing predicted meshes: `5`.
- Blockers: `postrun_status:summary_is_dry_run`, `missing_predicted_meshes:5`.

Remaining blockers:

- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window.
- After extraction runs, first use `scripts/check_extract_mesh_smoke.py` on the runtime summary, then rerun `scripts/check_geometry_metric_gate.py`.
- OBJ-based Chamfer/F-score metric-value computation remains blocked until the gate reports `metrics_allowed=true`.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: Guarded SMVP3D Geometry Evaluator

Date: 2026-05-23 06:43:39 CST

The current bounded prerequisite step added a guarded geometry evaluator entrypoint:

- Evaluator: `metrics/smvp3d_geometry_eval.py`.
- Tests: `tests/test_smvp3d_geometry_eval.py`.
- Current blocked report: `docs/superpowers/logs/rc-refgs-smvp3d-geometry-eval-current-blocked-2026-05-23.json`.

Evaluator contract:

- Reads the SMVP3D OBJ-reference geometry plan.
- Reads the geometry metric gate report.
- Refuses to compute when `metrics_allowed=false`.
- Computes only vertex-only Chamfer/F-score diagnostics when the gate reports `metrics_allowed=true` and ready reference/prediction mesh inputs exist.

Current real-artifact report:

- Status: `blocked_by_gate`.
- Metrics computed: `false`.
- Scenes: `[]`.
- Blockers: `postrun_status:summary_is_dry_run`, `missing_predicted_meshes:5`.
- No real Chamfer/F-score values were produced.

Remaining blockers:

- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window.
- After extraction runs, first use `scripts/check_extract_mesh_smoke.py`, then rerun `scripts/check_geometry_metric_gate.py`.
- Run `metrics/smvp3d_geometry_eval.py` on real SMVP3D inputs only after the gate reports `metrics_allowed=true`.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: SMVP3D Geometry Pipeline Status Summarizer

Date: 2026-05-23 14:08:01 CST

The current bounded prerequisite step added a machine-readable pipeline status summarizer:

- Summarizer: `scripts/summarize_smvp3d_geometry_pipeline_status.py`.
- Tests: `tests/test_smvp3d_geometry_pipeline_status.py`.
- Current blocked status: `docs/superpowers/logs/rc-refgs-smvp3d-geometry-pipeline-status-current-blocked-2026-05-23.json`.

Summarizer contract:

- Reads the post-run extraction smoke report.
- Reads the geometry metric gate report.
- Reads the guarded evaluator report.
- Emits one current pipeline `status`, one `next_action`, blocker list, and claim boundary.
- Does not compute Chamfer/F-score or any geometry metric values.

Current real-artifact report:

- Status: `blocked_pending_extraction`.
- Next action: `run_non_dryrun_extraction_smoke_with_explicit_compute`.
- Metrics ready: `false`.
- Metrics computed: `false`.
- Blockers: `postrun_status:summary_is_dry_run`, `missing_predicted_meshes:5`.

Remaining blockers:

- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window.
- The next runtime window should run extraction first, then post-run smoke validation, then gate rerun, then guarded evaluator only if the gate reports `metrics_allowed=true`.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: Extract-Mesh Post-Run Smoke Validator

Date: 2026-05-23 04:53:59 CST

The tenth bounded prerequisite step added a post-run extraction smoke validator:

- CLI: `scripts/check_extract_mesh_smoke.py`.
- Tests: `tests/test_extract_mesh_smoke_check.py`.
- Current missing-output report: `docs/superpowers/logs/rc-refgs-extract-mesh-postrun-smoke-current-missing-2026-05-23.json`.

Validator contract:

- Reads an `extract_mesh.py` runtime summary JSON.
- Checks only whether the referenced mesh path exists and has non-zero size.
- Reports `metrics_computed=false`.
- Does not report Chamfer/F-score or any geometry metric values.

Current report:

- Input summary: `docs/superpowers/logs/rc-refgs-extract-mesh-runtime-command-plan-2026-05-23.json`
- Status: `summary_is_dry_run`
- Ready: `false`
- Mesh exists: `false`
- Missing inputs: `[]`
- Metrics computed: `false`

Remaining blockers:

- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window.
- After extraction runs, this validator should be run on the non-dry-run runtime summary before any geometry metric work.
- OBJ-based Chamfer/F-score metric-value computation remains blocked until predicted meshes exist.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: Extract-Mesh Runtime Readiness Packet

Date: 2026-05-23 04:46:20 CST

The ninth bounded prerequisite step consolidated the extraction handoff into a runtime-readiness packet:

- JSON: `docs/superpowers/logs/rc-refgs-extract-mesh-runtime-readiness-2026-05-23.json`.
- Markdown: `docs/superpowers/logs/rc-refgs-extract-mesh-runtime-readiness-2026-05-23.md`.

The packet records:

- existing corrected i300 `teapot_base` target at iteration `300`
- `missing_inputs=[]`
- required environment `LD_LIBRARY_PATH=/home/liuly/anaconda3/envs/ref_gs/lib:$LD_LIBRARY_PATH`
- Open3D workaround status `ok=true`, `version=0.17.0`
- planned output mesh `/tmp/rc_refgs_i300_validation_base_rc_20260520/teapot_base/mesh_iter300_runtime_plan.ply`
- planned runtime summary `docs/superpowers/logs/rc-refgs-extract-mesh-runtime-command-plan-2026-05-23-runtime.json`
- SMVP3D dependency status: five OBJ references present, five predicted meshes missing, and `metrics_computed=false`
- explicit GO / CONDITIONAL GO / NO-GO boundaries for the next runtime window

The packet did not create the planned mesh output.

Remaining blockers:

- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window.
- OBJ-based Chamfer/F-score metric-value computation remains blocked until predicted meshes exist.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.

## Follow-up: Extract-Mesh Runtime Command Plan

Date: 2026-05-23 04:34:33 CST

The eighth bounded prerequisite step added runtime command-plan reporting to the root mesh extraction dry-run path:

- Entry point: `extract_mesh.py --emit_runtime_command`.
- Regression test: `tests/test_extract_mesh_static.py`.
- Real dry-run summary: `docs/superpowers/logs/rc-refgs-extract-mesh-runtime-command-plan-2026-05-23.json`.

Existing corrected i300 `teapot_base` command-plan result:

- `missing_inputs=[]`
- Open3D preflight with the library-path workaround: `ok=true`, `version=0.17.0`
- planned environment: `LD_LIBRARY_PATH=/home/liuly/anaconda3/envs/ref_gs/lib:$LD_LIBRARY_PATH`
- planned output mesh: `/tmp/rc_refgs_i300_validation_base_rc_20260520/teapot_base/mesh_iter300_runtime_plan.ply`
- planned runtime summary: `docs/superpowers/logs/rc-refgs-extract-mesh-runtime-command-plan-2026-05-23-runtime.json`
- the planned argv omits `--dry_run`, `--check_open3d`, and `--emit_runtime_command`

The dry-run command-plan artifact did not create the planned mesh output.

Remaining blockers:

- Non-dry-run mesh extraction still needs an explicitly allocated runtime/GPU window.
- OBJ-based Chamfer/F-score metric-value computation remains blocked until predicted meshes exist.
- Geometry-quality and reconstruction-quality claims remain **NO-GO**.
