import unittest
from pathlib import Path


class RenderQualityEvalStaticTests(unittest.TestCase):
    def test_render_quality_script_has_standard_metric_contract(self):
        metric_script = Path("metrics/render_quality_eval.py")
        self.assertTrue(metric_script.exists(), "metrics/render_quality_eval.py is missing")

        source = metric_script.read_text()
        required_snippets = [
            "ModelParams(parser, sentinel=True)",
            "get_combined_args(parser)",
            "REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
            "sys.path.insert(0, REPO_ROOT)",
            "def _extract_cuda_device(argv):",
            "def _maybe_set_cuda_device(argv):",
            "def _cuda_device_index(cuda_device):",
            "_maybe_set_cuda_device(sys.argv)",
            "safe_state(args.quiet, cuda_device=_cuda_device_index(args.cuda_device))",
            'parser.add_argument("--cuda_device"',
            'parser.add_argument("--split", choices=["train", "test", "both"]',
            'parser.add_argument("--mask_mode", choices=["none", "reflective", "both"]',
            'parser.add_argument("--skip_lpips", action="store_true")',
            "from lpipsPyTorch import lpips",
            "from utils.image_utils import psnr",
            "from utils.loss_utils import ssim",
            "full_psnr",
            "full_ssim",
            "full_lpips",
            "reflective_psnr",
            "reflective_ssim",
            "reflective_lpips",
            "num_images",
            "per_image",
            "pred_batch = pred[None, ...].contiguous()",
            "target_batch = target[None, ...].contiguous()",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_render_quality_selects_cuda_device_before_safe_state_initializes_cuda(self):
        source = Path("metrics/render_quality_eval.py").read_text()
        safe_state_call = "safe_state(args.quiet, cuda_device=_cuda_device_index(args.cuda_device))"

        self.assertIn(safe_state_call, source)
        self.assertNotIn("_select_torch_cuda_device(args.cuda_device)", source)

    def test_render_quality_script_records_loaded_iteration_and_output_path(self):
        metric_script = Path("metrics/render_quality_eval.py")
        self.assertTrue(metric_script.exists(), "metrics/render_quality_eval.py is missing")

        source = metric_script.read_text()
        required_snippets = [
            "scene.loaded_iter if scene.loaded_iter is not None else args.iteration",
            'f"render_quality_{args.split}_iter{loaded_iter}.json"',
            "json.dump(results, f, indent=2)",
            "torch.cuda.empty_cache()",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
