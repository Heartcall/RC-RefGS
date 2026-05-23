#!/usr/bin/env python
"""Post-run smoke checks for extract_mesh.py outputs."""

import argparse
import json
import os
from pathlib import Path


def _load_summary(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_report(path, report):
    if path is None:
        return
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)


def build_postrun_smoke_report(summary, mesh_path=None):
    resolved_mesh = mesh_path or summary.get("output_mesh")
    mesh_exists = bool(resolved_mesh) and os.path.exists(resolved_mesh)
    mesh_size = os.path.getsize(resolved_mesh) if mesh_exists else 0
    missing_inputs = summary.get("missing_inputs") or []
    summary_dry_run = bool(summary.get("dry_run"))

    if summary_dry_run:
        status = "summary_is_dry_run"
    elif missing_inputs:
        status = "missing_inputs"
    elif not mesh_exists:
        status = "missing_mesh"
    elif mesh_size <= 0:
        status = "empty_mesh"
    else:
        status = "ready"

    return {
        "mode": "extract_mesh_postrun_smoke_check",
        "ready": status == "ready",
        "status": status,
        "metrics_computed": False,
        "summary_mode": summary.get("mode"),
        "summary_dry_run": summary_dry_run,
        "model_path": summary.get("model_path"),
        "iteration": summary.get("iteration"),
        "mesh_path": resolved_mesh,
        "mesh_exists": mesh_exists,
        "mesh_size_bytes": mesh_size,
        "missing_inputs": missing_inputs,
        "claim_boundary": "Post-run smoke check only; no geometry metric values are computed.",
    }


def main():
    parser = argparse.ArgumentParser(description="Check extract_mesh.py post-run smoke outputs.")
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--mesh_path", default=None)
    parser.add_argument("--output_json", default=None)
    args = parser.parse_args()

    summary = _load_summary(args.summary_json)
    report = build_postrun_smoke_report(summary, mesh_path=args.mesh_path)
    _write_report(args.output_json, report)
    print(json.dumps(report, indent=2))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
