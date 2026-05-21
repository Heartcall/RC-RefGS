import unittest
from pathlib import Path


class MaterialQualityEvalStaticTests(unittest.TestCase):
    def test_material_quality_script_has_expected_contract(self):
        metric_script = Path("metrics/material_quality_eval.py")
        self.assertTrue(metric_script.exists(), "metrics/material_quality_eval.py is missing")

        source = metric_script.read_text()
        required_snippets = [
            "ModelParams(parser, sentinel=True)",
            "get_combined_args(parser)",
            "REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
            "sys.path.insert(0, REPO_ROOT)",
            "def _extract_cuda_device(argv):",
            "def _cuda_device_index(cuda_device):",
            "safe_state(args.quiet, cuda_device=_cuda_device_index(args.cuda_device))",
            'parser.add_argument("--cuda_device"',
            'parser.add_argument("--split", choices=["train", "test", "both"]',
            'parser.add_argument("--mask_mode", choices=["none", "reflective", "both"]',
            'parser.add_argument("--output_json"',
            "material_stats",
            "diff_light",
            "roughness_map",
            "spec_light",
            "specular_diffuse_ratio",
            "full_diffuse_variance",
            "reflective_roughness_variance",
            "reflective_specular_variance",
            "num_reflective_pixels",
            "per_image",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_material_quality_script_records_loaded_iteration_and_output_path(self):
        metric_script = Path("metrics/material_quality_eval.py")
        self.assertTrue(metric_script.exists(), "metrics/material_quality_eval.py is missing")

        source = metric_script.read_text()
        required_snippets = [
            "scene.loaded_iter if scene.loaded_iter is not None else args.iteration",
            'f"material_quality_{args.split}_iter{loaded_iter}.json"',
            "json.dump(results, f, indent=2)",
            "torch.cuda.empty_cache()",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
