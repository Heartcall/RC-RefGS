#!/usr/bin/env python3
"""Geometry/proxy evaluator for completed RC-RefGS paper assets.

The evaluator is intentionally conservative:
- it does not train;
- it does not fabricate GT geometry;
- it computes true mesh/depth/normal metrics only when required inputs exist;
- for the current FD-P2-lite/non-Shiny-Real package, it emits proxy-only
  diagnostics from existing final Gaussian point-cloud PLY files.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
import struct
from collections import defaultdict
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[3] / "paper_assets" / "geometry" / ".mplconfig"))

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[3]
GEOM_ROOT = REPO_ROOT / "paper_assets" / "geometry"
DATA_DIR = GEOM_ROOT / "data"
TABLE_DIR = GEOM_ROOT / "tables"
FIG_DIR = GEOM_ROOT / "figures"
QUAL_DIR = GEOM_ROOT / "qualitative"

MAIN_FULL = REPO_ROOT / "paper_assets/data/main_full_metrics_by_dataset_wide.csv"
ABLATION_FULL = REPO_ROOT / "paper_assets/data/ablation_full_metrics_by_dataset_wide.csv"
MAIN_LONG = REPO_ROOT / "paper_assets/data/main_full_metrics_by_dataset_long.csv"
ABLATION_LONG = REPO_ROOT / "paper_assets/data/ablation_full_metrics_by_dataset_long.csv"
GEOM_SIGNAL_INV = REPO_ROOT / "docs/superpowers/logs/rc-refgs-geometry-signal-inventory-2026-06-05.csv"

MAIN_MODEL_ROOT = Path("/tmp/rc_refgs_full_dataset_base_rc_i31000_20260527")
ABLATION_MODEL_ROOT = Path("/tmp/rc_refgs_full_dataset_ablations_i31000_20260528")
ITERATION = 31000

TRUE_GEOM_METRICS = [
    "chamfer_l1",
    "chamfer_l2",
    "fscore_0p5pct",
    "fscore_1pct",
    "fscore_2pct",
    "precision_1pct",
    "recall_1pct",
    "normal_mae",
    "normal_cosine",
    "depth_mae",
    "depth_rmse",
    "depth_absrel",
]
PROXY_METRICS = [
    "geometry_proxy_vertex_count",
    "geometry_proxy_bbox_diag",
    "geometry_proxy_vertex_count_delta_from_input",
]
METRIC_DIRECTION = {
    "geometry_proxy_vertex_count": "diagnostic",
    "geometry_proxy_bbox_diag": "diagnostic",
    "geometry_proxy_vertex_count_delta_from_input": "diagnostic",
}
VARIANTS = ["base", "rc", "wo_ref", "wo_conf", "rough_only"]

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


def _ensure_dirs() -> None:
    for d in [GEOM_ROOT, DATA_DIR, TABLE_DIR, FIG_DIR, QUAL_DIR, GEOM_ROOT / "scripts"]:
        d.mkdir(parents=True, exist_ok=True)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _json_load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _parse_ply_header(path: Path):
    with path.open("rb") as handle:
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
    return fmt, vertex_count, vertex_properties, data_offset


def load_ply_proxy(path: Path) -> dict[str, Any]:
    if not path or not path.exists():
        return {"exists": False, "vertex_count": None, "bbox_diag": None}
    fmt, vertex_count, properties, data_offset = _parse_ply_header(path)
    result = {"exists": True, "vertex_count": int(vertex_count), "bbox_diag": None}
    if vertex_count <= 0:
        return result
    prop_names = [name for name, _type in properties]
    if not all(axis in prop_names for axis in ("x", "y", "z")):
        return result
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    if fmt == "ascii":
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if line.strip() == "end_header":
                    break
            for _ in range(vertex_count):
                parts = handle.readline().strip().split()
                if len(parts) < len(properties):
                    break
                xyz = [float(parts[prop_names.index(axis)]) for axis in ("x", "y", "z")]
                for i, value in enumerate(xyz):
                    mins[i] = min(mins[i], value)
                    maxs[i] = max(maxs[i], value)
    elif fmt == "binary_little_endian":
        struct_fmt = "<" + "".join(PLY_TYPE_FORMATS.get(prop_type, "f") for _name, prop_type in properties)
        record_size = struct.calcsize(struct_fmt)
        x_index, y_index, z_index = [prop_names.index(axis) for axis in ("x", "y", "z")]
        with path.open("rb") as handle:
            handle.seek(data_offset)
            for _ in range(vertex_count):
                blob = handle.read(record_size)
                if len(blob) != record_size:
                    break
                values = struct.unpack(struct_fmt, blob)
                xyz = [float(values[x_index]), float(values[y_index]), float(values[z_index])]
                for i, value in enumerate(xyz):
                    mins[i] = min(mins[i], value)
                    maxs[i] = max(maxs[i], value)
    else:
        return result
    if all(math.isfinite(value) for value in mins + maxs):
        result["bbox_min"] = mins
        result["bbox_max"] = maxs
        result["bbox_diag"] = float(math.sqrt(sum((maxs[i] - mins[i]) ** 2 for i in range(3))))
    return result


def _nested_model_dir(seed_dir: Path, scene: str, variant: str) -> Path:
    # Shiny outputs often write directly under seed_0; converted Glossy outputs
    # often nest the model as seed_0/<scene>_blender_<variant>.
    direct_pc = seed_dir / "point_cloud" / f"iteration_{ITERATION}" / "point_cloud.ply"
    if direct_pc.exists():
        return seed_dir
    for child in seed_dir.iterdir() if seed_dir.exists() else []:
        if child.is_dir() and (child / "point_cloud" / f"iteration_{ITERATION}" / "point_cloud.ply").exists():
            return child
    return seed_dir


def find_model_dir(dataset: str, scene: str, variant: str, group: str) -> Path:
    root = MAIN_MODEL_ROOT if group == "main" or variant in {"base", "rc"} else ABLATION_MODEL_ROOT
    seed = root / dataset / scene / variant / "seed_0"
    return _nested_model_dir(seed, scene, variant)


def _scene_gt_info() -> dict[tuple[str, str], dict[str, Any]]:
    if not GEOM_SIGNAL_INV.exists():
        return {}
    inv = pd.read_csv(GEOM_SIGNAL_INV)
    info = {}
    for row in inv.to_dict("records"):
        info[(row["dataset"], row["scene"])] = row
    return info


def _metric_from_long(long_df: pd.DataFrame, dataset: str, split: str, scene: str, method_col: str, method: str, metric: str) -> float | None:
    rows = long_df[
        (long_df["dataset"] == dataset)
        & (long_df["split"] == split)
        & (long_df["scene"] == scene)
        & (long_df[method_col] == method)
        & (long_df["metric"] == metric)
    ]
    if rows.empty:
        return None
    value = rows.iloc[0].get("value")
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def evaluate_run(dataset: str, scene: str, variant: str, group: str, gt_info: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    model_dir = find_model_dir(dataset, scene, variant, group)
    point_file = model_dir / "point_cloud" / f"iteration_{ITERATION}" / "point_cloud.ply"
    input_file = model_dir / "input.ply"
    point_proxy = load_ply_proxy(point_file)
    input_proxy = load_ply_proxy(input_file)
    scene_info = gt_info.get((dataset, scene), {})

    gt_mesh_available = bool(scene_info.get("gt_mesh_available", False))
    gt_pc_available = bool(scene_info.get("gt_point_cloud_available", False))
    gt_depth_available = bool(scene_info.get("gt_depth_available", False))
    gt_normal_available = bool(scene_info.get("gt_normal_available", False))
    rendered_depth_available = bool(scene_info.get("rendered_depth_available", False))
    rendered_normal_available = bool(scene_info.get("rendered_normal_available", False))

    if gt_mesh_available or gt_pc_available:
        gt_type = "gt_mesh_or_point_cloud_available_uncomputed"
    elif gt_depth_available or gt_normal_available:
        gt_type = "image_space_gt_partial"
    else:
        gt_type = "none"

    true_mesh = gt_mesh_available or gt_pc_available
    true_depth = gt_depth_available and rendered_depth_available
    true_normal = gt_normal_available and rendered_normal_available

    unavailable = []
    if not point_proxy["exists"]:
        unavailable.append("missing_final_point_cloud")
    if not true_mesh:
        unavailable.append("missing_gt_mesh_or_point_cloud")
    if not true_depth:
        unavailable.append("missing_gt_depth_or_rendered_depth_buffers")
    if not true_normal:
        unavailable.append("missing_gt_normal_or_rendered_normal_buffers")
    unavailable.append("predicted_mesh_not_extracted")

    vertex_delta = None
    if point_proxy.get("vertex_count") is not None and input_proxy.get("vertex_count") is not None:
        vertex_delta = int(point_proxy["vertex_count"]) - int(input_proxy["vertex_count"])

    return {
        "dataset": dataset,
        "scene": scene,
        "variant": variant,
        "method": variant,
        "model_path": str(model_dir),
        "point_cloud_file": str(point_file) if point_file.exists() else "",
        "input_point_cloud_file": str(input_file) if input_file.exists() else "",
        "mesh_file": "",
        "gt_file": str(scene_info.get("gt_mesh_path") or scene_info.get("gt_point_cloud_path") or ""),
        "geometry_gt_type": gt_type,
        "evaluation_level": "level3_proxy",
        "aligned_flag": False,
        "valid_flag": bool(point_proxy["exists"]),
        "geometry_proxy_vertex_count": point_proxy.get("vertex_count"),
        "geometry_proxy_bbox_diag": point_proxy.get("bbox_diag"),
        "geometry_proxy_vertex_count_delta_from_input": vertex_delta,
        "unavailable_reasons": ";".join(unavailable),
        "note": "Proxy-only point-cloud artifact diagnostics; not a mesh/surface quality metric.",
    }


def build_expected_runs() -> tuple[pd.DataFrame, pd.DataFrame]:
    main_wide = _read_csv(MAIN_FULL)
    ablation_wide = _read_csv(ABLATION_FULL)
    main_rows = main_wide[["dataset", "scene"]].drop_duplicates().copy()
    main_rows["group"] = "main"
    main_rows["variant"] = None
    main_rows = main_rows.loc[main_rows.index.repeat(2)].reset_index(drop=True)
    main_rows["variant"] = ["base", "rc"] * (len(main_rows) // 2)
    abl_rows = ablation_wide[["dataset", "scene", "variant"]].drop_duplicates().copy()
    abl_rows["group"] = "ablation"
    return main_rows, abl_rows


def _long_from_runs(runs: list[dict[str, Any]], split_label: str = "all") -> pd.DataFrame:
    rows = []
    for run in runs:
        for metric in PROXY_METRICS:
            rows.append(
                {
                    "dataset": run["dataset"],
                    "split": split_label,
                    "scene": run["scene"],
                    "method": run["variant"],
                    "variant": run["variant"],
                    "metric": metric,
                    "value": run.get(metric),
                    "metric_direction": METRIC_DIRECTION[metric],
                    "geometry_gt_type": run["geometry_gt_type"],
                    "evaluation_level": run["evaluation_level"],
                    "mesh_file": run["mesh_file"],
                    "gt_file": run["gt_file"],
                    "aligned_flag": run["aligned_flag"],
                    "valid_flag": run["valid_flag"] and run.get(metric) is not None,
                    "source_file": run["point_cloud_file"],
                    "note": run["note"],
                }
            )
    return pd.DataFrame(rows)


def _wide_from_runs(runs: list[dict[str, Any]], group: str, split_label: str = "all") -> pd.DataFrame:
    if group == "main":
        rows = {}
        for run in runs:
            key = (run["dataset"], split_label, run["scene"])
            item = rows.setdefault(
                key,
                {
                    "dataset": run["dataset"],
                    "split": split_label,
                    "scene": run["scene"],
                    "notes": "Model-level proxy metrics; no train/test-specific geometry.",
                },
            )
            prefix = run["variant"]
            for metric in PROXY_METRICS:
                item[f"{prefix}_{metric}"] = run.get(metric)
        return pd.DataFrame(rows.values()).sort_values(["dataset", "split", "scene"])
    rows = []
    for run in runs:
        rows.append(
            {
                "dataset": run["dataset"],
                "split": split_label,
                "scene": run["scene"],
                "variant": run["variant"],
                **{metric: run.get(metric) for metric in PROXY_METRICS},
                "notes": "Model-level proxy metrics; no train/test-specific geometry.",
            }
        )
    return pd.DataFrame(rows).sort_values(["dataset", "split", "scene", "variant"])


def _avg_from_long(long_df: pd.DataFrame, method_col: str) -> pd.DataFrame:
    valid = long_df[long_df["valid_flag"]].copy()
    rows = []
    for (dataset, split, method, metric, level), g in valid.groupby(["dataset", "split", method_col, "metric", "evaluation_level"], dropna=False):
        rows.append(
            {
                "dataset": dataset,
                "split": split,
                method_col: method,
                "metric": metric,
                "mean_value": float(g["value"].mean()),
                "median_value": float(g["value"].median()),
                "std_value": float(g["value"].std(ddof=0)) if len(g) > 1 else 0.0,
                "valid_n": int(g["value"].notna().sum()),
                "total_scene_count": int(long_df[(long_df["dataset"] == dataset) & (long_df["split"] == split)][["scene"]].drop_duplicates().shape[0]),
                "metric_direction": METRIC_DIRECTION.get(metric, "unknown"),
                "evaluation_level": level,
                "note": "Proxy average only; not a geometry-quality mean.",
            }
        )
    return pd.DataFrame(rows)


def _fmt(value: Any, metric: str) -> str:
    if value is None or pd.isna(value):
        return "--"
    if "vertex_count" in metric:
        return f"{float(value):.0f}"
    return f"{float(value):.3f}"


def _latex_escape(s: Any) -> str:
    return str(s).replace("_", "\\_")


def write_latex_tables(main_wide: pd.DataFrame, main_avg: pd.DataFrame, abl_wide: pd.DataFrame, abl_avg: pd.DataFrame) -> None:
    def table_main(compact: bool) -> str:
        metrics = ["geometry_proxy_vertex_count"] if compact else ["geometry_proxy_vertex_count", "geometry_proxy_bbox_diag", "geometry_proxy_vertex_count_delta_from_input"]
        heads = "".join(f" & \\multicolumn{{2}}{{c}}{{{_latex_escape(m.replace('geometry_proxy_', 'proxy_'))}}}" for m in metrics)
        cmids = "".join(f"\\cmidrule(lr){{{4+i*2}-{5+i*2}}}" for i in range(len(metrics)))
        cols = "lll" + "cc" * len(metrics)
        lines = [
            "\\begin{table*}[t]",
            "\\centering",
            "\\caption{Main experiment geometry proxy diagnostics by dataset. No GT mesh or extracted predicted mesh is available; these values are point-cloud artifact proxies, not mesh-quality metrics.}",
            "\\label{tab:main_geometry_metrics_by_dataset" + ("_compact" if compact else "") + "}",
            "\\resizebox{\\textwidth}{!}{%",
            f"\\begin{{tabular}}{{{cols}}}",
            "\\toprule",
            f"Dataset & Split & Scene{heads} \\\\",
            f"& & {''.join([' & Base & RC' for _ in metrics])} \\\\",
            cmids,
            "\\midrule",
        ]
        for (dataset, split), g in main_wide.groupby(["dataset", "split"], sort=True):
            first = True
            for _, row in g.iterrows():
                prefix = f"{_latex_escape(dataset)} & {_latex_escape(split)}" if first else " & "
                vals = []
                for m in metrics:
                    vals += [_fmt(row.get(f"base_{m}"), m), _fmt(row.get(f"rc_{m}"), m)]
                lines.append(f"{prefix} & {_latex_escape(row['scene'])} & " + " & ".join(vals) + " \\\\")
                first = False
            avg_vals = []
            for m in metrics:
                for method in ["base", "rc"]:
                    v = main_avg[
                        (main_avg["dataset"] == dataset)
                        & (main_avg["split"] == split)
                        & (main_avg["method"] == method)
                        & (main_avg["metric"] == m)
                    ]["mean_value"]
                    avg_vals.append(_fmt(v.iloc[0] if not v.empty else None, m))
            lines.append(f" & & Avg. & " + " & ".join(avg_vals) + " \\\\")
            lines.append("\\midrule")
        lines[-1] = "\\bottomrule"
        lines += ["\\end{tabular}}", "\\end{table*}", ""]
        return "\n".join(lines)

    def table_ablation(compact: bool) -> str:
        metrics = ["geometry_proxy_vertex_count"] if compact else ["geometry_proxy_vertex_count", "geometry_proxy_bbox_diag", "geometry_proxy_vertex_count_delta_from_input"]
        cols = "llll" + "c" * len(metrics)
        header = "Dataset & Split & Scene & Variant & " + " & ".join(_latex_escape(m.replace("geometry_proxy_", "proxy_")) for m in metrics) + " \\\\"
        lines = [
            "\\begin{table*}[t]",
            "\\centering",
            "\\caption{Ablation geometry proxy diagnostics by dataset. Values are computed from final point-cloud artifacts only and must not be interpreted as Chamfer/F-score or mesh quality.}",
            "\\label{tab:ablation_geometry_metrics_by_dataset" + ("_compact" if compact else "") + "}",
            "\\resizebox{\\textwidth}{!}{%",
            f"\\begin{{tabular}}{{{cols}}}",
            "\\toprule",
            header,
            "\\midrule",
        ]
        for (dataset, split), g in abl_wide.groupby(["dataset", "split"], sort=True):
            first_ds = True
            for scene, sg in g.groupby("scene", sort=True):
                first_scene = True
                for _, row in sg.iterrows():
                    d = _latex_escape(dataset) if first_ds else ""
                    sp = _latex_escape(split) if first_ds else ""
                    sc = _latex_escape(scene) if first_scene else ""
                    vals = [_fmt(row.get(m), m) for m in metrics]
                    lines.append(f"{d} & {sp} & {sc} & {_latex_escape(row['variant'])} & " + " & ".join(vals) + " \\\\")
                    first_ds = False
                    first_scene = False
            for variant in VARIANTS:
                av = abl_avg[(abl_avg["dataset"] == dataset) & (abl_avg["split"] == split) & (abl_avg["variant"] == variant)]
                if av.empty:
                    continue
                vals = []
                for m in metrics:
                    v = av[av["metric"] == m]["mean_value"]
                    vals.append(_fmt(v.iloc[0] if not v.empty else None, m))
                lines.append(f" & & Avg. & {_latex_escape(variant)} & " + " & ".join(vals) + " \\\\")
            lines.append("\\midrule")
        lines[-1] = "\\bottomrule"
        lines += ["\\end{tabular}}", "\\end{table*}", ""]
        return "\n".join(lines)

    (TABLE_DIR / "table_main_geometry_metrics_by_dataset.tex").write_text(table_main(False), encoding="utf-8")
    (TABLE_DIR / "table_main_geometry_metrics_by_dataset_compact.tex").write_text(table_main(True), encoding="utf-8")
    (TABLE_DIR / "table_ablation_geometry_metrics_by_dataset.tex").write_text(table_ablation(False), encoding="utf-8")
    (TABLE_DIR / "table_ablation_geometry_metrics_by_dataset_compact.tex").write_text(table_ablation(True), encoding="utf-8")


def build_tradeoff(main_wide: pd.DataFrame, main_long_existing: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in main_wide.iterrows():
        dataset, scene, split = row["dataset"], row["scene"], row["split"]
        base_rc = _metric_from_long(main_long_existing, dataset, "test", scene, "method", "base", "mean_reflection_consistency")
        rc_rc = _metric_from_long(main_long_existing, dataset, "test", scene, "method", "rc", "mean_reflection_consistency")
        consistency_improvement = None
        if base_rc is not None and rc_rc is not None:
            consistency_improvement = base_rc - rc_rc
        base_v = row.get("base_geometry_proxy_vertex_count")
        rc_v = row.get("rc_geometry_proxy_vertex_count")
        base_bbox = row.get("base_geometry_proxy_bbox_diag")
        rc_bbox = row.get("rc_geometry_proxy_bbox_diag")
        rows.append(
            {
                "dataset": dataset,
                "split": split,
                "scene": scene,
                "consistency_improvement_test": consistency_improvement,
                "proxy_vertex_count_delta_rc_minus_base": None if pd.isna(base_v) or pd.isna(rc_v) else float(rc_v) - float(base_v),
                "proxy_bbox_diag_delta_rc_minus_base": None if pd.isna(base_bbox) or pd.isna(rc_bbox) else float(rc_bbox) - float(base_bbox),
                "geometry_metric_type": "level3_proxy",
                "claim_boundary": "Proxy deltas are artifact diagnostics, not mesh quality improvements.",
            }
        )
    return pd.DataFrame(rows)


def _setup_matplotlib() -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(GEOM_ROOT / ".mplconfig"))
    plt.rcParams.update(
        {
            "font.size": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
        }
    )


def savefig(fig, stem: str) -> None:
    fig.savefig(FIG_DIR / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_figures(main_wide: pd.DataFrame, tradeoff: pd.DataFrame, abl_wide: pd.DataFrame) -> None:
    _setup_matplotlib()
    label = main_wide["dataset"].str.replace("_synthetic", "", regex=False) + "/" + main_wide["scene"]
    delta = main_wide["rc_geometry_proxy_vertex_count"] - main_wide["base_geometry_proxy_vertex_count"]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    colors = ["#2563EB" if v >= 0 else "#D97706" for v in delta]
    ax.bar(np.arange(len(delta)), delta, color=colors)
    ax.axhline(0, color="#111827", linewidth=0.8)
    ax.set_xticks(np.arange(len(delta)))
    ax.set_xticklabels(label, rotation=60, ha="right", fontsize=6)
    ax.set_ylabel("RC - Base vertex count (proxy)")
    ax.set_title("Fig. G1. Geometry proxy changes by scene (not mesh quality)")
    ax.text(0.01, 0.98, "No GT mesh / no extracted mesh; proxy only.", transform=ax.transAxes, va="top", color="#DC2626")
    savefig(fig, "figG1_geometry_improvements_by_scene")

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))
    axes[0].scatter(tradeoff["consistency_improvement_test"], tradeoff["proxy_vertex_count_delta_rc_minus_base"], c="#2563EB", s=28)
    axes[0].axhline(0, color="#94A3B8", linewidth=0.8)
    axes[0].axvline(0, color="#94A3B8", linewidth=0.8)
    axes[0].set_xlabel("Reflection consistency improvement (test)")
    axes[0].set_ylabel("Vertex count delta (RC-Base)")
    axes[1].scatter(tradeoff["consistency_improvement_test"], tradeoff["proxy_bbox_diag_delta_rc_minus_base"], c="#7C3AED", s=28)
    axes[1].axhline(0, color="#94A3B8", linewidth=0.8)
    axes[1].axvline(0, color="#94A3B8", linewidth=0.8)
    axes[1].set_xlabel("Reflection consistency improvement (test)")
    axes[1].set_ylabel("BBox diag delta (RC-Base)")
    fig.suptitle("Fig. G2. Consistency vs geometry proxy trade-off")
    fig.text(0.5, -0.03, "Proxy diagnostics only; no Chamfer/F-score claim.", ha="center", color="#DC2626")
    savefig(fig, "figG2_consistency_vs_geometry_tradeoff")

    pivot = abl_wide.pivot_table(index="variant", values=["geometry_proxy_vertex_count", "geometry_proxy_bbox_diag"], aggfunc="mean").reindex([v for v in VARIANTS if v in abl_wide["variant"].unique()])
    norm = pivot.copy()
    for col in norm.columns:
        mn, mx = norm[col].min(), norm[col].max()
        norm[col] = 0.5 if mx == mn else (norm[col] - mn) / (mx - mn)
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    im = ax.imshow(norm.values, cmap="viridis", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(norm.columns)))
    ax.set_xticklabels([c.replace("geometry_proxy_", "proxy_") for c in norm.columns], rotation=25, ha="right")
    ax.set_yticks(np.arange(len(norm.index)))
    ax.set_yticklabels(norm.index)
    ax.set_title("Fig. G3. Ablation geometry proxy heatmap")
    for i in range(norm.shape[0]):
        for j in range(norm.shape[1]):
            ax.text(j, i, f"{norm.values[i, j]:.2f}", ha="center", va="center", color="white", fontsize=7)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="normalized proxy value")
    fig.text(0.5, -0.02, "Normalized diagnostic values; not better/worse quality.", ha="center", color="#DC2626")
    savefig(fig, "figG3_ablation_geometry_heatmap")

    fig, ax = plt.subplots(figsize=(6.2, 2.8))
    ax.axis("off")
    ax.text(0.5, 0.66, "Fig. G4 mesh qualitative montage is not available", ha="center", va="center", fontsize=14, weight="bold")
    ax.text(
        0.5,
        0.43,
        "No extracted predicted meshes and no accepted GT mesh/point cloud were found.\n"
        "The current package therefore does not include mesh renders or error heatmaps.",
        ha="center",
        va="center",
        fontsize=10,
        color="#374151",
    )
    ax.text(0.5, 0.18, "This placeholder records missing evidence; it is not a qualitative result.", ha="center", color="#DC2626")
    savefig(fig, "figG4_mesh_qualitative_montage")


def write_missing_fields(runs_main: list[dict[str, Any]], runs_abl: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    all_runs = runs_main + runs_abl
    for metric in TRUE_GEOM_METRICS:
        if metric.startswith("chamfer") or metric.startswith("fscore") or metric.startswith("precision") or metric.startswith("recall"):
            reason = "missing accepted GT mesh/point cloud and missing extracted predicted meshes"
            level = "level1_gt_mesh"
        elif metric.startswith("normal"):
            reason = "missing saved rendered normal buffers; Glossy has no GT normal; Shiny normal coordinate-space not verified"
            level = "level2_gt_normal"
        else:
            reason = "missing GT depth and saved rendered depth buffers"
            level = "level2_gt_depth"
        rows.append(
            {
                "metric": metric,
                "evaluation_level": level,
                "available": False,
                "affected_run_count": len(all_runs),
                "reason": reason,
                "safe_action": "Do not report this metric until required inputs exist.",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "geometry_missing_fields.csv", index=False)
    return df


def write_audit(main_runs: list[dict[str, Any]], abl_runs: list[dict[str, Any]], missing: pd.DataFrame) -> None:
    main_ok = sum(r["valid_flag"] for r in main_runs)
    abl_ok = sum(r["valid_flag"] for r in abl_runs)
    lines = [
        "# Geometry Evaluation Audit",
        "",
        "## Summary",
        "",
        f"- Main completed model rows inspected: {len(main_runs)}; final point clouds found: {main_ok}.",
        f"- Ablation completed model rows inspected: {len(abl_runs)}; final point clouds found: {abl_ok}.",
        "- True Chamfer/F-score/depth/normal metrics are not computable from current artifacts.",
        "- Generated metrics are Level 3 proxy diagnostics from existing final point-cloud PLY files only.",
        "",
        "## Answers",
        "",
        "1. Main checkpoints: no `chkpnt*.pth` files were found for the completed FD-P2-lite rows; final Gaussian point clouds are available.",
        "2. Ablation checkpoints: no `chkpnt*.pth` files were found for the completed non-Shiny-Real ablation rows; final Gaussian point clouds are available.",
        "3. Existing mesh files: none were found for completed rows.",
        "4. Runs requiring mesh extraction: all completed rows would require mesh extraction before mesh metrics or montage.",
        "5. GT mesh / GT point cloud: none accepted for the 14 non-Shiny-Real scenes.",
        "6. GT normal / depth: Shiny Blender Synthetic exposes GT normal PNGs, but saved rendered normals are absent and coordinate space is not verified; GT depth is absent.",
        "7. No GT geometry: all Glossy Synthetic converted scenes have no GT mesh, GT point cloud, GT depth, or GT normals in the current inventory.",
        "8. Mesh extraction method: `extract_mesh.py` uses `GaussianExtractor` with TSDF fusion from rendered depth/alpha/normal buffers; it is evaluation/extraction, not training.",
        "9. Geometry evaluation scripts: guarded proxy evaluators exist under `metrics/geometry_quality_eval.py` and `metrics/smvp3d_geometry_eval.py`; this package adds paper-asset tables/figures.",
        "10. Proxy metrics: vertex count, bounding-box diagonal, and vertex-count delta from input can be computed; they are diagnostics, not mesh quality.",
        "11. Claim support: current outputs do not support a mesh quality improvement claim.",
        "",
        "## Missing True Metrics",
        "",
    ]
    for row in missing.to_dict("records"):
        lines.append(f"- `{row['metric']}` ({row['evaluation_level']}): {row['reason']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "Safe: current artifacts support only geometry proxy diagnostics from final point-cloud PLY files.",
            "",
            "Unsafe: RC improves Chamfer, F-score, depth error, normal error, or mesh quality.",
            "",
        ]
    )
    (GEOM_ROOT / "geometry_evaluation_audit.md").write_text("\n".join(lines), encoding="utf-8")


def _pearson(x, y):
    vals = [(a, b) for a, b in zip(x, y) if pd.notna(a) and pd.notna(b)]
    if len(vals) < 3:
        return None
    xs, ys = np.asarray([a for a, _b in vals], dtype=float), np.asarray([b for _a, b in vals], dtype=float)
    if xs.std() == 0 or ys.std() == 0:
        return None
    return float(np.corrcoef(xs, ys)[0, 1])


def write_analysis(main_wide: pd.DataFrame, tradeoff: pd.DataFrame, abl_wide: pd.DataFrame) -> None:
    corr_vertex = _pearson(tradeoff["consistency_improvement_test"], tradeoff["proxy_vertex_count_delta_rc_minus_base"])
    corr_bbox = _pearson(tradeoff["consistency_improvement_test"], tradeoff["proxy_bbox_diag_delta_rc_minus_base"])
    lines = [
        "# Geometry Evaluation Results",
        "",
        "## 1. Evaluation Scope",
        "",
        "本次补测只使用已有 completed runs，不启动训练，不重新跑大规模实验。主实验覆盖 FD-P2-lite / non-Shiny-Real 的 Base 与 RC 共 28 个模型；消融覆盖 base/rc/wo_ref/wo_conf/rough_only 在同一 14 个 scene 上的 70 个模型层级条目，其中本次从消融根读取 wo_ref、wo_conf、rough_only 的 42 个完成模型，并复用主实验中的 base/rc proxy 作为对照。当前没有 accepted GT mesh 或 GT point cloud，也没有已抽取 predicted mesh，因此 Level 1 mesh metrics 不可计算。",
        "",
        "## 2. Main Experiment Geometry Results",
        "",
        "主实验可读取 final Gaussian point-cloud PLY，并计算 vertex count、bbox diagonal 和相对 input point cloud 的 vertex-count delta。这些是 artifact proxy diagnostics，不是 Chamfer/F-score、surface accuracy 或 mesh completeness。由于缺少 GT geometry 与 predicted mesh，不能判断 RC 是否改善真实 mesh quality。",
        "",
        "## 3. Ablation Geometry Results",
        "",
        "消融实验同样只能报告 point-cloud artifact proxies。wo_ref、wo_conf 和 rough_only 的 proxy 差异可用于发现模型规模或空间范围变化，但不能解释为几何质量优劣。不同 variant 的平均 proxy 值已写入 ablation_geometry_metrics_avg.csv 与 LaTeX 表。",
        "",
        "## 4. Consistency vs Geometry",
        "",
        f"以 test split 的 reflection consistency improvement 对齐主实验 proxy delta 后，vertex-count proxy 的 Pearson r 为 `{corr_vertex if corr_vertex is not None else 'NA'}`，bbox-diagonal proxy 的 Pearson r 为 `{corr_bbox if corr_bbox is not None else 'NA'}`。由于 y 轴是 proxy 而非真实 mesh error，该相关性只能说明 artifact-level 变化与 consistency 的关系，不能说明 surface quality 是否改善。",
        "",
        "## 5. Mesh Quality Diagnosis",
        "",
        "当前证据不支持“RC 改善 mesh quality”。更准确的结论是：RC 的 reflection consistency 改善尚未通过当前 artifact package 转化为可验证的 surface / mesh quality improvement。若论文目标包含几何质量，必须补充 mesh extraction、GT geometry 或 accepted evaluation point cloud，并计算 Chamfer/F-score/normal/depth 等真实指标。",
        "",
        "## 6. Limitations",
        "",
        "- 没有 accepted GT mesh / GT point cloud。",
        "- 没有已抽取 predicted mesh。",
        "- 没有 saved rendered depth / normal buffers。",
        "- Shiny Blender Synthetic 虽有 GT normal PNG，但当前缺少 rendered normal，且 normal coordinate space 未验证。",
        "- Proxy metrics 不能替代 mesh quality metrics。",
        "",
        "## 7. Claim Boundary",
        "",
        "Safe statement: 当前实验表明，RC 的 reflection consistency 改善尚未稳定转化为可验证的 mesh quality 提升；现有几何补测只支持 point-cloud proxy diagnostics，RC 更适合作为内部一致性正则或诊断信号，并需要进一步 geometry-aware / mesh-aware 评估。",
        "",
        "Unsafe statement: RC 必然提升 mesh quality、Chamfer、F-score、normal error 或 depth error。",
        "",
    ]
    (GEOM_ROOT / "geometry_results_analysis_zh.md").write_text("\n".join(lines), encoding="utf-8")


def append_geometry_sections() -> None:
    updates = {
        REPO_ROOT / "paper_assets/experiment_claim_boundary.md": """

<!-- GEOMETRY_EVALUATION:START -->
## Geometry / Mesh Quality Claim Boundary

当前 geometry 补测只从已有 completed runs 的 final point-cloud PLY 中得到 Level 3 proxy diagnostics（vertex count、bbox diagonal、input-to-final vertex-count delta）。当前没有 accepted GT mesh / GT point cloud、没有已抽取 predicted mesh，也没有 saved rendered depth/normal buffers，因此 Chamfer、F-score、depth error、normal error 均不可计算。

Safe wording: 当前结果不支持 RC 改善 mesh quality 的结论；RC 的 reflection consistency 改善仍需通过 geometry-aware / mesh-aware 评估验证。

Unsafe wording: RC 必然改善 Chamfer、F-score、normal/depth error 或 mesh quality。
<!-- GEOMETRY_EVALUATION:END -->
""",
        REPO_ROOT / "paper_assets/rc_results_summary_zh.md": """

<!-- GEOMETRY_EVALUATION:START -->
## 7. Geometry / Mesh Quality 补测

补测结果显示，当前 completed runs 只有 final point-cloud artifact 可用于 Level 3 proxy diagnostics；没有 accepted GT mesh / GT point cloud、没有 predicted mesh，也没有 saved rendered depth/normal buffers。因此，本结果包不能支持 mesh quality improvement claim。当前更安全的表述是：RC 的 consistency 改善尚未稳定转化为可验证的 surface / mesh quality 提升，后续需要 geometry-aware RC 或 mesh-aware RC filtering，并补充 Chamfer/F-score/normal/depth 指标。
<!-- GEOMETRY_EVALUATION:END -->
""",
        REPO_ROOT / "paper_assets/diagnostics/refl_metrics_degradation_analysis_zh.md": """

<!-- GEOMETRY_EVALUATION:START -->
## 9. Geometry / Mesh Quality Follow-up

几何补测进一步强化了当前 claim boundary：现有 evidence package 不能证明 reflection consistency improvement 会转化为 mesh quality improvement。由于缺少 GT mesh、predicted mesh、rendered depth/normal buffers，补测只能报告 point-cloud proxy diagnostics。该结果支持将 RC 暂时定位为 reflection consistency regularizer / diagnostic signal，并将下一阶段研究转向 geometry-aware RC 与 mesh-aware RC filtering，而不是直接声称其提升最终 surface quality。
<!-- GEOMETRY_EVALUATION:END -->
""",
    }
    for path, block in updates.items():
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        text = re.sub(r"\n?<!-- GEOMETRY_EVALUATION:START -->.*?<!-- GEOMETRY_EVALUATION:END -->\n?", "\n", text, flags=re.S)
        path.write_text(text.rstrip() + "\n" + block.lstrip(), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build RC-RefGS geometry/proxy paper assets.")
    parser.add_argument("--skip_doc_updates", action="store_true")
    args = parser.parse_args()

    _ensure_dirs()
    main_expected, ablation_expected = build_expected_runs()
    gt_info = _scene_gt_info()
    main_runs = [evaluate_run(row.dataset, row.scene, row.variant, "main", gt_info) for row in main_expected.itertuples(index=False)]
    ablation_runs = [evaluate_run(row.dataset, row.scene, row.variant, "ablation", gt_info) for row in ablation_expected.itertuples(index=False)]

    main_long = _long_from_runs(main_runs)
    abl_long = _long_from_runs(ablation_runs)
    main_wide = _wide_from_runs(main_runs, "main")
    abl_wide = _wide_from_runs(ablation_runs, "ablation")
    main_avg = _avg_from_long(main_long.rename(columns={"variant": "_variant"}), "method")
    abl_avg = _avg_from_long(abl_long, "variant")

    main_long.drop(columns=["variant"]).to_csv(DATA_DIR / "main_geometry_metrics_long.csv", index=False)
    main_wide.to_csv(DATA_DIR / "main_geometry_metrics_wide.csv", index=False)
    main_avg.to_csv(DATA_DIR / "main_geometry_metrics_avg.csv", index=False)
    abl_long.to_csv(DATA_DIR / "ablation_geometry_metrics_long.csv", index=False)
    abl_wide.to_csv(DATA_DIR / "ablation_geometry_metrics_wide.csv", index=False)
    abl_avg.to_csv(DATA_DIR / "ablation_geometry_metrics_avg.csv", index=False)

    existing_main_long = _read_csv(MAIN_LONG)
    tradeoff = build_tradeoff(main_wide, existing_main_long)
    tradeoff.to_csv(DATA_DIR / "geometry_consistency_tradeoff.csv", index=False)
    missing = write_missing_fields(main_runs, ablation_runs)
    write_latex_tables(main_wide, main_avg, abl_wide, abl_avg)
    write_figures(main_wide, tradeoff, abl_wide)
    write_audit(main_runs, ablation_runs, missing)
    write_analysis(main_wide, tradeoff, abl_wide)
    if not args.skip_doc_updates:
        append_geometry_sections()

    summary = {
        "main_runs": len(main_runs),
        "main_point_clouds_found": int(sum(r["valid_flag"] for r in main_runs)),
        "ablation_runs": len(ablation_runs),
        "ablation_point_clouds_found": int(sum(r["valid_flag"] for r in ablation_runs)),
        "true_geometry_metrics_computed": False,
        "proxy_metrics_computed": PROXY_METRICS,
        "claim_boundary": "No mesh quality improvement claim is supported.",
    }
    (GEOM_ROOT / "geometry_eval_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
