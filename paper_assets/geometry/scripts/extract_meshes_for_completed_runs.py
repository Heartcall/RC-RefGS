#!/usr/bin/env python3
"""Create guarded mesh-extraction command plans for completed RC-RefGS runs.

Default mode is dry-run. The script does not train. It only inspects completed
rows and writes commands that call the repository's extract_mesh.py entrypoint.
"""

from __future__ import annotations

import argparse
import csv
import shlex
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
MAIN_FULL = REPO_ROOT / "paper_assets/data/main_full_metrics_by_dataset_wide.csv"
ABLATION_FULL = REPO_ROOT / "paper_assets/data/ablation_full_metrics_by_dataset_wide.csv"
MAIN_ROOT = Path("/tmp/rc_refgs_full_dataset_base_rc_i31000_20260527")
ABLATION_ROOT = Path("/tmp/rc_refgs_full_dataset_ablations_i31000_20260528")
OUT_DIR = REPO_ROOT / "paper_assets/geometry/mesh_extraction_plans"
ITERATION = 31000


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


def _command(model_path: Path, output_mesh: Path, split: str, cuda_device: str | None, dry_run: bool) -> str:
    argv = [
        "python",
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan mesh extraction for completed RC-RefGS rows.")
    parser.add_argument("--execute", action="store_true", help="Actually execute extraction commands. Default is dry-run planning only.")
    parser.add_argument("--limit_scenes", nargs="*", default=None)
    parser.add_argument("--skip_existing", action="store_true")
    parser.add_argument("--split", default="train", choices=["train", "test", "both"])
    parser.add_argument("--cuda_device", default=None)
    args = parser.parse_args()

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
        command = _command(model_path, output_mesh, args.split, args.cuda_device, dry_run=not args.execute)
        rows.append(
            {
                "group": group,
                "dataset": dataset,
                "scene": scene,
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
