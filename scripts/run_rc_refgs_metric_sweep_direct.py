#!/usr/bin/env python
"""Direct metric-sweep runner for RC-RefGS evidence collection.

This avoids shell loops for render/material metric collection. Evaluator stdout
is redirected into per-cell logs so full-split runs do not flood the terminal,
and every cell status is recorded in a machine-readable summary.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path


SUPPORTED_METRICS = ("render_quality", "material_quality")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _quote_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _metric_filename(metric: str, split: str, iteration: int) -> str:
    if metric == "render_quality":
        return "render_quality_{split}_iter{iteration}.json".format(split=split, iteration=iteration)
    if metric == "material_quality":
        return "material_quality_{split}_iter{iteration}.json".format(split=split, iteration=iteration)
    raise ValueError(f"Unsupported metric: {metric}")


def _metric_script(metric: str) -> str:
    if metric == "render_quality":
        return "metrics/render_quality_eval.py"
    if metric == "material_quality":
        return "metrics/material_quality_eval.py"
    raise ValueError(f"Unsupported metric: {metric}")


def _metric_command(args: argparse.Namespace, scene: str, variant: str, metric: str, model_path: Path) -> tuple[list[str], Path]:
    output_json = model_path / _metric_filename(metric, args.split, args.iteration)
    command = [
        sys.executable,
        _metric_script(metric),
        "--source_path",
        str(Path(args.data_root) / scene),
        "--model_path",
        str(model_path),
        "--iteration",
        str(args.iteration),
        "--split",
        args.split,
        "--mask_mode",
        args.mask_mode,
        "--cuda_device",
        args.cuda_device,
        "--output_json",
        str(output_json),
    ]
    if args.max_images >= 0:
        command.extend(["--max_images", str(args.max_images)])
    if metric == "render_quality" and args.skip_lpips:
        command.append("--skip_lpips")
    if args.quiet:
        command.append("--quiet")
    return command, output_json


def _build_jobs(args: argparse.Namespace) -> list[dict]:
    jobs = []
    for scene in args.scenes:
        for variant in args.variants:
            model_path = Path(args.model_root) / f"{scene}_{variant}"
            for metric in args.metrics:
                command, output_json = _metric_command(args, scene, variant, metric, model_path)
                log_path = Path(args.log_root) / scene / variant / f"{metric}_{args.split}_iter{args.iteration}.log"
                jobs.append(
                    {
                        "scene": scene,
                        "variant": variant,
                        "metric": metric,
                        "model_path": str(model_path),
                        "output_json": str(output_json),
                        "log_path": str(log_path),
                        "command": command,
                    }
                )
    return jobs


def _run_job(job: dict, *, cwd: Path, dry_run: bool) -> dict:
    started_at = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    if dry_run:
        result = dict(job)
        result.update(
            {
                "status": "dry_run",
                "returncode": 0,
                "started_at": started_at,
                "finished_at": started_at,
                "command_string": _quote_command(job["command"]),
            }
        )
        print(f"DRY_RUN {result['command_string']}")
        return result

    log_path = Path(job["log_path"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        completed = subprocess.run(
            job["command"],
            cwd=str(cwd),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            check=False,
        )
    finished_at = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    result = dict(job)
    result.update(
        {
            "status": "passed" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "started_at": started_at,
            "finished_at": finished_at,
            "command_string": _quote_command(job["command"]),
        }
    )
    print(f"{result['status'].upper()} {job['metric']} {job['scene']} {job['variant']} log={job['log_path']}")
    return result


def _write_summary(args: argparse.Namespace, jobs: list[dict], results: list[dict]) -> dict:
    summary = {
        "data_root": args.data_root,
        "model_root": args.model_root,
        "iteration": args.iteration,
        "split": args.split,
        "mask_mode": args.mask_mode,
        "max_images": args.max_images,
        "metrics": list(args.metrics),
        "scenes": list(args.scenes),
        "variants": list(args.variants),
        "cuda_device": args.cuda_device,
        "dry_run": args.dry_run,
        "stop_on_failure": args.stop_on_failure,
        "job_count": len(jobs),
        "completed_count": len(results),
        "failed_count": sum(1 for result in results if result["status"] == "failed"),
        "jobs": results,
    }
    if args.summary_json:
        summary_path = Path(args.summary_json)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
    return summary


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RC-RefGS render/material metric sweeps directly.")
    parser.add_argument("--data_root", default="/data/liuly/dataset/3DGS/refnerf")
    parser.add_argument("--model_root", required=True)
    parser.add_argument("--scenes", nargs="+", default=["teapot", "toaster", "car"])
    parser.add_argument("--variants", nargs="+", default=["base", "rc"])
    parser.add_argument("--metrics", nargs="+", choices=SUPPORTED_METRICS, default=list(SUPPORTED_METRICS))
    parser.add_argument("--iteration", type=int, required=True)
    parser.add_argument("--split", choices=["train", "test", "both"], default="both")
    parser.add_argument("--mask_mode", choices=["none", "reflective", "both"], default="both")
    parser.add_argument("--max_images", type=int, default=-1)
    parser.add_argument("--cuda_device", default="0")
    parser.add_argument("--summary_json", default=None)
    parser.add_argument("--log_root", required=True)
    parser.add_argument("--skip_lpips", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--stop_on_failure", action="store_true", default=True)
    parser.add_argument("--continue_on_failure", dest="stop_on_failure", action="store_false")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = _repo_root()
    jobs = _build_jobs(args)
    results = []

    for job in jobs:
        result = _run_job(job, cwd=repo_root, dry_run=args.dry_run)
        results.append(result)
        _write_summary(args, jobs, results)
        if result["status"] == "failed" and args.stop_on_failure:
            raise SystemExit(2)

    summary = _write_summary(args, jobs, results)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
