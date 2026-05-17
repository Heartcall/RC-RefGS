import argparse
import json
import os


METRIC_KEYS = (
    "normal_mae_deg",
    "normal_mean_cosine",
    "reflective_normal_mae_deg",
    "reflective_normal_mean_cosine",
)

MARKDOWN_HEADER_PREFIX = "| Scene | Split | Images | GT normal space | Base normal MAE | RC normal MAE | Delta |"


def load_metrics(model_dir, metric_filename):
    metric_path = os.path.join(model_dir, metric_filename)
    with open(metric_path, "r", encoding="utf-8") as f:
        return json.load(f)


def delta(rc_value, base_value):
    if rc_value is None or base_value is None:
        return None
    return rc_value - base_value


def summarize_split(scene, split, base_split, rc_split, base_metrics, rc_metrics):
    if base_metrics.get("gt_normal_space") != rc_metrics.get("gt_normal_space"):
        raise ValueError(
            f"GT normal-space mismatch for {scene}: "
            f"base={base_metrics.get('gt_normal_space')} rc={rc_metrics.get('gt_normal_space')}"
        )
    if rc_split["num_images"] != base_split["num_images"]:
        raise ValueError(
            f"Image-count mismatch for {scene} {split}: "
            f"base={base_split['num_images']} rc={rc_split['num_images']}"
        )
    if rc_split["num_normal_images"] != base_split["num_normal_images"]:
        raise ValueError(
            f"Normal-image-count mismatch for {scene} {split}: "
            f"base={base_split['num_normal_images']} rc={rc_split['num_normal_images']}"
        )

    row = {
        "scene": scene,
        "split": split,
        "num_images": base_split["num_images"],
        "num_normal_images": base_split["num_normal_images"],
        "num_missing_normals": base_split["num_missing_normals"],
        "rc_num_missing_normals": rc_split["num_missing_normals"],
        "gt_normal_space": base_metrics.get("gt_normal_space"),
    }
    for key in METRIC_KEYS:
        base_key = f"base_{key}"
        rc_key = f"rc_{key}"
        row[base_key] = base_split.get(key)
        row[rc_key] = rc_split.get(key)
        row[f"{key}_delta"] = delta(row[rc_key], row[base_key])
    return row


def summarize_pair(scene, base_dir, rc_dir, metric_filename):
    base_metrics = load_metrics(base_dir, metric_filename)
    rc_metrics = load_metrics(rc_dir, metric_filename)
    base_splits = base_metrics["splits"]
    rc_splits = rc_metrics["splits"]

    rows = []
    for split in sorted(base_splits.keys()):
        if split not in rc_splits:
            raise ValueError(f"Missing RC split for {scene}: {split}")
        rows.append(summarize_split(scene, split, base_splits[split], rc_splits[split], base_metrics, rc_metrics))
    return rows


def format_value(value, places=6):
    if value is None:
        return "null"
    return f"{value:.{places}f}"


def write_markdown(summary, output_markdown):
    lines = [
        "# RC-RefGS Normal Quality Summary",
        "",
        MARKDOWN_HEADER_PREFIX + " Base cosine | RC cosine | Delta | Base reflective MAE | RC reflective MAE | Delta | Base reflective cosine | RC reflective cosine | Delta | Missing normals |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary["rows"]:
        missing = f"{row['num_missing_normals']}/{row['rc_num_missing_normals']}"
        lines.append(
            "| {scene} | {split} | {num_images} | {gt_normal_space} | {base_normal_mae_deg} | {rc_normal_mae_deg} | {normal_mae_deg_delta} | "
            "{base_normal_mean_cosine} | {rc_normal_mean_cosine} | {normal_mean_cosine_delta} | "
            "{base_reflective_normal_mae_deg} | {rc_reflective_normal_mae_deg} | {reflective_normal_mae_deg_delta} | "
            "{base_reflective_normal_mean_cosine} | {rc_reflective_normal_mean_cosine} | {reflective_normal_mean_cosine_delta} | {missing} |".format(
                scene=row["scene"],
                split=row["split"],
                num_images=row["num_images"],
                gt_normal_space=row["gt_normal_space"],
                base_normal_mae_deg=format_value(row["base_normal_mae_deg"]),
                rc_normal_mae_deg=format_value(row["rc_normal_mae_deg"]),
                normal_mae_deg_delta=format_value(row["normal_mae_deg_delta"]),
                base_normal_mean_cosine=format_value(row["base_normal_mean_cosine"]),
                rc_normal_mean_cosine=format_value(row["rc_normal_mean_cosine"]),
                normal_mean_cosine_delta=format_value(row["normal_mean_cosine_delta"]),
                base_reflective_normal_mae_deg=format_value(row["base_reflective_normal_mae_deg"]),
                rc_reflective_normal_mae_deg=format_value(row["rc_reflective_normal_mae_deg"]),
                reflective_normal_mae_deg_delta=format_value(row["reflective_normal_mae_deg_delta"]),
                base_reflective_normal_mean_cosine=format_value(row["base_reflective_normal_mean_cosine"]),
                rc_reflective_normal_mean_cosine=format_value(row["rc_reflective_normal_mean_cosine"]),
                reflective_normal_mean_cosine_delta=format_value(row["reflective_normal_mean_cosine_delta"]),
                missing=missing,
            )
        )

    os.makedirs(os.path.dirname(output_markdown), exist_ok=True)
    with open(output_markdown, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def build_summary(pairs, metric_filename):
    rows = []
    for scene, base_dir, rc_dir in pairs:
        rows.extend(summarize_pair(scene, base_dir, rc_dir, metric_filename))
    return {
        "metric_filename": metric_filename,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description="Summarize baseline-vs-RC normal quality JSON files.")
    parser.add_argument("--pair", action="append", nargs=3, metavar=("SCENE", "BASE_DIR", "RC_DIR"), required=True)
    parser.add_argument("--metric_filename", default="normal_quality_both_i300_full_raw.json")
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--output_markdown", default=None)
    args = parser.parse_args()

    summary = build_summary(args.pair, args.metric_filename)

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if args.output_markdown:
        write_markdown(summary, args.output_markdown)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
