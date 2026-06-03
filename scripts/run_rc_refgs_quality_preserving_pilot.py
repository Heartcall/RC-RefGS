#!/usr/bin/env python
"""Safe pilot runner for RC-RefGS quality-preserving variants."""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_TARGET_CSV = Path("docs/superpowers/logs/rc-refgs-quality-regression-target-scenes-2026-06-01.csv")
DEFAULT_OUTPUT_ROOT = Path("/tmp/rc_refgs_quality_preserving_rc_i31000_20260601")
DEFAULT_VARIANTS = (
    "rc_qp_lam005",
    "rc_qp_lam010",
    "rc_qp_lam015",
    "rc_qp_lam010_start5000_every8",
)
OPTIONAL_VARIANTS = (
    "rc_qp_lam010_gamma10",
    "rc_qp_lam010_gamma15",
    "rc_qp_lam010_dssim01",
    "rc_qp_lam010_dssim03",
)
VARIANT_CONFIGS = {
    "rc_qp_lam005": {
        "lambda_ref_consistency": "0.005",
        "ref_consistency_start": "3000",
        "ref_consistency_every": "4",
        "ref_consistency_gamma": "2.0",
        "lambda_dssim": "0.2",
    },
    "rc_qp_lam010": {
        "lambda_ref_consistency": "0.01",
        "ref_consistency_start": "3000",
        "ref_consistency_every": "4",
        "ref_consistency_gamma": "2.0",
        "lambda_dssim": "0.2",
    },
    "rc_qp_lam015": {
        "lambda_ref_consistency": "0.015",
        "ref_consistency_start": "3000",
        "ref_consistency_every": "4",
        "ref_consistency_gamma": "2.0",
        "lambda_dssim": "0.2",
    },
    "rc_qp_lam010_start5000_every8": {
        "lambda_ref_consistency": "0.01",
        "ref_consistency_start": "5000",
        "ref_consistency_every": "8",
        "ref_consistency_gamma": "2.0",
        "lambda_dssim": "0.2",
    },
    "rc_qp_lam010_gamma10": {
        "lambda_ref_consistency": "0.01",
        "ref_consistency_start": "3000",
        "ref_consistency_every": "4",
        "ref_consistency_gamma": "1.0",
        "lambda_dssim": "0.2",
    },
    "rc_qp_lam010_gamma15": {
        "lambda_ref_consistency": "0.01",
        "ref_consistency_start": "3000",
        "ref_consistency_every": "4",
        "ref_consistency_gamma": "1.5",
        "lambda_dssim": "0.2",
    },
    "rc_qp_lam010_dssim01": {
        "lambda_ref_consistency": "0.01",
        "ref_consistency_start": "3000",
        "ref_consistency_every": "4",
        "ref_consistency_gamma": "2.0",
        "lambda_dssim": "0.1",
    },
    "rc_qp_lam010_dssim03": {
        "lambda_ref_consistency": "0.01",
        "ref_consistency_start": "3000",
        "ref_consistency_every": "4",
        "ref_consistency_gamma": "2.0",
        "lambda_dssim": "0.3",
    },
}
FORBIDDEN_OUTPUT_FRAGMENTS = (
    "rc_refgs_full_dataset_base_rc_i31000_20260527",
    "rc_refgs_full_dataset_ablations_i31000_20260528",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _quote(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _split_values(values: list[str] | None, default: tuple[str, ...] | None = None) -> list[str]:
    if not values:
        return list(default or [])
    split: list[str] = []
    for value in values:
        split.extend(part for part in value.replace(",", " ").split() if part)
    return split


def _load_target_scenes(target_csv: Path) -> list[dict]:
    if not target_csv.exists():
        raise FileNotFoundError(f"target CSV missing: {target_csv}")

    scenes: dict[tuple[str, str], dict] = {}
    with target_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dataset = row.get("dataset", "")
            scene = row.get("scene", "")
            if not dataset or not scene:
                continue
            if dataset == "shiny_blender_real":
                continue
            key = (dataset, scene)
            scenes.setdefault(
                key,
                {
                    "dataset": dataset,
                    "scene": scene,
                    "source_path": row.get("source_path", ""),
                    "selection_reason": row.get("selection_reason", ""),
                    "evidence": row.get("evidence", ""),
                },
            )
    if not scenes:
        raise ValueError(f"no non-Shiny-Real pilot scenes found in {target_csv}")
    return [scenes[key] for key in sorted(scenes)]


def _effective_iterations(args: argparse.Namespace) -> int:
    return args.smoke_iterations if args.smoke else args.iterations


def _model_path(output_root: Path, dataset: str, scene: str, variant: str) -> Path:
    return output_root / dataset / scene / variant / "seed_0"


def _expected_artifacts(model_path: Path, iteration: int) -> list[Path]:
    return [
        model_path / "point_cloud" / f"iteration_{iteration}" / "point_cloud.ply",
        model_path / "reflection_consistency_train.json",
        model_path / "reflection_consistency_test.json",
        model_path / f"render_quality_both_iter{iteration}.json",
        model_path / "launcher_summary.json",
    ]


def _expected_artifacts_before_summary(model_path: Path, iteration: int) -> list[Path]:
    return _expected_artifacts(model_path, iteration)[:-1]


def _is_complete(model_path: Path, iteration: int) -> bool:
    if not all(path.exists() for path in _expected_artifacts(model_path, iteration)):
        return False
    try:
        summary = json.loads((model_path / "launcher_summary.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return summary.get("status") in {"completed", "skipped_complete"}


def _train_command(args: argparse.Namespace, source_path: str, model_path: Path, variant: str) -> list[str]:
    cfg = VARIANT_CONFIGS[variant]
    iteration = _effective_iterations(args)
    return [
        sys.executable,
        "train.py",
        "--cuda_device",
        args.device,
        "-s",
        source_path,
        "-m",
        str(model_path),
        "--eval",
        "--iterations",
        str(iteration),
        "--test_iterations",
        str(iteration),
        "--save_iterations",
        str(iteration),
        "--seed",
        "0",
        "--lambda_ref_consistency",
        cfg["lambda_ref_consistency"],
        "--ref_consistency_start",
        cfg["ref_consistency_start"],
        "--ref_consistency_every",
        cfg["ref_consistency_every"],
        "--ref_consistency_max_angle",
        str(args.ref_consistency_max_angle),
        "--ref_consistency_gamma",
        cfg["ref_consistency_gamma"],
        "--lambda_dssim",
        cfg["lambda_dssim"],
        "--quiet",
    ]


def _reflection_command(args: argparse.Namespace, source_path: str, model_path: Path, split: str) -> list[str]:
    iteration = _effective_iterations(args)
    return [
        sys.executable,
        "metrics/reflection_consistency_eval.py",
        "--cuda_device",
        args.device,
        "--model_path",
        str(model_path),
        "--source_path",
        source_path,
        "--iteration",
        str(iteration),
        "--split",
        split,
        "--max_pairs",
        str(args.max_pairs),
        "--max_angle_deg",
        str(args.ref_consistency_max_angle),
        "--gamma",
        str(args.metric_gamma),
        "--output_json",
        str(model_path / f"reflection_consistency_{split}.json"),
        "--quiet",
    ]


def _render_quality_command(args: argparse.Namespace, source_path: str, model_path: Path, image_key: str) -> list[str]:
    iteration = _effective_iterations(args)
    return [
        sys.executable,
        "metrics/render_quality_eval.py",
        "--cuda_device",
        args.device,
        "--model_path",
        str(model_path),
        "--source_path",
        source_path,
        "--iteration",
        str(iteration),
        "--split",
        "both",
        "--mask_mode",
        "both",
        "--image_key",
        image_key,
        "--output_json",
        str(model_path / f"render_quality_both_iter{iteration}.json"),
        "--quiet",
    ]


def build_jobs(args: argparse.Namespace) -> list[dict]:
    scenes = _load_target_scenes(Path(args.target_csv))
    requested_scenes = set(_split_values(args.scenes)) if args.scenes else None
    variants = _split_values(args.variants, DEFAULT_VARIANTS)
    unknown = sorted(set(variants) - set(VARIANT_CONFIGS))
    if unknown:
        raise SystemExit(f"Unknown variants: {', '.join(unknown)}")

    output_root = Path(args.output_root)
    for fragment in FORBIDDEN_OUTPUT_FRAGMENTS:
        if fragment in str(output_root):
            raise SystemExit(f"Refusing output_root that overlaps existing FD-P2-lite roots: {output_root}")

    jobs: list[dict] = []
    iteration = _effective_iterations(args)
    for scene_info in scenes:
        if requested_scenes and scene_info["scene"] not in requested_scenes:
            continue
        if scene_info["dataset"] == "shiny_blender_real":
            continue
        for variant in variants:
            model_path = _model_path(output_root, scene_info["dataset"], scene_info["scene"], variant)
            metric_commands = {
                "reflection_consistency_train": _reflection_command(args, scene_info["source_path"], model_path, "train"),
                "reflection_consistency_test": _reflection_command(args, scene_info["source_path"], model_path, "test"),
                "render_quality_both_pbr_rgb": _render_quality_command(args, scene_info["source_path"], model_path, "pbr_rgb"),
                "render_quality_both_render_fallback": _render_quality_command(args, scene_info["source_path"], model_path, "render"),
            }
            jobs.append(
                {
                    "dataset": scene_info["dataset"],
                    "scene": scene_info["scene"],
                    "variant": variant,
                    "seed": 0,
                    "device": args.device,
                    "source_path": scene_info["source_path"],
                    "model_path": str(model_path),
                    "iterations": iteration,
                    "selection_reason": scene_info["selection_reason"],
                    "evidence": scene_info["evidence"],
                    "variant_config": dict(VARIANT_CONFIGS[variant]),
                    "train_command": _train_command(args, scene_info["source_path"], model_path, variant),
                    "metric_commands": metric_commands,
                    "expected_artifacts": [str(path) for path in _expected_artifacts(model_path, iteration)],
                }
            )

    if args.max_jobs is not None:
        jobs = jobs[: args.max_jobs]
    return jobs


def _run(command: list[str], cwd: Path, dry_run: bool) -> tuple[str, int | None]:
    if dry_run:
        return "dry_run", None
    result = subprocess.run(command, cwd=str(cwd), check=False)
    return ("completed" if result.returncode == 0 else "failed"), result.returncode


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_job_summary(model_path: Path, job: dict, status: str, args: argparse.Namespace, *, render_fallback_used: bool = False) -> None:
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runner": "scripts/run_rc_refgs_quality_preserving_pilot.py",
        "status": status,
        "dry_run": not args.execute,
        "smoke": args.smoke,
        "skip_train": args.skip_train,
        "skip_metrics": args.skip_metrics,
        "render_fallback_used": render_fallback_used,
        "environment_notes": {
            "cpu_side_orchestration": True,
            "cuda_device_arg": job["device"],
            "no_cuda_visible_devices_set_by_runner": True,
            "headline_render_quality": "split both, mask_mode both, image_key pbr_rgb; render fallback is recorded only on pbr_rgb failure",
        },
        "job": job,
        "commands": {
            "train": _quote(job["train_command"]),
            **{name: _quote(cmd) for name, cmd in job["metric_commands"].items()},
        },
    }
    _write_json(model_path / "launcher_summary.json", summary)


def _write_status(output_root: Path, args: argparse.Namespace, jobs: list[dict], job_statuses: list[dict]) -> None:
    summary = {}
    for status in ["dry_run", "completed", "failed", "skipped_complete", "partial"]:
        summary[status] = sum(1 for job in job_statuses if job["status"] == status)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runner": "scripts/run_rc_refgs_quality_preserving_pilot.py",
        "dry_run": not args.execute,
        "execute": args.execute,
        "smoke": args.smoke,
        "output_root": str(output_root),
        "target_csv": str(args.target_csv),
        "max_jobs": args.max_jobs,
        "iterations": _effective_iterations(args),
        "requested_iterations": args.iterations,
        "smoke_iterations": args.smoke_iterations,
        "devices": args.devices,
        "device": args.device,
        "variants": _split_values(args.variants, DEFAULT_VARIANTS),
        "excluded_datasets": ["shiny_blender_real"],
        "safety_boundaries": [
            "dry-run by default",
            "execute requires --execute --confirm_execute YES",
            "no Shiny Blender Real",
            "new output root only",
            "no metric definition changes",
            "no claim upgrade from smoke",
        ],
        "summary": summary,
        "job_count": len(jobs),
        "jobs": job_statuses,
    }
    _write_json(output_root / "pilot_status.json", payload)
    _write_json(output_root / "pilot_plan.json", {"jobs": jobs, **{k: payload[k] for k in payload if k != "jobs"}})

    lines = [
        "# RC-RefGS Quality-Preserving Pilot Status",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Mode: `{'execute' if args.execute else 'dry_run'}`",
        f"- Smoke mode: `{args.smoke}`",
        f"- Output root: `{output_root}`",
        f"- Job count: `{len(jobs)}`",
        f"- Summary: dry_run `{summary['dry_run']}`, completed `{summary['completed']}`, failed `{summary['failed']}`, skipped_complete `{summary['skipped_complete']}`, partial `{summary['partial']}`",
        "",
        "| dataset | scene | variant | status | model_path |",
        "| --- | --- | --- | --- | --- |",
    ]
    for job in job_statuses:
        lines.append(
            f"| {job['dataset']} | {job['scene']} | {job['variant']} | {job['status']} | `{job['model_path']}` |"
        )
    (output_root / "pilot_status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _execute_job(job: dict, args: argparse.Namespace, repo_root: Path) -> dict:
    model_path = Path(job["model_path"])
    iteration = job["iterations"]
    if _is_complete(model_path, iteration):
        return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": "skipped_complete"}

    model_path.mkdir(parents=True, exist_ok=True)
    if not args.execute:
        _write_job_summary(model_path, job, "dry_run", args)
        return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": "dry_run"}

    status = "completed"
    return_codes: dict[str, int | None] = {}
    if not args.skip_train:
        train_status, code = _run(job["train_command"], repo_root, False)
        return_codes["train"] = code
        if train_status == "failed":
            _write_job_summary(model_path, {**job, "return_codes": return_codes}, "failed", args)
            return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": "failed", "failed_step": "train"}

    render_fallback_used = False
    if not args.skip_metrics:
        for key in ["reflection_consistency_train", "reflection_consistency_test"]:
            metric_status, code = _run(job["metric_commands"][key], repo_root, False)
            return_codes[key] = code
            if metric_status == "failed":
                status = "failed"
                _write_job_summary(model_path, {**job, "return_codes": return_codes}, status, args)
                return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": status, "failed_step": key}

        metric_status, code = _run(job["metric_commands"]["render_quality_both_pbr_rgb"], repo_root, False)
        return_codes["render_quality_both_pbr_rgb"] = code
        if metric_status == "failed":
            render_fallback_used = True
            metric_status, code = _run(job["metric_commands"]["render_quality_both_render_fallback"], repo_root, False)
            return_codes["render_quality_both_render_fallback"] = code
            if metric_status == "failed":
                status = "failed"
                _write_job_summary(model_path, {**job, "return_codes": return_codes}, status, args, render_fallback_used=True)
                return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": status, "failed_step": "render_quality_both"}

    if not all(path.exists() for path in _expected_artifacts_before_summary(model_path, iteration)):
        status = "partial"
    _write_job_summary(model_path, {**job, "return_codes": return_codes}, status, args, render_fallback_used=render_fallback_used)
    return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": status}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare or execute bounded RC-RefGS quality-preserving pilot jobs.")
    parser.add_argument("--target_csv", default=str(DEFAULT_TARGET_CSV))
    parser.add_argument("--output_root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--devices", required=True, help="Comma/space device list; only one selected device is used.")
    parser.add_argument("--iterations", type=int, default=31000)
    parser.add_argument("--smoke_iterations", type=int, default=1000)
    parser.add_argument("--smoke", action="store_true", help="Use --smoke_iterations as the effective iteration count.")
    parser.add_argument("--max_jobs", type=int, default=1)
    parser.add_argument("--variants", nargs="+", default=list(DEFAULT_VARIANTS))
    parser.add_argument("--scenes", nargs="+", default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--dry_run", action="store_true", help="Explicit no-op alias for default dry-run mode.")
    parser.add_argument("--skip_train", action="store_true")
    parser.add_argument("--skip_metrics", action="store_true")
    parser.add_argument("--confirm_execute", default="")
    parser.add_argument("--max_pairs", type=int, default=10)
    parser.add_argument("--ref_consistency_max_angle", type=float, default=20.0)
    parser.add_argument("--metric_gamma", type=float, default=2.0)
    args = parser.parse_args(argv)

    devices = _split_values([args.devices])
    if not devices:
        raise SystemExit("--devices is required")
    args.device = devices[0]
    if args.execute and args.confirm_execute != "YES":
        raise SystemExit("--execute requires --confirm_execute YES")
    if args.dry_run and args.execute:
        raise SystemExit("--dry_run and --execute are mutually exclusive")
    if args.max_jobs is not None and args.max_jobs < 1:
        raise SystemExit("--max_jobs must be >= 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = _repo_root()
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    jobs = build_jobs(args)
    statuses = []
    for job in jobs:
        print(f"[{job['dataset']}/{job['scene']}] {job['variant']} -> {job['model_path']}")
        print(f"TRAIN {_quote(job['train_command'])}")
        for name, command in job["metric_commands"].items():
            print(f"METRIC {name} {_quote(command)}")
        statuses.append(_execute_job(job, args, repo_root))

    _write_status(output_root, args, jobs, statuses)
    failed = [job for job in statuses if job["status"] == "failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
