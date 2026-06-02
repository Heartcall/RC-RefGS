# RC-RefGS FD-P2-lite Complete-Metric Final Results Analysis

## 1. Executive summary

- Scope: FD-P2-lite / non-Shiny-Real only.
- Complete-metric coverage is **70/70**: main base/RC `28/28` and ablation `42/42`.
- RC strongly improves reflection consistency in the scoped datasets: `14/14` train pairs and `13/14` test pairs favor RC.
- Render-quality metrics are mixed. RC should be reported as prioritizing consistency with image-quality tradeoffs, not as globally superior.
- Shiny Blender Real is excluded due to persistent OOM blocker.
- Original full FD-P2 and full 51-cell ablation claims remain NO-GO.

## 2. Scope and claim boundary

- Included datasets: `shiny_blender_synthetic` (`ball`, `car`, `coffee`, `helmet`, `teapot`, `toaster`) and `glossy_synthetic` (`angel`, `bell`, `cat`, `horse`, `luyu`, `potion`, `tbell`, `teapot`).
- Main variants: `base`, `rc`.
- Ablation variants: `wo_ref`, `wo_conf`, `rough_only`.
- Excluded dataset: `shiny_blender_real` due to persistent OOM blocker.
- Supported: scope-limited non-Shiny-Real complete-metric comparisons and paired diagnostic ablation interpretation.
- Not supported: Shiny Blender Real completion, original 17-scene FD-P2 completion, original 51-cell ablation completion, global render-quality superiority, causal attribution, or multi-seed robustness claims.

## 3. Complete metric set

| Metric | Region | Better direction | Splits |
| --- | --- | --- | --- |
| `mean_reflection_consistency` | reflection consistency | lower | train, test |
| `reflective_region_psnr` | reflective region | higher | train, test |
| `full_psnr` | full image | higher | train, test |
| `full_ssim` | full image | higher | train, test |
| `full_lpips` | full image | lower | train, test |
| `reflective_psnr` | reflective region | higher | train, test |
| `reflective_ssim` | reflective region | higher | train, test |
| `reflective_lpips` | reflective region | lower | train, test |

## 4. Main base-vs-RC summary

- Main comparison convention: `14` paired-scene rows, representing `28/28` complete models.
- Detailed per-scene base, RC, delta, and win flags are exported in `rc-refgs-fd-p2-lite-final-main-summary-2026-06-01.csv`.

### RC win counts

| Metric | Train RC wins | Test RC wins |
| --- | ---: | ---: |
| `mean_reflection_consistency` | 14/14 | 13/14 |
| `reflective_region_psnr` | 7/14 | 8/14 |
| `full_psnr` | 9/14 | 10/14 |
| `full_ssim` | 9/14 | 11/14 |
| `full_lpips` | 9/14 | 10/14 |
| `reflective_psnr` | 6/14 | 10/14 |
| `reflective_ssim` | 7/14 | 7/14 |
| `reflective_lpips` | 4/14 | 6/14 |

### Mean RC-minus-base deltas

| Metric | Train mean delta | Test mean delta |
| --- | ---: | ---: |
| `mean_reflection_consistency` | -0.074349 | -0.030599 |
| `reflective_region_psnr` | 0.024024 | -0.027898 |
| `full_psnr` | 0.026755 | 0.049286 |
| `full_ssim` | 0.000206 | 0.000460 |
| `full_lpips` | -0.000146 | -0.000356 |
| `reflective_psnr` | -0.082185 | -0.038935 |
| `reflective_ssim` | -0.000118 | -0.000206 |
| `reflective_lpips` | 0.000376 | 0.000437 |

### Dataset-level breakdown

| Dataset | Metric | Train mean delta / wins | Test mean delta / wins |
| --- | --- | ---: | ---: |
| `shiny_blender_synthetic` | `mean_reflection_consistency` | -0.147117 / 6/6 | -0.044536 / 5/6 |
| `shiny_blender_synthetic` | `reflective_region_psnr` | 0.181982 / 4/6 | -0.127711 / 2/6 |
| `shiny_blender_synthetic` | `full_psnr` | 0.064846 / 3/6 | 0.074978 / 4/6 |
| `shiny_blender_synthetic` | `full_ssim` | -0.000056 / 2/6 | 0.000069 / 4/6 |
| `shiny_blender_synthetic` | `full_lpips` | 0.000152 / 2/6 | 0.000084 / 4/6 |
| `shiny_blender_synthetic` | `reflective_psnr` | -0.055372 / 3/6 | 0.016360 / 4/6 |
| `shiny_blender_synthetic` | `reflective_ssim` | -0.000215 / 2/6 | -0.000163 / 4/6 |
| `shiny_blender_synthetic` | `reflective_lpips` | 0.000701 / 2/6 | 0.000976 / 2/6 |
| `glossy_synthetic` | `mean_reflection_consistency` | -0.019773 / 8/8 | -0.020146 / 8/8 |
| `glossy_synthetic` | `reflective_region_psnr` | -0.094445 / 3/8 | 0.046962 / 6/8 |
| `glossy_synthetic` | `full_psnr` | -0.001812 / 6/8 | 0.030017 / 6/8 |
| `glossy_synthetic` | `full_ssim` | 0.000402 / 7/8 | 0.000753 / 7/8 |
| `glossy_synthetic` | `full_lpips` | -0.000370 / 7/8 | -0.000687 / 6/8 |
| `glossy_synthetic` | `reflective_psnr` | -0.102295 / 3/8 | -0.080407 / 6/8 |
| `glossy_synthetic` | `reflective_ssim` | -0.000046 / 5/8 | -0.000239 / 3/8 |
| `glossy_synthetic` | `reflective_lpips` | 0.000133 / 2/8 | 0.000033 / 4/8 |

### Strongest improvements

- `mean_reflection_consistency/train`: `shiny_blender_synthetic/helmet` delta `-0.551036`.
- `mean_reflection_consistency/test`: `shiny_blender_synthetic/helmet` delta `-0.180882`.
- `reflective_region_psnr/train`: `shiny_blender_synthetic/teapot` delta `0.738475`.
- `reflective_region_psnr/test`: `glossy_synthetic/angel` delta `0.513029`.
- `full_psnr/train`: `shiny_blender_synthetic/teapot` delta `0.689702`.
- `full_psnr/test`: `shiny_blender_synthetic/coffee` delta `0.261050`.
- `full_ssim/train`: `glossy_synthetic/teapot` delta `0.000915`.
- `full_ssim/test`: `glossy_synthetic/teapot` delta `0.001869`.
- `full_lpips/train`: `glossy_synthetic/bell` delta `-0.001564`.
- `full_lpips/test`: `glossy_synthetic/bell` delta `-0.002622`.
- `reflective_psnr/train`: `shiny_blender_synthetic/teapot` delta `0.787239`.
- `reflective_psnr/test`: `shiny_blender_synthetic/teapot` delta `0.290175`.
- `reflective_ssim/train`: `glossy_synthetic/bell` delta `0.000781`.
- `reflective_ssim/test`: `glossy_synthetic/bell` delta `0.001185`.
- `reflective_lpips/train`: `glossy_synthetic/bell` delta `-0.001531`.
- `reflective_lpips/test`: `glossy_synthetic/bell` delta `-0.002677`.

### Weakest or negative cases

- `shiny_blender_synthetic/ball/train`: worsened `reflective_ssim, reflective_lpips`.
- `shiny_blender_synthetic/ball/test`: worsened `reflective_region_psnr, reflective_ssim, reflective_lpips`.
- `shiny_blender_synthetic/car/train`: worsened `reflective_region_psnr, full_psnr, full_ssim, full_lpips, reflective_psnr, reflective_ssim, reflective_lpips`.
- `shiny_blender_synthetic/car/test`: worsened `full_psnr, reflective_lpips`.
- `shiny_blender_synthetic/coffee/train`: worsened `reflective_region_psnr, full_psnr, full_ssim, full_lpips, reflective_psnr, reflective_ssim, reflective_lpips`.
- `shiny_blender_synthetic/coffee/test`: worsened `mean_reflection_consistency, reflective_region_psnr, reflective_psnr, reflective_ssim, reflective_lpips`.
- `shiny_blender_synthetic/helmet/train`: worsened `full_psnr, full_ssim, full_lpips, reflective_psnr, reflective_ssim, reflective_lpips`.
- `shiny_blender_synthetic/helmet/test`: worsened `reflective_region_psnr, full_ssim, full_lpips`.
- `shiny_blender_synthetic/toaster/train`: worsened `full_ssim, full_lpips`.
- `shiny_blender_synthetic/toaster/test`: worsened `reflective_region_psnr, full_psnr, full_ssim, full_lpips, reflective_psnr, reflective_lpips`.
- `glossy_synthetic/angel/train`: worsened `full_psnr, reflective_psnr, reflective_lpips`.
- `glossy_synthetic/angel/test`: worsened `reflective_ssim`.
- `glossy_synthetic/bell/train`: worsened `reflective_region_psnr`.
- `glossy_synthetic/cat/train`: worsened `reflective_region_psnr, reflective_psnr, reflective_ssim, reflective_lpips`.
- `glossy_synthetic/cat/test`: worsened `reflective_region_psnr, full_psnr, full_ssim, full_lpips, reflective_psnr, reflective_ssim, reflective_lpips`.
- `glossy_synthetic/horse/train`: worsened `reflective_lpips`.
- `glossy_synthetic/horse/test`: worsened `reflective_ssim, reflective_lpips`.
- `glossy_synthetic/luyu/train`: worsened `reflective_region_psnr, full_psnr, full_ssim, full_lpips, reflective_psnr, reflective_ssim, reflective_lpips`.
- `glossy_synthetic/luyu/test`: worsened `reflective_region_psnr, full_psnr, full_lpips, reflective_psnr, reflective_ssim, reflective_lpips`.
- `glossy_synthetic/tbell/train`: worsened `reflective_region_psnr, reflective_psnr, reflective_ssim, reflective_lpips`.
- `glossy_synthetic/tbell/test`: worsened `reflective_ssim, reflective_lpips`.
- `glossy_synthetic/teapot/train`: worsened `reflective_region_psnr, reflective_psnr, reflective_lpips`.

## 5. Main base-vs-RC conclusion

- RC consistently lowers reflection consistency in the scoped datasets: train `14/14`, test `13/14`.
- Render-quality effects are mixed across full-image and reflective-region PSNR, SSIM, and LPIPS.
- The evidence supports a consistency-prioritizing interpretation: RC improves reflection consistency while accepting image-quality tradeoffs in some scene/split rows.
- The evidence does not support a globally superior render-quality claim.

## 6. Ablation summary

- Ablation coverage is `42/42`: the same `14` scenes across `wo_ref`, `wo_conf`, and `rough_only`.
- The aggregate table compares each dataset/variant mean against paired RC means. Lower consistency and LPIPS are better; higher PSNR and SSIM are better.
- Full aggregate data are exported in `rc-refgs-fd-p2-lite-final-ablation-summary-2026-06-01.csv`.

| Dataset | Variant | Models | Train consistency | Test consistency | Train full PSNR / SSIM / LPIPS | Test full PSNR / SSIM / LPIPS | Train reflective PSNR / SSIM / LPIPS | Test reflective PSNR / SSIM / LPIPS |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `shiny_blender_synthetic` | `wo_ref` | 6/6 | 0.211805 | 0.075456 | 39.974134 / 0.988553 / 0.018039 | 35.642333 / 0.977039 / 0.029531 | 41.602831 / 0.992931 / 0.009892 | 36.887973 / 0.984427 / 0.017958 |
| `shiny_blender_synthetic` | `wo_conf` | 6/6 | 0.109448 | 0.038645 | 39.910465 / 0.988507 / 0.018096 | 35.649955 / 0.976911 / 0.029733 | 41.498613 / 0.992962 / 0.009294 | 36.874270 / 0.984406 / 0.017170 |
| `shiny_blender_synthetic` | `rough_only` | 6/6 | 0.193192 | 0.069570 | 39.962747 / 0.988586 / 0.017989 | 35.616543 / 0.976828 / 0.029735 | 41.364119 / 0.992895 / 0.009786 | 36.648069 / 0.983987 / 0.018113 |
| `glossy_synthetic` | `wo_ref` | 8/8 | 0.174459 | 0.179875 | 32.888937 / 0.973714 / 0.035164 | 30.163602 / 0.956734 / 0.043789 | 34.140334 / 0.980180 / 0.024096 | 31.465795 / 0.968753 / 0.031140 |
| `glossy_synthetic` | `wo_conf` | 8/8 | 0.159928 | 0.167266 | 32.895391 / 0.973660 / 0.035251 | 30.134392 / 0.956433 / 0.043950 | 34.176524 / 0.980014 / 0.024236 | 31.429838 / 0.968283 / 0.031484 |
| `glossy_synthetic` | `rough_only` | 8/8 | 0.175582 | 0.180672 | 32.928193 / 0.973736 / 0.035228 | 30.186743 / 0.956587 / 0.043954 | 34.039423 / 0.980224 / 0.024260 | 31.342511 / 0.968244 / 0.031422 |

Reflective-region PSNR from reflection-consistency JSON:

- `shiny_blender_synthetic/wo_ref`: train `35.501986`, test `31.395515`.
- `shiny_blender_synthetic/wo_conf`: train `35.263859`, test `31.467753`.
- `shiny_blender_synthetic/rough_only`: train `35.313420`, test `31.617157`.
- `glossy_synthetic/wo_ref`: train `26.341012`, test `24.311390`.
- `glossy_synthetic/wo_conf`: train `26.352376`, test `24.291163`.
- `glossy_synthetic/rough_only`: train `26.264969`, test `24.242445`.

## 7. Ablation interpretation

- `wo_ref`: Removing reflection-consistency supervision degrades aggregate reflection consistency relative to RC on both datasets and both splits. Among the targeted removal variants, this supports reflection-consistency supervision as the stronger contributor to the scoped consistency improvement. Render-quality effects are mixed: some PSNR/SSIM/LPIPS aggregates preserve or improve relative to RC while consistency worsens.
- `wo_conf`: Neutralizing confidence weighting also degrades aggregate reflection consistency relative to RC on both datasets and both splits, but generally less than wo_ref. Confidence weighting contributes to consistency without yielding a uniform render-quality direction. Render-quality effects remain metric- and dataset-dependent; no uniform quality advantage is supported.
- `rough_only`: Roughness-only regularization does not reproduce RC reflection-consistency behavior. This control is not a single-component removal, so it supports insufficiency of roughness-only regularization rather than an isolated causal ranking. Roughness-only render-quality behavior is mixed and often degrades relative to RC, especially on Glossy Synthetic.
- Component boundary: The scoped paired evidence suggests reflection-consistency supervision is more important than confidence weighting for consistency, while no single component has a uniform render-quality effect. These are scope-limited diagnostic interpretations, not causal claims.

## 8. Trade-off analysis

- RC improves consistency while worsening at least one render-quality metric in `21` scene/split rows.
- RC improves at least one reflective metric while worsening at least one full-image metric in `6` scene/split rows.
- RC worsens at least one tracked metric in `22` scene/split rows.
- Ablations improve at least one render-quality aggregate while degrading consistency relative to RC in `11` dataset/variant/split rows.
- Detailed scene/split patterns are exported in `rc-refgs-fd-p2-lite-final-tradeoff-summary-2026-06-01.csv`.

Ablation render-quality/consistency tradeoffs:
- `shiny_blender_synthetic/wo_ref/train`: consistency degrades relative to RC; full-image preserved/improved `full_lpips, full_ssim`; reflective preserved/improved `reflective_lpips, reflective_psnr, reflective_region_psnr, reflective_ssim`.
- `shiny_blender_synthetic/wo_ref/test`: consistency degrades relative to RC; full-image preserved/improved `full_ssim`; reflective preserved/improved `reflective_lpips, reflective_psnr, reflective_region_psnr, reflective_ssim`.
- `shiny_blender_synthetic/wo_conf/train`: consistency degrades relative to RC; full-image preserved/improved `none`; reflective preserved/improved `reflective_lpips, reflective_psnr, reflective_ssim`.
- `shiny_blender_synthetic/wo_conf/test`: consistency degrades relative to RC; full-image preserved/improved `none`; reflective preserved/improved `reflective_lpips, reflective_psnr, reflective_region_psnr, reflective_ssim`.
- `shiny_blender_synthetic/rough_only/train`: consistency degrades relative to RC; full-image preserved/improved `full_lpips, full_ssim`; reflective preserved/improved `reflective_lpips, reflective_ssim`.
- `shiny_blender_synthetic/rough_only/test`: consistency degrades relative to RC; full-image preserved/improved `none`; reflective preserved/improved `reflective_lpips, reflective_region_psnr`.
- `glossy_synthetic/wo_ref/train`: consistency degrades relative to RC; full-image preserved/improved `none`; reflective preserved/improved `reflective_psnr`.
- `glossy_synthetic/wo_ref/test`: consistency degrades relative to RC; full-image preserved/improved `none`; reflective preserved/improved `reflective_lpips, reflective_psnr, reflective_ssim`.
- `glossy_synthetic/wo_conf/train`: consistency degrades relative to RC; full-image preserved/improved `none`; reflective preserved/improved `reflective_psnr`.
- `glossy_synthetic/wo_conf/test`: consistency degrades relative to RC; full-image preserved/improved `none`; reflective preserved/improved `reflective_psnr, reflective_ssim`.
- `glossy_synthetic/rough_only/test`: consistency degrades relative to RC; full-image preserved/improved `none`; reflective preserved/improved `reflective_ssim`.

## 9. Evidence-supported conclusions

- Within the FD-P2-lite / non-Shiny-Real scope, complete-metric coverage is 70/70.
- The main base/RC comparison is complete at 28/28 under the full metric set.
- The non-Shiny-Real ablation comparison is complete at 42/42 under the full metric set.
- RC provides strong evidence for improved reflection consistency in the scoped datasets.
- Render-quality metrics show tradeoffs and should be reported separately from reflection-consistency improvements.
- Shiny Blender Real remains excluded due to OOM and is not used for full FD-P2 claims.
- Original full FD-P2 and full 51-cell ablation claims remain NO-GO.

## 10. Limitations

- Shiny Blender Real is excluded due to persistent OOM blocker.
- Single-seed evidence only (seed 0).
- The completed package is narrowed to non-Shiny-Real datasets.
- No full 17-scene FD-P2 claim is supported.
- No full 51-cell ablation claim is supported.
- Metric-specific tradeoffs remain between reflection consistency and render quality.

## 11. Recommended next actions

1. Generate publication-ready tables and figures from the final scoped package.
2. Write a scope-limited Results section using the final analysis artifacts.
3. Optionally retry Shiny Blender Real only with higher-memory GPUs or a redesigned reduced-resolution protocol.
4. Do not start multi-seed experiments until the current scoped evidence is packaged.
5. Keep any manuscript updates explicitly limited to the FD-P2-lite / non-Shiny-Real scope.
