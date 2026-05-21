# RC-RefGS Manuscript Model-Switch Manifest

Date: 2026-05-19 18:10:22 CST

Purpose: handoff manifest for the next gpt-5.5 manuscript-polishing window after completion of the reduced-ablation evidence matrix. This document updates the 2026-05-18 manifest with current evidence pointers and claim boundaries. It adds no experiments, code changes, metrics, or stronger claims.

## Read Order

1. `docs/superpowers/logs/rc-refgs-reduced-ablation-summary-2026-05-19.md`
   - Use as the current reduced-ablation index.
   - Confirm the paired JSON reports `missing_cells=[]` and the Markdown reports `Available cells: 30 / 30`.
2. `docs/superpowers/logs/rc-refgs-reduced-ablation-summary-2026-05-19.json`
   - Use for exact values, source metric paths, and reproducibility checks.
3. `docs/superpowers/logs/rc-refgs-render-quality-summary-2026-05-18-lpips.json`
   - Use as the LPIPS-enabled render-quality evidence source.
   - Treat LPIPS and PSNR/SSIM as mixed/context metrics, not as a broad rendering-quality win.
4. `docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md`
   - Use as the manuscript-facing scaffold, but update stale statements that say LPIPS or ablations are unavailable.
   - Preserve the `Supported` / `Mixed` / `Unsupported` claim table until final editing.
5. `docs/superpowers/logs/rc-refgs-manuscript-citation-source-map-2026-05-18.md`
   - Use to replace local code placeholders and identify unresolved external citation gaps.
   - Do not invent external citations without a dedicated literature audit.
6. `docs/superpowers/logs/rc-refgs-claim-framing-packet-2026-05-18.md`
   - Use as the conservative baseline claim-boundary packet, with the evidence updates in this manifest.
7. `docs/superpowers/logs/rc-refgs-acceptance-thresholds-2026-05-18.md`
   - Use as the acceptance gate for any attempted claim upgrade.
8. `docs/superpowers/logs/rc-refgs-claim-audit-2026-05-17.md`
   - Use for the original i300 reflection, PSNR/SSIM, normal, and geometry-feasibility audit trail.

## Current Evidence Center

**Supported**:

- Under the short i300 sanity protocol, RC-RefGS lowers measured reprojected reflection-consistency error relative to matched Ref-GS baselines on `teapot`, `toaster`, and `car`, train and held-out test.
- The reduced-ablation matrix is complete: 3 scenes x 5 variants x 2 splits = 30 / 30 available cells, with `missing_cells=[]`.
- The reduced-ablation summary is reproducible from metric JSONs and includes `base`, `rc`, `wo_ref`, `wo_conf`, and `rough_only` variants for `teapot`, `toaster`, and `car`.

Required protocol qualifiers:

- i300 evidence: 300 iterations, one seed, three scenes, train/test splits, `max_pairs=10`, `max_angle_deg=180`, pair-sampling-dependent reflection diagnostic.
- reduced-ablation evidence: 20 iterations, one seed, three scenes, train/test splits, five variants, `num_pairs=5`.
- Both evidence tracks are diagnostic and short-horizon.

## Required Caveats

**Mixed**:

- Standard PSNR/SSIM remains scene-dependent.
- LPIPS runtime is enabled and verified for the three i300 scenes, but the trends must stay caveated: full-image LPIPS is directionally favorable in the current summary, while reflective LPIPS is not uniformly favorable across all rows.
- Full-split normal diagnostics are directionally favorable but small and remain diagnostic-only.
- The reduced-ablation table does not isolate a clean causal story: `wo_conf` often lowers the reflection-consistency metric more than `rc`.

**Unsupported**:

- No extracted mesh/reference-geometry metric is available.
- RefNeRF `points3d.ply` is not ground-truth geometry.
- No material diagnostic, relighting study, external baseline comparison, longer-horizon ablation, or seed repeat is available.
- The reduced i20 matrix does not prove that `L_ref`, confidence weighting, or roughness smoothing caused all observed metric changes.
- `rough_only` is a control, not evidence that roughness regularization alone reproduces the RC behavior.

## Reduced-Ablation Interpretation

Allowed interpretation:

- The reduced-ablation workflow is complete and reproducible.
- At i20, `rc` is lower than `base` on the measured reflection-consistency metric for all three scenes and both splits.
- `wo_ref` is close to `base`, which is consistent with the reflection-consistency term being relevant to this diagnostic.
- `rough_only` is close to or slightly worse than `base`, so it should be described only as a control.

Required caution:

- `wo_conf` is often lower than `rc`; do not claim that the confidence weighting is necessary, sufficient, or superior from this matrix.
- The matrix is short-horizon and one-seed; do not use it as a causal proof or as manuscript-grade ablation evidence without longer runs and repeats.

## Forbidden Claim Boundary

The next manuscript-polishing window must not claim:

- improved overall novel-view synthesis quality,
- improved LPIPS as an aggregate method claim,
- improved mesh quality,
- improved surface reconstruction,
- improved geometry quality,
- improved material decomposition,
- superiority over external methods or paper baselines,
- causal proof that `L_ref` caused all observed metric changes,
- causal proof that confidence weighting is necessary or superior,
- causal proof that roughness smoothing explains the reflection metric movement,
- RefNeRF `points3d.ply` as ground-truth geometry.

## Allowed Polishing Tasks

- Improve clarity, flow, and concision of the manuscript integration draft.
- Update stale LPIPS and ablation-unavailable statements using the 2026-05-18 LPIPS summary and 2026-05-19 reduced-ablation summary.
- Integrate the reduced-ablation table as a preliminary short-horizon diagnostic, with all qualifiers intact.
- Update the `Supported` / `Mixed` / `Unsupported` claim table while preserving equivalent labels or explicit language.
- Replace local code placeholders with properly scoped local-code references or audited external citations.
- Add citation placeholders only when they are clearly marked as unresolved.

## Disallowed Polishing Tasks

- Do not remove short-run, one-seed, geometry, material, external-baseline, or causality caveats.
- Do not turn LPIPS runtime availability into a broad LPIPS or rendering-quality claim.
- Do not turn diagnostic normal results into geometry evidence.
- Do not convert the reduced i20 ablations into causal attribution.
- Do not cite external baselines as comparisons unless comparable results are available.
- Do not add new experiments, code, or training changes in the writing window.

## Verification Checklist For Next Window

- Check `CONDITIONAL GO`, `NO-GO`, `SWITCH MODEL`, `Supported`, `Mixed`, `Unsupported`, `reduced-ablation`, `30 / 30`, and `missing_cells=[]` remain present or are replaced by explicit equivalent language.
- Run a forbidden-claim confinement check after polishing.
- Confirm any use of LPIPS points to `docs/superpowers/logs/rc-refgs-render-quality-summary-2026-05-18-lpips.json` and remains caveated.
- Run `python -m unittest discover tests` if any repository file changes.
- Run `git diff --check` before completion.
- Update `docs/superpowers/logs/rc-refgs-autonomous-log.md` and `docs/superpowers/logs/rc-refgs-coordination-board.md`.

## Decision

**CONDITIONAL GO** for switching to gpt-5.5 manuscript polishing using this manifest, the integration draft, the citation/source map, the LPIPS-enabled render-quality summary, and the complete reduced-ablation summary.

**NO-GO** for broad rendering, aggregate LPIPS, geometry, reconstruction, material, external-superiority, or causal claims.

**SWITCH MODEL** to gpt-5.5 is recommended for final literature-aware prose polishing under these boundaries.
