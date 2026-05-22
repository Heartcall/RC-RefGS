# RC-RefGS P4 Full-Horizon Base/RC Preflight

Date: 2026-05-22
Window: codex P4 full-horizon-preflight

## Purpose

Define the first P4 full-horizon execution step without launching training in this window.

The latest completed evidence is the corrected i300 full-split material-quality summary for `teapot`, `toaster`, and `car`, and the earlier corrected i300 LPIPS-enabled render-quality summary. Both are mixed/unsupported for broad claim upgrades, so this P4 artifact is orchestration evidence only.

## Manifest

- JSON: `docs/superpowers/logs/rc-refgs-p4-base-rc-i31000-manifest-2026-05-22.json`
- Dry-run summary target: `docs/superpowers/logs/rc-refgs-p4-base-rc-i31000-dryrun-summary-2026-05-22.json`
- Future output root: `/tmp/rc_refgs_p4_base_rc_i31000_20260522`

## Matrix

- Scenes: `teapot`, `toaster`, `car`
- Variants: `base`, `rc`
- Seeds: `0`
- Iterations: `31000`
- RC schedule: `ref_consistency_start=3000`, `ref_consistency_every=4`
- Metrics: train/test `reflection_consistency`

Expected expanded jobs: 6.

Expected artifacts per job:

- `point_cloud/iteration_31000/point_cloud.ply`
- `reflection_consistency_train.json`
- `reflection_consistency_test.json`

Expected artifacts total: 18.

## Execution Boundary

This artifact does not add comparative evidence by itself. It only makes the next full-horizon launch auditable.

GO requires:

- manifest JSON parses;
- launcher dry-run expands to 6 jobs;
- dry-run summary records 18 expected missing artifacts before any future run;
- generated RC train commands include `--lambda_ref_consistency 0.02` and `--ref_consistency_start 3000`;
- standard unit/syntax/diff gates pass.

NO-GO boundaries:

- Do not use this preflight to upgrade manuscript, scientific, broad rendering, material, geometry, causal, external-superiority, full-horizon, or multi-seed claims.
- Do not start full ablations or multi-seed repeats until the matched base/RC full-horizon run is complete and summarized.
- Do not start training from this window.

## P4 Sequence

1. Run the matched base/RC `31000` matrix from this manifest when compute is intentionally allocated.
2. Summarize full-horizon base-vs-RC reflection/render/material diagnostics after all six jobs complete.
3. If the base/RC evidence is stable enough to justify expansion, run the matched full ablation matrix: `base`, `rc`, `wo_ref`, `wo_conf`, `rough_only`.
4. Only after the single-seed full matrix is summarized, run at least three matched seeds for any robustness claim.

## Preflight Results

- Manifest JSON parse: pass.
- Launcher dry-run expansion: pass.
- Dry-run summary parse: pass.
- Summary contract: pass with `job_count=6`, `missing_count=18`, `rc_jobs=3`, and `rc_schedule_ok=True`.
- RC train commands include `--lambda_ref_consistency 0.02` and `--ref_consistency_start 3000`.
- No training or metrics were launched in this window.

Decision from this artifact:

- GO for P4 base/RC full-horizon launch readiness after verification.
- CONDITIONAL GO for launching the six-job `31000` matrix only when a GPU window is explicitly allocated.
- NO-GO for claim upgrades, full ablations, and multi-seed expansion from this preflight alone.
