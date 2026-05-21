import argparse
import json
import os


METRIC_KEYS = (
    "full_diffuse_variance",
    "full_roughness_variance",
    "full_specular_variance",
    "full_specular_diffuse_ratio",
    "reflective_diffuse_variance",
    "reflective_roughness_variance",
    "reflective_specular_variance",
    "reflective_specular_diffuse_ratio",
)

SUMMARY_FIELDS = (
    "base_full_diffuse_variance",
    "rc_full_diffuse_variance",
    "base_full_roughness_variance",
    "rc_full_roughness_variance",
    "base_full_specular_variance",
    "rc_full_specular_variance",
    "base_reflective_diffuse_variance",
    "rc_reflective_diffuse_variance",
    "base_reflective_roughness_variance",
    "rc_reflective_roughness_variance",
    "base_reflective_specular_variance",
    "rc_reflective_specular_variance",
    "base_reflective_specular_diffuse_ratio",
    "rc_reflective_specular_diffuse_ratio",
)

MARKDOWN_HEADER_PREFIX = "| Scene | Split | Images | Base diffuse var | RC diffuse var | Delta |"


def load_metrics(model_dir, metric_filename):
    metric_path = os.path.join(model_dir, metric_filename)
    with open(metric_path, "r", encoding="utf-8") as f:
        return json.load(f)


def delta(rc_value, base_value):
    if rc_value is None or base_value is None:
        return None
    return rc_value - base_value


def summarize_split(scene, split, base_split, rc_split):
    if rc_split["num_images"] != base_split["num_images"]:
        raise ValueError(
            f"Image-count mismatch for {scene} {split}: "
            f"base={base_split['num_images']} rc={rc_split['num_images']}"
        )

    row = {
        "scene": scene,
        "split": split,
        "num_images": base_split["num_images"],
        "base_num_reflective_pixels": base_split.get("num_reflective_pixels"),
        "rc_num_reflective_pixels": rc_split.get("num_reflective_pixels"),
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
        rows.append(summarize_split(scene, split, base_splits[split], rc_splits[split]))
    return rows


def format_value(value, places=6):
    if value is None:
        return "null"
    return f"{value:.{places}f}"


def write_markdown(summary, output_markdown):
    lines = [
        "# RC-RefGS Material Quality Summary",
        "",
        MARKDOWN_HEADER_PREFIX + " Base roughness var | RC roughness var | Delta | Base specular var | RC specular var | Delta | Base reflective spec/diff | RC reflective spec/diff | Delta | Reflective pixels |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary["rows"]:
        reflective_pixels = f"{row['base_num_reflective_pixels']}/{row['rc_num_reflective_pixels']}"
        lines.append(
            "| {scene} | {split} | {num_images} | {base_full_diffuse_variance} | {rc_full_diffuse_variance} | {full_diffuse_variance_delta} | "
            "{base_full_roughness_variance} | {rc_full_roughness_variance} | {full_roughness_variance_delta} | "
            "{base_full_specular_variance} | {rc_full_specular_variance} | {full_specular_variance_delta} | "
            "{base_reflective_specular_diffuse_ratio} | {rc_reflective_specular_diffuse_ratio} | {reflective_specular_diffuse_ratio_delta} | {reflective_pixels} |".format(
                scene=row["scene"],
                split=row["split"],
                num_images=row["num_images"],
                base_full_diffuse_variance=format_value(row["base_full_diffuse_variance"]),
                rc_full_diffuse_variance=format_value(row["rc_full_diffuse_variance"]),
                full_diffuse_variance_delta=format_value(row["full_diffuse_variance_delta"]),
                base_full_roughness_variance=format_value(row["base_full_roughness_variance"]),
                rc_full_roughness_variance=format_value(row["rc_full_roughness_variance"]),
                full_roughness_variance_delta=format_value(row["full_roughness_variance_delta"]),
                base_full_specular_variance=format_value(row["base_full_specular_variance"]),
                rc_full_specular_variance=format_value(row["rc_full_specular_variance"]),
                full_specular_variance_delta=format_value(row["full_specular_variance_delta"]),
                base_reflective_specular_diffuse_ratio=format_value(row["base_reflective_specular_diffuse_ratio"]),
                rc_reflective_specular_diffuse_ratio=format_value(row["rc_reflective_specular_diffuse_ratio"]),
                reflective_specular_diffuse_ratio_delta=format_value(row["reflective_specular_diffuse_ratio_delta"]),
                reflective_pixels=reflective_pixels,
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
    parser = argparse.ArgumentParser(description="Summarize baseline-vs-RC material quality JSON files.")
    parser.add_argument("--pair", action="append", nargs=3, metavar=("SCENE", "BASE_DIR", "RC_DIR"), required=True)
    parser.add_argument("--metric_filename", default="material_quality_both_i300.json")
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
