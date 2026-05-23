import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from utils.smvp3d_utils import build_smvp3d_transforms, write_smvp3d_transforms, write_summary


def main():
    parser = argparse.ArgumentParser(
        description="Convert SMVP3D cameras.npz metadata into Ref-GS Blender-style transforms JSON files."
    )
    parser.add_argument("--scene_path", required=True)
    parser.add_argument("--image_dir", default="image")
    parser.add_argument("--extension", default=".png")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--llffhold", type=int, default=8)
    parser.add_argument("--summary_json", default=None)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    train_transforms, test_transforms, summary = build_smvp3d_transforms(
        args.scene_path,
        eval_split=args.eval,
        llffhold=args.llffhold,
        image_dir=args.image_dir,
        extension=args.extension,
    )

    if args.write:
        train_path, test_path = write_smvp3d_transforms(
            args.scene_path,
            train_transforms,
            test_transforms,
        )
        summary["transforms_train_path"] = train_path
        summary["transforms_test_path"] = test_path

    if args.summary_json:
        write_summary(args.summary_json, summary)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
