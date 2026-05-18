# RC-RefGS Geometry Metric Feasibility

Date: 2026-05-18 04:06:03 CST

## Current RefNeRF i300 Outputs

The existing `teapot`, `toaster`, and `car` i300 baseline/RC outputs contain:

- `input.ply`
- `point_cloud/iteration_300/point_cloud.ply`

They do not contain extracted mesh artifacts. The RefNeRF dataset directories contain `points3d.ply`, but the Blender reader in `scene/dataset_readers.py` generates random points inside `[-1, 1]` and writes `points3d.ply`. These files are initialization point clouds, not ground-truth geometry. Chamfer/F-score against these point clouds would be misleading.

Decision for current RefNeRF i300 geometry metrics: **NO-GO**.

## SMVP3D Reference Inventory

SMVP3D has usable reference geometry in principle:

| Scene | Images | Normals | OBJ vertices | OBJ faces | Camera file |
| --- | ---: | ---: | ---: | ---: | --- |
| david | 48 | 48 | 49996 | 100000 | `cameras.npz` |
| dragon | 48 | 48 | 437645 | 871414 | `cameras.npz` |
| hedgehog | 48 | 48 | 10005 | 20006 | `cameras.npz` |
| snail | 48 | 48 | 10007 | 20010 | `cameras.npz` |
| squirrel | 48 | 48 | 25002 | 50000 | `cameras.npz` |

Current repo support is incomplete: `Scene` recognizes COLMAP `sparse/` or Blender `transforms_train.json`, while SMVP3D has `cameras.npz` plus `image/`, `normal/`, `s0/`, `s1/`, and `s2/`.

Decision for SMVP3D geometry metrics: **CONDITIONAL GO** after adding a dataset adapter or transform conversion.

## Runtime Blockers

- Plain `open3d` import in `ref_gs` fails with `GLIBCXX_3.4.29` missing through the PIL/libLerc path.
- `open3d` imports when `LD_LIBRARY_PATH=$CONDA_PREFIX/lib` is exported first.
- `trimesh` is not installed in `ref_gs`.
- Importing `utils.mesh_utils` fails because `utils.render_utils` is missing.
- No `extract_mesh.py` entrypoint is present in this repo root.

## Recommended Order

1. Fix or replace the mesh utility runtime path: missing `utils.render_utils`, missing `trimesh`, and Open3D library path.
2. Add or restore a mesh extraction entrypoint and smoke-test it on one existing i300 output.
3. Add SMVP3D loader support or a deterministic `cameras.npz` to Ref-GS transforms conversion.
4. Only then implement Chamfer/F-score against SMVP3D OBJ references.

## Decision

**NO-GO** for geometry-quality claims and for immediate RefNeRF Chamfer/F-score on current i300 artifacts.

**CONDITIONAL GO** for a future codex task that first fixes geometry prerequisites.

**SWITCH MODEL** remains recommended for conservative claim framing with the already complete i300 reflection, PSNR/SSIM, and normal diagnostic evidence.
