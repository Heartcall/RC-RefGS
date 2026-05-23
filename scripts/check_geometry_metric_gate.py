import argparse
import json
from pathlib import Path


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_geometry_metric_gate(postrun_report, geometry_plan):
    postrun_ready = bool(postrun_report.get("ready", False))
    postrun_status = postrun_report.get("status", "unknown")
    missing_mesh_count = int(geometry_plan.get("missing_mesh_count", 0) or 0)

    blockers = []
    if not postrun_ready:
        blockers.append("postrun_status:{}".format(postrun_status))
    if missing_mesh_count:
        blockers.append("missing_predicted_meshes:{}".format(missing_mesh_count))

    metrics_allowed = postrun_ready and missing_mesh_count == 0
    return {
        "mode": "geometry_metric_gate_dryrun",
        "metrics_allowed": metrics_allowed,
        "status": "ready_for_metric_computation" if metrics_allowed else "blocked",
        "metrics_computed": False,
        "postrun_ready": postrun_ready,
        "postrun_status": postrun_status,
        "geometry_ready_count": int(geometry_plan.get("ready_count", 0) or 0),
        "missing_predicted_mesh_count": missing_mesh_count,
        "scene_count": int(geometry_plan.get("scene_count", 0) or 0),
        "reference_obj_count": int(geometry_plan.get("reference_obj_count", 0) or 0),
        "blockers": blockers,
        "claim_boundary": "Dry-run gate only; no geometry metric values are computed.",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Dry-run gate for deciding whether geometry metric computation is allowed."
    )
    parser.add_argument("--postrun_json", required=True)
    parser.add_argument("--geometry_plan_json", required=True)
    parser.add_argument("--output_json", required=True)
    args = parser.parse_args()

    report = build_geometry_metric_gate(
        _load_json(args.postrun_json),
        _load_json(args.geometry_plan_json),
    )
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["metrics_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
