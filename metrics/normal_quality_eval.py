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
            return argv[index + 1]
    return os.environ.get("CUDA_VISIBLE_DEVICES", "2")


os.environ["CUDA_VISIBLE_DEVICES"] = _extract_cuda_device(sys.argv)

import torch
import torch.nn.functional as F
from PIL import Image

from arguments import ModelParams, PipelineParams, get_combined_args
from gaussian_renderer import render
from scene import Scene, GaussianModel
from utils.general_utils import PILtoTorch, safe_state


def convert_gt_normal_space(normal, camera, gt_normal_space):
    if gt_normal_space == "raw":
        return normal

    converted = normal.clone()
    if gt_normal_space == "blender_world_to_colmap":
        converted[1:3, ...] *= -1.0
        return F.normalize(converted, dim=0)

    if gt_normal_space == "opengl_camera_to_world":
        converted[1:3, ...] *= -1.0
        c2w = (camera.world_view_transform.T).inverse().to(device=normal.device, dtype=normal.dtype)
        normal_hw = converted.permute(1, 2, 0).reshape(-1, 3)
        world = normal_hw @ c2w[:3, :3].T
        world = world.reshape(normal.shape[1], normal.shape[2], 3).permute(2, 0, 1)
        return F.normalize(world, dim=0)

    raise ValueError(f"Unknown GT normal space: {gt_normal_space}")


def load_gt_normal(dataset, split_name, camera, normal_suffix, gt_normal_space):
    normal_path = os.path.join(dataset.source_path, split_name, camera.image_name + normal_suffix)
    if not os.path.exists(normal_path):
        return None, normal_path

    normal_image = Image.open(normal_path).convert("RGB")
    normal = PILtoTorch(normal_image, (camera.image_width, camera.image_height)).cuda()
    normal = normal[:3, ...] * 2.0 - 1.0
    normal = F.normalize(normal, dim=0)
    normal = convert_gt_normal_space(normal, camera, gt_normal_space)
    return normal, normal_path


def normal_angular_error(pred_normal, gt_normal, mask, eps=1e-6):
    valid = mask.float()
    count = valid.sum()
    if count <= 0:
        return None

    pred = F.normalize(pred_normal, dim=0)
    gt = F.normalize(gt_normal, dim=0)
    cosine = (pred * gt).sum(dim=0, keepdim=True).clamp(-1.0 + eps, 1.0 - eps)
    angle = torch.rad2deg(torch.acos(cosine))
    return float((angle * valid).sum().item() / count.item())


def normal_mean_cosine(pred_normal, gt_normal, mask):
    valid = mask.float()
    count = valid.sum()
    if count <= 0:
        return None

    pred = F.normalize(pred_normal, dim=0)
    gt = F.normalize(gt_normal, dim=0)
    cosine = (pred * gt).sum(dim=0, keepdim=True).clamp(-1.0, 1.0)
    return float((cosine * valid).sum().item() / count.item())


def mean_optional(values):
    present = [v for v in values if v is not None]
    if not present:
        return None
    return float(sum(present) / len(present))


@torch.no_grad()
def evaluate_cameras(
    dataset,
    cameras,
    gaussians,
    pipe,
    bg,
    split_name,
    iteration,
    max_images,
    normal_key,
    normal_suffix,
    gt_normal_space,
    alpha_threshold,
    roughness_threshold,
):
    selected_cameras = cameras if max_images <= 0 else cameras[:max_images]
    per_image = []
    normal_mae_values = []
    normal_cosine_values = []
    reflective_mae_values = []
    reflective_cosine_values = []
    num_missing_normals = 0

    for camera in selected_cameras:
        gt_normal, normal_path = load_gt_normal(dataset, split_name, camera, normal_suffix, gt_normal_space)
        if gt_normal is None:
            num_missing_normals += 1
            per_image.append(
                {
                    "image_name": camera.image_name,
                    "normal_path": normal_path,
                    "normal_mae_deg": None,
                    "normal_mean_cosine": None,
                    "reflective_normal_mae_deg": None,
                    "reflective_normal_mean_cosine": None,
                }
            )
            continue

        render_pkg = render(camera, gaussians, pipe, bg, iteration=iteration)
        pred_normal = render_pkg[normal_key]
        alpha = render_pkg["rend_alpha"] > alpha_threshold
        roughness = render_pkg["roughness_map"] < roughness_threshold

        normal_mae = normal_angular_error(pred_normal, gt_normal, alpha)
        normal_cosine = normal_mean_cosine(pred_normal, gt_normal, alpha)
        reflective_mae = normal_angular_error(pred_normal, gt_normal, alpha & roughness)
        reflective_cosine = normal_mean_cosine(pred_normal, gt_normal, alpha & roughness)

        normal_mae_values.append(normal_mae)
        normal_cosine_values.append(normal_cosine)
        reflective_mae_values.append(reflective_mae)
        reflective_cosine_values.append(reflective_cosine)
        per_image.append(
            {
                "image_name": camera.image_name,
                "normal_path": normal_path,
                "normal_mae_deg": normal_mae,
                "normal_mean_cosine": normal_cosine,
                "reflective_normal_mae_deg": reflective_mae,
                "reflective_normal_mean_cosine": reflective_cosine,
            }
        )

    return {
        "num_images": len(selected_cameras),
        "num_normal_images": len(selected_cameras) - num_missing_normals,
        "num_missing_normals": num_missing_normals,
        "normal_mae_deg": mean_optional(normal_mae_values),
        "normal_mean_cosine": mean_optional(normal_cosine_values),
        "reflective_normal_mae_deg": mean_optional(reflective_mae_values),
        "reflective_normal_mean_cosine": mean_optional(reflective_cosine_values),
        "per_image": per_image,
    }


@torch.no_grad()
def evaluate(scene, dataset, gaussians, pipe, split, bg, args):
    splits = ["train", "test"] if split == "both" else [split]
    results = {}
    for split_name in splits:
        cameras = scene.getTestCameras(scale=1.0) if split_name == "test" else scene.getTrainCameras(scale=1.0)
        results[split_name] = evaluate_cameras(
            dataset=dataset,
            cameras=cameras,
            gaussians=gaussians,
            pipe=pipe,
            bg=bg,
            split_name=split_name,
            iteration=args.iteration,
            max_images=args.max_images,
            normal_key=args.normal_key,
            normal_suffix=args.normal_suffix,
            gt_normal_space=args.gt_normal_space,
            alpha_threshold=args.alpha_threshold,
            roughness_threshold=args.roughness_threshold,
        )
        torch.cuda.empty_cache()
    return results


def main():
    parser = ArgumentParser(description="Evaluate diagnostic normal-map agreement metrics.")
    lp = ModelParams(parser, sentinel=True)
    pp = PipelineParams(parser)

    parser.add_argument("--iteration", type=int, default=-1)
    parser.add_argument("--split", choices=["train", "test", "both"], default="test")
    parser.add_argument("--max_images", type=int, default=-1)
    parser.add_argument("--normal_key", choices=["rend_normal", "surf_normal"], default="rend_normal")
    parser.add_argument("--normal_suffix", type=str, default="_normal.png")
    parser.add_argument(
        "--gt_normal_space",
        choices=["raw", "blender_world_to_colmap", "opengl_camera_to_world"],
        default="raw",
        help="Coordinate convention for encoded GT normal PNGs before comparison to rendered world normals.",
    )
    parser.add_argument("--alpha_threshold", type=float, default=0.2)
    parser.add_argument("--roughness_threshold", type=float, default=0.6)
    parser.add_argument("--output_json", type=str, default=None)
    parser.add_argument("--cuda_device", type=str, default="2")
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
        "normal_key": args.normal_key,
        "normal_suffix": args.normal_suffix,
        "gt_normal_space": args.gt_normal_space,
        "splits": evaluate(scene, dataset, gaussians, pipe, args.split, bg, args),
    }

    if args.output_json is None:
        args.output_json = os.path.join(dataset.model_path, f"normal_quality_{args.split}_iter{loaded_iter}.json")

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))
    print(f"Saved normal quality metrics to {args.output_json}")


if __name__ == "__main__":
    main()
