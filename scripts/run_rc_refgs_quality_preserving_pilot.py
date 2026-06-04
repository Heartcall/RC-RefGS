#!/usr/bin/env python
"""Safe pilot runner for RC-RefGS quality-preserving variants."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


DEFAULT_TARGET_CSV = Path("docs/superpowers/logs/rc-refgs-quality-regression-target-scenes-2026-06-01.csv")
DEFAULT_OUTPUT_ROOT = Path("/tmp/rc_refgs_quality_preserving_rc_i31000_20260601")
DEFAULT_SHINY_BLENDER_SYNTHETIC_ROOT = "/data/liuly/dataset/3DGS/Shiny Blender Synthetic"
DEFAULT_GLOSSY_SYNTHETIC_ROOT = "/data/liuly/dataset/3DGS/GlossySyntheticConverted"
DEFAULT_REF_GS_CONDA_PREFIX = "/home/liuly/anaconda3/envs/ref_gs"
DEFAULT_REF_GS_PYTHON = f"{DEFAULT_REF_GS_CONDA_PREFIX}/bin/python"
LOGICAL_CUDA_DEVICE = "0"
COMMAND_TAIL_BYTES = 8192
SOURCE_MARKERS = (
    "transforms_train.json",
    "transforms_test.json",
    "points3d.ply",
    "sparse",
    "colmap/sparse",
)
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


def _conda_prefix_from_python(python_executable: str) -> str:
    python_path = Path(python_executable)
    if python_path.name.startswith("python") and python_path.parent.name == "bin":
        return str(python_path.parent.parent)
    return ""


def _subprocess_env(
    python_executable: str | None = None,
    *,
    cuda_visible_devices: str | None = None,
    conda_prefix: str | None = None,
) -> dict[str, str]:
    env = os.environ.copy()
    selected_prefix = _conda_prefix_from_python(python_executable or sys.executable)
    effective_conda_prefix = conda_prefix or selected_prefix or env.get("CONDA_PREFIX")
    if effective_conda_prefix:
        env["CONDA_PREFIX"] = effective_conda_prefix
        conda_lib = str(Path(effective_conda_prefix) / "lib")
        existing_ld_path = env.get("LD_LIBRARY_PATH", "")
        if existing_ld_path == conda_lib or existing_ld_path.startswith(f"{conda_lib}:"):
            env["LD_LIBRARY_PATH"] = existing_ld_path
        else:
            env["LD_LIBRARY_PATH"] = conda_lib if not existing_ld_path else f"{conda_lib}:{existing_ld_path}"
    if cuda_visible_devices is not None:
        env["CUDA_VISIBLE_DEVICES"] = str(cuda_visible_devices)
    return env


def _environment_summary(env: dict[str, str], python_executable: str | None = None) -> dict[str, str | bool]:
    ld_library_path = env.get("LD_LIBRARY_PATH", "")
    selected_python = python_executable or sys.executable
    return {
        "sys_executable": sys.executable,
        "selected_python_executable": selected_python,
        "conda_prefix": env.get("CONDA_PREFIX", ""),
        "cuda_visible_devices": env.get("CUDA_VISIBLE_DEVICES", ""),
        "ld_library_path": ld_library_path,
        "ld_library_path_prefix": ld_library_path.split(":", 1)[0] if ld_library_path else "",
        "conda_libstdcxx": str(Path(env.get("CONDA_PREFIX", "")) / "lib" / "libstdc++.so.6")
        if env.get("CONDA_PREFIX")
        else "",
    }


def _failed_preflight_result(name: str, message: str) -> dict:
    return {
        "status": "failed",
        "failed_check": name,
        "return_code": None,
        "stdout": "",
        "stderr": message,
        "checks": {
            name: {
                "status": "failed",
                "return_code": None,
                "stdout": "",
                "stderr": message,
            }
        },
    }


def _captured_check(name: str, command: list[str], cwd: Path, env: dict[str, str]) -> tuple[dict, subprocess.CompletedProcess]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    check = {
        "command": _quote(command),
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "status": "completed" if result.returncode == 0 else "failed",
    }
    return check, result


def _preflight_env(repo_root: Path, env: dict[str, str], python_executable: str | None = None) -> dict:
    selected_python = python_executable or sys.executable
    if not selected_python:
        return _failed_preflight_result("sys_executable", "sys.executable is empty")
    if not Path(selected_python).exists():
        return _failed_preflight_result("sys_executable", f"selected Python executable does not exist: {selected_python}")

    conda_prefix = env.get("CONDA_PREFIX")
    if not conda_prefix:
        return _failed_preflight_result("conda_prefix", "CONDA_PREFIX is not set")

    libstdcxx = Path(conda_prefix) / "lib" / "libstdc++.so.6"
    if not libstdcxx.exists():
        return _failed_preflight_result("libstdcxx_exists", f"missing {libstdcxx}")

    checks: dict[str, dict] = {
        "sys_executable": {
            "status": "completed",
            "path": selected_python,
            "return_code": None,
            "stdout": "",
            "stderr": "",
        },
        "conda_prefix": {
            "status": "completed",
            "path": conda_prefix,
            "return_code": None,
            "stdout": "",
            "stderr": "",
        },
        "libstdcxx_exists": {
            "status": "completed",
            "path": str(libstdcxx),
            "return_code": None,
            "stdout": "",
            "stderr": "",
        },
    }

    strings_check, strings_result = _captured_check("libstdcxx_strings", ["strings", str(libstdcxx)], repo_root, env)
    if strings_result.returncode != 0:
        checks["libstdcxx_strings"] = strings_check
        return {
            "status": "failed",
            "failed_check": "libstdcxx_strings",
            "return_code": strings_result.returncode,
            "stdout": strings_result.stdout,
            "stderr": strings_result.stderr,
            "checks": checks,
        }
    if "GLIBCXX_3.4.29" not in strings_result.stdout:
        strings_check["status"] = "failed"
        strings_check["stderr"] = "GLIBCXX_3.4.29 not found in conda libstdc++.so.6"
        checks["libstdcxx_strings"] = strings_check
        return {
            "status": "failed",
            "failed_check": "libstdcxx_strings",
            "return_code": strings_result.returncode,
            "stdout": strings_result.stdout,
            "stderr": strings_check["stderr"],
            "checks": checks,
        }
    checks["libstdcxx_strings"] = {
        "command": strings_check["command"],
        "return_code": strings_result.returncode,
        "stdout": "GLIBCXX_3.4.29 found",
        "stderr": strings_result.stderr,
        "status": "completed",
    }

    import_command = [
        selected_python,
        "-c",
        "import torch; import nvdiffrast.torch as dr; print('runtime import OK')",
    ]
    import_check, import_result = _captured_check("runtime_import", import_command, repo_root, env)
    checks["runtime_import"] = import_check
    if import_result.returncode != 0:
        return {
            "status": "failed",
            "failed_check": "runtime_import",
            "return_code": import_result.returncode,
            "stdout": import_result.stdout,
            "stderr": import_result.stderr,
            "checks": checks,
        }

    return {
        "status": "completed",
        "return_code": 0,
        "stdout": import_result.stdout,
        "stderr": import_result.stderr,
        "checks": checks,
    }


def _parse_torch_preflight_stdout(stdout: str) -> dict:
    for line in reversed(stdout.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def _fresh_torch_cuda_preflight(
    candidate_gpu: str,
    repo_root: Path,
    *,
    python_executable: str = DEFAULT_REF_GS_PYTHON,
) -> dict:
    env = _subprocess_env(
        python_executable,
        cuda_visible_devices=str(candidate_gpu),
        conda_prefix=DEFAULT_REF_GS_CONDA_PREFIX,
    )
    snippet = "\n".join(
        [
            "import json",
            "import torch",
            "available = bool(torch.cuda.is_available())",
            "count = int(torch.cuda.device_count())",
            "name = torch.cuda.get_device_name(0) if available and count > 0 else ''",
            "print(json.dumps({",
            "    'torch_cuda_available': available,",
            "    'torch_device_count': count,",
            "    'device_name': name,",
            "}))",
        ]
    )
    result = subprocess.run(
        [python_executable, "-c", snippet],
        cwd=str(repo_root),
        env=env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    parsed = _parse_torch_preflight_stdout(result.stdout)
    torch_cuda_available = bool(parsed.get("torch_cuda_available", False))
    try:
        torch_device_count = int(parsed.get("torch_device_count", 0) or 0)
    except (TypeError, ValueError):
        torch_device_count = 0
    device_name = str(parsed.get("device_name", "") or "")
    decision = "pass" if result.returncode == 0 and torch_cuda_available and torch_device_count >= 1 else "fail"
    return {
        "candidate_gpu": str(candidate_gpu),
        "CUDA_VISIBLE_DEVICES": str(candidate_gpu),
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "torch_cuda_available": torch_cuda_available,
        "torch_device_count": torch_device_count,
        "device_name": device_name,
        "decision": decision,
    }


def _manual_cuda_preflight(args: argparse.Namespace, repo_root: Path, env: dict[str, str]) -> dict:
    selected_python = _python_executable(args)
    snippet = "\n".join(
        [
            "import os, torch, json",
            "print(json.dumps({",
            "  'CUDA_VISIBLE_DEVICES': os.environ.get('CUDA_VISIBLE_DEVICES'),",
            "  'torch_cuda_available': torch.cuda.is_available(),",
            "  'torch_device_count': torch.cuda.device_count(),",
            "  'device_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,",
            "}))",
        ]
    )
    result = subprocess.run(
        [selected_python, "-c", snippet],
        cwd=str(repo_root),
        env=env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    parsed = _parse_torch_preflight_stdout(result.stdout)
    cuda_visible_devices = str(parsed.get("CUDA_VISIBLE_DEVICES", "") or "")
    torch_cuda_available = bool(parsed.get("torch_cuda_available", False))
    try:
        torch_device_count = int(parsed.get("torch_device_count", 0) or 0)
    except (TypeError, ValueError):
        torch_device_count = 0
    device_name = parsed.get("device_name")
    decision = (
        "pass"
        if result.returncode == 0
        and torch_cuda_available
        and torch_device_count >= 1
        and cuda_visible_devices == str(args.physical_gpu)
        else "fail"
    )
    return {
        "status": "completed" if decision == "pass" else "failed",
        "decision": decision,
        "command": _quote([selected_python, "-c", snippet]),
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "CUDA_VISIBLE_DEVICES": cuda_visible_devices,
        "expected_CUDA_VISIBLE_DEVICES": str(args.physical_gpu),
        "torch_cuda_available": torch_cuda_available,
        "torch_device_count": torch_device_count,
        "device_name": device_name,
    }


def _split_values(values: list[str] | None, default: tuple[str, ...] | None = None) -> list[str]:
    if not values:
        return list(default or [])
    split: list[str] = []
    for value in values:
        split.extend(part for part in value.replace(",", " ").split() if part)
    return split


def _parse_gpu_probe_row(row: str) -> tuple[str, int, int] | None:
    parts = [part.strip() for part in row.split(",")]
    if len(parts) != 3:
        return None
    index = parts[0]
    try:
        memory_used_mb = int(parts[1].replace("MiB", "").strip())
        utilization = int(parts[2].replace("%", "").strip())
    except ValueError:
        return None
    return index, memory_used_mb, utilization


def _select_auto_device(
    candidate_devices: list[str],
    max_memory_used_mb: int,
    max_utilization: int,
    *,
    repo_root: Path | None = None,
    python_executable: str = DEFAULT_REF_GS_PYTHON,
) -> tuple[str, str, list[dict]]:
    if not candidate_devices:
        raise SystemExit("--devices auto requires --candidate_devices")
    probe_env = os.environ.copy()
    probe_env.pop("LD_LIBRARY_PATH", None)
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,memory.used,utilization.gpu", "--format=csv,noheader"],
        env=probe_env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"nvidia-smi unavailable for --devices auto: {result.stderr.strip() or result.stdout.strip()}")

    candidates = set(candidate_devices)
    rows = []
    for line in result.stdout.splitlines():
        parsed = _parse_gpu_probe_row(line)
        if parsed is None:
            continue
        rows.append(parsed)
    preflight_results: list[dict] = []
    for index, memory_used_mb, utilization in rows:
        if index in candidates and memory_used_mb <= max_memory_used_mb and utilization <= max_utilization:
            preflight = _fresh_torch_cuda_preflight(index, repo_root or _repo_root(), python_executable=python_executable)
            preflight["nvidia_smi_idle"] = True
            preflight["nvidia_smi_memory_used_mb"] = memory_used_mb
            preflight["nvidia_smi_utilization_gpu_percent"] = utilization
            preflight_results.append(preflight)
            if preflight["decision"] == "pass":
                return index, "auto_idle_cuda_preflight", preflight_results

    details = "; ".join(
        f"{index}: memory={memory_used_mb}MiB utilization={utilization}%"
        for index, memory_used_mb, utilization in rows
        if index in candidates
    )
    if preflight_results:
        raise SystemExit(
            "no idle candidate GPU passed fresh torch CUDA preflight "
            f"({details}); preflight={json.dumps(preflight_results, sort_keys=True)}"
        )
    raise SystemExit(f"no idle candidate GPU available for --devices auto ({details})")


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


def _has_source_marker(source_path: Path) -> bool:
    return any((source_path / marker).exists() for marker in SOURCE_MARKERS)


def _resolve_source_path(args: argparse.Namespace, dataset: str, scene: str, csv_source_path: str) -> str:
    if dataset == "glossy_synthetic":
        root = Path(args.glossy_synthetic_root)
        candidates = [root / scene, root / f"{scene}_blender"]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return str(candidates[0])
    if dataset == "shiny_blender_synthetic":
        return str(Path(DEFAULT_SHINY_BLENDER_SYNTHETIC_ROOT) / scene)
    return csv_source_path


def _validate_source_path(job: dict) -> dict:
    source_path = Path(job["source_path"])
    result = {
        "source_path": str(source_path),
        "status": "completed",
        "exists": source_path.exists(),
        "marker_found": False,
        "markers_checked": list(SOURCE_MARKERS),
        "reason": "",
    }
    if not source_path.exists():
        result["status"] = "failed"
        result["reason"] = "source directory does not exist"
        return result
    if not source_path.is_dir():
        result["status"] = "failed"
        result["reason"] = "source path is not a directory"
        return result
    result["marker_found"] = _has_source_marker(source_path)
    if not result["marker_found"]:
        result["status"] = "failed"
        result["reason"] = "no recognized scene marker found"
    return result


def _effective_iterations(args: argparse.Namespace) -> int:
    return args.smoke_iterations if args.smoke else args.iterations


def _python_executable(args: argparse.Namespace) -> str:
    return args.python_executable or DEFAULT_REF_GS_PYTHON


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
        _python_executable(args),
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
        _python_executable(args),
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
        _python_executable(args),
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
            source_path = _resolve_source_path(args, scene_info["dataset"], scene_info["scene"], scene_info["source_path"])
            metric_commands = {
                "reflection_consistency_train": _reflection_command(args, source_path, model_path, "train"),
                "reflection_consistency_test": _reflection_command(args, source_path, model_path, "test"),
                "render_quality_both_pbr_rgb": _render_quality_command(args, source_path, model_path, "pbr_rgb"),
                "render_quality_both_render_fallback": _render_quality_command(args, source_path, model_path, "render"),
            }
            jobs.append(
                {
                    "dataset": scene_info["dataset"],
                    "scene": scene_info["scene"],
                    "variant": variant,
                    "seed": 0,
                    "device": args.device,
                    "physical_gpu": args.physical_gpu,
                    "cuda_visible_devices": args.physical_gpu,
                    "cuda_device_arg": args.device,
                    "device_mapping": {
                        "physical_gpu": args.physical_gpu,
                        "external_CUDA_VISIBLE_DEVICES": args.physical_gpu,
                        "logical_cuda_device_arg": args.device,
                    },
                    "source_path": source_path,
                    "csv_source_path": scene_info["source_path"],
                    "model_path": str(model_path),
                    "iterations": iteration,
                    "selection_reason": scene_info["selection_reason"],
                    "evidence": scene_info["evidence"],
                    "variant_config": dict(VARIANT_CONFIGS[variant]),
                    "train_command": _train_command(args, source_path, model_path, variant),
                    "metric_commands": metric_commands,
                    "expected_artifacts": [str(path) for path in _expected_artifacts(model_path, iteration)],
                }
            )

    if args.max_jobs is not None:
        jobs = jobs[: args.max_jobs]
    return jobs


def _run(command: list[str], cwd: Path, dry_run: bool, env: dict[str, str] | None = None) -> tuple[str, int | None]:
    if dry_run:
        return "dry_run", None
    result = subprocess.run(command, cwd=str(cwd), env=env, check=False)
    return ("completed" if result.returncode == 0 else "failed"), result.returncode


def _tail_file(path: Path, limit: int = COMMAND_TAIL_BYTES) -> str:
    if not path.exists():
        return ""
    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - limit), os.SEEK_SET)
        return f.read().decode("utf-8", errors="replace")


def _run_captured(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    *,
    source_path: str,
) -> dict:
    with tempfile.NamedTemporaryFile(prefix="rc_qp_stdout_", delete=True) as stdout_file:
        with tempfile.NamedTemporaryFile(prefix="rc_qp_stderr_", delete=True) as stderr_file:
            result = subprocess.run(
                command,
                cwd=str(cwd),
                env=env,
                check=False,
                stdout=stdout_file,
                stderr=stderr_file,
            )
            stdout_path = Path(stdout_file.name)
            stderr_path = Path(stderr_file.name)
            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout_tail": _tail_file(stdout_path),
                "stderr_tail": _tail_file(stderr_path),
                "command": _quote(command),
                "source_path": source_path,
                "env_CUDA_VISIBLE_DEVICES": env.get("CUDA_VISIBLE_DEVICES", ""),
            }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_job_summary(
    model_path: Path,
    job: dict,
    status: str,
    args: argparse.Namespace,
    *,
    render_fallback_used: bool = False,
    subprocess_env: dict[str, str] | None = None,
    preflight_env: dict | None = None,
    manual_cuda_preflight: dict | None = None,
    failed_step: str | None = None,
    source_path_validation: dict | None = None,
    command_results: dict | None = None,
) -> None:
    selected_python = _python_executable(args)
    subprocess_env = subprocess_env or _subprocess_env(
        selected_python,
        cuda_visible_devices=getattr(args, "physical_gpu", None),
        conda_prefix=DEFAULT_REF_GS_CONDA_PREFIX,
    )
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runner": "scripts/run_rc_refgs_quality_preserving_pilot.py",
        "status": status,
        "failed_step": failed_step,
        "dry_run": not args.execute,
        "smoke": args.smoke,
        "skip_train": args.skip_train,
        "skip_metrics": args.skip_metrics,
        "render_fallback_used": render_fallback_used,
        "environment": _environment_summary(subprocess_env, selected_python),
        "preflight_env": preflight_env,
        "manual_cuda_preflight": manual_cuda_preflight,
        "source_path_validation": source_path_validation,
        "command_results": command_results or {},
        "environment_notes": {
            "cpu_side_orchestration": True,
            "cuda_device_arg": job["device"],
            "physical_gpu": job.get("physical_gpu", ""),
            "external_CUDA_VISIBLE_DEVICES": subprocess_env.get("CUDA_VISIBLE_DEVICES", ""),
            "mapping_policy": "external CUDA_VISIBLE_DEVICES=<physical_gpu>; train and metrics use --cuda_device 0",
            "conda_lib_prepended_to_ld_library_path": bool(subprocess_env.get("CONDA_PREFIX")),
            "no_cuda_visible_devices_set_by_runner": False,
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
        "physical_gpu": args.physical_gpu,
        "cuda_device_arg": args.device,
        "cuda_visible_devices": args.physical_gpu,
        "cuda_preflight_results": args.cuda_preflight_results,
        "trust_manual_cuda_preflight": bool(getattr(args, "trust_manual_cuda_preflight_enabled", False)),
        "manual_cuda_preflight": getattr(args, "manual_cuda_preflight_result", None),
        "device_mapping": {
            "physical_gpu": args.physical_gpu,
            "external_CUDA_VISIBLE_DEVICES": args.physical_gpu,
            "logical_cuda_device_arg": args.device,
        },
        "selected_device_reason": args.selected_device_reason,
        "python_executable": _python_executable(args),
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
    selected_python = _python_executable(args)
    subprocess_env = _subprocess_env(
        selected_python,
        cuda_visible_devices=args.physical_gpu,
        conda_prefix=DEFAULT_REF_GS_CONDA_PREFIX,
    )
    if _is_complete(model_path, iteration):
        return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": "skipped_complete"}

    model_path.mkdir(parents=True, exist_ok=True)
    if not args.execute:
        _write_job_summary(model_path, job, "dry_run", args, subprocess_env=subprocess_env)
        return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": "dry_run"}

    status = "completed"
    return_codes: dict[str, int | None] = {}
    source_path_validation = _validate_source_path(job)
    if source_path_validation["status"] != "completed":
        _write_job_summary(
            model_path,
            {**job, "return_codes": {"source_path_validation": None}},
            "failed",
            args,
            subprocess_env=subprocess_env,
            source_path_validation=source_path_validation,
            failed_step="source_path_validation",
        )
        return {
            **{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]},
            "status": "failed",
            "failed_step": "source_path_validation",
        }

    manual_cuda_preflight_result = None
    if getattr(args, "trust_manual_cuda_preflight_enabled", False):
        manual_cuda_preflight_result = getattr(args, "manual_cuda_preflight_result", None)
        if manual_cuda_preflight_result is None:
            manual_cuda_preflight_result = _manual_cuda_preflight(args, repo_root, subprocess_env)
            args.manual_cuda_preflight_result = manual_cuda_preflight_result
        if manual_cuda_preflight_result.get("decision") != "pass":
            _write_job_summary(
                model_path,
                {**job, "return_codes": {"manual_cuda_preflight": manual_cuda_preflight_result.get("return_code")}},
                "failed",
                args,
                subprocess_env=subprocess_env,
                source_path_validation=source_path_validation,
                preflight_env={
                    "status": "failed",
                    "failed_check": "manual_cuda_preflight",
                    "manual_cuda_preflight": manual_cuda_preflight_result,
                },
                manual_cuda_preflight=manual_cuda_preflight_result,
                failed_step="manual_cuda_preflight",
            )
            return {
                **{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]},
                "status": "failed",
                "failed_step": "manual_cuda_preflight",
            }
        cuda_preflight_result = {
            "candidate_gpu": str(args.physical_gpu),
            "CUDA_VISIBLE_DEVICES": str(args.physical_gpu),
            "decision": "skipped_trusted_manual_cuda_preflight",
            "manual_cuda_preflight": manual_cuda_preflight_result,
        }
    else:
        cuda_preflight_result = _fresh_torch_cuda_preflight(args.physical_gpu, repo_root, python_executable=DEFAULT_REF_GS_PYTHON)
    if cuda_preflight_result["decision"] == "fail":
        _write_job_summary(
            model_path,
            {**job, "return_codes": {"cuda_preflight": cuda_preflight_result.get("return_code")}},
            "failed",
            args,
            subprocess_env=subprocess_env,
            source_path_validation=source_path_validation,
            preflight_env={"status": "failed", "failed_check": "cuda_preflight", "cuda_preflight": cuda_preflight_result},
            manual_cuda_preflight=manual_cuda_preflight_result,
            failed_step="cuda_preflight",
        )
        return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": "failed", "failed_step": "cuda_preflight"}

    preflight_result = _preflight_env(repo_root, subprocess_env, selected_python)
    preflight_result = {**preflight_result, "cuda_preflight": cuda_preflight_result}
    if manual_cuda_preflight_result is not None:
        preflight_result["manual_cuda_preflight"] = manual_cuda_preflight_result
    if preflight_result["status"] != "completed":
        _write_job_summary(
            model_path,
            {**job, "return_codes": {"preflight_env": preflight_result.get("return_code")}},
            "failed",
            args,
            subprocess_env=subprocess_env,
            source_path_validation=source_path_validation,
            preflight_env=preflight_result,
            manual_cuda_preflight=manual_cuda_preflight_result,
            failed_step="preflight_env",
        )
        return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": "failed", "failed_step": "preflight_env"}

    if not args.skip_train:
        train_result = _run_captured(job["train_command"], repo_root, subprocess_env, source_path=job["source_path"])
        train_result.setdefault("source_path", job["source_path"])
        train_result.setdefault("env_CUDA_VISIBLE_DEVICES", subprocess_env.get("CUDA_VISIBLE_DEVICES", ""))
        train_result.setdefault("command", _quote(job["train_command"]))
        train_status = train_result["status"]
        code = train_result["return_code"]
        return_codes["train"] = code
        if train_status == "failed":
            _write_job_summary(
                model_path,
                {**job, "return_codes": return_codes},
                "failed",
                args,
                subprocess_env=subprocess_env,
                source_path_validation=source_path_validation,
                preflight_env=preflight_result,
                manual_cuda_preflight=manual_cuda_preflight_result,
                command_results={"train": train_result},
                failed_step="train",
            )
            return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": "failed", "failed_step": "train"}

    render_fallback_used = False
    if not args.skip_metrics:
        for key in ["reflection_consistency_train", "reflection_consistency_test"]:
            metric_status, code = _run(job["metric_commands"][key], repo_root, False, subprocess_env)
            return_codes[key] = code
            if metric_status == "failed":
                status = "failed"
                _write_job_summary(
                    model_path,
                    {**job, "return_codes": return_codes},
                    status,
                    args,
                    subprocess_env=subprocess_env,
                    source_path_validation=source_path_validation,
                    preflight_env=preflight_result,
                    manual_cuda_preflight=manual_cuda_preflight_result,
                    failed_step=key,
                )
                return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": status, "failed_step": key}

        metric_status, code = _run(job["metric_commands"]["render_quality_both_pbr_rgb"], repo_root, False, subprocess_env)
        return_codes["render_quality_both_pbr_rgb"] = code
        if metric_status == "failed":
            render_fallback_used = True
            metric_status, code = _run(
                job["metric_commands"]["render_quality_both_render_fallback"],
                repo_root,
                False,
                subprocess_env,
            )
            return_codes["render_quality_both_render_fallback"] = code
            if metric_status == "failed":
                status = "failed"
                _write_job_summary(
                    model_path,
                    {**job, "return_codes": return_codes},
                    status,
                    args,
                    render_fallback_used=True,
                    subprocess_env=subprocess_env,
                    source_path_validation=source_path_validation,
                    preflight_env=preflight_result,
                    manual_cuda_preflight=manual_cuda_preflight_result,
                    failed_step="render_quality_both",
                )
                return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": status, "failed_step": "render_quality_both"}

    if not all(path.exists() for path in _expected_artifacts_before_summary(model_path, iteration)):
        status = "partial"
    _write_job_summary(
        model_path,
        {**job, "return_codes": return_codes},
        status,
        args,
        render_fallback_used=render_fallback_used,
        subprocess_env=subprocess_env,
        source_path_validation=source_path_validation,
        preflight_env=preflight_result,
        manual_cuda_preflight=manual_cuda_preflight_result,
    )
    return {**{k: job[k] for k in ["dataset", "scene", "variant", "model_path"]}, "status": status}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare or execute bounded RC-RefGS quality-preserving pilot jobs.")
    parser.add_argument("--target_csv", default=str(DEFAULT_TARGET_CSV))
    parser.add_argument("--output_root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--devices", required=True, help="Comma/space physical GPU list; only one selected device is used.")
    parser.add_argument("--candidate_devices", default="", help="Candidate GPU list used only when --devices auto.")
    parser.add_argument("--gpu_max_memory_used_mb", type=int, default=1000)
    parser.add_argument("--gpu_max_utilization", type=int, default=10)
    parser.add_argument("--python_executable", default=DEFAULT_REF_GS_PYTHON)
    parser.add_argument("--glossy_synthetic_root", default=DEFAULT_GLOSSY_SYNTHETIC_ROOT)
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
    parser.add_argument("--trust_manual_cuda_preflight", default="")
    parser.add_argument("--max_pairs", type=int, default=10)
    parser.add_argument("--ref_consistency_max_angle", type=float, default=20.0)
    parser.add_argument("--metric_gamma", type=float, default=2.0)
    args = parser.parse_args(argv)

    devices = _split_values([args.devices])
    if not devices:
        raise SystemExit("--devices is required")
    if args.trust_manual_cuda_preflight not in {"", "YES"}:
        raise SystemExit("--trust_manual_cuda_preflight must be YES when provided")
    args.trust_manual_cuda_preflight_enabled = args.trust_manual_cuda_preflight == "YES"
    if args.trust_manual_cuda_preflight_enabled:
        if devices[0] == "auto":
            raise SystemExit("--trust_manual_cuda_preflight requires explicit --devices, not auto")
        if len(devices) != 1:
            raise SystemExit("--trust_manual_cuda_preflight requires exactly one explicit --devices value")
        if not args.execute or args.confirm_execute != "YES":
            raise SystemExit("--trust_manual_cuda_preflight requires --execute --confirm_execute YES")
        parent_cuda_visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
        if not parent_cuda_visible_devices:
            raise SystemExit("--trust_manual_cuda_preflight requires parent CUDA_VISIBLE_DEVICES")
        if parent_cuda_visible_devices != devices[0]:
            raise SystemExit("parent CUDA_VISIBLE_DEVICES must match explicit --devices for --trust_manual_cuda_preflight")
    args.manual_cuda_preflight_result = None
    if devices[0] == "auto":
        args.physical_gpu, args.selected_device_reason, args.cuda_preflight_results = _select_auto_device(
            _split_values([args.candidate_devices]),
            args.gpu_max_memory_used_mb,
            args.gpu_max_utilization,
            repo_root=_repo_root(),
            python_executable=DEFAULT_REF_GS_PYTHON,
        )
    else:
        args.physical_gpu = devices[0]
        args.selected_device_reason = "explicit"
        args.cuda_preflight_results = []
    args.device = LOGICAL_CUDA_DEVICE
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
    if getattr(args, "trust_manual_cuda_preflight_enabled", False) and args.execute:
        selected_python = _python_executable(args)
        subprocess_env = _subprocess_env(
            selected_python,
            cuda_visible_devices=args.physical_gpu,
            conda_prefix=DEFAULT_REF_GS_CONDA_PREFIX,
        )
        args.manual_cuda_preflight_result = _manual_cuda_preflight(args, repo_root, subprocess_env)
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
