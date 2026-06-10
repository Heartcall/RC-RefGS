# Refl. Metrics Degradation Analysis

## 1. 现象概述

在当前 FD-P2-lite / non-Shiny-Real 完成实验范围内，RC 的 reflection consistency 改善与 Refl. PSNR、Refl. SSIM、Refl. LPIPS 的变化并不一致。按方向统一后的 improvement 定义为：PSNR/SSIM 使用 RC minus base，LPIPS 和 reflection consistency 使用 base minus RC，正值表示 RC 更好。整体统计如下：

| metric | win | loss | mean improvement | median improvement |
|---|---:|---:|---:|---:|
| Refl. PSNR | 16 | 12 | -0.061 | 0.019 |
| Refl. SSIM | 14 | 14 | -0.000162 | -0.000047 |
| Refl. LPIPS | 10 | 18 | -0.000406 | -0.000142 |

这说明 Refl. image quality 指标并没有随 reflection consistency 一起稳定提升。该现象不应被解释为 RC 必然失败，也不能说明 reflection consistency 指标无意义；更合理的解释是两类指标关注的误差形式不同。

## 2. 指标与训练目标不一致

训练中的基础重建项直接作用于 composited final RGB，即 `pbr_rgb` 与 ground-truth RGB 的 L1/DSSIM 组合。RC loss 则作用于 `spec_light`，通过 source depth 反投影、target projection 和双线性采样约束跨视角 specular prediction 的稳定性。其有效区域还经过 projection validity、depth consistency、source/target alpha、source roughness、normal agreement 和 specular confidence 加权。

相比之下，Refl. PSNR/SSIM/LPIPS 在 render-quality 评估中作用于 final rendered RGB，并使用 alpha 与 roughness 构成的 reflective mask。也就是说，RC 优化的是“几何对应区域内的 specular 稳定性”，而 Refl. image quality 衡量的是“单视角反射区域内 RGB 像素/感知误差”。这两个目标不必然同向。

## 3. 数据统计证据

reflection consistency 与 Refl. metrics 的相关性如下：

| metric | n | Pearson | Spearman | consistency-up quality-down rows |
|---|---:|---:|---:|---:|
| Refl. PSNR | 28 | 0.007 | -0.138 | 11 |
| Refl. SSIM | 28 | 0.042 | 0.017 | 13 |
| Refl. LPIPS | 28 | 0.100 | 0.111 | 17 |

最明显的 Refl. PSNR 下降场景：

| scene/split | improvement | base | RC |
|---|---:|---:|---:|
| shiny_blender_synthetic/coffee/train | -1.153 | 42.351 | 41.199 |
| glossy_synthetic/luyu/test | -0.656 | 31.369 | 30.714 |
| glossy_synthetic/luyu/train | -0.649 | 33.954 | 33.305 |
| glossy_synthetic/cat/test | -0.544 | 34.496 | 33.952 |
| shiny_blender_synthetic/coffee/test | -0.251 | 37.001 | 36.750 |

最明显的 Refl. PSNR 改善场景：

| scene/split | improvement | base | RC |
|---|---:|---:|---:|
| shiny_blender_synthetic/teapot/train | 0.787 | 50.348 | 51.136 |
| shiny_blender_synthetic/teapot/test | 0.290 | 47.424 | 47.714 |
| shiny_blender_synthetic/toaster/train | 0.231 | 35.977 | 36.207 |
| glossy_synthetic/potion/test | 0.174 | 34.026 | 34.200 |
| glossy_synthetic/bell/test | 0.145 | 32.165 | 32.310 |

最明显的 Refl. LPIPS 下降场景：

| scene/split | improvement | base | RC |
|---|---:|---:|---:|
| shiny_blender_synthetic/ball/test | -0.004307 | 0.026681 | 0.030988 |
| shiny_blender_synthetic/ball/train | -0.002788 | 0.022804 | 0.025592 |
| glossy_synthetic/luyu/test | -0.002417 | 0.024765 | 0.027182 |
| glossy_synthetic/luyu/train | -0.001706 | 0.019591 | 0.021298 |
| glossy_synthetic/cat/test | -0.001455 | 0.023703 | 0.025158 |

这些统计支持一个关键判断：存在多处“reflection consistency improvement > 0，但 Refl. quality improvement < 0”的行。因此，Refl. metrics 下降不是单个异常行造成的，而是当前 objective trade-off 的一部分。

## 4. 消融证据

消融表将 base、rc、wo_ref、wo_conf 和 rough_only 放在同一 scene/split 层级比较。各 variant 相对 RC 的方向统一结果如下，正值表示该 variant 在对应指标上优于 RC：

| variant vs RC | metric | win | loss | mean improvement vs RC |
|---|---|---:|---:|---:|
| base | Reflection consistency | 1 | 27 | -0.05247 |
| base | Refl. PSNR | 12 | 16 | 0.061 |
| base | Refl. SSIM | 14 | 14 | 0.000162 |
| base | Refl. LPIPS | 18 | 10 | 0.000406 |
| wo_ref | Reflection consistency | 1 | 27 | -0.04396 |
| wo_ref | Refl. PSNR | 15 | 13 | 0.076 |
| wo_ref | Refl. SSIM | 14 | 14 | 0.000242 |
| wo_ref | Refl. LPIPS | 17 | 11 | 0.000029 |
| wo_conf | Reflection consistency | 7 | 21 | -0.00638 |
| wo_conf | Refl. PSNR | 15 | 13 | 0.050 |
| wo_conf | Refl. SSIM | 16 | 12 | 0.000062 |
| wo_conf | Refl. LPIPS | 15 | 13 | 0.000188 |
| rough_only | Reflection consistency | 1 | 27 | -0.03926 |
| rough_only | Refl. PSNR | 8 | 20 | -0.091 |
| rough_only | Refl. SSIM | 14 | 14 | 0.000007 |
| rough_only | Refl. LPIPS | 15 | 13 | -0.000109 |

`wo_ref` 相对 RC 通常牺牲 reflection consistency，但若干 Refl. metrics 可与 RC 持平或更好，说明去掉反射一致性项可能释放单视角反射区域 RGB 拟合。`wo_conf` 使用 gamma=0.0，削弱 roughness confidence 的指数作用；其结果表明 confidence weighting 有助于 consistency，但并不保证 Refl. quality 统一改善。`rough_only` 不能复现 RC 的 consistency 行为，且其 Refl. metrics 也呈现 dataset/metric 依赖，说明 roughness smoothness 不是 RC trade-off 的充分替代解释。

## 5. 可能机制解释

### Objective mismatch

代码和指标共同支持该解释。RC loss 是 specular correspondence regularization；Refl. PSNR/SSIM/LPIPS 是 masked final-RGB image metric。前者鼓励跨视角稳定，后者奖励单视角像素/感知对齐，尤其会惩罚高光位置和强度的小偏差。

### High-frequency specular smoothing

RC loss 使用 L1 形式使 target sampled specular 贴近 detached source specular。该形式可能抑制某些 view-specific sharp highlights，使高光更保守或更平滑。当前没有 specular edge sharpness 或 variance 诊断，因此这是代码机制与指标趋势共同支持的合理假设，而不是已经被直接证明的结论。

### Mask mismatch

RC mask 比 Refl. metric mask 更严格：除了 alpha/roughness 外，还包含 target projection、depth consistency、target alpha、normal agreement 和 specular confidence。Refl. metrics 的 reflective mask 只由 alpha/roughness 选区决定，并作用于 final RGB。因此评估区域可能覆盖 RC 没有强约束、或 RC 权重较低的反射像素。

### Correspondence noise

RC 依赖 depth back-projection 和 target projection。若高反射区域的 depth、alpha 或 normal 不稳定，错误 correspondence 可能把 specular signal 对齐到不正确表面，造成局部 RGB 质量下降。当前结果包没有 depth-pass rate、normal agreement distribution 或 pair-angle distribution，因此该解释只能列为 plausible but unverified。

### Confidence weighting bias

RC 的 `spec_conf` 与 mean specular intensity 和 `(1 - roughness)^gamma` 相关，默认 gamma 为 2.0；`wo_conf` 使用 gamma=0.0。该设计会让低 roughness / 高 specular 区域受到更强约束，可能改善 consistency，但也可能放大高光位置偏差对 Refl. metrics 的影响。消融趋势只支持“confidence affects consistency and quality trade-off”，不支持“confidence 是唯一原因”。

### Small reflective mask sensitivity

Refl. metrics 在反射 mask 内计算，反射区域通常面积小、高频强，并且对边界/高光位置敏感。当前缺少 mask area ratio 和 per-image variance，所以不能定量证明小 mask 方差是主因，但它是解释 LPIPS/SSIM 波动的合理后续诊断方向。

### Schedule / lambda trade-off

RC 默认在 warm-up 后按固定频率启用，并引入额外 target render。若 lambda、启动时刻或 pair selection 不匹配场景，可能带来 consistency 与 image quality 之间的 trade-off。当前表格没有 lambda sweep，因此不能判断最优调度。

## 6. 哪些解释有证据，哪些只是合理假设

| Hypothesis                                               | Evidence from code                                                                                                                                       | Evidence from metrics                                                                                                                                                                   | Status                                 | Safe conclusion                                                                                                            | Needed follow-up                                                             |
|:---------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------|:---------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------|
| A. Optimization objective mismatch                       | train.py optimizes RGB reconstruction plus scheduled reflection_consistency_loss; render_quality_eval.py computes masked final-RGB PSNR/SSIM/LPIPS.      | Refl. PSNR Pearson 0.01, Spearman -0.14, tradeoff rows 11/28; Refl. SSIM Pearson 0.04, Spearman 0.02, tradeoff rows 13/28; Refl. LPIPS Pearson 0.10, Spearman 0.11, tradeoff rows 17/28 | Supported                              | Consistency improvement and masked RGB quality are related but non-equivalent objectives.                                  | Report consistency and image quality separately; add joint objective sweeps. |
| B. RC suppresses view-specific high-frequency highlights | reflection_consistency_loss uses L1 residual between detached source spec_light and sampled target spec_light.                                           | 44/84 dataset-split-metric scene rows are losses after direction alignment                                                                                                              | Partially supported                    | The loss form can favor stable specular predictions; current data are consistent with but do not directly prove smoothing. | Measure highlight edge sharpness and specular-map variance before/after RC.  |
| C. RC mask and reflective metric mask are mismatched     | RC mask adds projection, depth consistency, target alpha, normal agreement and specular confidence; Refl. metrics use alpha/roughness mask on final RGB. | Reflective metrics remain mixed despite strong consistency gains.                                                                                                                       | Supported as mechanism, not quantified | The optimized correspondence region can differ from the evaluated reflective image region.                                 | Export mask overlap, RC effective weight maps and reflective mask coverage.  |
| D. Wrong correspondence hurts reflective pixels          | RC projects source depth into target view and filters by depth tolerance, alpha and normal agreement.                                                    | Scene-level outliers exist, but no depth-pass or normal-pass diagnostics are available.                                                                                                 | Unknown / plausible                    | Correspondence noise cannot be ruled out from current aggregate tables.                                                    | Log depth consistency pass rate, normal agreement and pair angle per scene.  |
| E. Confidence weighting creates region bias              | spec_conf = mean(spec_light) * (1 - roughness)^gamma; wo_conf uses gamma 0.0 in the runner.                                                              | wo_conf vs RC reflective metrics: mean wins 46 / losses 38                                                                                                                              | Partially supported                    | Confidence weighting contributes to consistency, but does not create a uniform reflective-quality benefit.                 | Plot specular confidence distributions and test scene-adaptive thresholds.   |
| F. Small reflective masks make image metrics sensitive   | masked image metrics zero out non-reflective pixels and evaluate only alpha/roughness-selected regions.                                                  | No mask-area or per-image variance fields are present.                                                                                                                                  | Plausible but unverified               | Metric sensitivity is a reasonable concern but needs mask coverage and variance evidence.                                  | Record reflective mask area ratio and per-image metric variance.             |
| G. Trade-off is expected rather than a definite bug      | RC is an auxiliary scheduled regularizer on specular consistency, not a direct Refl. RGB loss.                                                           | Final logs report consistency gains with mixed render-quality effects.                                                                                                                  | Supported                              | The evidence supports an objective trade-off interpretation; it does not prove an implementation bug.                      | Run lambda/schedule/pair-angle sweeps and inspect qualitative specular maps. |

## 7. 论文中应如何表述

RC 的主要优化目标是跨视角反射预测的一致性，而 Refl. PSNR/SSIM/LPIPS 衡量的是反射区域内单视角 RGB 重建质量。二者关注的误差形式不同，因此在部分场景中会出现 reflection consistency 改善但 reflective-region image quality 下降的 trade-off。该现象说明 RC 更适合作为反射一致性正则，而非保证反射区域像素指标全面提升的通用插件。我们因此将 reflection consistency、reflective-region quality 和 full-image quality 分开报告，并在消融中明确分析 confidence weighting 与 roughness-only regularization 的作用边界。

## 8. 后续改进建议

1. 降低 `lambda_RC` 或采用 scene-adaptive lambda。
2. 更晚启动 RC，等待 depth、alpha 和 normal 更稳定。
3. 使用 color-preserving 或 perceptual-aware RC，减少对 final RGB 的副作用。
4. 对 RC loss 加 view-angle-aware weighting，避免过度约束大视角差高光。
5. 区分 sharp specular 与 broad specular，对尖锐高光降低一致性强度。
6. 改进 reflective mask，并报告 mask coverage 与 variance。
7. 尝试 symmetric but detached 或 EMA teacher，降低相互追逐不稳定性。
8. 对 pair selection 加 stronger overlap/depth/normal filtering。
9. 联合 reflective RGB reconstruction loss，使 consistency 与 masked RGB quality 更一致。
10. 记录 RC valid correspondence ratio、mean RC weight、depth pass rate、normal agreement、confidence distribution、pair angle distribution、highlight edge sharpness 和 specular map variance。
<!-- GEOMETRY_EVALUATION:START -->
## 9. Geometry / Mesh Quality Follow-up

几何补测进一步强化了当前 claim boundary：现有 evidence package 不能证明 reflection consistency improvement 会转化为 mesh quality improvement。由于缺少 GT mesh、predicted mesh、rendered depth/normal buffers，补测只能报告 point-cloud proxy diagnostics。该结果支持将 RC 暂时定位为 reflection consistency regularizer / diagnostic signal，并将下一阶段研究转向 geometry-aware RC 与 mesh-aware RC filtering，而不是直接声称其提升最终 surface quality。
<!-- GEOMETRY_EVALUATION:END -->
