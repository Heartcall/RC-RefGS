import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_ascii_ply(path, vertex_count=3):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("ply\n")
        handle.write("format ascii 1.0\n")
        handle.write(f"element vertex {vertex_count}\n")
        handle.write("property float x\n")
        handle.write("property float y\n")
        handle.write("property float z\n")
        handle.write("end_header\n")
        for index in range(vertex_count):
            handle.write(f"{index} 0 0\n")


class GeometrySignalInventoryTests(unittest.TestCase):
    def test_inventory_cli_reports_available_signals_without_shiny_real_or_raw_train_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            shiny = root / "Shiny Blender Synthetic" / "helmet"
            glossy = root / "GlossySyntheticConverted" / "luyu_blender"
            model = root / "outputs" / "shiny_blender_synthetic" / "helmet" / "base" / "seed_0"
            (shiny / "train").mkdir(parents=True)
            (shiny / "test").mkdir(parents=True)
            (glossy).mkdir(parents=True)
            (model / "point_cloud" / "iteration_31000").mkdir(parents=True)
            (shiny / "transforms_train.json").write_text("{}\n")
            (shiny / "test" / "r_0_normal.png").write_text("not_an_image\n")
            (glossy / "transforms_train.json").write_text("{}\n")
            _write_ascii_ply(glossy / "points3d.ply")
            _write_ascii_ply(model / "point_cloud" / "iteration_31000" / "point_cloud.ply")
            (model / "reflection_consistency_train.json").write_text(
                json.dumps({"mean_reflection_consistency": 0.1, "valid_pair_count": 3}) + "\n"
            )
            (model / "render_quality_both_iter31000.json").write_text(
                json.dumps({"image_key": "pbr_rgb", "mask_mode": "both", "splits": {}}) + "\n"
            )

            out_json = root / "inventory.json"
            out_csv = root / "inventory.csv"
            out_md = root / "inventory.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "inspect_rc_refgs_geometry_signals.py"),
                    "--shiny_blender_synthetic_root",
                    str(root / "Shiny Blender Synthetic"),
                    "--glossy_synthetic_root",
                    str(root / "GlossySyntheticConverted"),
                    "--output_roots",
                    str(root / "outputs"),
                    "--scenes",
                    "helmet",
                    "luyu",
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
            encoded = json.dumps(report)
            self.assertNotIn("shiny_blender_real", encoded)
            self.assertNotIn("/GlossySynthetic/", encoded)
            self.assertIn("geometry_proxy_metrics_available_now", report["possible_now"])
            self.assertIn("true_depth_metrics", report["unavailable_now"])
            self.assertIn("true_mesh_metrics", report["unavailable_now"])

            with open(out_csv, newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            self.assertIn("dataset", rows[0])
            self.assertIn("gt_normal_available", rows[0])
            self.assertIn("rendered_depth_available", rows[0])


if __name__ == "__main__":
    unittest.main()
