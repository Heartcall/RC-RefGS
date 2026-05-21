import unittest
from pathlib import Path


class MaterialQualitySummaryStaticTests(unittest.TestCase):
    def test_summary_script_has_expected_cli_and_outputs(self):
        summary_script = Path("metrics/summarize_material_quality.py")
        self.assertTrue(summary_script.exists(), "metrics/summarize_material_quality.py is missing")

        source = summary_script.read_text()
        required_snippets = [
            'parser.add_argument("--pair", action="append", nargs=3',
            'parser.add_argument("--metric_filename", default="material_quality_both_i300.json")',
            'parser.add_argument("--output_json"',
            'parser.add_argument("--output_markdown"',
            "load_metrics",
            "summarize_pair",
            "write_markdown",
            "full_diffuse_variance_delta",
            "full_roughness_variance_delta",
            "full_specular_variance_delta",
            "reflective_specular_diffuse_ratio_delta",
            "json.dump(summary, f, indent=2)",
            '"| Scene | Split | Images | Base diffuse var | RC diffuse var | Delta |"',
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_summary_script_records_supported_material_metrics(self):
        summary_script = Path("metrics/summarize_material_quality.py")
        self.assertTrue(summary_script.exists(), "metrics/summarize_material_quality.py is missing")

        source = summary_script.read_text()
        required_snippets = [
            '"base_full_diffuse_variance"',
            '"rc_full_diffuse_variance"',
            '"base_full_roughness_variance"',
            '"rc_full_roughness_variance"',
            '"base_full_specular_variance"',
            '"rc_full_specular_variance"',
            '"base_reflective_diffuse_variance"',
            '"rc_reflective_diffuse_variance"',
            '"base_reflective_roughness_variance"',
            '"rc_reflective_roughness_variance"',
            '"base_reflective_specular_variance"',
            '"rc_reflective_specular_variance"',
            '"base_reflective_specular_diffuse_ratio"',
            '"rc_reflective_specular_diffuse_ratio"',
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
