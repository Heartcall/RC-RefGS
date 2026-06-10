#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path


SHINY_SCENES = ["ball", "car", "coffee", "helmet", "teapot", "toaster"]
GLOSSY_SCENES = ["angel", "bell", "cat", "horse", "luyu", "potion", "tbell", "teapot"]
NON_SHINY_REAL_DATASETS = ("shiny_blender_synthetic", "glossy_synthetic")


def _exists(path):
    return path is not None and Path(path).exists()


def _count_matching(root, patterns, limit=100000):
    root = Path(root)
    if not root.exists():
        return 0
    count = 0
    for pattern in patterns:
        for _path in root.rglob(pattern):
            count += 1
            if count >= limit:
                return count
    return count


def _first_existing(root, names):
    root = Path(root)
    for name in names:
        path = root / name
        if path.exists():
            return str(path)
    return ""


def _resolve_scene(dataset, scene, shiny_root, glossy_root):
    if dataset == "shiny_blender_synthetic":
        return Path(shiny_root) / scene
    converted = Path(glossy_root) / f"{scene}_blender"
    if converted.exists():
        return converted
    return Path(glossy_root) / scene


def _model_dirs(output_roots, dataset, scene):
    dirs = []
    for output_root in output_roots:
        root = Path(output_root)
        scene_root = root / dataset / scene
        if not scene_root.exists():
            continue
        for variant_dir in scene_root.iterdir():
            seed_dir = variant_dir / "seed_0"
            if seed_dir.is_dir():
                dirs.append((variant_dir.name, seed_dir))
    return dirs


def inspect_scene(dataset, scene, scene_path, output_roots):
    normal_count = _count_matching(scene_path, ["*_normal.png", "*normal*.png"])
    depth_count = _count_matching(scene_path, ["*_depth.png", "*depth*.png", "*.exr"])
    gt_mesh = _first_existing(scene_path, ["mesh.obj", "mesh.ply", "gt_mesh.obj", "gt_mesh.ply"])
    init_points = _first_existing(scene_path, ["points3d.ply", "points.ply"])
    transforms_train = scene_path / "transforms_train.json"
    transforms_test = scene_path / "transforms_test.json"

    model_dirs = _model_dirs(output_roots, dataset, scene)
    rendered_depth = 0
    rendered_normal = 0
    point_clouds = 0
    reflective_metric_jsons = 0
    reflection_jsons = 0
    rc_valid_pair_fields = 0
    confidence_fields = 0
    angle_fields = 0
    for _variant, model_dir in model_dirs:
        if (model_dir / "point_cloud/iteration_31000/point_cloud.ply").exists():
            point_clouds += 1
        rendered_depth += _count_matching(model_dir, ["*depth*.png", "*depth*.npy", "*depth*.exr"])
        rendered_normal += _count_matching(model_dir, ["*normal*.png", "*normal*.npy"])
        rq = model_dir / "render_quality_both_iter31000.json"
        if rq.exists():
            try:
                data = json.loads(rq.read_text())
                if data.get("mask_mode") == "both":
                    reflective_metric_jsons += 1
            except json.JSONDecodeError:
                pass
        for rc_path in [model_dir / "reflection_consistency_train.json", model_dir / "reflection_consistency_test.json"]:
            if not rc_path.exists():
                continue
            reflection_jsons += 1
            try:
                rc_data = json.loads(rc_path.read_text())
            except json.JSONDecodeError:
                continue
            if "valid_pair_count" in rc_data:
                rc_valid_pair_fields += 1
            if any(key for key in rc_data if "confidence" in key.lower()):
                confidence_fields += 1
            if "max_angle_deg" in rc_data or any("angle" in key.lower() for key in rc_data):
                angle_fields += 1

    return {
        "dataset": dataset,
        "scene": scene,
        "scene_path": str(scene_path),
        "scene_path_exists": scene_path.exists(),
        "transforms_train_exists": transforms_train.exists(),
        "transforms_test_exists": transforms_test.exists(),
        "gt_depth_available": depth_count > 0,
        "gt_depth_file_count": depth_count,
        "gt_normal_available": normal_count > 0,
        "gt_normal_file_count": normal_count,
        "gt_mesh_available": bool(gt_mesh),
        "gt_mesh_path": gt_mesh,
        "gt_point_cloud_available": False,
        "gt_point_cloud_path": "",
        "initialization_point_cloud_available": bool(init_points),
        "initialization_point_cloud_path": init_points,
        "model_output_count": len(model_dirs),
        "rendered_depth_available": rendered_depth > 0,
        "rendered_depth_file_count": rendered_depth,
        "rendered_normal_available": rendered_normal > 0,
        "rendered_normal_file_count": rendered_normal,
        "final_point_cloud_available": point_clouds > 0,
        "final_point_cloud_count": point_clouds,
        "reflective_mask_available": False,
        "reflective_region_metrics_available": reflective_metric_jsons > 0,
        "reflection_consistency_json_count": reflection_jsons,
        "rc_valid_correspondence_fields_available": rc_valid_pair_fields > 0,
        "rc_valid_correspondence_field_count": rc_valid_pair_fields,
        "confidence_fields_available": confidence_fields > 0,
        "pair_angle_fields_available": angle_fields > 0,
        "normal_stability_fields_available": False,
    }


def build_inventory(args):
    output_roots = [Path(item) for item in args.output_roots]
    requested = set(args.scenes or SHINY_SCENES + GLOSSY_SCENES)
    rows = []
    for scene in SHINY_SCENES:
        if scene in requested:
            path = _resolve_scene("shiny_blender_synthetic", scene, args.shiny_blender_synthetic_root, args.glossy_synthetic_root)
            rows.append(inspect_scene("shiny_blender_synthetic", scene, path, output_roots))
    for scene in GLOSSY_SCENES:
        if scene in requested:
            path = _resolve_scene("glossy_synthetic", scene, args.shiny_blender_synthetic_root, args.glossy_synthetic_root)
            rows.append(inspect_scene("glossy_synthetic", scene, path, output_roots))

    any_gt_depth_and_render = any(r["gt_depth_available"] and r["rendered_depth_available"] for r in rows)
    any_gt_normal_and_render = any(r["gt_normal_available"] and r["rendered_normal_available"] for r in rows)
    any_gt_mesh_and_prediction = any(r["gt_mesh_available"] and r["final_point_cloud_available"] for r in rows)
    any_point_cloud_proxy = any(r["final_point_cloud_available"] for r in rows)

    return {
        "mode": "rc_refgs_geometry_signal_inventory",
        "datasets": list(NON_SHINY_REAL_DATASETS),
        "scene_count": len(rows),
        "rows": rows,
        "possible_now": [
            item
            for item, possible in [
                ("geometry_proxy_metrics_available_now", any_point_cloud_proxy),
                ("reflection_rgb_correlation_from_existing_json", True),
            ]
            if possible
        ],
        "unavailable_now": {
            "true_depth_metrics": not any_gt_depth_and_render,
            "true_normal_metrics": not any_gt_normal_and_render,
            "true_mesh_metrics": not any_gt_mesh_and_prediction,
        },
        "requires_additional_render_or_export": [
            "rendered depth buffers for depth error",
            "rendered normal buffers with verified coordinate space for normal error",
            "extracted predicted meshes plus GT geometry for Chamfer/F-score",
            "saved reflective masks if region-specific geometry metrics are required",
        ],
        "requires_code_changes": [
            "non-invasive RC correspondence diagnostics for pair-angle/confidence distributions",
            "depth/normal export or evaluator rendering path if true geometry metrics are needed",
        ],
        "raw_glossy_policy": "Converted GlossySynthetic root is used for scene discovery; raw GlossySynthetic is not used as a train source.",
        "claim_boundary": "Inventory only; no geometry metric values or surface-improvement claims.",
    }


def write_outputs(report, output_json, output_csv, output_md):
    Path(output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(output_json).write_text(json.dumps(report, indent=2) + "\n")
    if output_csv:
        fieldnames = list(report["rows"][0].keys()) if report["rows"] else ["dataset", "scene"]
        with open(output_csv, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report["rows"])
    if output_md:
        lines = [
            "# RC-RefGS Geometry Signal Inventory",
            "",
            f"Scenes inspected: `{report['scene_count']}`.",
            "",
            "## Possible Now",
            "",
        ]
        for item in report["possible_now"]:
            lines.append(f"- `{item}`")
        lines += ["", "## Unavailable Now", ""]
        for key, unavailable in report["unavailable_now"].items():
            lines.append(f"- `{key}`: {'unavailable' if unavailable else 'available'}")
        lines += ["", "## Required Next Instrumentation", ""]
        for item in report["requires_additional_render_or_export"]:
            lines.append(f"- {item}")
        lines += ["", "## Claim Boundary", "", report["claim_boundary"], ""]
        Path(output_md).write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Inspect non-Shiny-Real RC-RefGS geometry signal availability.")
    parser.add_argument("--shiny_blender_synthetic_root", default="/data/liuly/dataset/3DGS/Shiny Blender Synthetic")
    parser.add_argument("--glossy_synthetic_root", default="/data/liuly/dataset/3DGS/GlossySyntheticConverted")
    parser.add_argument("--output_roots", nargs="+", default=[])
    parser.add_argument("--scenes", nargs="*", default=None)
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--output_csv")
    parser.add_argument("--output_md")
    args = parser.parse_args()

    report = build_inventory(args)
    write_outputs(report, args.output_json, args.output_csv, args.output_md)
    print(json.dumps({"scene_count": report["scene_count"], "possible_now": report["possible_now"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
