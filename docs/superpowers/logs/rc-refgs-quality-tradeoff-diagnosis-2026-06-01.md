# RC-RefGS Quality Tradeoff Diagnosis - 2026-06-01

## Executive Summary

This diagnosis uses only the frozen FD-P2-lite / non-Shiny-Real final artifacts. It launches no training, no full metric sweep, and no Shiny Blender Real job.

RC strongly improves the reflection-consistency metric (`14/14` train, `13/14` test), but render quality remains mixed: full-image LPIPS wins are `9/14` train and `10/14` test, while reflective LPIPS wins are only `4/14` train and `6/14` test. The current conclusion remains that RC prioritizes reflection consistency, while PSNR/SSIM/LPIPS quality tradeoffs remain unresolved.

Decision: **CONDITIONAL GO** for a quality-preserving pilot plan. **NO-GO** for changing metrics, excluding bad scenes, claiming quality superiority, Shiny Blender Real completion, or full-scope claim upgrade.

## What Degraded

- Test full LPIPS regressions are concentrated in `glossy_synthetic/luyu` (+0.001538), `shiny_blender_synthetic/toaster` (+0.001531), `glossy_synthetic/cat` (+0.000160), and `shiny_blender_synthetic/helmet` (+0.000034).
- Test reflective LPIPS regressions are worst in `shiny_blender_synthetic/ball` (+0.004307), `glossy_synthetic/luyu` (+0.002417), `glossy_synthetic/cat` (+0.001455), `shiny_blender_synthetic/coffee` (+0.000870), and `shiny_blender_synthetic/car` (+0.000682).
- Test PSNR drops are largest for `glossy_synthetic/luyu` and `glossy_synthetic/cat`, especially reflective PSNR.
- Test SSIM drops are small in magnitude but still mark failures for `shiny_blender_synthetic/toaster`, `glossy_synthetic/cat`, and some reflective-region rows.

## Where It Degraded

### Train Categories

- `consistency_gain_quality_gain`: 3 scenes - shiny_blender_synthetic/teapot, glossy_synthetic/bell, glossy_synthetic/potion
- `consistency_gain_full_quality_drop`: 1 scenes - shiny_blender_synthetic/toaster
- `consistency_gain_reflective_quality_drop`: 5 scenes - shiny_blender_synthetic/ball, glossy_synthetic/cat, glossy_synthetic/horse, glossy_synthetic/tbell, glossy_synthetic/teapot
- `consistency_gain_quality_mixed`: 5 scenes - shiny_blender_synthetic/car, shiny_blender_synthetic/coffee, shiny_blender_synthetic/helmet, glossy_synthetic/angel, glossy_synthetic/luyu
- `no_consistency_gain`: 0 scenes

### Test Categories

- `consistency_gain_quality_gain`: 4 scenes - shiny_blender_synthetic/teapot, glossy_synthetic/bell, glossy_synthetic/potion, glossy_synthetic/teapot
- `consistency_gain_full_quality_drop`: 1 scenes - shiny_blender_synthetic/helmet
- `consistency_gain_reflective_quality_drop`: 4 scenes - shiny_blender_synthetic/ball, glossy_synthetic/angel, glossy_synthetic/horse, glossy_synthetic/tbell
- `consistency_gain_quality_mixed`: 4 scenes - shiny_blender_synthetic/car, shiny_blender_synthetic/toaster, glossy_synthetic/cat, glossy_synthetic/luyu
- `no_consistency_gain`: 1 scenes - shiny_blender_synthetic/coffee

Coffee is the only test split `no_consistency_gain` scene: RC improves train consistency for coffee, but test consistency delta is +0.002339, while test full-image quality improves and reflective-region PSNR/SSIM/LPIPS regress.

## Metric-Level Evidence

Top test regressions:

| type | scene | metric | delta_rc_minus_base |
| --- | --- | --- | --- |
| full LPIPS regression | glossy_synthetic/luyu | full_lpips | 0.001538 |
| full LPIPS regression | shiny_blender_synthetic/toaster | full_lpips | 0.001531 |
| full LPIPS regression | glossy_synthetic/cat | full_lpips | 0.000160 |
| full LPIPS regression | shiny_blender_synthetic/helmet | full_lpips | 3.397e-05 |
| reflective LPIPS regression | shiny_blender_synthetic/ball | reflective_lpips | 0.004307 |
| reflective LPIPS regression | glossy_synthetic/luyu | reflective_lpips | 0.002417 |
| reflective LPIPS regression | glossy_synthetic/cat | reflective_lpips | 0.001455 |
| reflective LPIPS regression | shiny_blender_synthetic/coffee | reflective_lpips | 0.000870 |
| reflective LPIPS regression | shiny_blender_synthetic/car | reflective_lpips | 0.000682 |
| full PSNR drop | glossy_synthetic/luyu | full_psnr | -0.421593 |
| full PSNR drop | glossy_synthetic/cat | full_psnr | -0.242756 |
| full PSNR drop | shiny_blender_synthetic/toaster | full_psnr | -0.175853 |
| full PSNR drop | shiny_blender_synthetic/car | full_psnr | -0.018468 |
| reflective PSNR drop | glossy_synthetic/luyu | reflective_psnr | -0.655782 |
| reflective PSNR drop | glossy_synthetic/cat | reflective_psnr | -0.544024 |
| reflective PSNR drop | shiny_blender_synthetic/coffee | reflective_psnr | -0.251257 |
| reflective PSNR drop | shiny_blender_synthetic/toaster | reflective_psnr | -0.154583 |
| any SSIM drop | glossy_synthetic/cat | reflective_ssim | -0.001948 |
| any SSIM drop | shiny_blender_synthetic/coffee | reflective_ssim | -0.001135 |
| any SSIM drop | glossy_synthetic/luyu | reflective_ssim | -0.000993 |
| any SSIM drop | shiny_blender_synthetic/toaster | full_ssim | -0.000822 |
| any SSIM drop | glossy_synthetic/horse | reflective_ssim | -0.000461 |

Correlation check over the 14 scoped scenes is weak and descriptive only. Test consistency-gain magnitude has low correlation with full LPIPS regression severity (`0.146`) and near-zero to negative correlation with PSNR drops, so the current artifacts do not prove a single global over-regularization mechanism. Over-regularization remains plausible because individual scenes show large consistency gains with quality losses.

Dataset-level test means: Shiny Blender Synthetic has stronger mean test consistency gain (-0.044536) but mean reflective LPIPS worsens (+0.000976). Glossy Synthetic has smaller mean consistency gain (-0.020146), mean full LPIPS improves (-0.000687), but mean reflective PSNR and reflective SSIM decline.

## Ablation Evidence

- `wo_ref`: removing reflection loss worsens reflection consistency relative to RC in both datasets. It does not reliably improve full-image PSNR/SSIM/LPIPS; reflective metrics sometimes preserve or improve relative to RC.
- `wo_conf`: removing confidence weighting also worsens consistency and full-image metrics relative to RC, while some reflective metrics improve relative to RC. This suggests confidence weighting may affect reflective-region behavior, but it is not the sole cause of full-image losses.
- `rough_only`: roughness-only loses the consistency gain and does not reliably rescue test full-image quality, so it is not a sufficient substitute for RC.
- Limitation: these are dataset-variant aggregate comparisons, not per-scene causal decompositions.

## Likely Causes

- **reflection loss strength or schedule over-regularization**: RC gains consistency in 14/14 train and 13/14 test pairs, but strict all-quality wins are much rarer. The large helmet consistency gain coexists with small test full SSIM/LPIPS regressions; luyu and cat show quality drops with consistency gains. Correlations between consistency-gain magnitude and quality-regression severity are weak, so over-regularization is plausible but not proven globally. Uncertainty: Existing results use only the current lambda/start/every/gamma setting, so strength and schedule are confounded.
- **confidence weighting and reflective-region emphasis**: wo_conf worsens consistency and full-image metrics relative to RC in aggregates, but reflective metrics are often preserved or improved relative to RC. Reflective LPIPS wins are only 4/14 train and 6/14 test, suggesting region-level behavior is less stable than full-image LPIPS. Uncertainty: The aggregate wo_conf evidence cannot identify scene-level mask-confidence failures.
- **loss-objective mismatch with LPIPS/PSNR/SSIM**: train.py optimizes L1 + DSSIM reconstruction plus auxiliary RC and optional regularizers; LPIPS is evaluation-only. This can improve the reflection-consistency metric without directly optimizing LPIPS or all PSNR/SSIM surfaces. Uncertainty: Adding LPIPS loss could bias toward the metric and may trade off PSNR/SSIM unless validated separately.
- **mask or reflective-region instability**: Full-image LPIPS improves more often than reflective LPIPS. Coffee is the test consistency exception while full-image quality improves and reflective quality drops, a pattern consistent with reflective-region mismatch or view-dependent mask instability. Uncertainty: The current artifacts do not expose per-pixel masks/roughness stability over training, so this remains diagnostic rather than confirmed.

## Alternative Explanations

- Some regressions may come from PBR image-key/compositing sensitivity rather than the RC term itself; the current headline comparisons must keep `pbr_rgb`, masks, splits, and LPIPS settings unchanged.
- Reflective-region metrics may amplify roughness-mask or threshold instability; this is suggested by reflective LPIPS underperformance but not proven by the available aggregate files.
- One-seed i31000 evidence may hide run-to-run variance; no multi-seed quality-preserving claim is available.

## Risks Of Optimizing For LPIPS/PSNR/SSIM

- Direct LPIPS training can bias toward the reported metric and should be disabled by default until validated.
- Improving full-image quality may reduce the reflection-consistency gain if the auxiliary RC term is weakened too far.
- Mask or split changes would make headline comparisons non-comparable; any such diagnostic must be labeled separately.

## Recommended Plan

Run a small quality-preserving pilot with reduced RC weight, delayed/lower-frequency RC scheduling, and a softer confidence gamma. Use new `rc_qp_*` variants under `/tmp/rc_refgs_quality_preserving_rc_i31000_20260601`. Do not claim the new variant exceeds base until paired pilot results prove it.
