# Geometry Evaluation Results

## 1. Evaluation Scope

本次补测只使用已有 completed runs，不启动训练，不重新跑大规模实验。主实验覆盖 FD-P2-lite / non-Shiny-Real 的 Base 与 RC 共 28 个模型；消融覆盖 base/rc/wo_ref/wo_conf/rough_only 在同一 14 个 scene 上的 70 个模型层级条目，其中本次从消融根读取 wo_ref、wo_conf、rough_only 的 42 个完成模型，并复用主实验中的 base/rc proxy 作为对照。当前没有 accepted GT mesh 或 GT point cloud，也没有已抽取 predicted mesh，因此 Level 1 mesh metrics 不可计算。

## 2. Main Experiment Geometry Results

主实验可读取 final Gaussian point-cloud PLY，并计算 vertex count、bbox diagonal 和相对 input point cloud 的 vertex-count delta。这些是 artifact proxy diagnostics，不是 Chamfer/F-score、surface accuracy 或 mesh completeness。由于缺少 GT geometry 与 predicted mesh，不能判断 RC 是否改善真实 mesh quality。

## 3. Ablation Geometry Results

消融实验同样只能报告 point-cloud artifact proxies。wo_ref、wo_conf 和 rough_only 的 proxy 差异可用于发现模型规模或空间范围变化，但不能解释为几何质量优劣。不同 variant 的平均 proxy 值已写入 ablation_geometry_metrics_avg.csv 与 LaTeX 表。

## 4. Consistency vs Geometry

以 test split 的 reflection consistency improvement 对齐主实验 proxy delta 后，vertex-count proxy 的 Pearson r 为 `-0.20218086926937517`，bbox-diagonal proxy 的 Pearson r 为 `0.1460581568569638`。由于 y 轴是 proxy 而非真实 mesh error，该相关性只能说明 artifact-level 变化与 consistency 的关系，不能说明 surface quality 是否改善。

## 5. Mesh Quality Diagnosis

当前证据不支持“RC 改善 mesh quality”。更准确的结论是：RC 的 reflection consistency 改善尚未通过当前 artifact package 转化为可验证的 surface / mesh quality improvement。若论文目标包含几何质量，必须补充 mesh extraction、GT geometry 或 accepted evaluation point cloud，并计算 Chamfer/F-score/normal/depth 等真实指标。

## 6. Limitations

- 没有 accepted GT mesh / GT point cloud。
- 没有已抽取 predicted mesh。
- 没有 saved rendered depth / normal buffers。
- Shiny Blender Synthetic 虽有 GT normal PNG，但当前缺少 rendered normal，且 normal coordinate space 未验证。
- Proxy metrics 不能替代 mesh quality metrics。

## 7. Claim Boundary

Safe statement: 当前实验表明，RC 的 reflection consistency 改善尚未稳定转化为可验证的 mesh quality 提升；现有几何补测只支持 point-cloud proxy diagnostics，RC 更适合作为内部一致性正则或诊断信号，并需要进一步 geometry-aware / mesh-aware 评估。

Unsafe statement: RC 必然提升 mesh quality、Chamfer、F-score、normal error 或 depth error。
