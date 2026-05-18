# RC-RefGS Manuscript Model-Switch Manifest

Date: 2026-05-18 14:59:41 CST

Purpose: handoff manifest for the next gpt-5.5 manuscript-polishing window. This document indexes the conservative RC-RefGS manuscript artifacts and restates the claim boundary. It adds no experiments, code changes, metrics, or stronger claims.

## Read Order

1. `docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md`
   - Use as the manuscript-facing scaffold.
   - Preserve the `Supported` / `Mixed` / `Unsupported` claim table until final editing.
2. `docs/superpowers/logs/rc-refgs-manuscript-citation-source-map-2026-05-18.md`
   - Use to replace local code placeholders and identify unresolved external citation gaps.
   - Do not invent external citations without a dedicated literature audit.
3. `docs/superpowers/logs/rc-refgs-claim-framing-packet-2026-05-18.md`
   - Use as the authoritative claim-boundary packet.
4. `docs/superpowers/logs/rc-refgs-acceptance-thresholds-2026-05-18.md`
   - Use as the acceptance gate for any attempted claim upgrade.
5. `docs/superpowers/logs/rc-refgs-claim-audit-2026-05-17.md`
   - Use for the underlying i300 reflection, PSNR/SSIM, normal, and geometry-feasibility audit trail.

## Current Manuscript Center

**Supported**: RC-RefGS lowers measured reprojected reflection-consistency error relative to matched Ref-GS baselines on `teapot`, `toaster`, and `car`, train and held-out test, under the short i300 sanity protocol.

Required protocol qualifiers:

- 300 iterations.
- One seed.
- Three scenes.
- Train and held-out test splits.
- `max_pairs=10`.
- `max_angle_deg=180`.
- Pair-sampling-dependent reflection diagnostic.

## Required Caveats

**Mixed**:

- Standard PSNR/SSIM is scene-dependent.
- `teapot` improves.
- `toaster` is mixed with small PSNR decreases and SSIM increases.
- `car` slightly decreases in PSNR/SSIM.
- Full-split normal diagnostics are directionally favorable but small.

**Unsupported**:

- LPIPS is unavailable/skipped.
- No extracted mesh/reference-geometry metric is available.
- RefNeRF `points3d.ply` is not ground-truth geometry.
- No material diagnostic, relighting, external baseline, or ablation table is available.
- No causal attribution to `L_ref` beyond the matched RC-vs-baseline observation.

## Forbidden Claim Boundary

The next manuscript-polishing window must not claim:

- improved overall novel-view synthesis quality,
- improved LPIPS,
- improved mesh quality,
- improved surface reconstruction,
- improved geometry quality,
- improved material decomposition,
- superiority over external methods or paper baselines,
- causal proof that `L_ref` caused all observed metric changes,
- RefNeRF `points3d.ply` as ground-truth geometry.

## Allowed Polishing Tasks

- Improve clarity, flow, and concision of the manuscript integration draft.
- Replace local code placeholders with properly scoped local-code references or audited external citations.
- Move the forbidden-claim boundary into internal comments or limitations prose, provided the boundary remains represented.
- Keep all claim labels until the final prose has an equivalent explicit qualifier.
- Add citation placeholders only when they are clearly marked as unresolved.

## Disallowed Polishing Tasks

- Do not remove LPIPS, geometry, ablation, or mixed-rendering caveats.
- Do not turn diagnostic normal results into geometry evidence.
- Do not convert PSNR/SSIM context into an aggregate quality claim.
- Do not cite external baselines as comparisons unless comparable results are available.
- Do not add new experiments, code, or training changes in the writing window.

## Verification Checklist For Next Window

- Check `CONDITIONAL GO`, `NO-GO`, `SWITCH MODEL`, `Supported`, `Mixed`, and `Unsupported` remain present or are replaced by explicit equivalent language.
- Run a forbidden-claim confinement check after polishing.
- Run `python -m unittest discover tests` if any repository file changes.
- Run `git diff --check` before completion.
- Update `docs/superpowers/logs/rc-refgs-autonomous-log.md` and `docs/superpowers/logs/rc-refgs-coordination-board.md`.

## Decision

**CONDITIONAL GO** for switching to gpt-5.5 manuscript polishing using this manifest, the integration draft, and the citation/source map.

**NO-GO** for broad rendering, LPIPS, geometry, reconstruction, material, external-superiority, or causal claims.

**SWITCH MODEL** to gpt-5.5 is recommended for final literature-aware prose polishing.
