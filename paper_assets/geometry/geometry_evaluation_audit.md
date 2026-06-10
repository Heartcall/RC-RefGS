# Geometry Evaluation Audit

## Summary

- Main completed model rows inspected: 28; final point clouds found: 28.
- Ablation completed model rows inspected: 70; final point clouds found: 70.
- True Chamfer/F-score/depth/normal metrics are not computable from current artifacts.
- Generated metrics are Level 3 proxy diagnostics from existing final point-cloud PLY files only.

## Answers

1. Main checkpoints: no `chkpnt*.pth` files were found for the completed FD-P2-lite rows; final Gaussian point clouds are available.
2. Ablation checkpoints: no `chkpnt*.pth` files were found for the completed non-Shiny-Real ablation rows; final Gaussian point clouds are available.
3. Existing mesh files: none were found for completed rows.
4. Runs requiring mesh extraction: all completed rows would require mesh extraction before mesh metrics or montage.
5. GT mesh / GT point cloud: none accepted for the 14 non-Shiny-Real scenes.
6. GT normal / depth: Shiny Blender Synthetic exposes GT normal PNGs, but saved rendered normals are absent and coordinate space is not verified; GT depth is absent.
7. No GT geometry: all Glossy Synthetic converted scenes have no GT mesh, GT point cloud, GT depth, or GT normals in the current inventory.
8. Mesh extraction method: `extract_mesh.py` uses `GaussianExtractor` with TSDF fusion from rendered depth/alpha/normal buffers; it is evaluation/extraction, not training.
9. Geometry evaluation scripts: guarded proxy evaluators exist under `metrics/geometry_quality_eval.py` and `metrics/smvp3d_geometry_eval.py`; this package adds paper-asset tables/figures.
10. Proxy metrics: vertex count, bounding-box diagonal, and vertex-count delta from input can be computed; they are diagnostics, not mesh quality.
11. Claim support: current outputs do not support a mesh quality improvement claim.

## Missing True Metrics

- `chamfer_l1` (level1_gt_mesh): missing accepted GT mesh/point cloud and missing extracted predicted meshes
- `chamfer_l2` (level1_gt_mesh): missing accepted GT mesh/point cloud and missing extracted predicted meshes
- `fscore_0p5pct` (level1_gt_mesh): missing accepted GT mesh/point cloud and missing extracted predicted meshes
- `fscore_1pct` (level1_gt_mesh): missing accepted GT mesh/point cloud and missing extracted predicted meshes
- `fscore_2pct` (level1_gt_mesh): missing accepted GT mesh/point cloud and missing extracted predicted meshes
- `precision_1pct` (level1_gt_mesh): missing accepted GT mesh/point cloud and missing extracted predicted meshes
- `recall_1pct` (level1_gt_mesh): missing accepted GT mesh/point cloud and missing extracted predicted meshes
- `normal_mae` (level2_gt_normal): missing saved rendered normal buffers; Glossy has no GT normal; Shiny normal coordinate-space not verified
- `normal_cosine` (level2_gt_normal): missing saved rendered normal buffers; Glossy has no GT normal; Shiny normal coordinate-space not verified
- `depth_mae` (level2_gt_depth): missing GT depth and saved rendered depth buffers
- `depth_rmse` (level2_gt_depth): missing GT depth and saved rendered depth buffers
- `depth_absrel` (level2_gt_depth): missing GT depth and saved rendered depth buffers

## Claim Boundary

Safe: current artifacts support only geometry proxy diagnostics from final point-cloud PLY files.

Unsafe: RC improves Chamfer, F-score, depth error, normal error, or mesh quality.
