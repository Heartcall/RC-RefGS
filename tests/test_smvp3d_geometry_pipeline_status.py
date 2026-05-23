import json
import os
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SMVP3DGeometryPipelineStatusTest(unittest.TestCase):
    def test_current_blocked_reports_extraction_next_action_without_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            postrun_path = os.path.join(tmpdir, "postrun.json")
            gate_path = os.path.join(tmpdir, "gate.json")
            eval_path = os.path.join(tmpdir, "eval.json")
            output_path = os.path.join(tmpdir, "status.json")
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
            with open(gate_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "geometry_metric_gate_dryrun",
                        "metrics_allowed": False,
                        "status": "blocked",
                        "metrics_computed": False,
                        "blockers": [
                            "postrun_status:summary_is_dry_run",
                            "missing_predicted_meshes:5",
                        ],
                    },
                    handle,
                )
            with open(eval_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "smvp3d_geometry_eval",
                        "status": "blocked_by_gate",
                        "metrics_computed": False,
                        "blockers": [
                            "postrun_status:summary_is_dry_run",
                            "missing_predicted_meshes:5",
                        ],
                        "scenes": [],
                    },
                    handle,
                )

            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO_ROOT, "scripts", "summarize_smvp3d_geometry_pipeline_status.py"),
                    "--postrun_json",
                    postrun_path,
                    "--gate_json",
                    gate_path,
                    "--eval_json",
                    eval_path,
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

            self.assertEqual(report["mode"], "smvp3d_geometry_pipeline_status")
            self.assertEqual(report["status"], "blocked_pending_extraction")
            self.assertEqual(report["next_action"], "run_non_dryrun_extraction_smoke_with_explicit_compute")
            self.assertFalse(report["metrics_ready"])
            self.assertFalse(report["metrics_computed"])
            self.assertEqual(
                report["blockers"],
                ["postrun_status:summary_is_dry_run", "missing_predicted_meshes:5"],
            )
            encoded = json.dumps(report).lower()
            self.assertNotIn("chamfer_l2", encoded)
            self.assertNotIn("f_score", encoded)

    def test_computed_evaluator_status_remains_diagnostic_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            postrun_path = os.path.join(tmpdir, "postrun.json")
            gate_path = os.path.join(tmpdir, "gate.json")
            eval_path = os.path.join(tmpdir, "eval.json")
            output_path = os.path.join(tmpdir, "status.json")
            with open(postrun_path, "w", encoding="utf-8") as handle:
                json.dump({"ready": True, "status": "ready", "metrics_computed": False}, handle)
            with open(gate_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "metrics_allowed": True,
                        "status": "ready_for_metric_computation",
                        "metrics_computed": False,
                        "blockers": [],
                    },
                    handle,
                )
            with open(eval_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "mode": "smvp3d_geometry_eval",
                        "status": "computed",
                        "metrics_computed": True,
                        "scene_count": 1,
                        "scenes": [{"scene": "synthetic", "status": "computed"}],
                    },
                    handle,
                )

            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO_ROOT, "scripts", "summarize_smvp3d_geometry_pipeline_status.py"),
                    "--postrun_json",
                    postrun_path,
                    "--gate_json",
                    gate_path,
                    "--eval_json",
                    eval_path,
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

            self.assertEqual(report["status"], "geometry_eval_computed")
            self.assertEqual(report["next_action"], "review_diagnostic_only_metrics_without_claim_upgrade")
            self.assertTrue(report["metrics_ready"])
            self.assertTrue(report["metrics_computed"])
            self.assertEqual(report["claim_boundary"], "Diagnostic status only; do not upgrade geometry claims from this summary.")


if __name__ == "__main__":
    unittest.main()
