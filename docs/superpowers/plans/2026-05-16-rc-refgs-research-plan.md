# RC-RefGS Research and Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reflection-consistency supervision to Ref-GS so view-dependent specular appearance becomes a cross-view geometry/material constraint rather than only a single-view RGB fitting term.

**Architecture:** Keep Ref-GS representation and renderer: 2D Gaussian surfels, deferred albedo/roughness/feature buffers, Sph-Mip directional encoding, and specular MLP. Add returned intermediate buffers, a view-pair reflection consistency loss, optional roughness-aware specular smoothness, and confidence-aware TSDF mesh extraction.

**Tech Stack:** Python, PyTorch, CUDA rasterizer already in Ref-GS, Open3D TSDF extraction, local datasets under `/data/liuly/dataset/3DGS`.

---

## Paper Method Plan

### Core Claim

- [ ] State the central problem as: Ref-GS can fit reflective RGB by changing normal, roughness, Gaussian feature, Sph-Mip entries, and MLP output jointly, but its supervision does not explicitly require the reflected appearance of the same surface region to be consistent across views.
- [ ] Use the code evidence:
  - `gaussian_renderer/__init__.py:125-167` computes reflected direction, Sph-Mip feature, Gaussian feature outer product, and `spec_light`.
  - `train.py:82-100` supervises final PBR RGB and normal self-consistency.
  - `utils/mesh_utils.py:131-171` extracts mesh from rendered depth by TSDF fusion.
- [ ] Define the proposed method name as **RC-RefGS: Reflection-Consistent Ref-GS**.

### Method Components

- [ ] **Intermediate buffer exposure**
  - Return `spec_light`, `diff_light`, `roughness_map`, `wo`, `feature_map`, `select_index`, and optionally linear unclamped `pbr_linear` from `render()`.
  - Purpose: make Ref-GS decomposition observable to losses and diagnostics without replacing Sph-Mip or MLP.

- [ ] **View-pair reflection consistency**
  - Sample a second nearby camera every `K` iterations.
  - Render both views.
  - Backproject confident pixels from source view using `surf_depth`.
  - Reproject to target view and use depth/alpha checks for visibility.
  - Compare the predicted specular response in reflection space:
    `L_ref = || stopgrad(C_s^src) - sample(C_s^tgt) ||_1`
    with confidence:
    `w = alpha_src * alpha_tgt * normal_agreement * depth_visibility * specular_confidence`.
  - Use `specular_confidence = clamp(mean(spec_light), 0, 1) * (1 - roughness)^gamma` for mirror-like regions first.

- [ ] **Reflection-coordinate consistency diagnostic**
  - Export per-view `wo` maps and `spec_light` maps.
  - Measure reprojected specular inconsistency on held-out view pairs.
  - Treat this as a new metric, not only a training loss.

- [ ] **Confidence-aware mesh extraction**
  - During mesh reconstruction, compute confidence:
    `conf = alpha * clamp(dot(rend_normal, surf_normal), 0, 1)`.
  - Mask depths below `conf_threshold` before TSDF fusion.
  - This is a supporting component, not the paper's core novelty.

## Experiment Plan

### Datasets

- [ ] Main: `/data/liuly/dataset/3DGS/refnerf/{ball,car,coffee,helmet,teapot,toaster}`.
  - Evidence: each object has train/test transforms, train/test RGB, alpha, normal, and `points3d.ply`.
- [ ] Mesh/normal validation: `/data/liuly/dataset/3DGS/glossy/SMVP3D/{david,dragon,hedgehog,snail,squirrel}`.
  - Evidence: each has `image/`, `normal/`, `s0/`, `s1/`, `s2/`, `cameras.npz`, and `.obj`.
- [ ] Real generalization: `/data/liuly/dataset/3DGS/glossy/GlossyReal/{bear,bunny,coral,maneki,vase}`.
- [ ] Cross-scene/lighting stress: `/data/liuly/dataset/3DGS/llff_colmap_LDR`.

### Baselines

- [ ] Ref-GS original code.
- [ ] 2DGS if runnable in the same environment.
- [ ] GS-2DGS / MaterialRefGS / SSR-GS / GS-2M if code is available or paper numbers can be cited.
- [ ] Ablations:
  - `RC-RefGS w/o L_ref`
  - `RC-RefGS w/o specular confidence`
  - `RC-RefGS w/o confidence TSDF`
  - `RC-RefGS roughness smoothness only`

### Metrics

- [ ] Novel view synthesis: PSNR, SSIM, LPIPS on all pixels.
- [ ] Reflective-region rendering: PSNR/SSIM/LPIPS inside alpha/specular masks.
- [ ] Reflection consistency: reprojected specular consistency error across view pairs.
- [ ] Geometry: normal MAE where normal maps exist; Chamfer/F-score where OBJ or point/mesh reference exists.
- [ ] Mesh extraction quality: connected component count, surface area outliers, depth-to-mesh reprojection error.
- [ ] Material diagnostics: cross-view albedo variance and roughness/specular maps.

### Expected Evidence Chain

- [ ] If `L_ref` is useful, it should reduce reprojected specular inconsistency before it improves global PSNR.
- [ ] Geometry hypothesis: reflective-region normal error and mesh artifacts decrease more than non-reflective-region errors when `L_ref` is enabled.
- [ ] If only PSNR improves, the method should be framed as view-dependent rendering stabilization, not surface reconstruction.
- [ ] If confidence TSDF improves mesh without rendering gains, report it as a practical extraction module, not core contribution.

## Implementation Plan

### Task 1: Expose Ref-GS Intermediate Buffers

**Files:**
- Modify: `gaussian_renderer/__init__.py`
- Test: `python -m py_compile gaussian_renderer/__init__.py`

- [ ] **Step 1: Add return keys in `render()`**

Add these entries to the `rets.update({...})` block near the existing `pbr_rgb` return:

```python
'spec_light': output_spec_rgb,
'diff_light': output_diff_rgb,
'roughness_map': output_roughness,
'reflection_dir': output_wo,
'feature_map': output_feature,
```

Construct the maps using the existing `select_index` pattern:

```python
output_spec_rgb = torch.zeros(image_height, image_width, 3, device="cuda")
output_spec_rgb.reshape(-1, 3)[select_index] = spec_light
output_spec_rgb = output_spec_rgb.permute(2, 0, 1)
```

- [ ] **Step 2: Compile**

Run:

```bash
python -m py_compile gaussian_renderer/__init__.py
```

Expected: exit code 0.

### Task 2: Add View-Pair Sampling Utility

**Files:**
- Create: `utils/reflection_consistency.py`
- Modify: `train.py`
- Test: `python -m py_compile utils/reflection_consistency.py train.py`

- [ ] **Step 1: Implement helper functions**

Create functions:

```python
def choose_pair_camera(viewpoint_stack, current_cam, max_angle_deg=20.0):
    """Return a nearby camera for cross-view reflection consistency."""

def backproject_depth(view, depth):
    """Convert source pixels and depth to world points."""

def project_points(view, points_world):
    """Project world points to normalized grid coordinates and depth."""

def reflection_consistency_loss(src_pkg, tgt_pkg, src_cam, tgt_cam, gamma=2.0):
    """Compute robust source-target specular consistency with alpha/depth/normal confidence."""
```

- [ ] **Step 2: Keep loss robust and sparse**

Use a random subset of confident pixels:

```python
mask = (src_pkg["rend_alpha"] > 0.2) & (src_pkg["roughness_map"].mean(0, keepdim=True) < 0.6)
```

Use `torch.nn.functional.grid_sample` for target specular sampling.

- [ ] **Step 3: Compile**

Run:

```bash
python -m py_compile utils/reflection_consistency.py train.py
```

Expected: exit code 0.

### Task 3: Wire Loss Into Training

**Files:**
- Modify: `arguments/__init__.py`
- Modify: `train.py`
- Test: short dry run if dependencies are available

- [ ] **Step 1: Add arguments**

In `OptimizationParams`, add:

```python
self.lambda_ref_consistency = 0.0
self.ref_consistency_start = 3000
self.ref_consistency_every = 4
self.ref_consistency_max_angle = 20.0
self.ref_consistency_gamma = 2.0
```

- [ ] **Step 2: Add scheduled loss**

In `train.py`, after normal loss:

```python
if opt.lambda_ref_consistency > 0 and iteration >= opt.ref_consistency_start and iteration % opt.ref_consistency_every == 0:
    pair_cam = choose_pair_camera(viewpoint_stack, viewpoint_cam, opt.ref_consistency_max_angle)
    if pair_cam is not None:
        pair_pkg = render(pair_cam, gaussians, pipe, bg, iteration=iteration)
        ref_loss = reflection_consistency_loss(render_pkg, pair_pkg, viewpoint_cam, pair_cam, opt.ref_consistency_gamma)
        loss = loss + opt.lambda_ref_consistency * ref_loss
```

- [ ] **Step 3: Run a syntax check**

Run:

```bash
python -m py_compile train.py arguments/__init__.py utils/reflection_consistency.py
```

Expected: exit code 0.

### Task 4: Add Confidence-Aware TSDF Extraction

**Files:**
- Modify: `utils/mesh_utils.py`
- Test: `python -m py_compile utils/mesh_utils.py`

- [ ] **Step 1: Store confidence maps**

In `GaussianExtractor.clean()`, add `self.confmaps = []`.

In `reconstruction()`, after normals:

```python
normal_agree = (normal * depth_normal).sum(dim=0, keepdim=True).clamp(0.0, 1.0)
conf = alpha * normal_agree
self.confmaps.append(conf.cpu())
```

- [ ] **Step 2: Apply depth masking**

In `extract_mesh_bounded`, before making RGBD:

```python
if hasattr(self, "confmaps"):
    depth[self.confmaps[i] < conf_threshold] = 0
```

Add parameter:

```python
def extract_mesh_bounded(..., conf_threshold=0.0):
```

- [ ] **Step 3: Compile**

Run:

```bash
python -m py_compile utils/mesh_utils.py
```

Expected: exit code 0.

### Task 5: Evaluation Scripts

**Files:**
- Create: `metrics/reflection_consistency_eval.py`
- Create: `scripts/run_rc_refgs_ablation.sh`

- [ ] **Step 1: Implement reflection consistency metric**

Inputs:

```bash
python metrics/reflection_consistency_eval.py --model_path output/... --source_path /data/liuly/dataset/3DGS/refnerf/teapot --iteration 30000
```

Outputs JSON:

```json
{
  "mean_reflection_consistency": 0.0,
  "reflective_region_psnr": 0.0,
  "num_pairs": 0
}
```

- [ ] **Step 2: Add ablation runner**

Run baseline and proposed settings for `teapot`, `toaster`, `car` first:

```bash
conda run -n ref_gs python train.py -s /data/liuly/dataset/3DGS/refnerf/teapot -m output/rc_refgs/teapot_base
conda run -n ref_gs python train.py -s /data/liuly/dataset/3DGS/refnerf/teapot -m output/rc_refgs/teapot_rc --lambda_ref_consistency 0.02 --ref_consistency_start 3000
```

Expected: both runs train without runtime errors; evaluation JSON is produced.

## Verification Checklist

- [ ] Every paper claim in the writeup is tagged `[Citation]`.
- [ ] Every design decision not directly present in papers/code is tagged `[Reasoning]`.
- [ ] Every expected performance gain is tagged `[Hypothesis]`.
- [ ] Baseline Ref-GS and proposed runs use identical iterations, data splits, and seeds where possible.
- [ ] Report negative outcomes: if reflection consistency improves but mesh does not, do not claim mesh improvement.
- [ ] Do not claim material decomposition unless albedo/roughness diagnostics or relighting support it.
