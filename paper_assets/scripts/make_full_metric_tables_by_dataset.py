#!/usr/bin/env python3
"""Generate per-dataset full-metric comparison tables for RC experiments.

The script reads finalized metric CSVs only and writes derived paper tables
under paper_assets/. It never infers absolute metric values from deltas.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper_assets"
DATA = OUT / "data"
TABLES = OUT / "tables"
CAPTIONS = OUT / "captions"

MAIN_SOURCE = ROOT / "docs/superpowers/logs/rc-refgs-fd-p2-lite-final-main-summary-2026-06-01.csv"
MAIN_COUNT_SOURCE = ROOT / "docs/superpowers/logs/rc-refgs-fd-p2-lite-main-table-2026-05-29.csv"
ABLATION_SOURCE = ROOT / "docs/superpowers/logs/rc-refgs-fd-p2-lite-complete-metrics-ablation-table-2026-05-29.csv"

METRIC_DIRECTIONS = {
    "mean_reflection_consistency": "lower",
    "reflective_region_psnr": "higher",
    "full_psnr": "higher",
    "full_ssim": "higher",
    "full_lpips": "lower",
    "reflective_psnr": "higher",
    "reflective_ssim": "higher",
    "reflective_lpips": "lower",
    "valid_pair_count": "count",
    "num_pairs": "count",
    "num_images": "count",
}

CORE_METRICS = [
    "mean_reflection_consistency",
    "full_psnr",
    "full_ssim",
    "full_lpips",
]

REFLECTIVE_METRICS = [
    "reflective_region_psnr",
    "reflective_psnr",
    "reflective_ssim",
    "reflective_lpips",
]

FULL_TABLE_METRICS = [
    "mean_reflection_consistency",
    "reflective_region_psnr",
    "full_psnr",
    "full_ssim",
    "full_lpips",
    "reflective_psnr",
    "reflective_ssim",
    "reflective_lpips",
]

FULL_CSV_METRICS = FULL_TABLE_METRICS + ["valid_pair_count", "num_pairs", "num_images"]

METRIC_LABELS = {
    "mean_reflection_consistency": "RC$\\downarrow$",
    "reflective_region_psnr": "Region PSNR$\\uparrow$",
    "full_psnr": "PSNR$\\uparrow$",
    "full_ssim": "SSIM$\\uparrow$",
    "full_lpips": "LPIPS$\\downarrow$",
    "reflective_psnr": "Refl. PSNR$\\uparrow$",
    "reflective_ssim": "Refl. SSIM$\\uparrow$",
    "reflective_lpips": "Refl. LPIPS$\\downarrow$",
}

METHOD_ORDER = ["base", "rc"]
VARIANT_ORDER = ["base", "rc", "wo_ref", "wo_conf", "rough_only"]
SPLIT_ORDER = ["train", "test"]


def ensure_dirs() -> None:
    for path in (DATA, TABLES, CAPTIONS):
        path.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source file not found: {path}")
    return pd.read_csv(path)


def require_columns(df: pd.DataFrame, required: Iterable[str], source: Path) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"{rel(source)} is missing required columns {missing}. "
            f"Actual columns: {', '.join(df.columns)}"
        )


def is_number(value: object) -> bool:
    try:
        return np.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def metric_direction(metric: str) -> str:
    return METRIC_DIRECTIONS.get(metric, "unknown")


def metric_sort_key(metric: str) -> int:
    try:
        return FULL_CSV_METRICS.index(metric)
    except ValueError:
        return len(FULL_CSV_METRICS)


def method_sort_key(method: str) -> int:
    order = VARIANT_ORDER if method in VARIANT_ORDER else METHOD_ORDER
    try:
        return order.index(method)
    except ValueError:
        return len(order)


def row_type_sort_key(row_type: str) -> int:
    return {"scene": 0, "avg": 1}.get(str(row_type), 2)


def split_sort_key(split: str) -> int:
    try:
        return SPLIT_ORDER.index(split)
    except ValueError:
        return len(SPLIT_ORDER)


def format_value(value: object, metric: str) -> str:
    if not is_number(value):
        return "--"
    v = float(value)
    if metric == "mean_reflection_consistency":
        return f"{v:.5f}"
    if metric in {"full_psnr", "reflective_region_psnr", "reflective_psnr"}:
        return f"{v:.2f}"
    if metric in {"full_ssim", "full_lpips", "reflective_ssim", "reflective_lpips"}:
        return f"{v:.3f}"
    if metric in {"valid_pair_count", "num_pairs", "num_images"}:
        return f"{v:.0f}"
    return f"{v:.4f}"


def escape_latex(text: object) -> str:
    s = "" if pd.isna(text) else str(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in s)


def maybe_bold(text: str, is_best: bool) -> str:
    return f"\\textbf{{{text}}}" if is_best and text != "--" else text


def best_mask(values: pd.Series, metric: str) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    mask = pd.Series(False, index=values.index)
    finite = numeric[np.isfinite(numeric)]
    if finite.empty:
        return mask
    best = finite.min() if metric_direction(metric) == "lower" else finite.max()
    return numeric.apply(lambda x: np.isfinite(x) and math.isclose(float(x), float(best), rel_tol=1e-10, abs_tol=1e-12))


def append_rows_from_wide(
    rows: list[dict[str, object]],
    row: pd.Series,
    split: str,
    method_or_variant: str,
    label_field: str,
    metrics: Iterable[str],
    source_file: Path,
    note: str,
) -> None:
    for metric in metrics:
        col = f"{method_or_variant}_{split}_{metric}"
        if col not in row.index:
            continue
        value = row[col]
        rows.append(
            {
                "dataset": row["dataset"],
                "split": split,
                "scene": row["scene"],
                label_field: method_or_variant,
                "metric": metric,
                "value": float(value) if is_number(value) else np.nan,
                "metric_direction": metric_direction(metric),
                "source_file": rel(source_file),
                "valid_flag": bool(is_number(value)),
                "note": note,
            }
        )


def build_main_long(audit: list[str]) -> pd.DataFrame:
    main = read_csv(MAIN_SOURCE)
    require_columns(main, ["dataset", "scene"], MAIN_SOURCE)
    rows: list[dict[str, object]] = []

    for _, row in main.iterrows():
        for split in SPLIT_ORDER:
            for method in METHOD_ORDER:
                append_rows_from_wide(
                    rows,
                    row,
                    split,
                    method,
                    "method",
                    FULL_TABLE_METRICS,
                    MAIN_SOURCE,
                    "absolute per-scene metric from final main summary",
                )

    if MAIN_COUNT_SOURCE.exists():
        counts = read_csv(MAIN_COUNT_SOURCE)
        require_columns(counts, ["dataset", "scene"], MAIN_COUNT_SOURCE)
        for _, row in counts.iterrows():
            for split in SPLIT_ORDER:
                for method in METHOD_ORDER:
                    col = f"{method}_{split}_valid_pair_count"
                    if col not in row.index:
                        continue
                    value = row[col]
                    rows.append(
                        {
                            "dataset": row["dataset"],
                            "split": split,
                            "scene": row["scene"],
                            "method": method,
                            "metric": "valid_pair_count",
                            "value": float(value) if is_number(value) else np.nan,
                            "metric_direction": "count",
                            "source_file": rel(MAIN_COUNT_SOURCE),
                            "valid_flag": bool(is_number(value)),
                            "note": "pair-count metric from earlier main consistency table",
                        }
                    )
    else:
        audit.append(f"- main full metrics: optional count source missing: {rel(MAIN_COUNT_SOURCE)}.")

    df = pd.DataFrame(rows)
    if df.empty:
        audit.append("- main full metrics: no rows were generated.")
    else:
        df = df.sort_values(
            by=["dataset", "split", "scene", "method", "metric"],
            key=lambda col: col.map(metric_sort_key) if col.name == "metric" else (
                col.map(method_sort_key) if col.name == "method" else (
                    col.map(split_sort_key) if col.name == "split" else col
                )
            ),
        )
    df.to_csv(DATA / "main_full_metrics_by_dataset_long.csv", index=False)
    return df


def build_ablation_long(main_long: pd.DataFrame, audit: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    if not main_long.empty:
        main_as_ablation = main_long.rename(columns={"method": "variant"}).copy()
        main_as_ablation["note"] = main_as_ablation["note"].astype(str) + "; included as base/rc variants for ablation comparison"
        rows.extend(main_as_ablation.to_dict("records"))
    else:
        audit.append("- ablation full metrics: base/rc variants unavailable because main long table is empty.")

    ablation = read_csv(ABLATION_SOURCE)
    require_columns(ablation, ["row_type", "dataset", "scene", "variant"], ABLATION_SOURCE)
    model_rows = ablation[ablation["row_type"].astype(str) == "model"].copy()
    metrics = FULL_TABLE_METRICS + ["valid_pair_count", "num_pairs", "num_images"]
    missing_metric_columns: set[str] = set()
    for _, row in model_rows.iterrows():
        for split in SPLIT_ORDER:
            for metric in metrics:
                col = f"{split}_{metric}"
                if col not in model_rows.columns:
                    missing_metric_columns.add(col)
                    continue
                value = row[col]
                rows.append(
                    {
                        "dataset": row["dataset"],
                        "split": split,
                        "scene": row["scene"],
                        "variant": row["variant"],
                        "metric": metric,
                        "value": float(value) if is_number(value) else np.nan,
                        "metric_direction": metric_direction(metric),
                        "source_file": rel(ABLATION_SOURCE),
                        "valid_flag": bool(is_number(value)),
                        "note": "absolute per-scene metric from complete ablation table",
                    }
                )
    for col in sorted(missing_metric_columns):
        audit.append(f"- ablation full metrics: source lacks {col}; skipped without creating empty values.")

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(subset=["dataset", "split", "scene", "variant", "metric"], keep="first")
        df = df.sort_values(
            by=["dataset", "split", "scene", "variant", "metric"],
            key=lambda col: col.map(metric_sort_key) if col.name == "metric" else (
                col.map(method_sort_key) if col.name == "variant" else (
                    col.map(split_sort_key) if col.name == "split" else col
                )
            ),
        )
    df.to_csv(DATA / "ablation_full_metrics_by_dataset_long.csv", index=False)
    return df


def make_wide(long_df: pd.DataFrame, label_col: str, output_path: Path) -> pd.DataFrame:
    if long_df.empty:
        wide = pd.DataFrame(columns=["dataset", "split", "scene", "notes"])
        wide.to_csv(output_path, index=False)
        return wide
    metric_values = long_df[long_df["valid_flag"]].copy()
    pivot = metric_values.pivot_table(
        index=["dataset", "split", "scene", label_col],
        columns="metric",
        values="value",
        aggfunc="first",
    ).reset_index()
    pivot["notes"] = "missing entries are NA and excluded from averages"

    if label_col == "method":
        wide = pivot.pivot_table(
            index=["dataset", "split", "scene"],
            columns="method",
            values=[c for c in pivot.columns if c not in {"dataset", "split", "scene", "method", "notes"}],
            aggfunc="first",
        )
        wide.columns = [f"{method}_{metric}" for metric, method in wide.columns]
        wide = wide.reset_index()
        wide["notes"] = "absolute base/RC metrics; NA indicates unavailable source value"
        ordered = ["dataset", "split", "scene"]
        for metric in FULL_CSV_METRICS:
            for method in METHOD_ORDER:
                col = f"{method}_{metric}"
                if col in wide.columns:
                    ordered.append(col)
        ordered += [col for col in wide.columns if col not in ordered and col != "notes"]
        if "notes" in wide.columns:
            ordered.append("notes")
        wide = wide[ordered]
    else:
        wide = pivot
        ordered = ["dataset", "split", "scene", label_col]
        ordered += [metric for metric in FULL_CSV_METRICS if metric in wide.columns]
        ordered += [col for col in wide.columns if col not in ordered and col != "notes"]
        if "notes" in wide.columns:
            ordered.append("notes")
        wide = wide[ordered]

    wide = wide.sort_values(
        by=["dataset", "split", "scene"] + ([label_col] if label_col in wide.columns else []),
        key=lambda col: col.map(method_sort_key) if col.name == label_col else (
            col.map(split_sort_key) if col.name == "split" else col
        ),
    )
    wide.to_csv(output_path, index=False, na_rep="NA")
    return wide


def make_avg(long_df: pd.DataFrame, label_col: str, output_path: Path, audit: list[str], table_name: str) -> pd.DataFrame:
    if long_df.empty:
        avg = pd.DataFrame(columns=["dataset", "split", label_col, "metric", "mean_value", "valid_n", "total_scene_count", "metric_direction", "note"])
        avg.to_csv(output_path, index=False)
        return avg

    valid = long_df[long_df["valid_flag"]].copy()
    group_cols = ["dataset", "split", label_col, "metric"]
    scene_counts = (
        long_df.groupby(["dataset", "split", label_col])["scene"]
        .nunique()
        .rename("total_scene_count")
        .reset_index()
    )
    avg = (
        valid.groupby(group_cols)
        .agg(mean_value=("value", "mean"), valid_n=("scene", "nunique"))
        .reset_index()
        .merge(scene_counts, on=["dataset", "split", label_col], how="left")
    )
    avg["metric_direction"] = avg["metric"].map(metric_direction)
    avg["note"] = avg.apply(
        lambda r: f"mean over {int(r['valid_n'])}/{int(r['total_scene_count'])} valid scene rows",
        axis=1,
    )
    for _, r in avg.iterrows():
        if int(r["valid_n"]) < int(r["total_scene_count"]):
            audit.append(
                f"- {table_name}: {r['dataset']} {r['split']} {r[label_col]} "
                f"{r['metric']} average computed over {int(r['valid_n'])}/"
                f"{int(r['total_scene_count'])} valid scene rows."
            )
    avg = avg.sort_values(
        by=["dataset", "split", label_col, "metric"],
        key=lambda col: col.map(metric_sort_key) if col.name == "metric" else (
            col.map(method_sort_key) if col.name == label_col else (
                col.map(split_sort_key) if col.name == "split" else col
            )
        ),
    )
    avg.to_csv(output_path, index=False)
    return avg


def add_avg_rows_for_main(wide: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows = []
    for _, r in wide.iterrows():
        row = {col: r.get(col, np.nan) for col in ["dataset", "split", "scene"]}
        row.update({col: r.get(col, np.nan) for col in wide.columns if col not in row})
        row["row_type"] = "scene"
        rows.append(row)
    for (dataset, split), group in wide.groupby(["dataset", "split"], sort=False):
        row = {"dataset": dataset, "split": split, "scene": f"Avg. (n={group['scene'].nunique()})", "row_type": "avg", "notes": "dataset-split average"}
        for method in METHOD_ORDER:
            for metric in metrics:
                col = f"{method}_{metric}"
                if col in group.columns:
                    row[col] = pd.to_numeric(group[col], errors="coerce").mean()
        rows.append(row)
    return pd.DataFrame(rows)


def add_avg_rows_for_ablation(wide: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows = []
    for _, r in wide.iterrows():
        row = r.to_dict()
        row["row_type"] = "scene"
        rows.append(row)
    for (dataset, split, variant), group in wide.groupby(["dataset", "split", "variant"], sort=False):
        row = {
            "dataset": dataset,
            "split": split,
            "scene": f"Avg. (n={group['scene'].nunique()})",
            "variant": variant,
            "row_type": "avg",
            "notes": "dataset-split-variant average",
        }
        for metric in metrics:
            if metric in group.columns:
                row[metric] = pd.to_numeric(group[metric], errors="coerce").mean()
        rows.append(row)
    return pd.DataFrame(rows)


def main_row_best_flags(row: pd.Series, metric: str) -> dict[str, bool]:
    values = pd.Series({method: row.get(f"{method}_{metric}", np.nan) for method in METHOD_ORDER})
    mask = best_mask(values, metric)
    return {method: bool(mask.get(method, False)) for method in METHOD_ORDER}


def write_main_latex(wide: pd.DataFrame, metrics: list[str], path: Path, caption: str, label: str) -> None:
    table = add_avg_rows_for_main(wide, metrics)
    table["_split_order"] = table["split"].map(split_sort_key)
    table["_row_order"] = table["row_type"].map(row_type_sort_key)
    colspec = "lll" + "cc" * len(metrics)
    header1 = ["Dataset", "Split", "Scene"] + [f"\\multicolumn{{2}}{{c}}{{{METRIC_LABELS[m]}}}" for m in metrics]
    cmid = []
    start = 4
    for _ in metrics:
        cmid.append(f"\\cmidrule(lr){{{start}-{start + 1}}}")
        start += 2
    header2 = ["", "", ""] + ["Base & RC" for _ in metrics]
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\resizebox{\\textwidth}{!}{%",
        f"\\begin{{tabular}}{{{colspec}}}",
        "\\toprule",
        " & ".join(header1) + r" \\",
        " ".join(cmid),
        " & ".join(header2) + r" \\",
        "\\midrule",
    ]
    for _, row in table.sort_values(by=["dataset", "_split_order", "_row_order", "scene"]).iterrows():
        cells = [escape_latex(row["dataset"]), escape_latex(row["split"]), escape_latex(row["scene"])]
        for metric in metrics:
            flags = main_row_best_flags(row, metric)
            for method in METHOD_ORDER:
                value = format_value(row.get(f"{method}_{metric}", np.nan), metric)
                cells.append(maybe_bold(value, flags[method]))
        lines.append(" & ".join(cells) + r" \\")
        if row.get("row_type") == "avg":
            lines.append("\\midrule")
    if lines[-1] == "\\midrule":
        lines.pop()
    lines.extend(["\\bottomrule", "\\end{tabular}}", "\\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_ablation_latex(wide: pd.DataFrame, metrics: list[str], path: Path, caption: str, label: str) -> None:
    table = add_avg_rows_for_ablation(wide, metrics)
    table["_split_order"] = table["split"].map(split_sort_key)
    table["_row_order"] = table["row_type"].map(row_type_sort_key)
    table["_variant_order"] = table["variant"].map(method_sort_key)
    colspec = "llll" + "c" * len(metrics)
    headers = ["Dataset", "Split", "Scene", "Variant"] + [METRIC_LABELS[m] for m in metrics]
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\resizebox{\\textwidth}{!}{%",
        f"\\begin{{tabular}}{{{colspec}}}",
        "\\toprule",
        " & ".join(headers) + r" \\",
        "\\midrule",
    ]

    best_lookup: dict[tuple[object, object, object, object, str], bool] = {}
    for row_type, group in table.groupby("row_type", sort=False):
        key_cols = ["dataset", "split", "scene"] if row_type == "scene" else ["dataset", "split"]
        for key, key_group in group.groupby(key_cols, sort=False):
            if not isinstance(key, tuple):
                key = (key,)
            for metric in metrics:
                mask = best_mask(key_group[metric] if metric in key_group.columns else pd.Series(dtype=float), metric)
                for idx, is_best in mask.items():
                    lookup_key = tuple(key_group.loc[idx, c] for c in key_cols) + (key_group.loc[idx, "variant"], metric)
                    best_lookup[lookup_key] = bool(is_best)

    sorted_table = table.sort_values(
        by=["dataset", "_split_order", "_row_order", "scene", "_variant_order", "variant"],
    )
    for _, row in sorted_table.iterrows():
        cells = [
            escape_latex(row["dataset"]),
            escape_latex(row["split"]),
            escape_latex(row["scene"]),
            escape_latex(row["variant"]),
        ]
        key_cols = ["dataset", "split", "scene"] if row.get("row_type") == "scene" else ["dataset", "split"]
        for metric in metrics:
            value = format_value(row.get(metric, np.nan), metric)
            lookup_key = tuple(row[c] for c in key_cols) + (row["variant"], metric)
            cells.append(maybe_bold(value, best_lookup.get(lookup_key, False)))
        lines.append(" & ".join(cells) + r" \\")
        if row.get("row_type") == "avg" and row["variant"] == sorted_table[sorted_table["row_type"] == "avg"]["variant"].iloc[-1]:
            lines.append("\\midrule")
    if lines[-1] == "\\midrule":
        lines.pop()
    lines.extend(["\\bottomrule", "\\end{tabular}}", "\\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_latex_tables(main_wide: pd.DataFrame, ablation_wide: pd.DataFrame) -> None:
    write_main_latex(
        main_wide,
        FULL_TABLE_METRICS,
        TABLES / "table_main_full_metrics_by_dataset.tex",
        "Main full-metric comparison by dataset. Missing entries are denoted by -- and excluded from averages.",
        "tab:main_full_metrics_by_dataset",
    )
    write_main_latex(
        main_wide,
        CORE_METRICS,
        TABLES / "table_main_full_metrics_by_dataset_compact.tex",
        "Compact main comparison by dataset using reflection consistency and full-image metrics.",
        "tab:main_full_metrics_by_dataset_compact",
    )
    write_main_latex(
        main_wide,
        REFLECTIVE_METRICS,
        TABLES / "table_main_reflective_region_metrics_by_dataset.tex",
        "Reflective-region and reflective-mask quality metrics for the main comparison by dataset.",
        "tab:main_reflective_region_metrics_by_dataset",
    )

    write_ablation_latex(
        ablation_wide,
        FULL_TABLE_METRICS,
        TABLES / "table_ablation_full_metrics_by_dataset.tex",
        "Ablation full-metric comparison by dataset. Missing entries are denoted by -- and excluded from averages.",
        "tab:ablation_full_metrics_by_dataset",
    )
    write_ablation_latex(
        ablation_wide,
        CORE_METRICS,
        TABLES / "table_ablation_full_metrics_by_dataset_compact.tex",
        "Compact ablation comparison by dataset using reflection consistency and full-image metrics.",
        "tab:ablation_full_metrics_by_dataset_compact",
    )
    write_ablation_latex(
        ablation_wide,
        REFLECTIVE_METRICS,
        TABLES / "table_ablation_reflective_region_metrics_by_dataset.tex",
        "Reflective-region and reflective-mask metrics for ablation variants by dataset.",
        "tab:ablation_reflective_region_metrics_by_dataset",
    )


def update_marked_section(path: Path, marker: str, content: str) -> None:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    block = f"{start}\n{content.rstrip()}\n{end}\n"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end) + r"\n?", flags=re.S)
    if pattern.search(old):
        new = pattern.sub(block, old)
    else:
        sep = "\n\n" if old and not old.endswith("\n\n") else ""
        new = old + sep + block
    path.write_text(new, encoding="utf-8")


def write_captions() -> None:
    text = """# Full metric table captions / 全指标表格标题

## Main full-metric tables

中文：表 X 展示主实验在不同数据集下的全部指标数值对照。每个数据集内部逐 scene 报告 Base 与 RC 的 cross-view reflection consistency、full-image PSNR/SSIM/LPIPS 以及可用的 reflective-region 或 reflective-mask metrics，并在同一 dataset 与 split 内给出平均值。RC$\\downarrow$ 和 LPIPS$\\downarrow$ 表示数值越低越好，PSNR$\\uparrow$ 和 SSIM$\\uparrow$ 表示数值越高越好。缺失项以 “--” 表示，未参与平均值计算。

English: Table X reports full-metric main comparisons by dataset. Within each dataset, per-scene Base and RC results are listed for cross-view reflection consistency, full-image PSNR/SSIM/LPIPS, and available reflective-region or reflective-mask metrics, followed by averages computed within the same dataset and split. RC$\\downarrow$ and LPIPS$\\downarrow$ indicate lower-is-better metrics, while PSNR$\\uparrow$ and SSIM$\\uparrow$ indicate higher-is-better metrics. Missing entries are denoted by “--” and excluded from averages.

## Ablation full-metric tables

中文：表 Y 展示消融实验在不同数据集下的全部指标数值对照。每个数据集内部逐 scene、split 和 variant 报告可用指标，并对每个 variant 分别计算 dataset-level 平均值。该表用于分析 RC、confidence weighting 和 roughness-only regularization 的作用边界，而不应被解释为所有指标的全面提升。

English: Table Y reports full-metric ablation comparisons by dataset. Within each dataset, available metrics are listed for each scene, split and variant, followed by per-variant dataset-level averages. The table is intended to analyze the roles and boundaries of RC, confidence weighting and roughness-only regularization, and should not be interpreted as a universal improvement across all metrics.
"""
    (CAPTIONS / "full_metric_table_captions_zh_en.md").write_text(text, encoding="utf-8")


def update_docs(audit_lines: list[str]) -> None:
    audit_content = "\n".join(
        [
            "## Full Metric Tables By Dataset",
            "",
            f"- Main absolute metrics source: `{rel(MAIN_SOURCE)}`.",
            f"- Main valid-pair count source: `{rel(MAIN_COUNT_SOURCE)}`.",
            f"- Ablation absolute metrics source: `{rel(ABLATION_SOURCE)}`.",
            "- The main full tables use absolute Base/RC values from the final main summary, not values reconstructed from deltas.",
            "- The ablation full tables combine Base/RC rows from the main absolute metrics with wo_ref/wo_conf/rough_only rows from the complete ablation table.",
            "- Averages are computed within dataset + split, and for ablations also within variant. Missing values are excluded from averages and displayed as `--` in LaTeX.",
            "- Source columns named `reflective_region_ssim` and `reflective_region_lpips` were not found; available `reflective_ssim` and `reflective_lpips` columns are retained under their source metric names.",
            "- The previously missing `reflective_region_psnr` delta is not reconstructed. Absolute `reflective_region_psnr` values are retained where present in the full metric sources.",
            *audit_lines,
        ]
    )
    update_marked_section(OUT / "experiment_data_audit.md", "FULL_METRIC_TABLES", audit_content)

    boundary_content = """## Full Metric Table Claim Boundary

| Claim | Supported by full metric tables? | Safe wording | Unsafe wording |
|---|---|---|---|
| Per-dataset/per-scene full metric comparisons are available. | Yes, within FD-P2-lite non-Shiny-Real completed runs. | The full metric tables provide per-dataset and per-scene numerical comparisons for available metrics. | The tables prove complete validation on every reflective dataset. |
| RC mainly improves reflection consistency. | Supported within the completed scope. | RC shows its most stable gain on cross-view reflection consistency in the completed scope. | RC is best on every dataset, scene and metric. |
| Full-image and reflective quality improve universally. | No. | Full-image and reflective-region quality should be reported metric by metric. | RC necessarily improves PSNR/SSIM/LPIPS. |
| Ablations clarify component boundaries. | Diagnostic support only. | The ablation table helps analyze confidence weighting and roughness-only boundaries in this scope. | rough_only can replace RC, or confidence weighting is universally dominant. |
| Mesh quality improves. | No independent support. | Mesh or geometry quality requires separate evaluation. | RC necessarily improves mesh quality. |
"""
    update_marked_section(OUT / "experiment_claim_boundary.md", "FULL_METRIC_TABLES", boundary_content)

    summary_content = """## 6. Per-dataset full metric tables

新增的 full metric tables 将主实验和消融实验拆分到 dataset、split、scene 与 method/variant 层级，避免只用 win-count 或平均 trade-off 概括结果。主实验表使用 Base 与 RC 的绝对指标值；消融表将 Base/RC 与 wo_ref、wo_conf、rough_only 放在同一 per-scene 表格中比较。所有 Avg. 行均在同一 dataset + split 内计算，消融表进一步按 variant 分开计算。缺失项以 “--” 显示并排除出平均值，因此这些表支持逐指标、逐范围的谨慎讨论，而不支持“所有指标全面提升”的结论。
"""
    update_marked_section(OUT / "rc_results_summary_zh.md", "FULL_METRIC_TABLES", summary_content)


def main() -> None:
    ensure_dirs()
    audit: list[str] = []
    main_long = build_main_long(audit)
    ablation_long = build_ablation_long(main_long, audit)

    main_wide = make_wide(main_long, "method", DATA / "main_full_metrics_by_dataset_wide.csv")
    ablation_wide = make_wide(ablation_long, "variant", DATA / "ablation_full_metrics_by_dataset_wide.csv")
    make_avg(main_long, "method", DATA / "main_full_metrics_by_dataset_avg.csv", audit, "main_full_metrics_by_dataset")
    make_avg(ablation_long, "variant", DATA / "ablation_full_metrics_by_dataset_avg.csv", audit, "ablation_full_metrics_by_dataset")

    write_latex_tables(main_wide, ablation_wide)
    write_captions()
    update_docs(audit)
    print("Wrote per-dataset full metric tables.")


if __name__ == "__main__":
    main()
