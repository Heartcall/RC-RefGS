# RC-RefGS Quality-Preserving Pilot Runner - 2026-06-01

## Executive Summary

This window created and validated a standalone runner for bounded `rc_qp_*` quality-preserving RC pilot experiments:

- Runner: `scripts/run_rc_refgs_quality_preserving_pilot.py`
- Tests: `tests/test_quality_preserving_pilot_runner.py`
- Dry-run output root: `/tmp/rc_refgs_quality_preserving_rc_i31000_20260601`
- Smoke status: **attempted once** on GPU 0 after an idle probe; failed at train import with a `GLIBCXX_3.4.29` runtime-library mismatch before training startup completed.

No training, metric sweep, Shiny Blender Real run, full 16-job pilot execution, full `i31000` pilot execution, metric-definition change, or result relabeling was performed.

Decision: **CONDITIONAL GO**. The runner is ready for command construction and safe orchestration, but runtime smoke is not end-to-end validated because the single GPU0 smoke failed at train import.

## Runner Choice

Existing launchers are not sufficient for `rc_qp_*` variants without modification:

- `scripts/run_rc_refgs_ablation_direct.py` accepts only `base`, `rc`, `wo_ref`, `wo_conf`, and `rough_only`.
- `scripts/run_rc_refgs_full_dataset_all_experiments.sh` validates the same fixed variant set and routes runtime through the direct ablation launcher.
- `train.py` itself supports the required knobs: `--lambda_ref_consistency`, `--ref_consistency_start`, `--ref_consistency_every`, `--ref_consistency_max_angle`, `--ref_consistency_gamma`, `--lambda_dssim`, `--seed`, `--iterations`, `--test_iterations`, `--save_iterations`, `--quiet`, and `--cuda_device`.

Therefore this task created a minimal standalone CPU-side orchestration script instead of modifying the full-dataset runner.

## Selected Pilot Scenes

Scenes are read from `docs/superpowers/logs/rc-refgs-quality-regression-target-scenes-2026-06-01.csv`.

| dataset | scene | reason |
| --- | --- | --- |
| `glossy_synthetic` | `luyu` | worst combined test full and reflective quality regression among Glossy Synthetic scenes |
| `glossy_synthetic` | `teapot` | control scene where RC improves consistency and all six test quality metrics |
| `shiny_blender_synthetic` | `coffee` | test consistency exception |
| `shiny_blender_synthetic` | `helmet` | strongest consistency gain with quality regression signal |

Shiny Blender Real is excluded.

## Candidate Variants

| variant | lambda_ref_consistency | start | every | gamma | lambda_dssim |
| --- | --- | --- | --- | --- | --- |
| `rc_qp_lam005` | `0.005` | `3000` | `4` | `2.0` | `0.2` |
| `rc_qp_lam010` | `0.010` | `3000` | `4` | `2.0` | `0.2` |
| `rc_qp_lam015` | `0.015` | `3000` | `4` | `2.0` | `0.2` |
| `rc_qp_lam010_start5000_every8` | `0.010` | `5000` | `8` | `2.0` | `0.2` |

Optional variants are supported in the runner but not part of the required first pilot set: `rc_qp_lam010_gamma10`, `rc_qp_lam010_gamma15`, `rc_qp_lam010_dssim01`, and `rc_qp_lam010_dssim03`.

## Dry-Run Evidence

Dry-run command executed:

```bash
python scripts/run_rc_refgs_quality_preserving_pilot.py --output_root /tmp/rc_refgs_quality_preserving_rc_i31000_20260601 --devices 7 --max_jobs 16 --variants rc_qp_lam005 rc_qp_lam010 rc_qp_lam015 rc_qp_lam010_start5000_every8 --dry_run
```

Outputs written:

- `/tmp/rc_refgs_quality_preserving_rc_i31000_20260601/pilot_plan.json`
- `/tmp/rc_refgs_quality_preserving_rc_i31000_20260601/pilot_status.json`
- `/tmp/rc_refgs_quality_preserving_rc_i31000_20260601/pilot_status.md`
- Per-job dry-run `launcher_summary.json` files under `<output_root>/<dataset>/<scene>/<variant>/seed_0/`

Dry-run status:

- `job_count=16`
- `dry_run=16`
- `completed=0`
- `failed=0`
- `partial=0`
- `skipped_complete=0`

The dry run emits each train command, train/test reflection-consistency metric commands, and render-quality `split=both`, `mask_mode=both`, `image_key=pbr_rgb` commands. A recorded `image_key=render` fallback command is present but only to be used and reported if `pbr_rgb` fails.

## Smoke-Run Status

Smoke was attempted exactly once.

Latest runtime-smoke attempt, 2026-06-03 18:37:33 CST:

- Output root: `/tmp/rc_refgs_quality_preserving_rc_smoke_20260601`
- Dataset/scene: `shiny_blender_synthetic/helmet`
- Variant: `rc_qp_lam010`
- Smoke iterations: `1000`
- Max jobs: `1`
- Device: GPU 0
- Runner command executed: yes

```bash
python scripts/run_rc_refgs_quality_preserving_pilot.py --output_root /tmp/rc_refgs_quality_preserving_rc_smoke_20260601 --devices 0 --scenes helmet --variants rc_qp_lam010 --max_jobs 1 --smoke --smoke_iterations 1000 --execute --confirm_execute YES
```

Pre-smoke process probe was empty. GPU probe confirmed GPU 0 idle:

```text
0, 3 MiB, 0 %
1, 3 MiB, 0 %
2, 3 MiB, 0 %
3, 3 MiB, 0 %
4, 19636 MiB, 99 %
5, 4632 MiB, 99 %
6, 7912 MiB, 98 %
7, 4632 MiB, 6 %
```

Generated smoke status artifacts:

- `/tmp/rc_refgs_quality_preserving_rc_smoke_20260601/pilot_plan.json`
- `/tmp/rc_refgs_quality_preserving_rc_smoke_20260601/pilot_status.json`
- `/tmp/rc_refgs_quality_preserving_rc_smoke_20260601/shiny_blender_synthetic/helmet/rc_qp_lam010/seed_0/launcher_summary.json`

`pilot_status.json` reports:

- `job_count=1`
- `failed=1`
- `failed_step=train`
- `dry_run=false`
- `smoke=true`
- `iterations=1000`

`launcher_summary.json` reports:

- `status=failed`
- `return_codes.train=1`
- `render_fallback_used=false`
- metric commands were generated but not executed

Failure:

```text
ImportError: /lib/x86_64-linux-gnu/libstdc++.so.6: version `GLIBCXX_3.4.29' not found (required by /home/liuly/anaconda3/lib/python3.12/site-packages/PIL/../../.././libLerc.so.4)
```

Validation status for this smoke:

- Train startup: failed during Python import before startup completed.
- Save artifact: not produced.
- Reflection metrics: not run.
- Render-quality metric: not run.
- Quality claim: none.

This is an engineering validation failure, not a scientific result, and it does not support any LPIPS/PSNR/SSIM or quality-preserving RC claim.

Latest runtime-smoke request, 2026-06-03 18:29:06 CST:

- Requested output root: `/tmp/rc_refgs_quality_preserving_rc_smoke_20260601`
- Requested variant: `rc_qp_lam010`
- Requested smoke iterations: `1000`
- Requested max jobs: `1`
- Target device policy: prefer GPU 7 only if verified idle
- Runner command executed: no
- `pilot_status.json` check: not applicable because the runner was not invoked
- per-job `launcher_summary.json` check: not applicable because the runner was not invoked
- Train startup, save artifact, reflection metric, and render-quality metric status: not attempted

Latest prohibited-process probe:

```bash
ps -eo pid,pgid,ppid,stat,etime,cmd | grep -E "train.py|render_quality_eval|reflection_consistency_eval|quality_preserving|run_rc_refgs" | grep -v grep || true
```

Result: empty.

Latest GPU probe:

```bash
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
```

Result:

```text
0, 3 MiB, 0 %
1, 3 MiB, 0 %
2, 3 MiB, 0 %
3, 3 MiB, 0 %
4, 19636 MiB, 100 %
5, 4632 MiB, 98 %
6, 8144 MiB, 98 %
7, 4632 MiB, 99 %
```

Because GPU 7 was busy, the smoke cell was skipped before invoking the runner. This is an engineering safety outcome, not a scientific result, and it does not support any LPIPS/PSNR/SSIM or quality-preserving RC claim.

Initial 2026-06-03 runner-preparation window:

Required pre-smoke process probe:

```bash
ps -eo pid,pgid,ppid,stat,etime,cmd | grep -E "train.py|render_quality_eval|reflection_consistency_eval|run_rc_refgs|quality_preserving" | grep -v grep || true
```

Result: empty.

GPU probe:

```bash
nvidia-smi
```

Result: exit code `9`, with `NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.`

Because GPU 5/6/7 idleness could not be verified, the smoke cell was skipped. This is not a scientific result and does not support any LPIPS/PSNR/SSIM claim.

## Future Full-Pilot Command

This command is documented for a later explicitly approved run. It was **not executed** in this task:

```bash
python scripts/run_rc_refgs_quality_preserving_pilot.py --output_root /tmp/rc_refgs_quality_preserving_rc_i31000_20260601 --devices 7 --max_jobs 16 --variants rc_qp_lam005 rc_qp_lam010 rc_qp_lam015 rc_qp_lam010_start5000_every8 --execute --confirm_execute YES
```

For a one-cell smoke later, use the separate smoke root and keep `--max_jobs 1`:

```bash
python scripts/run_rc_refgs_quality_preserving_pilot.py --output_root /tmp/rc_refgs_quality_preserving_rc_smoke_20260601 --devices 7 --scenes helmet --variants rc_qp_lam010 --max_jobs 1 --smoke --execute --confirm_execute YES
```

## Safety Boundaries

- No Shiny Blender Real.
- No full pilot execution in this task.
- No full `31000` iteration pilot execution in this task.
- No multi-seed.
- No overwrite/delete/move/relabel of existing base/RC/ablation outputs.
- No metric-definition changes.
- No changes to headline masks, splits, image_key, or LPIPS settings.
- No quality-preserving RC claim until new paired experiments prove it.

## Acceptance Criteria For Later Result Upgrade

Per target scene:

- Retain lower test `mean_reflection_consistency` than base.
- Improve or match base on test `full_lpips`, `full_psnr`, and `full_ssim` where possible.
- Improve or match base on `reflective_lpips`, `reflective_psnr`, and `reflective_ssim` where possible.

Across scoped scenes:

- At least `12/14` test reflection-consistency wins versus base.
- At least `12/14` test full-LPIPS wins versus base.
- At least `12/14` test full-PSNR or full-SSIM wins versus base.

If these targets are infeasible, report the Pareto tradeoff rather than forcing a quality-preserving claim.

## Validation

Completed before closeout:

- RED: `python -m unittest tests/test_quality_preserving_pilot_runner.py` failed before the runner existed.
- GREEN: `python -m unittest tests/test_quality_preserving_pilot_runner.py` passed.
- `python -m py_compile scripts/run_rc_refgs_quality_preserving_pilot.py` passed.
- `python -m json.tool /tmp/rc_refgs_quality_preserving_rc_i31000_20260601/pilot_status.json` passed.
- `python -m json.tool /tmp/rc_refgs_quality_preserving_rc_i31000_20260601/pilot_plan.json` passed.

Follow-up hardening on 2026-06-03 added explicit artifact-state coverage:

- A dry-run `launcher_summary.json` no longer makes a job eligible for `skipped_complete`.
- Only launcher summaries with status `completed` or `skipped_complete`, plus all required artifacts, satisfy the skip-complete predicate.
- Smoke-mode command construction is covered for `--smoke_iterations` output filenames and train iterations.

Final validation is recorded in `docs/superpowers/logs/rc-refgs-autonomous-log.md`.
