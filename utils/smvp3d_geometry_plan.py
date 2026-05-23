import json
import os


DEFAULT_SMVP3D_SCENES = ("david", "dragon", "hedgehog", "snail", "squirrel")


def _normalise_scenes(scenes):
    if scenes is None:
        return list(DEFAULT_SMVP3D_SCENES)
    return [scene for scene in scenes if scene]


def build_smvp3d_geometry_eval_plan(
    dataset_root,
    mesh_root,
    scenes=None,
    mesh_template="{scene}/mesh_iter{iteration}.ply",
    iteration=300,
):
    scene_names = _normalise_scenes(scenes)
    rows = []

    for scene in scene_names:
        reference_obj = os.path.abspath(os.path.join(dataset_root, scene, "{}.obj".format(scene)))
        predicted_mesh = os.path.abspath(
            os.path.join(mesh_root, mesh_template.format(scene=scene, iteration=iteration))
        )
        reference_exists = os.path.exists(reference_obj)
        prediction_exists = os.path.exists(predicted_mesh)

        if not reference_exists:
            status = "missing_reference"
        elif not prediction_exists:
            status = "missing_prediction"
        else:
            status = "ready"

        rows.append(
            {
                "scene": scene,
                "reference_obj": reference_obj,
                "predicted_mesh": predicted_mesh,
                "reference_exists": reference_exists,
                "prediction_exists": prediction_exists,
                "status": status,
            }
        )

    return {
        "mode": "smvp3d_geometry_eval_dryrun",
        "metrics_computed": False,
        "dataset_root": os.path.abspath(dataset_root),
        "mesh_root": os.path.abspath(mesh_root),
        "mesh_template": mesh_template,
        "iteration": int(iteration),
        "scene_count": len(rows),
        "reference_obj_count": sum(1 for row in rows if row["reference_exists"]),
        "ready_count": sum(1 for row in rows if row["status"] == "ready"),
        "missing_reference_count": sum(1 for row in rows if row["status"] == "missing_reference"),
        "missing_mesh_count": sum(1 for row in rows if row["status"] == "missing_prediction"),
        "scenes": rows,
        "claim_boundary": "Dry-run input plan only; no geometry metric values are computed.",
    }


def write_geometry_eval_plan(path, plan):
    with open(path, "w") as handle:
        json.dump(plan, handle, indent=2)
