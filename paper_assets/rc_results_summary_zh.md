# RC Results Summary (中文)

## 1. 主实验结论

在已完成的 FD-P2-lite / non-Shiny-Real 范围内，RC 的主要、最稳定收益体现在 cross-view reflection consistency。主实验的 paired scene/split 统计显示，train split 的有效行均由 RC 取得更低的一致性误差，test split 中除一个场景外也呈现一致性改善。因此，论文中可以安全表述为：RC 在当前完成范围内主要改善几何一致区域中的跨视角反射预测稳定性。

## 2. 渲染质量 trade-off

Full-image PSNR/SSIM/LPIPS 与 reflective-region PSNR/SSIM/LPIPS 不应和 reflection consistency 合并成单一“质量提升”结论。现有 win count 与 trade-off 行显示，不同图像质量指标之间存在 mixed behavior：部分场景和 split 中 RC 改善一致性的同时会降低至少一个渲染质量指标。因此，论文结果应将 reflection consistency、reflective-region quality 和 full-image quality 分开报告。

## 3. 消融实验结论

消融结果支持有限范围内的诊断性结论：去除 reflection-consistency supervision 的 wo_ref 不能复现 RC 的主要一致性行为；去除 confidence weighting 的 wo_conf 会削弱观察到的一致性趋势，但不能据此声称 confidence 是所有场景中的唯一或主导因素；rough_only 不能单独复现 RC 的 reflection consistency 行为。因此，roughness smoothness 应作为辅助正则讨论，而不是 RC 模块组的核心理论贡献。

## 4. 实验覆盖与限制

当前可用于论文主结论的范围是 FD-P2-lite / non-Shiny-Real / 已完成 runs。Shiny Blender Real 的 incomplete/OOM 单元被排除，不能写成完整验证；full FD-P2 与 full ablation 也不能据此宣称全部完成。当前结果包没有独立几何或 mesh quality 指标，因此不能主张 RC 必然改善几何质量或 mesh quality。

## 5. 论文安全表述

Safe claim：RC 在已完成 FD-P2-lite / non-Shiny-Real 设置下主要改善 cross-view reflection consistency，并且该收益需要与 full-image 和 reflective-region 渲染质量指标分开评价。

Unsafe claim：RC 全面优于所有 baseline、必然提升 PSNR/SSIM/LPIPS、已在所有 reflective datasets 上完成验证，或必然提升 mesh quality。


<!-- FULL_METRIC_TABLES:START -->
## 6. Per-dataset full metric tables

新增的 full metric tables 将主实验和消融实验拆分到 dataset、split、scene 与 method/variant 层级，避免只用 win-count 或平均 trade-off 概括结果。主实验表使用 Base 与 RC 的绝对指标值；消融表将 Base/RC 与 wo_ref、wo_conf、rough_only 放在同一 per-scene 表格中比较。所有 Avg. 行均在同一 dataset + split 内计算，消融表进一步按 variant 分开计算。缺失项以 “--” 显示并排除出平均值，因此这些表支持逐指标、逐范围的谨慎讨论，而不支持“所有指标全面提升”的结论。
<!-- FULL_METRIC_TABLES:END -->
<!-- GEOMETRY_EVALUATION:START -->
## 7. Geometry / Mesh Quality 补测

补测结果显示，当前 completed runs 只有 final point-cloud artifact 可用于 Level 3 proxy diagnostics；没有 accepted GT mesh / GT point cloud、没有 predicted mesh，也没有 saved rendered depth/normal buffers。因此，本结果包不能支持 mesh quality improvement claim。当前更安全的表述是：RC 的 consistency 改善尚未稳定转化为可验证的 surface / mesh quality 提升，后续需要 geometry-aware RC 或 mesh-aware RC filtering，并补充 Chamfer/F-score/normal/depth 指标。
<!-- GEOMETRY_EVALUATION:END -->
