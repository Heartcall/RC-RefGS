# RC-RefGS Quality-Preserving Stage 1 Follow-Up Analysis

Generated: 2026-06-05T00:20:38+08:00

## Executive Summary

Decision: **GO** for analysis/reporting. Stage 1 is now **4/4 completed** under `/tmp/rc_refgs_quality_preserving_rc_followup_helmet_luyu_i31000_20260604`. This task did not launch training or metrics; it only analyzed completed artifacts.

Neither Stage 1 variant is strong enough to expand directly to 4-scene confirmation. `rc_qp_lam010_start5000_every8` is the better of the two new variants because it improves over `rc_qp_lam010` on all 12 test quality cells for `helmet` and `luyu`, but it still beats base on only 3/12 test quality cells and only 1/2 test consistency scenes. `rc_qp_lam005` is weaker and beats base on 0/12 test quality cells.

Next candidate: a logic-level angle-aware or confidence-gated RC variant, not another pure weight/schedule-only expansion. No global quality-preserving claim is supported.

## Completion Status

| Dataset | Scene | Variant | Artifacts | Launcher status | Source path |
|---|---|---|---:|---|---|
| shiny_blender_synthetic | helmet | rc_qp_lam005 | 5/5 | completed | `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/helmet` |
| shiny_blender_synthetic | helmet | rc_qp_lam010_start5000_every8 | 5/5 | completed | `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/helmet` |
| glossy_synthetic | luyu | rc_qp_lam005 | 5/5 | completed | `/data/liuly/dataset/3DGS/GlossySyntheticConverted/luyu_blender` |
| glossy_synthetic | luyu | rc_qp_lam010_start5000_every8 | 5/5 | completed | `/data/liuly/dataset/3DGS/GlossySyntheticConverted/luyu_blender` |

Manual CUDA preflight in `pilot_status.json`: `decision=pass`, `torch_cuda_available=true`, `torch_device_count=1`, device `NVIDIA RTX A5000`.

## Aggregate Win Counts

Lower is better for reflection consistency and LPIPS; higher is better for PSNR/SSIM.

| Variant | Split | Reference | Consistency | Full quality | Reflective quality | All quality |
|---|---|---|---:|---:|---:|---:|
| rc_qp_lam005 | train | base | 1/2 | 1/6 | 1/6 | 2/12 |
| rc_qp_lam005 | train | rc | 0/2 | 4/6 | 6/6 | 10/12 |
| rc_qp_lam005 | train | rc_qp_lam010 | 0/2 | 3/6 | 1/6 | 4/12 |
| rc_qp_lam005 | test | base | 1/2 | 0/6 | 0/6 | 0/12 |
| rc_qp_lam005 | test | rc | 0/2 | 2/6 | 3/6 | 5/12 |
| rc_qp_lam005 | test | rc_qp_lam010 | 0/2 | 3/6 | 1/6 | 4/12 |
| rc_qp_lam010_start5000_every8 | train | base | 1/2 | 0/6 | 3/6 | 3/12 |
| rc_qp_lam010_start5000_every8 | train | rc | 0/2 | 3/6 | 3/6 | 6/12 |
| rc_qp_lam010_start5000_every8 | train | rc_qp_lam010 | 0/2 | 3/6 | 3/6 | 6/12 |
| rc_qp_lam010_start5000_every8 | test | base | 1/2 | 1/6 | 2/6 | 3/12 |
| rc_qp_lam010_start5000_every8 | test | rc | 0/2 | 3/6 | 4/6 | 7/12 |
| rc_qp_lam010_start5000_every8 | test | rc_qp_lam010 | 0/2 | 6/6 | 6/6 | 12/12 |
| rc_qp_lam010 | train | base | 2/2 | 1/6 | 1/6 | 2/12 |
| rc_qp_lam010 | train | rc | 0/2 | 4/6 | 5/6 | 9/12 |
| rc_qp_lam010 | test | base | 2/2 | 0/6 | 0/6 | 0/12 |
| rc_qp_lam010 | test | rc | 0/2 | 2/6 | 3/6 | 5/12 |

## Pareto Summary

| Variant | Test consistency vs base | Test consistency vs rc | Test quality vs base | Test quality vs rc | Test quality vs rc_qp_lam010 |
|---|---:|---:|---:|---:|---:|
| rc_qp_lam005 | 1/2 | 0/2 | 0/12 | 5/12 | 4/12 |
| rc_qp_lam010_start5000_every8 | 1/2 | 0/2 | 3/12 | 7/12 | 12/12 |
| rc_qp_lam010 | 2/2 | 0/2 | 0/12 | 5/12 |  |

Interpretation: `rc_qp_lam010_start5000_every8` is a useful diagnostic because it improves quality relative to `rc_qp_lam010`, but it does not preserve enough base quality or consistency to justify expansion. `rc_qp_lam005` does not solve the quality problem on the two stress scenes.

## Per-Scene Test Readout

| Scene | Variant | Consistency vs base | Consistency vs rc | Quality vs base | Quality vs rc | Quality vs rc_qp_lam010 |
|---|---|---:|---:|---:|---:|---:|
| shiny_blender_synthetic/helmet | rc_qp_lam005 | True | False | 0/6 | 0/6 | 2/6 |
| shiny_blender_synthetic/helmet | rc_qp_lam010_start5000_every8 | True | False | 2/6 | 2/6 | 6/6 |
| glossy_synthetic/luyu | rc_qp_lam005 | False | False | 0/6 | 5/6 | 2/6 |
| glossy_synthetic/luyu | rc_qp_lam010_start5000_every8 | False | False | 1/6 | 5/6 | 6/6 |

## Next Candidate Recommendation

Do **not** expand either Stage 1 variant to 4-scene confirmation yet. The best Stage 1 variant is `rc_qp_lam010_start5000_every8`, but it remains below the base-quality target on the two stress scenes.

Recommended next RC-RefGS candidate: implement a logic-level angle-aware or confidence-gated RC variant, for example `rc_qp_angle10` or an angle-gated stage-1 variant. Rationale: pure weight/schedule changes improved some quality tradeoffs but consistently weakened reflection consistency relative to current `rc`; the loss needs to avoid forcing view-dependent reflection configurations that are not geometrically comparable.

## Claim Boundary

This is a 2-scene Stage 1 analysis only. It does not support a global RC-RefGS-over-Ref-GS claim, a Shiny Real claim, a full FD-P2 claim upgrade, or a full 16-job/14-scene expansion. The original FD-P2-lite result remains unchanged.
