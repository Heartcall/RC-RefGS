import unittest
from pathlib import Path


class RenderQualitySummaryStaticTests(unittest.TestCase):
    def test_summary_script_has_expected_cli_and_outputs(self):
        summary_script = Path("metrics/summarize_render_quality.py")
        self.assertTrue(summary_script.exists(), "metrics/summarize_render_quality.py is missing")

        source = summary_script.read_text()
        required_snippets = [
            'parser.add_argument("--pair", action="append", nargs=3',
            'parser.add_argument("--metric_filename", default="render_quality_both_i300_skip_lpips.json")',
            'parser.add_argument("--output_json"',
            'parser.add_argument("--output_markdown"',
            "load_metrics",
            "summarize_pair",
            "write_markdown",
            "full_psnr_delta",
            "full_ssim_delta",
            "reflective_psnr_delta",
            "reflective_ssim_delta",
            "lpips_skipped",
            "json.dump(summary, f, indent=2)",
            '"| Scene | Split | Images | Base full PSNR | RC full PSNR | Delta |"',
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_summary_script_records_all_supported_metrics(self):
        summary_script = Path("metrics/summarize_render_quality.py")
        self.assertTrue(summary_script.exists(), "metrics/summarize_render_quality.py is missing")

        source = summary_script.read_text()
        required_snippets = [
            '"base_full_psnr"',
            '"rc_full_psnr"',
            '"base_full_ssim"',
            '"rc_full_ssim"',
            '"base_reflective_psnr"',
            '"rc_reflective_psnr"',
            '"base_reflective_ssim"',
            '"rc_reflective_ssim"',
            '"base_full_lpips"',
            '"rc_full_lpips"',
            '"base_reflective_lpips"',
            '"rc_reflective_lpips"',
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
