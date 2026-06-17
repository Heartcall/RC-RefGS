# RC-RefGS Prediction Artifact Recovery Plan

**Goal:** Recover provenance-matched completed predictions for TRUE GT geometry evaluation without training or substituting another run.

1. Recover the authoritative 28 main and 70 ablation rows and their recorded model paths.
2. Search `/data/liuly`, `/home/liuly`, `/mnt/data`, `/tmp`, repository outputs, logs, metadata, shell history, archives, symlinks, and trash for exact run artifacts.
3. Accept a candidate only when dataset, scene, variant, seed, iteration, and run provenance match the frozen completed experiment row.
4. If exact point clouds or checkpoints exist, perform evaluation-only mesh extraction and archive the result durably.
5. If no exact artifacts exist, do not run extraction or training; publish a recovery report and retain the mesh-quality NO-GO boundary.
6. Verify expected/valid/excluded row counts, finite-value handling, metric directions, tests, and repository diff hygiene.

**Outcome:** No exact artifact was recovered. Steps 4 and GT metric regeneration were therefore not executed.
