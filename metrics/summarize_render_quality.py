import argparse
import json
import os


METRIC_KEYS = (
    "full_psnr",
    "full_ssim",
    "full_lpips",
    "reflective_psnr",
    "reflective_ssim",
    "reflective_lpips",
)

SUMMARY_FIELDS = (
    "base_full_psnr",
    "rc_full_psnr",
    "base_full_ssim",
    "rc_full_ssim",
    "base_reflective_psnr",
    "rc_reflective_psnr",
    "base_reflective_ssim",
    "rc_reflective_ssim",
    "base_full_lpips",
    "rc_full_lpips",
    "base_reflective_lpips",
    "rc_reflective_lpips",
)

MARKDOWN_HEADER_PREFIX = "| Scene | Split | Images | Base full PSNR | RC full PSNR | Delta |"


def load_metrics(model_dir, metric_filename):
    metric_path = os.path.join(model_dir, metric_filename)
    with open(metric_path, "r", encoding="utf-8") as f:
        return json.load(f)


def delta(rc_value, base_value):
    if rc_value is None or base_value is None:
        return None
    return rc_value - base_value


def summarize_split(scene, split, base_split, rc_split, base_metrics, rc_metrics):
    row = {
        "scene": scene,
        "split": split,
        "num_images": base_split["num_images"],
        "lpips_skipped": bool(base_metrics.get("lpips_skipped") or rc_metrics.get("lpips_skipped")),
    }
    if rc_split["num_images"] != base_split["num_images"]:
        raise ValueError(
            f"Image-count mismatch for {scene} {split}: "
            f"base={base_split['num_images']} rc={rc_split['num_images']}"
        )

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
        "# RC-RefGS Render Quality Summary",
        "",
        MARKDOWN_HEADER_PREFIX + " Base full SSIM | RC full SSIM | Delta | Base reflective PSNR | RC reflective PSNR | Delta | Base reflective SSIM | RC reflective SSIM | Delta | LPIPS skipped |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary["rows"]:
        lines.append(
            "| {scene} | {split} | {num_images} | {base_full_psnr} | {rc_full_psnr} | {full_psnr_delta} | "
            "{base_full_ssim} | {rc_full_ssim} | {full_ssim_delta} | "
            "{base_reflective_psnr} | {rc_reflective_psnr} | {reflective_psnr_delta} | "
            "{base_reflective_ssim} | {rc_reflective_ssim} | {reflective_ssim_delta} | {lpips_skipped} |".format(
                scene=row["scene"],
                split=row["split"],
                num_images=row["num_images"],
                base_full_psnr=format_value(row["base_full_psnr"]),
                rc_full_psnr=format_value(row["rc_full_psnr"]),
                full_psnr_delta=format_value(row["full_psnr_delta"]),
                base_full_ssim=format_value(row["base_full_ssim"]),
                rc_full_ssim=format_value(row["rc_full_ssim"]),
                full_ssim_delta=format_value(row["full_ssim_delta"]),
                base_reflective_psnr=format_value(row["base_reflective_psnr"]),
                rc_reflective_psnr=format_value(row["rc_reflective_psnr"]),
                reflective_psnr_delta=format_value(row["reflective_psnr_delta"]),
                base_reflective_ssim=format_value(row["base_reflective_ssim"]),
                rc_reflective_ssim=format_value(row["rc_reflective_ssim"]),
                reflective_ssim_delta=format_value(row["reflective_ssim_delta"]),
                lpips_skipped=str(row["lpips_skipped"]).lower(),
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
    parser = argparse.ArgumentParser(description="Summarize baseline-vs-RC render quality JSON files.")
    parser.add_argument("--pair", action="append", nargs=3, metavar=("SCENE", "BASE_DIR", "RC_DIR"), required=True)
    parser.add_argument("--metric_filename", default="render_quality_both_i300_skip_lpips.json")
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
