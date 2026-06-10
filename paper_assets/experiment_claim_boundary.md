# Experiment Claim Boundary

| Claim | Supported by available results? | Evidence type | Scope | Safe wording | Unsafe wording |
|---|---|---|---|---|---|
| RC improves cross-view reflection consistency. | Yes, within scope. | Completed paired-scene CSV and win counts. | FD-P2-lite / non-Shiny-Real / train and test paired rows. | RC improves cross-view reflection consistency in the completed FD-P2-lite non-Shiny-Real setting. | RC universally improves all reflective reconstruction results. |
| RC improves full-image PSNR/SSIM/LPIPS. | Not as a universal claim. | Metric-specific win counts and trade-off rows. | Available completed rows only. | Full-image metrics show mixed, metric-dependent changes and should be reported separately. | RC guarantees better full-image rendering quality. |
| RC improves reflective-region quality. | Mixed support. | Reflective-region win counts. | Available completed rows only. | Reflective-region quality has mixed metric-specific behavior. | RC always improves reflective-region PSNR/SSIM/LPIPS. |
| Confidence weighting contributes to the RC behavior. | Trend-level support. | wo_conf ablation aggregate. | FD-P2-lite non-Shiny-Real ablation rows. | Removing confidence weighting weakens the observed consistency behavior in this scoped ablation. | Confidence weighting is always the dominant or sufficient factor. |
| Roughness smoothness alone explains RC. | No. | rough_only ablation aggregate. | FD-P2-lite non-Shiny-Real ablation rows. | Roughness-only regularization does not reproduce the main RC consistency behavior. | Roughness smoothness is the theoretical core of RC. |
| RC improves mesh quality. | No. | No independent geometry metric table in the result package. | Current available results. | Geometry filtering should be treated as an engineering extension requiring separate evaluation. | RC necessarily improves mesh or geometry quality. |


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

当前 geometry 补测只从已有 completed runs 的 final point-cloud PLY 中得到 Level 3 proxy diagnostics（vertex count、bbox diagonal、input-to-final vertex-count delta）。当前没有 accepted GT mesh / GT point cloud、没有已抽取 predicted mesh，也没有 saved rendered depth/normal buffers，因此 Chamfer、F-score、depth error、normal error 均不可计算。

Safe wording: 当前结果不支持 RC 改善 mesh quality 的结论；RC 的 reflection consistency 改善仍需通过 geometry-aware / mesh-aware 评估验证。

Unsafe wording: RC 必然改善 Chamfer、F-score、normal/depth error 或 mesh quality。
<!-- GEOMETRY_EVALUATION:END -->
