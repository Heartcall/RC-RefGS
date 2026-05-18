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
    if cuda_device is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = cuda_device

_maybe_set_cuda_device(sys.argv)

import torch

from arguments import ModelParams, PipelineParams, get_combined_args
from gaussian_renderer import render
from scene import Scene, GaussianModel
from utils.general_utils import safe_state
from utils.reflection_consistency import choose_pair_camera, reflection_consistency_loss


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
):
    if split == "test":
        cameras = scene.getTestCameras(scale=1.0)
    else:
        cameras = scene.getTrainCameras(scale=1.0)

    if len(cameras) == 0:
        return {
            "mean_reflection_consistency": 0.0,
            "reflective_region_psnr": 0.0,
            "num_pairs": 0,
        }

    reflection_values = []
    reflective_psnr_values = []
    num_pairs = 0

    for src_cam in cameras:
        if max_pairs > 0 and num_pairs >= max_pairs:
            break
        tgt_cam = choose_pair_camera(cameras, src_cam, max_angle_deg=max_angle_deg)
        if tgt_cam is None:
            continue

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
    parser.add_argument("--cuda_device", type=str, default=None)
    parser.add_argument("--quiet", action="store_true")

    args = get_combined_args(parser)
    safe_state(args.quiet)

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
