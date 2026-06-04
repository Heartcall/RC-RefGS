# Table captions / 表格标题

## Table 1
中文：表 1 汇总 FD-P2-lite / non-Shiny-Real 已完成主实验中的 cross-view reflection consistency 对比。Delta 表示 RC minus base，reflection consistency 数值越低越好，因此 improvement 采用 base minus RC。该表支持 RC 在该范围内主要改善反射一致性，但不包含可用于反推 base/RC 绝对值的原始逐场景数值。

English: Table 1 summarizes cross-view reflection consistency on the completed FD-P2-lite / non-Shiny-Real main runs. Delta denotes RC minus base; lower reflection-consistency values are better, so improvement is reported as base minus RC. The table supports a scoped consistency gain, but it does not contain the raw per-scene base/RC absolute values.

## Table 2
中文：表 2 展示不同指标上的 RC win count、win rate 和平均 delta。PSNR/SSIM 数值越高越好，LPIPS 和 reflection consistency 数值越低越好。结果表明渲染质量指标存在 mixed / trade-off，不能写成全图质量全面提升。

English: Table 2 reports RC win counts, win rates and mean deltas across metrics. Higher is better for PSNR/SSIM, whereas lower is better for LPIPS and reflection consistency. The results indicate mixed rendering-quality effects and should not be interpreted as a universal full-image quality improvement.

## Table 3
中文：表 3 汇总已完成消融实验中的 wo_ref、wo_conf 和 rough_only 变体。Reflection consistency 为越低越好，归一化分数在统一指标方向后、仅在可用消融变体内部计算。该表用于分析消融趋势，不应被解读为 roughness smoothness 或 confidence filtering 的独立主贡献。

English: Table 3 summarizes the completed ablation variants wo_ref, wo_conf and rough_only. Reflection consistency is lower-is-better, and the normalized score is computed only among available ablation variants after aligning metric directions. The table is intended for diagnostic ablation analysis rather than promoting roughness smoothness or confidence filtering as standalone main contributions.

## Table 4
中文：表 4 给出论文主张边界，将有结果支持的表述与不安全表述分开。证据范围限于当前可用 FD-P2-lite / non-Shiny-Real 结果及其消融聚合。该表用于避免把反射一致性收益误写为全局渲染质量或 mesh quality 的必然提升。

English: Table 4 states claim boundaries by separating supported wording from unsafe wording. The evidence scope is limited to the available FD-P2-lite / non-Shiny-Real results and their ablation aggregates. The table helps prevent consistency gains from being overstated as guaranteed full-image or mesh-quality improvements.

## Table 5
中文：表 5 统计当前实验覆盖、完成情况与排除项。Shiny Blender Real 的 incomplete/OOM 单元被明确排除，独立几何质量指标在当前结果包中不可用。该表限定了本文结果可以支持和不能支持的实验结论。

English: Table 5 reports experiment coverage, completed runs and exclusions. Incomplete/OOM Shiny Blender Real cells are explicitly excluded, and independent geometry-quality metrics are unavailable in the current result package. The table defines which experimental conclusions are supported and which are not.
