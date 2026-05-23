import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from utils.smvp3d_geometry_plan import build_smvp3d_geometry_eval_plan, write_geometry_eval_plan


def _parse_scenes(value):
    if not value:
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="Prepare an SMVP3D OBJ-reference geometry-evaluation dry-run plan."
    )
    parser.add_argument("--dataset_root", required=True)
    parser.add_argument("--mesh_root", required=True)
    parser.add_argument("--scenes", default=None, help="Comma-separated scene names. Defaults to all SMVP3D scenes.")
    parser.add_argument("--mesh_template", default="{scene}/mesh_iter{iteration}.ply")
    parser.add_argument("--iteration", type=int, default=300)
    parser.add_argument("--summary_json", default=None)
    args = parser.parse_args()

    plan = build_smvp3d_geometry_eval_plan(
        args.dataset_root,
        args.mesh_root,
        scenes=_parse_scenes(args.scenes),
        mesh_template=args.mesh_template,
        iteration=args.iteration,
    )

    if args.summary_json:
        write_geometry_eval_plan(args.summary_json, plan)

    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
