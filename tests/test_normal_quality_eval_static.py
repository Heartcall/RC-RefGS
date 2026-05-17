import unittest
from pathlib import Path


class NormalQualityEvalStaticTests(unittest.TestCase):
    def test_normal_quality_script_has_expected_contract(self):
        metric_script = Path("metrics/normal_quality_eval.py")
        self.assertTrue(metric_script.exists(), "metrics/normal_quality_eval.py is missing")

        source = metric_script.read_text()
        required_snippets = [
            "ModelParams(parser, sentinel=True)",
            "get_combined_args(parser)",
            "REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
            "sys.path.insert(0, REPO_ROOT)",
            "def _extract_cuda_device(argv):",
            'os.environ["CUDA_VISIBLE_DEVICES"] = _extract_cuda_device(sys.argv)',
            'parser.add_argument("--cuda_device"',
            'parser.add_argument("--split", choices=["train", "test", "both"]',
            'parser.add_argument("--normal_key", choices=["rend_normal", "surf_normal"]',
            'parser.add_argument("--normal_suffix", type=str, default="_normal.png")',
            '"--gt_normal_space"',
            "convert_gt_normal_space",
            "blender_world_to_colmap",
            "opengl_camera_to_world",
            'parser.add_argument("--output_json"',
            "load_gt_normal",
            "normal_angular_error",
            "normal_mean_cosine",
            "normal_mae_deg",
            "reflective_normal_mae_deg",
            "num_images",
            "num_normal_images",
            "num_missing_normals",
            "per_image",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_normal_quality_script_records_loaded_iteration_and_normal_paths(self):
        metric_script = Path("metrics/normal_quality_eval.py")
        self.assertTrue(metric_script.exists(), "metrics/normal_quality_eval.py is missing")

        source = metric_script.read_text()
        required_snippets = [
            "scene.loaded_iter if scene.loaded_iter is not None else args.iteration",
            'f"normal_quality_{args.split}_iter{loaded_iter}.json"',
            "os.path.join(dataset.source_path, split_name, camera.image_name + normal_suffix)",
            "json.dump(results, f, indent=2)",
            "torch.cuda.empty_cache()",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
