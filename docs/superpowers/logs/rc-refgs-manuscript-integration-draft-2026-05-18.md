# RC-RefGS Conservative Manuscript Integration Draft

Date: 2026-05-18 10:35:08 CST

Scope: manuscript-facing integration draft centered only on the currently supported reflection-consistency diagnostic. This artifact uses existing evidence only; it does not add experiments, training changes, or stronger claims.

Source evidence artifacts:

- `docs/superpowers/logs/rc-refgs-claim-audit-2026-05-17.md`
- `docs/superpowers/logs/rc-refgs-claim-framing-packet-2026-05-18.md`
- `docs/superpowers/logs/rc-refgs-acceptance-thresholds-2026-05-18.md`
- `docs/superpowers/logs/rc-refgs-manuscript-prose-skeleton-2026-05-18.md`
- `docs/superpowers/logs/rc-refgs-render-quality-summary-2026-05-17.md`
- `docs/superpowers/logs/rc-refgs-normal-quality-summary-2026-05-18.md`
- `docs/superpowers/logs/rc-refgs-geometry-feasibility-2026-05-18.md`

## 1. Title

RC-RefGS: Cross-View Reflection-Consistency Diagnostics for Ref-GS

## 2. Abstract

[Citation: Ref-GS code] Ref-GS models glossy scenes with 2D Gaussian surfels, deferred material buffers, Sph-Mip directional encoding, and a specular MLP. [Reasoning] In the baseline formulation, final RGB and normal regularization can be satisfied by coupled changes to normals, roughness, learned features, and view-dependent specular prediction, so reflected appearance is not explicitly constrained to agree across views. [Citation: this implementation] RC-RefGS preserves the base representation and renderer while adding exposed intermediate buffers, a gated cross-view reflection-consistency objective, and a matching reflection-consistency diagnostic. [Supported] Under the current short i300 sanity protocol on `teapot`, `toaster`, and `car`, RC-RefGS lowers measured reprojected reflection-consistency error relative to matched Ref-GS baselines on all train and held-out test rows, using `max_pairs=10` and `max_angle_deg=180`. [Mixed] Standard PSNR/SSIM results are scene-dependent and LPIPS is unavailable. [Unsupported] Current evidence does not support broad rendering-quality, geometry, reconstruction, material, external-superiority, or causal claims. [Reasoning] The manuscript framing should therefore present RC-RefGS as a reflection-consistency diagnostic and targeted training signal, with stronger claims gated on longer runs, LPIPS, ablations, and mesh/reference-geometry metrics.

## 3. Contribution Bullets

1. [Citation: this implementation] Expose Ref-GS intermediate rendering buffers needed to inspect view-dependent specular predictions without replacing the base Gaussian representation, Sph-Mip encoding, or specular MLP.
2. [Citation: this implementation] Add a disabled-by-default, gated cross-view reflection-consistency objective that compares confident reprojected specular predictions across a sampled view pair.
3. [Citation: this implementation] Provide a reflection-consistency evaluation path that reports mean reprojected reflection-consistency error, reflective-region PSNR, and pair counts.
4. [Supported] Show that, in three short i300 sanity runs, the RC setting lowers measured reflection-consistency error on six of six scene/split rows relative to matched baselines.
5. [Mixed] Report PSNR/SSIM and normal-map diagnostics as context, while keeping their interpretation caveated because rendering metrics are mixed, LPIPS is missing, and normal diagnostics are small diagnostic-only effects.

## 4. Method Framing

[Citation: Ref-GS code] The baseline renderer computes reflected directions, directional features, learned Gaussian feature interactions, and specular radiance before composing the final image. [Reasoning] Because supervision is applied mainly through rendered appearance and normal consistency, a reflective region may fit the observed views while still leaving cross-view specular agreement under-specified. [Citation: this implementation] RC-RefGS introduces a reflection-consistency path that renders a source and target view, reprojects confident source pixels, samples the target specular response, and penalizes disagreement under visibility and confidence checks. [Reasoning] This should be described as an auxiliary diagnostic-centered consistency signal, not as a new material decomposition model or a replacement renderer.

The method description should keep three boundaries explicit:

- [Supported] The base representation and renderer are preserved.
- [Supported] The added objective and evaluator target measured view-pair reflection-consistency error.
- [Unsupported] The current implementation evidence does not establish improved surface quality, material decomposition, or external-method superiority.

## 5. Experimental Protocol

Current evidence protocol:

- Scenes: `teapot`, `toaster`, `car`.
- Dataset family: RefNeRF-style data under `/data/liuly/dataset/3DGS/refnerf`.
- Training horizon: 300 iterations.
- Seeds: one.
- Splits: train and held-out test, with split preservation via `--eval`.
- Reflection diagnostic: `metrics/reflection_consistency_eval.py`.
- Reflection pair settings: `max_pairs=10`, `max_angle_deg=180`, with `num_pairs=10` for every reported baseline/RC row.
- Rendering metrics: `metrics/render_quality_eval.py --split both --mask_mode both --skip_lpips`.
- Normal diagnostics: full-split raw RefNeRF normal convention using `metrics/normal_quality_eval.py --split both --normal_key rend_normal --gt_normal_space raw`.
- Geometry metrics: not run; current RefNeRF i300 outputs have no extracted meshes, and RefNeRF `points3d.ply` is random initialization data in this repo.
- Ablations: not run; no `w/o L_ref`, `w/o specular confidence`, or roughness-only table is available.

Protocol reporting requirements:

- Always report scene, split, iteration count, seed count, pair count, `max_pairs`, and `max_angle_deg`.
- Keep reflection-consistency claims scoped to the measured diagnostic under this short-run protocol.
- Report PSNR/SSIM as mixed context, not as an aggregate quality result.
- State that LPIPS, mesh/reference-geometry metrics, and ablations are missing.

## 6. Results Framing

Reflection consistency:

[Supported] RC-RefGS lowers measured reprojected reflection-consistency error on all six audited rows:

| Scene | Split | Baseline reflection error | RC reflection error | Label |
| --- | --- | ---: | ---: | --- |
| `teapot` | train | 0.0039707922 | 0.0039400090 | Supported |
| `teapot` | test | 0.0018443021 | 0.0018346125 | Supported |
| `toaster` | train | 0.0030678714 | 0.0029527844 | Supported |
| `toaster` | test | 0.0025387909 | 0.0024728895 | Supported |
| `car` | train | 0.0022612946 | 0.0021638940 | Supported |
| `car` | test | 0.0012749511 | 0.0012496432 | Supported |

Rendering context:

[Mixed] Standard PSNR/SSIM is not uniformly favorable. `teapot` improves in full-image and reflective-region PSNR/SSIM. `toaster` has small PSNR decreases and small SSIM increases. `car` has small PSNR/SSIM decreases. LPIPS was skipped, so no LPIPS comparison is available.

Normal diagnostic context:

[Mixed] Full-split raw-convention normal diagnostics improve MAE and mean cosine on all six rows, but the deltas are small, especially for `toaster` and `car`. These results should be treated as normal-map diagnostics only, not as mesh or reference-geometry evidence.

Geometry and causality context:

[Unsupported] Current RefNeRF i300 outputs do not include extracted meshes. RefNeRF `points3d.ply` is not valid ground-truth geometry in this repo. SMVP3D has OBJ references in principle but needs loader/runtime work before comparable metrics can be run. [Unsupported] No ablation table is available, so causal attribution beyond the matched RC-vs-baseline contrast is not established.

## 7. Limitations

[Qualifier] The evidence is short-run only: 300 iterations, one seed, three scenes, and sampled reflection pairs. [Mixed] Rendering metrics are scene-dependent and LPIPS is missing. [Mixed] Normal-map diagnostics are directionally favorable but small and diagnostic-only. [Unsupported] Mesh/reference-geometry metrics are unavailable because current RefNeRF artifacts lack extracted meshes and SMVP3D support is incomplete. [Unsupported] Material diagnostics, relighting, external baselines, and causal ablations have not been audited.

This draft must not be treated as submission-ready prose until citation placeholders are replaced with real paper/code citations and the missing evidence gates are either satisfied or clearly listed as limitations.

## 8. Claim Table

| Claim area | Label | Manuscript-safe wording | Required caveat |
| --- | --- | --- | --- |
| Reflection-consistency diagnostic | Supported | RC-RefGS lowers measured reprojected reflection-consistency error relative to matched Ref-GS baselines in the current i300 three-scene sanity protocol. | Report scene, split, pair count, `max_pairs=10`, `max_angle_deg=180`, one seed, and 300 iterations. |
| Method change | Supported | RC-RefGS adds a gated cross-view reflection-consistency objective while preserving the base Ref-GS representation and renderer. | Do not imply a replacement material or geometry model. |
| Standard PSNR/SSIM | Mixed | PSNR/SSIM should be reported as scene-dependent context. | `teapot` improves, `toaster` is mixed, `car` slightly decreases, and LPIPS is unavailable. |
| Normal diagnostics | Mixed | Full-split raw-convention normal diagnostics are directionally favorable. | Effect sizes are small and not mesh/reference-geometry evidence. |
| LPIPS | Unsupported | No LPIPS result should be stated. | LPIPS was skipped. |
| Geometry and reconstruction | Unsupported | Geometry remains an open evaluation target. | No extracted RefNeRF meshes, no valid RefNeRF geometry target, and no SMVP3D adapter/runtime path yet. |
| Material decomposition | Unsupported | Material quality remains unevaluated. | No albedo variance, roughness stability, relighting, or material-specific diagnostic has been run. |
| External superiority | Unsupported | External-method comparison remains future work. | No external baseline runs or audited paper-number comparison is available. |
| Causal attribution | Unsupported | The current result is a matched RC-vs-baseline observation. | No `w/o L_ref`, `w/o specular confidence`, or roughness-only ablation exists. |

## 9. Upgrade Checklist Before Stronger Claims

- [ ] Longer-horizon matched baseline/RC runs with identical scenes, splits, iterations, seeds, and pair-selection settings.
- [ ] LPIPS for full-image and reflective-region metrics using cached or explicitly approved weights.
- [ ] More scenes and preferably repeated seeds before removing the short-run caveat.
- [ ] Matched ablations for `w/o L_ref`, `w/o specular confidence`, and roughness-only regularization.
- [ ] Mesh extraction/runtime repair before any geometry metric.
- [ ] SMVP3D loader support or deterministic `cameras.npz` to Ref-GS transform conversion before OBJ-reference Chamfer/F-score.
- [ ] Material diagnostics such as cross-view albedo variance, roughness stability, or relighting before material-quality language.
- [ ] External baseline runs or audited paper-number comparisons before external-superiority language.

## Forbidden Claim Boundary

The following broad claims remain forbidden in manuscript prose unless the upgrade gates above are satisfied:

- RC-RefGS improves overall novel-view synthesis quality.
- RC-RefGS improves LPIPS.
- RC-RefGS improves mesh quality, surface reconstruction, or geometry quality.
- RC-RefGS improves material decomposition.
- RC-RefGS outperforms external methods or paper baselines.
- RC-RefGS proves that `L_ref` causes all observed metric changes.
- RefNeRF `points3d.ply` is ground-truth geometry.

## Decision

**CONDITIONAL GO** for manuscript integration centered on the supported reflection-consistency diagnostic.

**NO-GO** for broad rendering, LPIPS, geometry, reconstruction, material, external-superiority, or causal claims.

**SWITCH MODEL** to gpt-5.5 remains recommended for final rhetoric, citation replacement, and manuscript-level polishing.
