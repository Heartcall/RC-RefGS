# Experiment Claim Boundary

| Claim | Supported by available results? | Evidence type | Scope | Safe wording | Unsafe wording |
|---|---|---|---|---|---|
| RC improves cross-view reflection consistency. | Yes, within scope. | Completed paired-scene CSV and win counts. | FD-P2-lite / non-Shiny-Real / train and test paired rows. | RC improves cross-view reflection consistency in the completed FD-P2-lite non-Shiny-Real setting. | RC universally improves all reflective reconstruction results. |
| RC improves full-image PSNR/SSIM/LPIPS. | Not as a universal claim. | Metric-specific win counts and trade-off rows. | Available completed rows only. | Full-image metrics show mixed, metric-dependent changes and should be reported separately. | RC guarantees better full-image rendering quality. |
| RC improves reflective-region quality. | Mixed support. | Reflective-region win counts. | Available completed rows only. | Reflective-region quality has mixed metric-specific behavior. | RC always improves reflective-region PSNR/SSIM/LPIPS. |
| Confidence weighting contributes to the RC behavior. | Trend-level support. | wo_conf ablation aggregate. | FD-P2-lite non-Shiny-Real ablation rows. | Removing confidence weighting weakens the observed consistency behavior in this scoped ablation. | Confidence weighting is always the dominant or sufficient factor. |
| Roughness smoothness alone explains RC. | No. | rough_only ablation aggregate. | FD-P2-lite non-Shiny-Real ablation rows. | Roughness-only regularization does not reproduce the main RC consistency behavior. | Roughness smoothness is the theoretical core of RC. |
| RC improves mesh quality. | No. | No independent geometry metric table in the result package. | Current available results. | Geometry filtering should be treated as an engineering extension requiring separate evaluation. | RC necessarily improves mesh or geometry quality. |
