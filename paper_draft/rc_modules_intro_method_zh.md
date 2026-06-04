# 标题建议

1. 跨视角反射一致性：面向高反射神经渲染的可插拔优化框架（Cross-view Reflection Consistency: A Plug-and-play Optimization Framework for Reflective Neural Rendering）
2. RC-Modules：一种脱离特定表示的反射一致性优化模块组（RC-Modules: Representation-agnostic Reflection Consistency Optimization Modules）
3. 面向反射场景重建的 Renderer Buffer 驱动跨视角一致性学习（Renderer-buffer-driven Cross-view Consistency Learning for Reflective Scene Reconstruction）
4. 基于中间渲染缓冲的反射一致性约束（Reflection Consistency from Intermediate Renderer Buffers）
5. 可迁移反射一致性优化：从单视角高光拟合到跨视角几何对应（Transferable Reflection Consistency Optimization: From Single-view Highlight Fitting to Cross-view Geometric Correspondence）

# Introduction

高反射场景重建是神经渲染和 3D Gaussian Splatting 系列方法中的一个核心难题。透明或近镜面材质会使图像颜色强烈依赖视角、照明方向和表面法线，导致同一三维表面在不同视角中呈现显著不同的高光、反射边界和环境映射。对于新视角合成、数字资产生成、逆向材质估计和可编辑三维内容生产而言，系统不仅需要在训练视角上重建像素颜色，还需要使反射分量在几何上可解释、跨视角上稳定，并在未见视角中保持一致的外观变化。

现有 3DGS、2DGS 和 NeRF-like 方法通常通过单视角或逐视角的 RGB 重建误差学习场景表示。这样的监督在漫反射区域通常有效，但在高反射区域存在内在歧义：模型可以通过局部颜色、视角相关特征、法线扰动或不透明度调整来拟合某一视角下的高光，而不必保证该高光与相邻视角中同一三维表面的反射响应一致。换言之，view-dependent specular appearance 容易被退化为单视角颜色拟合问题，而不是被建模为受几何对应约束的跨视角反射现象。

Ref-GS 等方向分解方法通过显式引入方向编码、粗糙度、反照率和 specular 分支，已经比普通颜色场表示更适合高反射场景。它们使反射外观可以通过法线、视线方向和材质特征共同决定，而不是完全混入低阶颜色参数中。然而，方向分解本身并不自动保证跨视角一致性。只要训练目标主要作用在最终 RGB 上，模型仍可能用多个内部自由度共同补偿同一反射区域的误差，从而在训练视角上取得可接受的重建质量，但在跨视角 specular 对应上产生不稳定预测。

本文将 RC-RefGS 中相对 Ref-GS 的优化部分重构为一个脱离特定表示的 RC 模块组。核心思想不是绑定某一种 Gaussian 参数化、某个特定 specular MLP 或某套 PBR 分解，而是要求 renderer 显式暴露一组 intermediate buffers，包括最终颜色、specular 分量、反射置信度或 roughness、alpha/visibility、depth 以及 normal。给定这些 buffers，RC 模块组可以通过 source view 的深度反投影、target view 的几何投影和可微采样，在不同视角之间建立同一表面的 reflective correspondence，并对 specular 分量施加 cross-view reflection consistency。

具体而言，RC 模块组包含六类可复用机制。第一，Renderer Intermediate Buffer Interface 规定可插拔方法需要提供的最小图像空间缓冲。第二，Cross-view Reflection Consistency Loss 用几何投影将 source specular map 与 target specular map 对齐并计算一致性误差。第三，Confidence-weighted Reflective Correspondence 将 alpha、depth consistency、normal agreement 和 material/specular confidence 组合为权重，减少错误对应和非反射区域对 loss 的干扰。第四，Scheduled RC Training Integration 在训练几何和 alpha 相对稳定后、按固定频率启用 RC 约束，以控制额外 target render 成本。第五，Material/Roughness Smoothness Regularization 作为可选材料正则和消融控制存在，但不构成跨视角 RC 的核心理论贡献。第六，Reflection-specific Evaluation Protocol 将 reflection consistency、reflective-region quality 和 full-image quality 分开报告，以避免把反射一致性收益误写为全面渲染质量提升。

这种表述使 RC 模块组可以迁移到不同可微 renderer。对于 3DGS、2DGS、GaussianShader、3DGS-DR 或 NeRF-like reflective reconstruction，方法不必复制 Ref-GS 的 Sph-Mip 编码、Gaussian feature 或 light MLP；它们只需满足最小 buffer contract：可渲染 specular 或 view-dependent residual，可输出 depth/alpha/normal，并能在相机之间进行投影和采样。由此，RC 模块组更适合被定位为 renderer-buffer-driven optimization，而不是某个 Ref-GS 内部参数的附加正则项。

仓库中的实验日志也提示了这种定位的必要性。在 FD-P2-lite / non-Shiny-Real 范围内，RC 在 `mean_reflection_consistency` 上表现出稳定改善，主比较中 train 14/14、test 13/14 个 paired-scene rows 支持 RC；但 PSNR、SSIM、LPIPS 以及 reflective-region 指标呈现 mixed/tradeoff。Shiny Blender Real 因 OOM 被排除，完整 17-scene FD-P2 和完整 51-cell ablation 结论仍为 NO-GO。因此，本文将 RC 定位为反射一致性优化模块，而不是保证全局图像质量、几何质量或材质分解全面提升的通用插件。

本文的贡献可概括为：提出一个脱离特定表示的 renderer-buffer-driven 反射一致性优化框架；设计一种基于深度反投影、目标视角投影和可微采样的 cross-view specular consistency loss；提出 confidence-weighted reflective correspondence，将 alpha、depth consistency、normal agreement 和 material/specular confidence 结合起来；给出 scheduled training、ablation protocol 和 reflection-specific metrics，用于安全评估该类优化模块的收益边界。

# Method

## 1. Problem Formulation

给定多视角训练集合

\[
\mathcal{D}=\{(I_i,\Pi_i)\}_{i=1}^{N},
\]

其中 \(I_i\) 表示第 \(i\) 个视角的观测图像，\(\Pi_i\) 表示对应相机参数，包括内参、外参和投影矩阵。设可微渲染器为

\[
R_\theta(\Pi_i) \rightarrow \mathcal{B}_i,
\]

其中 \(\theta\) 是任意可学习场景表示的参数，\(\mathcal{B}_i\) 是 renderer 返回的中间缓冲集合。最终渲染图像记为 \(\hat{I}_i\)，反射或高光分量记为 \(S_i\)，可见性或 alpha 记为 \(A_i\)，深度记为 \(D_i\)，法线记为 \(N_i\)，材质或 specular confidence 记为 \(C_i\)。

本文不假设 \(\theta\) 必须是 Ref-GS 的 Gaussian 参数。它可以来自 3D Gaussian Splatting、2D Gaussian Splatting、neural field、deferred shading renderer 或其他可微渲染框架。RC 模块组只要求 renderer 能提供可投影的几何缓冲和可采样的反射缓冲。因此，本文的优化目标可以写为

\[
\min_\theta \sum_i \mathcal{L}_{rgb}(\hat{I}_i,I_i)
+ \lambda_{rc}(t)\mathcal{L}_{rc}
+ \lambda_{reg}(t)\mathcal{L}_{reg},
\]

其中 \(\mathcal{L}_{rgb}\) 是目标方法原有的重建项，\(\mathcal{L}_{rc}\) 是跨视角反射一致性项，\(\mathcal{L}_{reg}\) 是可选材料或几何正则。调度权重 \(\lambda_{rc}(t)\) 和 \(\lambda_{reg}(t)\) 允许 RC 在训练早期关闭，并在几何、alpha 或基础颜色相对稳定后启用。

## 2. Renderer Buffer Interface

RC 模块组的最小接口是一个 renderer-buffer contract。给定视角 `view`，renderer 应返回如下语义等价的 buffers：

```python
render(view) -> {
    "rgb": I_hat,
    "specular_rgb": S,
    "specular_confidence": C,
    "alpha": A,
    "depth": D,
    "normal_render": N_r,
    "normal_depth": N_d,
}
```

在当前 RC-RefGS 实例中，`rgb` 对应 `pbr_rgb`，`specular_rgb` 对应 `spec_light`，`specular_confidence` 由 `roughness_map` 和 specular intensity 共同构造，`alpha` 对应 `rend_alpha`，`depth` 对应 `surf_depth`，`normal_render` 对应 `rend_normal`，`normal_depth` 对应 `surf_normal`。这些 key 都是图像空间 tensor，而不是 Gaussian 内部参数。因此，RC loss 可以直接消费 renderer 输出，而不需要访问或修改底层表示的优化变量。

该接口的设计目的有两点。第一，它把可迁移性边界放在 renderer 输出层，而不是放在 Ref-GS 的特定建模层。第二，它使不同模块共享同一组 buffers：RC loss 使用 specular、alpha、depth、normal 和 confidence；roughness smoothness 使用 material/confidence map；reflection-specific evaluation 使用相同 mask 定义反射区域；confidence-aware mesh filtering 使用 alpha 和 normal agreement 过滤低可信深度。

在迁移到没有显式 roughness 的方法时，`specular_confidence` 不应被强行解释为物理粗糙度。它可以是 learned reflective confidence、specular branch activation、view-dependent residual magnitude，或由 alpha、normal 稳定性和高光强度估计得到的反射区域置信度。关键要求是该量能在图像空间标记更可能发生镜面反射或强 view-dependent appearance 的区域。

## 3. Cross-view Reflection Consistency

对于 source view \(s\) 和 target view \(t\)，RC loss 首先使用 source depth 将像素 \(u\) 反投影为世界坐标点：

\[
X_s(u)=\Pi_s^{-1}(u,D_s(u)).
\]

然后将该三维点投影到 target view，得到 target 像素坐标 \(v\) 和预测 target 深度 \(\hat{z}_t\)：

\[
(v,\hat{z}_t)=\Pi_t(X_s(u)).
\]

在 target specular map 上使用双线性采样得到

\[
\tilde{S}_{t \leftarrow s}(u)=\operatorname{sample}(S_t,v).
\]

若 target alpha 和 target depth 同时支持该投影点，则 source 像素 \(u\) 和 target 采样位置 \(v\) 被视为候选 reflective correspondence。当前实现中的几何流程包括 `backproject_depth`、`project_points` 和 `grid_sample`。它们分别完成 source depth 反投影、target NDC 投影以及 target map 可微采样。

跨视角反射一致性残差定义为

\[
r_{s \rightarrow t}(u)=
\left\|
\operatorname{sg}(S_s(u))-\tilde{S}_{t \leftarrow s}(u)
\right\|_1,
\]

其中 \(\operatorname{sg}(\cdot)\) 表示 stop-gradient。当前实现对 source specular 使用 detach，使梯度主要回传到 target sampled specular 路径。该设计降低了双视角同时相互追逐造成的早期不稳定，但也意味着对称形式

\[
\mathcal{L}_{rc}^{sym}=\mathcal{L}_{s\rightarrow t}+\mathcal{L}_{t\rightarrow s}
\]

属于可迁移扩展，而不是当前仓库已经验证的事实。

## 4. Confidence-weighted Reflective Correspondence

反射区域的跨视角对应容易受到遮挡、depth 噪声、低 alpha 区域、非镜面材质和 normal 不一致的影响。因此，RC 模块组不对所有 source 像素等权施加 specular loss，而是构造二值 mask 和连续置信度权重。

首先定义有效性 mask：

\[
M(u)=
M_{proj}(u)
M_{depth}(u)
M_{\alpha}(u)
M_{refl}(u)
M_{normal}(u).
\]

其中 \(M_{proj}\) 要求投影坐标位于 target 图像有效区域且深度为正；\(M_{depth}\) 要求 target sampled depth 与 projected depth 的相对误差小于阈值；\(M_{\alpha}\) 要求 source 和 target 均为可见表面；\(M_{refl}\) 要求该点属于较高反射置信度区域；\(M_{normal}\) 要求 renderer normal 与 depth-derived normal 的点积为正。

连续权重写为

\[
w(u)=M(u)\,A_s(u)\,\tilde{A}_{t \leftarrow s}(u)\,
\max(0, N^r_s(u)\cdot N^d_s(u))\,C_s(u).
\]

在当前 Ref-GS 实例中，反射置信度实现为

\[
C_s(u)=
\operatorname{clamp}(\operatorname{mean}(S_s(u)),0,1)
\left(1-\operatorname{clamp}(R_s(u),0,1)\right)^{\gamma},
\]

其中 \(R_s\) 是 `roughness_map`，\(\gamma\) 默认值为 2.0。对于无 roughness 的 renderer，可用 learned confidence 或 specular residual confidence 替代该项。

最终 RC loss 为

\[
\mathcal{L}_{rc}(s,t)=
\frac{\sum_u w(u)\,r_{s\rightarrow t}(u)}
{\sum_u w(u)+\epsilon}.
\]

若有效权重和为 0，当前实现返回 0，以避免无有效对应时产生不稳定梯度。这一行为对迁移很重要，因为稀疏反射、高遮挡或相机 baseline 不合适的数据集可能在部分 iteration 中没有可用 pair。

## 5. Scheduled RC Training Integration

RC 模块组作为附加优化项插入目标方法原有训练流程。当前实例中的基础训练目标包含最终 PBR RGB 的 L1 + DSSIM、早期 alpha BCE warmup、normal self-consistency 正则，以及可选 roughness TV 正则。RC loss 只有在以下条件同时满足时启用：

\[
\lambda_{rc}>0,\quad t\geq t_{start},\quad t\bmod K=0,\quad \text{pair}(s)\neq \varnothing.
\]

代码默认参数为：`lambda_ref_consistency=0.0`、`ref_consistency_start=3000`、`ref_consistency_every=4`、`ref_consistency_max_angle=20.0`、`ref_consistency_gamma=2.0`。这意味着训练代码默认关闭 RC，实验 runner 的 `rc` variant 才显式设置 `lambda_ref_consistency`。这种 off-by-default 设计对可插拔模块尤为重要：它允许研究者先复现 base renderer，再逐步打开 RC，并通过相同训练路径进行 controlled ablation。

RC 的主要额外成本来自 target view 的第二次 render。若每 \(K\) 次迭代启用一次 RC，则平均每次迭代增加约 \(1/K\) 个 target render。实际迁移时，应优先在 alpha、depth 和 normal 相对稳定后启用，必要时降低 pair angle 或提高 mask 严格性，而不是直接增大 \(\lambda_{rc}\)。

## 6. Optional Material and Roughness Smoothness

Material/Roughness Smoothness Regularization 是一个辅助模块，而不是 RC loss 的核心理论贡献。当前实现中，当 `lambda_roughness_smoothness > 0` 且 iteration 达到 `roughness_smoothness_start` 后，对 `roughness_map` 施加图像空间 total variation：

\[
\mathcal{L}_{rough}=\operatorname{TV}(R).
\]

该项的作用是鼓励反射置信度或粗糙度图在局部上更平滑，并提供 `rough_only` 消融控制。仓库日志显示，roughness-only regularization 不能复现 RC 的 reflection-consistency 行为。因此，在论文叙事中应将其表述为材料正则和工程控制项，而不是跨视角反射一致性的主要来源。

## 7. Confidence-aware Geometry and Mesh Filtering

RC 模块组还可以为 mesh extraction 提供 confidence-aware filtering。当前实现中，mesh reconstruction 从 renderer 收集 `rend_alpha`、`surf_depth`、`rend_normal` 和 `surf_normal`，构造

\[
Q(u)=A(u)\max(0,N^r(u)\cdot N^d(u)).
\]

在 TSDF 融合前，若 `conf_threshold` 大于 0，则深度图中低于阈值的像素被置 0，从而减少低 alpha 或 normal 不一致区域进入体融合。这一模块与 RC loss 共享 alpha 和 normal agreement 的思想，但它是工程增强模块。除非有独立 Chamfer、F-score、normal MAE 或 mesh artifact 指标支持，不能把它写成 RC 必然改善几何质量的证据。

## 8. Reflection-specific Evaluation Protocol

为了避免把反射一致性收益误写为全局图像质量提升，评估协议应拆分为三类指标。第一类是 `mean_reflection_consistency`，即在 source-target view pairs 上重新渲染两视角并计算 \(\mathcal{L}_{rc}\) 型误差，数值越低表示跨视角 specular inconsistency 越小。第二类是 reflective-region metrics，在 alpha 和 roughness/confidence mask 内报告 PSNR、SSIM、LPIPS 或 `reflective_region_psnr`。第三类是 full-image metrics，在全图报告 PSNR、SSIM、LPIPS。

当前仓库的 evidence 支持这种拆分：FD-P2-lite / non-Shiny-Real 日志中，RC 在 `mean_reflection_consistency` 上 train 14/14、test 13/14 胜出；但 full-image 和 reflective-region 渲染质量指标存在 mixed/tradeoff。因而，论文应把 RC 的主要验证目标设为 reflection consistency，而把 image-quality tradeoff 作为结果和限制共同报告。

# Contributions

1. 提出 RC 模块组，一个脱离特定表示的 renderer-buffer-driven 反射一致性优化框架。该框架把可迁移边界定义在 renderer intermediate buffers 上，而不是绑定到 Ref-GS 的 Gaussian 参数、Sph-Mip 编码或 light MLP。
2. 设计 cross-view reflection consistency loss，通过 source depth 反投影、target 投影和可微采样，将不同视角下同一三维表面的 specular 分量联系起来。
3. 提出 confidence-weighted reflective correspondence，将 alpha、depth consistency、normal agreement 和 material/specular confidence 组合为权重，以降低遮挡、错误深度和非反射区域对 RC 约束的影响。
4. 给出 scheduled training integration、material/roughness smoothness control、confidence-aware mesh filtering 和 reflection-specific evaluation protocol，用于在可控成本和明确 claim boundary 下评估 RC 模块组。

# Evidence appendix

| 论文主张 | 支持状态 | 代码/文档证据 |
| --- | --- | --- |
| Renderer 可以暴露 specular、roughness/confidence、alpha、depth、normal 等中间缓冲。 | 代码支持 | `gaussian_renderer/__init__.py:84-88` 读取 roughness/feature；`gaussian_renderer/__init__.py:102-121` 解析 alpha、normal、depth 和 depth normal；`gaussian_renderer/__init__.py:202-215` 返回 `pbr_rgb`、`spec_light`、`roughness_map`、`rend_alpha`、`rend_normal`、`surf_depth`、`surf_normal`。 |
| RC loss 不需要直接访问 Gaussian 内部参数，而是消费 renderer buffers。 | 代码支持 | `utils/reflection_consistency.py:129-149` 只检查 render package 中的 `spec_light`、`rend_alpha`、`roughness_map`、`surf_depth`、`rend_normal`、`surf_normal` 等 key。 |
| RC 使用 source depth 反投影、target 投影和 grid sampling 建立跨视角对应。 | 代码支持 | `utils/reflection_consistency.py:60-88` 实现 backprojection；`utils/reflection_consistency.py:91-100` 实现 projection；`utils/reflection_consistency.py:103-110` 使用 `F.grid_sample`；`utils/reflection_consistency.py:155-160` 在 loss 中串联这些步骤。 |
| RC 使用 alpha、depth consistency、roughness/confidence 和 normal agreement 做 mask/weight。 | 代码支持 | `utils/reflection_consistency.py:166-185` 构造 normal agreement、depth check、spec confidence、mask 和 weighted loss。 |
| RC 在训练中按 schedule 启用，并需要额外 render pair view。 | 代码支持 | `train.py:140-151` 在 lambda、start、every 和 pair camera 条件满足时渲染 pair view 并加入 RC loss；`arguments/__init__.py:113-119` 定义默认调度参数。 |
| 基础训练仍包含原有 RGB 重建、alpha warmup 和 normal regularization。 | 代码支持 | `train.py:114-138` 包含 PBR RGB L1 + DSSIM、alpha BCE、normal regularization、roughness TV；`utils/loss_utils.py:17-18`、`utils/loss_utils.py:43-71`、`utils/loss_utils.py:81-85`、`utils/loss_utils.py:91-99` 给出对应 loss 实现。 |
| Roughness smoothness 是可选材料正则，不是 RC 核心贡献。 | 代码和文档支持 | `train.py:136-138` 仅在 `lambda_roughness_smoothness > 0` 且达到 start 后启用；`docs/rc_refgs_optimization_modules_reuse_guide.md:8` 明确不应与跨视角 RC loss 混为同一理论贡献；`docs/superpowers/logs/rc-refgs-fd-p2-lite-final-results-analysis-2026-06-01.md:163-166` 指出 `rough_only` 不复现 RC 行为。 |
| Confidence-aware mesh filtering 存在，但只能作为工程增强模块。 | 代码和文档支持 | `utils/mesh_utils.py:119-128` 构造 `conf = alpha * normal_agree`；`utils/mesh_utils.py:183-184` 用 `conf_threshold` mask depth；`docs/rc_refgs_optimization_modules_reuse_guide.md:9` 明确没有独立几何指标时不应宣称几何必然更优。 |
| 反射一致性评估和 reflective-region 渲染指标已有实现。 | 代码支持 | `metrics/reflection_consistency_eval.py:113-121` 计算 reflective-region PSNR；`metrics/reflection_consistency_eval.py:213-260` 动态或固定 pair 评估 `mean_reflection_consistency`；`metrics/render_quality_eval.py:77-81` 定义 reflective mask；`metrics/render_quality_eval.py:116-168` 输出 full 和 reflective PSNR/SSIM/LPIPS。 |
| Ablation runner 支持 base、rc、wo_ref、wo_conf、rough_only，并输出 reflection consistency metrics。 | 代码支持 | `scripts/run_rc_refgs_ablation_direct.py:20-22` 定义默认场景、variants 和 metric；`scripts/run_rc_refgs_ablation_direct.py:170-199` 设置 `wo_conf` 与 `rough_only`；`scripts/run_rc_refgs_ablation_direct.py:231-264` 调用 `metrics/reflection_consistency_eval.py`；`scripts/run_rc_refgs_ablation_direct.py:359-379` 定义 CLI 参数。 |
| RC 在已完成 FD-P2-lite / non-Shiny-Real 范围内主要改善 reflection consistency。 | 日志支持 | `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-results-analysis-2026-06-01.md:5-10` 给出 scope、70/70 coverage、14/14 train 和 13/14 test；`docs/superpowers/figures/fd-p2-lite/table2_rc_win_counts_by_metric.csv:2-3` 给出 win counts 和 mean delta。 |
| 渲染质量指标为 mixed/tradeoff，不能宣称全局质量全面优于 Ref-GS。 | 日志支持 | `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-results-analysis-2026-06-01.md:132-135` 明确 mixed 和不支持全局 superior claim；`docs/superpowers/figures/fd-p2-lite/table2_rc_win_counts_by_metric.csv:4-17` 给出各质量指标不同 win rate；`docs/superpowers/figures/fd-p2-lite/table4_tradeoff_summary.csv:1-29` 展示 per-scene/split tradeoff。 |
| Shiny Blender Real、完整 17-scene FD-P2、完整 51-cell ablation 和多 seed 结论不支持。 | 日志支持 | `docs/superpowers/logs/rc-refgs-current-main-and-ablation-analysis-2026-05-29.md:3-11` 记录 main 29/34、ablation 42/51、Shiny Real OOM 和 NO-GO；`docs/superpowers/logs/rc-refgs-fd-p2-lite-final-results-analysis-2026-06-01.md:17-19` 明确 not supported claims；`docs/superpowers/logs/rc-refgs-fd-p2-lite-final-results-analysis-2026-06-01.md:199-206` 列出限制。 |
| 可迁移到 3DGS、2DGS、GaussianShader、3DGS-DR、NeRF-like reflective reconstruction 是方法设计和接口推论，而非当前完整跨方法实验事实。 | 设计支持，实验未验证 | `README.md:58-61` 显示相关方法脉络；`docs/rc_refgs_optimization_modules_reuse_guide.md:5-11` 和 `docs/rc_refgs_optimization_modules_reuse_guide.md:56-73` 明确迁移应抽象为 `render(view) -> buffers`，但仓库日志没有完整跨方法实验结果。 |

# Claim boundary

## 有代码或日志支持的结论

- 本仓库实现了一个跨视角 reflection consistency loss，其输入是 renderer intermediate buffers，而不是直接访问 Gaussian 内部参数。
- 当前实现通过 source depth 反投影、target view 投影和 `grid_sample` 建立跨视角 specular correspondence。
- 当前实现使用 alpha、depth consistency、normal agreement、roughness/specular confidence 进行 confidence-weighted reflective correspondence。
- 当前训练路径以 off-by-default 方式集成 RC，并通过 start iteration、every interval、pair angle 和 lambda 控制启用时机与成本。
- 当前实现包含可选 roughness TV 正则和 confidence-aware TSDF depth filtering。
- 当前评估路径包含 reflection consistency、reflective-region quality 和 full-image quality 的拆分评估。
- 在 FD-P2-lite / non-Shiny-Real 范围内，RC 主要稳定改善 `mean_reflection_consistency`，并且图像质量指标存在 mixed/tradeoff。

## 仅属于方法设计或迁移假设的结论

- RC 模块组可迁移到 3DGS、2DGS、GaussianShader、3DGS-DR 和 NeRF-like reflective reconstruction，是由 buffer interface 推导出的可迁移设计主张。当前仓库没有提供这些外部方法上的完整实验验证。
- 对称 RC loss、frustum/depth overlap 更强的 pair selection、learned reflective confidence 和无 roughness renderer 的替代置信度，属于合理扩展，不是当前代码已完整验证的事实。
- Confidence-aware mesh filtering 可能改善 TSDF 融合输入质量，但当前证据不足以声称 RC 必然提升几何或 mesh quality。
- Roughness smoothness 可作为材料正则和消融控制，但不能写成 RC loss 的核心理论贡献。

## 不应写入论文主结论的说法

- 不应声称 RC-RefGS 或 RC 模块组全面优于 Ref-GS。
- 不应声称 PSNR、SSIM、LPIPS 必然提升。
- 不应声称几何质量、mesh quality 或材质分解质量必然提升。
- 不应声称已经完成所有 reflective datasets 的验证。
- 不应把 Shiny Blender Real incomplete/OOM 结果写成完整结论。
- 不应把 non-Shiny-Real FD-P2-lite 结果扩展为完整 17-scene FD-P2 或完整 51-cell ablation 结论。

# Skill usage summary

- 已检查当前 Codex 环境中的相关 skills。可用的 Nature/scientific-writing 相关 skills 包括 `nature-writing`、`nature-polishing`、`nature-reviewer`、`nature-citation`、`nature-academic-search`、`nature-data`、`nature-figure`、`nature-paper2ppt`、`nature-reader`、`nature-response`，本任务优先使用与论文 framing、Introduction/Method 写作、中文学术润色和 claim boundary 最直接相关的 skills。
- 使用了 `using-superpowers`：确认本轮必须先检查并应用相关 skills。
- 使用了 `nature-writing`：按 methods-paper 逻辑组织一篇方法论文的核心论点、Introduction funnel、Method module structure、title alternatives 和 claim-evidence map。
- 使用了 `nature-polishing`：按科研论文写作要求检查 Introduction 和 Method 的 gap、boundary、术语一致性与过度声明风险。
- 使用了 `brainstorming` 的 framing 原则：将用户给出的详细规格收敛为一个已明确的设计方向，即 “RC 模块组” 而非 “Ref-GS 实现细节”。由于用户已经指定输出文件、结构和主张边界，本轮未另行等待设计审批。
- 使用了 `writing-plans` 的多步骤文件责任划分思想：先做证据读取，再形成 claim map，最后写入单一 draft 文件。由于本任务是论文初稿生成而非代码实现，没有另建实现计划文件。
