# RC-RefGS Full Implementation Status

Date: 2026-05-22
Window intent: protocol tracking for full implementation + complete experiments.

Claim legend:
- Supported: evidence-backed under current scope.
- Mixed: partially favorable or conflicting evidence.
- Unsupported: missing prerequisites/evidence.

Decision legend:
- NO-GO: do not upgrade claim strength.
- CONDITIONAL GO: proceed with scoped engineering work.
- SWITCH MODEL: manuscript/claim-audit routing only after evidence refresh.

| Component | Current status | Evidence artifact | Missing work | Next task | Claim impact |
| --- | --- | --- | --- | --- | --- |
| Core RC training loss | Supported | `train.py`, `tests/test_rc_refgs_training_static.py`, `tests/test_reflection_consistency.py` | Longer-horizon and multi-seed evidence, not P1 helper coverage | Include in P4 full matrix only when compute is explicitly allocated | CONDITIONAL GO, NO-GO for causal claims |
| Roughness-only control | Supported | Reduced ablation summary `2026-05-19` (30/30) | Full-horizon + multi-seed runs | Include in P4 full matrix | CONDITIONAL GO, NO-GO for causal claims |
| Confidence-aware TSDF | Supported (code path) / Mixed (evidence) | `utils/mesh_utils.py`, static tests | Runtime geometry validation with valid references | P1/P3 runtime hardening + SMVP3D path | NO-GO for geometry claims |
| Reflection metric | Supported | `metrics/reflection_consistency_eval.py`, `tests/test_reflection_consistency_eval_static.py`, reduced summary; fixed pair-list mode and `valid_pair_count` output are implemented | Longer-horizon/multi-seed evidence and optional fixed-pair full-matrix reruns | Continue P3/P4 metric package, not P1 fixed-pair plumbing | CONDITIONAL GO |
| LPIPS/render metrics | Mixed / Unsupported for broad rendering gains | Corrected i300 LPIPS-enabled three-scene summary `rc-refgs-i300-three-scene-render-quality-full-summary-2026-05-21.{md,json}`; matching `render_quality_both_iter300.json` files for `teapot`, `toaster`, and `car` base/RC | Longer horizon, multi-seed, and a stable non-negative PSNR/SSIM/LPIPS trend would be required before any aggregate rendering claim | Keep as diagnostic table; next evidence work is P4 full-horizon only with explicit compute allocation | NO-GO for aggregate or broad rendering-quality claims |
| Normal metrics | Supported (diagnostic) | `rc-refgs-normal-quality-summary-2026-05-18.{md,json}`, `metrics/normal_quality_eval.py`, `tests/test_normal_quality_eval_static.py` | Broader scenes/horizons and geometry linkage | Keep as diagnostic table; evaluator CUDA auto-device hardening is complete | CONDITIONAL GO, NO-GO for geometry claims |
| Reduced ablations | Supported | `rc-refgs-reduced-ablation-summary-2026-05-19.{md,json}` | Extend to i300/i1000/full 31000 and multi-seed | P2/P4 orchestration + full runs | CONDITIONAL GO, NO-GO for causal claims |
| Primary ablation launcher | Supported (Python direct) / Mixed (bash wrapper) | `scripts/run_rc_refgs_ablation_direct.py`, `tests/test_reflection_consistency_eval_static.py`, one-variant launcher smoke under `/tmp/rc_refgs_direct_launcher_smoke_20260519_1943_gpu2` | Bash wrapper remains syntax-only under nested bash/conda; future runs should prefer Python direct launcher | P1 edge-case coverage, then P2 manifest orchestration | CONDITIONAL GO for launcher use; NO-GO for bash-wrapper runtime claims |
| Full 31000 runs | Unsupported (P4 base/RC preflight ready; 2026-05-22 launch-safety audit says no launch without allocated compute) | P4 base/RC manifest and dry-run summary `rc-refgs-p4-base-rc-i31000-manifest-2026-05-22.json`, `rc-refgs-p4-base-rc-i31000-dryrun-summary-2026-05-22.json`, preflight note `rc-refgs-p4-full-horizon-preflight-2026-05-22.md`, and launch-safety audit `rc-refgs-p4-launch-safety-audit-2026-05-22.md` | Execute matched base/rc full-horizon matrix, then summarize before ablations | P4 base/RC execution only when compute is explicitly allocated | CONDITIONAL GO for launch readiness; NO-GO for strong performance claims |
| Multi-seed runs | Unsupported | N/A | >=3 seeds for matched matrix | P4 multi-seed schedule | NO-GO for strong/causal claims |
| Material diagnostics | Mixed / Unsupported for material-quality claims | `metrics/material_quality_eval.py`, `metrics/summarize_material_quality.py`, `rc-refgs-i300-material-quality-smoke-summary-2026-05-20.{md,json}`, corrected i300 full-split summary `rc-refgs-i300-material-quality-full-summary-2026-05-21.{md,json}` | Interpretation thresholds, longer horizon, multi-seed evidence, and linkage to rendering/geometry outcomes | Keep as diagnostic table; next runtime work is P4 full-horizon only with explicit compute allocation | NO-GO for material claims |
| Geometry/SMVP3D | Unsupported | `rc-refgs-geometry-feasibility-2026-05-18.{md,json}` | Loader/transform/runtime + mesh/reference metrics | P3 geometry prerequisites | NO-GO for geometry claims |
| External baselines | Unsupported | N/A | Comparable protocol and reproducible comparisons | P4/P5 after core package | NO-GO for external-superiority claims |
| Manuscript claim audit | Supported (conservative) | claim framing + thresholds packets | Refresh after new full-horizon evidence only | P5 with gpt-5.5 after full-horizon artifacts exist | SWITCH MODEL only in P5 after fresh full-horizon evidence |

## Current Decision

- Overall execution state: CONDITIONAL GO for roadmap-driven engineering and bounded evidence/status refresh work; recent P1 edge-case/fixed-pair/CUDA auto-device hardening, corrected i300 render/material summaries, and P4 preflight/no-launch boundaries are reflected here.
- Render-quality boundary: Mixed / Unsupported for broad rendering-quality gains. Corrected i300 full-split LPIPS-enabled evidence across `teapot`, `toaster`, and `car` shows full PSNR improves in only 3/6 scene/split rows, full SSIM improves in 0/6 rows, and full LPIPS is worse in 5/6 rows.
- Material-diagnostic boundary: Mixed / Unsupported for material-quality claims. Corrected i300 full-split material diagnostics across `teapot`, `toaster`, and `car` show full diffuse variance increases in 6/6 rows, full roughness variance increases in 4/6 rows, full specular variance increases in 2/6 rows and decreases in 4/6 rows, and reflective specular/diffuse ratio is split 3/6 positive and 3/6 negative.
- P4 execution boundary: the `31000` `teapot/toaster/car` base/RC matrix is preflighted only; the dry-run summary expands 6 jobs and 18 expected pre-run missing artifacts, and the 2026-05-22 launch-safety audit kept the matrix unlaunched because compute was not explicitly allocated and most GPUs were occupied or active. This is launch-readiness/status evidence, not full-horizon performance evidence; do not repeat opportunistic no-launch audits unless GPU/process state or protocol artifacts change.
- Claim boundary: NO-GO for manuscript, scientific, broad rendering, geometry, material, external-superiority, causal, ablation, and multi-seed upgrades.
- Model routing: SWITCH MODEL only for P5 claim audit/manuscript integration after fresh full-horizon evidence artifacts exist.
