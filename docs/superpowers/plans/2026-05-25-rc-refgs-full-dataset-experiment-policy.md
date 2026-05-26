# RC-RefGS Full-Dataset Experiment Policy

Date: 2026-05-25
Mode: protocol-upgrade and experiment-scope hardening

## Required Datasets

All claim-bearing RC-RefGS experiments must cover complete scene manifests for:

1. Shiny Blender Synthetic
2. Shiny Blender Real
3. Glossy Synthetic

Current user-confirmed required scene sets:
- Shiny Blender Synthetic: `ball`, `car`, `coffee`, `helmet`, `teapot`, `toaster` (6)
- Shiny Blender Real: `gardenspheres`, `sedan`, `toycar` (3)
- Glossy Synthetic: `angel`, `bell`, `cat`, `horse`, `luyu`, `potion`, `tbell`, `teapot` (8)
- Total claim-bearing scene count: `17` (`6+3+8`)

## Complete-Dataset Rule

- Claim-bearing evidence must include all discovered scenes under each configured required-dataset root.
- Partial-scene runs are smoke/debug/pilot evidence only unless explicitly re-scoped by the user.

## Claim-Bearing vs Smoke/Debug

- Claim-bearing:
  - complete required-dataset manifest coverage;
  - matched protocol across included scenes;
  - scene-level and aggregate summaries.
- Smoke/debug/non-claim-bearing:
  - dry-runs, parser checks, bounded runtime probes, subset troubleshooting, single-scene tests.

## Prior Subset Evidence Rule

- Prior `teapot/toaster/car` results (including i20, i300, i31000) are subset/pilot/first-slice evidence only.
- They are valid operational evidence but not complete-dataset evidence.
- They cannot satisfy complete experiment package criteria by themselves.

## NeRF Synthetic Rule

- NeRF Synthetic is optional/background only.
- NeRF Synthetic cannot substitute for Shiny Blender Synthetic, Shiny Blender Real, and Glossy Synthetic in claim-bearing RC-RefGS conclusions.

## Additional GlossyReal Rule

- `/data/liuly/dataset/3DGS/glossy/GlossyReal` (`bear/bunny/coral/maneki/vase`) is optional additional glossy-real data.
- It must not substitute for required Shiny Blender Real claim-bearing scope unless the user explicitly expands required scope.

## Glossy Synthetic Conversion Rule

- If raw Glossy Synthetic (NeRO-style) format is detected, run `nero2blender.py` before RC-RefGS training/evaluation.
- Claim-bearing launch remains blocked until converted Blender-style scene outputs are validated.

## No-GO Boundaries

- NO-GO for complete-dataset claims when any required dataset root/scene coverage is incomplete or ambiguous.
- NO-GO for complete-dataset claims based only on `teapot/toaster/car`.
- NO-GO for causal claims without full-dataset matched ablations.
- NO-GO for robustness claims without multi-seed full-dataset repeats.
