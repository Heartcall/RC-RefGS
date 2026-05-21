#!/usr/bin/env python
"""Direct Python launcher for RC-RefGS ablation runs.

This avoids the nested bash/conda path used by run_rc_refgs_ablation.sh. Invoke
it from the desired Python environment, for example:

    conda run -n ref_gs python scripts/run_rc_refgs_ablation_direct.py --dry_run
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


DEFAULT_SCENES = ("teapot", "toaster", "car")
DEFAULT_VARIANTS = ("base", "rc", "wo_ref", "wo_conf", "rough_only")
SUPPORTED_METRICS = ("reflection_consistency",)
MANIFEST_FIELDS = (
    "data_root",
    "output_root",
    "scenes",
    "variants",
    "seeds",
    "iterations",
    "cuda_device",
    "lambda_ref_consistency",
    "ref_consistency_start",
    "ref_consistency_every",
    "ref_consistency_max_angle",
    "ref_consistency_gamma",
    "wo_conf_gamma",
    "roughness_smoothness_lambda",
    "roughness_smoothness_start",
    "max_pairs",
    "pair_list_json",
    "metrics",
    "summary_json",
    "check_missing",
    "skip_train",
    "skip_metrics",
    "dry_run",
    "quiet",
    "include_seed_in_path",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _quote_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _run(command: list[str], *, cwd: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"DRY_RUN {_quote_command(command)}")
        return
    subprocess.run(command, cwd=str(cwd), check=True)


def _load_manifest(manifest_json: str) -> dict:
    with open(manifest_json, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    if not isinstance(manifest, dict):
        raise ValueError("Experiment manifest must be a JSON object")

    unknown_fields = sorted(set(manifest) - set(MANIFEST_FIELDS))
    if unknown_fields:
        raise ValueError(f"Unknown manifest fields: {', '.join(unknown_fields)}")
    return manifest


def _cli_option_names(argv: list[str]) -> set[str]:
    names = set()
    for token in argv:
        if token.startswith("--"):
            name = token[2:].split("=", 1)[0].replace("-", "_")
            names.add(name)
    return names


def _validate_manifest_metrics(metrics) -> list[str]:
    if metrics is None:
        return list(SUPPORTED_METRICS)
    if isinstance(metrics, str):
        metrics = [metrics]
    if not isinstance(metrics, list):
        raise ValueError("Manifest field 'metrics' must be a string or list")

    unsupported = sorted(set(metrics) - set(SUPPORTED_METRICS))
    if unsupported:
        raise ValueError(f"Unsupported manifest metrics: {', '.join(unsupported)}")
    return metrics


def _apply_manifest(args: argparse.Namespace, argv: list[str]) -> argparse.Namespace:
    if args.manifest_json is None:
        return args

    manifest = _load_manifest(args.manifest_json)
    cli_names = _cli_option_names(argv)
    metrics = _validate_manifest_metrics(manifest.get("metrics"))

    for key, value in manifest.items():
        if key == "metrics" or key in cli_names:
            continue
        setattr(args, key, value)

    if "skip_metrics" not in cli_names and "metrics" in manifest:
        args.skip_metrics = len(metrics) == 0
    return args


def _model_path(
    output_root: Path,
    scene: str,
    variant: str,
    seed: int,
    *,
    include_seed_in_path: bool,
) -> Path:
    if include_seed_in_path:
        return output_root / f"{scene}_{variant}_seed{seed}"
    return output_root / f"{scene}_{variant}"


def _variant_train_args(args: argparse.Namespace, variant: str) -> tuple[list[str], str]:
    train_args: list[str] = []
    eval_gamma = args.ref_consistency_gamma

    if variant == "base":
        return train_args, eval_gamma
    if variant == "rc":
        train_args.extend(
            [
                "--lambda_ref_consistency",
                str(args.lambda_ref_consistency),
                "--ref_consistency_start",
                str(args.ref_consistency_start),
                "--ref_consistency_every",
                str(args.ref_consistency_every),
                "--ref_consistency_max_angle",
                str(args.ref_consistency_max_angle),
                "--ref_consistency_gamma",
                str(args.ref_consistency_gamma),
            ]
        )
        return train_args, eval_gamma
    if variant == "wo_ref":
        train_args.extend(
            [
                "--lambda_ref_consistency",
                "0.0",
                "--ref_consistency_start",
                str(args.ref_consistency_start),
                "--ref_consistency_every",
                str(args.ref_consistency_every),
                "--ref_consistency_max_angle",
                str(args.ref_consistency_max_angle),
                "--ref_consistency_gamma",
                str(args.ref_consistency_gamma),
            ]
        )
        return train_args, eval_gamma
    if variant == "wo_conf":
        eval_gamma = args.wo_conf_gamma
        train_args.extend(
            [
                "--lambda_ref_consistency",
                str(args.lambda_ref_consistency),
                "--ref_consistency_start",
                str(args.ref_consistency_start),
                "--ref_consistency_every",
                str(args.ref_consistency_every),
                "--ref_consistency_max_angle",
                str(args.ref_consistency_max_angle),
                "--ref_consistency_gamma",
                str(args.wo_conf_gamma),
            ]
        )
        return train_args, eval_gamma
    if variant == "rough_only":
        train_args.extend(
            [
                "--lambda_ref_consistency",
                "0.0",
                "--lambda_roughness_smoothness",
                str(args.roughness_smoothness_lambda),
                "--roughness_smoothness_start",
                str(args.roughness_smoothness_start),
            ]
        )
        return train_args, eval_gamma
    raise ValueError(f"Unknown variant: {variant}")


def _train_command(args: argparse.Namespace, scene: str, variant: str, model_path: Path, seed: int) -> list[str]:
    source_path = Path(args.data_root) / scene
    variant_args, _ = _variant_train_args(args, variant)
    command = [
        sys.executable,
        "train.py",
        "--cuda_device",
        args.cuda_device,
        "-s",
        str(source_path),
        "-m",
        str(model_path),
        "--eval",
        "--iterations",
        str(args.iterations),
        "--test_iterations",
        str(args.iterations),
        "--save_iterations",
        str(args.iterations),
        "--seed",
        str(seed),
    ]
    if args.quiet:
        command.append("--quiet")
    command.extend(variant_args)
    return command


def _metric_command(
    args: argparse.Namespace,
    scene: str,
    model_path: Path,
    split: str,
    eval_gamma: str,
) -> list[str]:
    source_path = Path(args.data_root) / scene
    metric_filename = "reflection_consistency_{split}.json"
    command = [
        sys.executable,
        "metrics/reflection_consistency_eval.py",
        "--cuda_device",
        args.cuda_device,
        "--model_path",
        str(model_path),
        "--source_path",
        str(source_path),
        "--iteration",
        str(args.iterations),
        "--split",
        split,
        "--max_pairs",
        str(args.max_pairs),
        "--max_angle_deg",
        str(args.ref_consistency_max_angle),
        "--gamma",
        str(eval_gamma),
        "--output_json",
        str(model_path / metric_filename.format(split=split)),
    ]
    if args.pair_list_json:
        command.extend(["--pair_list_json", str(args.pair_list_json)])
    return command


def _expected_artifacts(args: argparse.Namespace, model_path: Path) -> list[str]:
    artifacts: list[str] = []
    if not args.skip_train:
        artifacts.append(str(model_path / "point_cloud" / f"iteration_{args.iterations}" / "point_cloud.ply"))
    if not args.skip_metrics:
        for split in ("train", "test"):
            artifacts.append(str(model_path / f"reflection_consistency_{split}.json"))
    return artifacts


def _build_jobs(
    args: argparse.Namespace,
    output_root: Path,
    *,
    include_seed_in_path: bool,
) -> list[dict]:
    jobs: list[dict] = []
    for seed in args.seeds:
        for scene in args.scenes:
            for variant in args.variants:
                model_path = _model_path(
                    output_root,
                    scene,
                    variant,
                    seed,
                    include_seed_in_path=include_seed_in_path,
                )
                _, eval_gamma = _variant_train_args(args, variant)
                metric_commands = {
                    split: _metric_command(args, scene, model_path, split, eval_gamma)
                    for split in ("train", "test")
                }
                jobs.append(
                    {
                        "seed": seed,
                        "scene": scene,
                        "variant": variant,
                        "model_path": str(model_path),
                        "train_command": _train_command(args, scene, variant, model_path, seed),
                        "metric_commands": metric_commands,
                        "expected_artifacts": _expected_artifacts(args, model_path),
                    }
                )
    return jobs


def _collect_missing_artifacts(jobs: list[dict]) -> list[str]:
    missing_artifacts: list[str] = []
    for job in jobs:
        for artifact in job["expected_artifacts"]:
            if not Path(artifact).exists():
                missing_artifacts.append(artifact)
    return missing_artifacts


def _write_expansion_summary(
    summary_json: str | None,
    args: argparse.Namespace,
    jobs: list[dict],
    *,
    include_seed_in_path: bool,
    missing_artifacts: list[str],
) -> None:
    if summary_json is None:
        return

    summary = {
        "manifest_json": args.manifest_json,
        "data_root": args.data_root,
        "output_root": args.output_root,
        "scenes": args.scenes,
        "variants": args.variants,
        "seeds": args.seeds,
        "iterations": args.iterations,
        "cuda_device": args.cuda_device,
        "include_seed_in_path": include_seed_in_path,
        "skip_train": args.skip_train,
        "skip_metrics": args.skip_metrics,
        "check_missing": args.check_missing,
        "job_count": len(jobs),
        "jobs": jobs,
        "missing_artifacts": missing_artifacts,
    }
    summary["missing_count"] = len(summary["missing_artifacts"])

    summary_path = Path(summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RC-RefGS ablations without nested shell/conda wrapping.")
    parser.add_argument("--manifest_json", default=None)
    parser.add_argument("--data_root", default="/data/liuly/dataset/3DGS/refnerf")
    parser.add_argument("--output_root", default="output/rc_refgs")
    parser.add_argument("--scenes", nargs="+", default=list(DEFAULT_SCENES))
    parser.add_argument("--variants", nargs="+", default=list(DEFAULT_VARIANTS))
    parser.add_argument("--seeds", nargs="+", type=int, default=[0])
    parser.add_argument("--include_seed_in_path", action="store_true")
    parser.add_argument("--iterations", type=int, default=31000)
    parser.add_argument("--cuda_device", default="auto")
    parser.add_argument("--lambda_ref_consistency", default="0.02")
    parser.add_argument("--ref_consistency_start", default="3000")
    parser.add_argument("--ref_consistency_every", default="4")
    parser.add_argument("--ref_consistency_max_angle", default="20.0")
    parser.add_argument("--ref_consistency_gamma", default="2.0")
    parser.add_argument("--wo_conf_gamma", default="0.0")
    parser.add_argument("--roughness_smoothness_lambda", default="0.02")
    parser.add_argument("--roughness_smoothness_start", default="3000")
    parser.add_argument("--max_pairs", type=int, default=10)
    parser.add_argument("--pair_list_json", default=None)
    parser.add_argument("--summary_json", default=None)
    parser.add_argument("--check_missing", action="store_true")
    parser.add_argument("--skip_train", action="store_true")
    parser.add_argument("--skip_metrics", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--quiet", dest="quiet", action="store_true", default=True)
    parser.add_argument("--no_quiet", dest="quiet", action="store_false")
    args = parser.parse_args(argv)
    args = _apply_manifest(args, argv)
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = _repo_root()
    output_root = Path(args.output_root)
    include_seed_in_path = args.include_seed_in_path or len(args.seeds) > 1

    unknown_variants = sorted(set(args.variants) - set(DEFAULT_VARIANTS))
    if unknown_variants:
        raise SystemExit(f"Unknown variants: {', '.join(unknown_variants)}")

    jobs = _build_jobs(args, output_root, include_seed_in_path=include_seed_in_path)
    missing_artifacts: list[str] = []

    if args.check_missing:
        missing_artifacts = _collect_missing_artifacts(jobs)
        _write_expansion_summary(
            args.summary_json,
            args,
            jobs,
            include_seed_in_path=include_seed_in_path,
            missing_artifacts=missing_artifacts,
        )
        for artifact in missing_artifacts:
            print(f"MISSING {artifact}")
        if missing_artifacts:
            raise SystemExit(2)
        return 0

    for job in jobs:
        model_path = Path(job["model_path"])
        if not args.dry_run:
            model_path.mkdir(parents=True, exist_ok=True)

        print(f"[seed={job['seed']}] [{job['scene']}] {job['variant']} -> {model_path}")
        if not args.skip_train:
            _run(job["train_command"], cwd=repo_root, dry_run=args.dry_run)

        if not args.skip_metrics:
            for split in ("train", "test"):
                _run(job["metric_commands"][split], cwd=repo_root, dry_run=args.dry_run)

    missing_artifacts = _collect_missing_artifacts(jobs)
    _write_expansion_summary(
        args.summary_json,
        args,
        jobs,
        include_seed_in_path=include_seed_in_path,
        missing_artifacts=missing_artifacts,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
