import argparse
import json
from pathlib import Path


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _unique(items):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def summarize_pipeline(postrun_report, gate_report, eval_report):
    postrun_ready = bool(postrun_report.get("ready", False))
    gate_allowed = bool(gate_report.get("metrics_allowed", False))
    eval_computed = bool(eval_report.get("metrics_computed", False))

    blockers = _unique(
        list(gate_report.get("blockers", []))
        + list(eval_report.get("blockers", []))
    )

    if not postrun_ready:
        status = "blocked_pending_extraction"
        next_action = "run_non_dryrun_extraction_smoke_with_explicit_compute"
    elif not gate_allowed:
        status = "blocked_pending_metric_gate"
        next_action = "rerun_geometry_metric_gate_after_fixing_blockers"
    elif not eval_computed:
        status = "ready_for_geometry_eval"
        next_action = "run_guarded_smvp3d_geometry_eval"
    else:
        status = "geometry_eval_computed"
        next_action = "review_diagnostic_only_metrics_without_claim_upgrade"

    return {
        "mode": "smvp3d_geometry_pipeline_status",
        "status": status,
        "next_action": next_action,
        "metrics_ready": postrun_ready and gate_allowed,
        "metrics_computed": eval_computed,
        "postrun_ready": postrun_ready,
        "postrun_status": postrun_report.get("status", "unknown"),
        "gate_metrics_allowed": gate_allowed,
        "gate_status": gate_report.get("status", "unknown"),
        "evaluator_status": eval_report.get("status", "unknown"),
        "evaluator_scene_count": int(eval_report.get("scene_count", 0) or 0),
        "blockers": blockers,
        "claim_boundary": "Diagnostic status only; do not upgrade geometry claims from this summary.",
    }


def main():
    parser = argparse.ArgumentParser(description="Summarize guarded SMVP3D geometry pipeline status.")
    parser.add_argument("--postrun_json", required=True)
    parser.add_argument("--gate_json", required=True)
    parser.add_argument("--eval_json", required=True)
    parser.add_argument("--output_json", required=True)
    args = parser.parse_args()

    report = summarize_pipeline(
        _load_json(args.postrun_json),
        _load_json(args.gate_json),
        _load_json(args.eval_json),
    )
    _write_json(args.output_json, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "geometry_eval_computed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
