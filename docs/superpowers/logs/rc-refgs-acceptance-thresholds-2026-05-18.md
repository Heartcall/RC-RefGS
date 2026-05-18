# RC-RefGS Acceptance Thresholds and Paper-Language Guardrails

Date: 2026-05-18 05:06:23 CST

Scope: conservative acceptance thresholds for claims using the current i300 evidence only.

## Current Protocol

- Scenes: `teapot`, `toaster`, `car`.
- Iterations: 300.
- Seeds: one.
- Splits: train and held-out test.
- Reflection metric: `max_pairs=10`, `max_angle_deg=180`.
- LPIPS: unavailable/skipped.
- Mesh/reference geometry metrics: unavailable.
- Ablations: unavailable.

## Claim Gates

| Claim | Current status | Minimum threshold | Current evidence | Allowed strength |
| --- | --- | --- | --- | --- |
| Reflection-consistency diagnostic | Pass | Every scene/split row must have lower RC mean reflection-consistency error under identical split, iteration, and pair settings | Six of six rows pass on `teapot`, `toaster`, and `car` | Diagnostic-supported |
| Method-level reflection consistency | Conditional | Repeat at longer horizons on the intended main scene set; preserve identical seeds/splits/iterations; report pair counts and sampling settings; require no unexplained scene-level regressions | Current result is consistent but short-run and one-seed | Conditional |
| Overall rendering quality | Fail | LPIPS available, and PSNR/SSIM/LPIPS trends non-negative or explicitly explained across scenes/splits | PSNR/SSIM are mixed; LPIPS skipped | Table-only |
| Normal diagnostics | Pass with small-effect warning | All rows improve MAE and cosine; GT normal convention and missing-normal counts reported | Six of six rows improve with raw GT normals and zero missing normals, but small deltas | Directional diagnostic |
| Geometry quality | Fail | Extract comparable meshes and evaluate against valid reference geometry, such as SMVP3D OBJ, with Chamfer/F-score or equivalent | No extracted RefNeRF meshes; RefNeRF `points3d.ply` is random init; SMVP3D needs loader/runtime work | Forbidden |
| Causal attribution | Fail | Matched ablations for `w/o L_ref`, `w/o specular confidence`, and roughness-only regularization | No ablation metrics available | Hypothesis-only |

## Safe Paper Language

Contribution bullet:

> [Evidence] We add a gated cross-view reflection-consistency objective to Ref-GS while preserving the original representation and renderer. [Evidence] In short i300 sanity runs on `teapot`, `toaster`, and `car`, the RC setting lowers the measured reprojected reflection-consistency error on both train and held-out test splits relative to matched Ref-GS baselines. [Qualifier] These results support the intended diagnostic target and are not evidence of broad rendering or geometry improvement.

Results sentence:

> [Evidence] Across the three i300 sanity scenes, RC-RefGS reduces the measured reflection-consistency error in all six train/test rows under `max_pairs=10` and `max_angle_deg=180`. [Qualifier] PSNR/SSIM trends are mixed and LPIPS is unavailable, so we report these metrics without claiming overall novel-view synthesis gains.

Normal diagnostic sentence:

> [Evidence] Full-split raw-convention normal diagnostics improve MAE and mean cosine in all six scene/split rows. [Qualifier] The deltas are small and are treated as diagnostics rather than geometry-quality evidence.

Required limitation sentence:

> [Qualifier] Current evidence is limited to three short-run scenes, one seed, sampled reflection pairs, no LPIPS, no external baselines, no ablation table, and no mesh/reference-geometry metric.

## Forbidden Language

- Do not claim improved overall novel-view synthesis quality.
- Do not claim LPIPS improvement.
- Do not claim improved mesh quality, surface reconstruction, or geometry quality.
- Do not claim material decomposition improvement.
- Do not claim superiority over external methods or paper baselines.
- Do not claim the observed changes are caused specifically by `L_ref` until ablations are available.
- Do not use RefNeRF `points3d.ply` as ground-truth geometry.

## Upgrade Thresholds

Reflection claim upgrade:

- Run longer-horizon matched baseline/RC experiments.
- Keep identical scene/split/iteration/seed settings.
- Report `max_pairs`, `max_angle_deg`, valid pair counts, and per-scene deltas.
- Require no unexplained scene-level regressions before removing the short-run caveat.

Rendering claim upgrade:

- Run LPIPS with cached or explicitly approved weights.
- Report all-pixel and reflective-region PSNR/SSIM/LPIPS.
- Require non-negative or explicitly explained trends before any aggregate rendering-quality claim.

Geometry claim upgrade:

- Fix mesh extraction/runtime prerequisites.
- Add SMVP3D loader or deterministic `cameras.npz` to Ref-GS transform conversion.
- Evaluate extracted meshes against OBJ references with Chamfer/F-score or equivalent.
- Keep RefNeRF `points3d.ply` out of ground-truth geometry evaluation.

Causality claim upgrade:

- Run matched `w/o L_ref`, `w/o specular confidence`, and roughness-only regularization ablations.
- Keep scene/split/iteration/seed settings aligned with the main RC protocol.
- Attribute effects to `L_ref` only when the ablation table supports that attribution.

## Decision

**CONDITIONAL GO** for conservative paper language centered on the reflection-consistency diagnostic.

**NO-GO** for overall rendering-quality, LPIPS, geometry, surface-reconstruction, material-decomposition, external-superiority, or causal claims.

**SWITCH MODEL** to gpt-5.5 is still recommended for final manuscript prose polishing if that is the next task.
