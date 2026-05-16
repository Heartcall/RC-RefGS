import unittest
from pathlib import Path


class ReflectionConsistencyEvalStaticTests(unittest.TestCase):
    def test_metric_script_has_expected_json_contract(self):
        metric_script = Path("metrics/reflection_consistency_eval.py")
        self.assertTrue(metric_script.exists(), "metrics/reflection_consistency_eval.py is missing")

        source = metric_script.read_text()
        required_snippets = [
            "ModelParams(parser, sentinel=True)",
            "get_combined_args(parser)",
            "--iteration",
            "dataset.white_background",
            "mean_reflection_consistency",
            "reflective_region_psnr",
            "num_pairs",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_ablation_script_contains_required_scenes_and_flags(self):
        ablation_script = Path("scripts/run_rc_refgs_ablation.sh")
        self.assertTrue(ablation_script.exists(), "scripts/run_rc_refgs_ablation.sh is missing")

        source = ablation_script.read_text()
        required_snippets = [
            "SCENES=(teapot toaster car)",
            "--lambda_ref_consistency",
            "${scene}_base",
            "${scene}_rc",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
