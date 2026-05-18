# RC-RefGS Conservative Manuscript Prose Skeleton

Date: 2026-05-18 07:15:23 CST

Scope: manuscript-ready wording scaffold constrained to the current i300 evidence. This document is a prose handoff, not a new experiment or claim expansion.

Source artifacts:

- `docs/superpowers/logs/rc-refgs-claim-audit-2026-05-17.md`
- `docs/superpowers/logs/rc-refgs-claim-framing-packet-2026-05-18.md`
- `docs/superpowers/logs/rc-refgs-acceptance-thresholds-2026-05-18.md`
- `docs/superpowers/logs/rc-refgs-render-quality-summary-2026-05-17.md`
- `docs/superpowers/logs/rc-refgs-normal-quality-summary-2026-05-18.md`
- `docs/superpowers/logs/rc-refgs-geometry-feasibility-2026-05-18.md`

## Working Title

RC-RefGS: Reflection-Consistency Diagnostics for Ref-GS

## Conservative Abstract Draft

[Citation: Ref-GS code] Ref-GS represents glossy scenes with 2D Gaussian surfels, deferred material buffers, Sph-Mip directional encoding, and a specular MLP. [Reasoning] This representation can fit view-dependent appearance through several coupled variables, but its baseline supervision does not directly require the reflected response of a matched surface region to agree across views. [Citation: this implementation] RC-RefGS adds a gated cross-view reflection-consistency objective while preserving the base Ref-GS representation and renderer. [Evidence] In short i300 sanity runs on `teapot`, `toaster`, and `car`, RC-RefGS lowers measured reprojected reflection-consistency error relative to matched Ref-GS baselines on both train and held-out test splits under `max_pairs=10` and `max_angle_deg=180`. [Qualifier] Standard PSNR/SSIM trends are mixed, LPIPS is unavailable, normal-map improvements are small diagnostic effects, and no mesh/reference-geometry metrics are available. [Reasoning] We therefore frame the current result as evidence for the targeted reflection-consistency diagnostic, not as evidence for broad rendering, geometry, material, or reconstruction quality.

## Contribution Bullets

1. [Citation: this implementation] We expose intermediate Ref-GS rendering buffers and add a disabled-by-default, gated reflection-consistency loss that compares reprojected specular predictions across view pairs.
2. [Citation: this implementation] We provide a reflection-consistency evaluation script that reports mean reprojected reflection-consistency error, reflective-region PSNR, and valid pair counts for matched baseline/RC runs.
3. [Evidence] On the three audited i300 RefNeRF scenes, the RC setting reduces the measured reflection-consistency error in all six train/test rows relative to matched baselines.
4. [Qualifier] We report standard rendering and normal-map diagnostics as mixed or diagnostic-only evidence; they do not support a claim of overall rendering-quality, geometry-quality, material-decomposition, or reconstruction improvement.

## Method Framing

[Citation: Ref-GS code] The baseline renderer computes reflected directions, Sph-Mip features, Gaussian feature interactions, and per-pixel specular radiance before composing the final PBR image. [Reasoning] Because RGB supervision alone can be satisfied by compensating changes across normals, roughness, features, and the specular network, reflective appearance can remain under-constrained across views. [Citation: this implementation] RC-RefGS keeps the original renderer and adds an auxiliary view-pair loss on confident specular predictions. [Reasoning] The intent is not to replace the Ref-GS appearance model, but to make a cross-view reflection-consistency signal observable during training and measurable after training.

## Results Framing

[Evidence] The current evidence uses matched baseline and RC runs at 300 iterations on `teapot`, `toaster`, and `car`, with held-out split preservation, one seed, `max_pairs=10`, and `max_angle_deg=180`. [Evidence] RC reduces measured reprojected reflection-consistency error on all six scene/split rows. [Qualifier] This is a short-run diagnostic result and the metric is pair-sampling dependent, so every table should report split, pair count, and pair-selection settings.

[Evidence] Standard rendering metrics do not support an aggregate quality claim. `teapot` improves in PSNR/SSIM, `toaster` is mixed with small PSNR decreases and SSIM increases, and `car` slightly decreases in PSNR/SSIM. [Qualifier] LPIPS was skipped, so no LPIPS trend can be reported.

[Evidence] Full-split raw-convention normal diagnostics improve MAE and mean cosine on all six rows. [Qualifier] The effect sizes are small, especially for `toaster` and `car`, and these normal-map diagnostics are not mesh/reference-geometry evidence.

## Limitations Paragraph

[Qualifier] Current evidence is limited to three RefNeRF scenes, 300 training iterations, one seed, and sampled reflection pairs. [Unsupported] We do not claim improved overall novel-view synthesis, LPIPS, mesh quality, surface reconstruction, geometry quality, material decomposition, or superiority over external methods. [Unsupported] We also do not attribute the observed changes specifically to `L_ref` beyond the matched RC-vs-baseline contrast, because ablations for `w/o L_ref`, `w/o specular confidence`, and roughness-only regularization have not been run. [Unsupported] RefNeRF `points3d.ply` must not be used as ground-truth geometry because this repo's Blender reader writes random initialization points there. [Reasoning] Geometry claims require extracted meshes and valid reference metrics, most plausibly through future SMVP3D loader/runtime support and OBJ-based Chamfer/F-score evaluation.

## Forbidden Replacement Phrases

Do not replace the conservative wording with any of these claims:

- RC-RefGS improves overall novel-view synthesis quality.
- RC-RefGS improves LPIPS.
- RC-RefGS improves mesh quality or surface reconstruction.
- RC-RefGS improves material decomposition.
- RC-RefGS outperforms external glossy reconstruction methods.
- RC-RefGS proves that `L_ref` causes all observed metric changes.

## Upgrade Checklist Before Stronger Claims

- [ ] Longer-horizon matched baseline/RC runs with identical scene/split/iteration/seed settings.
- [ ] LPIPS for all-pixel and reflective-mask regions using cached or explicitly approved weights.
- [ ] Ablations for `w/o L_ref`, `w/o specular confidence`, and roughness-only regularization.
- [ ] Mesh extraction/runtime repair and valid reference-geometry metrics.
- [ ] SMVP3D loader or deterministic `cameras.npz` to Ref-GS transform conversion before OBJ-based geometry evaluation.

## Decision

**CONDITIONAL GO** for using this prose skeleton as a conservative manuscript handoff centered on the reflection-consistency diagnostic.

**NO-GO** for stronger rendering, LPIPS, geometry, reconstruction, material, external-superiority, or causal claims.

**SWITCH MODEL** to gpt-5.5 remains recommended for final rhetorical polish and citation-aware manuscript integration.
