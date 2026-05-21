# RC-RefGS Corrected i300 Validation Results

Date: 2026-05-20
Matrix: `teapot/toaster/car` x `base/rc`, seed 0, iteration 300
Output root: `/tmp/rc_refgs_i300_validation_base_rc_20260520`

## Execution

- Launcher: `scripts/run_rc_refgs_ablation_direct.py`
- Manifest: `docs/superpowers/logs/rc-refgs-i300-validation-manifest-2026-05-20.json`
- CUDA device override: `0`
- RC schedule: `ref_consistency_start=60`, `ref_consistency_every=4`
- Metric: dynamic-pair reflection consistency, `max_pairs=10`, train/test splits

## Artifact Check

- Expected artifacts: 18
- Found artifacts: 18
- Missing after run: 0

Each of the six model directories contains:

- `point_cloud/iteration_300/point_cloud.ply`
- `reflection_consistency_train.json`
- `reflection_consistency_test.json`

## Results

| Scene | Split | Base reflection error | RC reflection error | Delta RC-base | Base refl. PSNR | RC refl. PSNR | Delta RC-base |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| teapot | train | 0.0039792435 | 0.0038990002 | -0.0000802434 | 22.360122 | 22.462241 | 0.102119 |
| teapot | test | 0.0018519803 | 0.0018234213 | -0.0000285590 | 23.065242 | 23.150311 | 0.085069 |
| toaster | train | 0.0030265654 | 0.0030176094 | -0.0000089560 | 12.522532 | 12.521604 | -0.000927 |
| toaster | test | 0.0025858034 | 0.0025541257 | -0.0000316777 | 11.385143 | 11.384512 | -0.000631 |
| car | train | 0.0022225423 | 0.0021904636 | -0.0000320787 | 12.656790 | 12.633151 | -0.023639 |
| car | test | 0.0012438522 | 0.0012336909 | -0.0000101613 | 14.088415 | 14.071180 | -0.017236 |

## Claim Boundary

Supported:

- At corrected i300, seed 0, dynamic-pair evaluation, RC has lower measured reflection-consistency error than base on all three scenes and both train/test splits.

Mixed:

- Reflective-region PSNR is higher on teapot train/test and lower on toaster/car train/test.

Unsupported:

- Broad rendering-quality claims.
- Geometry, material, external-superiority, or causal claims.
- Multi-seed robustness claims.
- Full-horizon 31000 claims.
