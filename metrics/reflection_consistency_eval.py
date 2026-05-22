import json
import os
import sys
from argparse import ArgumentParser

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def _extract_cuda_device(argv):
    if "--cuda_device" in argv:
        index = argv.index("--cuda_device")
        if index + 1 < len(argv):
            value = argv[index + 1].strip()
            if value and value.lower() not in {"auto", "none"}:
                return value
            return None
    current = os.environ.get("CUDA_VISIBLE_DEVICES")
    if current is not None:
        current = current.strip()
        if current:
            return current
    return None

def _maybe_set_cuda_device(argv):
    cuda_device = _extract_cuda_device(argv)
    if cuda_device is not None and os.environ.get("RC_REF_GS_FILTER_CUDA_VISIBLE_DEVICES") == "1":
        os.environ["CUDA_VISIBLE_DEVICES"] = cuda_device

_maybe_set_cuda_device(sys.argv)

import torch

from arguments import ModelParams, PipelineParams, get_combined_args
from gaussian_renderer import render
from scene import Scene, GaussianModel
from utils.general_utils import safe_state
from utils.reflection_consistency import choose_pair_camera, reflection_consistency_loss


def _cuda_device_index(cuda_device):
    if cuda_device is None:
        return 0
    cuda_device = cuda_device.strip()
    if not cuda_device or cuda_device.lower() in {"auto", "none"}:
        return 0
    return int(cuda_device.split(",", 1)[0])


def masked_psnr(pred, target, mask, eps=1e-8):
    mask = mask.float()
    valid = mask.sum()
    if valid <= 0:
        return None
    mse = ((pred - target) ** 2 * mask).sum() / (valid * pred.shape[0]).clamp_min(1.0)
    mse = mse.clamp_min(eps)
    return float((-10.0 * torch.log10(mse)).item())


def reflective_region_psnr(render_pkg, camera, bg_color, alpha_threshold=0.2, roughness_threshold=0.6):
    alpha = render_pkg["rend_alpha"]
    roughness = render_pkg["roughness_map"]
    pred = render_pkg["pbr_rgb"] * alpha + (1.0 - alpha) * bg_color[:, None, None]

    gt = camera.original_image.cuda()
    target = gt[:3, ...] * gt[3:, ...] + (1.0 - gt[3:, ...]) * bg_color[:, None, None]
    mask = (alpha > alpha_threshold) & (roughness < roughness_threshold)
    return masked_psnr(pred, target, mask)


def _load_pair_list(pair_list_json):
    if pair_list_json is None:
        return None
    with open(pair_list_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("pairs", [])
    if not isinstance(data, list):
        raise ValueError("pair-list JSON must be a list or an object with a 'pairs' list")

    pairs = []
    for index, item in enumerate(data):
        if isinstance(item, dict):
            source = item.get("source", item.get("src"))
            target = item.get("target", item.get("tgt"))
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            source, target = item
        else:
            raise ValueError(f"pair-list entry {index} must be [source, target] or an object")

        if source is None or target is None:
            raise ValueError(f"pair-list entry {index} is missing source or target")
        pairs.append((str(source), str(target)))
    return pairs


def _camera_lookup(cameras):
    lookup = {}
    for camera in cameras:
        for attr_name in ("image_name", "uid", "colmap_id"):
            value = getattr(camera, attr_name, None)
            if value is not None:
                lookup[str(value)] = camera
    return lookup


def _resolve_pair_list(cameras, pair_specs):
    lookup = _camera_lookup(cameras)
    pairs = []
    for source_key, target_key in pair_specs:
        if source_key not in lookup:
            raise ValueError(f"source camera '{source_key}' from pair list was not found in split")
        if target_key not in lookup:
            raise ValueError(f"target camera '{target_key}' from pair list was not found in split")
        pairs.append((lookup[source_key], lookup[target_key]))
    return pairs


@torch.no_grad()
def evaluate(
    scene,
    gaussians,
    pipe,
    split,
    iteration,
    max_pairs,
    max_angle_deg,
    gamma,
    alpha_threshold,
    roughness_threshold,
    bg,
    pair_specs=None,
):
    if split == "test":
        cameras = scene.getTestCameras(scale=1.0)
    else:
        cameras = scene.getTrainCameras(scale=1.0)

    if isinstance(pair_specs, str):
        pair_specs = _load_pair_list(pair_specs)
    pair_mode = "fixed" if pair_specs is not None else "dynamic"
    requested_pair_count = len(pair_specs) if pair_specs is not None else 0

    if len(cameras) == 0:
        return {
            "mean_reflection_consistency": 0.0,
            "reflective_region_psnr": 0.0,
            "num_pairs": 0,
            "pair_mode": pair_mode,
            "max_pairs": int(max_pairs),
            "max_angle_deg": float(max_angle_deg),
            "valid_pair_count": 0,
            "requested_pair_count": int(requested_pair_count),
        }

    reflection_values = []
    reflective_psnr_values = []
    num_pairs = 0

    if pair_specs is None:
        eval_pairs = []
        for src_cam in cameras:
            tgt_cam = choose_pair_camera(cameras, src_cam, max_angle_deg=max_angle_deg)
            if tgt_cam is not None:
                eval_pairs.append((src_cam, tgt_cam))
    else:
        eval_pairs = _resolve_pair_list(cameras, pair_specs)

    for src_cam, tgt_cam in eval_pairs:
        if max_pairs > 0 and num_pairs >= max_pairs:
            break

        src_pkg = render(src_cam, gaussians, pipe, bg, iteration=iteration)
        tgt_pkg = render(tgt_cam, gaussians, pipe, bg, iteration=iteration)

        ref_value = reflection_consistency_loss(src_pkg, tgt_pkg, src_cam, tgt_cam, gamma=gamma)
        reflection_values.append(float(ref_value.item()))

        region_psnr = reflective_region_psnr(
            src_pkg,
            src_cam,
            bg,
            alpha_threshold=alpha_threshold,
            roughness_threshold=roughness_threshold,
        )
        if region_psnr is not None:
            reflective_psnr_values.append(region_psnr)
        num_pairs += 1

    mean_reflection = sum(reflection_values) / len(reflection_values) if reflection_values else 0.0
    mean_reflective_psnr = (
        sum(reflective_psnr_values) / len(reflective_psnr_values) if reflective_psnr_values else 0.0
    )

    return {
        "mean_reflection_consistency": float(mean_reflection),
        "reflective_region_psnr": float(mean_reflective_psnr),
        "num_pairs": int(num_pairs),
        "pair_mode": pair_mode,
        "max_pairs": int(max_pairs),
        "max_angle_deg": float(max_angle_deg),
        "valid_pair_count": int(num_pairs),
        "requested_pair_count": int(requested_pair_count),
    }


def main():
    parser = ArgumentParser(description="Evaluate RC-RefGS reflection consistency.")
    lp = ModelParams(parser, sentinel=True)
    pp = PipelineParams(parser)

    parser.add_argument("--iteration", type=int, default=-1)
    parser.add_argument("--split", choices=["train", "test"], default="test")
    parser.add_argument("--max_pairs", type=int, default=50)
    parser.add_argument("--max_angle_deg", type=float, default=20.0)
    parser.add_argument("--gamma", type=float, default=2.0)
    parser.add_argument("--alpha_threshold", type=float, default=0.2)
    parser.add_argument("--roughness_threshold", type=float, default=0.6)
    parser.add_argument("--output_json", type=str, default=None)
    parser.add_argument("--pair_list_json", type=str, default=None)
    parser.add_argument("--cuda_device", type=str, default=None)
    parser.add_argument("--quiet", action="store_true")

    args = get_combined_args(parser)
    safe_state(args.quiet, cuda_device=_cuda_device_index(args.cuda_device))
    pair_list_json = getattr(args, "pair_list_json", None)

    dataset = lp.extract(args)
    pipe = pp.extract(args)
    gaussians = GaussianModel(dataset.sh_degree, dataset)
    scene = Scene(dataset, gaussians, load_iteration=args.iteration, shuffle=False, resolution_scales=[1.0])
    bg_color = [1.0, 1.0, 1.0] if dataset.white_background else [0.0, 0.0, 0.0]
    bg = torch.tensor(bg_color, dtype=torch.float32, device="cuda")

    results = evaluate(
        scene=scene,
        gaussians=gaussians,
        pipe=pipe,
        split=args.split,
        iteration=args.iteration,
        max_pairs=args.max_pairs,
        max_angle_deg=args.max_angle_deg,
        gamma=args.gamma,
        alpha_threshold=args.alpha_threshold,
        roughness_threshold=args.roughness_threshold,
        bg=bg,
        pair_specs=pair_list_json,
    )

    loaded_iter = scene.loaded_iter if scene.loaded_iter is not None else args.iteration
    if args.output_json is None:
        args.output_json = os.path.join(
            dataset.model_path,
            f"reflection_consistency_{args.split}_iter{loaded_iter}.json",
        )

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))
    print(f"Saved reflection consistency metrics to {args.output_json}")


if __name__ == "__main__":
    main()
