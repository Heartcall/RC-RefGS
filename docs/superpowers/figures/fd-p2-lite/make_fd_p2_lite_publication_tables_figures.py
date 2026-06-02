#!/usr/bin/env python3
"""Generate scope-limited FD-P2-lite publication tables and figures."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

CACHE_ROOT = Path("/tmp/rc_refgs_fd_p2_lite_cache")
MPL_CONFIG_DIR = CACHE_ROOT / "matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve()
OUT_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]
LOG_DIR = REPO_ROOT / "docs" / "superpowers" / "logs"

ANALYSIS_JSON = LOG_DIR / "rc-refgs-fd-p2-lite-final-results-analysis-2026-06-01.json"
MAIN_CSV = LOG_DIR / "rc-refgs-fd-p2-lite-final-main-summary-2026-06-01.csv"
ABLATION_CSV = LOG_DIR / "rc-refgs-fd-p2-lite-final-ablation-summary-2026-06-01.csv"
TRADEOFF_CSV = LOG_DIR / "rc-refgs-fd-p2-lite-final-tradeoff-summary-2026-06-01.csv"

METRICS = [
    "mean_reflection_consistency",
    "reflective_region_psnr",
    "full_psnr",
    "full_ssim",
    "full_lpips",
    "reflective_psnr",
    "reflective_ssim",
    "reflective_lpips",
]
SPLITS = ["train", "test"]
BETTER_DIRECTION = {
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
    "mean_reflection_consistency": "Consistency error",
    "reflective_region_psnr": "Reflective-region PSNR",
    "full_psnr": "Full PSNR",
    "full_ssim": "Full SSIM",
    "full_lpips": "Full LPIPS",
    "reflective_psnr": "Reflective PSNR",
    "reflective_ssim": "Reflective SSIM",
    "reflective_lpips": "Reflective LPIPS",
}
SHORT_METRIC_LABELS = {
    "mean_reflection_consistency": "Consistency",
    "reflective_region_psnr": "Region\nPSNR",
    "full_psnr": "Full\nPSNR",
    "full_ssim": "Full\nSSIM",
    "full_lpips": "Full\nLPIPS",
    "reflective_psnr": "Reflective\nPSNR",
    "reflective_ssim": "Reflective\nSSIM",
    "reflective_lpips": "Reflective\nLPIPS",
}
DATASET_LABELS = {
    "shiny_blender_synthetic": "Shiny Blender Synthetic",
    "glossy_synthetic": "Glossy Synthetic",
}
VARIANT_LABELS = {
    "wo_ref": "wo_ref",
    "wo_conf": "wo_conf",
    "rough_only": "rough_only",
}
COLORS = {
    "train": "#2C6E9B",
    "test": "#E07A3F",
    "consistency": "#2C6E9B",
    "quality": "#5A9E68",
    "excluded": "#B65C5C",
    "neutral": "#707070",
}


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "figure.dpi": 120,
            "savefig.bbox": "tight",
            "svg.hashsalt": "rc-refgs-fd-p2-lite",
        }
    )


def load_inputs() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    analysis = json.loads(ANALYSIS_JSON.read_text())
    main_csv = pd.read_csv(MAIN_CSV)
    ablation_csv = pd.read_csv(ABLATION_CSV)
    tradeoff_csv = pd.read_csv(TRADEOFF_CSV)

    coverage = analysis["coverage"]
    if coverage["overall_non_shiny_real"]["strict_complete_models"] != 70:
        raise ValueError("Expected strict non-Shiny-Real complete-metric coverage of 70/70")
    if len(main_csv) != 14 or len(ablation_csv) != 6 or len(tradeoff_csv) != 28:
        raise ValueError("Unexpected frozen final-analysis CSV row counts")
    return analysis, main_csv, ablation_csv, tradeoff_csv


def latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def display_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{value:.6f}"
    return str(value)


def markdown_table(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    rows = [[display_value(value) for value in row] for row in frame.itertuples(index=False)]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines) + "\n"


def latex_table(frame: pd.DataFrame) -> str:
    columns = "l" * len(frame.columns)
    lines = [
        r"\begin{tabular}{" + columns + "}",
        r"\toprule",
        " & ".join(latex_escape(column) for column in frame.columns) + r" \\",
        r"\midrule",
    ]
    for row in frame.itertuples(index=False):
        lines.append(" & ".join(latex_escape(display_value(value)) for value in row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    return "\n".join(lines)


def write_table(frame: pd.DataFrame, stem: str) -> None:
    frame.to_csv(OUT_DIR / f"{stem}.csv", index=False, float_format="%.6f")
    (OUT_DIR / f"{stem}.md").write_text(markdown_table(frame))
    (OUT_DIR / f"{stem}.tex").write_text(latex_table(frame))


def save_figure(figure: plt.Figure, stem: str) -> None:
    creator = "RC-RefGS FD-P2-lite publication generator"
    figure.savefig(
        OUT_DIR / f"{stem}.pdf",
        metadata={"Creator": creator, "CreationDate": datetime(2026, 6, 1)},
    )
    figure.savefig(
        OUT_DIR / f"{stem}.svg",
        metadata={"Creator": creator, "Date": "2026-06-01"},
    )
    figure.savefig(
        OUT_DIR / f"{stem}.png",
        dpi=300,
        metadata={"Software": creator},
    )
    plt.close(figure)


def summarize_tradeoff(tradeoff_rows: list[dict[str, Any]]) -> str:
    parts = []
    for row in tradeoff_rows:
        worsened = ", ".join(row["all_worsened_metrics"]) or "none"
        parts.append(f"{row['split']}: worsened={worsened}")
    return "; ".join(parts)


def build_table1(analysis: dict[str, Any]) -> pd.DataFrame:
    tradeoffs_by_scene: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in analysis["tradeoff_summary"]["scene_split_rows"]:
        tradeoffs_by_scene.setdefault((row["dataset"], row["scene"]), []).append(row)

    rows = []
    for pair in analysis["main_summary"]["pairwise_results"]:
        row: dict[str, Any] = {"dataset": pair["dataset"], "scene": pair["scene"]}
        for split in SPLITS:
            metrics = pair["splits"][split]["metrics"]
            row[f"{split}_rc_delta_consistency"] = metrics["mean_reflection_consistency"][
                "delta_rc_minus_base"
            ]
            for metric in [
                "full_psnr",
                "full_ssim",
                "full_lpips",
                "reflective_psnr",
                "reflective_ssim",
                "reflective_lpips",
            ]:
                row[f"{split}_rc_delta_{metric}"] = metrics[metric]["delta_rc_minus_base"]
            row[f"consistency_win_{split}"] = metrics["mean_reflection_consistency"]["rc_wins"]
        row["quality_tradeoff_summary"] = summarize_tradeoff(
            tradeoffs_by_scene[(pair["dataset"], pair["scene"])]
        )
        rows.append(row)

    ordered_columns = ["dataset", "scene"]
    for metric in [
        "consistency",
        "full_psnr",
        "full_ssim",
        "full_lpips",
        "reflective_psnr",
        "reflective_ssim",
        "reflective_lpips",
    ]:
        ordered_columns.extend([f"train_rc_delta_{metric}", f"test_rc_delta_{metric}"])
    ordered_columns.extend(
        ["consistency_win_train", "consistency_win_test", "quality_tradeoff_summary"]
    )
    return pd.DataFrame(rows)[ordered_columns]


def metric_interpretation(metric: str, wins: int, total: int) -> str:
    if metric == "mean_reflection_consistency":
        return "RC consistency-target effect"
    if wins > total / 2:
        return "RC wins a majority; report separately from consistency"
    if wins == total / 2:
        return "Balanced outcomes; mixed render-quality effect"
    return "RC wins a minority; render-quality tradeoff"


def build_table2(analysis: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for metric in METRICS:
        for split in SPLITS:
            win_data = analysis["main_win_counts_by_metric_and_split"][metric][split]
            wins = win_data["rc_wins"]
            total = win_data["total_pairs"]
            rows.append(
                {
                    "metric": metric,
                    "split": split,
                    "better_direction": BETTER_DIRECTION[metric],
                    "rc_wins": wins,
                    "total_pairs": total,
                    "win_rate": f"{100.0 * wins / total:.1f}%",
                    "mean_delta": analysis["main_mean_deltas_by_metric_and_split"][metric][
                        split
                    ],
                    "interpretation": metric_interpretation(metric, wins, total),
                }
            )
    return pd.DataFrame(rows)


def ablation_interpretation(variant: str) -> str:
    return {
        "wo_ref": "Removal of reflection-consistency supervision; compare cautiously to RC.",
        "wo_conf": "Neutralized confidence weighting; compare cautiously to RC.",
        "rough_only": "Roughness-only regularization; compare cautiously to RC.",
    }[variant]


def build_table3(analysis: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for aggregate in analysis["ablation_summary_by_dataset_variant"]:
        row: dict[str, Any] = {
            "dataset": aggregate["dataset"],
            "variant": aggregate["variant"],
            "complete_expected": f"{aggregate['complete_models']}/{aggregate['expected_models']}",
        }
        for split in SPLITS:
            metrics = aggregate["splits"][split]["metrics"]
            for metric in METRICS:
                row[f"{split}_{metric}"] = metrics[metric]["ablation_mean"]
        row["interpretation_short"] = ablation_interpretation(aggregate["variant"])
        rows.append(row)
    ordered_columns = ["dataset", "variant", "complete_expected"]
    for metric in METRICS:
        ordered_columns.extend([f"train_{metric}", f"test_{metric}"])
    ordered_columns.append("interpretation_short")
    return pd.DataFrame(rows)[ordered_columns]


def tradeoff_category(row: dict[str, Any]) -> str:
    if not row["consistency_improved"]:
        return "no_consistency_gain"
    improved = row["full_image_improved_metrics"] + row["reflective_improved_metrics"]
    worsened = row["full_image_worsened_metrics"] + row["reflective_worsened_metrics"]
    if improved and not worsened:
        return "consistency_gain_quality_gain"
    if worsened and not improved:
        return "consistency_gain_quality_drop"
    if improved or worsened:
        return "consistency_gain_quality_mixed"
    return "ambiguous"


def build_table4(analysis: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for source_row in analysis["tradeoff_summary"]["scene_split_rows"]:
        rows.append(
            {
                "dataset": source_row["dataset"],
                "scene": source_row["scene"],
                "split": source_row["split"],
                "consistency_improves": source_row["consistency_improved"],
                "full_quality_improves": bool(source_row["full_image_improved_metrics"]),
                "reflective_quality_improves": bool(source_row["reflective_improved_metrics"]),
                "tradeoff_category": tradeoff_category(source_row),
                "notes": (
                    "improves="
                    + (", ".join(source_row["all_improved_metrics"]) or "none")
                    + "; worsens="
                    + (", ".join(source_row["all_worsened_metrics"]) or "none")
                ),
            }
        )
    return pd.DataFrame(rows)


def scene_labels(frame: pd.DataFrame) -> list[str]:
    prefixes = {
        "shiny_blender_synthetic": "SBS",
        "glossy_synthetic": "GS",
    }
    return [f"{prefixes[row.dataset]}: {row.scene}" for row in frame.itertuples()]


def make_figure1(table1: pd.DataFrame) -> None:
    labels = scene_labels(table1)
    positions = np.arange(len(table1))
    width = 0.38
    figure, axis = plt.subplots(figsize=(11.5, 4.8))
    axis.bar(
        positions - width / 2,
        table1["train_rc_delta_consistency"],
        width,
        label="Train",
        color=COLORS["train"],
    )
    axis.bar(
        positions + width / 2,
        table1["test_rc_delta_consistency"],
        width,
        label="Test",
        color=COLORS["test"],
    )
    axis.axhline(0.0, color="#333333", linewidth=0.8)
    axis.set_xticks(positions, labels, rotation=48, ha="right")
    axis.set_ylabel("RC - base consistency-error delta")
    axis.set_title("FD-P2-lite RC reflection-consistency delta by scene")
    axis.text(
        0.01,
        0.97,
        "Negative is better",
        transform=axis.transAxes,
        va="top",
        fontsize=8,
    )
    axis.legend(frameon=False)
    figure.tight_layout()
    save_figure(figure, "fig1_rc_consistency_delta_by_scene")


def make_figure2(table2: pd.DataFrame) -> None:
    positions = np.arange(len(METRICS))
    width = 0.38
    figure, axis = plt.subplots(figsize=(11.5, 4.9))
    for offset, split in [(-width / 2, "train"), (width / 2, "test")]:
        rows = table2[table2["split"] == split].set_index("metric").loc[METRICS]
        rates = rows["rc_wins"] / rows["total_pairs"]
        axis.bar(positions + offset, rates, width, label=split.title(), color=COLORS[split])
    axis.axvspan(-0.5, 0.5, color="#DDEBF2", alpha=0.65, zorder=0)
    axis.axhline(0.5, color="#777777", linewidth=0.8, linestyle="--")
    axis.set_ylim(0.0, 1.08)
    axis.set_xticks(positions, [SHORT_METRIC_LABELS[metric] for metric in METRICS])
    axis.set_ylabel("RC win rate")
    axis.set_title("FD-P2-lite RC win rates by metric")
    axis.legend(frameon=False, ncol=2)
    axis.text(
        0.01,
        -0.26,
        "Consistency and LPIPS: lower is better. PSNR and SSIM: higher is better. "
        "Consistency bars are highlighted.",
        transform=axis.transAxes,
        fontsize=8,
    )
    figure.subplots_adjust(bottom=0.30)
    save_figure(figure, "fig2_rc_win_rates_by_metric")


def make_figure3(analysis: dict[str, Any]) -> None:
    rows = []
    for pair in analysis["main_summary"]["pairwise_results"]:
        metrics = pair["splits"]["test"]["metrics"]
        rows.append(
            {
                "dataset": pair["dataset"],
                "scene": pair["scene"],
                "consistency_delta": metrics["mean_reflection_consistency"]["delta_rc_minus_base"],
                "full_lpips_delta": metrics["full_lpips"]["delta_rc_minus_base"],
            }
        )
    frame = pd.DataFrame(rows)
    figure, axis = plt.subplots(figsize=(7.4, 5.6))
    for dataset, subset in frame.groupby("dataset", sort=False):
        axis.scatter(
            subset["consistency_delta"],
            subset["full_lpips_delta"],
            label=DATASET_LABELS[dataset],
            s=42,
            alpha=0.88,
        )
    axis.axhline(0.0, color="#555555", linewidth=0.8)
    axis.axvline(0.0, color="#555555", linewidth=0.8)
    axis.set_xlabel("Test consistency-error delta, RC - base (lower is better)")
    axis.set_ylabel("Test full-LPIPS delta, RC - base (lower is better)")
    axis.set_title("FD-P2-lite consistency vs full-LPIPS tradeoff")

    notable = {frame.loc[frame["consistency_delta"].idxmin(), "scene"], "coffee"}
    notable.update(
        frame.loc[
            (frame["consistency_delta"] < 0) & (frame["full_lpips_delta"] > 0), "scene"
        ].tolist()
    )
    for row in frame.itertuples():
        if row.scene in notable:
            axis.annotate(
                row.scene,
                (row.consistency_delta, row.full_lpips_delta),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=7,
            )
    axis.legend(frameon=False, fontsize=8)
    figure.tight_layout()
    save_figure(figure, "fig3_consistency_quality_tradeoff_map")


def make_figure4(table3: pd.DataFrame) -> None:
    metric_specs = [
        ("mean_reflection_consistency", "Consistency error"),
        ("full_lpips", "Full LPIPS"),
        ("reflective_lpips", "Reflective LPIPS"),
    ]
    figure, axes = plt.subplots(2, 3, figsize=(12.0, 6.5))
    variants = ["wo_ref", "wo_conf", "rough_only"]
    positions = np.arange(len(variants))
    width = 0.38
    for row_index, dataset in enumerate(DATASET_LABELS):
        subset = table3[table3["dataset"] == dataset].set_index("variant").loc[variants]
        for column_index, (metric, label) in enumerate(metric_specs):
            axis = axes[row_index, column_index]
            axis.bar(
                positions - width / 2,
                subset[f"train_{metric}"],
                width,
                label="Train",
                color=COLORS["train"],
            )
            axis.bar(
                positions + width / 2,
                subset[f"test_{metric}"],
                width,
                label="Test",
                color=COLORS["test"],
            )
            axis.set_xticks(positions, [VARIANT_LABELS[variant] for variant in variants])
            axis.set_title(label)
            if column_index == 0:
                axis.set_ylabel(DATASET_LABELS[dataset])
            if row_index == 0 and column_index == 2:
                axis.legend(frameon=False)
    figure.suptitle("Non-Shiny-Real ablation aggregates (lower is better for all panels)", y=1.01)
    figure.tight_layout()
    save_figure(figure, "fig4_ablation_aggregate_comparison")


def make_figure5() -> None:
    labels = [
        "Main FD-P2-lite",
        "Ablation non-Shiny-Real",
        "Complete metrics",
    ]
    completed = [28, 42, 70]
    expected = [28, 42, 70]
    positions = np.arange(len(labels))
    figure, axis = plt.subplots(figsize=(8.4, 4.2))
    axis.barh(positions, [100.0] * len(labels), color="#ECECEC", height=0.55)
    axis.barh(positions, [100.0 * a / b for a, b in zip(completed, expected)], color=COLORS["quality"], height=0.55)
    axis.set_yticks(positions, labels)
    axis.set_xlim(0, 100)
    axis.set_xlabel("Scoped complete-metric coverage (%)")
    axis.set_title("FD-P2-lite / non-Shiny-Real scope coverage")
    axis.invert_yaxis()
    for position, done, total in zip(positions, completed, expected):
        axis.text(98, position, f"{done}/{total}", ha="right", va="center", color="white", weight="bold")
    axis.text(
        0.0,
        -0.28,
        "Excluded: Shiny Blender Real (OOM-blocked). This chart does not imply full 17-scene completion.",
        transform=axis.transAxes,
        fontsize=8,
        color=COLORS["excluded"],
    )
    figure.subplots_adjust(bottom=0.25)
    save_figure(figure, "fig5_scope_coverage_summary")


def write_readme() -> None:
    readme = """# FD-P2-lite Publication Tables and Figures

## Scope

This package reports FD-P2-lite / non-Shiny-Real evidence only. It uses the 14 scoped scenes from Shiny Blender Synthetic and Glossy Synthetic. Shiny Blender Real is excluded due to OOM. Original full FD-P2 and full 51-cell ablation claims remain NO-GO.

Scoped complete-metric coverage is `70/70`: main base/RC comparison `28/28`, and non-Shiny-Real ablation comparison `42/42`.

## Input Files

- `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-results-analysis-2026-06-01.json`
- `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-main-summary-2026-06-01.csv`
- `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-ablation-summary-2026-06-01.csv`
- `docs/superpowers/logs/rc-refgs-fd-p2-lite-final-tradeoff-summary-2026-06-01.csv`

The generator reads only these frozen final-analysis artifacts. It does not run training, metrics, recovery, or GPU work.

## Generated Tables

- `table1_main_base_vs_rc_summary.{csv,md,tex}`: 14 paired-scene rows with RC-minus-base deltas and consistency win flags.
- `table2_rc_win_counts_by_metric.{csv,md,tex}`: 16 metric-split rows with directions, RC win rates, mean deltas, and cautious interpretations.
- `table3_ablation_aggregate.{csv,md,tex}`: 6 dataset-variant aggregate rows for `wo_ref`, `wo_conf`, and `rough_only`.
- `table4_tradeoff_summary.{csv,md,tex}`: 28 scene-split rows. This is the documented scene-by-split convention for tradeoff reporting.

Numeric deltas use `RC - base`. For consistency and LPIPS, lower is better. For PSNR and SSIM, higher is better.

## Generated Figures

- `fig1_rc_consistency_delta_by_scene.{pdf,svg,png}`: scene-level train/test consistency deltas; negative is better.
- `fig2_rc_win_rates_by_metric.{pdf,svg,png}`: train/test RC win rates with metric-direction note.
- `fig3_consistency_quality_tradeoff_map.{pdf,svg,png}`: test consistency-error delta versus test full-LPIPS delta.
- `fig4_ablation_aggregate_comparison.{pdf,svg,png}`: dataset-separated ablation aggregates for consistency, full LPIPS, and reflective LPIPS.
- `fig5_scope_coverage_summary.{pdf,svg,png}`: scoped coverage panel with the Shiny Blender Real OOM exclusion stated explicitly.

Use PDF or SVG for publication layout and PNG for quick review.

## Regenerate

```bash
python docs/superpowers/figures/fd-p2-lite/make_fd_p2_lite_publication_tables_figures.py
```

## Claim Boundary

- FD-P2-lite / non-Shiny-Real only.
- Shiny Blender Real excluded due to OOM.
- Original full FD-P2 and full 51-cell ablation claims remain NO-GO.
"""
    (OUT_DIR / "README.md").write_text(readme)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    configure_style()
    analysis, _main_csv, _ablation_csv, _tradeoff_csv = load_inputs()
    table1 = build_table1(analysis)
    table2 = build_table2(analysis)
    table3 = build_table3(analysis)
    table4 = build_table4(analysis)

    write_table(table1, "table1_main_base_vs_rc_summary")
    write_table(table2, "table2_rc_win_counts_by_metric")
    write_table(table3, "table3_ablation_aggregate")
    write_table(table4, "table4_tradeoff_summary")

    make_figure1(table1)
    make_figure2(table2)
    make_figure3(analysis)
    make_figure4(table3)
    make_figure5()
    write_readme()

    print("Generated FD-P2-lite / non-Shiny-Real publication package")
    print(f"Output directory: {OUT_DIR}")
    print("Tables: 4 families; figures: 5 families; README: 1")


if __name__ == "__main__":
    main()
