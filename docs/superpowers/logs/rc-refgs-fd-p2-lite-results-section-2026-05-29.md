# RC-RefGS FD-P2-lite Results Section (Non-Shiny-Real Scope)

## 1. Scope-limited experimental setting

Within the non-Shiny-Real FD-P2-lite scope, we evaluate RC-RefGS on the two completed non-Shiny-Real datasets: Shiny Blender Synthetic and Glossy Synthetic. The main comparison contains matched `base` and `rc` runs for 14 scenes, giving 28/28 complete main jobs. The ablation comparison contains the three reduced variants `wo_ref`, `wo_conf`, and `rough_only` for the same 14 scenes, giving 42/42 complete ablation jobs.

Shiny Blender Real is excluded from this narrowed scope because it remains blocked by out-of-memory failures in the current formal runtime evidence. The original full FD-P2 scope remains incomplete due to Shiny Blender Real OOM. The original full ablation matrix remains incomplete due to Shiny Blender Real OOM.

The publication tables exported with this section are:

- Main base-vs-RC table: `docs/superpowers/logs/rc-refgs-fd-p2-lite-main-table-2026-05-29.csv`
- Ablation scene-variant table: `docs/superpowers/logs/rc-refgs-fd-p2-lite-ablation-table-2026-05-29.csv`

## 2. Main base-vs-RC findings

Within the non-Shiny-Real FD-P2-lite scope, RC reduces mean reflection consistency relative to the base model on all 14/14 training-scene pairs and on 13/14 test-scene pairs. Averaged over the scoped scenes, the RC-minus-base reflection-consistency delta is -0.074349 on the training split and -0.030599 on the test split, where lower reflection consistency is better.

The result is strongest on Shiny Blender Synthetic, where the average RC-minus-base delta is -0.147117 on train and -0.044536 on test. The largest individual improvements occur on `shiny_blender_synthetic/helmet`, with deltas of -0.551036 on train and -0.180882 on test, followed by `shiny_blender_synthetic/car` on train with -0.169805. Glossy Synthetic is directionally consistent but smaller in magnitude, with average deltas of -0.019773 on train and -0.020146 on test.

The only scoped exception is `shiny_blender_synthetic/coffee` on the test split, where RC is slightly higher than base by +0.002339. This exception prevents a universal test-split win claim, but it does not change the narrowed-scope aggregate direction.

## 3. Ablation findings

The non-Shiny-Real ablation evidence is complete at 42/42 scene-variant cells: 18/18 cells for Shiny Blender Synthetic and 24/24 cells for Glossy Synthetic. The ablation table reports per-scene values for `wo_ref`, `wo_conf`, and `rough_only`, with train/test reflection consistency, reflective-region PSNR, and valid-pair counts.

Aggregated by dataset and variant, the ablations show that removing reflection supervision (`wo_ref`) generally weakens consistency relative to the full RC behavior summarized in the paired main comparison. The confidence-neutralized variant (`wo_conf`) changes consistency substantially and is not interpretable as a full replacement for the RC mechanism because it removes one component while retaining the narrowed single-seed setting. The `rough_only` control does not reproduce the full RC behavior on the consistency metrics, supporting the interpretation that roughness regularization alone is insufficient within this scoped evidence package.

These ablations are useful for component-level diagnosis inside the non-Shiny-Real scope. They do not establish full-dataset causal claims because Shiny Blender Real is absent and the matrix is single-seed.

## 4. Limitations

This Results section is intentionally scope-limited. It uses only the completed FD-P2-lite non-Shiny-Real main evidence and the completed non-Shiny-Real ablation evidence. It excludes Shiny Blender Real due to the current OOM blocker, uses seed 0 only, and does not include multi-seed uncertainty estimates.

The metrics should be read as reflection-consistency and reflective-region diagnostic evidence, not as broad rendering-quality or material-quality proof. The CSV tables preserve per-scene values so that aggregate trends can be checked against scene-level behavior, including the `coffee` test-split exception.

## 5. Claim boundaries

Supported within this narrowed package:

- Main FD-P2-lite non-Shiny-Real completion: 28/28 jobs.
- Ablation non-Shiny-Real completion: 42/42 jobs.
- RC lowers reflection consistency on 14/14 scoped training pairs and 13/14 scoped test pairs.
- Non-Shiny-Real ablations provide complete single-seed diagnostic evidence for `wo_ref`, `wo_conf`, and `rough_only`.

Not supported by this package:

- Full 17-scene FD-P2 completion.
- Full 51-cell ablation completion.
- Shiny Blender Real conclusions.
- Broad manuscript claim upgrades, full-dataset causal claims, or multi-seed robustness claims.

