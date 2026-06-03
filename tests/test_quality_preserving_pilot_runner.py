import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def _load_runner():
    path = Path("scripts/run_rc_refgs_quality_preserving_pilot.py")
    spec = importlib.util.spec_from_file_location("quality_preserving_pilot", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QualityPreservingPilotRunnerTests(unittest.TestCase):
    def _write_target_csv(self, tmpdir: Path) -> Path:
        path = tmpdir / "targets.csv"
        rows = [
            {
                "dataset": "shiny_blender_synthetic",
                "scene": "helmet",
                "source_path": "/data/shiny/helmet",
                "selection_reason": "strongest consistency gain with quality regression signal",
                "evidence": "delta evidence",
                "variant": "rc_qp_lam010",
                "lambda_ref_consistency": "0.010",
                "ref_consistency_start": "3000",
                "ref_consistency_every": "4",
                "ref_consistency_gamma": "2.0",
                "lambda_dssim": "0.2",
                "expected_effect": "middle point",
                "acceptance_criteria": "future criteria",
            },
            {
                "dataset": "glossy_synthetic",
                "scene": "luyu",
                "source_path": "/data/glossy/luyu",
                "selection_reason": "reflective LPIPS regression",
                "evidence": "delta evidence",
                "variant": "rc_qp_lam005",
                "lambda_ref_consistency": "0.005",
                "ref_consistency_start": "3000",
                "ref_consistency_every": "4",
                "ref_consistency_gamma": "2.0",
                "lambda_dssim": "0.2",
                "expected_effect": "low pressure",
                "acceptance_criteria": "future criteria",
            },
        ]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_dry_run_command_generation_and_variant_flags(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            target_csv = self._write_target_csv(Path(tmp))
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(Path(tmp) / "out"),
                    "--devices",
                    "7",
                    "--variants",
                    "rc_qp_lam005",
                    "rc_qp_lam010",
                    "rc_qp_lam015",
                    "rc_qp_lam010_start5000_every8",
                    "--max_jobs",
                    "4",
                ]
            )
            jobs = runner.build_jobs(args)

        self.assertEqual(len(jobs), 4)
        commands = "\n".join(" ".join(job["train_command"]) for job in jobs)
        self.assertIn("--lambda_ref_consistency 0.005", commands)
        self.assertIn("--lambda_ref_consistency 0.01", commands)
        self.assertIn("--lambda_ref_consistency 0.015", commands)
        self.assertIn("--ref_consistency_start 5000", commands)
        self.assertIn("--ref_consistency_every 8", commands)
        self.assertIn("--lambda_dssim 0.2", commands)
        self.assertIn("--cuda_device 7", commands)
        self.assertNotIn("shiny_blender_real", json.dumps(jobs))

    def test_defaults_are_dry_run_and_execute_requires_confirmation(self):
        runner = Path("scripts/run_rc_refgs_quality_preserving_pilot.py")
        with tempfile.TemporaryDirectory() as tmp:
            target_csv = self._write_target_csv(Path(tmp))
            result = subprocess.run(
                [
                    sys.executable,
                    str(runner),
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(Path(tmp) / "out"),
                    "--devices",
                    "7",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            status = json.loads((Path(tmp) / "out" / "pilot_status.json").read_text())
            self.assertTrue(status["dry_run"])
            self.assertEqual(status["summary"]["dry_run"], 1)
            self.assertEqual(status["summary"]["completed"], 0)

            bad = subprocess.run(
                [
                    sys.executable,
                    str(runner),
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(Path(tmp) / "out2"),
                    "--devices",
                    "7",
                    "--execute",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("--execute requires --confirm_execute YES", bad.stderr)

    def test_output_paths_max_jobs_and_metric_commands(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            target_csv = self._write_target_csv(Path(tmp))
            output_root = Path(tmp) / "qp"
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(output_root),
                    "--devices",
                    "6",
                    "--variants",
                    "rc_qp_lam010",
                    "rc_qp_lam010_start5000_every8",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                ]
            )
            jobs = runner.build_jobs(args)

        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job["dataset"], "shiny_blender_synthetic")
        self.assertEqual(job["scene"], "helmet")
        self.assertEqual(job["variant"], "rc_qp_lam010")
        self.assertTrue(str(job["model_path"]).startswith(str(output_root)))
        self.assertNotIn("rc_refgs_full_dataset_base_rc_i31000_20260527", str(job["model_path"]))
        self.assertNotIn("rc_refgs_full_dataset_ablations_i31000_20260528", str(job["model_path"]))
        metric_commands = "\n".join(" ".join(cmd) for cmd in job["metric_commands"].values())
        self.assertIn("metrics/reflection_consistency_eval.py", metric_commands)
        self.assertIn("--split train", metric_commands)
        self.assertIn("--split test", metric_commands)
        self.assertIn("metrics/render_quality_eval.py", metric_commands)
        self.assertIn("--split both", metric_commands)
        self.assertIn("--mask_mode both", metric_commands)
        self.assertIn("--image_key pbr_rgb", metric_commands)

    def test_dry_run_launcher_summary_does_not_make_job_complete(self):
        runner = Path("scripts/run_rc_refgs_quality_preserving_pilot.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            output_root = root / "out"
            model_path = output_root / "shiny_blender_synthetic" / "helmet" / "rc_qp_lam010" / "seed_0"
            (model_path / "point_cloud" / "iteration_31000").mkdir(parents=True)
            (model_path / "point_cloud" / "iteration_31000" / "point_cloud.ply").write_text("ply\n", encoding="utf-8")
            (model_path / "reflection_consistency_train.json").write_text("{}", encoding="utf-8")
            (model_path / "reflection_consistency_test.json").write_text("{}", encoding="utf-8")
            (model_path / "render_quality_both_iter31000.json").write_text("{}", encoding="utf-8")
            (model_path / "launcher_summary.json").write_text('{"status":"dry_run"}\n', encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(runner),
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(output_root),
                    "--devices",
                    "7",
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            status = json.loads((output_root / "pilot_status.json").read_text())
            self.assertEqual(status["summary"]["skipped_complete"], 0)
            self.assertEqual(status["summary"]["dry_run"], 1)

    def test_completed_launcher_summary_allows_skip_complete(self):
        runner = Path("scripts/run_rc_refgs_quality_preserving_pilot.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            output_root = root / "out"
            model_path = output_root / "shiny_blender_synthetic" / "helmet" / "rc_qp_lam010" / "seed_0"
            (model_path / "point_cloud" / "iteration_31000").mkdir(parents=True)
            (model_path / "point_cloud" / "iteration_31000" / "point_cloud.ply").write_text("ply\n", encoding="utf-8")
            (model_path / "reflection_consistency_train.json").write_text("{}", encoding="utf-8")
            (model_path / "reflection_consistency_test.json").write_text("{}", encoding="utf-8")
            (model_path / "render_quality_both_iter31000.json").write_text("{}", encoding="utf-8")
            (model_path / "launcher_summary.json").write_text('{"status":"completed"}\n', encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(runner),
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(output_root),
                    "--devices",
                    "7",
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            status = json.loads((output_root / "pilot_status.json").read_text())
            self.assertEqual(status["summary"]["skipped_complete"], 1)
            self.assertEqual(status["summary"]["dry_run"], 0)

    def test_smoke_mode_uses_smoke_iterations_in_commands_and_artifacts(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            target_csv = self._write_target_csv(Path(tmp))
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(Path(tmp) / "smoke"),
                    "--devices",
                    "7",
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                    "--smoke",
                    "--smoke_iterations",
                    "123",
                ]
            )
            jobs = runner.build_jobs(args)

        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job["iterations"], 123)
        self.assertIn("--iterations 123", " ".join(job["train_command"]))
        self.assertIn("render_quality_both_iter123.json", json.dumps(job["expected_artifacts"]))


if __name__ == "__main__":
    unittest.main()
