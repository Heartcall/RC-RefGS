# RC-RefGS Current Main and Ablation Analysis (2026-05-29)

## 1. Executive summary
- Main FD-P2 formal completion: **29/34** jobs.
- Main complete base/rc pairs: **14/17** scenes.
- Ablation formal completion: **42/51** jobs.
- Non-Shiny-Real ablations: **42/42** complete.
- **All non-Shiny-Real ablation experiments are complete.**
- **Full ablation matrix is not complete because Shiny Blender Real remains OOM-blocked.**
- **FD-P2 main claim remains NO-GO until Shiny Real main cells are completed or scope is explicitly narrowed.**
- **No manuscript/scientific claim upgrade in this task.**

## 2. Main FD-P2 status
- Expected main jobs: 34
- Complete main jobs: 29
- Missing main jobs: 5
- Incomplete main cells (formal artifacts missing):
  - `shiny_blender_real/gardenspheres/rc/seed_0` -> point_cloud/iteration_31000/point_cloud.ply, reflection_consistency_train.json, reflection_consistency_test.json, launcher_summary.json
  - `shiny_blender_real/sedan/base/seed_0` -> point_cloud/iteration_31000/point_cloud.ply, reflection_consistency_train.json, reflection_consistency_test.json, launcher_summary.json
  - `shiny_blender_real/sedan/rc/seed_0` -> point_cloud/iteration_31000/point_cloud.ply, reflection_consistency_train.json, reflection_consistency_test.json, launcher_summary.json
  - `shiny_blender_real/toycar/base/seed_0` -> point_cloud/iteration_31000/point_cloud.ply, reflection_consistency_train.json, reflection_consistency_test.json, launcher_summary.json
  - `shiny_blender_real/toycar/rc/seed_0` -> point_cloud/iteration_31000/point_cloud.ply, reflection_consistency_train.json, reflection_consistency_test.json, launcher_summary.json

## 3. Main FD-P2 base-vs-RC reflection consistency table
| Dataset | Scene | Pair complete | Train delta (rc-base) | Test delta (rc-base) | RC lower train | RC lower test |
|---|---|---:|---:|---:|---:|---:|
| shiny_blender_synthetic | ball | yes | -0.004866 | -0.001398 | true | true |
| shiny_blender_synthetic | car | yes | -0.169805 | -0.037831 | true | true |
| shiny_blender_synthetic | coffee | yes | -0.031656 | 0.002339 | true | false |
| shiny_blender_synthetic | helmet | yes | -0.551036 | -0.180882 | true | true |
| shiny_blender_synthetic | teapot | yes | -0.009279 | -0.001198 | true | true |
| shiny_blender_synthetic | toaster | yes | -0.116057 | -0.048244 | true | true |
| shiny_blender_real | gardenspheres | no | n/a | n/a | n/a | n/a |
| shiny_blender_real | sedan | no | n/a | n/a | n/a | n/a |
| shiny_blender_real | toycar | no | n/a | n/a | n/a | n/a |
| glossy_synthetic | angel | yes | -0.016347 | -0.014609 | true | true |
| glossy_synthetic | bell | yes | -0.004472 | -0.001976 | true | true |
| glossy_synthetic | cat | yes | -0.007061 | -0.006836 | true | true |
| glossy_synthetic | horse | yes | -0.020893 | -0.030379 | true | true |
| glossy_synthetic | luyu | yes | -0.008841 | -0.004918 | true | true |
| glossy_synthetic | potion | yes | -0.005238 | -0.002452 | true | true |
| glossy_synthetic | tbell | yes | -0.054509 | -0.056501 | true | true |
| glossy_synthetic | teapot | yes | -0.040824 | -0.043500 | true | true |

## 4. Ablation status after Glossy Synthetic completion
- Shiny Blender Synthetic: **18/18**
- Glossy Synthetic: **24/24**
- Shiny Blender Real: **0/9**
- Non-Shiny-Real total: **42/42**
- Overall ablations: **42/51**

## 5. Ablation metric summary table
| Dataset | Variant | Complete/Expected | Mean train consistency | Mean test consistency | Mean train reflective PSNR | Mean test reflective PSNR |
|---|---|---:|---:|---:|---:|---:|
| shiny_blender_synthetic | wo_ref | 6/6 | 0.211805 | 0.075456 | 35.501986 | 31.395515 |
| shiny_blender_synthetic | wo_conf | 6/6 | 0.109448 | 0.038645 | 35.263859 | 31.467753 |
| shiny_blender_synthetic | rough_only | 6/6 | 0.193192 | 0.069570 | 35.313420 | 31.617157 |
| shiny_blender_real | wo_ref | 0/3 | n/a | n/a | n/a | n/a |
| shiny_blender_real | wo_conf | 0/3 | n/a | n/a | n/a | n/a |
| shiny_blender_real | rough_only | 0/3 | n/a | n/a | n/a | n/a |
| glossy_synthetic | wo_ref | 8/8 | 0.174459 | 0.179875 | 26.341012 | 24.311390 |
| glossy_synthetic | wo_conf | 8/8 | 0.159928 | 0.167266 | 26.352376 | 24.291163 |
| glossy_synthetic | rough_only | 8/8 | 0.175582 | 0.180672 | 26.264969 | 24.242445 |

## 6. Non-Shiny-Real ablation completion: 42/42
- Shiny Blender Synthetic (18/18) and Glossy Synthetic (24/24) are formally complete under the four-artifact criterion.
- This is a complete non-Shiny-Real ablation evidence package.

## 7. Shiny Real OOM blocker
- Shiny Blender Real ablations remain incomplete and OOM-blocked in prior runtime traces; current formal completion is 0/9.
- Full 51/51 ablation completion remains blocked until Shiny Real recovery is stabilized.

## 8. Evidence-supported conclusions
- All non-Shiny-Real ablation experiments are complete.
- Main FD-P2 evidence remains partial (29/34) and supports only subset conclusions on complete pairs.
- RC lowers reflection consistency on most complete main pairs (train 14/14, test 13/14).

## 9. Claims that remain unsupported
- Full-dataset main claim (34/34) is unsupported while Shiny Real main cells remain incomplete.
- Full ablation matrix claim (51/51) is unsupported while Shiny Real ablations remain incomplete.
- Manuscript/scientific claim upgrades remain unsupported in this task.

## 10. Recommended next actions
- Finish remaining FD-P2 Shiny Real base/rc cells before any full main claim.
- Keep non-Shiny-Real ablation package fixed as complete 42/42 evidence.
- Defer Shiny Blender Real ablations until bounded reduced-resolution recovery is stable and reproducible.
- No manuscript/scientific claim upgrade until main FD-P2 reaches 34/34 or scope is explicitly narrowed.
- Do not start multi-seed until single-seed full matrix is complete and summarized.
