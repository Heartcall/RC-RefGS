# RC-RefGS FD Ablation Runtime Issue Report (2026-05-29)

## Task
- Claimed task: **“Fix metric RGB/RGBA handling and add safe Shiny Real ablation recovery policy.”**

## Metric Bug (Fixed)
- File patched: `metrics/reflection_consistency_eval.py`
- Root cause: `reflective_region_psnr` assumed RGBA and used `gt[3:, ...]`.
- Symptom in Shiny Blender Real RGB images:
  - `RuntimeError: The size of tensor a (3) must match the size of tensor b (0)`
  - evidence: `/tmp/rc_refgs_full_dataset_ablations_i31000_20260528/logs/full_dataset_ablations_i31000_gpu5_7.log` lines `857-859`

### Applied behavior
- `channels >= 4`: alpha composite with `alpha = gt_image[3:4, ...]`
- `channels == 3`: RGB passthrough
- `channels < 3`: raise `ValueError` with shape

## Regression Coverage
- Updated `tests/test_reflection_consistency_eval_static.py` with:
  - static guard against unsafe `gt[3:, ...]` compositing
  - RGB passthrough behavior test
  - RGBA alpha-composite behavior test
  - invalid-channel `ValueError` test

## Required Verification
- `conda run -n ref_gs python -m unittest discover tests` -> pass (`77` tests)
- `bash -n scripts/run_rc_refgs_full_dataset_all_experiments.sh` -> pass
- `bash -n scripts/run_rc_refgs_ablation.sh` -> pass
- `git diff --check` -> pass

## Metrics-Only Recovery (Executed)
- Command mode: `--skip_train --rerun_failed`
- Output root: `/tmp/rc_refgs_full_dataset_ablations_i31000_20260528`
- Log: `/tmp/rc_refgs_full_dataset_ablations_i31000_20260528/logs/full_dataset_ablations_i31000_metrics_recovery_gpu0_postpatch.log`

## Formal Inventory After Recovery (Ablation variants only)
- Scope: `17 scenes × {wo_ref, wo_conf, rough_only} × seed 0 = 51 jobs`
- Complete: `18`
- Point-cloud exists but metrics missing: `0`
- Train-needed: `33`
- Preserved completed synthetic ablations: `18/18` (`shiny_blender_synthetic`)

## Remaining Shiny Real Runtime Failures
- Train-needed (all 9 cells):
  - `gardenspheres/{wo_ref,wo_conf,rough_only}`
  - `sedan/{wo_ref,wo_conf,rough_only}`
  - `toycar/{wo_ref,wo_conf,rough_only}`

### OOM/NaN evidence
- `Loss=nan` progression and point-growth to multi-million scale observed.
- OOM evidence:
  - `RuntimeError: CUDA out of memory. Tried to allocate 1.84 GiB`
  - evidence: `/tmp/rc_refgs_full_dataset_ablations_i31000_20260528/logs/full_dataset_ablations_i31000_gpu5_7.log` lines `907-918`

## Safe Bounded Recovery Policy (Do Not Launch Yet)
1. Run only failed Shiny Real ablation cells (9 jobs), no full-matrix relaunch.
2. Use direct per-job commands (not global 51-job rerun), with bounded controls:
   - lower resolution: `-r 2` (fallback `-r 4`)
   - reduce densification pressure:
     - `--densify_until_iter 8000`
     - `--densify_grad_threshold 0.0005`
     - `--opacity_cull 0.08`
3. Keep prohibitions:
   - no `--force_rerun`
   - no multi-seed
   - no full 51-job rerun without explicit user approval

## Decision
- Metric patch: **GO**
- Ablation runtime continuation: **CONDITIONAL GO** (synthetic preserved; Shiny Real failures isolated)
- Ablation claim upgrade: **NO-GO** until required ablation artifacts complete or Shiny Real scope is explicitly narrowed
