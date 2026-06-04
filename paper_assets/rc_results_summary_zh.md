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
