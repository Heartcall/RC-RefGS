import json
import os
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _write_image(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.new("RGB", (512, 512), (32, 64, 96)).save(path)


def _write_synthetic_cameras(path, count=2):
    camera_data = {}
    intrinsic = np.array(
        [
            [500.0, 0.0, 256.0],
            [0.0, 500.0, 256.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    for idx in range(count):
        w2c = np.eye(4, dtype=np.float64)
        w2c[:3, 3] = np.array([0.0, 0.0, 2.0 + idx], dtype=np.float64)
        world_mat = np.eye(4, dtype=np.float64)
        world_mat[:3, :4] = intrinsic @ w2c[:3, :4]
        camera_data["world_mat_{}".format(idx)] = world_mat
        camera_data["scale_mat_{}".format(idx)] = np.eye(4, dtype=np.float64)
    np.savez(path, **camera_data)


class SMVP3DTransformSupportTest(unittest.TestCase):
    def test_projection_decomposition_outputs_blender_compatible_transform(self):
        from utils.smvp3d_utils import build_smvp3d_transforms

        with tempfile.TemporaryDirectory() as tmpdir:
            _write_image(os.path.join(tmpdir, "image", "0000.png"))
            _write_synthetic_cameras(os.path.join(tmpdir, "cameras.npz"), count=1)

            train_transforms, test_transforms, summary = build_smvp3d_transforms(
                tmpdir,
                eval_split=False,
            )

            self.assertEqual(summary["camera_count"], 1)
            self.assertEqual(summary["missing_images"], [])
            self.assertEqual(len(train_transforms["frames"]), 1)
            self.assertEqual(test_transforms["frames"], [])
            self.assertEqual(train_transforms["fl_x"], 500.0)
            self.assertEqual(train_transforms["fl_y"], 500.0)

            frame = train_transforms["frames"][0]
            self.assertEqual(frame["file_path"], "image/0000")
            c2w_for_loader = np.array(frame["transform_matrix"], dtype=np.float64)
            c2w_for_loader[:3, 1:3] *= -1
            w2c = np.linalg.inv(c2w_for_loader)

            np.testing.assert_allclose(w2c[:3, :3], np.eye(3), atol=1e-6)
            np.testing.assert_allclose(w2c[:3, 3], np.array([0.0, 0.0, 2.0]), atol=1e-6)

    def test_cli_writes_train_test_transforms_and_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_image(os.path.join(tmpdir, "image", "0000.png"))
            _write_image(os.path.join(tmpdir, "image", "0001.png"))
            _write_synthetic_cameras(os.path.join(tmpdir, "cameras.npz"), count=2)
            summary_path = os.path.join(tmpdir, "summary.json")

            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO_ROOT, "scripts", "convert_smvp3d_transforms.py"),
                    "--scene_path",
                    tmpdir,
                    "--eval",
                    "--llffhold",
                    "2",
                    "--summary_json",
                    summary_path,
                    "--write",
                ],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            with open(os.path.join(tmpdir, "transforms_train.json"), "r") as handle:
                train_transforms = json.load(handle)
            with open(os.path.join(tmpdir, "transforms_test.json"), "r") as handle:
                test_transforms = json.load(handle)
            with open(summary_path, "r") as handle:
                summary = json.load(handle)

            self.assertEqual([f["file_path"] for f in train_transforms["frames"]], ["image/0001"])
            self.assertEqual([f["file_path"] for f in test_transforms["frames"]], ["image/0000"])
            self.assertEqual(summary["camera_count"], 2)
            self.assertEqual(summary["train_count"], 1)
            self.assertEqual(summary["test_count"], 1)
            self.assertEqual(summary["missing_images"], [])


if __name__ == "__main__":
    unittest.main()
