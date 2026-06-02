# RC-RefGS FD-P2 Full-Dataset Runtime Recovery (2026-05-27)

- Task claim: Complete FD-P2 remaining full-dataset base/RC i31000 jobs with safe single-GPU recovery.
- Runner mode: single-device GPU0 only (`--devices 0 --rerun_failed`).
- Active runner at launch time: none.
- Active runner after recovery run: none.

## Formal Output Completion Inventory (formal paths only)

- Complete jobs: 0/34
- Incomplete jobs: 34/34
- Jobs with point_cloud but missing metrics: 0
- Jobs with no point_cloud: 34
- Currently running job: none

## Recovery Run Result

- Command executed: `scripts/run_rc_refgs_full_dataset_all_experiments.sh ... --devices 0 --execute --confirm_full_dataset_execute YES --rerun_failed`
- Exit behavior: wrapper completed; all 34 jobs remained failed in status artifacts.
- Dominant failure signature:
  - `ImportError: /lib/x86_64-linux-gnu/libstdc++.so.6: version `GLIBCXX_3.4.29` not found ...`
- Failure location: training bootstrap (`train.py` import chain via `PIL/Image.py`).

## Status Artifact Snapshot

- `planned_count`: 0
- `completed_count`: 0
- `skipped_count`: 0
- `failed_count`: 34
- `missing_artifact_count`: 136

## Decision

- NO-GO for FD-P2 completion in current runtime environment.
- NO-GO for claim upgrades: 34/34 jobs are incomplete and formal required artifacts are missing.
