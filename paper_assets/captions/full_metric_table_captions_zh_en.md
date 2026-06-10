# Full metric table captions / 全指标表格标题

## Main full-metric tables

中文：表 X 展示主实验在不同数据集下的全部指标数值对照。每个数据集内部逐 scene 报告 Base 与 RC 的 cross-view reflection consistency、full-image PSNR/SSIM/LPIPS 以及可用的 reflective-region 或 reflective-mask metrics，并在同一 dataset 与 split 内给出平均值。RC$\downarrow$ 和 LPIPS$\downarrow$ 表示数值越低越好，PSNR$\uparrow$ 和 SSIM$\uparrow$ 表示数值越高越好。缺失项以 “--” 表示，未参与平均值计算。

English: Table X reports full-metric main comparisons by dataset. Within each dataset, per-scene Base and RC results are listed for cross-view reflection consistency, full-image PSNR/SSIM/LPIPS, and available reflective-region or reflective-mask metrics, followed by averages computed within the same dataset and split. RC$\downarrow$ and LPIPS$\downarrow$ indicate lower-is-better metrics, while PSNR$\uparrow$ and SSIM$\uparrow$ indicate higher-is-better metrics. Missing entries are denoted by “--” and excluded from averages.

## Ablation full-metric tables

中文：表 Y 展示消融实验在不同数据集下的全部指标数值对照。每个数据集内部逐 scene、split 和 variant 报告可用指标，并对每个 variant 分别计算 dataset-level 平均值。该表用于分析 RC、confidence weighting 和 roughness-only regularization 的作用边界，而不应被解释为所有指标的全面提升。

English: Table Y reports full-metric ablation comparisons by dataset. Within each dataset, available metrics are listed for each scene, split and variant, followed by per-variant dataset-level averages. The table is intended to analyze the roles and boundaries of RC, confidence weighting and roughness-only regularization, and should not be interpreted as a universal improvement across all metrics.
