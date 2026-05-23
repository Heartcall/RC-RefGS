import json
import os
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GeometryMetricGateTest(unittest.TestCase):
    def test_gate_allows_metric_computation_when_extraction_and_plan_are_ready(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            postrun_path = os.path.join(tmpdir, "postrun.json")
            plan_path = os.path.join(tmpdir, "plan.json")
            output_path = os.path.join(tmpdir, "gate.json")

            with open(postrun_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "extract_mesh_postrun_smoke_check",
                        "ready": True,
                        "status": "ready",
                        "metrics_computed": False,
                    },
                    handle,
                )
            with open(plan_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "smvp3d_geometry_eval_dryrun",
                        "metrics_computed": False,
                        "scene_count": 2,
                        "reference_obj_count": 2,
                        "ready_count": 2,
                        "missing_mesh_count": 0,
                    },
                    handle,
                )

            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO_ROOT, "scripts", "check_geometry_metric_gate.py"),
                    "--postrun_json",
                    postrun_path,
                    "--geometry_plan_json",
                    plan_path,
                    "--output_json",
                    output_path,
                ],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            with open(output_path, "r", encoding="utf-8") as handle:
                report = json.load(handle)

            self.assertEqual(report["mode"], "geometry_metric_gate_dryrun")
            self.assertTrue(report["metrics_allowed"])
            self.assertEqual(report["status"], "ready_for_metric_computation")
            self.assertFalse(report["metrics_computed"])
            self.assertEqual(report["blockers"], [])
            encoded = json.dumps(report).lower()
            self.assertNotIn("chamfer", encoded)
            self.assertNotIn("f_score", encoded)

    def test_gate_blocks_current_dryrun_and_missing_prediction_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            postrun_path = os.path.join(tmpdir, "postrun.json")
            plan_path = os.path.join(tmpdir, "plan.json")
            output_path = os.path.join(tmpdir, "gate.json")

            with open(postrun_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "extract_mesh_postrun_smoke_check",
                        "ready": False,
                        "status": "summary_is_dry_run",
                        "metrics_computed": False,
                    },
                    handle,
                )
            with open(plan_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "smvp3d_geometry_eval_dryrun",
                        "metrics_computed": False,
                        "scene_count": 1,
                        "reference_obj_count": 1,
                        "ready_count": 0,
                        "missing_mesh_count": 1,
                    },
                    handle,
                )

            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO_ROOT, "scripts", "check_geometry_metric_gate.py"),
                    "--postrun_json",
                    postrun_path,
                    "--geometry_plan_json",
                    plan_path,
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

            self.assertFalse(report["metrics_allowed"])
            self.assertEqual(report["status"], "blocked")
            self.assertFalse(report["metrics_computed"])
            self.assertEqual(
                report["blockers"],
                ["postrun_status:summary_is_dry_run", "missing_predicted_meshes:1"],
            )


if __name__ == "__main__":
    unittest.main()
