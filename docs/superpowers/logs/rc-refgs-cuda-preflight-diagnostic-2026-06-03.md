# RC-RefGS CUDA Preflight Diagnostic - 2026-06-03

## Executive Summary

Manual fresh-subprocess verification showed CUDA is available in the `ref_gs` environment when `CUDA_VISIBLE_DEVICES` is set before launching Python. The previous quality-preserving runner CUDA gate is therefore treated as a false negative in the runner preflight implementation, not as evidence that the environment lacks CUDA.

This window fixed CUDA preflight only. No training, metrics, 4-scene pilot, Shiny Blender Real run, metric-definition change, or quality-improvement claim was launched.

Decision: **GO** for CUDA preflight fix. Runtime/scientific claims remain **NO-GO** until new paired experiments actually complete.

## Manual Fresh-Subprocess Evidence

The user verified the following in the `ref_gs` environment with `CUDA_VISIBLE_DEVICES` set before launching each fresh Python subprocess:

| physical GPU | torch available | device count | device name |
| --- | --- | --- | --- |
| `0` | `true` | `1` | `NVIDIA RTX A5000` |
| `1` | `true` | `1` | `NVIDIA RTX A5000` |
| `2` | `true` | `1` | `NVIDIA RTX A5000` |
| `3` | `true` | `1` | `NVIDIA RTX A5000` |
| `5` | `true` | `1` | `NVIDIA GeForce RTX 3090 Ti` |
| `6` | `true` | `1` | `NVIDIA GeForce RTX 3090 Ti` |
| `7` | `true` | `1` | `NVIDIA GeForce RTX 3090 Ti` |

## Previous False Negative

The earlier four-scene `rc_qp_lam010` gate did not launch because the runner path reported CUDA unavailable for checked candidates. Given the manual fresh-subprocess result above, that gate is now interpreted as a runner preflight false negative.

The previous no-launch artifact remains preserved and is not relabeled as a completed experiment:

- `docs/superpowers/logs/rc-refgs-quality-preserving-lam010-4scene-pilot-2026-06-03.{md,json}`
- `docs/superpowers/logs/rc-refgs-quality-preserving-lam010-4scene-pilot-comparison-2026-06-03.csv`

## Fixed Design

The runner now checks CUDA visibility with one fresh subprocess per candidate physical GPU.

For candidate GPU `G`, the subprocess environment is:

```text
CUDA_VISIBLE_DEVICES=G
CONDA_PREFIX=/home/liuly/anaconda3/envs/ref_gs
LD_LIBRARY_PATH=/home/liuly/anaconda3/envs/ref_gs/lib:${LD_LIBRARY_PATH}
python=/home/liuly/anaconda3/envs/ref_gs/bin/python
```

The child subprocess imports `torch` only after that environment is already set. The parent runner does not import `torch` for preflight.

## Acceptance Policy

- Auto device selection accepts a candidate only if `nvidia-smi` says it is idle and the fresh torch CUDA subprocess preflight passes.
- Explicit device execution does not depend on `nvidia-smi`; if `nvidia-smi` is unreliable, an explicit physical GPU may proceed only if the fresh torch CUDA subprocess preflight passes.
- External mapping is `CUDA_VISIBLE_DEVICES=<physical_gpu>`.
- Train and metric commands use logical `--cuda_device 0`.
- Runner artifacts record `physical_gpu`, `cuda_visible_devices`, `cuda_device_arg`, `device_mapping`, and per-candidate `cuda_preflight_results`.

## Boundaries

- No training launched.
- No metrics launched.
- No 4-scene pilot launched.
- No Shiny Blender Real launched.
- No metric definitions changed.
- No quality improvement claimed.

## Validation

Required validation is recorded in the autonomous log and final closeout:

- `python -m unittest tests/test_quality_preserving_pilot_runner.py`
- `python -m py_compile scripts/run_rc_refgs_quality_preserving_pilot.py`
- `python -m json.tool docs/superpowers/logs/rc-refgs-quality-preserving-pilot-runner-2026-06-01.json`
- `python -m json.tool docs/superpowers/logs/rc-refgs-cuda-preflight-diagnostic-2026-06-03.json`
- `git diff --check`
