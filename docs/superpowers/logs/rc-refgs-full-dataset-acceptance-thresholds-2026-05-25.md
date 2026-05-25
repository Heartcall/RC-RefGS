# RC-RefGS Full-Dataset Acceptance Thresholds

Date: 2026-05-25

Scope baseline:
- Required datasets for claim-bearing conclusions:
  - Shiny Blender Synthetic
  - Shiny Blender Real
  - Glossy Synthetic
- Claim-bearing scope means complete scene coverage for all discovered scenes in all required datasets.
- `teapot/toaster/car` subset evidence is valid pilot evidence only and cannot satisfy complete-dataset thresholds.

## Reflection-Consistency Claim

Supported only if:
- RC improves over base across the full required dataset manifest, and
- both scene-level and aggregate reporting are provided for train/test splits, and
- missing-scene count is zero for required datasets (or explicitly user-waived).

## Rendering Claim

Supported only if:
- PSNR/SSIM/LPIPS (including reflective-region reporting where configured) improve, or are explicitly and defensibly explained, across the full required dataset manifest.

## Material Claim

Supported only if:
- material diagnostics improve across the full required dataset manifest, with scene-level and aggregate summaries.

## Causal Claim

Supported only after:
- full-dataset ablations are complete (`base`, `rc`, `wo_ref`, `wo_conf`, `rough_only`) and
- causal direction remains consistent under full-dataset coverage.

## Robustness Claim

Supported only after:
- multi-seed full-dataset repeats are complete (minimum 3 seeds), or
- explicit one-seed caveat is preserved and no robustness claim is made.

## Complete Experiment Package

Requires:
- all three required datasets (Shiny Blender Synthetic + Shiny Blender Real + Glossy Synthetic) with complete scene coverage;
- matched base/RC full-horizon runs;
- full-dataset render/material/normal summaries where supported;
- full-dataset matched ablations;
- multi-seed support for claim-bearing conclusions.

## No-GO Rules

- NO-GO for complete-dataset claims when any required dataset is missing.
- NO-GO for broad rendering/material/causal/external-superiority claims from subset-only evidence.
- NO-GO for manuscript claim upgrades until full-dataset thresholds are met.
