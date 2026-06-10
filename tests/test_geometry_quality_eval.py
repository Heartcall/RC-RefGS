import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_ascii_ply(path, vertices):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("ply\n")
        handle.write("format ascii 1.0\n")
        handle.write(f"element vertex {len(vertices)}\n")
        handle.write("property float x\n")
        handle.write("property float y\n")
        handle.write("property float z\n")
        handle.write("end_header\n")
        for x, y, z in vertices:
            handle.write(f"{x} {y} {z}\n")


class GeometryQualityEvalTests(unittest.TestCase):
    def test_missing_gt_blocks_true_depth_normal_and_mesh_metrics_but_keeps_proxy_metrics(self):
        from metrics.geometry_quality_eval import evaluate_model_geometry

        with tempfile.TemporaryDirectory() as tmpdir:
            model = Path(tmpdir) / "model"
            (model / "point_cloud" / "iteration_31000").mkdir(parents=True)
            _write_ascii_ply(model / "point_cloud" / "iteration_31000" / "point_cloud.ply", [(0, 0, 0), (1, 0, 0)])
            _write_ascii_ply(model / "input.ply", [(0, 0, 0)])
            (model / "reflection_consistency_test.json").write_text(
                json.dumps({"mean_reflection_consistency": 0.2}) + "\n"
            )
            (model / "render_quality_both_iter31000.json").write_text(
                json.dumps(
                    {
                        "image_key": "pbr_rgb",
                        "mask_mode": "both",
                        "splits": {
                            "test": {
                                "full_psnr": 1.0,
                                "full_ssim": 0.5,
                                "full_lpips": 0.25,
                                "reflective_psnr": 2.0,
                                "reflective_ssim": 0.6,
                                "reflective_lpips": 0.2,
                            }
                        },
                    }
                )
                + "\n"
            )

            row = evaluate_model_geometry(
                dataset="shiny_blender_synthetic",
                scene="helmet",
                variant="base",
                model_path=model,
                iteration=31000,
            )

            self.assertEqual(row["status"], "proxy_only")
            self.assertFalse(row["true_depth_metrics_computed"])
            self.assertFalse(row["true_normal_metrics_computed"])
            self.assertFalse(row["true_mesh_metrics_computed"])
            self.assertEqual(row["geometry_proxy_vertex_count"], 2)
            self.assertEqual(row["geometry_proxy_input_vertex_count"], 1)
            self.assertIn("missing_gt_depth", row["unavailable_reasons"])
            self.assertIn("normal_coordinate_space_unverified", row["unavailable_reasons"])
            self.assertIn("missing_gt_mesh_or_point_cloud", row["unavailable_reasons"])

    def test_cli_writes_required_csv_columns_and_excludes_shiny_real(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            model = root / "outputs" / "shiny_blender_synthetic" / "helmet" / "base" / "seed_0"
            (model / "point_cloud" / "iteration_31000").mkdir(parents=True)
            _write_ascii_ply(model / "point_cloud" / "iteration_31000" / "point_cloud.ply", [(0, 0, 0)])

            out_json = root / "geometry.json"
            out_csv = root / "geometry.csv"
            out_md = root / "geometry.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "metrics" / "geometry_quality_eval.py"),
                    "--model_roots",
                    str(root / "outputs"),
                    "--scenes",
                    "helmet",
                    "--variants",
                    "base",
                    "--output_json",
                    str(out_json),
                    "--output_csv",
                    str(out_csv),
                    "--output_md",
                    str(out_md),
                ],
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            report = json.loads(out_json.read_text())
            self.assertEqual(report["claim_boundary"], "Proxy diagnostics only; no mesh/surface improvement claim.")
            self.assertNotIn("shiny_blender_real", json.dumps(report))

            with open(out_csv, newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            for column in [
                "dataset",
                "scene",
                "variant",
                "status",
                "true_depth_metrics_computed",
                "true_normal_metrics_computed",
                "true_mesh_metrics_computed",
                "geometry_proxy_vertex_count",
            ]:
                self.assertIn(column, rows[0])


if __name__ == "__main__":
    unittest.main()
