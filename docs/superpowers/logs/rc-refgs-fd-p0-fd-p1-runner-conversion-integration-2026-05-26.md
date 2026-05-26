# RC-RefGS FD-P0/FD-P1 Runner + Conversion Integration

Date: 2026-05-26  
Window: `fd-p0-fd-p1-runner-conversion-integration-window`

## Claimed Task

Verify and integrate:
- full-dataset runner `--dataset_root` inference path; and
- Glossy Synthetic conversion-prep helper `scripts/prepare_glossy_synthetic_converted.sh`

Scope is docs/testing/planning only:
- no training launch
- no metric run
- no dataset conversion execution
- no manuscript/scientific claim upgrade

## Changes in This Window

- Added tests for conversion-prep helper:
  - `tests/test_prepare_glossy_synthetic_converted_static.py`
- Extended runner tests for `--dataset_root` inferred converted layout:
  - `tests/test_rc_refgs_full_dataset_runner_static.py`
- Fixed conversion-prep helper dry-run behavior:
  - `scripts/prepare_glossy_synthetic_converted.sh`
  - `--dry_run` now defers converted-output file validation and records plan output instead of failing.

## Verification

- RED->GREEN on conversion-prep dry-run regression:
  - RED: `python -m unittest tests.test_prepare_glossy_synthetic_converted_static` failed before fix (`missing transforms` in dry-run).
  - GREEN: same command passes (`Ran 3 tests`, `OK`).
- Runner static suite:
  - `python -m unittest tests.test_rc_refgs_full_dataset_runner_static` -> `Ran 8 tests`, `OK`.
- Script syntax:
  - `bash -n scripts/prepare_glossy_synthetic_converted.sh` -> pass.
  - `bash -n scripts/run_rc_refgs_full_dataset_all_experiments.sh` -> pass.
- Mock dry-run smoke checks:
  - conversion-prep dry-run now exits `0` with `converted_ok=1`, `converted_fail=0`.
  - runner `--dataset_root` dry-run exits `0` and writes `full_dataset_run_status.{json,md}`.

## Decision

**CONDITIONAL GO**

- GO scope:
  - FD-P1 dry-run orchestration is stable with dataset-root inference.
  - FD-P0 conversion-prep planning is regression-covered and no longer fails in dry-run.
- NO-GO scope:
  - claim-bearing full-dataset runtime before validated Glossy Synthetic conversion outputs;
  - complete-dataset claims;
  - manuscript/scientific claim upgrades;
  - broad rendering/material/geometry/external-superiority/causal/full-ablation/multi-seed claims.
- Next safe task:
  - bounded real Glossy Synthetic conversion execution with explicit operator confirmation, then manifest-gate refresh.
