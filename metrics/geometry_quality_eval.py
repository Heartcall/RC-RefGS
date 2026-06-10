#!/usr/bin/env python3
import argparse
import csv
import json
import math
import struct
from pathlib import Path


DATASETS = ("shiny_blender_synthetic", "glossy_synthetic")
LOWER_BETTER = {"mean_reflection_consistency", "full_lpips", "reflective_lpips"}
QUALITY_METRICS = [
    "full_psnr",
    "full_ssim",
    "full_lpips",
    "reflective_psnr",
    "reflective_ssim",
    "reflective_lpips",
]
BASE_FIELDS = [
    "dataset",
    "scene",
    "variant",
    "model_path",
    "status",
    "true_depth_metrics_computed",
    "true_normal_metrics_computed",
    "true_mesh_metrics_computed",
    "geometry_proxy_vertex_count",
    "geometry_proxy_input_vertex_count",
    "geometry_proxy_vertex_count_delta_from_input",
    "geometry_proxy_bbox_diag",
    "mean_reflection_consistency",
    "full_psnr",
    "full_ssim",
    "full_lpips",
    "reflective_psnr",
    "reflective_ssim",
    "reflective_lpips",
    "unavailable_reasons",
]


PLY_TYPE_FORMATS = {
    "char": "b",
    "uchar": "B",
    "int8": "b",
    "uint8": "B",
    "short": "h",
    "ushort": "H",
    "int16": "h",
    "uint16": "H",
    "int": "i",
    "uint": "I",
    "int32": "i",
    "uint32": "I",
    "float": "f",
    "float32": "f",
    "double": "d",
    "float64": "d",
}


def _load_json(path):
    path = Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def _parse_ply_header(path):
    with open(path, "rb") as handle:
        header_lines = []
        while True:
            line = handle.readline()
            if not line:
                raise ValueError(f"PLY header missing end_header: {path}")
            decoded = line.decode("utf-8", errors="replace").strip()
            header_lines.append(decoded)
            if decoded == "end_header":
                break
        data_offset = handle.tell()

    fmt = None
    vertex_count = 0
    vertex_properties = []
    in_vertex = False
    for line in header_lines:
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "format":
            fmt = parts[1]
        elif len(parts) >= 3 and parts[0] == "element":
            in_vertex = parts[1] == "vertex"
            if in_vertex:
                vertex_count = int(parts[2])
        elif in_vertex and len(parts) >= 3 and parts[0] == "property" and parts[1] != "list":
            vertex_properties.append((parts[2], parts[1]))
        elif in_vertex and len(parts) >= 3 and parts[0] == "property" and parts[1] == "list":
            raise ValueError("List properties in vertex records are not supported for proxy parsing.")
    return fmt, vertex_count, vertex_properties, data_offset


def load_ply_proxy(path):
    path = Path(path)
    if not path.exists():
        return {"exists": False, "vertex_count": None, "bbox_diag": None}

    fmt, vertex_count, properties, data_offset = _parse_ply_header(path)
    result = {"exists": True, "vertex_count": int(vertex_count), "bbox_diag": None}
    if vertex_count <= 0:
        return result

    prop_names = [name for name, _type in properties]
    if not all(axis in prop_names for axis in ("x", "y", "z")):
        return result

    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    if fmt == "ascii":
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if line.strip() == "end_header":
                    break
            for _ in range(vertex_count):
                parts = handle.readline().strip().split()
                if len(parts) < len(properties):
                    break
                xyz = [float(parts[prop_names.index(axis)]) for axis in ("x", "y", "z")]
                for index, value in enumerate(xyz):
                    mins[index] = min(mins[index], value)
                    maxs[index] = max(maxs[index], value)
    elif fmt == "binary_little_endian":
        struct_fmt = "<" + "".join(PLY_TYPE_FORMATS[prop_type] for _name, prop_type in properties)
        record_size = struct.calcsize(struct_fmt)
        x_index, y_index, z_index = [prop_names.index(axis) for axis in ("x", "y", "z")]
        with open(path, "rb") as handle:
            handle.seek(data_offset)
            for _ in range(vertex_count):
                blob = handle.read(record_size)
                if len(blob) != record_size:
                    break
                values = struct.unpack(struct_fmt, blob)
                xyz = [float(values[x_index]), float(values[y_index]), float(values[z_index])]
                for index, value in enumerate(xyz):
                    mins[index] = min(mins[index], value)
                    maxs[index] = max(maxs[index], value)
    else:
        return result

    if all(math.isfinite(value) for value in mins + maxs):
        result["bbox_min"] = mins
        result["bbox_max"] = maxs
        result["bbox_diag"] = float(math.sqrt(sum((maxs[i] - mins[i]) ** 2 for i in range(3))))
    return result


def _find_model_dirs(model_roots, scenes, variants):
    wanted_scenes = set(scenes or [])
    wanted_variants = set(variants or [])
    for root in model_roots:
        root = Path(root)
        for dataset in DATASETS:
            dataset_root = root / dataset
            if not dataset_root.exists():
                continue
            for scene_dir in dataset_root.iterdir():
                if not scene_dir.is_dir():
                    continue
                if wanted_scenes and scene_dir.name not in wanted_scenes:
                    continue
                for variant_dir in scene_dir.iterdir():
                    if not variant_dir.is_dir():
                        continue
                    if wanted_variants and variant_dir.name not in wanted_variants:
                        continue
                    seed_dir = variant_dir / "seed_0"
                    if seed_dir.is_dir():
                        yield dataset, scene_dir.name, variant_dir.name, seed_dir


def _render_metrics(model_path):
    data = _load_json(model_path / "render_quality_both_iter31000.json")
    split = data.get("splits", {}).get("test", {})
    return {metric: split.get(metric) for metric in QUALITY_METRICS}


def _reflection_metric(model_path):
    data = _load_json(model_path / "reflection_consistency_test.json")
    return data.get("mean_reflection_consistency")


def evaluate_model_geometry(dataset, scene, variant, model_path, iteration=31000):
    model_path = Path(model_path)
    point_path = model_path / f"point_cloud/iteration_{iteration}/point_cloud.ply"
    input_path = model_path / "input.ply"
    point_proxy = load_ply_proxy(point_path)
    input_proxy = load_ply_proxy(input_path)
    reasons = [
        "missing_gt_depth",
        "missing_rendered_depth_buffers",
        "missing_rendered_normal_buffers",
        "normal_coordinate_space_unverified",
        "missing_gt_mesh_or_point_cloud",
        "predicted_mesh_not_extracted",
    ]
    row = {
        "dataset": dataset,
        "scene": scene,
        "variant": variant,
        "model_path": str(model_path),
        "status": "proxy_only" if point_proxy["exists"] else "missing_point_cloud",
        "true_depth_metrics_computed": False,
        "true_normal_metrics_computed": False,
        "true_mesh_metrics_computed": False,
        "geometry_proxy_vertex_count": point_proxy.get("vertex_count"),
        "geometry_proxy_input_vertex_count": input_proxy.get("vertex_count"),
        "geometry_proxy_vertex_count_delta_from_input": None,
        "geometry_proxy_bbox_diag": point_proxy.get("bbox_diag"),
        "mean_reflection_consistency": _reflection_metric(model_path),
        "unavailable_reasons": reasons,
    }
    if row["geometry_proxy_vertex_count"] is not None and row["geometry_proxy_input_vertex_count"] is not None:
        row["geometry_proxy_vertex_count_delta_from_input"] = (
            row["geometry_proxy_vertex_count"] - row["geometry_proxy_input_vertex_count"]
        )
    row.update(_render_metrics(model_path))
    return row


def _pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 2:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return float(num / (den_x * den_y))


def _wins(value, reference, metric):
    if value is None or reference is None:
        return None
    return value < reference if metric in LOWER_BETTER else value > reference


def build_report(args):
    rows = [
        evaluate_model_geometry(dataset, scene, variant, model_path, args.iteration)
        for dataset, scene, variant, model_path in _find_model_dirs(args.model_roots, args.scenes, args.variants)
    ]
    rows.sort(key=lambda row: (row["dataset"], row["scene"], row["variant"]))

    by_key = {(row["dataset"], row["scene"], row["variant"]): row for row in rows}
    win_counts = {}
    for reference in ["base", "rc"]:
        wins = losses = unavailable = 0
        for row in rows:
            if row["variant"] == reference:
                continue
            ref = by_key.get((row["dataset"], row["scene"], reference))
            if not ref:
                continue
            # Vertex count is a proxy, not a quality metric; count directional change only.
            result = _wins(
                row.get("geometry_proxy_vertex_count"),
                ref.get("geometry_proxy_vertex_count"),
                "geometry_proxy_vertex_count",
            )
            if result is None:
                unavailable += 1
            elif result:
                wins += 1
            else:
                losses += 1
        win_counts[reference] = {
            "geometry_quality_metrics_available": False,
            "proxy_vertex_count_lower_than_reference": wins,
            "proxy_vertex_count_not_lower_than_reference": losses,
            "unavailable": unavailable,
            "claim_boundary": "Proxy count is not a geometry quality win.",
        }

    correlations = {
        "reflection_consistency_vs_reflective_lpips": _pearson(
            [row.get("mean_reflection_consistency") for row in rows],
            [row.get("reflective_lpips") for row in rows],
        ),
        "reflection_consistency_vs_proxy_vertex_count": _pearson(
            [row.get("mean_reflection_consistency") for row in rows],
            [row.get("geometry_proxy_vertex_count") for row in rows],
        ),
        "true_depth_error_correlation": None,
        "true_normal_error_correlation": None,
        "true_mesh_metric_correlation": None,
    }

    return {
        "mode": "rc_refgs_geometry_quality_eval",
        "status": "proxy_only" if rows else "no_rows",
        "iteration": args.iteration,
        "rows": rows,
        "row_count": len(rows),
        "computed_metrics": ["geometry_proxy_vertex_count", "geometry_proxy_bbox_diag"],
        "unavailable_metrics": {
            "depth_mae_rmse_absrel": "missing GT depth and saved rendered depth buffers",
            "normal_mae_cosine": "missing saved rendered normal buffers and unverified normal coordinate space",
            "chamfer_fscore": "missing GT mesh/eval point cloud and predicted mesh extraction",
        },
        "win_counts": win_counts,
        "correlations": correlations,
        "counterexamples": {
            "consistency_improves_but_rgb_worsens": [],
            "consistency_improves_but_depth_worsens": "unavailable_missing_depth_metrics",
            "consistency_improves_but_normal_worsens": "unavailable_missing_normal_metrics",
            "rgb_improves_but_geometry_worsens": "unavailable_true_geometry_metrics",
        },
        "claim_boundary": "Proxy diagnostics only; no mesh/surface improvement claim.",
    }


def _stringify(value):
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    if value is None:
        return ""
    return value


def write_outputs(report, output_json, output_csv, output_md):
    Path(output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(output_json).write_text(json.dumps(report, indent=2) + "\n")
    if output_csv:
        with open(output_csv, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=BASE_FIELDS)
            writer.writeheader()
            for row in report["rows"]:
                writer.writerow({field: _stringify(row.get(field)) for field in BASE_FIELDS})
    if output_md:
        lines = [
            "# RC-RefGS Geometry Evaluation Stage 1",
            "",
            f"Rows: `{report['row_count']}`.",
            "",
            "Computed metrics are proxy diagnostics only: `geometry_proxy_vertex_count` and `geometry_proxy_bbox_diag`.",
            "",
            "Unavailable true metrics:",
        ]
        for key, reason in report["unavailable_metrics"].items():
            lines.append(f"- `{key}`: {reason}")
        lines += ["", "Claim boundary: " + report["claim_boundary"], ""]
        Path(output_md).write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Guarded geometry/proxy evaluator for existing RC-RefGS outputs.")
    parser.add_argument("--model_roots", nargs="+", required=True)
    parser.add_argument("--scenes", nargs="*", default=None)
    parser.add_argument("--variants", nargs="*", default=None)
    parser.add_argument("--iteration", type=int, default=31000)
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--output_md", required=True)
    args = parser.parse_args()

    report = build_report(args)
    write_outputs(report, args.output_json, args.output_csv, args.output_md)
    print(json.dumps({"row_count": report["row_count"], "status": report["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
