# RC-RefGS Next Modification Selection

Generated: 2026-06-05T00:51:41+08:00

## Selected Candidate

`rc_qp_angle10_sched` from **Family A: Angle-aware RC gating**. It is a launcher-level variant: `lambda_ref_consistency=0.01`, `ref_consistency_start=5000`, `ref_consistency_every=8`, `ref_consistency_max_angle=10.0`, `ref_consistency_gamma=2.0`, `lambda_dssim=0.2`. No `train.py` or metric script change is required.

## Why Not More Weight/Schedule Sweeps

Pure weight/schedule tuning is already tested and insufficient. On the two stress scenes, `rc_qp_lam010_start5000_every8` is the best schedule candidate but wins only `3/12` test quality metrics vs base and `1/2` test consistency scenes vs base. `rc_qp_lam005` is weaker at `0/12` test quality wins vs base.

## Rationale

The evidence suggests reduced RC pressure improves quality relative to current RC, but consistency degrades because some RC pairs likely compare view-dependent reflections that should not be forced to match. A strict 10-degree training-pair angle is the lowest-risk logic change: it keeps the best schedule and regularizes only more physically comparable reflection configurations.

## Expected Effects

- Consistency: should retain useful consistency on comparable pairs but may remain weaker than current RC because fewer pairs are used.
- Quality: should reduce view-dependent over-regularization and may improve PSNR/SSIM/LPIPS on helmet/luyu.
- Risk: if the angle gate is too strict, valid-pair coverage may be too low and consistency may weaken.

## Scope Boundary

Run exactly `helmet` and `luyu`, exactly one new variant, no Shiny Blender Real, no full 16-job pilot, no 14-scene validation, no metric changes, and no global quality-preserving claim.
