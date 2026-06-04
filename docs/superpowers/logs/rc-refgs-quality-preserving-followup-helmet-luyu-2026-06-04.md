# RC-RefGS Quality-Preserving Stage 1 Follow-Up: Helmet/Luyu

Generated: 2026-06-04T12:33:16+08:00

## Executive Summary

Decision: **CONDITIONAL GO**.

Claimed exactly one task: "Add a guarded manual-CUDA-preflight trust mode and rerun the Stage 1 follow-up only if manual CUDA check passes."

The guarded manual-CUDA-preflight trust mode was implemented and validated in the runner/tests, but the required same-shell manual CUDA gate failed before rerun:

```json
{
  "CUDA_VISIBLE_DEVICES": "0",
  "torch_cuda_available": false,
  "torch_device_count": 0,
  "device_name": null
}
```

Because `torch_cuda_available=false` and `torch_device_count=0`, the Stage 1 follow-up was **not rerun** in this task. No `train.py` command was launched, no metric command was launched, and no scientific conclusion exists for `rc_qp_lam005` or `rc_qp_lam010_start5000_every8`.

## Runner Feature Status

- Added guarded CLI mode: `--trust_manual_cuda_preflight YES`.
- Trust mode is restricted to explicit `--devices`, parent `CUDA_VISIBLE_DEVICES`, matching device value, and `--execute --confirm_execute YES`.
- Trust mode is rejected for `--devices auto`, missing/mismatched `CUDA_VISIBLE_DEVICES`, and dry-run/non-execute contexts.
- When used by the runner after a passing manual check, the intended mapping is external `CUDA_VISIBLE_DEVICES=<device>` with train/metrics `--cuda_device 0`.
- Default behavior remains unchanged when the flag is absent.

## Validation Before Rerun

| Check | Result |
| --- | --- |
| `python -m unittest tests/test_quality_preserving_pilot_runner.py` | PASS: Ran 32 tests OK |
| `python -m py_compile scripts/run_rc_refgs_quality_preserving_pilot.py` | PASS |
| `git diff --check` | PASS |
| manual CUDA check with `CUDA_VISIBLE_DEVICES=0` | FAIL: torch reports no CUDA devices |

## Completion Status

| Item | Status |
| --- | --- |
| Stage 1 rerun launched in this task | no |
| Jobs launched in this task | 0 |
| Train launched in this task | no |
| Metrics launched in this task | no |
| Previous output root status | 4 recorded jobs, all failed at `cuda_preflight` before train/metrics |
| Shiny Blender Real | not run |
| Full 16-job pilot | not run |
| 14-scene validation | not run |

## Fixed-Metric Comparison Context

Comparison CSV: `docs/superpowers/logs/rc-refgs-quality-preserving-followup-helmet-luyu-comparison-2026-06-04.csv`

The CSV preserves prior `base`, current `rc`, and completed `rc_qp_lam010` comparison rows for the same scenes where available. The two Stage 1 follow-up variants are marked `not_run_manual_cuda_preflight_failed` with blank metric fields because no new train or metric artifacts were produced.

## Variant Assessment

No new Pareto decision is possible. Neither `rc_qp_lam005` nor `rc_qp_lam010_start5000_every8` is more promising based on this task, because both remain untested at runtime. Do not expand either variant to four scenes until this exact Stage 1 matrix completes and is compared against `base`, current `rc`, and `rc_qp_lam010`.

## Claim Boundary

This is an engineering/runtime gate result only. It is not a scientific result and does not support any global quality-preserving claim, LPIPS/PSNR/SSIM improvement claim, or Shiny Blender Real/full-pilot claim.

## Next Safe Action

Fix CUDA visibility for `/home/liuly/anaconda3/envs/ref_gs/bin/python` in the active shell/runtime context, then rerun exactly the same four Stage 1 cells with `--trust_manual_cuda_preflight YES` only after the manual CUDA check passes.
