# RC-RefGS Geometry Evaluation Stage 1 - 2026-06-05

## Executive Summary

Evaluated existing completed outputs only for `helmet` and `luyu` across `base`, current `rc`, `rc_qp_lam010`, `rc_qp_lam005`, `rc_qp_lam010_start5000_every8`, and `rc_qp_angle10_sched` (`12` rows). No training, no rendering, no Shiny Blender Real, and no metric-definition changes were performed.

True geometry metrics are unavailable from the current artifacts. The evaluator computed only proxy diagnostics from final PLY point clouds: vertex count and bounding-box diagonal. These are not surface-quality metrics and cannot support a mesh/surface improvement claim.

Decision: **CONDITIONAL GO** for proxy diagnostics and instrumentation planning; **NO-GO** for geometry-improvement claims.

## Metrics Actually Computed

- `geometry_proxy_vertex_count`
- `geometry_proxy_bbox_diag`

These are artifact diagnostics, not geometry-quality metrics.

## Metrics Unavailable

- Depth error: missing GT depth and saved rendered depth buffers.
- Normal error: missing saved rendered normals; Glossy has no GT normals; Shiny normal coordinate space still must be verified before claim-bearing use.
- Mesh/point-cloud Chamfer/F-score: no extracted predicted meshes and no accepted GT mesh/eval point cloud for these scenes.
- Reflective-region geometry error: reflective masks are not saved as reusable artifacts.

## Per-Scene / Per-Variant Proxy Table

| dataset | scene | variant | test reflection consistency | test reflective LPIPS | proxy vertices | proxy bbox diag | status |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `glossy_synthetic` | `luyu` | `base` | 0.1244205117225647 | 0.024764987407252192 | 155704 | 2.436008983017052 | proxy_only |
| `glossy_synthetic` | `luyu` | `rc` | 0.1195022352039814 | 0.027182404068298638 | 166906 | 2.4309956207289236 | proxy_only |
| `glossy_synthetic` | `luyu` | `rc_qp_angle10_sched` | 0.12829604670405387 | 0.027881017420440912 | 171522 | 2.440431803041994 | proxy_only |
| `glossy_synthetic` | `luyu` | `rc_qp_lam005` | 0.12577563151717186 | 0.026320869801566005 | 162253 | 2.445485553210973 | proxy_only |
| `glossy_synthetic` | `luyu` | `rc_qp_lam010` | 0.12256455346941948 | 0.025411097216419876 | 155943 | 2.4413573750179345 | proxy_only |
| `glossy_synthetic` | `luyu` | `rc_qp_lam010_start5000_every8` | 0.12836674004793167 | 0.024794823839329183 | 157172 | 2.434791582410234 | proxy_only |
| `shiny_blender_synthetic` | `helmet` | `base` | 0.21683893352746964 | 0.011352510314900428 | 60619 | 3.1117898624991978 | proxy_only |
| `shiny_blender_synthetic` | `helmet` | `rc` | 0.035956913605332375 | 0.011322217297274619 | 60312 | 3.1134405101621865 | proxy_only |
| `shiny_blender_synthetic` | `helmet` | `rc_qp_angle10_sched` | 0.0481265626847744 | 0.011476712876465171 | 62057 | 3.1134008007112834 | proxy_only |
| `shiny_blender_synthetic` | `helmet` | `rc_qp_lam005` | 0.047587974742054936 | 0.011743516454007476 | 62064 | 3.1127103994877325 | proxy_only |
| `shiny_blender_synthetic` | `helmet` | `rc_qp_lam010` | 0.03896044492721558 | 0.011728961081244051 | 61267 | 3.1142498391876496 | proxy_only |
| `shiny_blender_synthetic` | `helmet` | `rc_qp_lam010_start5000_every8` | 0.04388582669198513 | 0.011285552345216275 | 61286 | 3.1130202553077946 | proxy_only |

## Win Counts

The evaluator intentionally does not report geometry win counts because no true geometry metric was computed. Proxy vertex-count deltas are present in the JSON under `win_counts`, but the claim boundary is explicit: lower or higher splat count is not a geometry-quality win.

## Correlation Diagnostics

- Reflection consistency vs reflective LPIPS: `0.4903215991051819`.
- Reflection consistency vs proxy vertex count: `0.49408289477263756`.
- Reflection consistency vs depth/normal/mesh error: unavailable because those metrics are unavailable.

## Counterexamples

Consistency improves but RGB worsens vs base:
- `glossy_synthetic/luyu/rc`: consistency delta -0.00491828, full LPIPS delta 0.00153809, reflective LPIPS delta 0.00241742
- `glossy_synthetic/luyu/rc_qp_lam010`: consistency delta -0.00185596, full LPIPS delta 0.000628954, reflective LPIPS delta 0.00064611
- `shiny_blender_synthetic/helmet/rc`: consistency delta -0.180882, full LPIPS delta 3.39664e-05, reflective LPIPS delta -3.0293e-05
- `shiny_blender_synthetic/helmet/rc_qp_angle10_sched`: consistency delta -0.168712, full LPIPS delta 0.00011004, reflective LPIPS delta 0.000124203
- `shiny_blender_synthetic/helmet/rc_qp_lam005`: consistency delta -0.169251, full LPIPS delta 0.000508498, reflective LPIPS delta 0.000391006
- `shiny_blender_synthetic/helmet/rc_qp_lam010`: consistency delta -0.177878, full LPIPS delta 0.000368771, reflective LPIPS delta 0.000376451

Consistency improves but proxy vertex count increases vs base:
- `glossy_synthetic/luyu/rc`: proxy vertex count +11202 vs base
- `glossy_synthetic/luyu/rc_qp_lam010`: proxy vertex count +239 vs base
- `shiny_blender_synthetic/helmet/rc_qp_angle10_sched`: proxy vertex count +1438 vs base
- `shiny_blender_synthetic/helmet/rc_qp_lam005`: proxy vertex count +1445 vs base
- `shiny_blender_synthetic/helmet/rc_qp_lam010`: proxy vertex count +648 vs base
- `shiny_blender_synthetic/helmet/rc_qp_lam010_start5000_every8`: proxy vertex count +667 vs base

Depth/normal/mesh counterexamples cannot be evaluated yet because true geometry metrics are unavailable.

## Answers To Research Questions

1. Reflection consistency vs geometry quality: cannot be answered yet for depth/normal/mesh. Current artifacts support only proxy correlations.
2. Current RC geometry vs base: no true geometry conclusion. Proxy rows show scene-dependent splat-count changes only.
3. Quality-preserving variants and geometry: no true geometry conclusion; proxy-only diagnostics do not support improvement claims.
4. Consistency improves but RGB worsens: yes, there are RGB counterexamples in the two-scene set.
5. Geometry-aware RC loss justified: justified as a future instrumented research direction, not as a validated improvement.

## Claim Boundary

No mesh/surface improvement claim, no full FD-P2 claim, no Shiny Real claim, and no global RC-RefGS-over-Ref-GS claim are supported.
