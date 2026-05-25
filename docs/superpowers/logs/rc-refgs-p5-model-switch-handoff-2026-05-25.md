# RC-RefGS P5 Model-Switch Handoff

Date: 2026-05-25 14:03:01 CST

Purpose: handoff packet for a gpt-5.5 P5 claim-audit/manuscript-integration window after completion and reconciliation of the full-horizon `teapot/toaster/car` base/RC `i31000` matrix. This packet packages current evidence and boundaries only. It adds no experiments, code changes, manuscript prose edits, metric computation, or stronger claims.

## Current Protocol State

- P4 base/RC full-horizon single-seed matrix is complete and reconciled:
  - `6/6` cells complete.
  - `0/18` expected closeout artifacts missing.
  - Artifacts are recorded in `docs/superpowers/logs/rc-refgs-p4-base-rc-i31000-completion-status-2026-05-25.json`.
- Full `i31000` base-vs-RC reflection summary is available:
  - `docs/superpowers/logs/rc-refgs-p4-i31000-base-vs-rc-reflection-summary-2026-05-25.json`
  - `docs/superpowers/logs/rc-refgs-p4-i31000-base-vs-rc-reflection-summary-2026-05-25.md`
- Manual P4 closeout provenance is recorded in:
  - `docs/superpowers/logs/rc-refgs-p4-manual-artifact-reconciliation-2026-05-25.json`
- P5 claim audit/manuscript integration is now eligible under the roadmap model-routing rule, but should be performed by gpt-5.5.

## Read Order For gpt-5.5

1. `docs/superpowers/logs/rc-refgs-p4-i31000-base-vs-rc-reflection-summary-2026-05-25.md`
   - Use as the current full-horizon reflection evidence summary.
   - Preserve its boundary: single-seed full-horizon reflection summary only.
2. `docs/superpowers/logs/rc-refgs-p4-i31000-base-vs-rc-reflection-summary-2026-05-25.json`
   - Use for exact scene/split deltas and aggregate values.
3. `docs/superpowers/logs/rc-refgs-p4-base-rc-i31000-completion-status-2026-05-25.json`
   - Use to confirm `6/6` cells complete and `0/18` missing artifacts.
4. `docs/superpowers/logs/rc-refgs-p4-manual-artifact-reconciliation-2026-05-25.json`
   - Use for closeout provenance, including manual reruns and the `car_rc` metrics-only recovery.
5. `docs/superpowers/logs/rc-refgs-i300-three-scene-render-quality-full-summary-2026-05-21.md`
   - Use for corrected i300 PSNR/SSIM/LPIPS context.
   - Keep broad rendering-quality evidence as Mixed / Unsupported.
6. `docs/superpowers/logs/rc-refgs-i300-material-quality-full-summary-2026-05-21.md`
   - Use for material diagnostics only.
   - Keep material-quality claims as Mixed / Unsupported.
7. `docs/superpowers/logs/rc-refgs-reduced-ablation-summary-2026-05-19.md`
   - Use as preliminary reduced-ablation workflow evidence only.
   - Do not convert i20 reduced ablations into causal proof.
8. `docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md`
   - Use as the older manuscript-facing scaffold that may contain stale evidence statements.
9. `docs/superpowers/logs/rc-refgs-manuscript-evidence-refresh-checklist-2026-05-19.md`
   - Use as the earlier stale-statement checklist, then extend it with the full-horizon P4 evidence.
10. `docs/superpowers/logs/rc-refgs-claim-framing-packet-2026-05-18.md` and `docs/superpowers/logs/rc-refgs-acceptance-thresholds-2026-05-18.md`
   - Use as conservative claim-boundary and acceptance-gate references.

## Full-Horizon Reflection Evidence

Allowed factual statements:

- The matched `teapot/toaster/car` base/RC matrix is complete at `i31000` for train and test reflection-consistency evaluation.
- In the full-horizon single-seed summary, RC has lower mean reflection-consistency than base in all three train scenes and all three test scenes.
- Aggregate `rc - base` mean reflection-consistency deltas are:
  - train: `-0.12140093434912462`
  - test: `-0.04473169764969498`
- Aggregate `rc - base` reflective PSNR deltas are:
  - train: `+0.21495660146077591`
  - test: `+0.1319833119710291`
- Reflective PSNR is higher for RC in `3/3` train scenes and `2/3` test scenes.

Required qualifiers:

- These are single-seed results.
- The matrix covers only `teapot`, `toaster`, and `car`.
- The summary is a reflection-diagnostic evidence update, not a broad rendering, geometry, material, external-superiority, ablation, multi-seed, or causal proof.

## Current Claim Tags

Supported under current scope:

- RC training/evaluation path is implemented and exercised.
- Reflection-consistency metric and full-horizon base/RC `i31000` summary are available for the three-scene single-seed matrix.
- Reduced i20 ablation workflow is complete as a preliminary diagnostic matrix.

Mixed / Unsupported:

- Broad rendering-quality gains remain Mixed / Unsupported.
- Material-quality claims remain Mixed / Unsupported.
- Causal attribution to `L_ref`, confidence weighting, or roughness smoothing remains Unsupported.
- Multi-seed robustness remains Unsupported.

Unsupported / NO-GO:

- Geometry or surface-reconstruction quality claims.
- External-superiority claims.
- Manuscript/scientific claim upgrades beyond the current evidence tags.

## Forbidden Claim Boundary

The next P5 window must not claim:

- broad novel-view rendering improvement,
- aggregate LPIPS improvement,
- mesh-quality, surface-reconstruction, or geometry-quality improvement,
- material-decomposition improvement,
- superiority over external methods or paper baselines,
- causal proof that `L_ref` caused the observed metric changes,
- causal proof that confidence weighting is necessary or superior,
- causal proof that roughness smoothing explains the reflection metric movement,
- multi-seed robustness,
- full-ablation support beyond the existing reduced i20 diagnostic matrix,
- RefNeRF `points3d.ply` as ground-truth geometry.

## Allowed P5 Work

- Refresh the claim audit using the new P4 full-horizon reflection summary.
- Update stale manuscript-integration draft statements that still imply full-horizon evidence is missing.
- Preserve `Supported`, `Mixed`, and `Unsupported` tags or explicit equivalents.
- Preserve NO-GO boundaries unless acceptance thresholds are newly satisfied by verified evidence.
- Add citation TODOs or source-map entries only when clearly marked and traceable.

## Disallowed P5 Work

- Do not launch training, ablations, multi-seed runs, geometry metrics, or external comparisons from the manuscript window.
- Do not rewrite evidence boundaries into stronger claims.
- Do not use P4 reflection-only evidence to justify rendering, material, geometry, external-superiority, or causal claims.
- Do not remove one-seed, three-scene, no-full-ablation, no-multi-seed, and no-valid-geometry caveats.

## Verification Checklist For Next Window

- Confirm the P4 completion-status JSON still reports `completed_cells=6` and `missing_expected_artifacts=0`.
- Confirm the reflection summary JSON still reports RC lower mean reflection consistency on `3/3` train scenes and `3/3` test scenes.
- Run a forbidden-claim confinement check for broad rendering, aggregate LPIPS, geometry, material, external-superiority, causal, ablation, and multi-seed claims.
- If manuscript files are edited, run the repository verification gates required by the roadmap:
  - `conda run -n ref_gs python -m unittest discover tests`
  - `bash -n scripts/run_rc_refgs_ablation.sh`
  - `git diff --check`
- Update the coordination board and autonomous log with the actual P5 outcome.

## Decision

**SWITCH MODEL** to gpt-5.5 for P5 claim audit/manuscript integration using this handoff packet and the listed evidence artifacts.

**CONDITIONAL GO** for conservative claim-audit updates that preserve evidence tags and forbidden-claim boundaries.

**NO-GO** for broad rendering, aggregate LPIPS, geometry, surface reconstruction, material, external-superiority, causal, full-ablation, multi-seed, manuscript/scientific claim upgrades, or any runtime expansion in the P5 writing window.
