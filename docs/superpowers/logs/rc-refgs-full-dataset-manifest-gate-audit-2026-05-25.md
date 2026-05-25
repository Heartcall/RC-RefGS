# RC-RefGS Full-Dataset Manifest Gate Audit

Date: 2026-05-25 16:25:21 CST

Scope: FD-P0 docs/status-only audit. No training, metric computation, ablation, multi-seed run, geometry metric, manuscript prose edit, or claim upgrade was started.

## Result

- Shiny Blender Synthetic: discovered and already locked at `/data/liuly/dataset/3DGS/refnerf`.
  - Scenes: `ball`, `car`, `coffee`, `helmet`, `teapot`, `toaster`.
- Shiny Blender Real: discovered and now locked at `/data/liuly/dataset/3DGS/glossy/GlossyReal`.
  - Scenes: `bear`, `bunny`, `coral`, `maneki`, `vase`.
- Glossy Synthetic: still blocked.
  - No converted Glossy Synthetic root was found under `/data/liuly/dataset`.
  - NeRO synthetic config hints exist under `/home/liuly/Surface_Reconstruction/Glossy/NeRO/configs/material/syn`.
  - Available conversion scripts include `nero2blender.py` in sibling repos, but conversion readiness is not validated in this window.

## Gate Status

- Gate A, roots explicit: blocked by Glossy Synthetic.
- Gate B, scene discovery complete and non-empty: blocked by Glossy Synthetic.
- Gate C, Glossy Synthetic conversion readiness: blocked.
- Claim-bearing launch allowed: no.

## Decision

CONDITIONAL GO for continued manifest/status reconciliation.

NO-GO for claim-bearing full-dataset training, complete-dataset claims, manuscript/scientific claim upgrades, broad rendering/material/geometry/external-superiority/causal/full-ablation/multi-seed claims, or SWITCH MODEL routing for claim-bearing P5 audit.
