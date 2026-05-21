import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
