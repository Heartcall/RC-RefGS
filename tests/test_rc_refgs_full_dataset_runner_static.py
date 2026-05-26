import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class FullDatasetRunnerStaticTests(unittest.TestCase):
    @staticmethod
    def _write_minimal_blender_scene(scene_dir: Path) -> None:
        train_dir = scene_dir / "train"
        test_dir = scene_dir / "test"
        train_dir.mkdir(parents=True, exist_ok=True)
        test_dir.mkdir(parents=True, exist_ok=True)
        (train_dir / "r_0.png").write_text("", encoding="utf-8")
        (test_dir / "r_0.png").write_text("", encoding="utf-8")
        payload = (
            '{"camera_angle_x":0.5,"frames":[{"file_path":"./train/r_0","transform_matrix":'
            "[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}]}"
        )
        (scene_dir / "transforms_train.json").write_text(payload, encoding="utf-8")
        payload_test = (
            '{"camera_angle_x":0.5,"frames":[{"file_path":"./test/r_0","transform_matrix":'
            "[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}]}"
        )
        (scene_dir / "transforms_test.json").write_text(payload_test, encoding="utf-8")

    def test_runner_exists_is_executable_and_has_safe_shell_preamble(self):
        runner = Path("scripts/run_rc_refgs_full_dataset_all_experiments.sh")
        self.assertTrue(runner.exists(), "full-dataset runner is missing")
        mode = runner.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR, "runner is not user-executable")
        source = runner.read_text(encoding="utf-8")
        self.assertIn("#!/usr/bin/env bash", source)
        self.assertIn("set -euo pipefail", source)

    def test_runner_help_and_dry_run_safety_contract(self):
        runner = Path("scripts/run_rc_refgs_full_dataset_all_experiments.sh")
        source = runner.read_text(encoding="utf-8")
        required_snippets = [
            "--help",
            "DRY_RUN=1",
            "--execute",
            "--confirm_full_dataset_execute",
            'CONFIRM_FULL_DATASET_EXECUTE=""',
            '[[ "${CONFIRM_FULL_DATASET_EXECUTE}" == "YES" ]]',
            "Default mode is dry-run",
            "dry-run",
            "Refusing execution",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_runner_requires_complete_dataset_roots_and_conversion_check(self):
        runner = Path("scripts/run_rc_refgs_full_dataset_all_experiments.sh")
        source = runner.read_text(encoding="utf-8")
        required_snippets = [
            "--shiny_blender_synthetic_root",
            "--shiny_blender_real_root",
            "--glossy_synthetic_root",
            "shiny_blender_synthetic",
            "shiny_blender_real",
            "glossy_synthetic",
            "Shiny Blender Synthetic",
            "Shiny Blender Real",
            "Glossy Synthetic",
            "teapot/toaster/car",
            "subset evidence only",
            "transforms_train.json",
            "transforms_test.json",
            "blender_scene_trainable",
            "colmap/sparse",
            "nero2blender.py",
            "needs conversion",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_runner_uses_direct_launcher_and_avoids_cuda_visible_devices(self):
        runner = Path("scripts/run_rc_refgs_full_dataset_all_experiments.sh")
        source = runner.read_text(encoding="utf-8")
        self.assertIn("scripts/run_rc_refgs_ablation_direct.py", source)
        self.assertIn("--cuda_device", source)
        self.assertIn("--summary_json", source)
        self.assertIn("--dry_run", source)
        self.assertNotIn("scripts/run_rc_refgs_ablation.sh", source)
        self.assertNotIn("CUDA_VISIBLE_DEVICES=", source)

    def test_runner_tracks_completion_and_status_outputs(self):
        runner = Path("scripts/run_rc_refgs_full_dataset_all_experiments.sh")
        source = runner.read_text(encoding="utf-8")
        required_snippets = [
            "point_cloud/iteration_${ITERATIONS}/point_cloud.ply",
            "reflection_consistency_train.json",
            "reflection_consistency_test.json",
            "launcher_summary.json",
            "full_dataset_run_status.json",
            "full_dataset_run_status.md",
            "--force_rerun",
            "--rerun_failed",
            "--resume_existing",
            "--skip_train",
            "SKIP_COMPLETED=1",
            "jobs_per_gpu",
            "${OUTPUT_ROOT}/${dataset_name}/${scene}/${variant}/seed_${seed}",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_runner_help_executes_without_training(self):
        runner = Path("scripts/run_rc_refgs_full_dataset_all_experiments.sh")
        result = subprocess.run(
            [str(runner), "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Default mode is dry-run", result.stdout)
        self.assertIn("--confirm_full_dataset_execute YES", result.stdout)

    def test_nonexistent_roots_fail_before_training(self):
        runner = Path("scripts/run_rc_refgs_full_dataset_all_experiments.sh")
        result = subprocess.run(
            [
                str(runner),
                "--shiny_blender_synthetic_root",
                "/tmp/does-not-exist-shiny-syn",
                "--shiny_blender_real_root",
                "/tmp/does-not-exist-shiny-real",
                "--glossy_synthetic_root",
                "/tmp/does-not-exist-glossy-syn",
                "--output_root",
                "/tmp/rc-refgs-full-dataset-runner-test",
                "--devices",
                "0",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing", result.stderr.lower())
        self.assertNotIn("run_rc_refgs_ablation_direct.py", result.stdout)

    def test_dataset_root_inference_supports_converted_layout(self):
        runner = Path("scripts/run_rc_refgs_full_dataset_all_experiments.sh")
        with tempfile.TemporaryDirectory(prefix="rc_refgs_dataset_root_test_") as tmp:
            dataset_root = Path(tmp) / "dataset"
            output_root = Path(tmp) / "out"
            self._write_minimal_blender_scene(dataset_root / "refnerf_synthetic" / "teapot")
            self._write_minimal_blender_scene(dataset_root / "refnerf_real" / "bear")
            glossy_scene = dataset_root / "GlossySyntheticConverted" / "angel_blender"
            self._write_minimal_blender_scene(glossy_scene)

            result = subprocess.run(
                [
                    str(runner),
                    "--dataset_root",
                    str(dataset_root),
                    "--output_root",
                    str(output_root),
                    "--devices",
                    "0",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            status_json = output_root / "full_dataset_run_status.json"
            status_md = output_root / "full_dataset_run_status.md"
            self.assertTrue(status_json.exists(), "status json missing")
            self.assertTrue(status_md.exists(), "status markdown missing")
            self.assertIn("DRY-RUN", result.stdout)

    def test_dry_run_expands_shiny_real_colmap_sparse_schema_variants(self):
        runner = Path("scripts/run_rc_refgs_full_dataset_all_experiments.sh")
        with tempfile.TemporaryDirectory(prefix="rc_refgs_shiny_real_schema_") as tmp:
            root = Path(tmp)
            output_root = root / "out"

            self._write_minimal_blender_scene(root / "syn" / "chair")
            self._write_minimal_blender_scene(root / "glossy_syn" / "angel_blender")

            shiny_real_root = root / "real"
            for scene in ("bear", "bunny", "coral"):
                sparse_root = shiny_real_root / scene / "sparse" / "0"
                sparse_root.mkdir(parents=True, exist_ok=True)
                (sparse_root / "images.txt").write_text("", encoding="utf-8")
                (shiny_real_root / scene / "images").mkdir(parents=True, exist_ok=True)
                (shiny_real_root / scene / "images" / "000.jpg").write_text("", encoding="utf-8")
            for scene in ("maneki", "vase"):
                sparse_root = shiny_real_root / scene / "colmap" / "sparse" / "0"
                sparse_root.mkdir(parents=True, exist_ok=True)
                (sparse_root / "images.txt").write_text("", encoding="utf-8")
                (shiny_real_root / scene / "images").mkdir(parents=True, exist_ok=True)
                (shiny_real_root / scene / "images" / "000.jpg").write_text("", encoding="utf-8")

            result = subprocess.run(
                [
                    str(runner),
                    "--shiny_blender_synthetic_root",
                    str(root / "syn"),
                    "--shiny_blender_real_root",
                    str(shiny_real_root),
                    "--glossy_synthetic_root",
                    str(root / "glossy_syn"),
                    "--output_root",
                    str(output_root),
                    "--devices",
                    "0",
                    "--seeds",
                    "0",
                    "--iterations",
                    "31000",
                    "--variants",
                    "base,rc",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            status_json = output_root / "full_dataset_run_status.json"
            self.assertTrue(status_json.exists(), "status json missing")
            payload = status_json.read_text(encoding="utf-8")
            self.assertIn('"scene": "maneki"', payload)
            self.assertIn('"scene": "vase"', payload)
            self.assertIn('"scene": "bear"', payload)
            self.assertIn('"scene": "bunny"', payload)
            self.assertIn('"scene": "coral"', payload)
            self.assertIn('"status": "planned"', payload)
            self.assertIn("DRY-RUN would run:", result.stdout)


if __name__ == "__main__":
    unittest.main()
