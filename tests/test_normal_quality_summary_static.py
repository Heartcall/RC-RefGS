import unittest
from pathlib import Path


class NormalQualitySummaryStaticTests(unittest.TestCase):
    def test_summary_script_has_expected_cli_and_outputs(self):
        summary_script = Path("metrics/summarize_normal_quality.py")
        self.assertTrue(summary_script.exists(), "metrics/summarize_normal_quality.py is missing")

        source = summary_script.read_text()
        required_snippets = [
            'parser.add_argument("--pair", action="append", nargs=3',
            'parser.add_argument("--metric_filename", default="normal_quality_both_i300_full_raw.json")',
            'parser.add_argument("--output_json"',
            'parser.add_argument("--output_markdown"',
            "load_metrics",
            "summarize_pair",
            "write_markdown",
            "normal_mae_deg_delta",
            "normal_mean_cosine_delta",
            "reflective_normal_mae_deg_delta",
            "reflective_normal_mean_cosine_delta",
            "gt_normal_space",
            "json.dump(summary, f, indent=2)",
            '"| Scene | Split | Images | GT normal space | Base normal MAE | RC normal MAE | Delta |"',
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_summary_script_records_all_supported_metrics(self):
        summary_script = Path("metrics/summarize_normal_quality.py")
        self.assertTrue(summary_script.exists(), "metrics/summarize_normal_quality.py is missing")

        source = summary_script.read_text()
        required_snippets = [
            '"base_normal_mae_deg"',
            '"rc_normal_mae_deg"',
            '"base_normal_mean_cosine"',
            '"rc_normal_mean_cosine"',
            '"base_reflective_normal_mae_deg"',
            '"rc_reflective_normal_mae_deg"',
            '"base_reflective_normal_mean_cosine"',
            '"rc_reflective_normal_mean_cosine"',
            '"num_missing_normals"',
            '"num_normal_images"',
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
