# Experiment Data Audit

## Source priority

- Primary numerical sources: `docs/superpowers/figures/fd-p2-lite/table1_main_base_vs_rc_summary.csv`, `docs/superpowers/figures/fd-p2-lite/table2_rc_win_counts_by_metric.csv`, `docs/superpowers/figures/fd-p2-lite/table3_ablation_aggregate.csv`, and `docs/superpowers/figures/fd-p2-lite/table4_tradeoff_summary.csv`.
- The final FD-P2-lite analysis is treated as the authoritative scope definition for paper assets: FD-P2-lite / non-Shiny-Real / completed runs only.
- Older full-dataset and recovery notes are used only to document coverage limits, especially incomplete/OOM Shiny Blender Real cells.

## Data transformations

- Main paired-scene rows are converted from RC-minus-base deltas into direction-aware improvements.
- Reflection consistency and LPIPS are treated as lower-is-better; PSNR and SSIM are treated as higher-is-better.
- Table 1 reports compact deltas and win counts because the available source table does not contain raw base and RC absolute per-scene values.
- Ablation heatmaps use only available variants (`wo_ref`, `wo_conf`, `rough_only`); missing base/RC aggregate values are not inferred.
- No original result CSV, log or metric file is overwritten.

## Missing or excluded evidence

- Shiny Blender Real incomplete/OOM cells are excluded from paper claims.
- Full FD-P2 and full 51-cell ablation conclusions remain unsupported by this result package.
- No independent mesh or geometry-quality metric table is available here; mesh-quality claims are therefore unsupported.
- No qualitative montage is generated because a verified image set was not provided.

## Cleaning log

- main: source CSV lacks test_rc_delta_reflective_region_psnr; this metric is not expanded into cleaned_main_results.csv.
- main: source CSV lacks train_rc_delta_reflective_region_psnr; this metric is not expanded into cleaned_main_results.csv.
- win-counts: reflective_region_psnr aggregate rows are retained from the win-count source table.
- tradeoff: reflective_region_psnr evidence is retained in trade-off notes from the source table.


<!-- FULL_METRIC_TABLES:START -->
## Full Metric Tables By Dataset

- Main absolute metrics source: `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-main-summary-2026-06-01.csv`.
- Main valid-pair count source: `docs/superpowers/logs/rc-refgs-fd-p2-lite-main-table-2026-05-29.csv`.
- Ablation absolute metrics source: `docs/superpowers/logs/rc-refgs-fd-p2-lite-complete-metrics-ablation-table-2026-05-29.csv`.
- The main full tables use absolute Base/RC values from the final main summary, not values reconstructed from deltas.
- The ablation full tables combine Base/RC rows from the main absolute metrics with wo_ref/wo_conf/rough_only rows from the complete ablation table.
- Averages are computed within dataset + split, and for ablations also within variant. Missing values are excluded from averages and displayed as `--` in LaTeX.
- Source columns named `reflective_region_ssim` and `reflective_region_lpips` were not found; available `reflective_ssim` and `reflective_lpips` columns are retained under their source metric names.
- The previously missing `reflective_region_psnr` delta is not reconstructed. Absolute `reflective_region_psnr` values are retained where present in the full metric sources.
<!-- FULL_METRIC_TABLES:END -->
