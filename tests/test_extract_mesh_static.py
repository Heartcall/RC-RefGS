import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ExtractMeshStaticTests(unittest.TestCase):
    def test_extract_mesh_entrypoint_contract(self):
        script = Path("extract_mesh.py")
        self.assertTrue(script.exists(), "extract_mesh.py is missing")

        source = script.read_text()
        required_snippets = [
            "from arguments import ModelParams, PipelineParams, get_combined_args",
            "from gaussian_renderer import render",
            "from scene import Scene, GaussianModel",
            "from utils.mesh_utils import GaussianExtractor, post_process_mesh",
            "def _expected_point_cloud_dir(",
            "def _validate_inputs(",
            "def _write_summary(",
            "ModelParams(parser, sentinel=True)",
            "PipelineParams(parser)",
            "get_combined_args(parser)",
            'parser.add_argument("--iteration"',
            'parser.add_argument("--output_mesh"',
            'parser.add_argument("--dry_run"',
            'parser.add_argument("--check_imports"',
            'parser.add_argument("--check_open3d"',
            '"mesh_extraction"',
            '"missing_inputs"',
            '"open3d_info"',
            "extract_mesh_bounded(",
            "post_process_mesh(",
            "o3d.io.write_triangle_mesh",
        ]

        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_extract_mesh_dry_run_summary_reports_expected_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            model_path = tmpdir_path / "model"
            point_cloud_dir = model_path / "point_cloud" / "iteration_300"
            point_cloud_dir.mkdir(parents=True)
            (point_cloud_dir / "point_cloud.ply").write_text("ply\n", encoding="utf-8")
            (model_path / "cfg_args").write_text(
                "Namespace(model_path={!r}, source_path={!r}, sh_degree=3, "
                "white_background=False, images='images', resolution=-1, "
                "data_device='cuda', eval=True, run_dim=256, albedo_bias=0, "
                "gsrgb_loss=False, rand_init=False, init_until_iter=0, "
                "env_scope_center=[0.0, 0.0, 0.0], env_scope_radius=0.0, "
                "alpha_weight=0.0, depth_tv_weight=0.0, density_weight=0.0, "
                "tv_weight=0.0, xyz_axis=[0.0, 0.0, 0.0])".format(
                    str(model_path), str(tmpdir_path / "source")
                ),
                encoding="utf-8",
            )
            summary_json = tmpdir_path / "summary.json"
            output_mesh = tmpdir_path / "mesh_iter300.ply"

            result = subprocess.run(
                [
                    sys.executable,
                    "extract_mesh.py",
                    "--model_path",
                    str(model_path),
                    "--iteration",
                    "300",
                    "--output_mesh",
                    str(output_mesh),
                    "--summary_json",
                    str(summary_json),
                    "--dry_run",
                    "--check_imports",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(summary_json.exists(), "dry run did not write summary_json")
            summary = json.loads(summary_json.read_text())
            self.assertEqual(summary["mode"], "mesh_extraction")
            self.assertTrue(summary["dry_run"])
            self.assertTrue(summary["imports_checked"])
            self.assertEqual(summary["iteration"], 300)
            self.assertEqual(summary["model_path"], str(model_path))
            self.assertEqual(summary["output_mesh"], str(output_mesh))
            self.assertEqual(summary["missing_inputs"], [])
            self.assertIn("point_cloud.ply", "\n".join(summary["expected_inputs"]))

    def test_extract_mesh_open3d_preflight_is_non_crashing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            model_path = tmpdir_path / "model"
            point_cloud_dir = model_path / "point_cloud" / "iteration_300"
            point_cloud_dir.mkdir(parents=True)
            (point_cloud_dir / "point_cloud.ply").write_text("ply\n", encoding="utf-8")
            (model_path / "cfg_args").write_text(
                "Namespace(model_path={!r}, source_path={!r}, sh_degree=3, "
                "white_background=False, images='images', resolution=-1, "
                "data_device='cuda', eval=True, run_dim=256, albedo_bias=0, "
                "gsrgb_loss=False, rand_init=False, init_until_iter=0, "
                "env_scope_center=[0.0, 0.0, 0.0], env_scope_radius=0.0, "
                "alpha_weight=0.0, depth_tv_weight=0.0, density_weight=0.0, "
                "tv_weight=0.0, xyz_axis=[0.0, 0.0, 0.0])".format(
                    str(model_path), str(tmpdir_path / "source")
                ),
                encoding="utf-8",
            )
            summary_json = tmpdir_path / "summary.json"

            result = subprocess.run(
                [
                    sys.executable,
                    "extract_mesh.py",
                    "--model_path",
                    str(model_path),
                    "--iteration",
                    "300",
                    "--summary_json",
                    str(summary_json),
                    "--dry_run",
                    "--check_open3d",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(summary_json.read_text())
            self.assertIn("open3d_info", summary)
            self.assertIn("checked", summary["open3d_info"])
            self.assertTrue(summary["open3d_info"]["checked"])
            self.assertIn("ok", summary["open3d_info"])
            self.assertIn("recommended_ld_library_path_prefix", summary["open3d_info"])

    def test_extract_mesh_dry_run_can_emit_runtime_command_plan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            model_path = tmpdir_path / "model"
            point_cloud_dir = model_path / "point_cloud" / "iteration_300"
            point_cloud_dir.mkdir(parents=True)
            (point_cloud_dir / "point_cloud.ply").write_text("ply\n", encoding="utf-8")
            (model_path / "cfg_args").write_text(
                "Namespace(model_path={!r}, source_path={!r}, sh_degree=3, "
                "white_background=False, images='images', resolution=-1, "
                "data_device='cuda', eval=True, run_dim=256, albedo_bias=0, "
                "gsrgb_loss=False, rand_init=False, init_until_iter=0, "
                "env_scope_center=[0.0, 0.0, 0.0], env_scope_radius=0.0, "
                "alpha_weight=0.0, depth_tv_weight=0.0, density_weight=0.0, "
                "tv_weight=0.0, xyz_axis=[0.0, 0.0, 0.0])".format(
                    str(model_path), str(tmpdir_path / "source")
                ),
                encoding="utf-8",
            )
            summary_json = tmpdir_path / "summary.json"
            output_mesh = tmpdir_path / "mesh_iter300.ply"

            result = subprocess.run(
                [
                    sys.executable,
                    "extract_mesh.py",
                    "--model_path",
                    str(model_path),
                    "--iteration",
                    "300",
                    "--output_mesh",
                    str(output_mesh),
                    "--summary_json",
                    str(summary_json),
                    "--dry_run",
                    "--check_open3d",
                    "--emit_runtime_command",
                    "--cuda_device",
                    "0",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(summary_json.read_text())
            command_plan = summary["runtime_command_plan"]
            self.assertTrue(command_plan["requires_explicit_runtime_allocation"])
            self.assertIn("LD_LIBRARY_PATH", command_plan["environment"])
            self.assertIn("extract_mesh.py", " ".join(command_plan["argv"]))
            self.assertIn("--cuda_device", command_plan["argv"])
            self.assertIn("0", command_plan["argv"])
            self.assertNotIn("--dry_run", command_plan["argv"])
            self.assertNotIn("--check_open3d", command_plan["argv"])
            self.assertNotIn("--emit_runtime_command", command_plan["argv"])
            self.assertEqual(command_plan["output_mesh"], str(output_mesh))


if __name__ == "__main__":
    unittest.main()
