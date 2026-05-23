import json
import os
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _write_obj(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        handle.write("v 0 0 0\n")
        handle.write("v 1 0 0\n")
        handle.write("v 0 1 0\n")
        handle.write("f 1 2 3\n")


class SMVP3DGeometryEvalPlanTest(unittest.TestCase):
    def test_plan_reports_reference_objs_and_missing_prediction_meshes_without_metrics(self):
        from utils.smvp3d_geometry_plan import build_smvp3d_geometry_eval_plan

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = os.path.join(tmpdir, "SMVP3D")
            mesh_root = os.path.join(tmpdir, "meshes")
            _write_obj(os.path.join(dataset_root, "david", "david.obj"))
            _write_obj(os.path.join(dataset_root, "dragon", "dragon.obj"))
            os.makedirs(os.path.join(mesh_root, "dragon"), exist_ok=True)
            _write_obj(os.path.join(mesh_root, "dragon", "mesh_iter300.ply"))

            plan = build_smvp3d_geometry_eval_plan(
                dataset_root,
                mesh_root,
                scenes=["david", "dragon"],
                mesh_template="{scene}/mesh_iter{iteration}.ply",
                iteration=300,
            )

            self.assertEqual(plan["mode"], "smvp3d_geometry_eval_dryrun")
            self.assertFalse(plan["metrics_computed"])
            self.assertEqual(plan["scene_count"], 2)
            self.assertEqual(plan["reference_obj_count"], 2)
            self.assertEqual(plan["ready_count"], 1)
            self.assertEqual(plan["missing_mesh_count"], 1)
            self.assertNotIn("chamfer", json.dumps(plan).lower())
            self.assertNotIn("f_score", json.dumps(plan).lower())

            by_scene = {row["scene"]: row for row in plan["scenes"]}
            self.assertEqual(by_scene["david"]["status"], "missing_prediction")
            self.assertEqual(by_scene["dragon"]["status"], "ready")
            self.assertTrue(by_scene["david"]["reference_obj"].endswith("david/david.obj"))
            self.assertTrue(by_scene["dragon"]["predicted_mesh"].endswith("dragon/mesh_iter300.ply"))

    def test_cli_writes_summary_without_requiring_prediction_meshes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = os.path.join(tmpdir, "SMVP3D")
            mesh_root = os.path.join(tmpdir, "meshes")
            _write_obj(os.path.join(dataset_root, "snail", "snail.obj"))
            summary_path = os.path.join(tmpdir, "summary.json")

            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO_ROOT, "scripts", "prepare_smvp3d_geometry_eval.py"),
                    "--dataset_root",
                    dataset_root,
                    "--mesh_root",
                    mesh_root,
                    "--scenes",
                    "snail",
                    "--iteration",
                    "300",
                    "--summary_json",
                    summary_path,
                ],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            with open(summary_path, "r") as handle:
                summary = json.load(handle)

            self.assertFalse(summary["metrics_computed"])
            self.assertEqual(summary["scene_count"], 1)
            self.assertEqual(summary["ready_count"], 0)
            self.assertEqual(summary["missing_mesh_count"], 1)
            self.assertEqual(summary["scenes"][0]["status"], "missing_prediction")


if __name__ == "__main__":
    unittest.main()
