# RC-RefGS P4 Launch Safety Audit

Date: 2026-05-22 17:19 CST
Window: codex P4 launch-safety-audit

## Scope

Audit whether the preflighted P4 base/RC `31000` matrix can be launched in this window.

No training was launched. No metric code, training code, or claim-facing prose was changed.

## Recovered Inputs

- Manifest: `docs/superpowers/logs/rc-refgs-p4-base-rc-i31000-manifest-2026-05-22.json`
- Dry-run summary: `docs/superpowers/logs/rc-refgs-p4-base-rc-i31000-dryrun-summary-2026-05-22.json`
- Output root: `/tmp/rc_refgs_p4_base_rc_i31000_20260522`
- Matrix: `teapot/toaster/car` x `base/rc`, seed `0`, iteration `31000`

## Checks

- Manifest JSON parse: pass.
- Dry-run summary JSON parse: pass.
- Dry-run summary: `job_count=6`, `missing_count=18`.
- Check-missing dry run: exit 2 with 18 missing expected artifacts, consistent with not-yet-run state.
- Existing P4 launcher/train process check: no matching `run_rc_refgs_ablation_direct.py` or `train.py -s /data/liuly/dataset/3DGS/refnerf/(teapot|toaster|car)` process.
- CUDA visibility probe: `torch.cuda.is_available=True`, `torch.cuda.device_count=7`.
- GPU state at audit time:
  - GPU 0: 7039 MiB, 85% utilization, occupied by `gaomeng+` process `3406310`.
  - GPU 1: 3 MiB, 0% utilization.
  - GPU 2: 14105 MiB, 100% utilization, occupied by `tantao` process `3252701`.
  - GPUs 3-6: 20591-21952 MiB, 94-95% utilization, occupied by `tantao` `ov9d_plus` processes.

## Decision

No launch in this window.

Rationale:
- The coordination-board policy requires explicitly allocated compute before launching the six-job P4 `31000` matrix.
- This window did not include an explicit GPU allocation.
- Most GPUs are occupied or active, and starting a long full-horizon matrix opportunistically would risk interfering with existing jobs.
- The audit confirms launch readiness remains a planning/preflight state only; it does not produce full-horizon evidence.

## Claim Boundary

- CONDITIONAL GO for launching later only with explicit compute allocation.
- NO-GO for full-horizon performance, manuscript/scientific, broad rendering, material, geometry, causal, external-superiority, ablation, or multi-seed claim upgrades.
