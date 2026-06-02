# RC-RefGS FD-P2-lite Non-Shiny-Real Closed-Loop Experimental Summary

## 1. Scope definition
- Included datasets: `shiny_blender_synthetic` (6 scenes) + `glossy_synthetic` (8 scenes).
- Included main variants: `base`, `rc` (expected 28 jobs).
- Included ablation variants: `wo_ref`, `wo_conf`, `rough_only` (expected 42 jobs).
- Excluded dataset: `shiny_blender_real`.
- Exclusion reason: Shiny Blender Real remains OOM-blocked and is explicitly excluded in this narrowed scope decision.

## 2. Completion status
- Main FD-P2-lite: **28/28**.
- Ablation non-Shiny-Real: **42/42**.
- Original full FD-P2 (17-scene) scope: **not complete**.
- Original full ablation matrix (51-cell) scope: **not complete**.

## 3. Main result table
| Dataset | Scene | Base train | RC train | Train delta | Base test | RC test | Test delta | RC lower train? | RC lower test? |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| shiny_blender_synthetic | ball | 0.171265 | 0.166399 | -0.004866 | 0.049551 | 0.048153 | -0.001398 | true | true |
| shiny_blender_synthetic | car | 0.312476 | 0.142671 | -0.169805 | 0.086073 | 0.048242 | -0.037831 | true | true |
| shiny_blender_synthetic | coffee | 0.053886 | 0.022230 | -0.031656 | 0.006913 | 0.009251 | 0.002339 | true | false |
| shiny_blender_synthetic | helmet | 0.640577 | 0.089542 | -0.551036 | 0.216839 | 0.035957 | -0.180882 | true | true |
| shiny_blender_synthetic | teapot | 0.021762 | 0.012483 | -0.009279 | 0.003896 | 0.002698 | -0.001198 | true | true |
| shiny_blender_synthetic | toaster | 0.278151 | 0.162093 | -0.116057 | 0.105457 | 0.057213 | -0.048244 | true | true |
| glossy_synthetic | angel | 0.116105 | 0.099758 | -0.016347 | 0.122405 | 0.107795 | -0.014609 | true | true |
| glossy_synthetic | bell | 0.147816 | 0.143343 | -0.004472 | 0.109720 | 0.107743 | -0.001976 | true | true |
| glossy_synthetic | cat | 0.122459 | 0.115398 | -0.007061 | 0.156606 | 0.149770 | -0.006836 | true | true |
| glossy_synthetic | horse | 0.199373 | 0.178480 | -0.020893 | 0.225030 | 0.194651 | -0.030379 | true | true |
| glossy_synthetic | luyu | 0.118881 | 0.110040 | -0.008841 | 0.124421 | 0.119502 | -0.004918 | true | true |
| glossy_synthetic | potion | 0.092401 | 0.087164 | -0.005238 | 0.085846 | 0.083394 | -0.002452 | true | true |
| glossy_synthetic | tbell | 0.280801 | 0.226292 | -0.054509 | 0.316943 | 0.260442 | -0.056501 | true | true |
| glossy_synthetic | teapot | 0.335104 | 0.294280 | -0.040824 | 0.295933 | 0.252433 | -0.043500 | true | true |

## 4. Main result summary
- RC lowers reflection consistency on train: **14/14**.
- RC lowers reflection consistency on test: **13/14**.
- Strongest improvements (most negative rc-base deltas):
  - `shiny_blender_synthetic/helmet` `train` delta `-0.551036`
  - `shiny_blender_synthetic/helmet` `test` delta `-0.180882`
  - `shiny_blender_synthetic/car` `train` delta `-0.169805`
- Exception scene/split where RC is not lower:
  - `shiny_blender_synthetic/coffee` `test` delta `0.002339`

## 5. Ablation result table
| Dataset | Variant | Complete/Expected | Mean train consistency | Mean test consistency | Mean train reflective PSNR | Mean test reflective PSNR |
|---|---|---:|---:|---:|---:|---:|
| shiny_blender_synthetic | wo_ref | 6/6 | 0.211805 | 0.075456 | 35.501986 | 31.395515 |
| shiny_blender_synthetic | wo_conf | 6/6 | 0.109448 | 0.038645 | 35.263859 | 31.467753 |
| shiny_blender_synthetic | rough_only | 6/6 | 0.193192 | 0.069570 | 35.313420 | 31.617157 |
| glossy_synthetic | wo_ref | 8/8 | 0.174459 | 0.179875 | 26.341012 | 24.311390 |
| glossy_synthetic | wo_conf | 8/8 | 0.159928 | 0.167266 | 26.352376 | 24.291163 |
| glossy_synthetic | rough_only | 8/8 | 0.175582 | 0.180672 | 26.264969 | 24.242445 |

## 6. Ablation interpretation
- `wo_ref`: removing reflection-consistency supervision generally weakens consistency relative to RC on paired non-Shiny-Real evidence.
- `wo_conf`: neutralizing confidence weighting shows measurable consistency shifts versus RC; magnitude varies by dataset/scene.
- `rough_only`: roughness-only regularization alone does not reproduce full RC behavior on consistency metrics.
- Comparison limitations: interpretation is paired within narrowed non-Shiny-Real scope only; no Shiny Real support and no causal overclaim.

## 7. Evidence-supported conclusions
- Within the non-Shiny-Real FD-P2-lite scope, the main base/RC experiment is complete at 28/28.
- Within the non-Shiny-Real scope, the ablation experiment is complete at 42/42.
- RC reduces reflection consistency on nearly all scoped base/RC pairs.
- The full 17-scene FD-P2 claim remains unsupported because Shiny Blender Real is excluded due to OOM.
- The full 51-cell ablation claim remains unsupported because Shiny Blender Real ablations are excluded due to OOM.

## 8. Limitations
- Shiny Blender Real is excluded from this formal FD-P2-lite scope due to OOM blocker.
- Single seed only (seed 0).
- Reduced scope (non-Shiny-Real only).
- No full 17-scene FD-P2 claim from this scope.
- No full 51-cell ablation claim from this scope.

## 9. Recommended next actions
- Finalize non-Shiny-Real figures/tables for the scoped package.
- Write scope-limited results section with explicit exclusion boundaries.
- Optionally pursue Shiny Real with higher-memory resources or redesigned recovery.
- Do not start multi-seed until narrowed single-seed evidence is packaged.
