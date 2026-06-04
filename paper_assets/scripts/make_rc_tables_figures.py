#!/usr/bin/env python3
"""Build paper tables and figures for RC-RefGS FD-P2-lite results.

This script is intentionally read-only with respect to the original experiment
artifacts. It consumes finalized CSV summaries and writes derived paper assets
under paper_assets/.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "superpowers" / "figures" / "fd-p2-lite"
OUT = ROOT / "paper_assets"
DATA = OUT / "data"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
CAPTIONS = OUT / "captions"

SOURCE_FILES = {
    "main": SRC / "table1_main_base_vs_rc_summary.csv",
    "wins": SRC / "table2_rc_win_counts_by_metric.csv",
    "ablation": SRC / "table3_ablation_aggregate.csv",
    "tradeoff": SRC / "table4_tradeoff_summary.csv",
}

METRIC_DIRECTIONS = {
    "mean_reflection_consistency": "lower",
    "reflective_region_psnr": "higher",
    "full_psnr": "higher",
    "full_ssim": "higher",
    "full_lpips": "lower",
    "reflective_psnr": "higher",
    "reflective_ssim": "higher",
    "reflective_lpips": "lower",
}

METRIC_LABELS = {
    "mean_reflection_consistency": "Reflection consistency",
    "reflective_region_psnr": "Region PSNR",
    "full_psnr": "Full PSNR",
    "full_ssim": "Full SSIM",
    "full_lpips": "Full LPIPS",
    "reflective_psnr": "Reflective PSNR",
    "reflective_ssim": "Reflective SSIM",
    "reflective_lpips": "Reflective LPIPS",
}

DATASET_LABELS = {
    "shiny_blender_synthetic": "Shiny-Syn.",
    "glossy_synthetic": "Glossy-Syn.",
}

PALETTE = {
    "train": "#0072B2",
    "test": "#D55E00",
    "completed": "#009E73",
    "excluded": "#CC79A7",
    "failed": "#E69F00",
}


def ensure_dirs() -> None:
    for path in (DATA, TABLES, FIGURES, CAPTIONS, OUT / "scripts"):
        path.mkdir(parents=True, exist_ok=True)


def require_columns(df: pd.DataFrame, required: Iterable[str], name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        actual = ", ".join(df.columns)
        raise ValueError(f"{name} is missing columns {missing}. Actual columns: {actual}")


def read_csv_checked(key: str, required: Iterable[str]) -> pd.DataFrame:
    path = SOURCE_FILES[key]
    if not path.exists():
        raise FileNotFoundError(f"Required source CSV not found: {path}")
    df = pd.read_csv(path)
    require_columns(df, required, path.name)
    return df


def clean_numeric(df: pd.DataFrame, columns: Iterable[str], name: str, audit: list[str]) -> pd.DataFrame:
    out = df.copy()
    before = len(out)
    for col in columns:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    finite_mask = np.ones(len(out), dtype=bool)
    for col in columns:
        finite_mask &= np.isfinite(out[col].to_numpy(dtype=float))
    removed = before - int(finite_mask.sum())
    if removed:
        audit.append(f"- {name}: removed {removed} rows with NaN/inf in numeric columns.")
    return out.loc[finite_mask].reset_index(drop=True)


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def metric_improvement(delta: float, metric: str) -> float:
    return -delta if METRIC_DIRECTIONS[metric] == "lower" else delta


def format_metric(value: float, metric: str) -> str:
    if pd.isna(value):
        return "n/a"
    if metric == "mean_reflection_consistency":
        return f"{value:.5f}"
    if "psnr" in metric:
        return f"{value:.2f}"
    return f"{value:.3f}"


def short_dataset(name: str) -> str:
    return DATASET_LABELS.get(name, name)


def parse_complete_expected(value: str) -> tuple[int, int]:
    m = re.match(r"\s*(\d+)\s*/\s*(\d+)\s*", str(value))
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))


def to_latex_table(df: pd.DataFrame, path: Path, caption: str, label: str, resize: bool = True) -> None:
    tabular = df.to_latex(index=False, escape=True)
    if resize:
        body = (
            "\\begin{table}[t]\n"
            "\\centering\n"
            f"\\caption{{{caption}}}\n"
            f"\\label{{{label}}}\n"
            "\\resizebox{\\linewidth}{!}{%\n"
            f"{tabular}"
            "}\n"
            "\\end{table}\n"
        )
    else:
        body = (
            "\\begin{table}[t]\n"
            "\\centering\n"
            f"\\caption{{{caption}}}\n"
            f"\\label{{{label}}}\n"
            f"{tabular}"
            "\\end{table}\n"
        )
    path.write_text(body, encoding="utf-8")


def save_figure(fig: plt.Figure, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def build_clean_main(main_df: pd.DataFrame, audit: list[str]) -> pd.DataFrame:
    metric_suffix = {
        "mean_reflection_consistency": "consistency",
        "reflective_region_psnr": "reflective_region_psnr",
        "full_psnr": "full_psnr",
        "full_ssim": "full_ssim",
        "full_lpips": "full_lpips",
        "reflective_psnr": "reflective_psnr",
        "reflective_ssim": "reflective_ssim",
        "reflective_lpips": "reflective_lpips",
    }
    rows = []
    missing_delta_columns: set[str] = set()
    for _, row in main_df.iterrows():
        for split in ("train", "test"):
            for metric, suffix in metric_suffix.items():
                col = f"{split}_rc_delta_{suffix}"
                if col not in main_df.columns:
                    missing_delta_columns.add(col)
                    continue
                delta = pd.to_numeric(row[col], errors="coerce")
                if not np.isfinite(delta):
                    audit.append(f"- main: skipped non-finite delta for {row['dataset']}/{row['scene']} {split} {metric}.")
                    continue
                improvement = metric_improvement(float(delta), metric)
                rows.append(
                    {
                        "dataset": row["dataset"],
                        "dataset_label": short_dataset(row["dataset"]),
                        "scene": row["scene"],
                        "split": split,
                        "metric": metric,
                        "better_direction": METRIC_DIRECTIONS[metric],
                        "rc_minus_base_delta": float(delta),
                        "improvement": improvement,
                        "winner": "RC" if improvement > 0 else ("base" if improvement < 0 else "tie"),
                        "quality_tradeoff_summary": row.get("quality_tradeoff_summary", ""),
                    }
                )
    for col in sorted(missing_delta_columns):
        audit.append(f"- main: source CSV lacks {col}; this metric is not expanded into cleaned_main_results.csv.")
    cleaned = pd.DataFrame(rows)
    cleaned.to_csv(DATA / "cleaned_main_results.csv", index=False)
    return cleaned


def build_clean_ablation(ablation_df: pd.DataFrame, audit: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    numeric_cols = [
        c
        for c in ablation_df.columns
        if c.startswith("train_") or c.startswith("test_")
    ]
    ablation_df = clean_numeric(ablation_df, numeric_cols, "ablation", audit)

    long_rows = []
    missing_metric_columns: set[str] = set()
    for _, row in ablation_df.iterrows():
        completed, expected = parse_complete_expected(row["complete_expected"])
        for split in ("train", "test"):
            for metric in METRIC_DIRECTIONS:
                col = f"{split}_{metric}"
                if col not in ablation_df.columns:
                    missing_metric_columns.add(col)
                    continue
                long_rows.append(
                    {
                        "dataset": row["dataset"],
                        "dataset_label": short_dataset(row["dataset"]),
                        "variant": row["variant"],
                        "split": split,
                        "metric": metric,
                        "value": float(row[col]),
                        "better_direction": METRIC_DIRECTIONS[metric],
                        "completed_runs": completed,
                        "expected_runs": expected,
                        "interpretation_short": row["interpretation_short"],
                    }
                )
    for col in sorted(missing_metric_columns):
        audit.append(f"- ablation: source CSV lacks {col}; this metric is skipped in ablation outputs.")
    long_df = pd.DataFrame(long_rows)
    if long_df.empty:
        audit.append("- ablation: no metric columns were available; cleaned_ablation_results.csv is empty.")
        long_df.to_csv(DATA / "cleaned_ablation_results.csv", index=False)
        return long_df, pd.DataFrame()

    norm_parts = []
    for _, group in long_df.groupby(["dataset", "split", "metric"], sort=False):
        values = group["value"].to_numpy(dtype=float)
        score = -values if group["better_direction"].iloc[0] == "lower" else values
        mn, mx = float(score.min()), float(score.max())
        if math.isclose(mx, mn):
            normalized = np.full_like(score, 0.5, dtype=float)
        else:
            normalized = (score - mn) / (mx - mn)
        part = group.copy()
        part["normalized_score"] = normalized
        norm_parts.append(part)
    long_df = pd.concat(norm_parts, ignore_index=True)
    long_df.to_csv(DATA / "cleaned_ablation_results.csv", index=False)

    metric_cols = []
    for split in ("train", "test"):
        for metric in METRIC_DIRECTIONS:
            col = f"{split}_{metric}"
            if col in ablation_df.columns:
                metric_cols.append((split, metric, col))
            else:
                audit.append(f"- ablation compact: skipped missing column {col}.")

    rows = []
    for variant, group in ablation_df.groupby("variant", sort=False):
        weights = group["complete_expected"].apply(lambda x: parse_complete_expected(x)[0]).to_numpy(dtype=float)
        row = {"variant": variant, "valid_runs": int(weights.sum())}
        for split, metric, col in metric_cols:
            value = np.average(group[col].to_numpy(dtype=float), weights=weights)
            row[f"{split}_{metric}"] = value
        row["mean_normalized_score"] = long_df.loc[long_df["variant"] == variant, "normalized_score"].mean()
        row["interpretation"] = group["interpretation_short"].iloc[0]
        rows.append(row)
    compact = pd.DataFrame(rows)
    return long_df, compact


def build_metric_direction_map() -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {
                "metric": metric,
                "better_direction": direction,
                "paper_label": METRIC_LABELS[metric],
            }
            for metric, direction in METRIC_DIRECTIONS.items()
        ]
    )
    df.to_csv(DATA / "metric_direction_map.csv", index=False)
    return df


def build_win_counts(wins_df: pd.DataFrame, audit: list[str]) -> pd.DataFrame:
    wins = wins_df.copy()
    wins["win_rate_percent"] = wins["win_rate"].astype(str).str.rstrip("%").astype(float)
    wins["mean_delta"] = pd.to_numeric(wins["mean_delta"], errors="coerce")
    wins = clean_numeric(wins, ["rc_wins", "total_pairs", "win_rate_percent", "mean_delta"], "win-counts", audit)
    if "reflective_region_psnr" in set(wins["metric"]):
        audit.append("- win-counts: reflective_region_psnr aggregate rows are retained from the win-count source table.")
    wins.to_csv(DATA / "rc_win_counts_by_metric.csv", index=False)
    return wins


def build_tradeoff(tradeoff_df: pd.DataFrame, audit: list[str]) -> pd.DataFrame:
    tradeoff = tradeoff_df.copy()
    for col in ("consistency_improves", "full_quality_improves", "reflective_quality_improves"):
        tradeoff[col] = bool_series(tradeoff[col])
    if tradeoff["notes"].astype(str).str.contains("reflective_region_psnr", regex=False).any():
        audit.append("- tradeoff: reflective_region_psnr evidence is retained in trade-off notes from the source table.")
    tradeoff.to_csv(DATA / "rc_tradeoff_summary.csv", index=False)
    return tradeoff


def build_coverage() -> pd.DataFrame:
    rows = [
        {
            "experiment_group": "Main base-vs-RC, FD-P2-lite non-Shiny-Real",
            "expected_runs": 28,
            "completed_runs": 28,
            "valid_metrics": 28,
            "failed_oom_excluded": 0,
            "reason": "All non-Shiny-Real paired scene/split rows available.",
            "can_support_paper_claim": "Yes: scoped reflection-consistency comparison.",
        },
        {
            "experiment_group": "Ablation variants, FD-P2-lite non-Shiny-Real",
            "expected_runs": 42,
            "completed_runs": 42,
            "valid_metrics": 42,
            "failed_oom_excluded": 0,
            "reason": "wo_ref, wo_conf and rough_only completed for non-Shiny-Real scope.",
            "can_support_paper_claim": "Yes: scoped diagnostic ablation trends.",
        },
        {
            "experiment_group": "Full FD-P2 including Shiny Real main cells",
            "expected_runs": 34,
            "completed_runs": 29,
            "valid_metrics": 29,
            "failed_oom_excluded": 5,
            "reason": "Shiny Blender Real cells were incomplete/OOM and excluded.",
            "can_support_paper_claim": "No: do not claim complete full-dataset validation.",
        },
        {
            "experiment_group": "Full ablation including Shiny Real cells",
            "expected_runs": 51,
            "completed_runs": 42,
            "valid_metrics": 42,
            "failed_oom_excluded": 9,
            "reason": "Shiny Blender Real ablation cells were incomplete/OOM and excluded.",
            "can_support_paper_claim": "No: do not generalize ablation to Shiny Real.",
        },
        {
            "experiment_group": "Independent mesh or geometry-quality evaluation",
            "expected_runs": 0,
            "completed_runs": 0,
            "valid_metrics": 0,
            "failed_oom_excluded": 0,
            "reason": "No independent geometry-quality table is available in this result package.",
            "can_support_paper_claim": "No: do not claim mesh-quality improvement.",
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "experiment_coverage.csv", index=False)
    return df


def build_tables(cleaned_main: pd.DataFrame, wins: pd.DataFrame, ablation_compact: pd.DataFrame, coverage: pd.DataFrame, audit: list[str]) -> None:
    consistency = cleaned_main[cleaned_main["metric"] == "mean_reflection_consistency"]
    if consistency.empty:
        audit.append("- table1: skipped because mean_reflection_consistency is absent from cleaned main results.")
    else:
        table1 = (
            consistency.groupby("split")
            .agg(
                valid_paired_rows=("improvement", "size"),
                rc_wins=("winner", lambda s: int((s == "RC").sum())),
                mean_rc_minus_base_delta=("rc_minus_base_delta", "mean"),
                median_rc_minus_base_delta=("rc_minus_base_delta", "median"),
                mean_improvement_base_minus_rc=("improvement", "mean"),
                median_improvement_base_minus_rc=("improvement", "median"),
            )
            .reset_index()
        )
        table1["win_rate"] = table1["rc_wins"] / table1["valid_paired_rows"] * 100
        table1_csv = table1.copy()
        table1_csv.to_csv(DATA / "table1_main_reflection_consistency_data.csv", index=False)
        table1_tex = table1.copy()
        table1_tex["mean_rc_minus_base_delta"] = table1_tex["mean_rc_minus_base_delta"].map(lambda x: f"{x:.5f}")
        table1_tex["median_rc_minus_base_delta"] = table1_tex["median_rc_minus_base_delta"].map(lambda x: f"{x:.5f}")
        table1_tex["mean_improvement_base_minus_rc"] = table1_tex["mean_improvement_base_minus_rc"].map(lambda x: f"{x:.5f}")
        table1_tex["median_improvement_base_minus_rc"] = table1_tex["median_improvement_base_minus_rc"].map(lambda x: f"{x:.5f}")
        table1_tex["win_rate"] = table1_tex["win_rate"].map(lambda x: f"{x:.1f}%")
        table1_tex = table1_tex.rename(
            columns={
                "split": "Split",
                "valid_paired_rows": "Rows",
                "rc_wins": "RC wins",
                "mean_rc_minus_base_delta": "Mean delta",
                "median_rc_minus_base_delta": "Median delta",
                "mean_improvement_base_minus_rc": "Mean improvement",
                "median_improvement_base_minus_rc": "Median improvement",
                "win_rate": "Win rate",
            }
        )
        to_latex_table(
            table1_tex,
            TABLES / "table1_main_reflection_consistency.tex",
            "Main comparison on cross-view reflection consistency in completed FD-P2-lite non-Shiny-Real runs. Delta denotes RC minus base; lower is better, so positive improvement means base minus RC.",
            "tab:rc_main_consistency",
        )

    table2 = wins.copy()
    table2_csv = table2.copy()
    table2_csv.to_csv(DATA / "table2_quality_tradeoff_data.csv", index=False)
    table2_required = ["metric", "split", "better_direction", "rc_wins", "total_pairs", "win_rate_percent", "mean_delta", "interpretation"]
    if table2.empty or any(col not in table2.columns for col in table2_required):
        audit.append("- table2: skipped because win-count columns are incomplete.")
    else:
        table2_tex = table2[table2_required].copy()
        table2_tex["metric"] = table2_tex["metric"].map(METRIC_LABELS).fillna(table2_tex["metric"])
        table2_tex["win_rate_percent"] = table2_tex["win_rate_percent"].map(lambda x: f"{x:.1f}%")
        table2_tex["mean_delta"] = [
            format_metric(v, m)
            for v, m in zip(table2["mean_delta"], table2["metric"], strict=True)
        ]
        table2_tex = table2_tex.rename(
            columns={
                "metric": "Metric",
                "split": "Split",
                "better_direction": "Better",
                "rc_wins": "RC wins",
                "total_pairs": "Rows",
                "win_rate_percent": "Win rate",
                "mean_delta": "Mean delta",
                "interpretation": "Interpretation",
            }
        )
        to_latex_table(
            table2_tex,
            TABLES / "table2_quality_tradeoff.tex",
            "Rendering-quality trade-offs under RC training. Metric direction is listed explicitly; mean delta is RC minus base.",
            "tab:rc_quality_tradeoff",
        )

    table3 = ablation_compact.copy()
    table3_csv = table3.copy()
    table3_csv.to_csv(DATA / "table3_ablation_compact_data.csv", index=False)
    desired_cols = [
        "variant",
        "valid_runs",
        "train_mean_reflection_consistency",
        "test_mean_reflection_consistency",
        "train_full_psnr",
        "test_full_psnr",
        "train_reflective_psnr",
        "test_reflective_psnr",
        "mean_normalized_score",
        "interpretation",
    ]
    available_cols = [col for col in desired_cols if col in table3.columns]
    missing_cols = [col for col in desired_cols if col not in table3.columns]
    for col in missing_cols:
        audit.append(f"- table3: omitted missing ablation column {col}.")
    if not available_cols or table3.empty:
        audit.append("- table3: skipped because no ablation aggregate columns are available.")
    else:
        table3_tex = table3[available_cols].copy()
        for col in ("train_mean_reflection_consistency", "test_mean_reflection_consistency"):
            if col in table3_tex.columns:
                table3_tex[col] = table3_tex[col].map(lambda x: f"{x:.5f}")
        for col in ("train_full_psnr", "test_full_psnr", "train_reflective_psnr", "test_reflective_psnr"):
            if col in table3_tex.columns:
                table3_tex[col] = table3_tex[col].map(lambda x: f"{x:.2f}")
        if "mean_normalized_score" in table3_tex.columns:
            table3_tex["mean_normalized_score"] = table3_tex["mean_normalized_score"].map(lambda x: f"{x:.3f}")
        table3_tex = table3_tex.rename(
            columns={
                "variant": "Variant",
                "valid_runs": "Valid runs",
                "train_mean_reflection_consistency": "Train RC metric",
                "test_mean_reflection_consistency": "Test RC metric",
                "train_full_psnr": "Train full PSNR",
                "test_full_psnr": "Test full PSNR",
                "train_reflective_psnr": "Train refl. PSNR",
                "test_reflective_psnr": "Test refl. PSNR",
                "mean_normalized_score": "Norm. score",
                "interpretation": "Interpretation",
            }
        )
        to_latex_table(
            table3_tex,
            TABLES / "table3_ablation.tex",
            "Ablation aggregates for completed FD-P2-lite non-Shiny-Real runs. Reflection-consistency values are lower-is-better; normalized score is computed within available ablation variants after aligning metric directions.",
            "tab:rc_ablation",
        )

    claim_rows = [
        {
            "Claim": "RC improves mean reflection consistency.",
            "Supported?": "Yes, scoped",
            "Evidence type": "completed paired scene/split CSV",
            "Scope": "FD-P2-lite non-Shiny-Real",
            "Safe wording": "RC improves cross-view reflection consistency in the completed setting.",
            "Unsafe wording": "RC universally improves all reflective reconstruction results.",
        },
        {
            "Claim": "RC improves full-image PSNR/SSIM/LPIPS.",
            "Supported?": "No universal support",
            "Evidence type": "metric-specific win counts",
            "Scope": "available rows only",
            "Safe wording": "Full-image metrics show mixed, metric-dependent changes.",
            "Unsafe wording": "RC guarantees better full-image rendering quality.",
        },
        {
            "Claim": "Reflective-region quality always improves.",
            "Supported?": "No",
            "Evidence type": "reflective-region metric win counts",
            "Scope": "available rows only",
            "Safe wording": "Reflective-region quality should be reported separately from consistency.",
            "Unsafe wording": "RC consistently improves all reflective-region metrics.",
        },
        {
            "Claim": "Confidence weighting contributes to RC.",
            "Supported?": "Trend only",
            "Evidence type": "scoped ablation aggregate",
            "Scope": "wo_conf diagnostic rows",
            "Safe wording": "Removing confidence weighting weakens the observed consistency behavior in this ablation scope.",
            "Unsafe wording": "Confidence weighting is always the dominant factor.",
        },
        {
            "Claim": "Roughness smoothness alone reproduces RC.",
            "Supported?": "No",
            "Evidence type": "rough_only ablation aggregate",
            "Scope": "available non-Shiny-Real rows",
            "Safe wording": "Roughness-only regularization does not reproduce the main RC consistency behavior.",
            "Unsafe wording": "Roughness smoothness is the central theoretical contribution.",
        },
        {
            "Claim": "RC improves mesh or geometry quality.",
            "Supported?": "No",
            "Evidence type": "no independent geometry metric table",
            "Scope": "current result package",
            "Safe wording": "Geometry filtering is an engineering extension requiring separate evaluation.",
            "Unsafe wording": "RC necessarily improves mesh quality.",
        },
    ]
    table4 = pd.DataFrame(claim_rows)
    table4.to_csv(DATA / "table4_claim_boundary_data.csv", index=False)
    to_latex_table(
        table4,
        TABLES / "table4_claim_boundary.tex",
        "Claim boundary for interpreting the available RC results.",
        "tab:rc_claim_boundary",
    )

    table5 = coverage.copy()
    table5.to_csv(DATA / "table5_experiment_coverage_data.csv", index=False)
    table5_tex = table5.rename(
        columns={
            "experiment_group": "Experiment group",
            "expected_runs": "Expected",
            "completed_runs": "Completed",
            "valid_metrics": "Valid metrics",
            "failed_oom_excluded": "Failed/OOM/excluded",
            "reason": "Reason",
            "can_support_paper_claim": "Can support claim?",
        }
    )
    to_latex_table(
        table5_tex,
        TABLES / "table5_experiment_coverage.tex",
        "Experiment coverage for the available RC result package.",
        "tab:rc_experiment_coverage",
    )


def plot_win_counts(wins: pd.DataFrame, audit: list[str]) -> None:
    required = {"metric", "split", "win_rate_percent", "rc_wins", "total_pairs"}
    missing = required - set(wins.columns)
    if wins.empty or missing:
        audit.append(f"- fig1: skipped because win-count data are empty or missing columns {sorted(missing)}.")
        return
    metrics = list(dict.fromkeys(wins["metric"]))
    labels = [METRIC_LABELS[m] for m in metrics]
    y = np.arange(len(metrics))
    height = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for offset, split in [(-height / 2, "train"), (height / 2, "test")]:
        sub = wins[wins["split"] == split].set_index("metric").reindex(metrics)
        if sub.empty or sub["win_rate_percent"].isna().all():
            audit.append(f"- fig1: skipped {split} layer because no win-rate rows are available.")
            continue
        bars = ax.barh(y + offset, sub["win_rate_percent"], height=height, label=split, color=PALETTE[split])
        for bar, (_, row) in zip(bars, sub.iterrows(), strict=True):
            if pd.isna(row["win_rate_percent"]):
                continue
            ax.text(
                bar.get_width() + 1.0,
                bar.get_y() + bar.get_height() / 2,
                f"{int(row['rc_wins'])}/{int(row['total_pairs'])}",
                va="center",
                fontsize=8,
            )
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 108)
    ax.set_xlabel("RC win rate (%)")
    ax.set_title("RC wins by metric and split")
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    ax.legend(frameon=False, loc="lower right")
    save_figure(fig, "fig1_rc_win_count_by_metric")


def plot_reflection_delta(cleaned_main: pd.DataFrame, audit: list[str]) -> None:
    required = {"metric", "dataset_label", "scene", "split", "improvement"}
    missing = required - set(cleaned_main.columns)
    if cleaned_main.empty or missing:
        audit.append(f"- fig2: skipped because cleaned main data are empty or missing columns {sorted(missing)}.")
        return
    consistency = cleaned_main[cleaned_main["metric"] == "mean_reflection_consistency"].copy()
    if consistency.empty:
        audit.append("- fig2: skipped because mean_reflection_consistency is absent from cleaned main results.")
        return
    consistency["scene_label"] = consistency["dataset_label"] + "/" + consistency["scene"]
    order = (
        consistency.groupby("scene_label")["improvement"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    pivot = consistency.pivot(index="scene_label", columns="split", values="improvement").reindex(order)
    missing_splits = [split for split in ("train", "test") if split not in pivot.columns]
    for split in missing_splits:
        audit.append(f"- fig2: {split} layer omitted because that split is missing.")
    x = np.arange(len(pivot))
    width = 0.38
    fig, ax = plt.subplots(figsize=(8.0, 4.3))
    if "train" in pivot.columns:
        ax.bar(x - width / 2, pivot["train"], width, label="train", color=PALETTE["train"])
    if "test" in pivot.columns:
        ax.bar(x + width / 2, pivot["test"], width, label="test", color=PALETTE["test"])
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, rotation=45, ha="right")
    ax.set_ylabel("Reflection consistency improvement (base - RC)")
    ax.set_title("Per-scene reflection consistency improvement")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.legend(frameon=False)
    save_figure(fig, "fig2_per_scene_reflection_delta")


def plot_tradeoff(cleaned_main: pd.DataFrame, audit: list[str]) -> None:
    required = {"metric", "dataset", "dataset_label", "scene", "split", "improvement"}
    missing = required - set(cleaned_main.columns)
    if cleaned_main.empty or missing:
        audit.append(f"- fig3: skipped because cleaned main data are empty or missing columns {sorted(missing)}.")
        return
    if "mean_reflection_consistency" not in set(cleaned_main["metric"]):
        audit.append("- fig3: skipped because mean_reflection_consistency is absent from cleaned main results.")
        return
    quality_metric = None
    for candidate in ("full_psnr", "full_lpips"):
        if candidate in set(cleaned_main["metric"]):
            quality_metric = candidate
            break
    if quality_metric is None:
        audit.append("- fig3: skipped because neither full_psnr nor full_lpips is present in cleaned main results.")
        return
    refl = cleaned_main[cleaned_main["metric"] == "mean_reflection_consistency"][
        ["dataset", "dataset_label", "scene", "split", "improvement"]
    ].rename(columns={"improvement": "reflection_improvement"})
    quality = cleaned_main[cleaned_main["metric"] == quality_metric][
        ["dataset", "scene", "split", "improvement"]
    ].rename(columns={"improvement": "quality_improvement"})
    merged = refl.merge(quality, on=["dataset", "scene", "split"], how="inner")
    if merged.empty:
        audit.append(f"- fig3: skipped because no paired rows exist for mean_reflection_consistency and {quality_metric}.")
        return
    fig, ax = plt.subplots(figsize=(5.8, 4.5))
    for split, sub in merged.groupby("split"):
        ax.scatter(
            sub["reflection_improvement"],
            sub["quality_improvement"],
            label=split,
            s=42,
            alpha=0.85,
            color=PALETTE[split],
            edgecolor="white",
            linewidth=0.5,
        )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Reflection consistency improvement (base - RC)")
    ylabel = "Full-image PSNR change (RC - base)" if quality_metric == "full_psnr" else "Full-image LPIPS improvement (base - RC)"
    ax.set_ylabel(ylabel)
    ax.set_title("Consistency gain vs. rendering-quality change")
    ax.grid(linestyle=":", alpha=0.4)
    ax.legend(frameon=False)
    save_figure(fig, "fig3_tradeoff_scatter")


def plot_ablation_heatmap(ablation_long: pd.DataFrame, audit: list[str]) -> None:
    required = {"variant", "metric", "normalized_score"}
    missing = required - set(ablation_long.columns)
    if ablation_long.empty or missing:
        audit.append(f"- fig4: skipped because ablation data are empty or missing columns {sorted(missing)}.")
        return
    plot_metrics = [
        "mean_reflection_consistency",
        "full_psnr",
        "full_ssim",
        "full_lpips",
        "reflective_psnr",
        "reflective_ssim",
        "reflective_lpips",
    ]
    available_metrics = [metric for metric in plot_metrics if metric in set(ablation_long["metric"])]
    for metric in sorted(set(plot_metrics) - set(available_metrics)):
        audit.append(f"- fig4: omitted missing ablation metric {metric}.")
    if not available_metrics:
        audit.append("- fig4: skipped because none of the requested heatmap metrics are present.")
        return
    mat = (
        ablation_long[ablation_long["metric"].isin(available_metrics)]
        .groupby(["variant", "metric"])["normalized_score"]
        .mean()
        .unstack("metric")
        .reindex(index=["wo_ref", "wo_conf", "rough_only"], columns=available_metrics)
    )
    mat = mat.dropna(axis=0, how="all").dropna(axis=1, how="all")
    if mat.empty:
        audit.append("- fig4: skipped because normalized ablation matrix is empty after dropping missing rows/columns.")
        return
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad("#F2F2F2")
    masked = np.ma.masked_invalid(mat.to_numpy(dtype=float))
    image = ax.imshow(masked, vmin=0, vmax=1, cmap=cmap, aspect="auto")
    ax.set_xticks(np.arange(len(mat.columns)))
    ax.set_xticklabels([METRIC_LABELS[m] for m in mat.columns], rotation=35, ha="right")
    ax.set_yticks(np.arange(len(mat.index)))
    ax.set_yticklabels(mat.index)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            value = mat.iloc[i, j]
            if pd.isna(value):
                ax.text(j, i, "--", ha="center", va="center", fontsize=8, color="black")
            else:
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8, color="white" if value < 0.5 else "black")
    cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Normalized score (higher is better)")
    ax.set_title("Ablation normalized performance")
    save_figure(fig, "fig4_ablation_heatmap")


def plot_coverage(coverage: pd.DataFrame, audit: list[str]) -> None:
    required = {"completed_runs", "failed_oom_excluded", "expected_runs"}
    missing = required - set(coverage.columns)
    if coverage.empty or missing:
        audit.append(f"- fig5: skipped because coverage data are empty or missing columns {sorted(missing)}.")
        return
    labels = [
        "Main\nnon-Shiny",
        "Ablation\nnon-Shiny",
        "Full main\nincl. Real",
        "Full ablation\nincl. Real",
        "Geometry\nmetrics",
    ]
    completed = coverage["completed_runs"].to_numpy(dtype=float)
    excluded = coverage["failed_oom_excluded"].to_numpy(dtype=float)
    expected = coverage["expected_runs"].to_numpy(dtype=float)
    missing = np.maximum(expected - completed - excluded, 0)
    x = np.arange(len(coverage))
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    ax.bar(x, completed, label="completed", color=PALETTE["completed"])
    ax.bar(x, excluded, bottom=completed, label="failed/OOM/excluded", color=PALETTE["excluded"])
    ax.bar(x, missing, bottom=completed + excluded, label="not scheduled/absent", color="#999999")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Run or metric count")
    ax.set_title("Experiment coverage and exclusions")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.legend(frameon=False, loc="upper right")
    save_figure(fig, "fig5_experiment_coverage")


def write_captions() -> None:
    table_text = """# Table captions / 表格标题

## Table 1
中文：表 1 汇总 FD-P2-lite / non-Shiny-Real 已完成主实验中的 cross-view reflection consistency 对比。Delta 表示 RC minus base，reflection consistency 数值越低越好，因此 improvement 采用 base minus RC。该表支持 RC 在该范围内主要改善反射一致性，但不包含可用于反推 base/RC 绝对值的原始逐场景数值。

English: Table 1 summarizes cross-view reflection consistency on the completed FD-P2-lite / non-Shiny-Real main runs. Delta denotes RC minus base; lower reflection-consistency values are better, so improvement is reported as base minus RC. The table supports a scoped consistency gain, but it does not contain the raw per-scene base/RC absolute values.

## Table 2
中文：表 2 展示不同指标上的 RC win count、win rate 和平均 delta。PSNR/SSIM 数值越高越好，LPIPS 和 reflection consistency 数值越低越好。结果表明渲染质量指标存在 mixed / trade-off，不能写成全图质量全面提升。

English: Table 2 reports RC win counts, win rates and mean deltas across metrics. Higher is better for PSNR/SSIM, whereas lower is better for LPIPS and reflection consistency. The results indicate mixed rendering-quality effects and should not be interpreted as a universal full-image quality improvement.

## Table 3
中文：表 3 汇总已完成消融实验中的 wo_ref、wo_conf 和 rough_only 变体。Reflection consistency 为越低越好，归一化分数在统一指标方向后、仅在可用消融变体内部计算。该表用于分析消融趋势，不应被解读为 roughness smoothness 或 confidence filtering 的独立主贡献。

English: Table 3 summarizes the completed ablation variants wo_ref, wo_conf and rough_only. Reflection consistency is lower-is-better, and the normalized score is computed only among available ablation variants after aligning metric directions. The table is intended for diagnostic ablation analysis rather than promoting roughness smoothness or confidence filtering as standalone main contributions.

## Table 4
中文：表 4 给出论文主张边界，将有结果支持的表述与不安全表述分开。证据范围限于当前可用 FD-P2-lite / non-Shiny-Real 结果及其消融聚合。该表用于避免把反射一致性收益误写为全局渲染质量或 mesh quality 的必然提升。

English: Table 4 states claim boundaries by separating supported wording from unsafe wording. The evidence scope is limited to the available FD-P2-lite / non-Shiny-Real results and their ablation aggregates. The table helps prevent consistency gains from being overstated as guaranteed full-image or mesh-quality improvements.

## Table 5
中文：表 5 统计当前实验覆盖、完成情况与排除项。Shiny Blender Real 的 incomplete/OOM 单元被明确排除，独立几何质量指标在当前结果包中不可用。该表限定了本文结果可以支持和不能支持的实验结论。

English: Table 5 reports experiment coverage, completed runs and exclusions. Incomplete/OOM Shiny Blender Real cells are explicitly excluded, and independent geometry-quality metrics are unavailable in the current result package. The table defines which experimental conclusions are supported and which are not.
"""
    figure_text = """# Figure captions / 图标题

## Figure 1
中文：图 1 展示 RC 在不同指标和 split 上的 win count / total。Reflection consistency 与 LPIPS 为越低越好，PSNR/SSIM 为越高越好。RC 在 reflection consistency 上最稳定，而图像质量指标呈现 mixed 趋势。

English: Figure 1 shows RC win counts over total valid rows across metrics and splits. Lower is better for reflection consistency and LPIPS, while higher is better for PSNR/SSIM. RC is most stable on reflection consistency, whereas image-quality metrics show mixed behavior.

## Figure 2
中文：图 2 展示每个 scene/split 的 reflection consistency improvement，其中正值表示 base minus RC 大于零，即 RC 更好。该图仅统计 FD-P2-lite / non-Shiny-Real 已完成 paired rows。除一个 test row 外，多数场景呈现一致性改善，但该图不评价全图渲染质量。

English: Figure 2 shows per-scene reflection-consistency improvement, where positive values indicate base minus RC is greater than zero. The plot includes only completed FD-P2-lite / non-Shiny-Real paired rows. Most scenes improve in consistency except one test row, but the figure does not assess full-image rendering quality.

## Figure 3
中文：图 3 将 reflection consistency improvement 与 full-image PSNR change 进行配对散点展示。横轴越大表示反射一致性改善越强，纵轴为 RC minus base 的 PSNR 变化。散点分布说明反射一致性收益与全图 PSNR 改善并不完全一致，因此需要分开报告。

English: Figure 3 plots reflection-consistency improvement against full-image PSNR change for paired rows. Larger x-values indicate stronger consistency gains, and the y-axis is the RC-minus-base PSNR change. The distribution shows that consistency gains do not necessarily coincide with full-image PSNR improvements, motivating separate reporting.

## Figure 4
中文：图 4 展示可用消融变体在多个指标上的归一化表现。所有指标先按方向统一为越高越好，再在每个 dataset/split/metric 内做 min-max normalization。该图用于比较 wo_ref、wo_conf 和 rough_only 的相对趋势，不包含缺失的 base/RC 原始聚合值。

English: Figure 4 visualizes normalized performance for available ablation variants across metrics. All metrics are first direction-aligned so that higher is better and then min-max normalized within each dataset/split/metric group. The figure compares relative trends for wo_ref, wo_conf and rough_only, without fabricating missing raw base/RC aggregate values.

## Figure 5
中文：图 5 展示主实验、消融实验和不可用几何指标的覆盖情况。已完成 non-Shiny-Real 结果可用于有限范围的 consistency 和 ablation 结论，Shiny Blender Real incomplete/OOM 单元与几何质量结论不能作为完成实验使用。该图用于限定论文结果的外推范围。

English: Figure 5 summarizes coverage for main runs, ablations and unavailable geometry metrics. Completed non-Shiny-Real results support scoped consistency and ablation conclusions, whereas incomplete/OOM Shiny Blender Real cells and absent geometry metrics cannot be treated as completed evidence. The figure constrains the extrapolation scope of the paper results.

## Figure 6 plan
中文：当前脚本未生成 qualitative montage，因为未指定可核验的 GT/base/RC/specular/mask 图像集合。若后续补充渲染图，可按 GT / base / RC / error / specular / reflective mask 的列布局制作，并在每个 panel 标明 scene、split、method 和 metric。

English: This script does not generate a qualitative montage because no verified GT/base/RC/specular/mask image set is specified. If render images are provided later, a GT / base / RC / error / specular / reflective mask layout can be assembled with scene, split, method and metric labels for every panel.
"""
    (CAPTIONS / "table_captions_zh_en.md").write_text(table_text, encoding="utf-8")
    (CAPTIONS / "figure_captions_zh_en.md").write_text(figure_text, encoding="utf-8")


def write_audit_and_summaries(audit_lines: list[str]) -> None:
    audit_text = f"""# Experiment Data Audit

## Source priority

- Primary numerical sources: `{SOURCE_FILES['main'].relative_to(ROOT)}`, `{SOURCE_FILES['wins'].relative_to(ROOT)}`, `{SOURCE_FILES['ablation'].relative_to(ROOT)}`, and `{SOURCE_FILES['tradeoff'].relative_to(ROOT)}`.
- The final FD-P2-lite analysis is treated as the authoritative scope definition for paper assets: FD-P2-lite / non-Shiny-Real / completed runs only.
- Older full-dataset and recovery notes are used only to document coverage limits, especially incomplete/OOM Shiny Blender Real cells.

## Data transformations

- Main paired-scene rows are converted from RC-minus-base deltas into direction-aware improvements.
- Reflection consistency and LPIPS are treated as lower-is-better; PSNR and SSIM are treated as higher-is-better.
- Table 1 reports compact deltas and win counts because the available source table does not contain raw base and RC absolute per-scene values.
- Ablation heatmaps use only available variants (`wo_ref`, `wo_conf`, `rough_only`); missing base/RC aggregate values are not inferred.
- No original result CSV, log or metric file is overwritten.

## Missing or excluded evidence

- Shiny Blender Real incomplete/OOM cells are excluded from paper claims.
- Full FD-P2 and full 51-cell ablation conclusions remain unsupported by this result package.
- No independent mesh or geometry-quality metric table is available here; mesh-quality claims are therefore unsupported.
- No qualitative montage is generated because a verified image set was not provided.

## Cleaning log

{chr(10).join(audit_lines) if audit_lines else "- No NaN/inf rows were removed from the source CSVs."}
"""
    (OUT / "experiment_data_audit.md").write_text(audit_text, encoding="utf-8")

    boundary_text = """# Experiment Claim Boundary

| Claim | Supported by available results? | Evidence type | Scope | Safe wording | Unsafe wording |
|---|---|---|---|---|---|
| RC improves cross-view reflection consistency. | Yes, within scope. | Completed paired-scene CSV and win counts. | FD-P2-lite / non-Shiny-Real / train and test paired rows. | RC improves cross-view reflection consistency in the completed FD-P2-lite non-Shiny-Real setting. | RC universally improves all reflective reconstruction results. |
| RC improves full-image PSNR/SSIM/LPIPS. | Not as a universal claim. | Metric-specific win counts and trade-off rows. | Available completed rows only. | Full-image metrics show mixed, metric-dependent changes and should be reported separately. | RC guarantees better full-image rendering quality. |
| RC improves reflective-region quality. | Mixed support. | Reflective-region win counts. | Available completed rows only. | Reflective-region quality has mixed metric-specific behavior. | RC always improves reflective-region PSNR/SSIM/LPIPS. |
| Confidence weighting contributes to the RC behavior. | Trend-level support. | wo_conf ablation aggregate. | FD-P2-lite non-Shiny-Real ablation rows. | Removing confidence weighting weakens the observed consistency behavior in this scoped ablation. | Confidence weighting is always the dominant or sufficient factor. |
| Roughness smoothness alone explains RC. | No. | rough_only ablation aggregate. | FD-P2-lite non-Shiny-Real ablation rows. | Roughness-only regularization does not reproduce the main RC consistency behavior. | Roughness smoothness is the theoretical core of RC. |
| RC improves mesh quality. | No. | No independent geometry metric table in the result package. | Current available results. | Geometry filtering should be treated as an engineering extension requiring separate evaluation. | RC necessarily improves mesh or geometry quality. |
"""
    (OUT / "experiment_claim_boundary.md").write_text(boundary_text, encoding="utf-8")

    summary_text = """# RC Results Summary (中文)

## 1. 主实验结论

在已完成的 FD-P2-lite / non-Shiny-Real 范围内，RC 的主要、最稳定收益体现在 cross-view reflection consistency。主实验的 paired scene/split 统计显示，train split 的有效行均由 RC 取得更低的一致性误差，test split 中除一个场景外也呈现一致性改善。因此，论文中可以安全表述为：RC 在当前完成范围内主要改善几何一致区域中的跨视角反射预测稳定性。

## 2. 渲染质量 trade-off

Full-image PSNR/SSIM/LPIPS 与 reflective-region PSNR/SSIM/LPIPS 不应和 reflection consistency 合并成单一“质量提升”结论。现有 win count 与 trade-off 行显示，不同图像质量指标之间存在 mixed behavior：部分场景和 split 中 RC 改善一致性的同时会降低至少一个渲染质量指标。因此，论文结果应将 reflection consistency、reflective-region quality 和 full-image quality 分开报告。

## 3. 消融实验结论

消融结果支持有限范围内的诊断性结论：去除 reflection-consistency supervision 的 wo_ref 不能复现 RC 的主要一致性行为；去除 confidence weighting 的 wo_conf 会削弱观察到的一致性趋势，但不能据此声称 confidence 是所有场景中的唯一或主导因素；rough_only 不能单独复现 RC 的 reflection consistency 行为。因此，roughness smoothness 应作为辅助正则讨论，而不是 RC 模块组的核心理论贡献。

## 4. 实验覆盖与限制

当前可用于论文主结论的范围是 FD-P2-lite / non-Shiny-Real / 已完成 runs。Shiny Blender Real 的 incomplete/OOM 单元被排除，不能写成完整验证；full FD-P2 与 full ablation 也不能据此宣称全部完成。当前结果包没有独立几何或 mesh quality 指标，因此不能主张 RC 必然改善几何质量或 mesh quality。

## 5. 论文安全表述

Safe claim：RC 在已完成 FD-P2-lite / non-Shiny-Real 设置下主要改善 cross-view reflection consistency，并且该收益需要与 full-image 和 reflective-region 渲染质量指标分开评价。

Unsafe claim：RC 全面优于所有 baseline、必然提升 PSNR/SSIM/LPIPS、已在所有 reflective datasets 上完成验证，或必然提升 mesh quality。
"""
    (OUT / "rc_results_summary_zh.md").write_text(summary_text, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    audit: list[str] = []
    main_df = read_csv_checked(
        "main",
        [
            "dataset",
            "scene",
            "train_rc_delta_consistency",
            "test_rc_delta_consistency",
            "consistency_win_train",
            "consistency_win_test",
        ],
    )
    required_main_delta_cols = []
    for split in ("train", "test"):
        for suffix in (
            "consistency",
            "full_psnr",
            "full_ssim",
            "full_lpips",
            "reflective_psnr",
            "reflective_ssim",
            "reflective_lpips",
        ):
            required_main_delta_cols.append(f"{split}_rc_delta_{suffix}")
    require_columns(main_df, required_main_delta_cols, SOURCE_FILES["main"].name)

    wins_df = read_csv_checked(
        "wins",
        ["metric", "split", "better_direction", "rc_wins", "total_pairs", "win_rate", "mean_delta", "interpretation"],
    )
    ablation_df = read_csv_checked(
        "ablation",
        ["dataset", "variant", "complete_expected", "train_mean_reflection_consistency", "test_mean_reflection_consistency", "interpretation_short"],
    )
    tradeoff_df = read_csv_checked(
        "tradeoff",
        ["dataset", "scene", "split", "consistency_improves", "full_quality_improves", "reflective_quality_improves", "tradeoff_category", "notes"],
    )

    build_metric_direction_map()
    cleaned_main = build_clean_main(main_df, audit)
    wins = build_win_counts(wins_df, audit)
    tradeoff = build_tradeoff(tradeoff_df, audit)
    coverage = build_coverage()
    ablation_long, ablation_compact = build_clean_ablation(ablation_df, audit)

    build_tables(cleaned_main, wins, ablation_compact, coverage, audit)
    plot_win_counts(wins, audit)
    plot_reflection_delta(cleaned_main, audit)
    plot_tradeoff(cleaned_main, audit)
    plot_ablation_heatmap(ablation_long, audit)
    plot_coverage(coverage, audit)
    write_captions()
    write_audit_and_summaries(audit)

    print(f"Wrote paper assets to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
