# RC-RefGS Next Modification Stage 1 - rc_qp_angle10_sched Analysis

## Executive Summary

The completed two-scene Stage 1 run for `rc_qp_angle10_sched` is analyzable: `2/2` jobs completed at iteration `31000`, with fixed `pbr_rgb` render-quality metrics and train/test reflection-consistency metrics present. No Shiny Blender Real, full 16-job pilot, 14-scene validation, metric changes, or global claim is involved.

Result: `rc_qp_angle10_sched` is **not worth expanding** to 4-scene confirmation. It is not Pareto-better than the prior best pure schedule variant (`rc_qp_lam010_start5000_every8`) on helmet/luyu, and it clearly fails the base-quality target.

Decision: **GO for analysis; NO-GO for 4-scene expansion**.

## Completion Status

| dataset | scene | status | required artifacts |
| --- | --- | --- | --- |
| `shiny_blender_synthetic` | `helmet` | completed | 5/5 |
| `glossy_synthetic` | `luyu` | completed | 5/5 |

Manual CUDA preflight passed in `pilot_status.json`: `CUDA_VISIBLE_DEVICES=0`, `torch_cuda_available=true`, `torch_device_count=1`, device `NVIDIA RTX A5000`.

## Test-Split Win Counts

| reference | consistency wins | quality wins | expansion implication |
| --- | ---: | ---: | --- |
| `base` | 1/2 | 0/12 | insufficient |
| `rc` | 0/2 | 0/12 | diagnostic |
| `rc_qp_lam010` | 0/2 | 7/12 | diagnostic |
| `rc_qp_lam005` | 0/2 | 6/12 | diagnostic |
| `rc_qp_lam010_start5000_every8` | 1/2 | 4/12 | insufficient |

Quality metrics are `full_psnr`, `full_ssim`, `full_lpips`, `reflective_psnr`, `reflective_ssim`, and `reflective_lpips`; LPIPS and reflection consistency are lower-is-better.

## Per-Scene Test Metrics

| dataset | scene | variant | consistency | full_psnr | full_ssim | full_lpips | reflective_psnr | reflective_ssim | reflective_lpips |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `shiny_blender_synthetic` | `helmet` | `base` | 0.216838933527 | 35.8392297745 | 0.985016433299 | 0.0146340828622 | 36.4629203129 | 0.986908330023 | 0.0113525103149 |
| `shiny_blender_synthetic` | `helmet` | `rc` | 0.0359569136053 | 35.9123687553 | 0.985004830658 | 0.0146680492209 | 36.5550987053 | 0.986920369565 | 0.0113222172973 |
| `shiny_blender_synthetic` | `helmet` | `rc_qp_lam010` | 0.0389604449272 | 35.6922024536 | 0.984486527443 | 0.015002853875 | 36.31802701 | 0.986445338726 | 0.0117289610812 |
| `shiny_blender_synthetic` | `helmet` | `rc_qp_lam005` | 0.0475879747421 | 35.6341431141 | 0.984747545421 | 0.0151425805897 | 36.2513000107 | 0.98667044878 | 0.011743516454 |
| `shiny_blender_synthetic` | `helmet` | `rc_qp_lam010_start5000_every8` | 0.043885826692 | 35.7659474468 | 0.984887879789 | 0.0145856592664 | 36.3615517426 | 0.986776240468 | 0.0112855523452 |
| `shiny_blender_synthetic` | `helmet` | `rc_qp_angle10_sched` | 0.0481265626848 | 35.7744579315 | 0.98499209553 | 0.0147441232647 | 36.377449646 | 0.986840356588 | 0.0114767128765 |
| `glossy_synthetic` | `luyu` | `base` | 0.124420511723 | 29.4777971506 | 0.947934940457 | 0.0375685002655 | 31.3694570065 | 0.968790642917 | 0.0247649874073 |
| `glossy_synthetic` | `luyu` | `rc` | 0.119502235204 | 29.0562040806 | 0.947979975492 | 0.0391065921867 | 30.7136751413 | 0.967797785997 | 0.0271824040683 |
| `glossy_synthetic` | `luyu` | `rc_qp_lam010` | 0.122564553469 | 29.2722738981 | 0.94689290598 | 0.0381974545307 | 31.1600471735 | 0.968595538288 | 0.0254110972164 |
| `glossy_synthetic` | `luyu` | `rc_qp_lam005` | 0.125775631517 | 29.2969816923 | 0.947662848979 | 0.0386610424612 | 31.1597456932 | 0.968465406448 | 0.0263208698016 |
| `glossy_synthetic` | `luyu` | `rc_qp_lam010_start5000_every8` | 0.128366740048 | 29.3571181297 | 0.947377122939 | 0.0379283421207 | 31.2642651796 | 0.968813195825 | 0.0247948238393 |
| `glossy_synthetic` | `luyu` | `rc_qp_angle10_sched` | 0.128296046704 | 28.9760224819 | 0.946933355182 | 0.039406096912 | 30.5398204327 | 0.966637872159 | 0.0278810174204 |

## Interpretation

- Versus base: `rc_qp_angle10_sched` wins `1/2` test consistency scenes and `0/12` test quality metrics. This is far below the later 14-scene success target.
- Versus current `rc`: it wins `0/12` test quality metrics and `0/2` consistency scenes. It does not preserve the current RC consistency strength.
- Versus prior `rc_qp_lam010_start5000_every8`: it wins only `4/12` test quality metrics and `1/2` consistency scenes, so the angle-aware gate is not Pareto-better than the best pure schedule candidate on this stress pair.
- Both scenes block expansion on quality: helmet retains a consistency win vs base but loses all six test quality metrics, while luyu loses both consistency and all six test quality metrics vs base.

## Expansion Decision

Do not expand `rc_qp_angle10_sched` to 4 scenes. The next useful direction should not be this strict angle gate as-is. A more plausible follow-up would be a confidence-gated or softer hybrid variant, but that requires a separate scoped task and new evidence.

## Claim Boundary

This is a two-scene Stage 1 analysis only. It does not support a global RC-RefGS-over-Ref-GS claim, does not alter FD-P2-lite conclusions, does not include Shiny Blender Real, and does not change metric definitions.
