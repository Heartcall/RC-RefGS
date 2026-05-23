import argparse
import json
import os
from pathlib import Path

import numpy as np


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _load_mesh_vertices(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        lines = handle.readlines()

    if lines and lines[0].strip() == "ply":
        return _load_ascii_ply_vertices(lines)
    return _load_obj_style_vertices(lines)


def _load_obj_style_vertices(lines):
    vertices = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 4 and parts[0] == "v":
            vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
    return np.asarray(vertices, dtype=np.float64)


def _load_ascii_ply_vertices(lines):
    vertex_count = None
    header_end = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("element vertex "):
            vertex_count = int(stripped.split()[-1])
        if stripped == "end_header":
            header_end = index + 1
            break

    if vertex_count is None or header_end is None:
        raise ValueError("Only ASCII PLY files with an element vertex header are supported.")

    vertices = []
    for line in lines[header_end : header_end + vertex_count]:
        parts = line.strip().split()
        if len(parts) >= 3:
            vertices.append([float(parts[0]), float(parts[1]), float(parts[2])])
    return np.asarray(vertices, dtype=np.float64)


def _nearest_distances(source, target, chunk_size=4096):
    distances = []
    for start in range(0, len(source), chunk_size):
        chunk = source[start : start + chunk_size]
        diff = chunk[:, None, :] - target[None, :, :]
        squared = np.sum(diff * diff, axis=2)
        distances.append(np.sqrt(np.min(squared, axis=1)))
    return np.concatenate(distances)


def vertex_chamfer_and_fscore(reference_vertices, predicted_vertices, fscore_threshold):
    if len(reference_vertices) == 0 or len(predicted_vertices) == 0:
        raise ValueError("Both reference and predicted meshes must contain at least one vertex.")

    ref_to_pred = _nearest_distances(reference_vertices, predicted_vertices)
    pred_to_ref = _nearest_distances(predicted_vertices, reference_vertices)
    chamfer_l2 = float(np.mean(ref_to_pred * ref_to_pred) + np.mean(pred_to_ref * pred_to_ref))

    precision = float(np.mean(pred_to_ref <= fscore_threshold))
    recall = float(np.mean(ref_to_pred <= fscore_threshold))
    if precision + recall <= 0.0:
        f_score = 0.0
    else:
        f_score = float(2.0 * precision * recall / (precision + recall))

    return {
        "chamfer_l2": chamfer_l2,
        "precision": precision,
        "recall": recall,
        "f_score": f_score,
        "num_reference_vertices": int(len(reference_vertices)),
        "num_predicted_vertices": int(len(predicted_vertices)),
    }


def _blocked_report(gate):
    return {
        "mode": "smvp3d_geometry_eval",
        "status": "blocked_by_gate",
        "metrics_computed": False,
        "sampling_mode": "vertices_only",
        "blockers": gate.get("blockers", []),
        "scenes": [],
        "claim_boundary": "Gate-blocked run; no geometry metric values are computed.",
    }


def evaluate_plan(geometry_plan, gate, fscore_threshold):
    if not gate.get("metrics_allowed", False):
        return _blocked_report(gate), 2

    scene_reports = []
    failures = []
    for row in geometry_plan.get("scenes", []):
        if row.get("status") != "ready":
            continue
        reference_obj = row.get("reference_obj")
        predicted_mesh = row.get("predicted_mesh")
        if not reference_obj or not os.path.exists(reference_obj):
            failures.append("missing_reference:{}".format(row.get("scene", "unknown")))
            continue
        if not predicted_mesh or not os.path.exists(predicted_mesh):
            failures.append("missing_prediction:{}".format(row.get("scene", "unknown")))
            continue

        reference_vertices = _load_mesh_vertices(reference_obj)
        predicted_vertices = _load_mesh_vertices(predicted_mesh)
        metrics = vertex_chamfer_and_fscore(reference_vertices, predicted_vertices, fscore_threshold)
        metrics.update(
            {
                "scene": row.get("scene"),
                "reference_obj": reference_obj,
                "predicted_mesh": predicted_mesh,
                "status": "computed",
            }
        )
        scene_reports.append(metrics)

    if failures or not scene_reports:
        return (
            {
                "mode": "smvp3d_geometry_eval",
                "status": "blocked_by_inputs",
                "metrics_computed": False,
                "sampling_mode": "vertices_only",
                "blockers": failures or ["no_ready_scenes"],
                "scene_count": int(geometry_plan.get("scene_count", 0) or 0),
                "scenes": [],
                "claim_boundary": "Input-blocked run; no geometry metric values are computed.",
            },
            2,
        )

    return (
        {
            "mode": "smvp3d_geometry_eval",
            "status": "computed",
            "metrics_computed": True,
            "sampling_mode": "vertices_only",
            "fscore_threshold": float(fscore_threshold),
            "scene_count": len(scene_reports),
            "mean_chamfer_l2": float(np.mean([row["chamfer_l2"] for row in scene_reports])),
            "mean_f_score": float(np.mean([row["f_score"] for row in scene_reports])),
            "scenes": scene_reports,
            "claim_boundary": "Metric values are vertex-only geometry diagnostics; do not upgrade claims without full protocol evidence.",
        },
        0,
    )


def main():
    parser = argparse.ArgumentParser(description="Guarded SMVP3D OBJ-reference geometry evaluator.")
    parser.add_argument("--geometry_plan_json", required=True)
    parser.add_argument("--gate_json", required=True)
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--fscore_threshold", type=float, default=0.01)
    args = parser.parse_args()

    report, exit_code = evaluate_plan(
        _load_json(args.geometry_plan_json),
        _load_json(args.gate_json),
        args.fscore_threshold,
    )
    _write_json(args.output_json, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
