import csv
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "paper_assets"
    / "geometry_gt"
    / "rerun_20260611"
    / "final_diagnostics"
    / "scripts"
    / "generate_geometry_failure_diagnostics.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_geometry_failure_diagnostics", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class GeometryFailureDiagnosticsTests(unittest.TestCase):
    def test_win_loss_summary_respects_metric_direction(self):
        diag = _load_module()
        rows = [
            {"dataset": "glossy_synthetic", "scene": "bell", "metric": "chamfer_l1", "base": 2.0, "rc": 1.0},
            {"dataset": "glossy_synthetic", "scene": "cat", "metric": "chamfer_l1", "base": 1.0, "rc": 1.5},
            {"dataset": "shiny_blender_synthetic", "scene": "teapot", "metric": "fscore_1pct", "base": 0.7, "rc": 0.8},
        ]

        summary = diag.compute_win_loss(rows)

        by_metric = {row["metric"]: row for row in summary}
        self.assertEqual(by_metric["chamfer_l1"]["rc_win"], 1)
        self.assertEqual(by_metric["chamfer_l1"]["rc_loss"], 1)
        self.assertAlmostEqual(by_metric["chamfer_l1"]["mean_rc_improvement"], 0.25)
        self.assertEqual(by_metric["fscore_1pct"]["rc_win"], 1)
        self.assertEqual(by_metric["fscore_1pct"]["rc_loss"], 0)
        self.assertAlmostEqual(by_metric["fscore_1pct"]["mean_rc_improvement"], 0.1)

    def test_scene_failure_mode_classification_keeps_mixed_claim_boundary(self):
        diag = _load_module()
        rows = [
            {"metric": "chamfer_l1", "base": 1.0, "rc": 0.8},
            {"metric": "chamfer_l2", "base": 1.0, "rc": 0.9},
            {"metric": "fscore_0p5pct", "base": 0.7, "rc": 0.8},
        ]
        improving = diag.classify_scene(rows)
        self.assertEqual(improving["failure_mode"], "improved_primary_geometry")

        rows[0]["rc"] = 1.2
        rows[1]["rc"] = 1.1
        rows[2]["rc"] = 0.6
        degraded = diag.classify_scene(rows)
        self.assertEqual(degraded["failure_mode"], "degraded_primary_geometry")
        self.assertEqual(degraded["stable_mesh_quality_claim"], "NO-GO")

    def test_generator_writes_missing_join_report_without_forcing_correlation(self):
        diag = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            final_all = root / "final_all"
            output_root = root / "outputs"
            diagnostics = root / "diagnostics"
            data = final_all / "data"
            main_rows = [
                {
                    "dataset": "glossy_synthetic",
                    "scene": "bell",
                    "chamfer_l1_base": "1.0",
                    "chamfer_l1_rc": "0.8",
                    "fscore_1pct_base": "0.7",
                    "fscore_1pct_rc": "0.8",
                }
            ]
            _write_csv(
                data / "main_base_vs_rc_geometry_delta.csv",
                main_rows,
                list(main_rows[0].keys()),
            )
            _write_csv(
                data / "ablation_geometry_metrics_long.csv",
                [
                    {
                        "dataset": "glossy_synthetic",
                        "scene": "bell",
                        "split": "scene_geometry",
                        "variant": "base",
                        "metric": "chamfer_l1",
                        "value": "1.0",
                        "metric_direction": "lower",
                    }
                ],
                ["dataset", "scene", "split", "variant", "metric", "value", "metric_direction"],
            )

            summary = diag.generate_diagnostics(final_all, output_root, diagnostics)

            self.assertEqual(summary["claim_boundary"]["stable_mesh_quality_improvement"], "NO-GO")
            missing = diagnostics / "analysis" / "rc_consistency_geometry_correlation_missing_fields.md"
            self.assertTrue(missing.exists())
            corr_csv = diagnostics / "data" / "rc_consistency_geometry_correlation.csv"
            with open(corr_csv, newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["status"], "missing_join_fields")
            self.assertFalse(any(math.isinf(float(row["joinable_rows"])) for row in rows))


if __name__ == "__main__":
    unittest.main()
