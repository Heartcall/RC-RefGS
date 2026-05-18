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
from lpipsPyTorch import lpips
from scene import Scene, GaussianModel
from utils.general_utils import safe_state
from utils.image_utils import psnr
from utils.loss_utils import ssim


def composite_gt(camera, bg):
    gt = camera.original_image.cuda()
    if gt.shape[0] >= 4:
        return gt[:3, ...] * gt[3:, ...] + (1.0 - gt[3:, ...]) * bg[:, None, None]
    return gt[:3, ...]


def composite_prediction(render_pkg, bg, image_key):
    pred = render_pkg[image_key].clamp(0.0, 1.0)
    if image_key == "pbr_rgb" and "rend_alpha" in render_pkg:
        alpha = render_pkg["rend_alpha"].clamp(0.0, 1.0)
        pred = pred * alpha + (1.0 - alpha) * bg[:, None, None]
    return pred.clamp(0.0, 1.0)


def reflective_mask(render_pkg, alpha_threshold, roughness_threshold):
    alpha = render_pkg["rend_alpha"]
    roughness = render_pkg["roughness_map"]
    mask = (alpha > alpha_threshold) & (roughness < roughness_threshold)
    return mask.float()


def masked_image(pred, target, mask):
    mask = mask.float()
    return pred * mask, target * mask


def metric_bundle(pred, target, lpips_enabled=True, mask=None):
    if mask is not None:
        valid = float(mask.sum().item())
        if valid <= 0:
            return None
        pred, target = masked_image(pred, target, mask)

    pred_batch = pred[None, ...].contiguous().clamp(0.0, 1.0)
    target_batch = target[None, ...].contiguous().clamp(0.0, 1.0)
    values = {
        "psnr": float(psnr(pred_batch, target_batch).mean().item()),
        "ssim": float(ssim(pred_batch, target_batch).mean().item()),
        "lpips": None,
    }
    if lpips_enabled:
        # lpipsPyTorch expects tensors in [-1, 1].
        values["lpips"] = float(lpips(pred_batch * 2.0 - 1.0, target_batch * 2.0 - 1.0).mean().item())
    return values


def mean_metric(values, key):
    present = [item[key] for item in values if item is not None and item[key] is not None]
    if not present:
        return None
    return float(sum(present) / len(present))


@torch.no_grad()
def evaluate_cameras(
    cameras,
    gaussians,
    pipe,
    bg,
    iteration,
    max_images,
    image_key,
    mask_mode,
    alpha_threshold,
    roughness_threshold,
    skip_lpips,
):
    per_image = []
    full_values = []
    reflective_values = []

    selected_cameras = cameras if max_images <= 0 else cameras[:max_images]
    for camera in selected_cameras:
        render_pkg = render(camera, gaussians, pipe, bg, iteration=iteration)
        pred = composite_prediction(render_pkg, bg, image_key)
        target = composite_gt(camera, bg).clamp(0.0, 1.0)

        full_metrics = None
        if mask_mode in ("none", "both"):
            full_metrics = metric_bundle(pred, target, lpips_enabled=not skip_lpips)
            full_values.append(full_metrics)

        reflective_metrics = None
        if mask_mode in ("reflective", "both"):
            mask = reflective_mask(render_pkg, alpha_threshold, roughness_threshold)
            reflective_metrics = metric_bundle(pred, target, lpips_enabled=not skip_lpips, mask=mask)
            if reflective_metrics is not None:
                reflective_values.append(reflective_metrics)

        per_image.append(
            {
                "image_name": getattr(camera, "image_name", str(len(per_image))),
                "full": full_metrics,
                "reflective": reflective_metrics,
            }
        )

    return {
        "num_images": len(selected_cameras),
        "full_psnr": mean_metric(full_values, "psnr"),
        "full_ssim": mean_metric(full_values, "ssim"),
        "full_lpips": mean_metric(full_values, "lpips"),
        "reflective_psnr": mean_metric(reflective_values, "psnr"),
        "reflective_ssim": mean_metric(reflective_values, "ssim"),
        "reflective_lpips": mean_metric(reflective_values, "lpips"),
        "per_image": per_image,
    }


@torch.no_grad()
def evaluate(scene, gaussians, pipe, split, bg, args):
    splits = ["train", "test"] if split == "both" else [split]
    results = {}
    for split_name in splits:
        cameras = scene.getTestCameras(scale=1.0) if split_name == "test" else scene.getTrainCameras(scale=1.0)
        results[split_name] = evaluate_cameras(
            cameras=cameras,
            gaussians=gaussians,
            pipe=pipe,
            bg=bg,
            iteration=args.iteration,
            max_images=args.max_images,
            image_key=args.image_key,
            mask_mode=args.mask_mode,
            alpha_threshold=args.alpha_threshold,
            roughness_threshold=args.roughness_threshold,
            skip_lpips=args.skip_lpips,
        )
        torch.cuda.empty_cache()
    return results


def main():
    parser = ArgumentParser(description="Evaluate Ref-GS rendering quality metrics.")
    lp = ModelParams(parser, sentinel=True)
    pp = PipelineParams(parser)

    parser.add_argument("--iteration", type=int, default=-1)
    parser.add_argument("--split", choices=["train", "test", "both"], default="test")
    parser.add_argument("--max_images", type=int, default=-1)
    parser.add_argument("--mask_mode", choices=["none", "reflective", "both"], default="both")
    parser.add_argument("--image_key", choices=["pbr_rgb", "render"], default="pbr_rgb")
    parser.add_argument("--alpha_threshold", type=float, default=0.2)
    parser.add_argument("--roughness_threshold", type=float, default=0.6)
    parser.add_argument("--skip_lpips", action="store_true")
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

    loaded_iter = scene.loaded_iter if scene.loaded_iter is not None else args.iteration
    results = {
        "iteration": int(loaded_iter),
        "split": args.split,
        "image_key": args.image_key,
        "mask_mode": args.mask_mode,
        "lpips_skipped": bool(args.skip_lpips),
        "splits": evaluate(scene, gaussians, pipe, args.split, bg, args),
    }

    if args.output_json is None:
        args.output_json = os.path.join(dataset.model_path, f"render_quality_{args.split}_iter{loaded_iter}.json")

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))
    print(f"Saved render quality metrics to {args.output_json}")


if __name__ == "__main__":
    main()
