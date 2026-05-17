# RC-RefGS Claim-Framing Audit

Date: 2026-05-17 19:43 CST

Scope: Audit the three-scene i300 evidence currently available for RC-RefGS claim framing. This is a research-side audit, not a new implementation or training run.

## Evidence Audited

All runs used held-out Blender split preservation via `--eval`, 300 training iterations, and `metrics/reflection_consistency_eval.py` with `--max_pairs 10 --max_angle_deg 180`.

| Scene | Split | Baseline reflection error | RC reflection error | Direction | Baseline reflective PSNR | RC reflective PSNR | Direction |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| teapot | train | 0.0039707922 | 0.0039400090 | RC lower | 22.43657 | 22.47500 | RC higher |
| teapot | test | 0.0018443021 | 0.0018346125 | RC lower | 23.03556 | 23.17403 | RC higher |
| toaster | train | 0.0030678714 | 0.0029527844 | RC lower | 12.52431 | 12.52055 | RC lower |
| toaster | test | 0.0025387909 | 0.0024728895 | RC lower | 11.38461 | 11.38067 | RC lower |
| car | train | 0.0022612946 | 0.0021638940 | RC lower | 12.64239 | 12.61926 | RC lower |
| car | test | 0.0012749511 | 0.0012496432 | RC lower | 14.07574 | 14.06942 | RC lower |

Every row used `num_pairs=10` for both baseline and RC.

## Claims Allowed Now

- [Citation] The implemented RC-RefGS path exposes Ref-GS intermediate buffers and adds a gated cross-view reflection-consistency loss without replacing the base representation or renderer.
- [Citation] On the three audited RefNeRF scenes (`teapot`, `toaster`, `car`) at 300 iterations, RC has lower measured reprojected reflection-consistency error than the matched baseline on both train and held-out test splits.
- [Reasoning] The evidence supports framing RC-RefGS as a method that directly optimizes and improves a reflection-consistency diagnostic under this short-run protocol.
- [Hypothesis] The reflection-consistency improvement may become more meaningful at longer training horizons or with stronger view-pair schedules, but this requires further experiments.

## Claims That Must Be Qualified

- [Reasoning] Rendering-quality claims are mixed under current evidence: reflection-consistency error improves on all three scenes, standard PSNR/SSIM improves on `teapot`, standard PSNR is slightly lower on `toaster` and `car`, and standard SSIM is mixed by scene.
- [Reasoning] Current evidence is short-run only: 300 iterations, one seed, three scenes, and 10 sampled pairs per split.
- [Reasoning] The current metric is pair-sampling dependent because it uses `choose_pair_camera` and a capped number of pairs; report the pair count and angle threshold with results.
- [Reasoning] Standard PSNR/SSIM were collected with `metrics/render_quality_eval.py --split both --mask_mode both --skip_lpips`; LPIPS remains unverified in this evidence set because it was intentionally skipped to avoid network-dependent weight downloads.
- [Reasoning] Normal diagnostics are preliminary but broader than before: a full-split sweep with the validated raw GT-normal interpretation improves angular MAE and mean cosine on all six scene/split rows, but the deltas are small and no mesh/reference-geometry metrics have been run.

## Claims Not Supported Yet

- [Unsupported] Do not claim overall novel-view rendering improvement. Standard PSNR/SSIM are mixed across the three audited scenes, and LPIPS is not yet available for these runs.
- [Unsupported] Do not claim mesh or surface reconstruction improvement. Normal diagnostics are small and mixed, and no Chamfer/F-score, mesh connected-component count, or TSDF quality metric has been run.
- [Unsupported] Do not claim improved material decomposition. No albedo variance, roughness stability, relighting, or material-specific diagnostic has been run.
- [Unsupported] Do not claim full Ref-GS superiority over external methods such as 2DGS, MaterialRefGS, SSR-GS, GS-2M, or paper baselines. No external baseline runs or cited paper-number comparison has been audited.
- [Unsupported] Do not claim the reflective-region PSNR trend is positive. It is mixed and currently negative on two of the three audited scenes.

## Recommended Framing

Use this as the current central empirical statement:

> [Citation] In short i300 held-out split sanity runs on `teapot`, `toaster`, and `car`, RC-RefGS consistently reduces the measured reprojected reflection-consistency error relative to the matched Ref-GS baseline. [Reasoning] This supports the method's intended optimization target, but not yet a broad rendering or geometry quality claim because standard full-image and reflective-mask PSNR/SSIM are mixed, LPIPS was skipped, and normal diagnostics are small-magnitude diagnostic evidence rather than mesh/reference-geometry evidence.

## Standard Rendering Metrics Added

Date: 2026-05-17 21:55 CST

All rows used `metrics/render_quality_eval.py --split both --mask_mode both --skip_lpips` on the existing i300 baseline and RC outputs. LPIPS fields are present in the JSON as `null` because LPIPS was skipped.

| Scene | Split | Images | Base full PSNR | RC full PSNR | Delta | Base full SSIM | RC full SSIM | Delta | Base reflective PSNR | RC reflective PSNR | Delta | Base reflective SSIM | RC reflective SSIM | Delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| teapot | train | 100 | 32.439304 | 32.477029 | +0.037726 | 0.980768 | 0.980926 | +0.000157 | 32.519255 | 32.556076 | +0.036821 | 0.983348 | 0.983439 | +0.000091 |
| teapot | test | 200 | 32.073170 | 32.114460 | +0.041289 | 0.979763 | 0.979891 | +0.000129 | 32.171206 | 32.209708 | +0.038502 | 0.982758 | 0.982821 | +0.000063 |
| toaster | train | 100 | 15.681681 | 15.678951 | -0.002730 | 0.757115 | 0.757437 | +0.000322 | 15.688060 | 15.685283 | -0.002777 | 0.772835 | 0.773084 | +0.000249 |
| toaster | test | 200 | 15.156367 | 15.154467 | -0.001900 | 0.746358 | 0.746698 | +0.000340 | 15.162786 | 15.160840 | -0.001946 | 0.764650 | 0.764830 | +0.000180 |
| car | train | 100 | 18.450134 | 18.440332 | -0.009803 | 0.827930 | 0.827766 | -0.000164 | 18.510903 | 18.495415 | -0.015488 | 0.841613 | 0.841492 | -0.000121 |
| car | test | 200 | 18.635364 | 18.629492 | -0.005872 | 0.824684 | 0.824566 | -0.000118 | 18.660756 | 18.655019 | -0.005737 | 0.842216 | 0.842153 | -0.000063 |

[Reasoning] These standard PSNR/SSIM results reinforce the conservative framing: RC improves the intended reflection-consistency diagnostic, but does not yet support an overall rendering-quality improvement claim.

## Normal Diagnostics Added

Date: 2026-05-18 01:11 CST

All rows used `metrics/normal_quality_eval.py --split both --max_images 10 --normal_key rend_normal` on existing i300 baseline and RC outputs. Lower normal MAE is better; higher mean cosine is better. These are diagnostic only because the RefNeRF normal-map coordinate convention has not been independently audited.

| Scene | Split | Images | Base normal MAE | RC normal MAE | Delta | Base cosine | RC cosine | Delta | Base reflective MAE | RC reflective MAE | Delta | Base reflective cosine | RC reflective cosine | Delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| teapot | train | 10 | 32.758381 | 32.452056 | -0.306325 | 0.783338 | 0.785723 | +0.002384 | 32.787696 | 32.452044 | -0.335652 | 0.783086 | 0.785722 | +0.002637 |
| teapot | test | 10 | 30.333576 | 30.021443 | -0.312133 | 0.817596 | 0.819446 | +0.001850 | 30.430115 | 30.016101 | -0.414013 | 0.816790 | 0.819497 | +0.002707 |
| toaster | train | 10 | 36.835108 | 36.825683 | -0.009425 | 0.740339 | 0.740811 | +0.000473 | 36.835108 | 36.825683 | -0.009425 | 0.740339 | 0.740811 | +0.000473 |
| toaster | test | 10 | 45.962905 | 45.805554 | -0.157351 | 0.647346 | 0.649304 | +0.001957 | 45.962905 | 45.805554 | -0.157351 | 0.647346 | 0.649304 | +0.001957 |
| car | train | 10 | 35.754578 | 35.740965 | -0.013614 | 0.754170 | 0.753897 | -0.000273 | 35.754578 | 35.740965 | -0.013614 | 0.754170 | 0.753897 | -0.000273 |
| car | test | 10 | 30.289805 | 30.533033 | +0.243227 | 0.815701 | 0.812674 | -0.003027 | 30.289805 | 30.533033 | +0.243227 | 0.815701 | 0.812674 | -0.003027 |

[Reasoning] The normal diagnostic trend is mostly favorable but not uniform. It is insufficient for a geometry claim because it is max-10 only and lacks mesh/reference-geometry metrics.

## Normal Coordinate Convention Audit Added

Date: 2026-05-18 01:27 CST

The evaluator now exposes `--gt_normal_space {raw,blender_world_to_colmap,opengl_camera_to_world}` while preserving `raw` as the default. A bounded baseline-only convention audit compared these three interpretations on the existing i300 baseline outputs with `--split both --max_images 5 --normal_key rend_normal`. Lower MAE and higher cosine are better.

| Scene | Split | Best space | Raw MAE | Blender->COLMAP MAE | OpenGL-camera->world MAE | Raw cosine | Blender->COLMAP cosine | OpenGL-camera->world cosine |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| teapot | train | raw | 31.983499 | 123.200294 | 49.239782 | 0.792955 | -0.450730 | 0.582934 |
| teapot | test | raw | 30.227852 | 133.672966 | 63.390974 | 0.818411 | -0.615333 | 0.385957 |
| toaster | train | raw | 40.866046 | 88.120789 | 74.087781 | 0.697575 | 0.000108 | 0.233159 |
| toaster | test | raw | 46.581565 | 128.463862 | 60.114358 | 0.637763 | -0.560553 | 0.425848 |
| car | train | raw | 40.025168 | 105.238936 | 55.871046 | 0.702184 | -0.227611 | 0.489963 |
| car | test | raw | 29.707215 | 146.539453 | 36.907460 | 0.818702 | -0.771725 | 0.752702 |

[Reasoning] The sampled evidence supports comparing rendered world normals directly against the raw RefNeRF normal PNG encoding in this repo. It strongly disfavors treating the PNGs as Blender-world normals requiring a Y/Z flip or as OpenGL camera-space normals. This validates the evaluator convention for diagnostic use only; it does not create mesh or reconstruction-quality evidence.

## Full-Split Normal Diagnostics Added

Date: 2026-05-18 02:27 CST

All rows used `metrics/normal_quality_eval.py --split both --normal_key rend_normal --gt_normal_space raw` on the existing i300 baseline and RC outputs. Lower normal MAE is better; higher mean cosine is better.

| Scene | Split | Images | Base normal MAE | RC normal MAE | Delta | Base cosine | RC cosine | Delta | Base reflective MAE | RC reflective MAE | Delta | Base reflective cosine | RC reflective cosine | Delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| teapot | train | 100 | 33.643254 | 33.371342 | -0.271912 | 0.774773 | 0.776746 | +0.001974 | 33.688870 | 33.370734 | -0.318136 | 0.774390 | 0.776752 | +0.002362 |
| teapot | test | 200 | 36.097747 | 35.809875 | -0.287872 | 0.746387 | 0.748793 | +0.002405 | 36.136722 | 35.809423 | -0.327299 | 0.746058 | 0.748797 | +0.002739 |
| toaster | train | 100 | 38.870086 | 38.849698 | -0.020388 | 0.720695 | 0.721056 | +0.000361 | 38.870086 | 38.849698 | -0.020388 | 0.720695 | 0.721056 | +0.000361 |
| toaster | test | 200 | 38.979297 | 38.927241 | -0.052056 | 0.717666 | 0.718360 | +0.000694 | 38.979297 | 38.927241 | -0.052056 | 0.717666 | 0.718360 | +0.000694 |
| car | train | 100 | 35.469802 | 35.441386 | -0.028416 | 0.754837 | 0.755093 | +0.000256 | 35.469802 | 35.441386 | -0.028416 | 0.754837 | 0.755093 | +0.000256 |
| car | test | 200 | 37.944846 | 37.912114 | -0.032733 | 0.726169 | 0.726579 | +0.000409 | 37.944846 | 37.912114 | -0.032733 | 0.726169 | 0.726579 | +0.000409 |

[Reasoning] The full-split normal diagnostics are directionally consistent: RC improves angular MAE and mean cosine on all audited scene/split rows. The magnitude is small, especially on `toaster` and `car`, and the evidence remains a normal-map diagnostic rather than a mesh or reconstruction-quality result.

## Minimum Next Evidence

1. Add LPIPS evidence for full images and reflective masks, either by using cached weights or by explicitly approving network-dependent weight downloads.
2. Run longer matched training for at least `teapot`, `toaster`, and `car`, preferably with the same seed and held-out split preservation.
3. Report pair-count and selection policy for reflection-consistency metrics.
4. Add stronger geometry evidence before making surface reconstruction claims: mesh metrics where reference geometry is available, such as Chamfer/F-score, connected component count, or depth-to-mesh reprojection diagnostics.
5. Add ablations before attributing causality beyond the single RC-vs-baseline contrast: `w/o L_ref`, `w/o specular confidence`, and roughness-only regularization.

## Decision

CONDITIONAL GO for research framing:

- GO to describe RC-RefGS as improving the targeted reflection-consistency diagnostic under the current i300 three-scene protocol.
- CONDITIONAL on stronger standard rendering evidence, LPIPS, and geometry metrics before claiming better novel-view synthesis, reconstruction, or material quality.
- SWITCH MODEL recommended for paper-claim drafting and experiment-priority decisions; stay in coding mode for evaluator implementation.
