import csv
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
            {
                "dataset": "glossy_synthetic",
                "scene": "teapot",
                "source_path": "/data/glossy/teapot",
                "selection_reason": "control scene",
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
        self.assertIn("--cuda_device 0", commands)
        self.assertEqual({job["physical_gpu"] for job in jobs}, {"7"})
        self.assertEqual({job["cuda_device_arg"] for job in jobs}, {"0"})
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
        self.assertIn("--cuda_device 0", metric_commands)
        self.assertNotIn("--cuda_device 6", metric_commands)
        self.assertIn("--split both", metric_commands)
        self.assertIn("--mask_mode both", metric_commands)
        self.assertIn("--image_key pbr_rgb", metric_commands)

    def test_glossy_synthetic_paths_resolve_to_converted_root(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            glossy_root = root / "GlossySyntheticConverted"
            for scene in ["luyu", "teapot"]:
                scene_root = glossy_root / scene
                scene_root.mkdir(parents=True)
                (scene_root / "transforms_train.json").write_text("{}", encoding="utf-8")
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(root / "out"),
                    "--devices",
                    "0",
                    "--glossy_synthetic_root",
                    str(glossy_root),
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "luyu",
                    "teapot",
                    "--max_jobs",
                    "2",
                ]
            )
            jobs = runner.build_jobs(args)

        by_scene = {job["scene"]: job for job in jobs}
        self.assertEqual(by_scene["luyu"]["source_path"], str(glossy_root / "luyu"))
        self.assertEqual(by_scene["teapot"]["source_path"], str(glossy_root / "teapot"))
        self.assertIn(str(glossy_root / "luyu"), " ".join(by_scene["luyu"]["train_command"]))
        self.assertIn(str(glossy_root / "teapot"), " ".join(by_scene["teapot"]["train_command"]))

    def test_glossy_synthetic_paths_can_resolve_converted_blender_alias(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            glossy_root = root / "GlossySyntheticConverted"
            for scene in ["luyu_blender", "teapot_blender"]:
                scene_root = glossy_root / scene
                scene_root.mkdir(parents=True)
                (scene_root / "transforms_train.json").write_text("{}", encoding="utf-8")
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(root / "out"),
                    "--devices",
                    "0",
                    "--glossy_synthetic_root",
                    str(glossy_root),
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "luyu",
                    "teapot",
                    "--max_jobs",
                    "2",
                ]
            )
            jobs = runner.build_jobs(args)

        by_scene = {job["scene"]: job for job in jobs}
        self.assertEqual(by_scene["luyu"]["source_path"], str(glossy_root / "luyu_blender"))
        self.assertEqual(by_scene["teapot"]["source_path"], str(glossy_root / "teapot_blender"))

    def test_shiny_blender_synthetic_paths_remain_on_shiny_root(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(root / "out"),
                    "--devices",
                    "0",
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                ]
            )
            job = runner.build_jobs(args)[0]

        self.assertEqual(job["source_path"], "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/helmet")

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

    def test_train_command_uses_default_ref_gs_interpreter(self):
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
                    "0",
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                ]
            )
            job = runner.build_jobs(args)[0]

        self.assertEqual(job["train_command"][0], runner.DEFAULT_REF_GS_PYTHON)
        self.assertNotEqual(job["train_command"][0], "python")

    def test_train_command_uses_explicit_python_executable(self):
        runner = _load_runner()
        explicit_python = "/home/liuly/anaconda3/envs/ref_gs/bin/python"
        with tempfile.TemporaryDirectory() as tmp:
            target_csv = self._write_target_csv(Path(tmp))
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(Path(tmp) / "out"),
                    "--devices",
                    "0",
                    "--python_executable",
                    explicit_python,
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                ]
            )
            job = runner.build_jobs(args)[0]

        self.assertEqual(job["train_command"][0], explicit_python)
        for command in job["metric_commands"].values():
            self.assertEqual(command[0], explicit_python)

    def test_subprocess_env_prepends_conda_lib_and_preserves_existing_ld_path(self):
        runner = _load_runner()
        with mock.patch.dict(
            os.environ,
            {"CONDA_PREFIX": "/opt/conda/envs/ref_gs", "LD_LIBRARY_PATH": "/usr/local/cuda/lib64:/custom/lib"},
            clear=True,
        ):
            env = runner._subprocess_env("/opt/conda/envs/ref_gs/bin/python")

        self.assertEqual(
            env["LD_LIBRARY_PATH"],
            "/opt/conda/envs/ref_gs/lib:/usr/local/cuda/lib64:/custom/lib",
        )
        self.assertEqual(env["CONDA_PREFIX"], "/opt/conda/envs/ref_gs")

    def test_subprocess_env_infers_conda_prefix_from_explicit_python(self):
        runner = _load_runner()
        with mock.patch.dict(
            os.environ,
            {"CONDA_PREFIX": "/home/liuly/anaconda3", "LD_LIBRARY_PATH": "/home/liuly/anaconda3/lib"},
            clear=True,
        ):
            env = runner._subprocess_env("/home/liuly/anaconda3/envs/ref_gs/bin/python")

        self.assertEqual(env["CONDA_PREFIX"], "/home/liuly/anaconda3/envs/ref_gs")
        self.assertEqual(
            env["LD_LIBRARY_PATH"],
            "/home/liuly/anaconda3/envs/ref_gs/lib:/home/liuly/anaconda3/lib",
        )

    def test_auto_device_selects_idle_candidate_that_passes_fresh_torch_preflight(self):
        runner = _load_runner()
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            if command[0] == "nvidia-smi":
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="0, 3 MiB, 0 %\n5, 4632 MiB, 98 %\n6, 3 MiB, 0 %\n",
                    stderr="",
                )
            self.assertEqual(command[0], runner.DEFAULT_REF_GS_PYTHON)
            self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "0")
            self.assertEqual(kwargs["env"]["CONDA_PREFIX"], runner.DEFAULT_REF_GS_CONDA_PREFIX)
            self.assertTrue(kwargs["env"]["LD_LIBRARY_PATH"].startswith(f"{runner.DEFAULT_REF_GS_CONDA_PREFIX}/lib"))
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout='{"torch_cuda_available": true, "torch_device_count": 1, "device_name": "NVIDIA RTX A5000"}\n',
                stderr="",
            )

        with mock.patch.object(runner.subprocess, "run", side_effect=fake_run):
            args = runner.parse_args(
                [
                    "--devices",
                    "auto",
                    "--candidate_devices",
                    "0,5,6",
                    "--gpu_max_memory_used_mb",
                    "1000",
                    "--gpu_max_utilization",
                    "10",
                ]
            )

        self.assertEqual(args.device, "0")
        self.assertEqual(args.physical_gpu, "0")
        self.assertEqual(args.selected_device_reason, "auto_idle_cuda_preflight")
        self.assertEqual(len(args.cuda_preflight_results), 1)
        self.assertEqual(args.cuda_preflight_results[0]["decision"], "pass")
        self.assertEqual(len([call for call in calls if call[0][0] == runner.DEFAULT_REF_GS_PYTHON]), 1)

    def test_auto_device_probe_does_not_inherit_ld_library_path(self):
        runner = _load_runner()
        nvidia_smi = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="0, 3 MiB, 0 %\n",
            stderr="",
        )

        def fake_run(command, **kwargs):
            if command[0] == "nvidia-smi":
                self.assertNotIn("LD_LIBRARY_PATH", kwargs["env"])
                return nvidia_smi
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout='{"torch_cuda_available": true, "torch_device_count": 1, "device_name": "NVIDIA RTX A5000"}\n',
                stderr="",
            )

        with mock.patch.dict(os.environ, {"LD_LIBRARY_PATH": "/home/liuly/anaconda3/envs/ref_gs/lib"}, clear=True):
            with mock.patch.object(runner.subprocess, "run", side_effect=fake_run):
                device, reason, results = runner._select_auto_device(["0"], 1000, 10)

        self.assertEqual(device, "0")
        self.assertEqual(reason, "auto_idle_cuda_preflight")
        self.assertEqual(results[0]["decision"], "pass")

    def test_fresh_torch_cuda_preflight_uses_fresh_subprocess_env_before_import(self):
        runner = _load_runner()

        def fake_run(command, **kwargs):
            self.assertEqual(command[:2], [runner.DEFAULT_REF_GS_PYTHON, "-c"])
            snippet = command[2]
            self.assertIn("import torch", snippet)
            self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "2")
            self.assertEqual(kwargs["env"]["CONDA_PREFIX"], runner.DEFAULT_REF_GS_CONDA_PREFIX)
            self.assertTrue(kwargs["env"]["LD_LIBRARY_PATH"].startswith(f"{runner.DEFAULT_REF_GS_CONDA_PREFIX}/lib"))
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout='{"torch_cuda_available": true, "torch_device_count": 1, "device_name": "NVIDIA RTX A5000"}\n',
                stderr="",
            )

        with mock.patch.object(runner.subprocess, "run", side_effect=fake_run) as run:
            result = runner._fresh_torch_cuda_preflight("2", Path.cwd())

        self.assertEqual(run.call_count, 1)
        self.assertEqual(result["candidate_gpu"], "2")
        self.assertEqual(result["CUDA_VISIBLE_DEVICES"], "2")
        self.assertTrue(result["torch_cuda_available"])
        self.assertEqual(result["torch_device_count"], 1)
        self.assertEqual(result["device_name"], "NVIDIA RTX A5000")
        self.assertEqual(result["decision"], "pass")

    def test_parent_runner_does_not_import_torch_for_preflight(self):
        runner_source = Path("scripts/run_rc_refgs_quality_preserving_pilot.py").read_text(encoding="utf-8")
        parent_imports = [
            line.strip()
            for line in runner_source.splitlines()
            if line.strip() in {"import torch", "from torch import cuda"} or line.strip().startswith("import torch ")
        ]
        self.assertEqual(parent_imports, [])

    def test_auto_device_rejects_idle_candidate_that_fails_torch_preflight(self):
        runner = _load_runner()

        def fake_run(command, **kwargs):
            if command[0] == "nvidia-smi":
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="0, 3 MiB, 0 %\n1, 3 MiB, 0 %\n",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout='{"torch_cuda_available": false, "torch_device_count": 0, "device_name": ""}\n',
                stderr="",
            )

        with mock.patch.object(runner.subprocess, "run", side_effect=fake_run):
            with self.assertRaises(SystemExit) as caught:
                runner._select_auto_device(["0", "1"], 1000, 10)

        self.assertIn("no idle candidate GPU passed fresh torch CUDA preflight", str(caught.exception))

    def test_trust_manual_cuda_preflight_rejects_auto_devices(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            target_csv = self._write_target_csv(Path(tmp))
            with mock.patch.object(runner, "_select_auto_device", return_value=("0", "auto_idle_cuda_preflight", [])):
                with mock.patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"}, clear=True):
                    with self.assertRaises(SystemExit) as caught:
                        runner.parse_args(
                            [
                                "--target_csv",
                                str(target_csv),
                                "--output_root",
                                str(Path(tmp) / "out"),
                                "--devices",
                                "auto",
                                "--candidate_devices",
                                "0",
                                "--trust_manual_cuda_preflight",
                                "YES",
                                "--execute",
                                "--confirm_execute",
                                "YES",
                            ]
                        )

        self.assertIn("--trust_manual_cuda_preflight requires explicit --devices", str(caught.exception))

    def test_trust_manual_cuda_preflight_rejects_missing_cuda_visible_devices(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            target_csv = self._write_target_csv(Path(tmp))
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(SystemExit) as caught:
                    runner.parse_args(
                        [
                            "--target_csv",
                            str(target_csv),
                            "--output_root",
                            str(Path(tmp) / "out"),
                            "--devices",
                            "0",
                            "--trust_manual_cuda_preflight",
                            "YES",
                            "--execute",
                            "--confirm_execute",
                            "YES",
                        ]
                    )

        self.assertIn("requires parent CUDA_VISIBLE_DEVICES", str(caught.exception))

    def test_trust_manual_cuda_preflight_rejects_mismatched_cuda_visible_devices(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            target_csv = self._write_target_csv(Path(tmp))
            with mock.patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "1"}, clear=True):
                with self.assertRaises(SystemExit) as caught:
                    runner.parse_args(
                        [
                            "--target_csv",
                            str(target_csv),
                            "--output_root",
                            str(Path(tmp) / "out"),
                            "--devices",
                            "0",
                            "--trust_manual_cuda_preflight",
                            "YES",
                            "--execute",
                            "--confirm_execute",
                            "YES",
                        ]
                    )

        self.assertIn("must match explicit --devices", str(caught.exception))

    def test_trust_manual_cuda_preflight_passes_and_skips_fresh_cuda_preflight(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            with mock.patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"}, clear=True):
                args = runner.parse_args(
                    [
                        "--target_csv",
                        str(target_csv),
                        "--output_root",
                        str(root / "out"),
                        "--devices",
                        "0",
                        "--trust_manual_cuda_preflight",
                        "YES",
                        "--variants",
                        "rc_qp_lam010",
                        "--scenes",
                        "helmet",
                        "--max_jobs",
                        "1",
                        "--execute",
                        "--confirm_execute",
                        "YES",
                    ]
                )
            job = runner.build_jobs(args)[0]
            manual_result = {
                "status": "completed",
                "decision": "pass",
                "return_code": 0,
                "stdout": '{"CUDA_VISIBLE_DEVICES":"0","torch_cuda_available":true,"torch_device_count":1,"device_name":"GPU"}\n',
                "stderr": "",
                "CUDA_VISIBLE_DEVICES": "0",
                "torch_cuda_available": True,
                "torch_device_count": 1,
                "device_name": "GPU",
            }

            with mock.patch.object(runner, "_validate_source_path", return_value={"status": "completed"}):
                with mock.patch.object(runner, "_manual_cuda_preflight", return_value=manual_result) as manual:
                    with mock.patch.object(runner, "_fresh_torch_cuda_preflight") as fresh:
                        with mock.patch.object(runner, "_preflight_env", return_value={"status": "completed"}):
                            with mock.patch.object(runner, "_run_captured", return_value={"status": "completed", "return_code": 0}) as train_run:
                                with mock.patch.object(runner, "_run", return_value=("completed", 0)) as metric_run:
                                    with mock.patch.object(runner, "_expected_artifacts_before_summary", return_value=[]):
                                        status = runner._execute_job(job, args, Path.cwd())
            summary = json.loads((Path(job["model_path"]) / "launcher_summary.json").read_text(encoding="utf-8"))

        self.assertEqual(status["status"], "completed")
        manual.assert_called_once()
        self.assertFalse(fresh.called)
        self.assertEqual(job["train_command"][job["train_command"].index("--cuda_device") + 1], "0")
        for command in job["metric_commands"].values():
            self.assertEqual(command[command.index("--cuda_device") + 1], "0")
        train_run.assert_called_once()
        self.assertGreaterEqual(metric_run.call_count, 3)
        self.assertEqual(summary["manual_cuda_preflight"]["decision"], "pass")
        self.assertEqual(summary["preflight_env"]["manual_cuda_preflight"]["decision"], "pass")

    def test_trust_manual_cuda_preflight_failure_blocks_train_and_writes_status(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            with mock.patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"}, clear=True):
                args = runner.parse_args(
                    [
                        "--target_csv",
                        str(target_csv),
                        "--output_root",
                        str(root / "out"),
                        "--devices",
                        "0",
                        "--trust_manual_cuda_preflight",
                        "YES",
                        "--variants",
                        "rc_qp_lam010",
                        "--scenes",
                        "helmet",
                        "--max_jobs",
                        "1",
                        "--execute",
                        "--confirm_execute",
                        "YES",
                    ]
                )
            job = runner.build_jobs(args)[0]
            manual_result = {
                "status": "failed",
                "decision": "fail",
                "return_code": 1,
                "stdout": '{"CUDA_VISIBLE_DEVICES":"0","torch_cuda_available":false,"torch_device_count":0}\n',
                "stderr": "cuda unavailable",
                "CUDA_VISIBLE_DEVICES": "0",
                "torch_cuda_available": False,
                "torch_device_count": 0,
            }

            with mock.patch.object(runner, "_validate_source_path", return_value={"status": "completed"}):
                with mock.patch.object(runner, "_manual_cuda_preflight", return_value=manual_result):
                    with mock.patch.object(runner, "_fresh_torch_cuda_preflight") as fresh:
                        with mock.patch.object(runner, "_preflight_env") as env_preflight:
                            with mock.patch.object(runner, "_run_captured") as train_run:
                                status = runner._execute_job(job, args, Path.cwd())
            summary = json.loads((Path(job["model_path"]) / "launcher_summary.json").read_text(encoding="utf-8"))

        self.assertEqual(status["status"], "failed")
        self.assertEqual(status["failed_step"], "manual_cuda_preflight")
        self.assertFalse(fresh.called)
        self.assertFalse(env_preflight.called)
        self.assertFalse(train_run.called)
        self.assertEqual(summary["failed_step"], "manual_cuda_preflight")
        self.assertEqual(summary["manual_cuda_preflight"]["stderr"], "cuda unavailable")

    def test_explicit_device_uses_fresh_torch_preflight_before_train(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(root / "out"),
                    "--devices",
                    "5",
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                    "--execute",
                    "--confirm_execute",
                    "YES",
                ]
            )
            job = runner.build_jobs(args)[0]

            with mock.patch.object(
                runner,
                "_fresh_torch_cuda_preflight",
                return_value={
                    "candidate_gpu": "5",
                    "CUDA_VISIBLE_DEVICES": "5",
                    "return_code": 0,
                    "stdout": '{"torch_cuda_available": true, "torch_device_count": 1, "device_name": "NVIDIA GeForce RTX 3090 Ti"}',
                    "stderr": "",
                    "torch_cuda_available": True,
                    "torch_device_count": 1,
                    "device_name": "NVIDIA GeForce RTX 3090 Ti",
                    "decision": "pass",
                },
            ) as preflight:
                with mock.patch.object(runner, "_validate_source_path", return_value={"status": "completed"}):
                    with mock.patch.object(runner, "_preflight_env", return_value={"status": "completed"}):
                        with mock.patch.object(runner, "_run_captured", return_value={"status": "completed", "return_code": 0}) as train_run:
                            with mock.patch.object(runner, "_run", return_value=("completed", 0)) as metric_run:
                                with mock.patch.object(runner, "_expected_artifacts_before_summary", return_value=[]):
                                    status = runner._execute_job(job, args, Path.cwd())

        self.assertEqual(status["status"], "completed")
        preflight.assert_called_once()
        self.assertEqual(preflight.call_args.args[0], "5")
        self.assertEqual(job["train_command"][job["train_command"].index("--cuda_device") + 1], "0")
        train_run.assert_called_once()
        self.assertGreaterEqual(metric_run.call_count, 3)

    def test_preflight_failure_prevents_train_execution_and_writes_status(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            output_root = root / "out"
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(output_root),
                    "--devices",
                    "0",
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                    "--execute",
                    "--confirm_execute",
                    "YES",
                ]
            )
            job = runner.build_jobs(args)[0]

            with mock.patch.object(
                runner,
                "_fresh_torch_cuda_preflight",
                return_value={
                    "candidate_gpu": "0",
                    "CUDA_VISIBLE_DEVICES": "0",
                    "return_code": 0,
                    "stdout": '{"torch_cuda_available": true, "torch_device_count": 1, "device_name": "NVIDIA RTX A5000"}',
                    "stderr": "",
                    "torch_cuda_available": True,
                    "torch_device_count": 1,
                    "device_name": "NVIDIA RTX A5000",
                    "decision": "pass",
                },
            ):
                with mock.patch.object(runner, "_preflight_env", return_value={"status": "failed", "return_code": 2, "stdout": "", "stderr": "missing conda"}):
                    with mock.patch.object(runner, "_run") as run:
                        status = runner._execute_job(job, args, Path.cwd())

            self.assertFalse(run.called)
            self.assertEqual(status["status"], "failed")
            self.assertEqual(status["failed_step"], "preflight_env")
            model_path = Path(job["model_path"])
            summary = json.loads((model_path / "launcher_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "failed")
            self.assertEqual(summary["failed_step"], "preflight_env")
            self.assertEqual(summary["preflight_env"]["stderr"], "missing conda")

    def test_failed_source_path_validation_blocks_train(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            missing_root = root / "missing_glossy"
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(root / "out"),
                    "--devices",
                    "0",
                    "--glossy_synthetic_root",
                    str(missing_root),
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "luyu",
                    "--max_jobs",
                    "1",
                    "--execute",
                    "--confirm_execute",
                    "YES",
                ]
            )
            job = runner.build_jobs(args)[0]
            with mock.patch.object(runner, "_fresh_torch_cuda_preflight") as cuda_preflight:
                with mock.patch.object(runner, "_preflight_env") as env_preflight:
                    with mock.patch.object(runner, "_run") as run:
                        status = runner._execute_job(job, args, Path.cwd())

            self.assertEqual(status["status"], "failed")
            self.assertEqual(status["failed_step"], "source_path_validation")
            self.assertFalse(cuda_preflight.called)
            self.assertFalse(env_preflight.called)
            self.assertFalse(run.called)
            summary = json.loads((Path(job["model_path"]) / "launcher_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["failed_step"], "source_path_validation")
            self.assertEqual(summary["source_path_validation"]["status"], "failed")

    def test_failed_train_records_stdout_and_stderr_tail(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            glossy_root = root / "GlossySyntheticConverted"
            scene_root = glossy_root / "luyu"
            scene_root.mkdir(parents=True)
            (scene_root / "transforms_train.json").write_text("{}", encoding="utf-8")
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(root / "out"),
                    "--devices",
                    "0",
                    "--glossy_synthetic_root",
                    str(glossy_root),
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "luyu",
                    "--max_jobs",
                    "1",
                    "--execute",
                    "--confirm_execute",
                    "YES",
                ]
            )
            job = runner.build_jobs(args)[0]
            with mock.patch.object(
                runner,
                "_fresh_torch_cuda_preflight",
                return_value={
                    "candidate_gpu": "0",
                    "CUDA_VISIBLE_DEVICES": "0",
                    "return_code": 0,
                    "stdout": "{}",
                    "stderr": "",
                    "torch_cuda_available": True,
                    "torch_device_count": 1,
                    "device_name": "NVIDIA RTX A5000",
                    "decision": "pass",
                },
            ):
                with mock.patch.object(runner, "_preflight_env", return_value={"status": "completed"}):
                    with mock.patch.object(
                        runner,
                        "_run_captured",
                        return_value={
                            "status": "failed",
                            "return_code": 7,
                            "stdout_tail": "stdout tail",
                            "stderr_tail": "stderr tail",
                            "command": "train command",
                        },
                    ):
                        status = runner._execute_job(job, args, Path.cwd())

            self.assertEqual(status["failed_step"], "train")
            summary = json.loads((Path(job["model_path"]) / "launcher_summary.json").read_text(encoding="utf-8"))
            train_result = summary["command_results"]["train"]
            self.assertEqual(train_result["return_code"], 7)
            self.assertEqual(train_result["stdout_tail"], "stdout tail")
            self.assertEqual(train_result["stderr_tail"], "stderr tail")
            self.assertEqual(train_result["source_path"], str(scene_root))
            self.assertEqual(train_result["env_CUDA_VISIBLE_DEVICES"], "0")

    def test_launcher_summary_records_environment_info(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(root / "out"),
                    "--devices",
                    "0",
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                ]
            )
            job = runner.build_jobs(args)[0]
            env = {
                "CONDA_PREFIX": "/opt/conda/envs/ref_gs",
                "LD_LIBRARY_PATH": "/opt/conda/envs/ref_gs/lib:/usr/local/cuda/lib64",
            }
            runner._write_job_summary(Path(job["model_path"]), job, "dry_run", args, subprocess_env=env)

            summary = json.loads((Path(job["model_path"]) / "launcher_summary.json").read_text(encoding="utf-8"))

        self.assertEqual(summary["environment"]["sys_executable"], sys.executable)
        self.assertEqual(summary["environment"]["conda_prefix"], "/opt/conda/envs/ref_gs")
        self.assertEqual(summary["environment"]["ld_library_path_prefix"], "/opt/conda/envs/ref_gs/lib")
        self.assertEqual(summary["environment_notes"]["mapping_policy"], "external CUDA_VISIBLE_DEVICES=<physical_gpu>; train and metrics use --cuda_device 0")
        self.assertEqual(summary["job"]["physical_gpu"], "0")
        self.assertEqual(summary["job"]["cuda_device_arg"], "0")

    def test_failed_preflight_status_is_not_complete(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            model_path = Path(tmp) / "model"
            iteration_dir = model_path / "point_cloud" / "iteration_1000"
            iteration_dir.mkdir(parents=True)
            (iteration_dir / "point_cloud.ply").write_text("ply\n", encoding="utf-8")
            (model_path / "reflection_consistency_train.json").write_text("{}", encoding="utf-8")
            (model_path / "reflection_consistency_test.json").write_text("{}", encoding="utf-8")
            (model_path / "render_quality_both_iter1000.json").write_text("{}", encoding="utf-8")
            (model_path / "launcher_summary.json").write_text(
                '{"status":"failed","failed_step":"preflight_env"}\n',
                encoding="utf-8",
            )

            self.assertFalse(runner._is_complete(model_path, 1000))

    def test_dry_run_remains_non_executing_after_preflight_addition(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            output_root = root / "out"
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(output_root),
                    "--devices",
                    "0",
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "helmet",
                    "--max_jobs",
                    "1",
                ]
            )
            job = runner.build_jobs(args)[0]
            with mock.patch.object(runner, "_preflight_env") as preflight:
                with mock.patch.object(runner, "_run") as run:
                    status = runner._execute_job(job, args, Path.cwd())

            self.assertEqual(status["status"], "dry_run")
            self.assertFalse(preflight.called)
            self.assertFalse(run.called)

    def test_max_jobs_one_limits_runtime_smoke_to_one_job(self):
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
                    "0",
                    "--variants",
                    "rc_qp_lam005",
                    "rc_qp_lam010",
                    "--smoke",
                    "--smoke_iterations",
                    "1000",
                    "--max_jobs",
                    "1",
                    "--execute",
                    "--confirm_execute",
                    "YES",
                ]
            )
            jobs = runner.build_jobs(args)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["iterations"], 1000)

    def test_retry_can_target_only_luyu_and_teapot_with_max_jobs_two(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_csv = self._write_target_csv(root)
            glossy_root = root / "GlossySyntheticConverted"
            for scene in ["luyu", "teapot"]:
                scene_root = glossy_root / scene
                scene_root.mkdir(parents=True)
                (scene_root / "transforms_train.json").write_text("{}", encoding="utf-8")
            args = runner.parse_args(
                [
                    "--target_csv",
                    str(target_csv),
                    "--output_root",
                    str(root / "out"),
                    "--devices",
                    "0",
                    "--glossy_synthetic_root",
                    str(glossy_root),
                    "--variants",
                    "rc_qp_lam010",
                    "--scenes",
                    "luyu",
                    "teapot",
                    "--max_jobs",
                    "2",
                ]
            )
            jobs = runner.build_jobs(args)

        self.assertEqual(len(jobs), 2)
        self.assertEqual({job["scene"] for job in jobs}, {"luyu", "teapot"})
        self.assertEqual({job["dataset"] for job in jobs}, {"glossy_synthetic"})


if __name__ == "__main__":
    unittest.main()
