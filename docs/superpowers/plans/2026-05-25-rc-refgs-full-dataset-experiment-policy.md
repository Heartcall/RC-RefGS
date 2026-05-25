# RC-RefGS Full-Dataset Experiment Policy

Date: 2026-05-25  
Mode: protocol upgrade and experiment-scope hardening

## Required Datasets

All current and future RC-RefGS claim-bearing experiments must cover the complete scene manifests of:

1. Shiny Blender Synthetic
2. Shiny Blender Real
3. Glossy Synthetic

## Explicit Exclusion Rule

- NeRF Synthetic may be used for optional/background analysis only.
- NeRF Synthetic must not substitute for the three required glossy/reflective datasets above unless scope is explicitly expanded by the user in a later window.

## Complete-Dataset Rule

- Claim-bearing evidence must include all discovered scenes under the configured roots for all three required datasets.
- Do not silently route full-evidence runs to only `teapot/toaster/car`.
- Any partial-scene run must be explicitly labeled as non-claim-bearing.

## Prior Results Rule

- Existing `teapot/toaster/car` i20/i300/i31000 outputs remain valid as completed pilot/subset/first-slice evidence.
- They do not satisfy complete-dataset acceptance thresholds.
- They cannot independently support "complete experiment package" claims.

## Claim-Bearing vs Smoke/Debug

- Allowed as non-claim-bearing:
  - smoke runs, dry-runs, launcher parsing tests, single-scene debug probes, bounded runtime troubleshooting.
- Required for claim-bearing:
  - complete required-dataset manifest coverage;
  - matched experiment protocol across included scenes;
  - documented aggregate + scene-level summaries.

## Dataset Availability Gates

- Gate A: roots for all required datasets must be explicitly set in the required full-dataset manifest.
- Gate B: scene discovery must be complete and non-empty for each required dataset (or missing dataset must be explicitly blocked with user-visible status).
- Gate C: Glossy Synthetic conversion readiness must be validated if raw NeRO format is detected (`nero2blender.py` conversion step required before training).
- No claim-bearing training/evaluation launch is allowed until Gates A/B/C are satisfied or explicitly user-waived.

## Required Manifest Fields

Claim-bearing manifests must include:

- dataset key (`shiny_blender_synthetic`, `shiny_blender_real`, `glossy_synthetic`)
- dataset root
- full scene list
- dataset status (`discovered`, `needs_user_path`, `needs_conversion_or_discovery`, etc.)
- conversion note/checklist for Glossy Synthetic when applicable
- claim-bearing scope declaration that all discovered scenes are included

## Required Output Summaries

Claim-bearing runs must emit machine-readable and markdown summaries that include:

- per-scene and aggregate reflection-consistency deltas (base vs RC)
- per-scene and aggregate render metrics (PSNR/SSIM/LPIPS + reflective-region metrics)
- material diagnostics where supported
- normal diagnostics where supported
- explicit caveats for missing datasets/scenes/seeds

## Required No-GO Boundaries

- NO-GO for complete-dataset claims when any required dataset is missing from execution.
- NO-GO for causal claims without full-dataset matched ablations.
- NO-GO for robustness claims without multi-seed full-dataset repeats.
- NO-GO for manuscript claim upgrades unless complete-dataset acceptance thresholds are met.
