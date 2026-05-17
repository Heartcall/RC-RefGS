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
            "REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
            "sys.path.insert(0, REPO_ROOT)",
            "def _extract_cuda_device(argv):",
            'os.environ["CUDA_VISIBLE_DEVICES"] = _extract_cuda_device(sys.argv)',
            'parser.add_argument("--cuda_device"',
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
            "CUDA_DEVICE=\"${CUDA_DEVICE:-${CUDA_VISIBLE_DEVICES:-2}}\"",
            "--cuda_device \"${CUDA_DEVICE}\"",
            "--lambda_ref_consistency",
            "${scene}_base",
            "${scene}_rc",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
