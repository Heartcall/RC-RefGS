# RC-RefGS Claim-Framing Packet

Date: 2026-05-18 04:19:25 CST

Scope: conservative paper-claim handoff using current i300 evidence only.

## Current Evidence

| Evidence area | Status | What it supports | Caveat |
| --- | --- | --- | --- |
| Reflection consistency | Supported | RC lowers measured reprojected reflection-consistency error on `teapot`, `toaster`, and `car`, train and test | Pair-sampling dependent, `max_pairs=10`, `max_angle_deg=180` |
| Standard PSNR/SSIM | Mixed | `teapot` improves; `toaster`/`car` are mixed or slightly lower | LPIPS skipped; no overall rendering-quality claim |
| Normal diagnostics | Directionally favorable diagnostic | Full-split raw-convention normal MAE/cosine improve on all six scene/split rows | Small deltas; not mesh/reference-geometry evidence |
| Geometry | Unsupported / No-go | SMVP3D has usable OBJ references in principle | Current RefNeRF artifacts have no extracted meshes; RefNeRF `points3d.ply` is random initialization data; SMVP3D needs loader/runtime prerequisites |

## Allowed Wording

- RC-RefGS adds a gated cross-view reflection-consistency objective to Ref-GS while preserving the base representation and renderer.
- In short i300 sanity runs on `teapot`, `toaster`, and `car`, RC-RefGS consistently lowers the measured reprojected reflection-consistency error relative to matched Ref-GS baselines on both train and held-out test splits.
- This supports the intended optimization target: reducing a view-pair reflection-consistency diagnostic.
- Full-split normal-map diagnostics are directionally favorable but small, and should be reported as diagnostics rather than geometry evidence.

## Required Qualifiers

- Rendering quality remains mixed: PSNR/SSIM gains are scene-dependent, and LPIPS is unavailable.
- Evidence is short-run only: 300 iterations, one seed, three scenes, and sampled reflection pairs.
- Normal diagnostic effect sizes are small, especially outside `teapot`.
- Geometry claims require extracted meshes and reference-geometry metrics; current evidence does not provide them.

## Forbidden Claims

- Do not claim improved overall novel-view synthesis quality.
- Do not claim improved mesh quality, surface reconstruction, or geometry quality.
- Do not claim material decomposition improvement.
- Do not claim superiority over external methods or paper baselines.
- Do not claim LPIPS improvement.
- Do not use RefNeRF `points3d.ply` as ground-truth geometry.

## Acceptance Gates

Reflection-consistency claim:

- Report scene, split, `max_pairs`, `max_angle_deg`, and pair count.
- Keep the claim scoped to measured reflection-consistency error under the i300 sanity protocol.

Rendering claim:

- Run LPIPS with cached or explicitly approved weights.
- Require non-negative or explicitly explained PSNR/SSIM/LPIPS trends across scenes before any overall rendering claim.
- Repeat at longer training horizons and preferably more than one seed.

Geometry claim:

- Fix mesh extraction/runtime prerequisites.
- Do not evaluate RefNeRF random `points3d.ply` as ground truth.
- Add SMVP3D loader support or deterministic `cameras.npz` to Ref-GS transform conversion.
- Run Chamfer/F-score or equivalent mesh/reference metrics against OBJ references.

Causality claim:

- Run `w/o L_ref`, `w/o specular confidence`, and roughness-only regularization ablations.
- Avoid attributing all observed changes to RC before ablations are available.

## Decision

**CONDITIONAL GO** for conservative RC-RefGS claim framing centered on the reflection-consistency diagnostic.

**NO-GO** for broad rendering-quality, geometry-quality, surface-reconstruction, material-decomposition, LPIPS, or external-superiority claims.

**SWITCH MODEL** to gpt-5.5 is recommended for paper language and acceptance-threshold drafting.
