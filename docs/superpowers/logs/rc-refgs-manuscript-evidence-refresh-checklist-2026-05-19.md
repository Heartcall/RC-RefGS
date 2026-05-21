# RC-RefGS Manuscript Evidence Refresh Checklist

Date: 2026-05-19 18:55:39 CST

Purpose: line-level checklist for the next gpt-5.5 manuscript-polishing window. This artifact identifies stale evidence statements in `docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md` and maps each to current evidence. It adds no experiments, code changes, metrics, or stronger claims.

Authoritative current evidence:

- `docs/superpowers/logs/rc-refgs-manuscript-model-switch-manifest-2026-05-19.md`
- `docs/superpowers/logs/rc-refgs-render-quality-summary-2026-05-18-lpips.json`
- `docs/superpowers/logs/rc-refgs-reduced-ablation-summary-2026-05-19.md`
- `docs/superpowers/logs/rc-refgs-reduced-ablation-summary-2026-05-19.json`

## Required Global Updates

Apply these replacements only with the caveats shown here:

- Replace "LPIPS is unavailable", "LPIPS is missing", "LPIPS was skipped", and "No LPIPS result should be stated" with a mixed/context statement.
  - Current evidence: LPIPS runtime is enabled and verified for the three i300 scenes.
  - Exact caveat: full-image LPIPS is lower for RC on all six scene/split rows, but reflective-region LPIPS is mixed, lower on `toaster` train/test and `car` train, and higher on `teapot` train/test and `car` test.
  - Forbidden upgrade: do not state that RC-RefGS improves LPIPS as an aggregate method claim.
- Replace "ablations are missing", "No ablation table is available", and "no `w/o L_ref`, `w/o specular confidence`, or roughness-only ablation exists" with a preliminary reduced-ablation statement.
  - Current evidence: reduced i20 ablation matrix is complete: `30 / 30` cells and `missing_cells=[]`.
  - Exact caveat: the matrix is 20 iterations, one seed, three scenes, train/test, `num_pairs=5`; it is workflow/preliminary diagnostic evidence only.
  - Forbidden upgrade: do not state causal proof, confidence-weighting superiority, or manuscript-grade ablation support.

## Draft Locations To Refresh

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:23`

- Stale statement: "Standard PSNR/SSIM results are scene-dependent and LPIPS is unavailable" and stronger claims are gated on "LPIPS, ablations".
- Replacement intent: say PSNR/SSIM and LPIPS are scene/region dependent; LPIPS is available but mixed at reflective-region level; reduced ablations exist but are short-horizon and non-causal.
- Keep labels: `Mixed`, `Unsupported`, `Reasoning`.

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:31`

- Stale statement: rendering context is caveated because "LPIPS is missing".
- Replacement intent: rendering context remains caveated because PSNR/SSIM and reflective-region LPIPS are mixed, despite full-image LPIPS moving lower in the current i300 summary.

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:54`

- Stale statement: rendering metrics command uses `--skip_lpips`.
- Replacement intent: cite `docs/superpowers/logs/rc-refgs-render-quality-summary-2026-05-18-lpips.json` for LPIPS-enabled evidence and keep the old skip-LPIPS summary only as historical context.

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:64`

- Stale statement: "State that LPIPS, mesh/reference-geometry metrics, and ablations are missing."
- Replacement intent: state that LPIPS and reduced ablations are now available with strict caveats; mesh/reference-geometry metrics remain missing.

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:83`

- Stale statement: "LPIPS was skipped, so no LPIPS comparison is available."
- Replacement intent: add a compact LPIPS context sentence: full-image LPIPS is lower for RC on all six i300 rows, while reflective-region LPIPS is mixed three lower and three higher.

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:91`

- Stale statement: "No ablation table is available, so causal attribution beyond the matched RC-vs-baseline contrast is not established."
- Replacement intent: say a reduced i20 ablation table is complete, but it does not establish causal attribution because it is short-horizon/one-seed and `wo_conf` often lowers the reflection-consistency metric more than `rc`.

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:95`

- Stale statement: "LPIPS is missing" and "causal ablations have not been audited."
- Replacement intent: say LPIPS is measured but mixed/contextual, and reduced ablations are audited only as preliminary i20 diagnostics.

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:105`

- Stale table caveat: "LPIPS is unavailable."
- Replacement intent: change to "LPIPS is available, but only supports mixed/context reporting; no aggregate quality claim."

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:107`

- Stale table row: `LPIPS | Unsupported | No LPIPS result should be stated. | LPIPS was skipped.`
- Replacement intent: relabel LPIPS as `Mixed`, with safe wording: "LPIPS can be reported as current i300 context only." Required caveat: "full-image LPIPS is directionally favorable; reflective-region LPIPS is mixed; no aggregate LPIPS claim."

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:111`

- Stale table caveat: no ablations exist.
- Replacement intent: keep causal attribution `Unsupported`, but update caveat to: "Reduced i20 ablations exist, are complete 30/30, and remain insufficient for causal attribution; `wo_conf` often outperforms `rc` on the reflection-consistency diagnostic."

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:116`

- Stale upgrade checklist item: LPIPS still needs collection.
- Replacement intent: mark the LPIPS collection gate as satisfied for the current i300 diagnostic set, but keep a future gate for longer-horizon or repeated-seed LPIPS.

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:118`

- Stale upgrade checklist item: matched ablations still need collection.
- Replacement intent: split into two gates:
  - current reduced i20 ablation matrix is complete;
  - longer-horizon/repeated-seed ablations are still required before causal claims.

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:129`

- Forbidden claim remains valid: "RC-RefGS improves LPIPS."
- Replacement intent: keep forbidden boundary, or refine to "RC-RefGS improves LPIPS as an aggregate method claim."

`docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md:140`

- NO-GO statement remains valid, but should be updated from broad "LPIPS" to "aggregate LPIPS" to allow contextual reporting without claim expansion.

## Safe Replacement Language

Use language like:

> In the current i300 diagnostic summary, RC-RefGS lowers full-image LPIPS on all six scene/split rows, while reflective-region LPIPS remains mixed. These values are reported as context only and do not support a broad rendering-quality or aggregate LPIPS claim.

Use language like:

> The reduced i20 ablation matrix is complete across `teapot`, `toaster`, and `car` for `base`, `rc`, `wo_ref`, `wo_conf`, and `rough_only`, with `30 / 30` cells available and `missing_cells=[]`. It is preliminary short-horizon evidence only; because `wo_conf` often lowers the diagnostic more than `rc`, it does not establish confidence-weighting superiority or causal attribution.

## Required Verification For Manuscript Refresh

- `rg -n "LPIPS is unavailable|LPIPS is missing|LPIPS was skipped|No LPIPS result should be stated|No ablation table is available|no .*ablation exists" docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md`
  - Expected after refresh: no stale matches except historical notes explicitly labeled as old evidence.
- `rg -n "CONDITIONAL GO|NO-GO|SWITCH MODEL|Supported|Mixed|Unsupported|30 / 30|missing_cells=\\[\\]|aggregate LPIPS|causal attribution" <refreshed manuscript artifact>`
  - Expected: all boundary markers or equivalent explicit language remain present.
- Run a forbidden-claim confinement check for broad rendering, aggregate LPIPS, geometry, reconstruction, material, external-superiority, and causal-proof claims.
- Run `python -m unittest discover tests` if any repository file changes.
- Run `git diff --check` before completion.

## Decision

**CONDITIONAL GO** for gpt-5.5 manuscript polishing using this checklist together with `docs/superpowers/logs/rc-refgs-manuscript-model-switch-manifest-2026-05-19.md`.

**NO-GO** for broad rendering, aggregate LPIPS, geometry, reconstruction, material, external-superiority, confidence-weighting superiority, or causal claims.

**SWITCH MODEL** to gpt-5.5 remains recommended for the actual prose refresh.
