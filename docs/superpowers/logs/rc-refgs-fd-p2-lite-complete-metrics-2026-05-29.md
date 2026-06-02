# RC-RefGS FD-P2-lite / Non-Shiny-Real Final Complete-Metric Analysis

## 1. Executive summary
- Render-quality artifact coverage: **70/70** (main 28/28, ablation 42/42).
- Strict required-field coverage: **70/70** (main 28/28, ablation 42/42).
- LPIPS omissions on `ball/base`, `ball/rc`, and `car/base` were recovered in this task.
- Decision: **GO** for non-Shiny-Real complete-metric package under strict parsing.

## 2. Scope and boundaries
- Included: Shiny Blender Synthetic + Glossy Synthetic (14 scenes), seed 0.
- Excluded: Shiny Blender Real (OOM-blocked; still outside this narrowed scope).
- Full 17-scene FD-P2 and full 51-cell ablation claims remain NO-GO.

## 3. Coverage details
- Main strict complete models: **28/28**
- Ablation strict complete models: **42/42**
- Parsed ambiguities: **0**

## 4. Main base-vs-RC summary
- `mean_reflection_consistency` RC wins: train 14/14 (available), test 13/14 (available).
- `reflective_region_psnr` RC wins: train 7/14 (available), test 8/14 (available).
- `full_psnr` RC wins: train 9/14 (available), test 10/14 (available).
- `full_ssim` RC wins: train 9/14 (available), test 11/14 (available).
- `full_lpips` RC wins: train 9/14 (available), test 10/14 (available).
- `reflective_psnr` RC wins: train 6/14 (available), test 10/14 (available).
- `reflective_ssim` RC wins: train 7/14 (available), test 7/14 (available).
- `reflective_lpips` RC wins: train 4/14 (available), test 6/14 (available).

## 5. Tradeoff counts
- consistency improves but quality worsens: 21 split-cases
- reflective improves but full-image worsens: 6 split-cases
- any metric worsened: 22 split-cases

## 6. LPIPS recovery note
- Per-cell manual logs for these three cells showed they were previously skipped as already-valid artifacts; no retained per-cell LPIPS exception stack was present in those logs.
- Recovery reruns were executed with LPIPS enabled on GPU7 (`image_key=pbr_rgb`) and now produce numeric `full_lpips`/`reflective_lpips` for train and test in all three target JSONs.
