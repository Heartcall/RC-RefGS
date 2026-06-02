import unittest
from pathlib import Path
import ast

import torch


class ReflectionConsistencyTrainingGateTests(unittest.TestCase):
    def test_train_supports_preimport_cuda_device_cli_override(self):
        source = Path("train.py").read_text()

        self.assertIn("def _extract_cuda_device(argv):", source)
        self.assertIn("def _maybe_set_cuda_device(argv):", source)
        self.assertIn("_maybe_set_cuda_device(sys.argv)", source)
        self.assertIn('current = os.environ.get("CUDA_VISIBLE_DEVICES")', source)
        self.assertIn("parser.add_argument('--cuda_device'", source)

    def test_train_supports_explicit_seed_cli_override(self):
        train_source = Path("train.py").read_text()
        utils_source = Path("utils/general_utils.py").read_text()

        self.assertIn("parser.add_argument('--seed'", train_source)
        self.assertIn("safe_state(args.quiet, seed=args.seed)", train_source)
        self.assertIn("def safe_state(silent, seed=0, cuda_device=0):", utils_source)
        self.assertIn("random.seed(seed)", utils_source)
        self.assertIn("np.random.seed(seed)", utils_source)
        self.assertIn("torch.manual_seed(seed)", utils_source)
        self.assertIn('torch.cuda.set_device(torch.device(f"cuda:{cuda_device}"))', utils_source)

    def test_optimization_params_define_disabled_default_reflection_consistency(self):
        source = Path("arguments/__init__.py").read_text()

        required_defaults = [
            "self.lambda_ref_consistency = 0.0",
            "self.ref_consistency_start = 3000",
            "self.ref_consistency_every = 4",
            "self.ref_consistency_max_angle = 20.0",
            "self.ref_consistency_gamma = 2.0",
            "self.lambda_roughness_smoothness = 0.0",
            "self.roughness_smoothness_start = 3000",
        ]
        for default in required_defaults:
            with self.subTest(default=default):
                self.assertIn(default, source)

    def test_train_uses_reflection_consistency_only_behind_ablation_gate(self):
        source = Path("train.py").read_text()

        required_snippets = [
            "from utils.reflection_consistency import choose_pair_camera, reflection_consistency_loss",
            "opt.lambda_ref_consistency > 0",
            "iteration >= opt.ref_consistency_start",
            "iteration % opt.ref_consistency_every == 0",
            "pair_cam = choose_pair_camera(",
            "reflection_consistency_loss(",
            "loss = loss + opt.lambda_ref_consistency * ref_loss",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_train_uses_roughness_smoothness_only_behind_ablation_gate(self):
        source = Path("train.py").read_text()

        required_snippets = [
            "opt.lambda_roughness_smoothness > 0",
            "iteration >= opt.roughness_smoothness_start",
            'roughness_smoothness_loss = tv_loss(render_pkg["roughness_map"][None])',
            "loss = loss + opt.lambda_roughness_smoothness * roughness_smoothness_loss",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_train_ground_truth_compositing_is_channel_aware(self):
        source = Path("train.py").read_text()

        self.assertNotIn("gt_image[:3,...] * gt_image[3:,...]", source)
        self.assertIn("def _prepare_gt_image(gt_image, bg):", source)
        self.assertIn("if channels >= 4:", source)
        self.assertIn("alpha = gt_image[3:4, ...]", source)
        self.assertIn("if channels == 3:", source)
        self.assertIn("raise ValueError", source)
        self.assertIn("gt_image = _prepare_gt_image(viewpoint_cam.original_image.cuda(), bg)", source)

    def test_prepare_gt_image_handles_rgb_and_rgba(self):
        source = Path("train.py").read_text()
        module = ast.parse(source)

        func_node = None
        for node in module.body:
            if isinstance(node, ast.FunctionDef) and node.name == "_prepare_gt_image":
                func_node = node
                break
        self.assertIsNotNone(func_node, "train.py must define _prepare_gt_image")

        compiled = compile(ast.Module(body=[func_node], type_ignores=[]), filename="train.py", mode="exec")
        scope = {}
        exec(compiled, scope)
        prepare_gt_image = scope["_prepare_gt_image"]

        bg = torch.tensor([1.0, 1.0, 1.0], dtype=torch.float32)

        rgb = torch.tensor(
            [
                [[0.1, 0.2], [0.3, 0.4]],
                [[0.5, 0.6], [0.7, 0.8]],
                [[0.9, 1.0], [0.0, 0.2]],
            ],
            dtype=torch.float32,
        )
        rgb_out = prepare_gt_image(rgb, bg)
        self.assertEqual(tuple(rgb_out.shape), (3, 2, 2))
        self.assertTrue(torch.allclose(rgb_out, rgb))

        alpha = torch.tensor([[[1.0, 0.5], [0.0, 0.25]]], dtype=torch.float32)
        rgba = torch.cat([rgb, alpha], dim=0)
        rgba_out = prepare_gt_image(rgba, bg)
        expected = rgb * alpha + (1.0 - alpha) * bg[:, None, None]
        self.assertEqual(tuple(rgba_out.shape), (3, 2, 2))
        self.assertTrue(torch.allclose(rgba_out, expected))

        gray = torch.ones((1, 2, 2), dtype=torch.float32)
        with self.assertRaises(ValueError):
            prepare_gt_image(gray, bg)


if __name__ == "__main__":
    unittest.main()
