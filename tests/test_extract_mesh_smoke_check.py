import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ExtractMeshSmokeCheckTests(unittest.TestCase):
    def test_postrun_smoke_check_reports_ready_mesh_without_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            mesh_path = root / "mesh_iter300.ply"
            mesh_path.write_text("ply\nformat ascii 1.0\nend_header\n", encoding="utf-8")
            runtime_summary = root / "runtime_summary.json"
            output_json = root / "check.json"
            runtime_summary.write_text(
                json.dumps(
                    {
                        "mode": "mesh_extraction",
                        "dry_run": False,
                        "model_path": str(root / "model"),
                        "iteration": 300,
                        "output_mesh": str(mesh_path),
                        "missing_inputs": [],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/check_extract_mesh_smoke.py",
                    "--summary_json",
                    str(runtime_summary),
                    "--output_json",
                    str(output_json),
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output_json.read_text())
            self.assertEqual(report["mode"], "extract_mesh_postrun_smoke_check")
            self.assertTrue(report["ready"])
            self.assertFalse(report["metrics_computed"])
            self.assertEqual(report["mesh_path"], str(mesh_path))
            self.assertGreater(report["mesh_size_bytes"], 0)
            encoded = json.dumps(report).lower()
            self.assertNotIn("chamfer", encoded)
            self.assertNotIn("f_score", encoded)

    def test_postrun_smoke_check_fails_when_mesh_is_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            mesh_path = root / "missing_mesh.ply"
            runtime_summary = root / "runtime_summary.json"
            output_json = root / "check.json"
            runtime_summary.write_text(
                json.dumps(
                    {
                        "mode": "mesh_extraction",
                        "dry_run": False,
                        "model_path": str(root / "model"),
                        "iteration": 300,
                        "output_mesh": str(mesh_path),
                        "missing_inputs": [],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/check_extract_mesh_smoke.py",
                    "--summary_json",
                    str(runtime_summary),
                    "--output_json",
                    str(output_json),
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(output_json.read_text())
            self.assertFalse(report["ready"])
            self.assertEqual(report["status"], "missing_mesh")


if __name__ == "__main__":
    unittest.main()
