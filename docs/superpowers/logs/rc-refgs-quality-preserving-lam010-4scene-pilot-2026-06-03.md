# RC-RefGS Quality-Preserving lam010 Four-Scene Pilot - 2026-06-03

## Executive Summary

Task claim: **Run the first quality-preserving RC scientific pilot: 4 target scenes with `rc_qp_lam010` at 31000 iterations.**

Decision: **CONDITIONAL GO** for the pilot gate only. The scientific pilot was **not launched** because no GPU was safely visible to the required `/home/liuly/anaconda3/envs/ref_gs/bin/python` PyTorch runtime at preflight time.

No scientific result was produced. No LPIPS/PSNR/SSIM improvement is claimed. No global quality-preserving RC claim is made.

## Scope

- Variant: `rc_qp_lam010`
- Iterations: `31000`
- Seed: `0`
- Target scene count: `4`
- Max jobs: `4`
- Output root: `/tmp/rc_refgs_quality_preserving_rc_lam010_4scene_i31000_20260603`
- Target CSV: `docs/superpowers/logs/rc-refgs-quality-regression-target-scenes-2026-06-01.csv`

Explicit exclusions:

- No Shiny Blender Real.
- No full `16`-job pilot.
- No other `rc_qp_*` variants.
- No metric-definition changes.
- No changes to existing FD-P2-lite base/RC/ablation results.
- No quality-improvement claim before paired comparison.

## Selected Scenes

The target CSV has `16` rows because each of the four selected scenes is repeated across variants. With `--variants rc_qp_lam010`, the runner plans exactly four jobs.

| dataset | scene | role | source path |
| --- | --- | --- | --- |
| `shiny_blender_synthetic` | `helmet` | strongest consistency gain with quality regression signal | `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/helmet` |
| `shiny_blender_synthetic` | `coffee` | coffee test consistency exception | `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/coffee` |
| `glossy_synthetic` | `luyu` | worst combined test full and reflective quality regression among Glossy Synthetic scenes | `/data/liuly/dataset/3DGS/GlossySynthetic/luyu` |
| `glossy_synthetic` | `teapot` | control scene where RC improves consistency and all six test quality metrics | `/data/liuly/dataset/3DGS/GlossySynthetic/teapot` |

Planned jobs:

- `glossy_synthetic/luyu/rc_qp_lam010/seed_0`
- `glossy_synthetic/teapot/rc_qp_lam010/seed_0`
- `shiny_blender_synthetic/coffee/rc_qp_lam010/seed_0`
- `shiny_blender_synthetic/helmet/rc_qp_lam010/seed_0`

## Smoke Baseline

The engineering smoke was checked before this pilot gate:

- Smoke root: `/tmp/rc_refgs_quality_preserving_rc_smoke_20260601_cuda0_explicit`
- Smoke job: `shiny_blender_synthetic/helmet/rc_qp_lam010/seed_0`
- `point_cloud/iteration_1000/point_cloud.ply`: present
- `reflection_consistency_train.json`: present
- `reflection_consistency_test.json`: present
- `render_quality_both_iter1000.json`: present
- `launcher_summary.json`: present

The smoke remains engineering validation only.

## Safety Gate

Pre-launch prohibited-process scan for `train.py`, `render_quality_eval`, `reflection_consistency_eval`, `quality_preserving`, and `run_rc_refgs` returned empty.

Shell-level `nvidia-smi` was available and reported:

```text
0, 3 MiB, 0 %
1, 3 MiB, 0 %
2, 3 MiB, 0 %
3, 3 MiB, 0 %
4, 19636 MiB, 100 %
5, 4632 MiB, 0 %
6, 7834 MiB, 99 %
7, 4632 MiB, 99 %
```

However, the required `ref_gs` runtime could not see CUDA:

```text
CUDA_VISIBLE_DEVICES unset -> torch.cuda.is_available() False, device_count 0
CUDA_VISIBLE_DEVICES=0 -> False, 0
CUDA_VISIBLE_DEVICES=1 -> False, 0
CUDA_VISIBLE_DEVICES=2 -> False, 0
CUDA_VISIBLE_DEVICES=3 -> False, 0
CUDA_VISIBLE_DEVICES=5 -> False, 0
```

Because no candidate GPU was safely visible to `/home/liuly/anaconda3/envs/ref_gs/bin/python`, the 31000-iteration pilot command was **not executed**.

## Run Outcome

- Runner command executed: no
- `pilot_status.json`: not created
- Completed jobs: `0`
- Failed jobs: `0`
- Partial jobs: `0`
- Not-started jobs: `4`
- Full `16`-job pilot started: no
- Shiny Blender Real started: no

Required artifacts per completed job would be:

- `point_cloud/iteration_31000/point_cloud.ply`
- `reflection_consistency_train.json`
- `reflection_consistency_test.json`
- `render_quality_both_iter31000.json`
- `launcher_summary.json`

No completed `rc_qp_lam010` `i31000` jobs exist in this pilot root, so no completed-job artifact verification or paired metric comparison is possible.

## Paired Comparison Status

Comparison CSV:

- `docs/superpowers/logs/rc-refgs-quality-preserving-lam010-4scene-pilot-comparison-2026-06-03.csv`

Status:

- Base vs RC vs `rc_qp_lam010`: not comparable.
- Reason: no `rc_qp_lam010` `i31000` artifacts were produced for the four selected scenes.
- Quality-improvement claim: not made.
- Reflection-preservation claim: not made.

## Recommendation

Do **not** expand to the full 16-job pilot yet.

Next step: resolve CUDA visibility for `/home/liuly/anaconda3/envs/ref_gs/bin/python`, then rerun this same four-scene `rc_qp_lam010` pilot gate before considering any full-pilot expansion.
