# Geometry-Aware RC-RefGS Design - 2026-06-05

## Motivation

The completed RC-RefGS experiments show that reflection consistency is useful as a mechanism metric, but it is not sufficient as the final success metric. RGB quality remains mixed, and no current artifact proves improved depth, normals, mesh quality, or usable surface reconstruction.

## Proposed Guarded Geometry RC Loss

```text
L_geo_rc =
  sum_u M_valid(u) * w(u) * [
    lambda_d * rho(D_t(u) - warp(D_s)(u))
    + lambda_n * (1 - dot(N_t(u), warp(N_s)(u))))
  ]
```

## Required Masks

- RC valid correspondence mask
- visibility / non-occlusion mask
- reflective mask
- depth-valid mask
- normal-valid mask

## Required Weights

- reflection-direction similarity
- confidence weight
- optional reconstruction residual guard
- optional pair-angle gate

## Safeguards

- late start
- low lambda
- Huber or Charbonnier robust penalty
- no geometry loss where depth/normal is invalid
- no normal loss unless coordinate system is verified
- no mesh claim without GT geometry or accepted reference protocol

## First Candidate For Later Implementation

`rc_geo_guard_stage1`

Conservative defaults:

| parameter | value |
| --- | ---: |
| `lambda_ref_consistency` | 0.01 |
| `ref_consistency_start` | 5000 |
| `ref_consistency_every` | 8 |
| `lambda_geo_rc_depth` | 0.01 |
| `lambda_geo_rc_normal` | 0.005 |
| `geo_rc_start` | 7000 |
| `geo_rc_every` | 8 |

## Future Evaluation

Run only `helmet,luyu` first with `max_jobs=2`, compare against base/current rc/previous qp variants, and keep the claim boundary local. No global claim from two scenes.

## Current Status

Design only. The loss is not implemented in this task.
