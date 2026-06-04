# Figure captions / 图标题

## Figure 1
中文：图 1 展示 RC 在不同指标和 split 上的 win count / total。Reflection consistency 与 LPIPS 为越低越好，PSNR/SSIM 为越高越好。RC 在 reflection consistency 上最稳定，而图像质量指标呈现 mixed 趋势。

English: Figure 1 shows RC win counts over total valid rows across metrics and splits. Lower is better for reflection consistency and LPIPS, while higher is better for PSNR/SSIM. RC is most stable on reflection consistency, whereas image-quality metrics show mixed behavior.

## Figure 2
中文：图 2 展示每个 scene/split 的 reflection consistency improvement，其中正值表示 base minus RC 大于零，即 RC 更好。该图仅统计 FD-P2-lite / non-Shiny-Real 已完成 paired rows。除一个 test row 外，多数场景呈现一致性改善，但该图不评价全图渲染质量。

English: Figure 2 shows per-scene reflection-consistency improvement, where positive values indicate base minus RC is greater than zero. The plot includes only completed FD-P2-lite / non-Shiny-Real paired rows. Most scenes improve in consistency except one test row, but the figure does not assess full-image rendering quality.

## Figure 3
中文：图 3 将 reflection consistency improvement 与 full-image PSNR change 进行配对散点展示。横轴越大表示反射一致性改善越强，纵轴为 RC minus base 的 PSNR 变化。散点分布说明反射一致性收益与全图 PSNR 改善并不完全一致，因此需要分开报告。

English: Figure 3 plots reflection-consistency improvement against full-image PSNR change for paired rows. Larger x-values indicate stronger consistency gains, and the y-axis is the RC-minus-base PSNR change. The distribution shows that consistency gains do not necessarily coincide with full-image PSNR improvements, motivating separate reporting.

## Figure 4
中文：图 4 展示可用消融变体在多个指标上的归一化表现。所有指标先按方向统一为越高越好，再在每个 dataset/split/metric 内做 min-max normalization。该图用于比较 wo_ref、wo_conf 和 rough_only 的相对趋势，不包含缺失的 base/RC 原始聚合值。

English: Figure 4 visualizes normalized performance for available ablation variants across metrics. All metrics are first direction-aligned so that higher is better and then min-max normalized within each dataset/split/metric group. The figure compares relative trends for wo_ref, wo_conf and rough_only, without fabricating missing raw base/RC aggregate values.

## Figure 5
中文：图 5 展示主实验、消融实验和不可用几何指标的覆盖情况。已完成 non-Shiny-Real 结果可用于有限范围的 consistency 和 ablation 结论，Shiny Blender Real incomplete/OOM 单元与几何质量结论不能作为完成实验使用。该图用于限定论文结果的外推范围。

English: Figure 5 summarizes coverage for main runs, ablations and unavailable geometry metrics. Completed non-Shiny-Real results support scoped consistency and ablation conclusions, whereas incomplete/OOM Shiny Blender Real cells and absent geometry metrics cannot be treated as completed evidence. The figure constrains the extrapolation scope of the paper results.

## Figure 6 plan
中文：当前脚本未生成 qualitative montage，因为未指定可核验的 GT/base/RC/specular/mask 图像集合。若后续补充渲染图，可按 GT / base / RC / error / specular / reflective mask 的列布局制作，并在每个 panel 标明 scene、split、method 和 metric。

English: This script does not generate a qualitative montage because no verified GT/base/RC/specular/mask image set is specified. If render images are provided later, a GT / base / RC / error / specular / reflective mask layout can be assembled with scene, split, method and metric labels for every panel.
