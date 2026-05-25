# RC-RefGS Full Implementation and Experiment Roadmap

Date: 2026-05-19
Mode: Dual-Window Long-Horizon Protocol (meta-planning superseding roadmap)

## Scope and Priority Rule

This roadmap supersedes ad hoc next-step selection for generic continuation prompts.

When the user sends:

`Continue RC-RefGS autonomous execution under the Dual-Window Long-Horizon Protocol...`

the agent must:
1. Recover state from git + plan + autonomous log + coordination board (and linked evidence artifacts).
2. Follow this roadmap queue in order (P0 -> P5), selecting the highest-value safe unblocked task.
3. Claim exactly one task in the coordination board, execute, verify, log, release claim, then decide GO / CONDITIONAL GO / SWITCH MODEL / NO-GO.

## Current Completed Evidence Inventory

- RC core code path implemented and guarded (intermediate buffers, reflection loss gate, roughness-only control scaffold, confidence-aware TSDF path).
- Python direct-command ablation launcher implemented and smoke-verified on one reduced `teapot/base` slice:
  - `scripts/run_rc_refgs_ablation_direct.py`
  - `/tmp/rc_refgs_direct_launcher_smoke_20260519_1943_gpu2/teapot_base/reflection_consistency_{train,test}.json`
- Reflection metric entrypoint implemented (`metrics/reflection_consistency_eval.py`).
- Render-quality evaluator and LPIPS-enabled i300 summary artifact available:
  - `docs/superpowers/logs/rc-refgs-render-quality-summary-2026-05-18-lpips.{md,json}`
  - corrected i300 full-split three-scene summary: `docs/superpowers/logs/rc-refgs-i300-three-scene-render-quality-full-summary-2026-05-21.{md,json}`
- Normal-quality full-split summary artifact available:
  - `docs/superpowers/logs/rc-refgs-normal-quality-summary-2026-05-18.{md,json}`
- Material-quality diagnostics are implemented and summarized for corrected i300 `teapot/toaster/car` base/RC full splits:
  - `docs/superpowers/logs/rc-refgs-i300-material-quality-full-summary-2026-05-21.{md,json}`
- Reduced ablation summary is complete (30/30 cells, no missing cells):
  - `docs/superpowers/logs/rc-refgs-reduced-ablation-summary-2026-05-19.{md,json}`
- P4 base/RC full-horizon single-seed matrix is completed and reconciled:
  - `docs/superpowers/logs/rc-refgs-p4-base-rc-i31000-manifest-2026-05-22.json`
  - `docs/superpowers/logs/rc-refgs-p4-base-rc-i31000-dryrun-summary-2026-05-22.json`
  - `docs/superpowers/logs/rc-refgs-p4-full-horizon-preflight-2026-05-22.md`
  - `docs/superpowers/logs/rc-refgs-p4-launch-safety-audit-2026-05-22.md`
  - `docs/superpowers/logs/rc-refgs-p4-manual-artifact-reconciliation-2026-05-25.json`
  - `docs/superpowers/logs/rc-refgs-p4-base-rc-i31000-completion-status-2026-05-25.json`
  - `docs/superpowers/logs/rc-refgs-p4-i31000-base-vs-rc-reflection-summary-2026-05-25.{json,md}`
- Conservative claim framing and thresholds exist:
  - `docs/superpowers/logs/rc-refgs-claim-framing-packet-2026-05-18.md`
  - `docs/superpowers/logs/rc-refgs-acceptance-thresholds-2026-05-18.md`
- Geometry prerequisite blocker state is refreshed:
  - `docs/superpowers/logs/rc-refgs-geometry-prereq-refresh-2026-05-22.md`
- Existing-artifact extraction dry-run/import-check smoke is recorded:
  - `docs/superpowers/logs/rc-refgs-extract-mesh-teapot-base-dryrun-smoke-2026-05-22.json`
- SMVP3D `cameras.npz` transform conversion support is added and dry-run on real `dragon` metadata:
  - `utils/smvp3d_utils.py`
  - `scripts/convert_smvp3d_transforms.py`
  - `tests/test_smvp3d_transform_support.py`
  - `docs/superpowers/logs/rc-refgs-smvp3d-dragon-transform-dryrun-2026-05-22.json`
- SMVP3D transform conversion dry-run coverage is complete for all five scenes:
  - `docs/superpowers/logs/rc-refgs-smvp3d-all-scene-transform-dryrun-summary-2026-05-23.json`
- SMVP3D OBJ-reference geometry-evaluation dry-run scaffolding is added:
  - `utils/smvp3d_geometry_plan.py`
  - `scripts/prepare_smvp3d_geometry_eval.py`
  - `tests/test_smvp3d_geometry_eval_plan.py`
  - `docs/superpowers/logs/rc-refgs-smvp3d-obj-reference-dryrun-plan-2026-05-23.json`
- Mesh extraction Open3D runtime preflight is added:
  - `extract_mesh.py --check_open3d`
  - `docs/superpowers/logs/rc-refgs-extract-mesh-open3d-preflight-2026-05-23.json`
  - `docs/superpowers/logs/rc-refgs-extract-mesh-open3d-preflight-ldpath-2026-05-23.json`
- Mesh extraction dry-run runtime command planning is added:
  - `extract_mesh.py --emit_runtime_command`
  - `docs/superpowers/logs/rc-refgs-extract-mesh-runtime-command-plan-2026-05-23.json`
- Mesh extraction runtime-readiness handoff packet is recorded:
  - `docs/superpowers/logs/rc-refgs-extract-mesh-runtime-readiness-2026-05-23.{json,md}`
- Mesh extraction post-run smoke validator is added:
  - `scripts/check_extract_mesh_smoke.py`
  - `tests/test_extract_mesh_smoke_check.py`
  - `docs/superpowers/logs/rc-refgs-extract-mesh-postrun-smoke-current-missing-2026-05-23.json`
- Geometry metric dry-run gate checker is added:
  - `scripts/check_geometry_metric_gate.py`
  - `tests/test_geometry_metric_gate.py`
  - `docs/superpowers/logs/rc-refgs-geometry-metric-gate-current-nogo-2026-05-23.json`
- Guarded SMVP3D geometry evaluator entrypoint is added:
  - `metrics/smvp3d_geometry_eval.py`
  - `tests/test_smvp3d_geometry_eval.py`
  - `docs/superpowers/logs/rc-refgs-smvp3d-geometry-eval-current-blocked-2026-05-23.json`
- SMVP3D geometry pipeline status summarizer is added:
  - `scripts/summarize_smvp3d_geometry_pipeline_status.py`
  - `tests/test_smvp3d_geometry_pipeline_status.py`
  - `docs/superpowers/logs/rc-refgs-smvp3d-geometry-pipeline-status-current-blocked-2026-05-23.json`

## Current Blockers

- Bash script launcher reliability is still Mixed in nested bash/conda contexts; use the Python direct-command launcher as the primary launcher until the bash wrapper is runtime repaired.
- Full-horizon matched runs (31000) for the `teapot/toaster/car` base/RC single-seed matrix are complete (`6/6` cells, `0/18` missing expected artifacts). Do not relaunch this matrix unless a concrete artifact corruption/regression is found.
- Multi-seed evidence is missing.
- Material diagnostics exist for corrected i300 full splits, but remain Mixed / Unsupported for material-quality claims and need longer-horizon/multi-seed linkage before claim use.
- Geometry metrics are blocked pending extracted meshes. No-GPU prerequisite repairs now isolate `utils.mesh_utils` from missing top-level image-helper and unused `trimesh` import blockers, add a root `extract_mesh.py` dry-run/import-check entrypoint, verify that entrypoint on one existing corrected i300 `teapot_base` artifact with `missing_inputs=[]`, add deterministic SMVP3D `cameras.npz` to Ref-GS transform conversion support, dry-run that conversion across all five SMVP3D scenes, add an OBJ-reference dry-run plan that confirms all five OBJ references exist while expected predicted meshes are missing, add an Open3D preflight that records the plain-environment `GLIBCXX_3.4.29` failure plus the successful `LD_LIBRARY_PATH=$CONDA_PREFIX/lib` workaround, add a dry-run runtime command plan, consolidate a runtime-readiness handoff packet, add a post-run extraction smoke validator for the next extraction smoke, add a dry-run geometry metric gate, add a guarded SMVP3D geometry evaluator entrypoint, and add a pipeline status summarizer. The current gate result is `metrics_allowed=false` because the post-run report is still `summary_is_dry_run` and five predicted SMVP3D meshes are missing; the evaluator therefore writes `blocked_by_gate` and no real Chamfer/F-score values. The current pipeline summary is `blocked_pending_extraction` with next action `run_non_dryrun_extraction_smoke_with_explicit_compute`. The no-compute P3 geometry implementation path is exhausted unless a new blocker or stale artifact is found; remaining geometry work is one non-dry-run extraction smoke with explicit runtime/GPU allocation, validator pass, and gate rerun before any OBJ-reference metric result can be produced.
- External baseline comparisons are missing.

## Definitions

### Full RC-RefGS code complete

`Full RC-RefGS code complete` means all are true:
- All method components are implemented behind safe defaults.
- Ablation variants are runnable through a documented launcher.
- Train/eval paths pass unit/static/smoke checks.
- No known runtime blocker for the primary experiment launcher.
- Outputs are reproducibly named and summarized.

### Complete experiment package

`Complete experiment package` means all are true:
- Matched base/rc/ablation runs are completed.
- Train/test metrics are produced.
- PSNR/SSIM/LPIPS summaries exist for all-pixel and reflective-region masks.
- Reflection-consistency summaries include pair settings and valid-pair reporting.
- Normal diagnostics are summarized.
- Material diagnostics are included if supported.
- Geometry metrics use only valid references.
- Multi-seed evidence exists (or one-seed caveat is explicit and preserved).
- Claim audit is updated after results.

## Prioritized Autonomous Task Queue

### P0 - Protocol and runtime hardening

Status: complete for the Python direct-command path as of 2026-05-19 19:47:45 CST.

- Python direct-command launcher added:
  - `scripts/run_rc_refgs_ablation_direct.py`
- Static/dry-run coverage added:
  - `tests/test_reflection_consistency_eval_static.py`
- Smoke verified:
  - `teapot/base`, one iteration, train/test reflection metrics, `num_pairs=1`, GPU 2.
- Keep `scripts/run_rc_refgs_ablation.sh` as syntax-verified only until its nested bash/conda CUDA behavior is repaired.

Verification gate:
- launcher smoke on one reduced scene/variant set (complete for Python direct launcher);
- `python -m unittest discover tests`;
- `bash -n scripts/run_rc_refgs_ablation.sh`;
- `git diff --check`.

### P1 - Code completeness

- Audit implementation against method contract:
  - intermediate buffers;
  - reflection consistency pair sampling;
  - visibility/confidence weighting;
  - stopgrad behavior;
  - schedule controls;
  - roughness-only control;
  - confidence-aware TSDF path.
- Add missing edge-case tests:
  - empty masks;
  - no valid pair camera;
  - missing render keys;
  - CPU import safety;
  - CUDA auto-device behavior;
  - deterministic seed/output naming.
- Add material diagnostic exporters for cross-view albedo/roughness/specular-map variance (if unsupported, record explicit Unsupported status).
- Add fixed pair-list support for reflection metric evaluation.

Verification gate:
- targeted RED->GREEN tests for each new edge case;
- full unittest pass;
- touched-file compile checks;
- deterministic output naming check.

### P2 - Experiment automation

- Create reproducible experiment manifest format:
  - scenes, variants, iterations, seeds, metrics, output roots, pair-list settings.
- Add orchestration for:
  - scenes: `teapot`, `toaster`, `car` first; then `ball`, `coffee`, `helmet` if available.
  - variants: `base`, `rc`, `wo_ref`, `wo_conf`, `rough_only`.
  - iterations: i300/i1000 validation, then 31000 full runs.
  - seeds: >= 3 before strong claim upgrade.
- Ensure every run uses `--eval` and produces train/test metrics.

Verification gate:
- manifest schema check;
- dry-run expansion log;
- one-scene reduced orchestration smoke;
- artifact existence check.

### P3 - Metrics completion

Status: mostly complete for corrected i300 `teapot/toaster/car` base/RC diagnostics; remaining P3 work is geometry-prerequisite work or optional fixed-pair/full-horizon reruns, not material/rendering plumbing.

- Reflection consistency:
  - fixed pair lists implemented;
  - `max_pairs`, `max_angle_deg`, valid-pair counts in outputs.
- Rendering:
  - PSNR/SSIM/LPIPS for all-pixel and reflective-region masks are summarized for corrected i300 full splits.
- Normal diagnostics:
  - full split;
  - raw GT convention;
  - missing-normal counts.
- Material diagnostics:
  - cross-view diffuse/albedo variance, roughness variance, and specular consistency are summarized for corrected i300 full splits;
  - keep as diagnostic-only unless longer-horizon/multi-seed evidence supports a material-quality claim.
- Geometry:
  - do not use RefNeRF `points3d.ply` as GT;
  - add SMVP3D loader/transform support first;
  - evaluate extracted meshes against valid OBJ references only.

Verification gate:
- metrics JSON schema checks;
- per-metric summary artifacts in JSON+Markdown;
- explicit Unsupported markers where prerequisites remain missing.

### P4 - Full experiment execution

- Base/RC `i31000` single-seed matrix closure is complete; keep the reconciled completion and summary artifacts as the baseline reference.
- Next highest-value runtime tasks are post-P4 scope only (claim exactly one per window):
  - run matched full ablations;
  - run multi-seed repeats;
  - optionally expand scene set and SMVP3D geometry experiments.
- Launch gate for post-P4 runtime tasks: require explicit compute allocation, process/GPU safety checks, and strict one-claim scope discipline.
- If compute is not explicitly allocated, do not relaunch completed base/RC cells; use bounded docs/status reconciliation or geometry-prerequisite routing checks instead.

Verification gate:
- run-matrix completion table;
- missing-run detector returns zero for required matrix;
- summaries regenerated with reproducible command.

### P5 - Claim audit and manuscript integration

- Full-horizon evidence artifacts now exist for the matched `teapot/toaster/car` base/RC `i31000` matrix, so P5 claim-audit routing is eligible.
- Update claim audit and manuscript integration drafts.
- Upgrade claims only when acceptance thresholds are satisfied.
- Preserve NO-GO boundaries for manuscript/scientific, broad rendering, geometry, material, external-superiority, causal, ablation, and multi-seed claims until evidence supports upgrades.

Verification gate:
- claim-audit artifact includes Supported / Mixed / Unsupported tags;
- forbidden-claim lint checks pass;
- evidence links resolve to concrete JSON/Markdown artifacts.

## Per-Task Verification Gates (Global Minimum)

Every execution task must run:
- targeted task verification commands;
- `conda run -n ref_gs python -m unittest discover tests`;
- `bash -n scripts/run_rc_refgs_ablation.sh` (launcher syntax gate);
- `git diff --check`.

If environment blocks a command, log failure reason and downgrade decision to CONDITIONAL GO.

## Per-Claim Acceptance Thresholds

- Reflection diagnostic claim:
  - Allowed when matched scene/split rows show lower reflection-consistency under identical settings.
- Rendering aggregate claim:
  - Requires non-negative or explicitly justified cross-scene PSNR/SSIM/LPIPS trends.
- Geometry claim:
  - Requires extracted meshes and valid reference metrics (OBJ-based), never RefNeRF `points3d.ply` as GT.
- Causal claim (`L_ref` attribution):
  - Requires complete matched ablation table and acceptance-threshold pass.
- External-superiority claim:
  - Requires matched baseline protocol and reproducible comparative evidence.

Until thresholds are met: keep claim state as Supported / Mixed / Unsupported with NO-GO boundaries.

## Model Routing Rules

- `gpt-5.3-codex`: code implementation, test work, launch/runtime hardening, experiment execution, metrics generation/summaries.
- `gpt-5.5`: claim audit, conservative manuscript integration, citation-aware prose updates.

Switching rule:
- Do not SWITCH MODEL for manuscript work during P0-P4 unless explicitly requested.
- SWITCH MODEL to gpt-5.5 during P5 only when fresh full-horizon evidence artifacts are present.

## Decision Policy

- GO: roadmap task completed, verification passes, next-step ambiguity removed.
- CONDITIONAL GO: task completed but non-critical verification blocked by environment or known unresolved prerequisite.
- NO-GO: ambiguous roadmap state, unreleased claim, or missing required protocol artifacts.
- SWITCH MODEL: only for P5 claim-audit/manuscript windows after evidence refresh.
