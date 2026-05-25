# RC-RefGS P4 i31000 Base-vs-RC Reflection Summary (teapot/toaster/car)

Date: 2026-05-25  
Source: `docs/superpowers/logs/rc-refgs-p4-manual-artifact-reconciliation-2026-05-25.json`  
Scope: `teapot/toaster/car x base/rc x i31000`, split = `train` + `test`

## Completion Reconciliation

- Matrix artifacts are complete: `6/6` cells, `18/18` expected artifacts present.
- Manual closeout reconciled for previously incomplete cells:
  - `toaster_rc`: manual full rerun + train/test reflection evaluation.
  - `car_base`: manual full rerun + train/test reflection evaluation.
  - `car_rc`: manual full rerun produced point cloud; later metrics-only rerun produced train/test reflection JSON after resolving a prior metric device-mismatch failure.

## Scene-Level Base-vs-RC Reflection Deltas (`rc - base`)

| Scene | Split | Delta mean_reflection_consistency | Delta reflective_region_psnr |
| --- | --- | ---:| ---:|
| teapot | train | -0.010081 | +0.304620 |
| teapot | test | -0.001458 | +0.292069 |
| toaster | train | -0.196750 | +0.313780 |
| toaster | test | -0.094231 | -0.018325 |
| car | train | -0.157372 | +0.026470 |
| car | test | -0.038506 | +0.122206 |

Interpretation rule used:
- lower `mean_reflection_consistency` is better
- higher `reflective_region_psnr` is better

## Aggregate Split Summary

| Split | Base avg mean_reflection_consistency | RC avg mean_reflection_consistency | Avg delta (`rc-base`) | RC wins (lower is better) |
| --- | ---:| ---:| ---:| ---:|
| train | 0.223496 | 0.102095 | -0.121401 | 3/3 |
| test | 0.081078 | 0.036346 | -0.044732 | 3/3 |

| Split | Base avg reflective_region_psnr | RC avg reflective_region_psnr | Avg delta (`rc-base`) | RC wins (higher is better) |
| --- | ---:| ---:| ---:| ---:|
| train | 33.896664 | 34.111620 | +0.214957 | 3/3 |
| test | 29.541148 | 29.673132 | +0.131983 | 2/3 |

## Boundary

- This is a single-seed full-horizon reflection summary only.
- No full ablation, no multi-seed, no geometry expansion, and no manuscript/scientific claim upgrade is made from this artifact.
