#!/usr/bin/env python
"""Smoke-testable mesh extraction entrypoint for RC-RefGS outputs."""

from __future__ import annotations

import json
import os
import shlex
import sys
from argparse import ArgumentParser
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from arguments import ModelParams, PipelineParams, get_combined_args


def _expected_point_cloud_dir(model_path, iteration):
    return Path(model_path) / "point_cloud" / f"iteration_{iteration}"


def _default_output_mesh(model_path, iteration):
    return Path(model_path) / f"mesh_iter{iteration}.ply"


def _validate_inputs(model_path, iteration):
    point_cloud_dir = _expected_point_cloud_dir(model_path, iteration)
    expected_inputs = [point_cloud_dir / "point_cloud.ply"]
    missing_inputs = [str(path) for path in expected_inputs if not path.exists()]
    return [str(path) for path in expected_inputs], missing_inputs


def _check_imports():
    from utils.mesh_utils import GaussianExtractor, post_process_mesh

    return {
        "GaussianExtractor": GaussianExtractor.__name__,
        "post_process_mesh": post_process_mesh.__name__,
    }


def _recommended_ld_library_path_prefix():
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        return str(Path(conda_prefix) / "lib")
    return "$CONDA_PREFIX/lib"


def _check_open3d():
    info = {
        "checked": True,
        "ok": False,
        "version": None,
        "error_type": None,
        "error": None,
        "recommended_ld_library_path_prefix": _recommended_ld_library_path_prefix(),
    }
    try:
        import open3d as o3d
    except Exception as exc:  # Import can fail on shared-library resolution.
        info["error_type"] = exc.__class__.__name__
        info["error"] = str(exc)
        return info

    info["ok"] = True
    info["version"] = getattr(o3d, "__version__", None)
    return info


def _write_summary(summary_json, summary):
    if summary_json is None:
        return
    summary_path = Path(summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def _runtime_summary_path(summary_json):
    if summary_json is None:
        return None
    summary_path = Path(summary_json)
    suffix = summary_path.suffix or ".json"
    return str(summary_path.with_name(summary_path.stem + "-runtime" + suffix))


def _build_runtime_command_plan(args):
    argv = [
        sys.executable,
        "extract_mesh.py",
        "--model_path",
        str(args.model_path),
        "--iteration",
        str(args.iteration),
        "--output_mesh",
        str(args.output_mesh),
        "--mesh_mode",
        args.mesh_mode,
        "--split",
        args.split,
        "--voxel_size",
        str(args.voxel_size),
        "--sdf_trunc",
        str(args.sdf_trunc),
        "--depth_trunc",
        str(args.depth_trunc),
        "--conf_threshold",
        str(args.conf_threshold),
        "--mesh_resolution",
        str(args.mesh_resolution),
        "--cluster_to_keep",
        str(args.cluster_to_keep),
    ]
    runtime_summary = _runtime_summary_path(args.summary_json)
    if runtime_summary is not None:
        argv.extend(["--summary_json", runtime_summary])
    if args.cuda_device is not None:
        argv.extend(["--cuda_device", str(args.cuda_device)])
    if args.post_process:
        argv.append("--post_process")
    if args.no_mask_background:
        argv.append("--no_mask_background")
    if args.quiet:
        argv.append("--quiet")

    env = {
        "LD_LIBRARY_PATH": "{}:$LD_LIBRARY_PATH".format(_recommended_ld_library_path_prefix())
    }
    return {
        "requires_explicit_runtime_allocation": True,
        "environment": env,
        "argv": argv,
        "command_line": " ".join(shlex.quote(part) for part in argv),
        "output_mesh": str(args.output_mesh),
        "runtime_summary_json": runtime_summary,
        "claim_boundary": "Command plan only; extraction is not executed during dry-run.",
    }


def _cuda_device_index(cuda_device):
    if cuda_device is None:
        return 0
    cuda_device = str(cuda_device).strip()
    if not cuda_device or cuda_device.lower() in {"auto", "none"}:
        return 0
    return int(cuda_device.split(",", 1)[0])


def _camera_list(scene, split):
    cameras = []
    if split in {"train", "both"}:
        cameras.extend(scene.getTrainCameras())
    if split in {"test", "both"}:
        cameras.extend(scene.getTestCameras())
    return cameras


def _run_extraction(args, lp, pp):
    import torch
    import open3d as o3d
    from gaussian_renderer import render
    from scene import Scene, GaussianModel
    from utils.general_utils import safe_state
    from utils.mesh_utils import GaussianExtractor, post_process_mesh

    safe_state(args.quiet, cuda_device=_cuda_device_index(args.cuda_device))

    dataset = lp.extract(args)
    pipe = pp.extract(args)
    gaussians = GaussianModel(dataset.sh_degree, dataset)
    scene = Scene(dataset, gaussians, load_iteration=args.iteration, shuffle=False, resolution_scales=[1.0])
    bg_color = [1.0, 1.0, 1.0] if dataset.white_background else [0.0, 0.0, 0.0]

    extractor = GaussianExtractor(gaussians, render, pipe, bg_color=bg_color)
    cameras = _camera_list(scene, args.split)
    if not cameras:
        raise ValueError(f"No cameras available for split '{args.split}'")

    extractor.reconstruction(cameras)
    if args.mesh_mode == "bounded":
        mesh = extractor.extract_mesh_bounded(
            voxel_size=args.voxel_size,
            sdf_trunc=args.sdf_trunc,
            depth_trunc=args.depth_trunc,
            mask_backgrond=not args.no_mask_background,
            conf_threshold=args.conf_threshold,
        )
    else:
        mesh = extractor.extract_mesh_unbounded(resolution=args.mesh_resolution)

    if args.post_process:
        mesh = post_process_mesh(mesh, cluster_to_keep=args.cluster_to_keep)

    output_mesh = Path(args.output_mesh)
    output_mesh.parent.mkdir(parents=True, exist_ok=True)
    o3d.io.write_triangle_mesh(str(output_mesh), mesh)
    torch.cuda.empty_cache()
    return str(output_mesh)


def _build_summary(
    args,
    *,
    dry_run,
    imports_checked,
    import_info,
    open3d_info,
    runtime_command_plan,
    expected_inputs,
    missing_inputs,
):
    return {
        "mode": "mesh_extraction",
        "dry_run": bool(dry_run),
        "imports_checked": bool(imports_checked),
        "import_info": import_info,
        "open3d_info": open3d_info,
        "runtime_command_plan": runtime_command_plan,
        "model_path": str(args.model_path),
        "iteration": int(args.iteration),
        "output_mesh": str(args.output_mesh),
        "mesh_mode": args.mesh_mode,
        "split": args.split,
        "expected_inputs": expected_inputs,
        "missing_inputs": missing_inputs,
    }


def _parse_args(parser, argv):
    cmdline_args = parser.parse_args(argv)
    cfg_args = Path(cmdline_args.model_path) / "cfg_args"
    if cfg_args.exists():
        combined_args = get_combined_args(parser)
        for key, value in vars(cmdline_args).items():
            if not hasattr(combined_args, key):
                setattr(combined_args, key, value)
        return combined_args
    return cmdline_args


def main(argv=None):
    parser = ArgumentParser(description="Extract a mesh from a trained RC-RefGS model.")
    lp = ModelParams(parser, sentinel=True)
    pp = PipelineParams(parser)
    parser.add_argument("--iteration", type=int, default=-1)
    parser.add_argument("--output_mesh", type=str, default=None)
    parser.add_argument("--summary_json", type=str, default=None)
    parser.add_argument("--mesh_mode", choices=["bounded", "unbounded"], default="bounded")
    parser.add_argument("--split", choices=["train", "test", "both"], default="train")
    parser.add_argument("--voxel_size", type=float, default=0.004)
    parser.add_argument("--sdf_trunc", type=float, default=0.02)
    parser.add_argument("--depth_trunc", type=float, default=3.0)
    parser.add_argument("--conf_threshold", type=float, default=0.0)
    parser.add_argument("--mesh_resolution", type=int, default=1024)
    parser.add_argument("--cluster_to_keep", type=int, default=1000)
    parser.add_argument("--post_process", action="store_true")
    parser.add_argument("--no_mask_background", action="store_true")
    parser.add_argument("--cuda_device", type=str, default=None)
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--check_imports", action="store_true")
    parser.add_argument("--check_open3d", action="store_true")
    parser.add_argument("--emit_runtime_command", action="store_true")
    parser.add_argument("--quiet", action="store_true")

    args = _parse_args(parser, argv)
    if args.iteration == -1:
        from utils.system_utils import searchForMaxIteration

        args.iteration = searchForMaxIteration(Path(args.model_path) / "point_cloud")
    if args.output_mesh is None:
        args.output_mesh = str(_default_output_mesh(args.model_path, args.iteration))

    expected_inputs, missing_inputs = _validate_inputs(args.model_path, args.iteration)
    import_info = None
    open3d_info = None
    if args.check_open3d:
        open3d_info = _check_open3d()
    if args.check_imports:
        import_info = _check_imports()
    runtime_command_plan = None
    if args.emit_runtime_command:
        runtime_command_plan = _build_runtime_command_plan(args)

    summary = _build_summary(
        args,
        dry_run=args.dry_run,
        imports_checked=args.check_imports,
        import_info=import_info,
        open3d_info=open3d_info,
        runtime_command_plan=runtime_command_plan,
        expected_inputs=expected_inputs,
        missing_inputs=missing_inputs,
    )

    if args.dry_run:
        _write_summary(args.summary_json, summary)
        print(json.dumps(summary, indent=2))
        return 0

    if missing_inputs:
        summary["error"] = "missing required extraction inputs"
        _write_summary(args.summary_json, summary)
        print(json.dumps(summary, indent=2))
        return 2

    output_mesh = _run_extraction(args, lp, pp)
    summary["output_mesh"] = output_mesh
    summary["dry_run"] = False
    _write_summary(args.summary_json, summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
