# RC-RefGS GT Geometry Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reproducible GT geometry evaluation and conservative paper assets for completed RC-RefGS main and ablation runs.

**Architecture:** A single Python evaluator owns geometry loading, deterministic sampling, metrics, optional diagnostic alignment, project manifest construction, and artifact generation. Frozen experiment tables define expected rows; filesystem checks decide valid evaluations versus exclusions.

**Tech Stack:** Python, NumPy, SciPy `cKDTree`, trimesh, plyfile, pandas, matplotlib, unittest.

---

### Task 1: Core geometry metrics

**Files:**
- Create: `tests/test_evaluate_gt_geometry.py`
- Create: `paper_assets/geometry_gt/scripts/evaluate_gt_geometry.py`

- [ ] Write failing tests for identity, translated geometry, deterministic mesh sampling, and diagnostic similarity alignment.
- [ ] Run `python -m unittest tests/test_evaluate_gt_geometry.py -v` and confirm the missing evaluator failure.
- [ ] Implement geometry loading, sampling, raw metrics, normal gating, mismatch diagnostics, and explicitly labeled alignment.
- [ ] Re-run the targeted tests and require zero failures.

### Task 2: Project row audit and batch outputs

**Files:**
- Modify: `tests/test_evaluate_gt_geometry.py`
- Modify: `paper_assets/geometry_gt/scripts/evaluate_gt_geometry.py`

- [ ] Add a failing test for 28 main rows, 70 ablation rows, and 14 GT mappings.
- [ ] Implement completed-row construction, prediction discovery, GT mapping, exclusions, and requested CSV writers.
- [ ] Run the targeted tests and require zero failures.

### Task 3: Paper tables, figures, and analysis

**Files:**
- Modify: `paper_assets/geometry_gt/scripts/evaluate_gt_geometry.py`
- Create generated artifacts under `paper_assets/geometry_gt/`

- [ ] Implement LaTeX tables and Python/matplotlib PDF+PNG figures with explicit no-data handling.
- [ ] Implement the Chinese audit/results analysis and claim-boundary table.
- [ ] Run one synthetic smoke evaluation, then the full project package command.
- [ ] Verify figures visually and verify all requested artifact paths.

### Task 4: Protocol logs and final verification

**Files:**
- Modify: `docs/superpowers/logs/rc-refgs-autonomous-log.md`
- Modify: `docs/superpowers/logs/rc-refgs-coordination-board.md`
- Modify: `paper_assets/rc_results_summary_zh.md`
- Modify: `paper_assets/experiment_claim_boundary.md`

- [ ] Record commands, per-row outcomes, exclusions, decision, and next action.
- [ ] Run unit tests, compilation, CSV assertions, finite-value checks, `git diff --check`, and prohibited-process scan.
- [ ] Request an independent code review and resolve critical/important findings.
