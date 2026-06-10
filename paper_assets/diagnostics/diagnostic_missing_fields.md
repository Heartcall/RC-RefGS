# Diagnostic Missing Fields

The current result package is sufficient for aggregate metric diagnosis but not for attributing reflective quality degradation to a single mechanism. The following fields were not found and were not fabricated:

- reflective mask area ratio per image / scene;
- RC valid correspondence ratio;
- mean RC effective weight / weight sum;
- depth consistency pass rate;
- normal agreement mean or distribution;
- specular confidence mean or distribution;
- source-target pair angle distribution;
- per-scene lambda_RC sensitivity;
- highlight edge sharpness metric;
- specular map variance before/after RC;
- reflective_region_ssim and reflective_region_lpips columns. Available reflective_ssim and reflective_lpips are retained under their source metric names;
- per-image mask coverage and per-image Refl. metric variance.

Recommended lightweight logging for the next run: save mask area, RC mask overlap with the reflective evaluation mask, depth/normal pass rates, mean confidence, pair angle, and per-image reflective PSNR/SSIM/LPIPS variance.
