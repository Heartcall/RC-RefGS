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
- Normal-quality full-split summary artifact available:
  - `docs/superpowers/logs/rc-refgs-normal-quality-summary-2026-05-18.{md,json}`
- Reduced ablation summary is complete (30/30 cells, no missing cells):
  - `docs/superpowers/logs/rc-refgs-reduced-ablation-summary-2026-05-19.{md,json}`
- Conservative claim framing and thresholds exist:
  - `docs/superpowers/logs/rc-refgs-claim-framing-packet-2026-05-18.md`
  - `docs/superpowers/logs/rc-refgs-acceptance-thresholds-2026-05-18.md`

## Current Blockers

- Bash script launcher reliability is still Mixed in nested bash/conda contexts; use the Python direct-command launcher as the primary launcher until the bash wrapper is runtime repaired.
- Full-horizon matched runs (31000) are not executed for the full matrix.
- Multi-seed evidence is missing.
- Material diagnostics are missing.
- Geometry metrics are blocked pending valid SMVP3D loader/transform/runtime path.
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

- Reflection consistency:
  - fixed pair lists;
  - `max_pairs`, `max_angle_deg`, valid-pair counts in outputs.
- Rendering:
  - PSNR/SSIM/LPIPS for all-pixel and reflective-region masks.
- Normal diagnostics:
  - full split;
  - raw GT convention;
  - missing-normal counts.
- Material diagnostics:
  - cross-view albedo variance, roughness variance, specular consistency (if supported).
- Geometry:
  - do not use RefNeRF `points3d.ply` as GT;
  - add SMVP3D loader/transform support first;
  - evaluate extracted meshes against valid OBJ references only.

Verification gate:
- metrics JSON schema checks;
- per-metric summary artifacts in JSON+Markdown;
- explicit Unsupported markers where prerequisites remain missing.

### P4 - Full experiment execution

- Run matched full 31000 base/rc first on `teapot`/`toaster`/`car`.
- Run matched full ablations.
- Run multi-seed repeats.
- Optionally expand scene set and SMVP3D geometry experiments.
- Summarize results into machine-readable JSON and manuscript-ready Markdown.

Verification gate:
- run-matrix completion table;
- missing-run detector returns zero for required matrix;
- summaries regenerated with reproducible command.

### P5 - Claim audit and manuscript integration

- Switch to gpt-5.5 only after new evidence artifacts exist.
- Update claim audit and manuscript integration drafts.
- Upgrade claims only when acceptance thresholds are satisfied.
- Preserve NO-GO boundaries for rendering, geometry, material, external-superiority, and causal claims until evidence supports upgrades.

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
- SWITCH MODEL to gpt-5.5 during P5 only when fresh evidence artifacts are present.

## Decision Policy

- GO: roadmap task completed, verification passes, next-step ambiguity removed.
- CONDITIONAL GO: task completed but non-critical verification blocked by environment or known unresolved prerequisite.
- NO-GO: ambiguous roadmap state, unreleased claim, or missing required protocol artifacts.
- SWITCH MODEL: only for P5 claim-audit/manuscript windows after evidence refresh.
