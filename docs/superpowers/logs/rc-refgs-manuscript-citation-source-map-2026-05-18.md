# RC-RefGS Manuscript Citation and Source Map

Date: 2026-05-18 14:48:16 CST

Scope: source map for `docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md`. This is a citation/integration handoff only; it adds no experiments, code changes, or stronger claims.

## Claim Boundary

**CONDITIONAL GO** for citation-aware polishing of the conservative manuscript integration draft.

**NO-GO** for broad rendering, LPIPS, geometry, reconstruction, material, external-superiority, or causal claims.

**SWITCH MODEL** to gpt-5.5 remains recommended for final rhetoric and external citation replacement.

## Local Code Citation Map

| Draft claim | Local source | How to cite it in prose | Label |
| --- | --- | --- | --- |
| Ref-GS computes reflection directions, directional features, Gaussian feature interactions, and specular radiance before final composition. | `gaussian_renderer/__init__.py:125`, `gaussian_renderer/__init__.py:151`, `gaussian_renderer/__init__.py:163`, `gaussian_renderer/__init__.py:172` | Cite as local code evidence for the baseline renderer path. | Supported |
| Intermediate buffers are exposed without replacing the renderer. | `gaussian_renderer/__init__.py:182`, `gaussian_renderer/__init__.py:202` | Cite as local code evidence that `spec_light`, `diff_light`, `roughness_map`, `reflection_dir`, `feature_map`, and `select_index` are returned. | Supported |
| Training supervises final PBR RGB and applies normal consistency before optional RC loss. | `train.py:91`, `train.py:101`, `train.py:108` | Cite as local code evidence for the baseline training losses. | Supported |
| RC loss is disabled by default and gated by optimization parameters. | `arguments/__init__.py:113`, `train.py:113` | Cite as local code evidence that `lambda_ref_consistency=0.0` by default and the loss only runs when enabled and scheduled. | Supported |
| RC training renders a paired view and adds reflection-consistency loss. | `train.py:113`, `train.py:116`, `train.py:117`, `train.py:124` | Cite as local code evidence for the implemented training intervention. | Supported |
| Pair selection, reprojection, target sampling, confidence masks, and weighted residual are implemented in the helper. | `utils/reflection_consistency.py:32`, `utils/reflection_consistency.py:60`, `utils/reflection_consistency.py:91`, `utils/reflection_consistency.py:113`, `utils/reflection_consistency.py:148`, `utils/reflection_consistency.py:162` | Cite as local code evidence for the view-pair reflection-consistency computation. | Supported |
| The reflection evaluator reports mean consistency error, reflective-region PSNR, and pair count. | `metrics/reflection_consistency_eval.py:51`, `metrics/reflection_consistency_eval.py:81`, `metrics/reflection_consistency_eval.py:110`, `metrics/reflection_consistency_eval.py:122` | Cite as local code evidence for the diagnostic protocol and output fields. | Supported |
| Confidence-aware TSDF masking exists but is not evaluated as geometry evidence here. | `utils/mesh_utils.py:136`, `utils/mesh_utils.py:165` | Mention only as implementation context; do not cite it as evidence of geometry improvement. | Mixed |

## Evidence Artifact Map

| Draft result or qualifier | Evidence artifact | Manuscript use | Label |
| --- | --- | --- | --- |
| RC lowers measured reprojected reflection-consistency error on `teapot`, `toaster`, and `car`, train and test. | `docs/superpowers/logs/rc-refgs-claim-audit-2026-05-17.md` | Primary empirical support for the central diagnostic claim. | Supported |
| The allowed central wording is narrow and diagnostic-centered. | `docs/superpowers/logs/rc-refgs-claim-framing-packet-2026-05-18.md` | Use to police abstract, contributions, and results wording. | Supported |
| Stronger claims require explicit acceptance gates. | `docs/superpowers/logs/rc-refgs-acceptance-thresholds-2026-05-18.md` | Use to preserve upgrade checklist and claim-table wording. | Supported |
| Standard PSNR/SSIM trends are mixed and LPIPS is skipped. | `docs/superpowers/logs/rc-refgs-render-quality-summary-2026-05-17.md` | Report as context only; no aggregate rendering-quality claim. | Mixed |
| Full-split raw-convention normal diagnostics are directionally favorable but small. | `docs/superpowers/logs/rc-refgs-normal-quality-summary-2026-05-18.md` | Report as diagnostic-only context; no geometry claim. | Mixed |
| RefNeRF geometry metrics are not valid from current artifacts; SMVP3D needs loader/runtime prerequisites. | `docs/superpowers/logs/rc-refgs-geometry-feasibility-2026-05-18.md` | Use in limitations and forbidden-claim boundary. | Unsupported |
| Manuscript-facing claim table and forbidden boundary are already integrated. | `docs/superpowers/logs/rc-refgs-manuscript-integration-draft-2026-05-18.md` | Starting point for gpt-5.5 polishing. | Supported |

## External Citation Gaps

These are required before manuscript submission, but they are not filled in this codex window because no web/literature audit was requested and no new claims should be introduced.

| Placeholder | Needed citation type | Current action |
| --- | --- | --- |
| `[External citation: Ref-GS paper]` | Original Ref-GS method paper. | Required before replacing local `Ref-GS code` placeholder in abstract/method sections. |
| `[External citation: 2DGS / Gaussian surfel rendering background]` | Background citation if manuscript situates Ref-GS among Gaussian surface methods. | Optional for current diagnostic draft; required for full related-work prose. |
| `[External citation: reflective/glossy reconstruction baseline papers]` | External methods such as MaterialRefGS, SSR-GS, GS-2M, or related glossy reconstruction baselines. | Do not use for superiority claims unless evaluated or carefully framed as related work. |
| `[External citation: PSNR/SSIM/LPIPS metrics]` | Metric definitions if the manuscript includes a formal metrics section. | LPIPS must remain marked unavailable for current evidence. |
| `[External citation: Chamfer/F-score geometry metrics]` | Metric definitions if future geometry evaluation is added. | Not needed for current result section because geometry metrics are unavailable. |

## Manuscript Replacement Guidance

- Replace `[Citation: Ref-GS code]` with a combination of the external Ref-GS paper citation and local code references above.
- Replace `[Citation: this implementation]` with local code references and, if writing a paper draft, a self-reference such as "our implementation".
- Keep `[Supported]`, `[Mixed]`, and `[Unsupported]` labels until final editing; they are guardrails against claim drift.
- Keep the forbidden-claim boundary in reviewer notes or internal draft comments if it is removed from polished prose.
- Do not convert mixed PSNR/SSIM, normal diagnostics, or geometry feasibility into positive headline claims.

## Forbidden Claim Boundary

The following statements remain forbidden outside an explicit forbidden/limitations section:

- RC-RefGS improves overall novel-view synthesis quality.
- RC-RefGS improves LPIPS.
- RC-RefGS improves mesh quality, surface reconstruction, or geometry quality.
- RC-RefGS improves material decomposition.
- RC-RefGS outperforms external methods or paper baselines.
- RC-RefGS proves that `L_ref` causes all observed metric changes.
- RefNeRF `points3d.ply` is ground-truth geometry.

## Decision

**CONDITIONAL GO** for using this citation/source map as a handoff aid for manuscript polishing.

**NO-GO** for broader rendering, LPIPS, geometry, reconstruction, material, external-superiority, or causal claims.

**SWITCH MODEL** to gpt-5.5 is recommended for final literature-aware citation replacement and prose polishing.
