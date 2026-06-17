from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "paper_assets/geometry/scripts/extract_meshes_for_completed_runs.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("extract_mesh_manifest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GeometryRerunMeshManifestTests(unittest.TestCase):
    def test_manifest_mode_plans_complete_run_and_excludes_missing_run(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmpdir:
            root = Path(tmpdir)
            complete = root / "complete"
            missing = root / "missing"
            point_cloud = complete / "point_cloud/iteration_31000/point_cloud.ply"
            point_cloud.parent.mkdir(parents=True)
            point_cloud.write_text("ply\n", encoding="utf-8")
            (complete / "cfg_args").write_text("Namespace()", encoding="utf-8")
            manifest = root / "jobs.csv"
            with manifest.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "dataset",
                        "scene",
                        "split",
                        "variant",
                        "seed",
                        "iteration",
                        "status",
                        "model_path",
                        "point_cloud_path",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "dataset": "shiny_blender_synthetic",
                        "scene": "ball",
                        "split": "scene_geometry",
                        "variant": "base",
                        "seed": 0,
                        "iteration": 31000,
                        "status": "completed",
                        "model_path": complete,
                        "point_cloud_path": point_cloud,
                    }
                )
                writer.writerow(
                    {
                        "dataset": "shiny_blender_synthetic",
                        "scene": "ball",
                        "split": "scene_geometry",
                        "variant": "rc",
                        "seed": 0,
                        "iteration": 31000,
                        "status": "failed_exit_1",
                        "model_path": missing,
                        "point_cloud_path": missing / "point_cloud/iteration_31000/point_cloud.ply",
                    }
                )

            output_manifest = root / "prediction_mesh_manifest.csv"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--manifest",
                    str(manifest),
                    "--prediction-root",
                    str(root / "pred_meshes"),
                    "--manifest-output",
                    str(output_manifest),
                    "--split",
                    "both",
                ],
                cwd=str(REPO_ROOT),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with output_manifest.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            by_variant = {row["variant"]: row for row in rows}
            self.assertEqual(by_variant["base"]["status"], "planned")
            self.assertEqual(by_variant["base"]["split"], "both")
            self.assertEqual(by_variant["rc"]["status"], "excluded")
            self.assertIn("not completed", by_variant["rc"]["reason"])
            self.assertIn("pred_meshes", by_variant["base"]["prediction_path"])
            self.assertIn("extract_mesh_iter31000.log", by_variant["base"]["extraction_log_path"])
            self.assertNotIn("Ref-GS-I2", "\n".join(row["prediction_path"] for row in rows))

    def test_prediction_root_accepts_workspace_absolute_path_and_rejects_temp_roots(self):
        module = _load_script_module()
        durable_root = REPO_ROOT / "output/rc_refgs_geometry_rerun/pred_meshes"

        self.assertEqual(module._validate_prediction_root(durable_root), durable_root)
        with self.assertRaises(SystemExit):
            module._validate_prediction_root(Path("relative/pred_meshes"))
        for forbidden in [Path("/tmp/pred_meshes"), Path("/var/tmp/pred_meshes"), Path("/dev/shm/pred_meshes")]:
            with self.subTest(forbidden=forbidden), self.assertRaises(SystemExit):
                module._validate_prediction_root(forbidden)

    def test_execute_continues_after_failure_and_main_always_writes_manifest(self):
        module = _load_script_module()
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmpdir:
            root = Path(tmpdir)
            manifest = root / "jobs.csv"
            source_rows = []
            for variant in ["base", "rc"]:
                model_path = root / "runs" / variant
                point_cloud = model_path / "point_cloud/iteration_31000/point_cloud.ply"
                point_cloud.parent.mkdir(parents=True)
                point_cloud.write_text("ply\n", encoding="utf-8")
                (model_path / "cfg_args").write_text("Namespace()", encoding="utf-8")
                source_rows.append(
                    {
                        "dataset": "shiny_blender_synthetic",
                        "scene": "ball",
                        "split": "scene_geometry",
                        "variant": variant,
                        "seed": 0,
                        "iteration": 31000,
                        "status": "completed",
                        "model_path": model_path,
                        "point_cloud_path": point_cloud,
                    }
                )
            with manifest.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(source_rows[0]))
                writer.writeheader()
                writer.writerows(source_rows)

            output_manifest = root / "prediction_mesh_manifest.csv"
            prediction_root = root / "pred_meshes"
            calls = 0

            def fake_run(argv, **kwargs):
                nonlocal calls
                calls += 1
                self.assertEqual(argv[argv.index("--split") + 1], "both")
                self.assertIn("--depth_trunc", argv)
                self.assertEqual(argv[argv.index("--depth_trunc") + 1], "10.0")
                self.assertIn("MPLCONFIGDIR", kwargs["env"])
                self.assertTrue(kwargs["env"]["MPLCONFIGDIR"].startswith(str(REPO_ROOT)))
                self.assertNotIn("/tmp", kwargs["env"]["MPLCONFIGDIR"])
                if calls == 1:
                    raise subprocess.CalledProcessError(7, argv)
                output_mesh = Path(argv[argv.index("--output_mesh") + 1])
                output_mesh.write_text("ply\n", encoding="utf-8")
                return subprocess.CompletedProcess(argv, 0)

            argv = [
                str(SCRIPT),
                "--execute",
                "--manifest",
                str(manifest),
                "--prediction-root",
                str(prediction_root),
                "--manifest-output",
                str(output_manifest),
                "--python-executable",
                sys.executable,
                "--split",
                "both",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                module.subprocess, "run", side_effect=fake_run
            ):
                self.assertEqual(module.main(), 0)

            with output_manifest.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            by_variant = {row["variant"]: row for row in rows}
            self.assertEqual(by_variant["base"]["status"], "failed_exit_7")
            self.assertIn("exit code 7", by_variant["base"]["reason"])
            self.assertIn(by_variant["base"]["extraction_log_path"], by_variant["base"]["reason"])
            self.assertEqual(by_variant["base"]["split"], "both")
            self.assertEqual(by_variant["rc"]["status"], "completed")
            self.assertEqual(by_variant["rc"]["split"], "both")


if __name__ == "__main__":
    unittest.main()
