# RC-RefGS GT Geometry Evaluation Design

## Scope

Evaluate true geometry only for the completed FD-P2-lite non-Shiny-Real main
and ablation rows. Do not train, substitute unrelated outputs, or convert proxy
statistics into geometry evidence.

## Data Contract

- Main: 14 scenes x `base,rc` = 28 model rows.
- Ablation: 14 scenes x `base,rc,wo_ref,wo_conf,rough_only` = 70 model rows.
- Geometry is scene-level for one trained model, so exported `split` is
  `scene_geometry`; train/test image metrics are not duplicated or averaged.
- Glossy Synthetic uses `eval_pts.ply` as a GT point cloud.
- Shiny Blender Synthetic uses `<scene>_gt_mesh.ply` as a GT mesh.
- `points3d.ply` is not accepted as Glossy GT.

## Evaluation

Raw coordinates are primary. Meshes are sampled deterministically; point clouds
are deterministically subsampled without replacement. Bidirectional nearest
neighbors produce Chamfer-L1, Chamfer-L2, accuracy, completeness, and
precision/recall/F-score at 0.5%, 1%, and 2% of the GT bounding-box diagonal.
Normal metrics are emitted only when both sampled geometries have reliable
normals.

Coordinate mismatch is reported from center and scale diagnostics. Optional
similarity alignment is explicitly labeled diagnostic and never replaces the
raw primary result.

## Current Artifact Boundary

The historical completed output roots under `/tmp` are absent. Frozen CSV/JSON
summaries prove prior completion but do not contain prediction coordinates.
Unrelated `Ref-GS-I2` baseline meshes are not provenance-matched and are not
substituted. If no matching prediction is found, the row is excluded and all
paper-facing outputs state that true geometry remains unevaluated.

## Outputs And Validation

The evaluator writes the requested audit, CSVs, LaTeX tables, and Python/
matplotlib PDF+PNG figures. Tests cover metric definitions, deterministic
sampling, explicit alignment, and project-row mapping. Validation checks row
counts, finite values, aggregate membership, output existence, and metric
directions.
