from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/run_rc_refgs_geometry_rerun.py"


def load_module():
    spec = importlib.util.spec_from_file_location("geometry_rerun_launcher", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GeometryRerunLauncherTests(unittest.TestCase):
    def run_launcher(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(REPO_ROOT),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    def test_all_dry_run_writes_exact_70_job_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "manifest.csv"
            result = self.run_launcher(
                "--dry-run",
                "--manifest-output",
                str(manifest),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with manifest.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 70)
            self.assertEqual({row["seed"] for row in rows}, {"0"})
            self.assertEqual({row["iteration"] for row in rows}, {"31000"})
            self.assertEqual(
                {row["variant"] for row in rows},
                {"base", "rc", "wo_ref", "wo_conf", "rough_only"},
            )
            self.assertTrue(all(row["split"] == "scene_geometry" for row in rows))
            self.assertTrue(
                all(
                    row["model_path"].startswith(
                        "/data/liuly/experiments/rc_refgs_geometry_rerun/runs/"
                    )
                    for row in rows
                )
            )
            self.assertTrue(all("/tmp/" not in row["model_path"] for row in rows))
            required = {
                "cfg_args_path",
                "train_log_path",
                "reflection_train_log_path",
                "reflection_test_log_path",
                "render_quality_log_path",
                "point_cloud_path",
                "checkpoint_path",
                "cameras_path",
                "reflection_train_path",
                "reflection_test_path",
                "render_quality_path",
            }
            self.assertTrue(required.issubset(rows[0]))
            expected = rows[0]["expected_artifact_paths"]
            self.assertIn("reflection_consistency_train.log", expected)
            self.assertIn("chkpnt31000.pth", expected)

    def test_ball_base_rc_smoke_subset_has_two_commands(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "manifest.csv"
            result = self.run_launcher(
                "--dry-run",
                "--subset",
                "ball_base_rc_smoke",
                "--manifest-output",
                str(manifest),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with manifest.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual({row["scene"] for row in rows}, {"ball"})
            self.assertEqual({row["variant"] for row in rows}, {"base", "rc"})
            self.assertTrue(all("train.py" in row["command"] for row in rows))

    def test_execute_refuses_non_durable_output_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_launcher(
                "--execute",
                "--confirm-execute",
                "NEW_GEOMETRY_RERUN_20260611",
                "--output-root",
                str(Path(tmpdir) / "runs"),
                "--manifest-output",
                str(Path(tmpdir) / "manifest.csv"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("durable", result.stderr.lower())

    def test_execute_refuses_low_disk_before_cuda_probe(self):
        module = load_module()
        args = SimpleNamespace(
            output_root=module.DURABLE_RUN_ROOT,
            confirm_execute=module.CONFIRM_TOKEN,
            min_free_gib=80.0,
            python_executable=module.REF_GS_PYTHON,
            devices=["0"],
        )
        usage = SimpleNamespace(free=10 * 1024 ** 3)
        with mock.patch.object(module.shutil, "disk_usage", return_value=usage), mock.patch.object(
            module, "_cuda_probe"
        ) as cuda_probe:
            with self.assertRaises(SystemExit) as raised:
                module.validate_execute(args)
        self.assertIn("safety threshold", str(raised.exception))
        cuda_probe.assert_not_called()

    def test_execute_refuses_failed_cuda_after_disk_gate(self):
        module = load_module()
        args = SimpleNamespace(
            output_root=module.DURABLE_RUN_ROOT,
            confirm_execute=module.CONFIRM_TOKEN,
            min_free_gib=80.0,
            python_executable=module.REF_GS_PYTHON,
            devices=["0"],
        )
        usage = SimpleNamespace(free=100 * 1024 ** 3)
        with mock.patch.object(module.shutil, "disk_usage", return_value=usage), mock.patch.object(
            module, "_cuda_probe", return_value=(False, {"available": False, "count": 0})
        ):
            with self.assertRaises(SystemExit) as raised:
                module.validate_execute(args)
        self.assertIn("CUDA preflight failed", str(raised.exception))

    def test_execute_refuses_unreviewed_seed_or_iteration(self):
        module = load_module()
        args = SimpleNamespace(
            output_root=module.DURABLE_RUN_ROOT,
            confirm_execute=module.CONFIRM_TOKEN,
            min_free_gib=80.0,
            python_executable=module.REF_GS_PYTHON,
            devices=["0"],
            seed=1,
            iterations=31000,
        )
        with self.assertRaises(SystemExit) as raised:
            module.validate_execute(args)
        self.assertIn("seed 0", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
