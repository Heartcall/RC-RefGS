import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class MetricSweepDirectStaticTests(unittest.TestCase):
    def test_metric_sweep_runner_contract(self):
        runner = Path("scripts/run_rc_refgs_metric_sweep_direct.py")
        self.assertTrue(runner.exists(), "scripts/run_rc_refgs_metric_sweep_direct.py is missing")

        source = runner.read_text()
        required_snippets = [
            "SUPPORTED_METRICS =",
            '"render_quality"',
            '"material_quality"',
            "def _build_jobs(",
            "def _metric_command(",
            "def _run_job(",
            "def _write_summary(",
            "subprocess.run(",
            "stdout=log_file",
            "stderr=subprocess.STDOUT",
            'parser.add_argument("--stop_on_failure"',
            'parser.add_argument("--summary_json"',
            'parser.add_argument("--log_root"',
            'parser.add_argument("--dry_run"',
            "render_quality_{split}_iter{iteration}.json",
            "material_quality_{split}_iter{iteration}.json",
            "raise SystemExit(2)",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_metric_sweep_runner_dry_run_writes_status_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            summary_json = tmpdir_path / "summary.json"
            log_root = tmpdir_path / "logs"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_rc_refgs_metric_sweep_direct.py",
                    "--data_root",
                    "/data/liuly/dataset/3DGS/refnerf",
                    "--model_root",
                    str(tmpdir_path / "models"),
                    "--scenes",
                    "teapot",
                    "--variants",
                    "base",
                    "rc",
                    "--metrics",
                    "render_quality",
                    "material_quality",
                    "--iteration",
                    "300",
                    "--split",
                    "both",
                    "--mask_mode",
                    "both",
                    "--cuda_device",
                    "0",
                    "--summary_json",
                    str(summary_json),
                    "--log_root",
                    str(log_root),
                    "--dry_run",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(summary_json.exists(), "dry run did not write summary_json")
            summary = json.loads(summary_json.read_text())
            self.assertEqual(summary["job_count"], 4)
            self.assertEqual(summary["failed_count"], 0)
            self.assertTrue(summary["dry_run"])
            self.assertTrue(summary["stop_on_failure"])
            statuses = {job["status"] for job in summary["jobs"]}
            self.assertEqual(statuses, {"dry_run"})
            commands = "\n".join(" ".join(job["command"]) for job in summary["jobs"])
            self.assertIn("metrics/render_quality_eval.py", commands)
            self.assertIn("metrics/material_quality_eval.py", commands)
            self.assertIn("--output_json", commands)
            self.assertIn(str(log_root), "\n".join(job["log_path"] for job in summary["jobs"]))


if __name__ == "__main__":
    unittest.main()
