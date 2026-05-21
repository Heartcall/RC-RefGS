import math

import torch
import torch.nn.functional as F


def _camera_center(camera):
    center = getattr(camera, "camera_center", None)
    if center is None:
        return None
    return torch.as_tensor(center, dtype=torch.float32)


def _camera_forward(camera):
    rays_d = getattr(camera, "rays_d", None)
    if rays_d is not None:
        h = int(getattr(camera, "image_height")) // 2
        w = int(getattr(camera, "image_width")) // 2
        return F.normalize(rays_d[h, w].detach().float().cpu(), dim=0)
    return torch.tensor([0.0, 0.0, 1.0], dtype=torch.float32)


def _angle_deg(a, b, eps=1e-8):
    a_norm = torch.linalg.norm(a)
    b_norm = torch.linalg.norm(b)
    if a_norm < eps or b_norm < eps:
        return None
    cos = torch.clamp(torch.dot(a / a_norm, b / b_norm), -1.0, 1.0)
    return float(torch.rad2deg(torch.acos(cos)))


def choose_pair_camera(viewpoint_stack, current_cam, max_angle_deg=20.0):
    current_center = _camera_center(current_cam)
    if current_center is None:
        return None

    candidates = []
    for candidate in viewpoint_stack:
        if candidate is current_cam:
            continue
        candidate_center = _camera_center(candidate)
        if candidate_center is None:
            continue

        angle = _angle_deg(current_center, candidate_center)
        if angle is None:
            angle = _angle_deg(_camera_forward(current_cam), candidate_center - current_center)
        if angle is None or angle > max_angle_deg:
            continue

        distance = torch.linalg.norm(candidate_center - current_center).item()
        candidates.append((angle, distance, candidate))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2]


def backproject_depth(view, depth):
    if depth.ndim == 3:
        depth = depth[0]
    device = depth.device
    dtype = depth.dtype
    c2w = (view.world_view_transform.to(device=device, dtype=dtype).T).inverse()

    width = int(view.image_width)
    height = int(view.image_height)
    fx = width / (2.0 * math.tan(float(view.FoVx) / 2.0))
    fy = height / (2.0 * math.tan(float(view.FoVy) / 2.0))

    grid_x, grid_y = torch.meshgrid(
        torch.arange(width, device=device, dtype=dtype),
        torch.arange(height, device=device, dtype=dtype),
        indexing="xy",
    )
    pixels = torch.stack(
        [
            (grid_x - width / 2.0) / fx,
            (grid_y - height / 2.0) / fy,
            torch.ones_like(grid_x),
        ],
        dim=-1,
    ).reshape(-1, 3)

    rays_d = pixels @ c2w[:3, :3].T
    rays_o = c2w[:3, 3]
    return depth.reshape(-1, 1) * rays_d + rays_o


def project_points(view, points_world):
    device = points_world.device
    dtype = points_world.dtype
    transform = view.full_proj_transform.to(device=device, dtype=dtype)
    points_h = torch.cat([points_world, torch.ones_like(points_world[..., :1])], dim=-1)
    projected = points_h @ transform
    depth = projected[..., -1:]
    grid = projected[..., :2] / depth.clamp_min(torch.finfo(dtype).eps)
    valid = ((grid > -1.0) & (grid < 1.0) & (depth > 0)).all(dim=-1)
    return grid, depth, valid


def _sample_map(image, grid):
    return F.grid_sample(
        image[None],
        grid[None, :, None, :],
        mode="bilinear",
        padding_mode="border",
        align_corners=True,
    )[0, :, :, 0].T


def _require_render_keys(render_pkg, keys, package_name):
    for key in keys:
        if key not in render_pkg:
            raise KeyError(f"{package_name} render package missing required key: {key}")


def reflection_consistency_loss(
    src_pkg,
    tgt_pkg,
    src_cam,
    tgt_cam,
    gamma=2.0,
    alpha_threshold=0.2,
    roughness_threshold=0.6,
    depth_tolerance=0.02,
):
    _require_render_keys(
        src_pkg,
        (
            "spec_light",
            "rend_alpha",
            "roughness_map",
            "surf_depth",
            "rend_normal",
            "surf_normal",
        ),
        "source",
    )
    _require_render_keys(
        tgt_pkg,
        (
            "spec_light",
            "rend_alpha",
            "surf_depth",
        ),
        "target",
    )

    spec_src = src_pkg["spec_light"]
    spec_tgt = tgt_pkg["spec_light"]
    depth_src = src_pkg["surf_depth"]

    points = backproject_depth(src_cam, depth_src)
    grid, projected_depth, valid = project_points(tgt_cam, points)

    sampled_spec = _sample_map(spec_tgt, grid)
    sampled_alpha = _sample_map(tgt_pkg["rend_alpha"], grid)[:, :1]
    sampled_depth = _sample_map(tgt_pkg["surf_depth"], grid)[:, :1]

    src_spec = spec_src.reshape(spec_src.shape[0], -1).T
    src_alpha = src_pkg["rend_alpha"].reshape(1, -1).T
    src_roughness = src_pkg["roughness_map"].reshape(1, -1).T

    src_normal_agree = (
        src_pkg["rend_normal"] * src_pkg["surf_normal"]
    ).sum(dim=0, keepdim=True).reshape(1, -1).T.clamp(0.0, 1.0)

    depth_scale = projected_depth.abs().clamp_min(1.0)
    depth_ok = (sampled_depth - projected_depth).abs() <= depth_tolerance * depth_scale
    spec_conf = src_spec.mean(dim=-1, keepdim=True).clamp(0.0, 1.0) * (
        1.0 - src_roughness.clamp(0.0, 1.0)
    ).pow(gamma)

    mask = (
        valid[:, None]
        & depth_ok
        & (src_alpha > alpha_threshold)
        & (sampled_alpha > alpha_threshold)
        & (src_roughness < roughness_threshold)
        & (src_normal_agree > 0.0)
    )

    weight = mask.float() * src_alpha * sampled_alpha * src_normal_agree * spec_conf
    weight_sum = weight.sum()
    if weight_sum <= 0:
        return spec_src.new_zeros(())

    residual = (src_spec.detach() - sampled_spec).abs().mean(dim=-1, keepdim=True)
    return (residual * weight).sum() / weight_sum
