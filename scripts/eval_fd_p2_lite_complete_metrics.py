#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SHINY_SYNTHETIC_SCENES = ["ball", "car", "coffee", "helmet", "teapot", "toaster"]
GLOSSY_SYNTHETIC_SCENES = ["angel", "bell", "cat", "horse", "luyu", "potion", "tbell", "teapot"]
MAIN_VARIANTS = ["base", "rc"]
ABLATION_VARIANTS = ["wo_ref", "wo_conf", "rough_only"]
REQUIRED_ARTIFACTS = [
    "point_cloud/iteration_31000/point_cloud.ply",
    "reflection_consistency_train.json",
    "reflection_consistency_test.json",
    "launcher_summary.json",
]
REQUIRED_RENDER_FIELDS = [
    "full_psnr",
    "full_ssim",
    "full_lpips",
    "reflective_psnr",
    "reflective_ssim",
    "reflective_lpips",
    "num_images",
]


def _fmt(v):
    if v is None:
        return "NA"
    if isinstance(v, (int, float)):
        return f"{v:.6f}"
    return str(v)


def _iter_cells(root: Path, datasets, variants, exp_type: str):
    for dataset, scenes in datasets.items():
        for scene in scenes:
            for variant in variants:
                yield {
                    "exp_type": exp_type,
                    "dataset": dataset,
                    "scene": scene,
                    "variant": variant,
                    "seed_dir": root / dataset / scene / variant / "seed_0",
                }


def _resolve_model_dir(seed_dir: Path):
    if not seed_dir.exists():
        return None
    if (seed_dir / "launcher_summary.json").exists():
        return seed_dir
    child_dirs = [p for p in seed_dir.iterdir() if p.is_dir()]
    with_summary = [d for d in child_dirs if (d / "launcher_summary.json").exists()]
    if with_summary:
        return sorted(with_summary)[0]
    if len(child_dirs) == 1:
        return child_dirs[0]
    return None


def _missing_artifacts(model_dir: Path):
    return [rel for rel in REQUIRED_ARTIFACTS if not (model_dir / rel).exists()]


def _load_reflection(model_dir: Path, split: str):
    path = model_dir / f"reflection_consistency_{split}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for key in ("mean_reflection_consistency", "reflective_region_psnr", "num_pairs", "valid_pair_count"):
        value = payload.get(key)
        if not isinstance(value, (int, float)):
            raise ValueError(f"{path}: missing/non-numeric {key}")
        out[key] = float(value)
    return out


def _parse_source_path(model_dir: Path):
    cfg_path = model_dir / "cfg_args"
    text = cfg_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"source_path='([^']+)'", text)
    if not match:
        raise ValueError(f"Unable to parse source_path from {cfg_path}")
    return match.group(1)


def _validate_render_json(path: Path):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False, "invalid_json", None
    if not isinstance(payload, dict):
        return False, "root_not_object", None
    splits = payload.get("splits")
    if not isinstance(splits, dict) or "train" not in splits or "test" not in splits:
        return False, "missing_train_or_test_split", payload
    for split in ("train", "test"):
        split_payload = splits.get(split)
        if not isinstance(split_payload, dict):
            return False, f"{split}_not_object", payload
        for field in REQUIRED_RENDER_FIELDS:
            if field not in split_payload:
                return False, f"{split}_missing_{field}", payload
    return True, "ok", payload


def _run_render_eval(repo_root: Path, model_dir: Path, source_path: str, cuda_device: str, output_json: Path):
    env = os.environ.copy()
    env.pop("CUDA_VISIBLE_DEVICES", None)
    conda_prefix = env.get("CONDA_PREFIX")
    if conda_prefix:
        prior_ld = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = f"{conda_prefix}/lib:{prior_ld}" if prior_ld else f"{conda_prefix}/lib"

    attempts = []

    def run_once(image_key: str, skip_lpips: bool):
        cmd = [
            sys.executable,
            "metrics/render_quality_eval.py",
            "--cuda_device",
            str(cuda_device),
            "-s",
            source_path,
            "-m",
            str(model_dir),
            "--iteration",
            "31000",
            "--split",
            "both",
            "--mask_mode",
            "both",
            "--image_key",
            image_key,
            "--output_json",
            str(output_json),
            "--quiet",
        ]
        if skip_lpips:
            cmd.append("--skip_lpips")
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True)
        attempts.append(
            {
                "image_key": image_key,
                "lpips_skipped": bool(skip_lpips),
                "returncode": int(proc.returncode),
                "stdout_tail": proc.stdout[-1000:],
                "stderr_tail": proc.stderr[-1000:],
            }
        )
        return proc

    run_order = [("pbr_rgb", False), ("pbr_rgb", True), ("render", False), ("render", True)]
    for image_key, skip_lpips in run_order:
        proc = run_once(image_key, skip_lpips)
        if proc.returncode == 0:
            ok, _, payload = _validate_render_json(output_json)
            if ok:
                return True, payload, {"image_key_used": image_key, "lpips_skipped": bool(skip_lpips), "attempts": attempts}
        if not skip_lpips:
            lower_err = ((proc.stdout or "") + "\n" + (proc.stderr or "")).lower()
            if "out of memory" in lower_err or "cuda oom" in lower_err or "lpips" in lower_err:
                continue
        if image_key == "pbr_rgb":
            continue
    return False, None, {"attempts": attempts}


def _split_metrics(row: dict, split: str):
    refl = row.get("reflection", {}).get(split, {})
    render = row.get("render_quality", {}).get("splits", {}).get(split, {})
    return {
        "mean_reflection_consistency": refl.get("mean_reflection_consistency"),
        "reflective_region_psnr": refl.get("reflective_region_psnr"),
        "valid_pair_count": refl.get("valid_pair_count"),
        "num_pairs": refl.get("num_pairs"),
        "full_psnr": render.get("full_psnr"),
        "full_ssim": render.get("full_ssim"),
        "full_lpips": render.get("full_lpips"),
        "reflective_psnr": render.get("reflective_psnr"),
        "reflective_ssim": render.get("reflective_ssim"),
        "reflective_lpips": render.get("reflective_lpips"),
        "num_images": render.get("num_images"),
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate complete metric set for FD-P2-lite non-Shiny-Real scope.")
    parser.add_argument("--main_root", default="/tmp/rc_refgs_full_dataset_base_rc_i31000_20260527")
    parser.add_argument("--ablation_root", default="/tmp/rc_refgs_full_dataset_ablations_i31000_20260528")
    parser.add_argument("--cuda_device", default="0")
    parser.add_argument("--repo_root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    main_root = Path(args.main_root)
    ablation_root = Path(args.ablation_root)

    out_json = repo_root / "docs/superpowers/logs/rc-refgs-fd-p2-lite-complete-metrics-2026-05-29.json"
    out_md = repo_root / "docs/superpowers/logs/rc-refgs-fd-p2-lite-complete-metrics-2026-05-29.md"
    out_main_csv = repo_root / "docs/superpowers/logs/rc-refgs-fd-p2-lite-complete-metrics-main-table-2026-05-29.csv"
    out_ablation_csv = repo_root / "docs/superpowers/logs/rc-refgs-fd-p2-lite-complete-metrics-ablation-table-2026-05-29.csv"

    main_cells = list(
        _iter_cells(
            main_root,
            {
                "shiny_blender_synthetic": SHINY_SYNTHETIC_SCENES,
                "glossy_synthetic": GLOSSY_SYNTHETIC_SCENES,
            },
            MAIN_VARIANTS,
            "main",
        )
    )
    ablation_cells = list(
        _iter_cells(
            ablation_root,
            {
                "shiny_blender_synthetic": SHINY_SYNTHETIC_SCENES,
                "glossy_synthetic": GLOSSY_SYNTHETIC_SCENES,
            },
            ABLATION_VARIANTS,
            "ablation",
        )
    )
    all_cells = main_cells + ablation_cells
    total_cells = len(all_cells)

    records = []
    failures = []

    for idx, cell in enumerate(all_cells, start=1):
        seed_dir = cell["seed_dir"]
        model_dir = _resolve_model_dir(seed_dir)
        label = f"[{idx:02d}/{total_cells:02d}] {cell['exp_type']} {cell['dataset']}/{cell['scene']}/{cell['variant']}"
        record = {
            **cell,
            "seed_dir": str(seed_dir),
            "model_dir": str(model_dir) if model_dir else None,
            "complete_artifacts": False,
            "missing_artifacts": [],
            "reflection": {},
            "render_quality_path": None,
            "render_quality_status": "not_checked",
            "image_key_used": None,
            "lpips_skipped": None,
        }

        if model_dir is None:
            print(f"{label} -> missing_model_dir", flush=True)
            record["render_quality_status"] = "missing_model_dir"
            failures.append({**cell, "reason": "missing_model_dir", "seed_dir": str(seed_dir)})
            records.append(record)
            continue

        missing = _missing_artifacts(model_dir)
        record["missing_artifacts"] = missing
        if missing:
            print(f"{label} -> incomplete_artifacts", flush=True)
            record["render_quality_status"] = "incomplete_artifacts"
            failures.append({**cell, "reason": "incomplete_artifacts", "missing_artifacts": missing, "model_dir": str(model_dir)})
            records.append(record)
            continue

        record["complete_artifacts"] = True
        try:
            record["reflection"]["train"] = _load_reflection(model_dir, "train")
            record["reflection"]["test"] = _load_reflection(model_dir, "test")
        except Exception as exc:
            print(f"{label} -> reflection_parse_failed", flush=True)
            record["render_quality_status"] = "reflection_parse_failed"
            failures.append({**cell, "reason": "reflection_parse_failed", "error": str(exc), "model_dir": str(model_dir)})
            records.append(record)
            continue

        render_json_path = model_dir / "render_quality_both_iter31000.json"
        record["render_quality_path"] = str(render_json_path)

        valid, _, payload = _validate_render_json(render_json_path) if render_json_path.exists() else (False, "missing", None)
        if valid:
            print(f"{label} -> existing_valid", flush=True)
            record["render_quality_status"] = "existing_valid"
            record["image_key_used"] = payload.get("image_key")
            record["lpips_skipped"] = bool(payload.get("lpips_skipped"))
            record["render_quality"] = payload
            records.append(record)
            continue

        print(f"{label} -> evaluating", flush=True)
        source_path = _parse_source_path(model_dir)
        ok, payload, meta = _run_render_eval(repo_root, model_dir, source_path, args.cuda_device, render_json_path)
        if not ok:
            print(f"{label} -> eval_failed", flush=True)
            record["render_quality_status"] = "eval_failed"
            record["eval_attempts"] = meta.get("attempts", [])
            failures.append(
                {
                    **cell,
                    "reason": "eval_failed",
                    "model_dir": str(model_dir),
                    "render_path": str(render_json_path),
                    "attempts": meta.get("attempts", []),
                }
            )
            records.append(record)
            continue

        print(f"{label} -> evaluated", flush=True)
        record["render_quality_status"] = "evaluated"
        record["image_key_used"] = meta.get("image_key_used")
        record["lpips_skipped"] = bool(meta.get("lpips_skipped"))
        record["eval_attempts"] = meta.get("attempts", [])
        record["render_quality"] = payload
        records.append(record)

    for record in records:
        render_path = record.get("render_quality_path")
        if render_path and Path(render_path).exists() and record.get("render_quality_status") in {"existing_valid", "evaluated"}:
            json.loads(Path(render_path).read_text(encoding="utf-8"))

    main_records = [r for r in records if r["exp_type"] == "main" and r.get("render_quality_status") in {"existing_valid", "evaluated"}]
    ablation_records = [r for r in records if r["exp_type"] == "ablation" and r.get("render_quality_status") in {"existing_valid", "evaluated"}]

    main_index = {(r["dataset"], r["scene"], r["variant"]): r for r in main_records}
    main_pairs = []
    rc_win_counts = {
        "train_total_pairs": 0,
        "test_total_pairs": 0,
        "train_rc_lower_consistency": 0,
        "test_rc_lower_consistency": 0,
        "both_splits_rc_lower": 0,
        "not_lower_cases": [],
    }

    for dataset, scenes in (("shiny_blender_synthetic", SHINY_SYNTHETIC_SCENES), ("glossy_synthetic", GLOSSY_SYNTHETIC_SCENES)):
        for scene in scenes:
            base_row = main_index.get((dataset, scene, "base"))
            rc_row = main_index.get((dataset, scene, "rc"))
            if not base_row or not rc_row:
                failures.append({"exp_type": "main", "dataset": dataset, "scene": scene, "reason": "missing_base_or_rc_for_pairwise"})
                continue
            pair = {"dataset": dataset, "scene": scene}
            both_lower = True
            for split in ("train", "test"):
                base_split = _split_metrics(base_row, split)
                rc_split = _split_metrics(rc_row, split)
                base_cons = base_split["mean_reflection_consistency"]
                rc_cons = rc_split["mean_reflection_consistency"]
                delta_cons = rc_cons - base_cons
                pair[f"base_{split}_consistency"] = base_cons
                pair[f"rc_{split}_consistency"] = rc_cons
                pair[f"{split}_consistency_delta"] = delta_cons
                rc_lower = delta_cons < 0
                pair[f"rc_lower_{split}"] = rc_lower
                rc_win_counts[f"{split}_total_pairs"] += 1
                if rc_lower:
                    rc_win_counts[f"{split}_rc_lower_consistency"] += 1
                else:
                    both_lower = False
                    rc_win_counts["not_lower_cases"].append(
                        {"dataset": dataset, "scene": scene, "split": split, "delta": delta_cons}
                    )
                for metric in (
                    "reflective_region_psnr",
                    "full_psnr",
                    "full_ssim",
                    "full_lpips",
                    "reflective_psnr",
                    "reflective_ssim",
                    "reflective_lpips",
                ):
                    pair[f"base_{split}_{metric}"] = base_split[metric]
                    pair[f"rc_{split}_{metric}"] = rc_split[metric]
                    if isinstance(base_split[metric], (int, float)) and isinstance(rc_split[metric], (int, float)):
                        pair[f"{split}_{metric}_delta"] = rc_split[metric] - base_split[metric]
                    else:
                        pair[f"{split}_{metric}_delta"] = None
            if both_lower:
                rc_win_counts["both_splits_rc_lower"] += 1
            main_pairs.append(pair)

    aggregate_main = {}
    for split in ("train", "test"):
        aggregate_main[split] = {}
        for metric in (
            "consistency",
            "reflective_region_psnr",
            "full_psnr",
            "full_ssim",
            "full_lpips",
            "reflective_psnr",
            "reflective_ssim",
            "reflective_lpips",
        ):
            deltas = [p.get(f"{split}_{metric}_delta") for p in main_pairs if isinstance(p.get(f"{split}_{metric}_delta"), (int, float))]
            aggregate_main[split][f"mean_delta_{metric}"] = (sum(deltas) / len(deltas)) if deltas else None
            aggregate_main[split][f"median_delta_{metric}"] = statistics.median(deltas) if deltas else None

    ablation_summary = []
    for dataset, scenes in (("shiny_blender_synthetic", SHINY_SYNTHETIC_SCENES), ("glossy_synthetic", GLOSSY_SYNTHETIC_SCENES)):
        for variant in ABLATION_VARIANTS:
            rows = [r for r in ablation_records if r["dataset"] == dataset and r["variant"] == variant]

            def avg(values):
                nums = [v for v in values if isinstance(v, (int, float))]
                return (sum(nums) / len(nums)) if nums else None

            ablation_summary.append(
                {
                    "dataset": dataset,
                    "variant": variant,
                    "complete_models": len(rows),
                    "expected_models": len(scenes),
                    "mean_train_consistency": avg([_split_metrics(r, "train")["mean_reflection_consistency"] for r in rows]),
                    "mean_test_consistency": avg([_split_metrics(r, "test")["mean_reflection_consistency"] for r in rows]),
                    "mean_train_reflective_psnr_reflection_json": avg([_split_metrics(r, "train")["reflective_region_psnr"] for r in rows]),
                    "mean_test_reflective_psnr_reflection_json": avg([_split_metrics(r, "test")["reflective_region_psnr"] for r in rows]),
                    "mean_train_full_psnr": avg([_split_metrics(r, "train")["full_psnr"] for r in rows]),
                    "mean_test_full_psnr": avg([_split_metrics(r, "test")["full_psnr"] for r in rows]),
                    "mean_train_full_ssim": avg([_split_metrics(r, "train")["full_ssim"] for r in rows]),
                    "mean_test_full_ssim": avg([_split_metrics(r, "test")["full_ssim"] for r in rows]),
                    "mean_train_full_lpips": avg([_split_metrics(r, "train")["full_lpips"] for r in rows]),
                    "mean_test_full_lpips": avg([_split_metrics(r, "test")["full_lpips"] for r in rows]),
                    "mean_train_reflective_psnr": avg([_split_metrics(r, "train")["reflective_psnr"] for r in rows]),
                    "mean_test_reflective_psnr": avg([_split_metrics(r, "test")["reflective_psnr"] for r in rows]),
                    "mean_train_reflective_ssim": avg([_split_metrics(r, "train")["reflective_ssim"] for r in rows]),
                    "mean_test_reflective_ssim": avg([_split_metrics(r, "test")["reflective_ssim"] for r in rows]),
                    "mean_train_reflective_lpips": avg([_split_metrics(r, "train")["reflective_lpips"] for r in rows]),
                    "mean_test_reflective_lpips": avg([_split_metrics(r, "test")["reflective_lpips"] for r in rows]),
                }
            )

    tradeoff_cases = []
    for pair in main_pairs:
        for split in ("train", "test"):
            if not pair.get(f"rc_lower_{split}", False):
                continue
            degradations = []
            for metric in ("reflective_region_psnr", "full_psnr", "full_ssim", "reflective_psnr", "reflective_ssim"):
                delta = pair.get(f"{split}_{metric}_delta")
                if isinstance(delta, (int, float)) and delta < 0:
                    degradations.append({"metric": metric, "delta": delta})
            for metric in ("full_lpips", "reflective_lpips"):
                delta = pair.get(f"{split}_{metric}_delta")
                if isinstance(delta, (int, float)) and delta > 0:
                    degradations.append({"metric": metric, "delta": delta})
            if degradations:
                tradeoff_cases.append(
                    {"dataset": pair["dataset"], "scene": pair["scene"], "split": split, "degrades": degradations}
                )

    output_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scope_name": "FD-P2-lite non-Shiny-Real complete metric set",
        "metric_set_version": "reflection_consistency + render_quality_eval(split=both, mask_mode=both, image_key=pbr_rgb|fallback_render, iteration=31000)",
        "main_expected_models": 28,
        "main_evaluated_models": len(main_records),
        "ablation_expected_models": 42,
        "ablation_evaluated_models": len(ablation_records),
        "missing_or_failed_metric_cells": failures,
        "per_model_metrics": records,
        "aggregate_main_base_vs_rc": {
            "pair_count": len(main_pairs),
            "pairs": main_pairs,
            "rc_win_counts": rc_win_counts,
            "delta_aggregates": aggregate_main,
            "tradeoff_cases": tradeoff_cases,
        },
        "aggregate_ablation_by_dataset_variant": ablation_summary,
        "limitations": [
            "Shiny Blender Real is excluded from FD-P2-lite due to OOM blocker.",
            "Single-seed evidence only (seed 0).",
            "If lpips_skipped=true in any cell, LPIPS interpretation is limited for those cells.",
            "No training/recovery was executed in this task.",
        ],
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")

    main_fields = [
        "dataset",
        "scene",
        "base_train_consistency",
        "rc_train_consistency",
        "train_consistency_delta",
        "rc_lower_train",
        "base_test_consistency",
        "rc_test_consistency",
        "test_consistency_delta",
        "rc_lower_test",
        "base_train_reflective_region_psnr",
        "rc_train_reflective_region_psnr",
        "train_reflective_region_psnr_delta",
        "base_test_reflective_region_psnr",
        "rc_test_reflective_region_psnr",
        "test_reflective_region_psnr_delta",
        "base_train_full_psnr",
        "rc_train_full_psnr",
        "train_full_psnr_delta",
        "base_test_full_psnr",
        "rc_test_full_psnr",
        "test_full_psnr_delta",
        "base_train_full_ssim",
        "rc_train_full_ssim",
        "train_full_ssim_delta",
        "base_test_full_ssim",
        "rc_test_full_ssim",
        "test_full_ssim_delta",
        "base_train_full_lpips",
        "rc_train_full_lpips",
        "train_full_lpips_delta",
        "base_test_full_lpips",
        "rc_test_full_lpips",
        "test_full_lpips_delta",
        "base_train_reflective_psnr",
        "rc_train_reflective_psnr",
        "train_reflective_psnr_delta",
        "base_test_reflective_psnr",
        "rc_test_reflective_psnr",
        "test_reflective_psnr_delta",
        "base_train_reflective_ssim",
        "rc_train_reflective_ssim",
        "train_reflective_ssim_delta",
        "base_test_reflective_ssim",
        "rc_test_reflective_ssim",
        "test_reflective_ssim_delta",
        "base_train_reflective_lpips",
        "rc_train_reflective_lpips",
        "train_reflective_lpips_delta",
        "base_test_reflective_lpips",
        "rc_test_reflective_lpips",
        "test_reflective_lpips_delta",
    ]
    with out_main_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=main_fields)
        writer.writeheader()
        for pair in main_pairs:
            row = {"dataset": pair["dataset"], "scene": pair["scene"]}
            for split in ("train", "test"):
                row[f"base_{split}_consistency"] = pair.get(f"base_{split}_consistency")
                row[f"rc_{split}_consistency"] = pair.get(f"rc_{split}_consistency")
                row[f"{split}_consistency_delta"] = pair.get(f"{split}_consistency_delta")
                row[f"rc_lower_{split}"] = pair.get(f"rc_lower_{split}")
                for metric in (
                    "reflective_region_psnr",
                    "full_psnr",
                    "full_ssim",
                    "full_lpips",
                    "reflective_psnr",
                    "reflective_ssim",
                    "reflective_lpips",
                ):
                    row[f"base_{split}_{metric}"] = pair.get(f"base_{split}_{metric}")
                    row[f"rc_{split}_{metric}"] = pair.get(f"rc_{split}_{metric}")
                    row[f"{split}_{metric}_delta"] = pair.get(f"{split}_{metric}_delta")
            writer.writerow(row)

    ablation_fields = [
        "row_type",
        "dataset",
        "scene",
        "variant",
        "complete_models",
        "expected_models",
        "train_consistency",
        "test_consistency",
        "train_reflective_region_psnr",
        "test_reflective_region_psnr",
        "train_full_psnr",
        "test_full_psnr",
        "train_full_ssim",
        "test_full_ssim",
        "train_full_lpips",
        "test_full_lpips",
        "train_reflective_psnr",
        "test_reflective_psnr",
        "train_reflective_ssim",
        "test_reflective_ssim",
        "train_reflective_lpips",
        "test_reflective_lpips",
        "valid_pair_count_train",
        "valid_pair_count_test",
        "num_pairs_train",
        "num_pairs_test",
        "lpips_skipped",
        "image_key_used",
        "render_quality_status",
        "model_dir",
    ]
    with out_ablation_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ablation_fields)
        writer.writeheader()
        for row in sorted(ablation_records, key=lambda r: (r["dataset"], r["scene"], r["variant"])):
            train = _split_metrics(row, "train")
            test = _split_metrics(row, "test")
            writer.writerow(
                {
                    "row_type": "model",
                    "dataset": row["dataset"],
                    "scene": row["scene"],
                    "variant": row["variant"],
                    "train_consistency": train["mean_reflection_consistency"],
                    "test_consistency": test["mean_reflection_consistency"],
                    "train_reflective_region_psnr": train["reflective_region_psnr"],
                    "test_reflective_region_psnr": test["reflective_region_psnr"],
                    "train_full_psnr": train["full_psnr"],
                    "test_full_psnr": test["full_psnr"],
                    "train_full_ssim": train["full_ssim"],
                    "test_full_ssim": test["full_ssim"],
                    "train_full_lpips": train["full_lpips"],
                    "test_full_lpips": test["full_lpips"],
                    "train_reflective_psnr": train["reflective_psnr"],
                    "test_reflective_psnr": test["reflective_psnr"],
                    "train_reflective_ssim": train["reflective_ssim"],
                    "test_reflective_ssim": test["reflective_ssim"],
                    "train_reflective_lpips": train["reflective_lpips"],
                    "test_reflective_lpips": test["reflective_lpips"],
                    "valid_pair_count_train": train["valid_pair_count"],
                    "valid_pair_count_test": test["valid_pair_count"],
                    "num_pairs_train": train["num_pairs"],
                    "num_pairs_test": test["num_pairs"],
                    "lpips_skipped": row.get("lpips_skipped"),
                    "image_key_used": row.get("image_key_used"),
                    "render_quality_status": row.get("render_quality_status"),
                    "model_dir": row.get("model_dir"),
                }
            )
        for summary in sorted(ablation_summary, key=lambda s: (s["dataset"], s["variant"])):
            writer.writerow(
                {
                    "row_type": "aggregate",
                    "dataset": summary["dataset"],
                    "variant": summary["variant"],
                    "complete_models": summary["complete_models"],
                    "expected_models": summary["expected_models"],
                    "train_consistency": summary["mean_train_consistency"],
                    "test_consistency": summary["mean_test_consistency"],
                    "train_reflective_region_psnr": summary["mean_train_reflective_psnr_reflection_json"],
                    "test_reflective_region_psnr": summary["mean_test_reflective_psnr_reflection_json"],
                    "train_full_psnr": summary["mean_train_full_psnr"],
                    "test_full_psnr": summary["mean_test_full_psnr"],
                    "train_full_ssim": summary["mean_train_full_ssim"],
                    "test_full_ssim": summary["mean_test_full_ssim"],
                    "train_full_lpips": summary["mean_train_full_lpips"],
                    "test_full_lpips": summary["mean_test_full_lpips"],
                    "train_reflective_psnr": summary["mean_train_reflective_psnr"],
                    "test_reflective_psnr": summary["mean_test_reflective_psnr"],
                    "train_reflective_ssim": summary["mean_train_reflective_ssim"],
                    "test_reflective_ssim": summary["mean_test_reflective_ssim"],
                    "train_reflective_lpips": summary["mean_train_reflective_lpips"],
                    "test_reflective_lpips": summary["mean_test_reflective_lpips"],
                }
            )

    lines = []
    lines.append("# RC-RefGS FD-P2-lite Non-Shiny-Real Complete Metric Set Evaluation")
    lines.append("")
    lines.append("## 1. Scope and metric set")
    lines.append("- Included: Shiny Blender Synthetic + Glossy Synthetic, seed 0.")
    lines.append("- Main: 14 scenes × 2 variants = 28 models.")
    lines.append("- Ablation: 14 scenes × 3 variants = 42 models.")
    lines.append("- Metrics: reflection consistency + render quality (full/reflective PSNR, SSIM, LPIPS).")
    lines.append("")
    lines.append("## 2. Completion of metric evaluation")
    lines.append(f"- Main evaluated models: {len(main_records)}/28")
    lines.append(f"- Ablation evaluated models: {len(ablation_records)}/42")
    lines.append(f"- Missing/failed metric cells: {len(failures)}")
    lines.append("")
    lines.append("## 3. Main base/RC results under complete metrics")
    lines.append(f"- Pairwise coverage: {len(main_pairs)}/14")
    lines.append(f"- RC lowers reflection consistency on train: {rc_win_counts['train_rc_lower_consistency']}/14")
    lines.append(f"- RC lowers reflection consistency on test: {rc_win_counts['test_rc_lower_consistency']}/14")
    if rc_win_counts["not_lower_cases"]:
        lines.append("- Non-lower exception(s):")
        for item in rc_win_counts["not_lower_cases"]:
            lines.append(f"  - {item['dataset']}/{item['scene']} {item['split']} delta={item['delta']:.6f}")
    lines.append("")
    lines.append("### Mean delta (rc - base)")
    lines.append("| Split | Consistency | ReflRegion PSNR | Full PSNR | Full SSIM | Full LPIPS | Refl PSNR | Refl SSIM | Refl LPIPS |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for split in ("train", "test"):
        agg = aggregate_main[split]
        lines.append(
            "| "
            + split
            + " | "
            + " | ".join(
                [
                    _fmt(agg["mean_delta_consistency"]),
                    _fmt(agg["mean_delta_reflective_region_psnr"]),
                    _fmt(agg["mean_delta_full_psnr"]),
                    _fmt(agg["mean_delta_full_ssim"]),
                    _fmt(agg["mean_delta_full_lpips"]),
                    _fmt(agg["mean_delta_reflective_psnr"]),
                    _fmt(agg["mean_delta_reflective_ssim"]),
                    _fmt(agg["mean_delta_reflective_lpips"]),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## 4. Ablation results under complete metrics")
    lines.append("| Dataset | Variant | Complete/Expected | Train Consistency | Test Consistency | Train Full PSNR | Test Full PSNR | Train Full SSIM | Test Full SSIM | Train Full LPIPS | Test Full LPIPS |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for summary in sorted(ablation_summary, key=lambda s: (s["dataset"], s["variant"])):
        lines.append(
            "| "
            + " | ".join(
                [
                    summary["dataset"],
                    summary["variant"],
                    f"{summary['complete_models']}/{summary['expected_models']}",
                    _fmt(summary["mean_train_consistency"]),
                    _fmt(summary["mean_test_consistency"]),
                    _fmt(summary["mean_train_full_psnr"]),
                    _fmt(summary["mean_test_full_psnr"]),
                    _fmt(summary["mean_train_full_ssim"]),
                    _fmt(summary["mean_test_full_ssim"]),
                    _fmt(summary["mean_train_full_lpips"]),
                    _fmt(summary["mean_test_full_lpips"]),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## 5. Consistency-quality tradeoffs")
    lines.append(f"- Cases where RC improves consistency but degrades at least one quality metric: {len(tradeoff_cases)}")
    for item in tradeoff_cases[:20]:
        detail = ", ".join(f"{d['metric']}={d['delta']:+.6f}" for d in item["degrades"][:5])
        lines.append(f"- {item['dataset']}/{item['scene']} {item['split']}: {detail}")
    if len(tradeoff_cases) > 20:
        lines.append(f"- ... {len(tradeoff_cases) - 20} additional cases in JSON artifact.")
    lines.append("")
    lines.append("## 6. Limitations")
    lines.append("- Shiny Blender Real remains excluded due to OOM blocker.")
    lines.append("- Single-seed only.")
    lines.append("- This task does not retrain or recover jobs.")
    lines.append("")
    lines.append("## 7. Claim boundary")
    lines.append("- No full 17-scene FD-P2 claim in this task.")
    lines.append("- No full 51-cell ablation claim in this task.")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "main_evaluated_models": len(main_records),
                "main_expected_models": 28,
                "ablation_evaluated_models": len(ablation_records),
                "ablation_expected_models": 42,
                "missing_or_failed_metric_cells": len(failures),
                "main_pair_count": len(main_pairs),
                "rc_train_wins": rc_win_counts["train_rc_lower_consistency"],
                "rc_test_wins": rc_win_counts["test_rc_lower_consistency"],
                "tradeoff_cases": len(tradeoff_cases),
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
