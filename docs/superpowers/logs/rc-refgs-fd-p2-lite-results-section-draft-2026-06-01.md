# Results

## Experimental Scope

Within the FD-P2-lite / non-Shiny-Real scope, we evaluate RC-RefGS on two datasets: Shiny Blender Synthetic, containing six scenes, and Glossy Synthetic, containing eight scenes. Shiny Blender Real is excluded due to OOM. This exclusion is explicit: the present section reports a narrowed non-Shiny-Real evaluation and does not imply completion of the original Shiny-Real-inclusive protocol.

The main comparison contains 14 matched scenes evaluated with the `base` and `rc` variants, yielding 28/28 completed model evaluations. The ablation study uses the same 14 scenes with the `wo_ref`, `wo_conf`, and `rough_only` variants, yielding 42/42 completed model evaluations. Across the 70 scoped models, complete-metric coverage is 70/70. Every model includes train- and test-split reflection consistency, reflective-region PSNR from the reflection-consistency evaluator, full-image PSNR/SSIM/LPIPS, and reflective-region PSNR/SSIM/LPIPS from the render-quality evaluator.

For interpretation, lower values are better for reflection-consistency error and LPIPS, whereas higher values are better for PSNR and SSIM. The original full 17-scene FD-P2 and full 51-cell ablation claims remain unsupported.

## Main Comparison: Base vs RC

RC reduces reflection-consistency error on 14/14 training pairs and 13/14 test pairs. The mean RC-minus-base consistency delta is `-0.074349` on the training split and `-0.030599` on the test split. This pattern supports the intended effect of RC on reflection behavior within the evaluated non-Shiny-Real scope. The strongest consistency improvement occurs on `shiny_blender_synthetic/helmet`, where the RC-minus-base delta is `-0.551036` on train and `-0.180882` on test.

The render-quality metrics show mixed tradeoffs. Full-image PSNR favors RC on 9/14 training pairs and 10/14 test pairs, while full-image SSIM favors RC on 9/14 training pairs and 11/14 test pairs. Full-image LPIPS favors RC on 9/14 training pairs and 10/14 test pairs. Reflective-region behavior is less uniform: reflective-region PSNR from the reflection-consistency evaluator favors RC on 7/14 training pairs and 8/14 test pairs; reflective PSNR from the render-quality evaluator favors RC on 6/14 training pairs and 10/14 test pairs; reflective SSIM favors RC on 7/14 pairs for both splits; and reflective LPIPS favors RC on only 4/14 training pairs and 6/14 test pairs.

These results do not support a universal image-quality improvement claim. Rather, the scoped evidence indicates that RC primarily improves reflection consistency while introducing scene- and metric-dependent quality tradeoffs. The most visible exception to the consistency trend is `shiny_blender_synthetic/coffee` on the test split, where the RC-minus-base consistency delta is `+0.002339`.

## Ablation Results

The non-Shiny-Real ablation study is complete at 42/42 scoped model evaluations. The `wo_ref` variant removes reflection-consistency supervision, `wo_conf` removes or neutralizes confidence weighting, and `rough_only` replaces the full RC configuration with roughness-only regularization. Table 1 reports compact aggregate consistency and render-quality values by dataset and variant.

| Dataset | Variant | Train consistency | Test consistency | Train full PSNR / SSIM / LPIPS | Test full PSNR / SSIM / LPIPS | Train reflective PSNR / SSIM / LPIPS | Test reflective PSNR / SSIM / LPIPS |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| Shiny Blender Synthetic | `wo_ref` | 0.211805 | 0.075456 | 39.974134 / 0.988553 / 0.018039 | 35.642333 / 0.977039 / 0.029531 | 41.602831 / 0.992931 / 0.009892 | 36.887973 / 0.984427 / 0.017958 |
| Shiny Blender Synthetic | `wo_conf` | 0.109448 | 0.038645 | 39.910465 / 0.988507 / 0.018096 | 35.649955 / 0.976911 / 0.029733 | 41.498613 / 0.992962 / 0.009294 | 36.874270 / 0.984406 / 0.017170 |
| Shiny Blender Synthetic | `rough_only` | 0.193192 | 0.069570 | 39.962747 / 0.988586 / 0.017989 | 35.616543 / 0.976828 / 0.029735 | 41.364119 / 0.992895 / 0.009786 | 36.648069 / 0.983987 / 0.018113 |
| Glossy Synthetic | `wo_ref` | 0.174459 | 0.179875 | 32.888937 / 0.973714 / 0.035164 | 30.163602 / 0.956734 / 0.043789 | 34.140334 / 0.980180 / 0.024096 | 31.465795 / 0.968753 / 0.031140 |
| Glossy Synthetic | `wo_conf` | 0.159928 | 0.167266 | 32.895391 / 0.973660 / 0.035251 | 30.134392 / 0.956433 / 0.043950 | 34.176524 / 0.980014 / 0.024236 | 31.429838 / 0.968283 / 0.031484 |
| Glossy Synthetic | `rough_only` | 0.175582 | 0.180672 | 32.928193 / 0.973736 / 0.035228 | 30.186743 / 0.956587 / 0.043954 | 34.039423 / 0.980224 / 0.024260 | 31.342511 / 0.968244 / 0.031422 |

Relative to paired RC models, `wo_ref` degrades aggregate reflection consistency on both datasets and both splits. `wo_conf` also degrades aggregate consistency, but generally by less than `wo_ref`. The `rough_only` control does not reproduce the RC consistency behavior. Within this scope, the comparison suggests that reflection-consistency supervision is the stronger contributor to the observed consistency improvement, with confidence weighting also contributing. The `rough_only` result indicates that roughness-only regularization is insufficient to reproduce the full RC behavior. These observations are diagnostic rather than causal: the experiment is single-seed and excludes Shiny Blender Real.

The render-quality ablation results are not uniformly ordered. Some ablations preserve or improve selected PSNR, SSIM, or LPIPS aggregates while degrading consistency relative to RC. This reinforces the need to report component-level consistency effects separately from image-quality effects.

## Trade-off Analysis

The main comparison indicates that RC acts primarily as a consistency-targeted regularizer. RC improves reflection consistency while worsening at least one render-quality metric in 21/28 scene-split rows. In 6/28 scene-split rows, RC improves at least one reflective-region metric while worsening at least one full-image metric. Across the ablation aggregates, 11 dataset-variant-split rows improve at least one render-quality aggregate while degrading consistency relative to paired RC.

Lower reflection-consistency error therefore does not imply universal improvement in perceptual or image-quality metrics. The scoped results support RC as a consistency-targeted regularizer rather than a universal quality booster. Reflection-consistency improvements and PSNR/SSIM/LPIPS behavior should be presented as related but distinct outcomes.

## Limitations

Shiny Blender Real is excluded due to OOM. The reported results use a single seed and are limited to the FD-P2-lite / non-Shiny-Real scope. They do not support an original full 17-scene FD-P2 claim, and the full 51-cell ablation matrix is not complete. Metric-specific tradeoffs remain present, particularly for reflective-region LPIPS and other reflective quality measures. Accordingly, the results should be described as scope-limited evidence rather than as a universal reconstruction-quality improvement.

## Summary

Within the FD-P2-lite / non-Shiny-Real scope, complete-metric coverage is 70/70. The main base/RC comparison is complete at 28/28, and the non-Shiny-Real ablation comparison is complete at 42/42. RC provides strong evidence for improved reflection consistency in the scoped datasets, while render-quality metrics show mixed tradeoffs. Shiny Blender Real is excluded due to OOM. The original full 17-scene FD-P2 and full 51-cell ablation claims remain unsupported.

