#!/usr/bin/env python3
"""Diagnose reflective-region metric degradation under RC training.

This script reads existing result CSVs and writes derived diagnostic tables,
figures, and a Chinese analysis report. It does not modify source metrics or
launch any training/evaluation job.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper_assets"
DIAG = OUT / "diagnostics"
DATA = OUT / "data"

MAIN_WIDE = DATA / "main_full_metrics_by_dataset_wide.csv"
ABLATION_WIDE = DATA / "ablation_full_metrics_by_dataset_wide.csv"
TRADEOFF = DATA / "rc_tradeoff_summary.csv"
WIN_COUNTS = DATA / "rc_win_counts_by_metric.csv"

METRIC_DIRECTIONS = {
    "mean_reflection_consistency": "lower",
    "reflective_region_psnr": "higher",
    "reflective_psnr": "higher",
    "reflective_ssim": "higher",
    "reflective_lpips": "lower",
    "full_psnr": "higher",
    "full_ssim": "higher",
    "full_lpips": "lower",
}

REFL_METRICS = ["reflective_psnr", "reflective_ssim", "reflective_lpips"]
REFL_WITH_REGION = ["reflective_region_psnr", *REFL_METRICS]
HEATMAP_METRICS = ["mean_reflection_consistency", *REFL_METRICS]
VARIANT_ORDER = ["base", "rc", "wo_ref", "wo_conf", "rough_only"]

METRIC_LABELS = {
    "mean_reflection_consistency": "Reflection consistency",
    "reflective_region_psnr": "Region PSNR",
    "reflective_psnr": "Refl. PSNR",
    "reflective_ssim": "Refl. SSIM",
    "reflective_lpips": "Refl. LPIPS",
    "full_psnr": "Full PSNR",
    "full_ssim": "Full SSIM",
    "full_lpips": "Full LPIPS",
}

PALETTE = {
    "train": "#0072B2",
    "test": "#D55E00",
    "positive": "#009E73",
    "negative": "#CC79A7",
}


def ensure_dirs() -> None:
    DIAG.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return pd.read_csv(path)


def require_columns(df: pd.DataFrame, columns: Iterable[str], source: Path) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{rel(source)} missing columns {missing}; actual columns: {', '.join(df.columns)}")


def direction(metric: str) -> str:
    return METRIC_DIRECTIONS.get(metric, "unknown")


def improvement(base: float, rc: float, metric: str) -> float:
    if not np.isfinite(base) or not np.isfinite(rc):
        return np.nan
    return base - rc if direction(metric) == "lower" else rc - base


def format_num(value: float, metric: str | None = None) -> str:
    if value is None or not np.isfinite(value):
        return "--"
    if metric == "mean_reflection_consistency":
        return f"{value:.5f}"
    if metric and "psnr" in metric:
        return f"{value:.3f}"
    if metric and ("ssim" in metric or "lpips" in metric):
        return f"{value:.6f}"
    return f"{value:.4f}"


def latex_escape(text: object) -> str:
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


def write_latex_table(df: pd.DataFrame, path: Path, caption: str, label: str) -> None:
    tabular = df.to_latex(index=False, escape=True)
    text = (
        "\\begin{table*}[t]\n"
        "\\centering\n"
        f"\\caption{{{caption}}}\n"
        f"\\label{{{label}}}\n"
        "\\resizebox{\\textwidth}{!}{%\n"
        f"{tabular}"
        "}\n"
        "\\end{table*}\n"
    )
    path.write_text(text, encoding="utf-8")


def save_fig(fig: plt.Figure, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(DIAG / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(DIAG / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def build_main_improvements(main: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in main.iterrows():
        for metric in ["mean_reflection_consistency", *REFL_WITH_REGION, "full_psnr", "full_ssim", "full_lpips"]:
            bcol = f"base_{metric}"
            rcol = f"rc_{metric}"
            if bcol not in main.columns or rcol not in main.columns:
                continue
            base = pd.to_numeric(row[bcol], errors="coerce")
            rc = pd.to_numeric(row[rcol], errors="coerce")
            imp = improvement(float(base), float(rc), metric)
            rows.append(
                {
                    "dataset": row["dataset"],
                    "split": row["split"],
                    "scene": row["scene"],
                    "metric": metric,
                    "base_value": float(base) if np.isfinite(base) else np.nan,
                    "rc_value": float(rc) if np.isfinite(rc) else np.nan,
                    "metric_direction": direction(metric),
                    "improvement": imp,
                    "winner": "RC" if imp > 1e-12 else ("base" if imp < -1e-12 else "tie"),
                    "source_file": rel(MAIN_WIDE),
                }
            )
    return pd.DataFrame(rows)


def degradation_summary(improvements: pd.DataFrame) -> pd.DataFrame:
    rows = []
    sub = improvements[improvements["metric"].isin(REFL_WITH_REGION)].copy()
    for (dataset, split, metric), group in sub.groupby(["dataset", "split", "metric"], sort=False):
        valid = group[np.isfinite(group["improvement"])].copy()
        if valid.empty:
            continue
        worst = valid.loc[valid["improvement"].idxmin()]
        best = valid.loc[valid["improvement"].idxmax()]
        rows.append(
            {
                "dataset": dataset,
                "split": split,
                "metric": metric,
                "win": int((valid["improvement"] > 1e-12).sum()),
                "loss": int((valid["improvement"] < -1e-12).sum()),
                "tie": int((valid["improvement"].abs() <= 1e-12).sum()),
                "mean_improvement": valid["improvement"].mean(),
                "median_improvement": valid["improvement"].median(),
                "std_improvement": valid["improvement"].std(ddof=0),
                "min_improvement": valid["improvement"].min(),
                "max_improvement": valid["improvement"].max(),
                "worst_scene": f"{worst['scene']} ({format_num(worst['improvement'], metric)})",
                "best_scene": f"{best['scene']} ({format_num(best['improvement'], metric)})",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(DIAG / "tableD2_refl_metric_degradation_summary.csv", index=False)
    tex = df.copy()
    for col in ["mean_improvement", "median_improvement", "std_improvement", "min_improvement", "max_improvement"]:
        tex[col] = [format_num(v, m) for v, m in zip(tex[col], tex["metric"], strict=True)]
    tex["metric"] = tex["metric"].map(METRIC_LABELS)
    write_latex_table(
        tex,
        DIAG / "tableD2_refl_metric_degradation_summary.tex",
        "Reflective-region metric degradation summary. Positive improvement means RC is better after aligning metric directions.",
        "tab:diag_refl_metric_degradation",
    )
    return df


def metric_definition_table() -> pd.DataFrame:
    rows = [
        {
            "Metric / Loss": "RGB reconstruction loss",
            "Operates on": "composited final pbr_rgb vs ground-truth RGB",
            "Region / Mask": "full image; alpha-composited where RGBA is available",
            "Direction": "lower loss",
            "Optimized during training?": "Yes",
            "Potential mismatch": "single-view RGB fitting can reward view-specific highlight placement",
        },
        {
            "Metric / Loss": "RC loss",
            "Operates on": "spec_light sampled across source-target view projection",
            "Region / Mask": "projection valid, depth consistency, source/target alpha, source roughness, normal agreement, specular confidence",
            "Direction": "lower",
            "Optimized during training?": "Yes, scheduled when lambda_ref_consistency > 0",
            "Potential mismatch": "regularizes specular stability, not final RGB pixel fidelity",
        },
        {
            "Metric / Loss": "mean_reflection_consistency",
            "Operates on": "same spec_light consistency loss on evaluation pairs",
            "Region / Mask": "same RC correspondence masks and weights",
            "Direction": "lower better",
            "Optimized during training?": "Indirectly aligned with RC loss",
            "Potential mismatch": "does not evaluate ground-truth RGB reconstruction",
        },
        {
            "Metric / Loss": "reflective_region_psnr",
            "Operates on": "final pbr_rgb vs ground-truth RGB",
            "Region / Mask": "alpha > 0.2 and roughness < 0.6",
            "Direction": "higher better",
            "Optimized during training?": "No direct loss",
            "Potential mismatch": "uses image-space mask without RC depth/normal/correspondence confidence",
        },
        {
            "Metric / Loss": "Refl. PSNR / SSIM / LPIPS",
            "Operates on": "final rendered RGB vs ground-truth RGB",
            "Region / Mask": "reflective mask from alpha and roughness in render-quality evaluation",
            "Direction": "PSNR/SSIM higher; LPIPS lower",
            "Optimized during training?": "No direct loss",
            "Potential mismatch": "single-view masked image metrics are sensitive to highlight shifts and mask definition",
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(DIAG / "tableD1_metric_definition_mismatch.csv", index=False)
    write_latex_table(
        df,
        DIAG / "tableD1_metric_definition_mismatch.tex",
        "Definition mismatch between RC optimization and reflective-region image-quality metrics.",
        "tab:diag_metric_definition_mismatch",
    )
    return df


def correlations(improvements: pd.DataFrame) -> pd.DataFrame:
    cons = improvements[improvements["metric"] == "mean_reflection_consistency"][
        ["dataset", "split", "scene", "improvement"]
    ].rename(columns={"improvement": "consistency_improvement"})
    rows = []
    for metric in REFL_METRICS:
        q = improvements[improvements["metric"] == metric][["dataset", "split", "scene", "improvement"]].rename(
            columns={"improvement": "quality_improvement"}
        )
        merged = cons.merge(q, on=["dataset", "split", "scene"], how="inner")
        if len(merged) >= 3:
            pearson = merged["consistency_improvement"].corr(merged["quality_improvement"], method="pearson")
            spearman = merged["consistency_improvement"].corr(merged["quality_improvement"], method="spearman")
        else:
            pearson = np.nan
            spearman = np.nan
        rows.append(
            {
                "metric": metric,
                "n": len(merged),
                "pearson": pearson,
                "spearman": spearman,
                "tradeoff_rows": int(((merged["consistency_improvement"] > 0) & (merged["quality_improvement"] < 0)).sum()),
            }
        )
    return pd.DataFrame(rows)


def ablation_vs_rc_summary(ablation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    key_cols = ["dataset", "split", "scene"]
    rc = ablation[ablation["variant"] == "rc"].set_index(key_cols)
    for variant in [v for v in VARIANT_ORDER if v != "rc"]:
        var = ablation[ablation["variant"] == variant].set_index(key_cols)
        common = var.join(rc, lsuffix="_variant", rsuffix="_rc", how="inner")
        for metric in HEATMAP_METRICS:
            vcol = f"{metric}_variant"
            rcol = f"{metric}_rc"
            if vcol not in common.columns or rcol not in common.columns:
                continue
            if direction(metric) == "lower":
                rel_imp = common[rcol] - common[vcol]  # positive means variant better than RC
            else:
                rel_imp = common[vcol] - common[rcol]
            rows.append(
                {
                    "variant": variant,
                    "metric": metric,
                    "win_vs_rc": int((rel_imp > 1e-12).sum()),
                    "loss_vs_rc": int((rel_imp < -1e-12).sum()),
                    "tie_vs_rc": int((rel_imp.abs() <= 1e-12).sum()),
                    "mean_improvement_vs_rc": rel_imp.mean(),
                    "n": int(rel_imp.notna().sum()),
                }
            )
    return pd.DataFrame(rows)


def plot_refl_improvements(improvements: pd.DataFrame) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(9.5, 7.2), sharex=True)
    labels = None
    for ax, metric in zip(axes, REFL_METRICS, strict=True):
        sub = improvements[improvements["metric"] == metric].copy()
        sub["label"] = sub["dataset"].str.replace("_synthetic", "", regex=False) + "/" + sub["scene"] + "/" + sub["split"]
        sub = sub.sort_values("improvement")
        labels = sub["label"].tolist()
        colors = [PALETTE["positive"] if v >= 0 else PALETTE["negative"] for v in sub["improvement"]]
        ax.bar(np.arange(len(sub)), sub["improvement"], color=colors)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_ylabel(METRIC_LABELS[metric])
        ax.grid(axis="y", linestyle=":", alpha=0.35)
    axes[-1].set_xticks(np.arange(len(labels)))
    axes[-1].set_xticklabels(labels, rotation=65, ha="right", fontsize=7)
    fig.suptitle("Reflective image-quality improvements by scene (positive = RC better)", y=1.01)
    save_fig(fig, "figD1_refl_metric_improvements_by_scene")


def plot_tradeoff_scatter(improvements: pd.DataFrame, corr_df: pd.DataFrame) -> None:
    cons = improvements[improvements["metric"] == "mean_reflection_consistency"][
        ["dataset", "split", "scene", "improvement"]
    ].rename(columns={"improvement": "consistency_improvement"})
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.4), sharex=True)
    for ax, metric in zip(axes, REFL_METRICS, strict=True):
        q = improvements[improvements["metric"] == metric][["dataset", "split", "scene", "improvement"]].rename(
            columns={"improvement": "quality_improvement"}
        )
        merged = cons.merge(q, on=["dataset", "split", "scene"], how="inner")
        for split, group in merged.groupby("split"):
            ax.scatter(
                group["consistency_improvement"],
                group["quality_improvement"],
                s=38,
                alpha=0.85,
                color=PALETTE.get(split, "#666666"),
                label=split,
                edgecolor="white",
                linewidth=0.5,
            )
        ax.axhline(0, color="black", linewidth=0.8)
        ax.axvline(0, color="black", linewidth=0.8)
        row = corr_df[corr_df["metric"] == metric].iloc[0]
        ax.set_title(f"{METRIC_LABELS[metric]}\nr={row['pearson']:.2f}, rho={row['spearman']:.2f}")
        ax.set_xlabel("Consistency improvement")
        ax.grid(linestyle=":", alpha=0.35)
    axes[0].set_ylabel("Reflective metric improvement")
    axes[-1].legend(frameon=False, loc="best")
    save_fig(fig, "figD2_consistency_vs_refl_quality_tradeoff")


def plot_ablation_heatmap(ablation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (dataset, split, scene, metric), group in ablation.groupby(["dataset", "split", "scene", "metric"], sort=False):
        if metric not in HEATMAP_METRICS:
            continue
        values = pd.to_numeric(group["value"], errors="coerce")
        aligned = -values if direction(metric) == "lower" else values
        if aligned.notna().sum() == 0:
            continue
        mn = aligned.min()
        mx = aligned.max()
        if math.isclose(float(mx), float(mn)):
            norm = pd.Series(0.5, index=group.index)
        else:
            norm = (aligned - mn) / (mx - mn)
        for idx, score in norm.items():
            rows.append(
                {
                    "variant": group.loc[idx, "variant"],
                    "metric": metric,
                    "normalized_score": float(score),
                }
            )
    norm_df = pd.DataFrame(rows)
    mat = (
        norm_df.groupby(["variant", "metric"])["normalized_score"]
        .mean()
        .unstack("metric")
        .reindex(index=VARIANT_ORDER, columns=HEATMAP_METRICS)
    )
    fig, ax = plt.subplots(figsize=(6.8, 3.0))
    image = ax.imshow(mat.to_numpy(dtype=float), vmin=0, vmax=1, cmap="viridis", aspect="auto")
    ax.set_xticks(np.arange(len(mat.columns)))
    ax.set_xticklabels([METRIC_LABELS[m] for m in mat.columns], rotation=30, ha="right")
    ax.set_yticks(np.arange(len(mat.index)))
    ax.set_yticklabels(mat.index)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            val = mat.iloc[i, j]
            ax.text(j, i, "--" if pd.isna(val) else f"{val:.2f}", ha="center", va="center", fontsize=8, color="white" if pd.notna(val) and val < 0.5 else "black")
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("Normalized score (higher is better)")
    ax.set_title("Ablation behavior on consistency and reflective metrics")
    save_fig(fig, "figD3_ablation_refl_metrics_heatmap")
    return mat.reset_index()


def long_ablation(ablation_wide: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in ablation_wide.iterrows():
        for metric in HEATMAP_METRICS + ["reflective_region_psnr", "full_psnr", "full_ssim", "full_lpips"]:
            if metric not in ablation_wide.columns:
                continue
            value = pd.to_numeric(row[metric], errors="coerce")
            if not np.isfinite(value):
                continue
            rows.append(
                {
                    "dataset": row["dataset"],
                    "split": row["split"],
                    "scene": row["scene"],
                    "variant": row["variant"],
                    "metric": metric,
                    "value": float(value),
                    "metric_direction": direction(metric),
                }
            )
    return pd.DataFrame(rows)


def hypothesis_table(summary: pd.DataFrame, corr_df: pd.DataFrame, abl_summary: pd.DataFrame) -> pd.DataFrame:
    refl_loss_rows = int((summary[summary["metric"].isin(REFL_METRICS)]["loss"]).sum())
    refl_total_rows = int((summary[summary["metric"].isin(REFL_METRICS)][["win", "loss", "tie"]].sum(axis=1)).sum())
    tradeoff_text = f"{refl_loss_rows}/{refl_total_rows} dataset-split-metric scene rows are losses after direction alignment"
    corr_text = "; ".join(
        f"{METRIC_LABELS[r.metric]} Pearson {r.pearson:.2f}, Spearman {r.spearman:.2f}, tradeoff rows {int(r.tradeoff_rows)}/{int(r.n)}"
        for r in corr_df.itertuples()
    )
    wo_conf = abl_summary[(abl_summary["variant"] == "wo_conf") & (abl_summary["metric"].isin(REFL_METRICS))]
    wo_conf_text = (
        f"wo_conf vs RC reflective metrics: mean wins {wo_conf['win_vs_rc'].sum()} / losses {wo_conf['loss_vs_rc'].sum()}"
        if not wo_conf.empty
        else "wo_conf comparison unavailable"
    )
    rows = [
        {
            "Hypothesis": "A. Optimization objective mismatch",
            "Evidence from code": "train.py optimizes RGB reconstruction plus scheduled reflection_consistency_loss; render_quality_eval.py computes masked final-RGB PSNR/SSIM/LPIPS.",
            "Evidence from metrics": corr_text,
            "Status": "Supported",
            "Safe conclusion": "Consistency improvement and masked RGB quality are related but non-equivalent objectives.",
            "Needed follow-up": "Report consistency and image quality separately; add joint objective sweeps.",
        },
        {
            "Hypothesis": "B. RC suppresses view-specific high-frequency highlights",
            "Evidence from code": "reflection_consistency_loss uses L1 residual between detached source spec_light and sampled target spec_light.",
            "Evidence from metrics": tradeoff_text,
            "Status": "Partially supported",
            "Safe conclusion": "The loss form can favor stable specular predictions; current data are consistent with but do not directly prove smoothing.",
            "Needed follow-up": "Measure highlight edge sharpness and specular-map variance before/after RC.",
        },
        {
            "Hypothesis": "C. RC mask and reflective metric mask are mismatched",
            "Evidence from code": "RC mask adds projection, depth consistency, target alpha, normal agreement and specular confidence; Refl. metrics use alpha/roughness mask on final RGB.",
            "Evidence from metrics": "Reflective metrics remain mixed despite strong consistency gains.",
            "Status": "Supported as mechanism, not quantified",
            "Safe conclusion": "The optimized correspondence region can differ from the evaluated reflective image region.",
            "Needed follow-up": "Export mask overlap, RC effective weight maps and reflective mask coverage.",
        },
        {
            "Hypothesis": "D. Wrong correspondence hurts reflective pixels",
            "Evidence from code": "RC projects source depth into target view and filters by depth tolerance, alpha and normal agreement.",
            "Evidence from metrics": "Scene-level outliers exist, but no depth-pass or normal-pass diagnostics are available.",
            "Status": "Unknown / plausible",
            "Safe conclusion": "Correspondence noise cannot be ruled out from current aggregate tables.",
            "Needed follow-up": "Log depth consistency pass rate, normal agreement and pair angle per scene.",
        },
        {
            "Hypothesis": "E. Confidence weighting creates region bias",
            "Evidence from code": "spec_conf = mean(spec_light) * (1 - roughness)^gamma; wo_conf uses gamma 0.0 in the runner.",
            "Evidence from metrics": wo_conf_text,
            "Status": "Partially supported",
            "Safe conclusion": "Confidence weighting contributes to consistency, but does not create a uniform reflective-quality benefit.",
            "Needed follow-up": "Plot specular confidence distributions and test scene-adaptive thresholds.",
        },
        {
            "Hypothesis": "F. Small reflective masks make image metrics sensitive",
            "Evidence from code": "masked image metrics zero out non-reflective pixels and evaluate only alpha/roughness-selected regions.",
            "Evidence from metrics": "No mask-area or per-image variance fields are present.",
            "Status": "Plausible but unverified",
            "Safe conclusion": "Metric sensitivity is a reasonable concern but needs mask coverage and variance evidence.",
            "Needed follow-up": "Record reflective mask area ratio and per-image metric variance.",
        },
        {
            "Hypothesis": "G. Trade-off is expected rather than a definite bug",
            "Evidence from code": "RC is an auxiliary scheduled regularizer on specular consistency, not a direct Refl. RGB loss.",
            "Evidence from metrics": "Final logs report consistency gains with mixed render-quality effects.",
            "Status": "Supported",
            "Safe conclusion": "The evidence supports an objective trade-off interpretation; it does not prove an implementation bug.",
            "Needed follow-up": "Run lambda/schedule/pair-angle sweeps and inspect qualitative specular maps.",
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(DIAG / "tableD3_hypothesis_evidence_matrix.csv", index=False)
    write_latex_table(
        df,
        DIAG / "tableD3_hypothesis_evidence_matrix.tex",
        "Hypothesis-evidence matrix for reflective-region metric degradation under RC.",
        "tab:diag_hypothesis_evidence",
    )
    return df


def diagnostic_data_used(main: pd.DataFrame, ablation: pd.DataFrame, tradeoff: pd.DataFrame, wins: pd.DataFrame) -> None:
    rows = [
        {
            "source_file": rel(MAIN_WIDE),
            "role": "main base-vs-RC absolute per-scene metrics",
            "rows": len(main),
            "columns_used": ", ".join([c for c in main.columns if c.startswith("base_") or c.startswith("rc_")][:20]),
        },
        {
            "source_file": rel(ABLATION_WIDE),
            "role": "ablation per-scene variant metrics",
            "rows": len(ablation),
            "columns_used": ", ".join([c for c in ["variant", *HEATMAP_METRICS, *REFL_METRICS] if c in ablation.columns]),
        },
        {
            "source_file": rel(TRADEOFF),
            "role": "trade-off categories and notes",
            "rows": len(tradeoff),
            "columns_used": ", ".join(tradeoff.columns),
        },
        {
            "source_file": rel(WIN_COUNTS),
            "role": "metric win counts",
            "rows": len(wins),
            "columns_used": ", ".join(wins.columns),
        },
    ]
    pd.DataFrame(rows).to_csv(DIAG / "diagnostic_data_used.csv", index=False)


def missing_fields_report() -> None:
    text = """# Diagnostic Missing Fields

The current result package is sufficient for aggregate metric diagnosis but not for attributing reflective quality degradation to a single mechanism. The following fields were not found and were not fabricated:

- reflective mask area ratio per image / scene;
- RC valid correspondence ratio;
- mean RC effective weight / weight sum;
- depth consistency pass rate;
- normal agreement mean or distribution;
- specular confidence mean or distribution;
- source-target pair angle distribution;
- per-scene lambda_RC sensitivity;
- highlight edge sharpness metric;
- specular map variance before/after RC;
- reflective_region_ssim and reflective_region_lpips columns. Available reflective_ssim and reflective_lpips are retained under their source metric names;
- per-image mask coverage and per-image Refl. metric variance.

Recommended lightweight logging for the next run: save mask area, RC mask overlap with the reflective evaluation mask, depth/normal pass rates, mean confidence, pair angle, and per-image reflective PSNR/SSIM/LPIPS variance.
"""
    (DIAG / "diagnostic_missing_fields.md").write_text(text, encoding="utf-8")


def top_scenes_table(improvements: pd.DataFrame, metric: str, k: int = 5, best: bool = False) -> str:
    sub = improvements[improvements["metric"] == metric].copy()
    sub["label"] = sub["dataset"] + "/" + sub["scene"] + "/" + sub["split"]
    sub = sub.sort_values("improvement", ascending=not best).head(k)
    lines = ["| scene/split | improvement | base | RC |", "|---|---:|---:|---:|"]
    for r in sub.itertuples():
        lines.append(f"| {r.label} | {format_num(r.improvement, metric)} | {format_num(r.base_value, metric)} | {format_num(r.rc_value, metric)} |")
    return "\n".join(lines)


def write_report(
    improvements: pd.DataFrame,
    summary: pd.DataFrame,
    corr_df: pd.DataFrame,
    abl_summary: pd.DataFrame,
    hypo: pd.DataFrame,
) -> None:
    overall_rows = []
    for metric in REFL_METRICS:
        sub = improvements[improvements["metric"] == metric]
        overall_rows.append(
            {
                "metric": METRIC_LABELS[metric],
                "win": int((sub["improvement"] > 1e-12).sum()),
                "loss": int((sub["improvement"] < -1e-12).sum()),
                "mean": sub["improvement"].mean(),
                "median": sub["improvement"].median(),
            }
        )
    overall_md = ["| metric | win | loss | mean improvement | median improvement |", "|---|---:|---:|---:|---:|"]
    for r in overall_rows:
        metric_key = next(k for k, v in METRIC_LABELS.items() if v == r["metric"])
        overall_md.append(f"| {r['metric']} | {r['win']} | {r['loss']} | {format_num(r['mean'], metric_key)} | {format_num(r['median'], metric_key)} |")

    corr_md = ["| metric | n | Pearson | Spearman | consistency-up quality-down rows |", "|---|---:|---:|---:|---:|"]
    for r in corr_df.itertuples():
        corr_md.append(f"| {METRIC_LABELS[r.metric]} | {r.n} | {r.pearson:.3f} | {r.spearman:.3f} | {r.tradeoff_rows} |")

    abl_md = ["| variant vs RC | metric | win | loss | mean improvement vs RC |", "|---|---|---:|---:|---:|"]
    for r in abl_summary[abl_summary["metric"].isin(HEATMAP_METRICS)].itertuples():
        abl_md.append(f"| {r.variant} | {METRIC_LABELS[r.metric]} | {r.win_vs_rc} | {r.loss_vs_rc} | {format_num(r.mean_improvement_vs_rc, r.metric)} |")

    text = f"""# Refl. Metrics Degradation Analysis

## 1. 现象概述

在当前 FD-P2-lite / non-Shiny-Real 完成实验范围内，RC 的 reflection consistency 改善与 Refl. PSNR、Refl. SSIM、Refl. LPIPS 的变化并不一致。按方向统一后的 improvement 定义为：PSNR/SSIM 使用 RC minus base，LPIPS 和 reflection consistency 使用 base minus RC，正值表示 RC 更好。整体统计如下：

{chr(10).join(overall_md)}

这说明 Refl. image quality 指标并没有随 reflection consistency 一起稳定提升。该现象不应被解释为 RC 必然失败，也不能说明 reflection consistency 指标无意义；更合理的解释是两类指标关注的误差形式不同。

## 2. 指标与训练目标不一致

训练中的基础重建项直接作用于 composited final RGB，即 `pbr_rgb` 与 ground-truth RGB 的 L1/DSSIM 组合。RC loss 则作用于 `spec_light`，通过 source depth 反投影、target projection 和双线性采样约束跨视角 specular prediction 的稳定性。其有效区域还经过 projection validity、depth consistency、source/target alpha、source roughness、normal agreement 和 specular confidence 加权。

相比之下，Refl. PSNR/SSIM/LPIPS 在 render-quality 评估中作用于 final rendered RGB，并使用 alpha 与 roughness 构成的 reflective mask。也就是说，RC 优化的是“几何对应区域内的 specular 稳定性”，而 Refl. image quality 衡量的是“单视角反射区域内 RGB 像素/感知误差”。这两个目标不必然同向。

## 3. 数据统计证据

reflection consistency 与 Refl. metrics 的相关性如下：

{chr(10).join(corr_md)}

最明显的 Refl. PSNR 下降场景：

{top_scenes_table(improvements, "reflective_psnr", best=False)}

最明显的 Refl. PSNR 改善场景：

{top_scenes_table(improvements, "reflective_psnr", best=True)}

最明显的 Refl. LPIPS 下降场景：

{top_scenes_table(improvements, "reflective_lpips", best=False)}

这些统计支持一个关键判断：存在多处“reflection consistency improvement > 0，但 Refl. quality improvement < 0”的行。因此，Refl. metrics 下降不是单个异常行造成的，而是当前 objective trade-off 的一部分。

## 4. 消融证据

消融表将 base、rc、wo_ref、wo_conf 和 rough_only 放在同一 scene/split 层级比较。各 variant 相对 RC 的方向统一结果如下，正值表示该 variant 在对应指标上优于 RC：

{chr(10).join(abl_md)}

`wo_ref` 相对 RC 通常牺牲 reflection consistency，但若干 Refl. metrics 可与 RC 持平或更好，说明去掉反射一致性项可能释放单视角反射区域 RGB 拟合。`wo_conf` 使用 gamma=0.0，削弱 roughness confidence 的指数作用；其结果表明 confidence weighting 有助于 consistency，但并不保证 Refl. quality 统一改善。`rough_only` 不能复现 RC 的 consistency 行为，且其 Refl. metrics 也呈现 dataset/metric 依赖，说明 roughness smoothness 不是 RC trade-off 的充分替代解释。

## 5. 可能机制解释

### Objective mismatch

代码和指标共同支持该解释。RC loss 是 specular correspondence regularization；Refl. PSNR/SSIM/LPIPS 是 masked final-RGB image metric。前者鼓励跨视角稳定，后者奖励单视角像素/感知对齐，尤其会惩罚高光位置和强度的小偏差。

### High-frequency specular smoothing

RC loss 使用 L1 形式使 target sampled specular 贴近 detached source specular。该形式可能抑制某些 view-specific sharp highlights，使高光更保守或更平滑。当前没有 specular edge sharpness 或 variance 诊断，因此这是代码机制与指标趋势共同支持的合理假设，而不是已经被直接证明的结论。

### Mask mismatch

RC mask 比 Refl. metric mask 更严格：除了 alpha/roughness 外，还包含 target projection、depth consistency、target alpha、normal agreement 和 specular confidence。Refl. metrics 的 reflective mask 只由 alpha/roughness 选区决定，并作用于 final RGB。因此评估区域可能覆盖 RC 没有强约束、或 RC 权重较低的反射像素。

### Correspondence noise

RC 依赖 depth back-projection 和 target projection。若高反射区域的 depth、alpha 或 normal 不稳定，错误 correspondence 可能把 specular signal 对齐到不正确表面，造成局部 RGB 质量下降。当前结果包没有 depth-pass rate、normal agreement distribution 或 pair-angle distribution，因此该解释只能列为 plausible but unverified。

### Confidence weighting bias

RC 的 `spec_conf` 与 mean specular intensity 和 `(1 - roughness)^gamma` 相关，默认 gamma 为 2.0；`wo_conf` 使用 gamma=0.0。该设计会让低 roughness / 高 specular 区域受到更强约束，可能改善 consistency，但也可能放大高光位置偏差对 Refl. metrics 的影响。消融趋势只支持“confidence affects consistency and quality trade-off”，不支持“confidence 是唯一原因”。

### Small reflective mask sensitivity

Refl. metrics 在反射 mask 内计算，反射区域通常面积小、高频强，并且对边界/高光位置敏感。当前缺少 mask area ratio 和 per-image variance，所以不能定量证明小 mask 方差是主因，但它是解释 LPIPS/SSIM 波动的合理后续诊断方向。

### Schedule / lambda trade-off

RC 默认在 warm-up 后按固定频率启用，并引入额外 target render。若 lambda、启动时刻或 pair selection 不匹配场景，可能带来 consistency 与 image quality 之间的 trade-off。当前表格没有 lambda sweep，因此不能判断最优调度。

## 6. 哪些解释有证据，哪些只是合理假设

{hypo.to_markdown(index=False)}

## 7. 论文中应如何表述

RC 的主要优化目标是跨视角反射预测的一致性，而 Refl. PSNR/SSIM/LPIPS 衡量的是反射区域内单视角 RGB 重建质量。二者关注的误差形式不同，因此在部分场景中会出现 reflection consistency 改善但 reflective-region image quality 下降的 trade-off。该现象说明 RC 更适合作为反射一致性正则，而非保证反射区域像素指标全面提升的通用插件。我们因此将 reflection consistency、reflective-region quality 和 full-image quality 分开报告，并在消融中明确分析 confidence weighting 与 roughness-only regularization 的作用边界。

## 8. 后续改进建议

1. 降低 `lambda_RC` 或采用 scene-adaptive lambda。
2. 更晚启动 RC，等待 depth、alpha 和 normal 更稳定。
3. 使用 color-preserving 或 perceptual-aware RC，减少对 final RGB 的副作用。
4. 对 RC loss 加 view-angle-aware weighting，避免过度约束大视角差高光。
5. 区分 sharp specular 与 broad specular，对尖锐高光降低一致性强度。
6. 改进 reflective mask，并报告 mask coverage 与 variance。
7. 尝试 symmetric but detached 或 EMA teacher，降低相互追逐不稳定性。
8. 对 pair selection 加 stronger overlap/depth/normal filtering。
9. 联合 reflective RGB reconstruction loss，使 consistency 与 masked RGB quality 更一致。
10. 记录 RC valid correspondence ratio、mean RC weight、depth pass rate、normal agreement、confidence distribution、pair angle distribution、highlight edge sharpness 和 specular map variance。
"""
    (DIAG / "refl_metrics_degradation_analysis_zh.md").write_text(text, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    main = read_csv(MAIN_WIDE)
    ablation_wide = read_csv(ABLATION_WIDE)
    tradeoff = read_csv(TRADEOFF)
    wins = read_csv(WIN_COUNTS)

    require_columns(main, ["dataset", "split", "scene", "base_mean_reflection_consistency", "rc_mean_reflection_consistency"], MAIN_WIDE)
    require_columns(ablation_wide, ["dataset", "split", "scene", "variant", "mean_reflection_consistency"], ABLATION_WIDE)

    diagnostic_data_used(main, ablation_wide, tradeoff, wins)
    missing_fields_report()
    metric_definition_table()

    improvements = build_main_improvements(main)
    improvements.to_csv(DIAG / "main_refl_metric_improvements_long.csv", index=False)
    summary = degradation_summary(improvements)
    corr_df = correlations(improvements)
    corr_df.to_csv(DIAG / "consistency_refl_quality_correlations.csv", index=False)
    ablation_long = long_ablation(ablation_wide)
    ablation_long.to_csv(DIAG / "ablation_refl_metrics_long.csv", index=False)
    abl_summary = ablation_vs_rc_summary(ablation_wide)
    abl_summary.to_csv(DIAG / "ablation_vs_rc_refl_metric_summary.csv", index=False)
    plot_refl_improvements(improvements)
    plot_tradeoff_scatter(improvements, corr_df)
    heatmap_df = plot_ablation_heatmap(ablation_long)
    heatmap_df.to_csv(DIAG / "ablation_refl_metrics_heatmap_values.csv", index=False)
    hypo = hypothesis_table(summary, corr_df, abl_summary)
    write_report(improvements, summary, corr_df, abl_summary, hypo)
    print(f"Wrote diagnostics to {rel(DIAG)}")


if __name__ == "__main__":
    main()
