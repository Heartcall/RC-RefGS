# RC-RefGS Coordination Board

## Active Task Claims

None.

## Completed Tasks

- 2026-05-16 09:03 CST | research plan created: `docs/superpowers/plans/2026-05-16-rc-refgs-research-plan.md`.
- 2026-05-16 13:54:04 CST | model/window: codex implementation window | completed: Task 1 - expose Ref-GS intermediate render buffers | files touched: `gaussian_renderer/__init__.py`, `tests/test_rc_refgs_static.py` | verification: `python -m unittest tests.test_rc_refgs_static` exit 0, `python -m py_compile gaussian_renderer/__init__.py` exit 0 | artifact: `render()` now returns `spec_light`, `diff_light`, `roughness_map`, `reflection_dir`, and `feature_map`.
- 2026-05-16 13:57:25 CST | model/window: codex implementation window | completed: Task 2 safe subset - reflection consistency helper scaffolding | files touched: `utils/reflection_consistency.py`, `tests/test_reflection_consistency.py` | verification: `python -m unittest tests.test_reflection_consistency` exit 0, `python -m py_compile utils/reflection_consistency.py` exit 0 | artifact: helper functions for camera pairing, backprojection, projection, and masked specular consistency loss.
- 2026-05-16 14:00:46 CST | model/window: codex implementation window | completed: Task 3 safe subset - disabled-by-default training gate | files touched: `arguments/__init__.py`, `train.py`, `tests/test_rc_refgs_training_static.py` | verification: `python -m unittest tests.test_rc_refgs_training_static` exit 0, `python -m unittest discover tests` exit 0, `python -m py_compile gaussian_renderer/__init__.py utils/reflection_consistency.py train.py arguments/__init__.py` exit 0 | artifact: ablation arguments and guarded train-time reflection consistency loss.
- 2026-05-16 14:03:08 CST | model/window: codex implementation window | completed: Task 4 - confidence-aware TSDF extraction | files touched: `utils/mesh_utils.py`, `tests/test_rc_refgs_mesh_confidence_static.py` | verification: `python -m unittest tests.test_rc_refgs_mesh_confidence_static` exit 0, `python -m unittest tests.test_rc_refgs_static tests.test_reflection_consistency tests.test_rc_refgs_mesh_confidence_static` exit 0, `python -m py_compile utils/mesh_utils.py` exit 0 | artifact: confidence maps are cached during reconstruction and optional `conf_threshold` masking is applied before TSDF integration.
- 2026-05-16 14:08:35 CST | model/window: codex implementation window | completed: Task 5 - reflection consistency metric script and ablation runner | files touched: `metrics/reflection_consistency_eval.py`, `scripts/run_rc_refgs_ablation.sh`, `tests/test_reflection_consistency_eval_static.py` | verification: `python -m unittest tests.test_reflection_consistency_eval_static` exit 0, `python -m unittest discover tests` exit 0, `python -m py_compile gaussian_renderer/__init__.py utils/reflection_consistency.py train.py arguments/__init__.py utils/mesh_utils.py metrics/reflection_consistency_eval.py` exit 0 | artifacts: JSON metric script (`mean_reflection_consistency`, `reflective_region_psnr`, `num_pairs`) and ablation launch script for `teapot/toaster/car`.
- 2026-05-16 14:12:47 CST | model/window: codex implementation window | completed: smoke-run blocker code fix - pre-import CUDA device selection | files touched: `train.py`, `tests/test_rc_refgs_training_static.py` | verification: `python -m unittest tests.test_rc_refgs_training_static` exit 0, `python -m unittest discover tests` exit 0, `python -m py_compile gaussian_renderer/__init__.py utils/reflection_consistency.py train.py arguments/__init__.py utils/mesh_utils.py metrics/reflection_consistency_eval.py` exit 0 | artifact: `--cuda_device` is applied before torch import; existing `CUDA_VISIBLE_DEVICES` is preserved if no CLI override is supplied; default remains GPU 2.
- 2026-05-16 15:36:45 CST | model/window: codex implementation window | completed: renderer diagnostic contract gap - return `select_index` | files touched: `gaussian_renderer/__init__.py`, `tests/test_rc_refgs_static.py` | verification: `python -m unittest tests.test_rc_refgs_static` exit 0, `python -m unittest discover tests` exit 0, `python -m py_compile gaussian_renderer/__init__.py` exit 0, full compile command exit 0 | artifact: `render()` now returns `'select_index': select_index` alongside RC intermediate maps.
- 2026-05-16 16:09:20 CST | model/window: codex implementation window | completed: explicit CUDA-device control for metric and ablation launch path | files touched: `metrics/reflection_consistency_eval.py`, `scripts/run_rc_refgs_ablation.sh`, `tests/test_reflection_consistency_eval_static.py` | verification: `python -m unittest tests.test_reflection_consistency_eval_static` RED exit 1 then GREEN exit 0, `python -m unittest discover tests` exit 0, `python -m py_compile gaussian_renderer/__init__.py utils/reflection_consistency.py train.py arguments/__init__.py utils/mesh_utils.py metrics/reflection_consistency_eval.py` exit 0, `bash -n scripts/run_rc_refgs_ablation.sh` exit 0 | artifact: metric script applies `--cuda_device` before torch import; ablation runner exposes `CUDA_DEVICE` and passes it to train/eval commands.

## Blockers

- Baseline one-iteration smoke failed earlier on 2026-05-16 because default hardcoded GPU had only 9.56 MiB free; root cause was `train.py` overwriting `CUDA_VISIBLE_DEVICES`. Code fix completed at 14:12:47 CST.
- Current smoke blocker at 2026-05-16 14:12:47 CST is GPU resource availability, not the CLI parsing path: `--cuda_device 1` reaches torch but a minimal CUDA allocation fails with `all CUDA-capable devices are busy or unavailable`; `--cuda_device 0` reaches camera loading but fails CUDA OOM with only 7.56 MiB free.
- Rechecked at 2026-05-16 15:32 CST: GPU 1 is visible and low-memory, but minimal CUDA allocation still fails with `all CUDA-capable devices are busy or unavailable`.
- Rechecked at 2026-05-16 16:07 CST: GPU 1 remains visible and low-memory, but minimal CUDA allocation still fails with `all CUDA-capable devices are busy or unavailable`.

## Model Handoffs

## Model Handoff
Target model: gpt-5.5
Reason: Coding tasks through Task 5 are complete and smoke-run code-path fixes are landed, but execution is currently blocked by unavailable usable GPU resources; highest-value next step is research-side prioritization/go-no-go framing while waiting for compute.
Current state: RC-RefGS Task 1-5 implementations are in-tree and lightweight verification is green; one-iteration smoke attempts fail due GPU busy/unavailable or OOM.
Files touched: `metrics/reflection_consistency_eval.py`, `scripts/run_rc_refgs_ablation.sh`, `tests/test_reflection_consistency_eval_static.py`, `docs/superpowers/logs/rc-refgs-autonomous-log.md`, `docs/superpowers/logs/rc-refgs-coordination-board.md`.
Files to avoid: `train.py`, `arguments/__init__.py`, `gaussian_renderer/__init__.py`, `utils/reflection_consistency.py`, `utils/mesh_utils.py` unless a new coding claim is made.
Recommended next task: Perform plan-audit/go-no-go review for experiment sequencing under compute scarcity, then define the minimum evidence run matrix to execute immediately once one GPU is free.
Required skills: `using-superpowers`, `executing-plans`.
Verification command: N/A (reasoning/audit handoff). When resuming execution, rerun `python -m unittest discover tests` before launching smoke.
Go/no-go criterion: GO only if the audit confirms the reduced run matrix still tests the main RC claim; otherwise CONDITIONAL GO with explicit risk tags.

## Go/No-Go Decisions

- 2026-05-16 13:54:04 CST | GO for Task 1 only. Rationale: exposes already-computed tensors, preserves default behavior, and enables later reflection-consistency loss implementation.
- 2026-05-16 13:57:25 CST | CONDITIONAL GO for Task 2 helper scaffolding only. Do not edit `train.py` until helper tests pass.
- 2026-05-16 14:00:46 CST | CONDITIONAL GO for Task 3 safe subset. Add arguments and gated code only; no smoke training in this step.
- 2026-05-16 14:03:08 CST | GO for Task 4. Rationale: confidence-aware TSDF path is default-preserving (`conf_threshold=0.0`) and covered by static + compile verification.
- 2026-05-16 14:08:35 CST | GO for Task 5. Rationale: evaluator/ablation artifacts are present, tested for contract coverage, and repo-wide lightweight regression is green.
- 2026-05-16 14:12:47 CST | CONDITIONAL GO after smoke blocker code fix. Rationale: unit/static/compile checks pass; one-iteration training smoke is blocked by unavailable usable GPU memory/resources.
- 2026-05-16 15:18:52 CST | SWITCH MODEL. Rationale: implementation tasks are complete for this phase; next high-value step is gpt-5.5 research audit while waiting for compute availability.
- 2026-05-16 15:36:45 CST | CONDITIONAL GO after renderer diagnostic contract patch. Rationale: non-GPU verification is green; runtime smoke remains blocked by GPU resource availability.
- 2026-05-16 16:09:20 CST | CONDITIONAL GO after eval/ablation CUDA-device patch. Rationale: non-GPU verification is green and experiment launch path can target a selected GPU, but runtime smoke remains blocked by GPU resource availability.

## Next Suggested Tasks

- Recommended next verification task: when a usable GPU is available, rerun one-iteration baseline smoke with `--cuda_device <free_gpu>` and then RC smoke with `--lambda_ref_consistency 0.02 --ref_consistency_start 1 --ref_consistency_every 1`.
- Recommended next experiment task after smoke passes: run a tiny RC vs baseline smoke pair (`teapot` only) and generate `metrics/reflection_consistency_eval.py` JSON outputs for sanity checking.
- Recommended next verification task after that: confirm `scripts/run_rc_refgs_ablation.sh` end-to-end on at least one scene with reduced iterations before launching full runs.
- Recommended immediate cross-model task: gpt-5.5 should audit whether RC claims can be defended if only smoke-scale evidence is available initially and prepare exact acceptance thresholds for first full run.
