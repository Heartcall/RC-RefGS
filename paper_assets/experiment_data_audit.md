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
