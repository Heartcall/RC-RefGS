# Experiment Claim Boundary

| Claim | Supported by available results? | Evidence type | Scope | Safe wording | Unsafe wording |
|---|---|---|---|---|---|
| RC improves cross-view reflection consistency. | Yes, within scope. | Completed paired-scene CSV and win counts. | FD-P2-lite / non-Shiny-Real / train and test paired rows. | RC improves cross-view reflection consistency in the completed FD-P2-lite non-Shiny-Real setting. | RC universally improves all reflective reconstruction results. |
| RC improves full-image PSNR/SSIM/LPIPS. | Not as a universal claim. | Metric-specific win counts and trade-off rows. | Available completed rows only. | Full-image metrics show mixed, metric-dependent changes and should be reported separately. | RC guarantees better full-image rendering quality. |
| RC improves reflective-region quality. | Mixed support. | Reflective-region win counts. | Available completed rows only. | Reflective-region quality has mixed metric-specific behavior. | RC always improves reflective-region PSNR/SSIM/LPIPS. |
| Confidence weighting contributes to the RC behavior. | Trend-level support. | wo_conf ablation aggregate. | FD-P2-lite non-Shiny-Real ablation rows. | Removing confidence weighting weakens the observed consistency behavior in this scoped ablation. | Confidence weighting is always the dominant or sufficient factor. |
| Roughness smoothness alone explains RC. | No. | rough_only ablation aggregate. | FD-P2-lite non-Shiny-Real ablation rows. | Roughness-only regularization does not reproduce the main RC consistency behavior. | Roughness smoothness is the theoretical core of RC. |
| RC improves mesh quality. | No. | GT mapping/evaluator available, but 0/28 main and 0/70 ablation prediction rows are currently evaluable. | FD-P2-lite non-Shiny-Real completed-row manifest; historical prediction roots absent. | GT resources are available, but exact completed prediction geometry must be restored before true geometry can be evaluated. | RC necessarily improves mesh or geometry quality. |


<!-- FULL_METRIC_TABLES:START -->
## Full Metric Table Claim Boundary

| Claim | Supported by full metric tables? | Safe wording | Unsafe wording |
|---|---|---|---|
| Per-dataset/per-scene full metric comparisons are available. | Yes, within FD-P2-lite non-Shiny-Real completed runs. | The full metric tables provide per-dataset and per-scene numerical comparisons for available metrics. | The tables prove complete validation on every reflective dataset. |
| RC mainly improves reflection consistency. | Supported within the completed scope. | RC shows its most stable gain on cross-view reflection consistency in the completed scope. | RC is best on every dataset, scene and metric. |
| Full-image and reflective quality improve universally. | No. | Full-image and reflective-region quality should be reported metric by metric. | RC necessarily improves PSNR/SSIM/LPIPS. |
| Ablations clarify component boundaries. | Diagnostic support only. | The ablation table helps analyze confidence weighting and roughness-only boundaries in this scope. | rough_only can replace RC, or confidence weighting is universally dominant. |
| Mesh quality improves. | No independent support. | Mesh or geometry quality requires separate evaluation. | RC necessarily improves mesh quality. |
<!-- FULL_METRIC_TABLES:END -->
<!-- GEOMETRY_EVALUATION:START -->
## Geometry / Mesh Quality Claim Boundary

GT geometry 现已覆盖全部 14 个 scoped scenes：Glossy Synthetic 使用 8 个 `eval_pts.ply` GT point clouds，Shiny Blender Synthetic 使用 6 个 GT meshes。TRUE geometry evaluator 已实现 deterministic sampling、raw-coordinate Chamfer/accuracy/completeness 和 0.5%/1%/2% GT bbox 阈值 F-score，并将 similarity alignment 限定为显式 diagnostic。

Historical boundary: exact May 27/28 prediction geometry is still unavailable, so the historical recovery package remains main `0/28` and ablation `0/70`; no historical average is reported and no `Ref-GS-I2` substitution is allowed.

New-rerun smoke evidence: the separately labeled `shiny_blender_synthetic/ball` Base/RC smoke has two non-empty meshes and two finite raw-coordinate GT rows. Base/RC Chamfer-L1 is `0.0077380615/0.0077896341`; 0.5% F-score is `0.9990550/0.9989650`, with both equal to `1.0` at 1% and 2% thresholds. This validates the extraction/evaluation pipeline but does not show RC geometry improvement.

Safe wording: GT resources and the repaired extraction/evaluation pipeline are operational for the ball smoke; current one-scene evidence shows comparable geometry with Base slightly better on primary Chamfer and strict-threshold F-score. Broader RC mesh-quality conclusions require separately reviewed multi-scene evidence.

Unsafe wording: RC 必然改善 Chamfer、F-score、normal/depth error 或 mesh quality。

New-rerun boundary: the ball Base/RC smoke is complete and isolated from historical outputs. Pipeline status is GO; automatic expansion to the remaining rerun matrix is NO-GO pending separate resource review, and the mesh-quality improvement claim remains NO-GO because the smoke does not favor RC on primary geometry metrics.
<!-- GEOMETRY_EVALUATION:END -->
