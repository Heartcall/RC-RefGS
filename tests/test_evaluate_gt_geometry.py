from __future__ import annotations

import importlib.util
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import trimesh


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper_assets/geometry_gt/scripts/evaluate_gt_geometry.py"


def load_module():
    spec = importlib.util.spec_from_file_location("evaluate_gt_geometry", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GeometryMetricTests(unittest.TestCase):
    def test_main_accepts_nested_smoke_output_under_rerun_namespace(self):
        module = load_module()
        output_root = module.RERUN_OUTPUT_ROOT / "smoke_ball_base_rc"
        with mock.patch.object(module, "build_manifest_package", return_value={"ok": True}):
            try:
                result = module.main(
                    [
                        "--prediction-manifest",
                        "prediction.csv",
                        "--gt-mapping",
                        "gt.csv",
                        "--output-root",
                        str(output_root),
                        "--split",
                        "main",
                    ]
                )
            except SystemExit as exc:
                self.fail(str(exc))
        self.assertEqual(result, 0)

    def test_identity_point_cloud_has_perfect_metrics(self):
        module = load_module()
        points = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            dtype=np.float64,
        )
        result = module.compute_metrics(points, points, gt_bbox_diagonal=np.sqrt(2.0))
        self.assertAlmostEqual(result["chamfer_l1"], 0.0)
        self.assertAlmostEqual(result["chamfer_l2"], 0.0)
        self.assertAlmostEqual(result["accuracy"], 0.0)
        self.assertAlmostEqual(result["completeness"], 0.0)
        self.assertAlmostEqual(result["fscore_1pct"], 1.0)

    def test_single_translated_point_reports_bidirectional_distance(self):
        module = load_module()
        gt = np.array([[0.0, 0.0, 0.0]], dtype=np.float64)
        pred = np.array([[1.0, 0.0, 0.0]], dtype=np.float64)
        result = module.compute_metrics(pred, gt, gt_bbox_diagonal=1.0)
        self.assertAlmostEqual(result["accuracy"], 1.0)
        self.assertAlmostEqual(result["completeness"], 1.0)
        self.assertAlmostEqual(result["chamfer_l1"], 1.0)
        self.assertAlmostEqual(result["chamfer_l2"], 1.0)
        self.assertAlmostEqual(result["fscore_2pct"], 0.0)

    def test_mesh_sampling_is_deterministic_for_fixed_seed(self):
        module = load_module()
        mesh = trimesh.Trimesh(
            vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float),
            faces=np.array([[0, 1, 2]], dtype=int),
            process=False,
        )
        first = module.sample_geometry(mesh, 64, seed=17)
        second = module.sample_geometry(mesh, 64, seed=17)
        np.testing.assert_allclose(first.points, second.points)
        np.testing.assert_allclose(first.normals, second.normals)

    def test_similarity_alignment_is_explicit_and_improves_diagnostic_result(self):
        module = load_module()
        gt = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]],
            dtype=np.float64,
        )
        pred = gt * 2.5 + np.array([4.0, -3.0, 2.0])
        aligned, transform = module.diagnostic_similarity_align(pred, gt)
        raw = module.compute_metrics(pred, gt, gt_bbox_diagonal=np.linalg.norm(np.ptp(gt, axis=0)))
        diagnostic = module.compute_metrics(aligned, gt, gt_bbox_diagonal=np.linalg.norm(np.ptp(gt, axis=0)))
        self.assertEqual(transform["label"], "diagnostic_similarity_aligned")
        self.assertLess(diagnostic["chamfer_l1"], raw["chamfer_l1"])
        self.assertLess(diagnostic["chamfer_l1"], 1e-8)

    def test_project_rows_match_completed_scope_and_gt_map(self):
        module = load_module()
        rows, mappings = module.build_project_rows()
        self.assertEqual(sum(row["group"] == "main" for row in rows), 28)
        self.assertEqual(sum(row["group"] == "ablation" for row in rows), 70)
        self.assertEqual(len(mappings), 14)
        self.assertTrue(all(Path(row["gt_path"]).exists() for row in rows))
        self.assertEqual(
            {row["geometry_source_type"] for row in rows},
            {"GT mesh", "GT point cloud"},
        )

    def test_batch_flattening_preserves_labeled_diagnostic_alignment(self):
        module = load_module()
        evaluation = {
            "chamfer_l1": 0.5,
            "diagnostic_similarity_alignment": {
                "transform": {
                    "label": "diagnostic_similarity_aligned",
                    "primary_metric": False,
                },
                "metrics": {
                    "chamfer_l1": 0.1,
                    "fscore_1pct": 0.9,
                },
            },
        }
        flattened = module.flatten_evaluation(evaluation)
        self.assertTrue(flattened["diagnostic_similarity_applied"])
        self.assertEqual(
            flattened["diagnostic_similarity_label"],
            "diagnostic_similarity_aligned",
        )
        self.assertAlmostEqual(flattened["diagnostic_similarity_chamfer_l1"], 0.1)
        self.assertAlmostEqual(flattened["diagnostic_similarity_fscore_1pct"], 0.9)

    def test_manifest_package_writes_isolated_rerun_outputs(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmpdir:
            root = Path(tmpdir)
            prediction = root / "prediction.ply"
            gt = root / "gt.ply"
            cloud = trimesh.points.PointCloud(
                np.array(
                    [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                    dtype=float,
                )
            )
            cloud.export(prediction)
            cloud.export(gt)
            prediction_manifest = root / "prediction_manifest.csv"
            with prediction_manifest.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "dataset",
                        "scene",
                        "split",
                        "variant",
                        "prediction_path",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "dataset": "synthetic",
                        "scene": "scene",
                        "split": "scene_geometry",
                        "variant": "base",
                        "prediction_path": prediction,
                        "status": "completed",
                    }
                )
            gt_mapping = root / "gt_mapping.csv"
            with gt_mapping.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "dataset",
                        "scene",
                        "gt_path",
                        "geometry_source_type",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "dataset": "synthetic",
                        "scene": "scene",
                        "gt_path": gt,
                        "geometry_source_type": "GT point cloud",
                    }
                )
            output_root = root / "rerun_outputs"

            summary = module.build_manifest_package(
                prediction_manifest=prediction_manifest,
                gt_mapping=gt_mapping,
                output_root=output_root,
                split_scope="all",
                num_points=100,
                seed=17,
            )

            self.assertEqual(summary["valid_prediction_rows"], 1)
            self.assertTrue((output_root / "data/ablation_geometry_metrics_wide.csv").is_file())
            with (output_root / "data/ablation_geometry_metrics_wide.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertAlmostEqual(float(rows[0]["chamfer_l1"]), 0.0)
            persisted = json.loads((output_root / "geometry_gt_eval_summary.json").read_text())
            self.assertEqual(persisted["evaluation_source"], "prediction_manifest")

    def test_manifest_package_refuses_legacy_output_root(self):
        module = load_module()
        with self.assertRaises(ValueError):
            module.validate_manifest_output_root(module.OUTPUT_ROOT)


if __name__ == "__main__":
    unittest.main()
