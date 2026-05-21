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


MATERIAL_SUMMARY_KEYS = (
    "full_diffuse_variance",
    "full_roughness_variance",
    "full_specular_variance",
    "full_specular_diffuse_ratio",
    "reflective_diffuse_variance",
    "reflective_roughness_variance",
    "reflective_specular_variance",
    "reflective_specular_diffuse_ratio",
)


def _cuda_device_index(cuda_device):
    if cuda_device is None:
        return 0
    cuda_device = cuda_device.strip()
    if not cuda_device or cuda_device.lower() in {"auto", "none"}:
        return 0
    return int(cuda_device.split(",", 1)[0])


def mean_optional(values):
    present = [v for v in values if v is not None]
    if not present:
        return None
    return float(sum(present) / len(present))


def tensor_variance(values):
    if values.numel() <= 0:
        return None
    return float(values.float().var(unbiased=False).item())


def tensor_mean(values):
    if values.numel() <= 0:
        return None
    return float(values.float().mean().item())


def masked_values(tensor, mask):
    mask = mask.bool()
    if tensor.shape[0] > 1:
        mask = mask.expand(tensor.shape[0], -1, -1)
    return tensor[mask]


def material_stats(render_pkg, mask):
    diffuse = masked_values(render_pkg["diff_light"], mask)
    roughness = masked_values(render_pkg["roughness_map"], mask)
    specular = masked_values(render_pkg["spec_light"], mask)

    specular_mean = tensor_mean(specular)
    diffuse_mean = tensor_mean(diffuse)
    if specular_mean is None or diffuse_mean is None or diffuse_mean <= 1e-8:
        specular_diffuse_ratio = None
    else:
        specular_diffuse_ratio = float(specular_mean / diffuse_mean)

    return {
        "num_pixels": int(mask.sum().item()),
        "diffuse_mean": diffuse_mean,
        "diffuse_variance": tensor_variance(diffuse),
        "roughness_mean": tensor_mean(roughness),
        "roughness_variance": tensor_variance(roughness),
        "specular_mean": specular_mean,
        "specular_variance": tensor_variance(specular),
        "specular_diffuse_ratio": specular_diffuse_ratio,
    }


def prefixed_stats(prefix, stats):
    return {
        f"{prefix}_diffuse_mean": stats["diffuse_mean"],
        f"{prefix}_diffuse_variance": stats["diffuse_variance"],
        f"{prefix}_roughness_mean": stats["roughness_mean"],
        f"{prefix}_roughness_variance": stats["roughness_variance"],
        f"{prefix}_specular_mean": stats["specular_mean"],
        f"{prefix}_specular_variance": stats["specular_variance"],
        f"{prefix}_specular_diffuse_ratio": stats["specular_diffuse_ratio"],
    }


def mean_prefixed(per_image, key):
    return mean_optional([image.get(key) for image in per_image])


@torch.no_grad()
def evaluate_cameras(
    cameras,
    gaussians,
    pipe,
    bg,
    iteration,
    max_images,
    mask_mode,
    alpha_threshold,
    roughness_threshold,
):
    selected_cameras = cameras if max_images <= 0 else cameras[:max_images]
    per_image = []

    for camera in selected_cameras:
        render_pkg = render(camera, gaussians, pipe, bg, iteration=iteration)
        alpha_mask = render_pkg["rend_alpha"] > alpha_threshold
        reflective_mask = alpha_mask & (render_pkg["roughness_map"] < roughness_threshold)

        image_stats = {
            "image_name": getattr(camera, "image_name", str(len(per_image))),
            "num_full_pixels": int(alpha_mask.sum().item()),
            "num_reflective_pixels": int(reflective_mask.sum().item()),
        }
        if mask_mode in ("none", "both"):
            image_stats.update(prefixed_stats("full", material_stats(render_pkg, alpha_mask)))
        if mask_mode in ("reflective", "both"):
            image_stats.update(prefixed_stats("reflective", material_stats(render_pkg, reflective_mask)))
        per_image.append(image_stats)

    summary = {
        "num_images": len(selected_cameras),
        "num_reflective_pixels": int(sum(image["num_reflective_pixels"] for image in per_image)),
        "per_image": per_image,
    }
    for prefix in ("full", "reflective"):
        for key in (
            "diffuse_mean",
            "diffuse_variance",
            "roughness_mean",
            "roughness_variance",
            "specular_mean",
            "specular_variance",
            "specular_diffuse_ratio",
        ):
            summary[f"{prefix}_{key}"] = mean_prefixed(per_image, f"{prefix}_{key}")
    return summary


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
            mask_mode=args.mask_mode,
            alpha_threshold=args.alpha_threshold,
            roughness_threshold=args.roughness_threshold,
        )
        torch.cuda.empty_cache()
    return results


def main():
    parser = ArgumentParser(description="Evaluate diagnostic material-map variance metrics.")
    lp = ModelParams(parser, sentinel=True)
    pp = PipelineParams(parser)

    parser.add_argument("--iteration", type=int, default=-1)
    parser.add_argument("--split", choices=["train", "test", "both"], default="test")
    parser.add_argument("--max_images", type=int, default=-1)
    parser.add_argument("--mask_mode", choices=["none", "reflective", "both"], default="both")
    parser.add_argument("--alpha_threshold", type=float, default=0.2)
    parser.add_argument("--roughness_threshold", type=float, default=0.6)
    parser.add_argument("--output_json", type=str, default=None)
    parser.add_argument("--cuda_device", type=str, default=None)
    parser.add_argument("--quiet", action="store_true")

    args = get_combined_args(parser)
    safe_state(args.quiet, cuda_device=_cuda_device_index(args.cuda_device))

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
        "mask_mode": args.mask_mode,
        "splits": evaluate(scene, gaussians, pipe, args.split, bg, args),
    }

    if args.output_json is None:
        args.output_json = os.path.join(dataset.model_path, f"material_quality_{args.split}_iter{loaded_iter}.json")

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))
    print(f"Saved material quality metrics to {args.output_json}")


if __name__ == "__main__":
    main()
