import unittest
from pathlib import Path


class ReducedAblationSummaryStaticTests(unittest.TestCase):
    def test_summary_script_has_expected_cli_and_outputs(self):
        summary_script = Path("metrics/summarize_reduced_ablation.py")
        self.assertTrue(summary_script.exists(), "metrics/summarize_reduced_ablation.py is missing")

        source = summary_script.read_text()
        required_snippets = [
            'parser.add_argument("--scene-root", action="append", nargs=2',
            'parser.add_argument("--iteration", type=int, default=20)',
            'parser.add_argument("--output_json", required=True)',
            'parser.add_argument("--output_markdown", default=None)',
            "EXPECTED_VARIANTS",
            "EXPECTED_SPLITS",
            "reflection_consistency_",
            '"mean_reflection_consistency"',
            '"reflective_region_psnr"',
            '"num_pairs"',
            '"missing_cells"',
            '"available_cells"',
            "json.dump(summary, f, indent=2)",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_summary_script_tracks_missing_cells_and_base_deltas(self):
        summary_script = Path("metrics/summarize_reduced_ablation.py")
        self.assertTrue(summary_script.exists(), "metrics/summarize_reduced_ablation.py is missing")

        source = summary_script.read_text()
        required_snippets = [
            '"baseline_mean_reflection_consistency"',
            '"mean_reflection_consistency_delta_vs_base"',
            '"status"',
            '"missing"',
            '"available"',
            "write_markdown",
            '"| Scene | Variant | Split | Status | Mean RC | Delta vs Base | Num Pairs |"',
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
