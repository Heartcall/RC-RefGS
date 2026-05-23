# RC-RefGS Extract-Mesh Runtime Readiness

Date: 2026-05-23 04:45:06 CST

This packet consolidates the existing extraction dry-run, Open3D preflight, runtime command-plan, and SMVP3D OBJ-reference dry-run evidence. It is a handoff artifact only: no training, extraction, mesh metric computation, or claim upgrade was performed.

## Source Artifacts

- `docs/superpowers/logs/rc-refgs-extract-mesh-teapot-base-dryrun-smoke-2026-05-22.json`
- `docs/superpowers/logs/rc-refgs-extract-mesh-open3d-preflight-2026-05-23.json`
- `docs/superpowers/logs/rc-refgs-extract-mesh-open3d-preflight-ldpath-2026-05-23.json`
- `docs/superpowers/logs/rc-refgs-extract-mesh-runtime-command-plan-2026-05-23.json`
- `docs/superpowers/logs/rc-refgs-smvp3d-obj-reference-dryrun-plan-2026-05-23.json`

## Runtime Target

- Model path: `/tmp/rc_refgs_i300_validation_base_rc_20260520/teapot_base`
- Iteration: `300`
- Split: `train`
- Mesh mode: `bounded`
- Point-cloud input: `/tmp/rc_refgs_i300_validation_base_rc_20260520/teapot_base/point_cloud/iteration_300/point_cloud.ply`
- Missing inputs: `[]`
- Planned output mesh: `/tmp/rc_refgs_i300_validation_base_rc_20260520/teapot_base/mesh_iter300_runtime_plan.ply`
- Planned mesh currently exists: `false`
- Planned runtime summary: `docs/superpowers/logs/rc-refgs-extract-mesh-runtime-command-plan-2026-05-23-runtime.json`

## Environment Boundary

- Plain Open3D import: `ok=false`, `error_type=ImportError`, contains `GLIBCXX_3.4.29`.
- Required runtime environment: `LD_LIBRARY_PATH=/home/liuly/anaconda3/envs/ref_gs/lib:$LD_LIBRARY_PATH`
- Open3D under required environment: `ok=true`, `version=0.17.0`

## Planned Command

```bash
export LD_LIBRARY_PATH="/home/liuly/anaconda3/envs/ref_gs/lib:$LD_LIBRARY_PATH"
/home/liuly/anaconda3/envs/ref_gs/bin/python extract_mesh.py --model_path /tmp/rc_refgs_i300_validation_base_rc_20260520/teapot_base --iteration 300 --output_mesh /tmp/rc_refgs_i300_validation_base_rc_20260520/teapot_base/mesh_iter300_runtime_plan.ply --mesh_mode bounded --split train --voxel_size 0.004 --sdf_trunc 0.02 --depth_trunc 3.0 --conf_threshold 0.0 --mesh_resolution 1024 --cluster_to_keep 1000 --summary_json docs/superpowers/logs/rc-refgs-extract-mesh-runtime-command-plan-2026-05-23-runtime.json --cuda_device 0
```

The planned argv intentionally omits `--dry_run`, `--check_open3d`, and `--emit_runtime_command`.

## Geometry Dependency

- SMVP3D scene count: `5`
- Reference OBJ count: `5`
- Missing predicted mesh count: `5`
- Metrics computed: `false`

## Decision Boundary

- GO: Use this packet as the command/env/gate handoff for one explicitly allocated non-dry-run extraction smoke.
- CONDITIONAL GO: Run extraction only in a deliberate runtime window with explicit GPU allocation and the required library-path environment applied.
- NO-GO: Do not compute Chamfer/F-score values until predicted meshes exist.
- NO-GO: Do not upgrade geometry, reconstruction, manuscript, scientific, or P4 claims from this packet.
