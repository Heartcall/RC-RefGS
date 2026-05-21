# RC-RefGS Full Implementation Status

Date: 2026-05-19
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
| Core RC training loss | Supported | `train.py`, `tests/test_rc_refgs_training_static.py` | Edge-case tests (empty masks/no pair/missing keys) | Add P1 edge-case coverage | CONDITIONAL GO, NO-GO for causal claims |
| Roughness-only control | Supported | Reduced ablation summary `2026-05-19` (30/30) | Full-horizon + multi-seed runs | Include in P4 full matrix | CONDITIONAL GO, NO-GO for causal claims |
| Confidence-aware TSDF | Supported (code path) / Mixed (evidence) | `utils/mesh_utils.py`, static tests | Runtime geometry validation with valid references | P1/P3 runtime hardening + SMVP3D path | NO-GO for geometry claims |
| Reflection metric | Supported | `metrics/reflection_consistency_eval.py`, reduced summary | Fixed pair-list mode + richer pair stats in outputs | Implement P1/P3 fixed-pair reporting | CONDITIONAL GO |
| LPIPS/render metrics | Mixed | `rc-refgs-render-quality-summary-2026-05-18-lpips.{md,json}` | Longer horizon + multi-seed + stable trend explanation | P3/P4 full metric package | NO-GO for aggregate rendering claims |
| Normal metrics | Supported (diagnostic) | `rc-refgs-normal-quality-summary-2026-05-18.{md,json}` | Broader scenes/horizons and geometry linkage | Continue P3 diagnostics | CONDITIONAL GO, NO-GO for geometry claims |
| Reduced ablations | Supported | `rc-refgs-reduced-ablation-summary-2026-05-19.{md,json}` | Extend to i300/i1000/full 31000 and multi-seed | P2/P4 orchestration + full runs | CONDITIONAL GO, NO-GO for causal claims |
| Primary ablation launcher | Supported (Python direct) / Mixed (bash wrapper) | `scripts/run_rc_refgs_ablation_direct.py`, `tests/test_reflection_consistency_eval_static.py`, one-variant launcher smoke under `/tmp/rc_refgs_direct_launcher_smoke_20260519_1943_gpu2` | Bash wrapper remains syntax-only under nested bash/conda; future runs should prefer Python direct launcher | P1 edge-case coverage, then P2 manifest orchestration | CONDITIONAL GO for launcher use; NO-GO for bash-wrapper runtime claims |
| Full 31000 runs | Unsupported | N/A | Execute matched base/rc/ablation matrix | P4 execution | NO-GO for strong performance claims |
| Multi-seed runs | Unsupported | N/A | >=3 seeds for matched matrix | P4 multi-seed schedule | NO-GO for strong/causal claims |
| Material diagnostics | Unsupported | N/A | Export and summarize albedo/roughness/specular variance | P1/P3 material diagnostics | NO-GO for material claims |
| Geometry/SMVP3D | Unsupported | `rc-refgs-geometry-feasibility-2026-05-18.{md,json}` | Loader/transform/runtime + mesh/reference metrics | P3 geometry prerequisites | NO-GO for geometry claims |
| External baselines | Unsupported | N/A | Comparable protocol and reproducible comparisons | P4/P5 after core package | NO-GO for external-superiority claims |
| Manuscript claim audit | Supported (conservative) | claim framing + thresholds packets | Refresh after new full evidence only | P5 with gpt-5.5 | SWITCH MODEL only in P5 |

## Current Decision

- Overall execution state: CONDITIONAL GO for roadmap-driven engineering; P0 Python direct launcher hardening is complete for reduced launcher use.
- Claim boundary: NO-GO for broad rendering, geometry, material, external-superiority, and causal upgrades.
- Model routing: SWITCH MODEL only for P5 claim audit/manuscript integration after new evidence artifacts exist.
