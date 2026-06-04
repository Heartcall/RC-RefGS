# RC-RefGS Quality-Preserving lam010 Four-Scene Pilot Analysis

Generated: 2026-06-04T04:01:31+08:00

## Executive Summary

Final pilot completion: **4/4 completed**. The completed scenes are `coffee`, `helmet`, `luyu`, and `teapot`. Shiny Blender Real was not run, the full 16-job pilot was not started, and this analysis did not launch training or metrics.

`rc_qp_lam010` is mixed. It preserves most base-vs-consistency gains, but it is weaker than the current `rc` variant on consistency. It improves many quality metrics over current `rc`, but not enough against `base` to justify a quality-preserving claim or direct full expansion.

Expansion decision: **do not expand directly to the full 16-job pilot now**. Run a narrower next sweep around `rc_qp_lam005` and `rc_qp_lam010_start5000_every8`, with `helmet` and `luyu` as priority stress scenes.

## Artifact Check

| Dataset | Scene | Required artifacts | Source path |
|---|---|---:|---|
| shiny_blender_synthetic | coffee | 5/5 | `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/coffee` |
| shiny_blender_synthetic | helmet | 5/5 | `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/helmet` |
| glossy_synthetic | luyu | 5/5 | `/data/liuly/dataset/3DGS/GlossySyntheticConverted/luyu_blender` |
| glossy_synthetic | teapot | 5/5 | `/data/liuly/dataset/3DGS/GlossySyntheticConverted/teapot_blender` |

Failed raw-path backup directories named `seed_0.failed_raw_glossy_path_20260604` were ignored.

## Aggregate Win Counts

| Split | Comparison | Consistency | Full quality | Reflective quality | All quality |
|---|---|---:|---:|---:|---:|
| train | rc_qp vs base | 4/4 | 6/12 | 4/12 | 10/24 |
| train | rc_qp vs rc | 0/4 | 10/12 | 11/12 | 21/24 |
| test | rc_qp vs base | 3/4 | 6/12 | 5/12 | 11/24 |
| test | rc_qp vs rc | 0/4 | 8/12 | 9/12 | 17/24 |

Lower is better for reflection consistency and LPIPS. Higher is better for PSNR and SSIM.

## Per-Scene Test Summary

| Dataset | Scene | Consistency vs base | Consistency vs rc | Quality wins vs base | Quality wins vs rc | Interpretation |
|---|---|---:|---:|---:|---:|---|
| shiny_blender_synthetic | coffee | False | False | 5/6 | 6/6 | Quality improves, but consistency remains the known test exception. |
| shiny_blender_synthetic | helmet | True | False | 0/6 | 0/6 | Worst pilot scene; quality and rc-level consistency both regress. |
| glossy_synthetic | luyu | True | False | 0/6 | 5/6 | Quality improves over rc but still trails base on all test quality metrics. |
| glossy_synthetic | teapot | True | False | 6/6 | 6/6 | Best pilot scene; quality beats both base and rc while retaining base consistency gain. |

## Per-Scene Metrics

### shiny_blender_synthetic / coffee

| Split | Metric | Base | RC | rc_qp_lam010 | Win vs base | Win vs rc |
|---|---|---:|---:|---:|---:|---:|
| train | mean_reflection_consistency | 0.0538857832551 | 0.0222299552523 | 0.0281347357202 | TRUE | FALSE |
| train | full_psnr | 39.0128235626 | 38.8458512497 | 38.9893872833 | FALSE | TRUE |
| train | full_ssim | 0.98340732336 | 0.983227201104 | 0.983787487149 | TRUE | TRUE |
| train | full_lpips | 0.0344631484151 | 0.0353838243335 | 0.0332308696117 | TRUE | TRUE |
| train | reflective_psnr | 42.3514097977 | 41.1987946701 | 42.2942978668 | FALSE | TRUE |
| train | reflective_ssim | 0.991609037519 | 0.99044829607 | 0.991371529102 | FALSE | TRUE |
| train | reflective_lpips | 0.00982107999967 | 0.011069074315 | 0.00987288075034 | FALSE | TRUE |
| test | mean_reflection_consistency | 0.00691277757287 | 0.00925146806985 | 0.00950876385905 | FALSE | FALSE |
| test | full_psnr | 34.6128314304 | 34.8738812447 | 34.9630744171 | TRUE | TRUE |
| test | full_ssim | 0.974197021723 | 0.974914058745 | 0.975091389716 | TRUE | TRUE |
| test | full_lpips | 0.0460944677796 | 0.0458372793999 | 0.0447970513161 | TRUE | TRUE |
| test | reflective_psnr | 37.0008195019 | 36.7495622444 | 37.447891798 | TRUE | TRUE |
| test | reflective_ssim | 0.985390269756 | 0.984255130589 | 0.985357004106 | FALSE | TRUE |
| test | reflective_lpips | 0.0134853238496 | 0.014355186841 | 0.0134496945655 | TRUE | TRUE |

### shiny_blender_synthetic / helmet

| Split | Metric | Base | RC | rc_qp_lam010 | Win vs base | Win vs rc |
|---|---|---:|---:|---:|---:|---:|
| train | mean_reflection_consistency | 0.640577447414 | 0.0895418930799 | 0.0978540290147 | TRUE | FALSE |
| train | full_psnr | 40.1417076874 | 40.051305542 | 40.1660605621 | TRUE | TRUE |
| train | full_ssim | 0.993489298224 | 0.993292196989 | 0.993429845572 | FALSE | TRUE |
| train | full_lpips | 0.00633137773257 | 0.00645906769671 | 0.00652566800825 | FALSE | FALSE |
| train | reflective_psnr | 40.8460811996 | 40.7701453781 | 40.8880712509 | TRUE | TRUE |
| train | reflective_ssim | 0.994107502103 | 0.993927591443 | 0.994082311392 | FALSE | TRUE |
| train | reflective_lpips | 0.00499711540295 | 0.00511385741876 | 0.00517804526491 | FALSE | FALSE |
| test | mean_reflection_consistency | 0.216838933527 | 0.0359569136053 | 0.0389604449272 | TRUE | FALSE |
| test | full_psnr | 35.8392297745 | 35.9123687553 | 35.6922024536 | FALSE | FALSE |
| test | full_ssim | 0.985016433299 | 0.985004830658 | 0.984486527443 | FALSE | FALSE |
| test | full_lpips | 0.0146340828622 | 0.0146680492209 | 0.015002853875 | FALSE | FALSE |
| test | reflective_psnr | 36.4629203129 | 36.5550987053 | 36.31802701 | FALSE | FALSE |
| test | reflective_ssim | 0.986908330023 | 0.986920369565 | 0.986445338726 | FALSE | FALSE |
| test | reflective_lpips | 0.0113525103149 | 0.0113222172973 | 0.0117289610812 | FALSE | FALSE |

### glossy_synthetic / luyu

| Split | Metric | Base | RC | rc_qp_lam010 | Win vs base | Win vs rc |
|---|---|---:|---:|---:|---:|---:|
| train | mean_reflection_consistency | 0.118880660087 | 0.110039874166 | 0.115317115188 | TRUE | FALSE |
| train | full_psnr | 32.0753399815 | 31.6153134789 | 31.9564231804 | FALSE | TRUE |
| train | full_ssim | 0.966454624065 | 0.966079334595 | 0.965698321483 | FALSE | FALSE |
| train | full_lpips | 0.0314378451855 | 0.0326743896751 | 0.0321352286431 | FALSE | TRUE |
| train | reflective_psnr | 33.9542378698 | 33.3053354876 | 33.9518160479 | FALSE | TRUE |
| train | reflective_ssim | 0.979644142623 | 0.97896852025 | 0.979634701141 | FALSE | TRUE |
| train | reflective_lpips | 0.0195913613009 | 0.0212975137983 | 0.0197575792055 | FALSE | TRUE |
| test | mean_reflection_consistency | 0.124420511723 | 0.119502235204 | 0.122564553469 | TRUE | FALSE |
| test | full_psnr | 29.4777971506 | 29.0562040806 | 29.2722738981 | FALSE | TRUE |
| test | full_ssim | 0.947934940457 | 0.947979975492 | 0.94689290598 | FALSE | FALSE |
| test | full_lpips | 0.0375685002655 | 0.0391065921867 | 0.0381974545307 | FALSE | TRUE |
| test | reflective_psnr | 31.3694570065 | 30.7136751413 | 31.1600471735 | FALSE | TRUE |
| test | reflective_ssim | 0.968790642917 | 0.967797785997 | 0.968595538288 | FALSE | TRUE |
| test | reflective_lpips | 0.0247649874073 | 0.0271824040683 | 0.0254110972164 | FALSE | TRUE |

### glossy_synthetic / teapot

| Split | Metric | Base | RC | rc_qp_lam010 | Win vs base | Win vs rc |
|---|---|---:|---:|---:|---:|---:|
| train | mean_reflection_consistency | 0.335104346275 | 0.294280053675 | 0.306185293198 | TRUE | FALSE |
| train | full_psnr | 29.8696459021 | 30.0148143598 | 30.1680472408 | TRUE | TRUE |
| train | full_ssim | 0.968270107572 | 0.969185413527 | 0.969909928739 | TRUE | TRUE |
| train | full_lpips | 0.038586791006 | 0.0383540912797 | 0.0372852646313 | TRUE | TRUE |
| train | reflective_psnr | 30.5104755163 | 30.4758541414 | 30.6357427325 | TRUE | TRUE |
| train | reflective_ssim | 0.971274278526 | 0.971477758139 | 0.972354170999 | TRUE | TRUE |
| train | reflective_lpips | 0.0329098770328 | 0.0330767084878 | 0.0322346746023 | TRUE | TRUE |
| test | mean_reflection_consistency | 0.295932878554 | 0.252433353662 | 0.262338533998 | TRUE | FALSE |
| test | full_psnr | 26.5828143358 | 26.751352787 | 26.8090282679 | TRUE | TRUE |
| test | full_ssim | 0.944871343672 | 0.946739990264 | 0.94757752493 | TRUE | TRUE |
| test | full_lpips | 0.0511018079706 | 0.0500873576384 | 0.0482428383548 | TRUE | TRUE |
| test | reflective_psnr | 27.2015644312 | 27.2088465691 | 27.3453389406 | TRUE | TRUE |
| test | reflective_ssim | 0.951212920249 | 0.9515491575 | 0.953435946256 | TRUE | TRUE |
| test | reflective_lpips | 0.0438581835479 | 0.0430140802637 | 0.0410339867231 | TRUE | TRUE |

## Interpretation

- Consistency: `rc_qp_lam010` beats base in 7/8 train/test scene pairs, including 3/4 test scenes, but loses to current `rc` in 8/8 pairs. It preserves most base-level consistency gain, not the full current-RC gain.
- Quality versus current `rc`: test quality improves in 17/24 metrics, including 8/12 full-image metrics and 9/12 reflective-region metrics. This indicates the lower RC weight helps quality tradeoffs relative to current `rc`.
- Quality versus base: test quality improves in only 11/24 metrics, including 6/12 full-image metrics and 5/12 reflective-region metrics. That is insufficient for a quality-preserving claim.
- Dataset/scene dependence is strong: `glossy_synthetic/teapot` is favorable, `shiny_blender_synthetic/helmet` is unfavorable, `glossy_synthetic/luyu` improves over `rc` but not base, and `coffee` retains the known test consistency exception while improving quality.

## Expansion Decision

Do **not** expand directly to the full 16-job pilot from this evidence alone. The result is promising as a diagnostic because `rc_qp_lam010` improves many quality metrics over current `rc`, but it does not beat base broadly enough and weakens consistency relative to `rc`.

Recommended next step is a narrower variant/schedule sweep before full expansion:

- `rc_qp_lam005`: test whether lower reflection-consistency weight restores base-level quality while retaining most consistency gain.
- `rc_qp_lam010_start5000_every8`: test whether delayed/lower-frequency consistency improves `helmet` and `luyu`.
- If compute is constrained, run those first on `helmet` and `luyu`; if they improve, then expand to the remaining planned matrix.

## Claim Boundary

This is a 4-scene, seed-0 pilot only. It does not establish global quality-preserving RC. The original FD-P2-lite main result remains unchanged: RC strongly improves reflection consistency while LPIPS/PSNR/SSIM quality tradeoffs remain mixed.
