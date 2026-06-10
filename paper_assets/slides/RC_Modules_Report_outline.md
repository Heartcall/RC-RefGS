# RC Modules Report Outline

Deck: `paper_assets/slides/RC_Modules_Report.pptx`

Scope: FD-P2-lite / non-Shiny-Real / completed runs. No training or new evaluation is performed.

## Slide 1: Title
- Takeaway: RC 更适合作为反射一致性正则与诊断模块。
- Source: 整理自论文草稿、实验表格与诊断报告

## Slide 2: Motivation
- Takeaway: 普通 RGB loss 容易把高光当成单视角颜色拟合。
- Source: 论文 Introduction

## Slide 3: Core idea
- Takeaway: RC 只依赖 renderer intermediate buffers，而不是特定 Gaussian 参数化。
- Source: 论文 Method: Renderer-Buffer Interface

## Slide 4: Method overview
- Takeaway: RC 的流程是 render buffers、几何投影、可微采样和加权 specular consistency。
- Source: 论文 Method: Cross-view Reflective Correspondence

## Slide 5: Buffer interface
- Takeaway: 可迁移性来自最小 buffer contract。
- Source: 论文 Method: Renderer-Buffer Interface

## Slide 6: Main finding
- Takeaway: RC 的最稳定收益集中在 reflection consistency。
- Source: paper_assets/figures/fig1_rc_win_count_by_metric.png

## Slide 7: Full metrics
- Takeaway: per-dataset full metric table 支持逐指标讨论，而非整体胜利叙事。
- Source: paper_assets/data/main_full_metrics_by_dataset_avg.csv

## Slide 8: Reflective-region problem
- Takeaway: Refl. PSNR/SSIM/LPIPS 没有稳定提升。
- Source: paper_assets/diagnostics/figD1_refl_metric_improvements_by_scene.png

## Slide 9: Trade-off
- Takeaway: Consistency improvement 不能推出 Refl. image-quality improvement。
- Source: paper_assets/diagnostics/figD2_consistency_vs_refl_quality_tradeoff.png

## Slide 10: Ablation
- Takeaway: 消融显示 confidence 和 RC loss 的作用边界。
- Source: paper_assets/diagnostics/figD3_ablation_refl_metrics_heatmap.png

## Slide 11: Why worse
- Takeaway: Refl. metrics 下降更像 objective trade-off，而不是已证实的单点 bug。
- Source: paper_assets/diagnostics/refl_metrics_degradation_analysis_zh.md

## Slide 12: Mesh limitation
- Takeaway: 缺少独立几何指标，因此不能主张 mesh quality 改善。
- Source: paper_assets/experiment_claim_boundary.md

## Slide 13: Future direction
- Takeaway: 下一阶段应从 consistency-only 转向 geometry-aware / mesh-aware RC。
- Source: 诊断报告后续改进建议

## Slide 14: Next experiments
- Takeaway: 下一步需要补轻量诊断与几何指标。
- Source: paper_assets/diagnostics/diagnostic_missing_fields.md

## Slide 15: Conclusion
- Takeaway: 论文主张应降级为反射一致性正则，并转向几何感知验证。
- Source: 汇总自结果摘要、claim boundary 与诊断报告

## Evidence Boundary
- Supported: RC mainly improves cross-view reflection consistency within the completed FD-P2-lite / non-Shiny-Real scope.
- Mixed: full-image and reflective-region PSNR/SSIM/LPIPS.
- Unsupported: universal quality improvement, full reflective dataset validation, or mesh-quality improvement.
- Missing diagnostics: mask coverage, RC valid correspondence ratio, depth/normal pass rate, pair-angle distribution, highlight sharpness, and mesh metrics.
