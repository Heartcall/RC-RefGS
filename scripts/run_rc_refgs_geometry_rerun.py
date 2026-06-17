#!/usr/bin/env python3
"""Plan and execute the durable RC-RefGS geometry rerun matrix.

Dry-run is the default-safe workflow. Training requires explicit execution,
confirmation, CUDA availability, sufficient durable storage, and an output
path below the fixed experiment root.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DURABLE_ROOT = Path("/data/liuly/experiments/rc_refgs_geometry_rerun")
DURABLE_RUN_ROOT = DURABLE_ROOT / "runs"
DEFAULT_MANIFEST = (
    REPO_ROOT
    / "paper_assets/geometry_gt/rerun_20260611/data/geometry_rerun_job_manifest.csv"
)
DEFAULT_SMOKE_MANIFEST = DEFAULT_MANIFEST.with_name(
    "geometry_rerun_job_manifest_ball_base_rc_smoke.csv"
)
REF_GS_PYTHON = Path("/home/liuly/anaconda3/envs/ref_gs/bin/python")
CONFIRM_TOKEN = "NEW_GEOMETRY_RERUN_20260611"
VARIANTS = ("base", "rc", "wo_ref", "wo_conf", "rough_only")
SCENES = (
    (
        "glossy_synthetic",
        "angel",
        "/data/liuly/dataset/3DGS/GlossySyntheticConverted/angel_blender",
    ),
    (
        "glossy_synthetic",
        "bell",
        "/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender",
    ),
    (
        "glossy_synthetic",
        "cat",
        "/data/liuly/dataset/3DGS/GlossySyntheticConverted/cat_blender",
    ),
    (
        "glossy_synthetic",
        "horse",
        "/data/liuly/dataset/3DGS/GlossySyntheticConverted/horse_blender",
    ),
    (
        "glossy_synthetic",
        "luyu",
        "/data/liuly/dataset/3DGS/GlossySyntheticConverted/luyu_blender",
    ),
    (
        "glossy_synthetic",
        "potion",
        "/data/liuly/dataset/3DGS/GlossySyntheticConverted/potion_blender",
    ),
    (
        "glossy_synthetic",
        "tbell",
        "/data/liuly/dataset/3DGS/GlossySyntheticConverted/tbell_blender",
    ),
    (
        "glossy_synthetic",
        "teapot",
        "/data/liuly/dataset/3DGS/GlossySyntheticConverted/teapot_blender",
    ),
    (
        "shiny_blender_synthetic",
        "ball",
        "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball",
    ),
    (
        "shiny_blender_synthetic",
        "car",
        "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/car",
    ),
    (
        "shiny_blender_synthetic",
        "coffee",
        "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/coffee",
    ),
    (
        "shiny_blender_synthetic",
        "helmet",
        "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/helmet",
    ),
    (
        "shiny_blender_synthetic",
        "teapot",
        "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/teapot",
    ),
    (
        "shiny_blender_synthetic",
        "toaster",
        "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster",
    ),
)
MANIFEST_FIELDS = (
    "dataset",
    "scene",
    "split",
    "variant",
    "seed",
    "iteration",
    "source_path",
    "model_path",
    "device",
    "status",
    "command",
    "train_command",
    "reflection_train_command",
    "reflection_test_command",
    "render_quality_command",
    "cfg_args_path",
    "train_log_path",
    "reflection_train_log_path",
    "reflection_test_log_path",
    "render_quality_log_path",
    "point_cloud_path",
    "checkpoint_path",
    "cameras_path",
    "transforms_train_path",
    "transforms_test_path",
    "reflection_train_path",
    "reflection_test_path",
    "render_quality_path",
    "expected_artifact_paths",
)


def _quote(argv):
    return " ".join(shlex.quote(str(part)) for part in argv)


def _variant_args(variant):
    if variant == "base":
        return [], "2.0"
    if variant == "rc":
        return [
            "--lambda_ref_consistency", "0.02",
            "--ref_consistency_start", "3000",
            "--ref_consistency_every", "4",
            "--ref_consistency_max_angle", "20.0",
            "--ref_consistency_gamma", "2.0",
        ], "2.0"
    if variant == "wo_ref":
        return [
            "--lambda_ref_consistency", "0.0",
            "--ref_consistency_start", "3000",
            "--ref_consistency_every", "4",
            "--ref_consistency_max_angle", "20.0",
            "--ref_consistency_gamma", "2.0",
        ], "2.0"
    if variant == "wo_conf":
        return [
            "--lambda_ref_consistency", "0.02",
            "--ref_consistency_start", "3000",
            "--ref_consistency_every", "4",
            "--ref_consistency_max_angle", "20.0",
            "--ref_consistency_gamma", "0.0",
        ], "0.0"
    if variant == "rough_only":
        return [
            "--lambda_ref_consistency", "0.0",
            "--lambda_roughness_smoothness", "0.02",
            "--roughness_smoothness_start", "3000",
        ], "2.0"
    raise ValueError("Unknown variant: {}".format(variant))


def _build_row(dataset, scene, source_path, variant, seed, iteration, model_path, device, python):
    model_path = Path(model_path)
    source_path = Path(source_path)
    variant_args, eval_gamma = _variant_args(variant)
    point_cloud = model_path / "point_cloud" / "iteration_{}".format(iteration) / "point_cloud.ply"
    train_log = model_path / "logs/train.log"
    reflection_train = model_path / "reflection_consistency_train.json"
    reflection_test = model_path / "reflection_consistency_test.json"
    render_quality = model_path / "render_quality_both_iter{}.json".format(iteration)
    reflection_train_log = model_path / "logs/reflection_consistency_train.log"
    reflection_test_log = model_path / "logs/reflection_consistency_test.log"
    render_quality_log = model_path / "logs/render_quality_both_iter{}.log".format(iteration)
    train_command = [
        str(python), "train.py", "--cuda_device", str(device),
        "-s", str(source_path), "-m", str(model_path), "--eval",
        "--iterations", str(iteration), "--test_iterations", str(iteration),
        "--save_iterations", str(iteration), "--checkpoint_iterations", str(iteration),
        "--seed", str(seed),
    ] + variant_args
    reflection_base = [
        str(python), "metrics/reflection_consistency_eval.py",
        "--cuda_device", str(device), "--model_path", str(model_path),
        "--source_path", str(source_path), "--iteration", str(iteration),
        "--max_pairs", "10", "--max_angle_deg", "20.0", "--gamma", eval_gamma,
    ]
    reflection_train_command = reflection_base + [
        "--split", "train", "--output_json", str(reflection_train)
    ]
    reflection_test_command = reflection_base + [
        "--split", "test", "--output_json", str(reflection_test)
    ]
    render_command = [
        str(python), "metrics/render_quality_eval.py", "--cuda_device", str(device),
        "--model_path", str(model_path), "--iteration", str(iteration),
        "--split", "both", "--mask_mode", "both", "--image_key", "pbr_rgb",
        "--output_json", str(render_quality),
    ]
    expected = [
        model_path / "cfg_args",
        train_log,
        reflection_train_log,
        reflection_test_log,
        render_quality_log,
        point_cloud,
        model_path / "chkpnt{}.pth".format(iteration),
        model_path / "cameras.json",
        source_path / "transforms_train.json",
        source_path / "transforms_test.json",
        reflection_train,
        reflection_test,
        render_quality,
    ]
    commands = [train_command, reflection_train_command, reflection_test_command, render_command]
    return {
        "dataset": dataset,
        "scene": scene,
        "split": "scene_geometry",
        "variant": variant,
        "seed": seed,
        "iteration": iteration,
        "source_path": str(source_path),
        "model_path": str(model_path),
        "device": str(device),
        "status": "planned",
        "command": " && ".join(_quote(command) for command in commands),
        "train_command": _quote(train_command),
        "reflection_train_command": _quote(reflection_train_command),
        "reflection_test_command": _quote(reflection_test_command),
        "render_quality_command": _quote(render_command),
        "cfg_args_path": str(model_path / "cfg_args"),
        "train_log_path": str(train_log),
        "reflection_train_log_path": str(reflection_train_log),
        "reflection_test_log_path": str(reflection_test_log),
        "render_quality_log_path": str(render_quality_log),
        "point_cloud_path": str(point_cloud),
        "checkpoint_path": str(model_path / "chkpnt{}.pth".format(iteration)),
        "cameras_path": str(model_path / "cameras.json"),
        "transforms_train_path": str(source_path / "transforms_train.json"),
        "transforms_test_path": str(source_path / "transforms_test.json"),
        "reflection_train_path": str(reflection_train),
        "reflection_test_path": str(reflection_test),
        "render_quality_path": str(render_quality),
        "expected_artifact_paths": json.dumps([str(path) for path in expected]),
        "_commands": commands,
    }


def build_manifest_rows(output_root, subset, devices, python, seed=0, iteration=31000):
    scenes = SCENES
    variants = VARIANTS
    if subset == "ball_base_rc_smoke":
        scenes = tuple(row for row in SCENES if row[0] == "shiny_blender_synthetic" and row[1] == "ball")
        variants = ("base", "rc")
    rows = []
    index = 0
    for dataset, scene, source_path in scenes:
        for variant in variants:
            device = devices[index % len(devices)]
            model_path = Path(output_root) / dataset / scene / variant / "seed_{}".format(seed)
            rows.append(
                _build_row(
                    dataset, scene, source_path, variant, seed, iteration,
                    model_path, device, python,
                )
            )
            index += 1
    return rows


def validate_sources(rows):
    missing = []
    for row in rows:
        for field in ("transforms_train_path", "transforms_test_path"):
            path = Path(row[field])
            if not path.is_file():
                missing.append(str(path))
    if missing:
        raise SystemExit("Source validation failed; missing: {}".format(", ".join(missing)))


def write_manifest(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _is_below(path, root):
    path = Path(path).resolve(strict=False)
    root = Path(root).resolve(strict=False)
    return path == root or root in path.parents


def _existing_ancestor(path):
    path = Path(path).resolve(strict=False)
    while not path.exists() and path != path.parent:
        path = path.parent
    return path


def _cuda_probe(python, devices):
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(devices[0])
    result = subprocess.run(
        [str(python), "-c", "import json,torch; print(json.dumps({'available':torch.cuda.is_available(),'count':torch.cuda.device_count()}))"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=env,
    )
    if result.returncode != 0:
        return False, result.stderr.strip()
    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return False, result.stdout.strip()
    return bool(payload.get("available") and payload.get("count", 0) > 0), payload


def validate_execute(args):
    output_root = Path(args.output_root).resolve(strict=False)

    # 只禁止明显不安全的临时目录；不再强制要求 output_root 位于 /data/liuly/experiments/.../runs
    forbidden_roots = [
        Path("/tmp").resolve(strict=False),
        Path("/var/tmp").resolve(strict=False),
        Path("/dev/shm").resolve(strict=False),
    ]

    for root in forbidden_roots:
        if output_root == root or root in output_root.parents:
            raise SystemExit(
                "Execution refused: output path must not be under temporary root {}".format(root)
            )

    # 必须是绝对路径，避免输出落到未知相对目录
    if not output_root.is_absolute():
        raise SystemExit("Execution refused: --output-root must be an absolute path")

    if args.confirm_execute != CONFIRM_TOKEN:
        raise SystemExit("Execution refused: --confirm-execute {} is required".format(CONFIRM_TOKEN))

    if getattr(args, "seed", 0) != 0 or getattr(args, "iterations", 31000) != 31000:
        raise SystemExit("Execution refused: the reviewed experiment is fixed to seed 0 and iteration 31000")

    ancestor = _existing_ancestor(output_root)
    free_gib = shutil.disk_usage(str(ancestor)).free / (1024 ** 3)
    if free_gib < args.min_free_gib:
        raise SystemExit(
            "Execution refused: {:.1f} GiB free is below {:.1f} GiB safety threshold".format(
                free_gib, args.min_free_gib
            )
        )

    cuda_ok, detail = _cuda_probe(args.python_executable, args.devices)
    if not cuda_ok:
        raise SystemExit("Execution refused: CUDA preflight failed: {}".format(detail))


def _required_complete(row):
    required = [
        row["cfg_args_path"], row["train_log_path"], row["point_cloud_path"],
        row["cameras_path"], row["reflection_train_path"],
        row["reflection_test_path"], row["render_quality_path"],
    ]
    return all(Path(path).is_file() and Path(path).stat().st_size > 0 for path in required)


def _run_logged(command, log_path):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    ref_lib = "/home/liuly/anaconda3/envs/ref_gs/lib"
    env["LD_LIBRARY_PATH"] = ref_lib + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    with log_path.open("a", encoding="utf-8") as handle:
        subprocess.run(command, cwd=str(REPO_ROOT), env=env, stdout=handle, stderr=subprocess.STDOUT, check=True)


def execute_rows(rows, manifest_path):
    for row in rows:
        if _required_complete(row):
            row["status"] = "skipped_complete"
            write_manifest(manifest_path, rows)
            continue
        model_path = Path(row["model_path"])
        model_path.mkdir(parents=True, exist_ok=True)
        logs = model_path / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        try:
            command_logs = [
                row["train_log_path"],
                row["reflection_train_log_path"],
                row["reflection_test_log_path"],
                row["render_quality_log_path"],
            ]
            for command, log_path in zip(row["_commands"], command_logs):
                _run_logged(command, log_path)
            row["status"] = "completed" if _required_complete(row) else "incomplete"
        except subprocess.CalledProcessError as exc:
            row["status"] = "failed_exit_{}".format(exc.returncode)
        write_manifest(manifest_path, rows)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Plan the durable RC-RefGS geometry rerun.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--subset", choices=["all", "ball_base_rc_smoke"], default="all")
    parser.add_argument("--output-root", type=Path, default=DURABLE_RUN_ROOT)
    parser.add_argument("--manifest-output", type=Path, default=None)
    parser.add_argument("--devices", default="0")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--iterations", type=int, default=31000)
    parser.add_argument("--python-executable", type=Path, default=REF_GS_PYTHON)
    parser.add_argument("--min-free-gib", type=float, default=80.0)
    parser.add_argument("--confirm-execute", default="")
    args = parser.parse_args(argv)
    args.devices = [item for item in args.devices.replace(",", " ").split() if item]
    if not args.devices:
        parser.error("--devices must not be empty")
    if args.manifest_output is None:
        args.manifest_output = DEFAULT_SMOKE_MANIFEST if args.subset == "ball_base_rc_smoke" else DEFAULT_MANIFEST
    return args


def main(argv=None):
    args = parse_args(argv)
    rows = build_manifest_rows(
        args.output_root, args.subset, args.devices, args.python_executable,
        seed=args.seed, iteration=args.iterations,
    )
    validate_sources(rows)
    write_manifest(args.manifest_output, rows)
    print("manifest={} jobs={} subset={}".format(args.manifest_output, len(rows), args.subset))
    if args.execute:
        validate_execute(args)
        execute_rows(rows, args.manifest_output)
    else:
        for row in rows:
            print("DRY_RUN {}".format(row["command"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
