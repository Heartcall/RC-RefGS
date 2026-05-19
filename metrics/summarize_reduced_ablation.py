import argparse
import json
import os


EXPECTED_VARIANTS = ("base", "rc", "wo_ref", "wo_conf", "rough_only")
EXPECTED_SPLITS = ("train", "test")

MARKDOWN_HEADER = "| Scene | Variant | Split | Status | Mean RC | Delta vs Base | Num Pairs |"


def metric_json_path(root_dir, scene, variant, split):
    model_dir = os.path.join(root_dir, f"{scene}_{variant}")
    return os.path.join(model_dir, f"reflection_consistency_{split}.json")


def point_cloud_dir(root_dir, scene, variant, iteration):
    model_dir = os.path.join(root_dir, f"{scene}_{variant}")
    return os.path.join(model_dir, "point_cloud", f"iteration_{iteration}")


def load_metric(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt_float(value):
    if value is None:
        return "null"
    return f"{value:.10f}"


def summarize_scene(scene, root_dir, iteration):
    rows = []
    by_split_variant = {}
    missing_cells = []

    for variant in EXPECTED_VARIANTS:
        pc_exists = os.path.isdir(point_cloud_dir(root_dir, scene, variant, iteration))
        for split in EXPECTED_SPLITS:
            metric_path = metric_json_path(root_dir, scene, variant, split)
            key = (split, variant)
            row = {
                "scene": scene,
                "variant": variant,
                "split": split,
                "iteration": iteration,
                "metric_json": metric_path,
                "point_cloud_iteration_dir": point_cloud_dir(root_dir, scene, variant, iteration),
                "point_cloud_exists": pc_exists,
                "status": "missing",
                "mean_reflection_consistency": None,
                "reflective_region_psnr": None,
                "num_pairs": None,
                "baseline_mean_reflection_consistency": None,
                "mean_reflection_consistency_delta_vs_base": None,
            }

            if os.path.isfile(metric_path):
                metric = load_metric(metric_path)
                row["status"] = "available"
                row["mean_reflection_consistency"] = metric.get("mean_reflection_consistency")
                row["reflective_region_psnr"] = metric.get("reflective_region_psnr")
                row["num_pairs"] = metric.get("num_pairs")
            else:
                missing_cells.append(
                    {
                        "scene": scene,
                        "variant": variant,
                        "split": split,
                        "metric_json": metric_path,
                        "point_cloud_exists": pc_exists,
                    }
                )

            by_split_variant[key] = row
            rows.append(row)

    for split in EXPECTED_SPLITS:
        base_row = by_split_variant[(split, "base")]
        base_metric = base_row["mean_reflection_consistency"] if base_row["status"] == "available" else None
        for variant in EXPECTED_VARIANTS:
            row = by_split_variant[(split, variant)]
            row["baseline_mean_reflection_consistency"] = base_metric
            if row["status"] == "available" and base_metric is not None:
                row["mean_reflection_consistency_delta_vs_base"] = (
                    row["mean_reflection_consistency"] - base_metric
                )

    available_cells = sum(1 for row in rows if row["status"] == "available")
    expected_cells = len(rows)
    return rows, missing_cells, available_cells, expected_cells


def build_summary(scene_roots, iteration):
    rows = []
    missing_cells = []
    expected_cells = 0
    available_cells = 0

    for scene, root_dir in scene_roots:
        scene_rows, scene_missing, scene_available, scene_expected = summarize_scene(scene, root_dir, iteration)
        rows.extend(scene_rows)
        missing_cells.extend(scene_missing)
        available_cells += scene_available
        expected_cells += scene_expected

    return {
        "iteration": iteration,
        "expected_variants": list(EXPECTED_VARIANTS),
        "expected_splits": list(EXPECTED_SPLITS),
        "scene_roots": [{"scene": scene, "root_dir": root_dir} for scene, root_dir in scene_roots],
        "expected_cells": expected_cells,
        "available_cells": available_cells,
        "missing_cells": missing_cells,
        "rows": rows,
    }


def write_markdown(summary, output_markdown):
    lines = [
        "# RC-RefGS Reduced Ablation Summary",
        "",
        f"- Iteration: {summary['iteration']}",
        f"- Available cells: {summary['available_cells']} / {summary['expected_cells']}",
        f"- Missing cells: {len(summary['missing_cells'])}",
        "",
        MARKDOWN_HEADER,
        "| --- | --- | --- | --- | ---: | ---: | ---: |",
    ]

    for row in summary["rows"]:
        lines.append(
            "| {scene} | {variant} | {split} | {status} | {mean_rc} | {delta} | {num_pairs} |".format(
                scene=row["scene"],
                variant=row["variant"],
                split=row["split"],
                status=row["status"],
                mean_rc=fmt_float(row["mean_reflection_consistency"]),
                delta=fmt_float(row["mean_reflection_consistency_delta_vs_base"]),
                num_pairs="null" if row["num_pairs"] is None else row["num_pairs"],
            )
        )

    if summary["missing_cells"]:
        lines.extend(["", "## Missing Cells", "", "| Scene | Variant | Split | Point Cloud Exists | Metric JSON |", "| --- | --- | --- | --- | --- |"])
        for cell in summary["missing_cells"]:
            lines.append(
                "| {scene} | {variant} | {split} | {pc} | {path} |".format(
                    scene=cell["scene"],
                    variant=cell["variant"],
                    split=cell["split"],
                    pc=str(cell["point_cloud_exists"]).lower(),
                    path=cell["metric_json"],
                )
            )

    os.makedirs(os.path.dirname(output_markdown), exist_ok=True)
    with open(output_markdown, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Summarize reduced i20 ablation reflection-consistency JSON artifacts.")
    parser.add_argument("--scene-root", action="append", nargs=2, metavar=("SCENE", "ROOT_DIR"), required=True)
    parser.add_argument("--iteration", type=int, default=20)
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--output_markdown", default=None)
    args = parser.parse_args()

    summary = build_summary(args.scene_root, args.iteration)

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if args.output_markdown:
        write_markdown(summary, args.output_markdown)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
