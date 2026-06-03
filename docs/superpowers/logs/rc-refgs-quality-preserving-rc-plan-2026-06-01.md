# RC-RefGS Quality-Preserving RC Plan - 2026-06-01

## Objective

Design and later evaluate a quality-preserving RC variant that can beat or match base on PSNR/SSIM/LPIPS while retaining most of the reflection-consistency gain. This plan is not an implementation approval and launches no experiments.

## Non-Negotiable Claim/Evaluation Rules

- Do not change headline metric definitions, masks, splits, image_key, or LPIPS settings.
- Do not run Shiny Blender Real in this pilot scope.
- Do not overwrite base, rc, or existing ablation outputs.
- Use new output root /tmp/rc_refgs_quality_preserving_rc_i31000_20260601 and rc_qp_* variant names.
- Do not claim the quality-preserving variant exceeds base until paired experiments prove it.

## Candidate Variants

| variant | lambda_ref_consistency | start | every | gamma | lambda_dssim | expected_effect |
| --- | --- | --- | --- | --- | --- | --- |
| rc_qp_lam005 | 0.005 | 3000 | 4 | 2.0 | 0.2 | largest reduction in RC pressure; should reduce quality regressions but may lose some consistency gain |
| rc_qp_lam010 | 0.01 | 3000 | 4 | 2.0 | 0.2 | middle point likely to preserve most consistency gain while easing quality pressure |
| rc_qp_lam010_start5000_every8 | 0.01 | 5000 | 8 | 2.0 | 0.2 | lets reconstruction settle and halves RC update frequency; primary quality-preserving schedule candidate |
| rc_qp_lam010_gamma10 | 0.01 | 3000 | 4 | 1.0 | 0.2 | tests whether confidence weighting sharpness contributes to reflective-region quality regressions |
| rc_qp_lam015 | 0.015 | 3000 | 4 | 2.0 | 0.2 | phase-2 bridge toward current rc baseline if 0.005/0.010 underfit consistency |
| rc_qp_lam010_start7000_every8 | 0.01 | 7000 | 8 | 2.0 | 0.2 | phase-2 delayed-start diagnostic if start5000 still harms quality |
| rc_qp_lam010_gamma15 | 0.01 | 3000 | 4 | 1.5 | 0.2 | phase-2 middle confidence weighting diagnostic |

First-wave pilot cap: use only `rc_qp_lam005`, `rc_qp_lam010`, `rc_qp_lam010_start5000_every8`, and `rc_qp_lam010_gamma10` for `4 scenes x 4 configs = 16 jobs`. Hold `rc_qp_lam015`, `start7000`, gamma `1.5`, LPIPS-loss, and DSSIM sweeps for phase 2.

## Pilot Scene Selection

| dataset | scene | selection_reason | evidence |
| --- | --- | --- | --- |
| shiny_blender_synthetic | helmet | strongest consistency gain with quality regression signal | test consistency delta -0.180882; test full LPIPS delta +0.00003397 and full SSIM delta -0.0000116 |
| shiny_blender_synthetic | coffee | test consistency exception | test consistency delta +0.002339; reflective PSNR/SSIM/LPIPS all regress on test |
| glossy_synthetic | luyu | worst combined test full and reflective quality regression among Glossy Synthetic scenes | test full LPIPS delta +0.001538; reflective LPIPS delta +0.002417; full PSNR delta -0.421593; reflective PSNR delta -0.655782 |
| glossy_synthetic | teapot | control scene where RC improves consistency and all six test quality metrics | test consistency delta -0.043500; full/reflective PSNR, SSIM, and LPIPS all improve on test |

Full pilot matrix CSV: `docs/superpowers/logs/rc-refgs-quality-regression-target-scenes-2026-06-01.csv`

## Commands To Run Later

Launcher status: current launchers do not support new `rc_qp_*` variants. Direct `train.py` can run a single pilot cell today; batch-safe launcher execution needs the minimal extension below.

Example pilot cell: `shiny_blender_synthetic/helmet`, variant `rc_qp_lam010_start5000_every8`.

- Source path: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/helmet`
- Model path: `/tmp/rc_refgs_quality_preserving_rc_i31000_20260601/shiny_blender_synthetic/helmet/rc_qp_lam010_start5000_every8/seed_0`

Train command:

```bash
conda run -n ref_gs python train.py --cuda_device 0 -s "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/helmet" -m /tmp/rc_refgs_quality_preserving_rc_i31000_20260601/shiny_blender_synthetic/helmet/rc_qp_lam010_start5000_every8/seed_0 --eval --iterations 31000 --test_iterations 31000 --save_iterations 31000 --seed 0 --lambda_ref_consistency 0.01 --ref_consistency_start 5000 --ref_consistency_every 8 --ref_consistency_max_angle 20.0 --ref_consistency_gamma 2.0
```

Reflection metric command:

```bash
conda run -n ref_gs python metrics/reflection_consistency_eval.py --cuda_device 0 --model_path /tmp/rc_refgs_quality_preserving_rc_i31000_20260601/shiny_blender_synthetic/helmet/rc_qp_lam010_start5000_every8/seed_0 --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/helmet" --iteration 31000 --split test --max_pairs 10 --max_angle_deg 20.0 --gamma 2.0 --output_json /tmp/rc_refgs_quality_preserving_rc_i31000_20260601/shiny_blender_synthetic/helmet/rc_qp_lam010_start5000_every8/seed_0/reflection_consistency_test.json
```

Render-quality metric command:

```bash
conda run -n ref_gs python metrics/render_quality_eval.py --cuda_device 0 --model_path /tmp/rc_refgs_quality_preserving_rc_i31000_20260601/shiny_blender_synthetic/helmet/rc_qp_lam010_start5000_every8/seed_0 --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/helmet" --iteration 31000 --split both --mask_mode both --image_key pbr_rgb --output_json /tmp/rc_refgs_quality_preserving_rc_i31000_20260601/shiny_blender_synthetic/helmet/rc_qp_lam010_start5000_every8/seed_0/render_quality_both_iter31000.json
```

## Minimal Launcher Extension

- Add rc_qp_* variant metadata support in scripts/run_rc_refgs_ablation_direct.py without changing existing variant behavior.
- Allow safe extra_train_args or explicit per-variant config fields only for new rc_qp_* variants.
- Update full-dataset runner variant validation to accept rc_qp_* only when metadata is supplied.
- Add static tests for command construction and unknown-variant rejection.

Preserve existing `base`, `rc`, `wo_ref`, `wo_conf`, and `rough_only` behavior. Add tests that verify command construction for one `rc_qp_*` variant and unknown-variant rejection when metadata is missing.

## Acceptance Criteria

- Per target scene: lower test mean reflection consistency than base; beat base on test full LPIPS, full PSNR, and full SSIM where possible; beat or match base on reflective LPIPS, PSNR, and SSIM where possible.
- Across scoped scenes: at least `12/14` test reflection-consistency wins, at least `12/14` test full LPIPS wins, and at least `12/14` test full PSNR or full SSIM wins before any broader quality-preserving claim.
- If all metrics exceeding base is infeasible, document the exact Pareto tradeoff and choose the setting that increases quality wins without erasing consistency gains.

## Stop Criteria

- Stop a candidate if it loses test consistency versus base on more than one pilot scene.
- Stop a candidate if it worsens test full LPIPS and full PSNR on two or more pilot scenes.
- Stop full-scope expansion if pilot results only shift the consistency-quality tradeoff without increasing Pareto wins.

## How To Update Claims If Quality Improves

- Report first as pilot evidence only, with scene list, seed, output root, and exact command/config.
- Keep Shiny Blender Real excluded and full 17-scene / 51-cell claims NO-GO until required full-dataset evidence exists.
- Do not merge pilot results into current base/rc/ablation artifacts or relabel existing results.

## How To Report If The Tradeoff Remains

- State that RC is effective as a reflection-consistency regularizer but remains mixed for PSNR/SSIM/LPIPS.
- Preserve the current claim boundary: consistency gains are supported in FD-P2-lite / non-Shiny-Real scope, broad rendering-quality gains remain unsupported.
- Use the best Pareto setting only if it improves a documented metric frontier; otherwise keep current RC as the reflection-consistency baseline and avoid quality-preserving claims.
