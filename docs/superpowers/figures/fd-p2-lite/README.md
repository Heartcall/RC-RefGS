# FD-P2-lite Publication Tables and Figures

## Scope

This package reports FD-P2-lite / non-Shiny-Real evidence only. It uses the 14 scoped scenes from Shiny Blender Synthetic and Glossy Synthetic. Shiny Blender Real is excluded due to OOM. Original full FD-P2 and full 51-cell ablation claims remain NO-GO.

Scoped complete-metric coverage is `70/70`: main base/RC comparison `28/28`, and non-Shiny-Real ablation comparison `42/42`.

## Input Files

- `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-results-analysis-2026-06-01.json`
- `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-main-summary-2026-06-01.csv`
- `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-ablation-summary-2026-06-01.csv`
- `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-tradeoff-summary-2026-06-01.csv`

The generator reads only these frozen final-analysis artifacts. It does not run training, metrics, recovery, or GPU work.

## Generated Tables

- `table1_main_base_vs_rc_summary.{csv,md,tex}`: 14 paired-scene rows with RC-minus-base deltas and consistency win flags.
- `table2_rc_win_counts_by_metric.{csv,md,tex}`: 16 metric-split rows with directions, RC win rates, mean deltas, and cautious interpretations.
- `table3_ablation_aggregate.{csv,md,tex}`: 6 dataset-variant aggregate rows for `wo_ref`, `wo_conf`, and `rough_only`.
- `table4_tradeoff_summary.{csv,md,tex}`: 28 scene-split rows. This is the documented scene-by-split convention for tradeoff reporting.

Numeric deltas use `RC - base`. For consistency and LPIPS, lower is better. For PSNR and SSIM, higher is better.

## Generated Figures

- `fig1_rc_consistency_delta_by_scene.{pdf,svg,png}`: scene-level train/test consistency deltas; negative is better.
- `fig2_rc_win_rates_by_metric.{pdf,svg,png}`: train/test RC win rates with metric-direction note.
- `fig3_consistency_quality_tradeoff_map.{pdf,svg,png}`: test consistency-error delta versus test full-LPIPS delta.
- `fig4_ablation_aggregate_comparison.{pdf,svg,png}`: dataset-separated ablation aggregates for consistency, full LPIPS, and reflective LPIPS.
- `fig5_scope_coverage_summary.{pdf,svg,png}`: scoped coverage panel with the Shiny Blender Real OOM exclusion stated explicitly.

Use PDF or SVG for publication layout and PNG for quick review.

## Regenerate

```bash
python docs/superpowers/figures/fd-p2-lite/make_fd_p2_lite_publication_tables_figures.py
```

## Claim Boundary

- FD-P2-lite / non-Shiny-Real only.
- Shiny Blender Real excluded due to OOM.
- Original full FD-P2 and full 51-cell ablation claims remain NO-GO.
