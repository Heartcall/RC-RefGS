#!/usr/bin/env python3
"""Create guarded mesh-extraction command plans for completed RC-RefGS runs.

Default mode is dry-run. The script does not train. It only inspects completed
rows and writes commands that call the repository's extract_mesh.py entrypoint.
"""

from __future__ import annotations

import argparse
import csv
import os
import shlex
import subprocess
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
MAIN_FULL = REPO_ROOT / "paper_assets/data/main_full_metrics_by_dataset_wide.csv"
ABLATION_FULL = REPO_ROOT / "paper_assets/data/ablation_full_metrics_by_dataset_wide.csv"
MAIN_ROOT = Path("/tmp/rc_refgs_full_dataset_base_rc_i31000_20260527")
ABLATION_ROOT = Path("/tmp/rc_refgs_full_dataset_ablations_i31000_20260528")
OUT_DIR = REPO_ROOT / "paper_assets/geometry/mesh_extraction_plans"
ITERATION = 31000
DEFAULT_DEPTH_TRUNC = 10.0
RERUN_ROOT = Path("/data/liuly/experiments/rc_refgs_geometry_rerun")
RERUN_PREDICTION_ROOT = RERUN_ROOT / "pred_meshes"
RERUN_MANIFEST_OUTPUT = (
    REPO_ROOT
    / "paper_assets/geometry_gt/rerun_20260611/data/prediction_mesh_manifest.csv"
)
REF_GS_PYTHON = Path("/home/liuly/anaconda3/envs/ref_gs/bin/python")


def _nested_model_dir(seed_dir: Path) -> Path:
    pc = seed_dir / "point_cloud" / f"iteration_{ITERATION}" / "point_cloud.ply"
    if pc.exists():
        return seed_dir
    if seed_dir.exists():
        for child in seed_dir.iterdir():
            if child.is_dir() and (child / "point_cloud" / f"iteration_{ITERATION}" / "point_cloud.ply").exists():
                return child
    return seed_dir


def _expected_runs():
    main = pd.read_csv(MAIN_FULL)[["dataset", "scene"]].drop_duplicates()
    for row in main.itertuples(index=False):
        for variant in ["base", "rc"]:
            yield "main", row.dataset, row.scene, variant, _nested_model_dir(MAIN_ROOT / row.dataset / row.scene / variant / "seed_0")
    abl = pd.read_csv(ABLATION_FULL)[["dataset", "scene", "variant"]].drop_duplicates()
    for row in abl.itertuples(index=False):
        root = MAIN_ROOT if row.variant in {"base", "rc"} else ABLATION_ROOT
        yield "ablation", row.dataset, row.scene, row.variant, _nested_model_dir(root / row.dataset / row.scene / row.variant / "seed_0")


def _command(
    model_path: Path,
    output_mesh: Path,
    split: str,
    cuda_device: str | None,
    dry_run: bool,
    python_executable: str = "python",
    depth_trunc: float = DEFAULT_DEPTH_TRUNC,
) -> str:
    argv = [
        str(python_executable),
        "extract_mesh.py",
        "--model_path",
        str(model_path),
        "--iteration",
        str(ITERATION),
        "--output_mesh",
        str(output_mesh),
        "--split",
        split,
        "--mesh_mode",
        "bounded",
        "--depth_trunc",
        str(depth_trunc),
        "--summary_json",
        str(output_mesh.with_suffix(".summary.json")),
        "--check_imports",
        "--check_open3d",
    ]
    if cuda_device is not None:
        argv += ["--cuda_device", str(cuda_device)]
    if dry_run:
        argv += ["--dry_run", "--emit_runtime_command"]
    return " ".join(shlex.quote(part) for part in argv)


def _is_below(path: Path, root: Path) -> bool:
    path = path.resolve(strict=False)
    root = root.resolve(strict=False)
    return path == root or root in path.parents


def _manifest_point_cloud(row: dict, model_path: Path, iteration: int) -> Path:
    explicit = row.get("point_cloud_path", "").strip()
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.append(model_path / "point_cloud" / f"iteration_{iteration}" / "point_cloud.ply")
    if model_path.exists():
        candidates.extend(
            sorted(model_path.glob(f"*/point_cloud/iteration_{iteration}/point_cloud.ply"))
        )
    return next((path for path in candidates if path.is_file()), candidates[0])


def _manifest_rows(
    manifest: Path,
    prediction_root: Path,
    split: str,
    cuda_device: str | None,
    python_executable: Path,
    depth_trunc: float,
):
    with manifest.open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    rows = []
    for source in source_rows:
        dataset = source.get("dataset", "").strip()
        scene = source.get("scene", "").strip()
        variant = source.get("variant", "").strip()
        seed = int(source.get("seed", "0") or 0)
        iteration = int(source.get("iteration", str(ITERATION)) or ITERATION)
        model_path = Path(source.get("model_path", ""))
        point_cloud = _manifest_point_cloud(source, model_path, iteration)
        output_mesh = (
            prediction_root
            / dataset
            / scene
            / variant
            / f"seed_{seed}"
            / f"mesh_iter{iteration}.ply"
        )
        summary_path = output_mesh.with_suffix(".summary.json")
        extraction_log = model_path / "logs" / f"extract_mesh_iter{iteration}.log"
        reason = ""
        if "Ref-GS-I2" in str(model_path):
            status = "excluded"
            reason = "unrelated Ref-GS-I2 artifact is prohibited"
        elif source.get("status", "").strip().lower() not in {"completed", "skipped_complete"}:
            status = "excluded"
            reason = "run manifest row is not completed: {}".format(
                source.get("status", "").strip() or "missing status"
            )
        elif not point_cloud.is_file():
            checkpoint = Path(source.get("checkpoint_path", "")) if source.get("checkpoint_path") else None
            status = "excluded"
            if checkpoint is not None and checkpoint.is_file():
                reason = "checkpoint present but final point_cloud.ply is missing"
            else:
                reason = "missing final point_cloud.ply"
        elif not (model_path / "cfg_args").is_file():
            status = "excluded"
            reason = "missing cfg_args"
        elif output_mesh.is_file() and output_mesh.stat().st_size > 0:
            status = "completed"
            reason = "existing durable mesh"
        else:
            status = "planned"
        command = _command(
            model_path,
            output_mesh,
            split,
            cuda_device,
            dry_run=True,
            python_executable=str(python_executable),
            depth_trunc=depth_trunc,
        )
        rows.append(
            {
                "dataset": dataset,
                "scene": scene,
                "split": split,
                "variant": variant,
                "seed": seed,
                "iteration": iteration,
                "model_path": str(model_path),
                "point_cloud_path": str(point_cloud),
                "prediction_path": str(output_mesh),
                "summary_path": str(summary_path),
                "extraction_log_path": str(extraction_log),
                "cuda_device": cuda_device or "",
                "depth_trunc": depth_trunc,
                "status": status,
                "reason": reason,
                "command": command,
            }
        )
    return rows


def _write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else [
        "dataset", "scene", "split", "variant", "seed", "iteration",
        "model_path", "point_cloud_path", "prediction_path", "summary_path",
        "extraction_log_path", "cuda_device", "status", "reason", "command",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def _validate_prediction_root(prediction_root: Path) -> Path:
    prediction_root = Path(prediction_root)

    if not prediction_root.is_absolute():
        raise SystemExit("Execution refused: --prediction-root must be an absolute path")

    prediction_root = prediction_root.resolve(strict=False)

    forbidden_roots = [
        Path("/tmp").resolve(strict=False),
        Path("/var/tmp").resolve(strict=False),
        Path("/dev/shm").resolve(strict=False),
    ]

    for root in forbidden_roots:
        if prediction_root == root or root in prediction_root.parents:
            raise SystemExit(
                f"Execution refused: prediction root must not be under temporary root {root}"
            )

    return prediction_root

def _execute_manifest_rows(rows: list[dict], prediction_root: Path, python_executable: Path) -> None:
    prediction_root = _validate_prediction_root(prediction_root)

    env = os.environ.copy()
    ref_lib = "/home/liuly/anaconda3/envs/ref_gs/lib"
    env["LD_LIBRARY_PATH"] = ref_lib + (
        ":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else ""
    )
    mpl_config_dir = REPO_ROOT / "paper_assets/geometry/.mplconfig"
    mpl_config_dir.mkdir(parents=True, exist_ok=True)
    env["MPLCONFIGDIR"] = str(mpl_config_dir)
    for row in rows:
        if row["status"] != "planned":
            continue
        output_mesh = Path(row["prediction_path"])
        output_mesh.parent.mkdir(parents=True, exist_ok=True)
        argv = [
            str(python_executable),
            "extract_mesh.py",
            "--model_path", row["model_path"],
            "--iteration", str(row["iteration"]),
            "--output_mesh", row["prediction_path"],
            "--split", row["split"],
            "--mesh_mode", "bounded",
            "--depth_trunc", str(row["depth_trunc"]),
            "--summary_json", row["summary_path"],
            "--check_imports",
            "--check_open3d",
        ]
        if row.get("cuda_device"):
            argv.extend(["--cuda_device", row["cuda_device"]])
        extraction_log = Path(row["extraction_log_path"])
        extraction_log.parent.mkdir(parents=True, exist_ok=True)
        with extraction_log.open("a", encoding="utf-8") as handle:
            try:
                subprocess.run(
                    argv,
                    cwd=str(REPO_ROOT),
                    env=env,
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
            except subprocess.CalledProcessError as exc:
                row["status"] = f"failed_exit_{exc.returncode}"
                row["reason"] = (
                    f"extract_mesh.py exited with exit code {exc.returncode}; "
                    f"see log {extraction_log}"
                )
                continue
        if output_mesh.is_file() and output_mesh.stat().st_size > 0:
            row["status"] = "completed"
            row["reason"] = ""
        else:
            row["status"] = "failed_no_mesh"
            row["reason"] = "mesh extraction completed without a non-empty mesh"


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan mesh extraction for completed RC-RefGS rows.")
    parser.add_argument("--execute", action="store_true", help="Actually execute extraction commands. Default is dry-run planning only.")
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--prediction-root", type=Path, default=RERUN_PREDICTION_ROOT)
    parser.add_argument("--manifest-output", type=Path, default=RERUN_MANIFEST_OUTPUT)
    parser.add_argument("--python-executable", type=Path, default=REF_GS_PYTHON)
    parser.add_argument("--limit_scenes", nargs="*", default=None)
    parser.add_argument("--skip_existing", action="store_true")
    parser.add_argument("--split", default="train", choices=["train", "test", "both"])
    parser.add_argument("--cuda_device", default=None)
    parser.add_argument("--depth_trunc", type=float, default=DEFAULT_DEPTH_TRUNC)
    args = parser.parse_args()

    if args.manifest is not None:
        rows = _manifest_rows(
            args.manifest,
            args.prediction_root,
            args.split,
            args.cuda_device,
            args.python_executable,
            args.depth_trunc,
        )
        try:
            if args.execute:
                _execute_manifest_rows(rows, args.prediction_root, args.python_executable)
        finally:
            _write_rows(args.manifest_output, rows)
        counts = {}
        for row in rows:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        print(
            f"Wrote {args.manifest_output} rows={len(rows)} "
            f"status={counts}"
        )
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for group, dataset, scene, variant, model_path in _expected_runs():
        if args.limit_scenes and scene not in args.limit_scenes:
            continue
        point_cloud = model_path / "point_cloud" / f"iteration_{ITERATION}" / "point_cloud.ply"
        output_mesh = model_path / f"mesh_iter{ITERATION}.ply"
        if args.skip_existing and output_mesh.exists():
            status = "skip_existing"
        elif not point_cloud.exists():
            status = "missing_point_cloud"
        else:
            status = "planned" if not args.execute else "not_executed_by_guard"
        command = _command(
            model_path,
            output_mesh,
            args.split,
            args.cuda_device,
            dry_run=not args.execute,
            depth_trunc=args.depth_trunc,
        )
        rows.append(
            {
                "group": group,
                "dataset": dataset,
                "scene": scene,
                "extraction_split": args.split,
                "variant": variant,
                "model_path": str(model_path),
                "point_cloud": str(point_cloud),
                "output_mesh": str(output_mesh),
                "status": status,
                "command": command,
            }
        )
    out_csv = OUT_DIR / "extract_meshes_for_completed_runs_plan.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["status"])
        writer.writeheader()
        writer.writerows(rows)
    out_md = OUT_DIR / "extract_meshes_for_completed_runs_plan.md"
    lines = [
        "# Mesh Extraction Command Plan",
        "",
        f"Rows planned: {len(rows)}.",
        "",
        "Default mode is dry-run. No extraction or training is executed by this planner.",
        "",
        f"CSV: `{out_csv}`",
        "",
    ]
    for row in rows[:20]:
        lines.append(f"- `{row['dataset']}/{row['scene']}/{row['variant']}`: {row['status']}")
    if len(rows) > 20:
        lines.append(f"- ... {len(rows) - 20} additional rows in CSV.")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
