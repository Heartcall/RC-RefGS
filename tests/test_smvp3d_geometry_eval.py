import json
import os
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _write_triangle_mesh(path):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("v 0 0 0\n")
        handle.write("v 1 0 0\n")
        handle.write("v 0 1 0\n")
        handle.write("f 1 2 3\n")


class SMVP3DGeometryEvalTest(unittest.TestCase):
    def test_blocked_gate_refuses_metric_computation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gate_path = os.path.join(tmpdir, "gate.json")
            plan_path = os.path.join(tmpdir, "plan.json")
            output_path = os.path.join(tmpdir, "metrics.json")
            with open(gate_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "geometry_metric_gate_dryrun",
                        "metrics_allowed": False,
                        "status": "blocked",
                        "metrics_computed": False,
                        "blockers": ["missing_predicted_meshes:1"],
                    },
                    handle,
                )
            with open(plan_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "smvp3d_geometry_eval_dryrun",
                        "metrics_computed": False,
                        "scene_count": 1,
                        "ready_count": 0,
                        "scenes": [],
                    },
                    handle,
                )

            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO_ROOT, "metrics", "smvp3d_geometry_eval.py"),
                    "--geometry_plan_json",
                    plan_path,
                    "--gate_json",
                    gate_path,
                    "--output_json",
                    output_path,
                ],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 2, msg=result.stderr)
            with open(output_path, "r", encoding="utf-8") as handle:
                report = json.load(handle)

            self.assertEqual(report["mode"], "smvp3d_geometry_eval")
            self.assertFalse(report["metrics_computed"])
            self.assertEqual(report["status"], "blocked_by_gate")
            self.assertEqual(report["blockers"], ["missing_predicted_meshes:1"])
            self.assertEqual(report["scenes"], [])

    def test_ready_synthetic_meshes_compute_vertex_chamfer_and_fscore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_path = os.path.join(tmpdir, "reference.obj")
            pred_path = os.path.join(tmpdir, "prediction.ply")
            gate_path = os.path.join(tmpdir, "gate.json")
            plan_path = os.path.join(tmpdir, "plan.json")
            output_path = os.path.join(tmpdir, "metrics.json")
            _write_triangle_mesh(ref_path)
            _write_triangle_mesh(pred_path)
            with open(gate_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "geometry_metric_gate_dryrun",
                        "metrics_allowed": True,
                        "status": "ready_for_metric_computation",
                        "metrics_computed": False,
                        "blockers": [],
                    },
                    handle,
                )
            with open(plan_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "smvp3d_geometry_eval_dryrun",
                        "metrics_computed": False,
                        "scene_count": 1,
                        "ready_count": 1,
                        "scenes": [
                            {
                                "scene": "synthetic",
                                "reference_obj": ref_path,
                                "predicted_mesh": pred_path,
                                "status": "ready",
                            }
                        ],
                    },
                    handle,
                )

            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO_ROOT, "metrics", "smvp3d_geometry_eval.py"),
                    "--geometry_plan_json",
                    plan_path,
                    "--gate_json",
                    gate_path,
                    "--output_json",
                    output_path,
                    "--fscore_threshold",
                    "0.01",
                ],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            with open(output_path, "r", encoding="utf-8") as handle:
                report = json.load(handle)

            self.assertTrue(report["metrics_computed"])
            self.assertEqual(report["status"], "computed")
            self.assertEqual(report["scene_count"], 1)
            self.assertEqual(report["mean_chamfer_l2"], 0.0)
            self.assertEqual(report["mean_f_score"], 1.0)
            self.assertEqual(report["scenes"][0]["chamfer_l2"], 0.0)
            self.assertEqual(report["scenes"][0]["f_score"], 1.0)
            self.assertEqual(report["sampling_mode"], "vertices_only")


if __name__ == "__main__":
    unittest.main()
