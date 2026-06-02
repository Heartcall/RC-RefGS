import unittest
from pathlib import Path
import ast

import torch


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
            "def _maybe_set_cuda_device(argv):",
            "_maybe_set_cuda_device(sys.argv)",
            'value.lower() not in {"auto", "none"}',
            'os.environ["CUDA_VISIBLE_DEVICES"] = cuda_device',
            "safe_state(args.quiet)",
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

    def test_metric_script_supports_fixed_pair_lists(self):
        metric_script = Path("metrics/reflection_consistency_eval.py")
        self.assertTrue(metric_script.exists(), "metrics/reflection_consistency_eval.py is missing")

        source = metric_script.read_text()
        required_snippets = [
            "def _load_pair_list(",
            "def _camera_lookup(",
            "def _resolve_pair_list(",
            'parser.add_argument("--pair_list_json"',
            'pair_list_json = getattr(args, "pair_list_json", None)',
            "pair_specs=pair_list_json",
            '"pair_mode"',
            '"dynamic"',
            '"fixed"',
            '"valid_pair_count"',
            '"requested_pair_count"',
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

    def test_ablation_script_supports_eval_split_preserving_variant_matrix(self):
        ablation_script = Path("scripts/run_rc_refgs_ablation.sh")
        self.assertTrue(ablation_script.exists(), "scripts/run_rc_refgs_ablation.sh is missing")

        source = ablation_script.read_text()
        required_snippets = [
            "VARIANTS=(base rc wo_ref wo_conf rough_only)",
            "--eval",
            "--ref_consistency_gamma",
            "ROUGHNESS_SMOOTH_LAMBDA",
            "--lambda_roughness_smoothness",
            "--roughness_smoothness_start",
            "export -n CUDA_DEVICE",
            "for split in train test; do",
            "reflection_consistency_${split}.json",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_direct_ablation_launcher_contract(self):
        launcher = Path("scripts/run_rc_refgs_ablation_direct.py")
        self.assertTrue(launcher.exists(), "scripts/run_rc_refgs_ablation_direct.py is missing")

        source = launcher.read_text()
        required_snippets = [
            "subprocess.run",
            "sys.executable",
            "DEFAULT_SCENES =",
            '("teapot", "toaster", "car")',
            "DEFAULT_VARIANTS =",
            '("base", "rc", "wo_ref", "wo_conf", "rough_only")',
            "--dry_run",
            "--cuda_device",
            "--eval",
            "--lambda_ref_consistency",
            "--lambda_roughness_smoothness",
            "--no_quiet",
            "--pair_list_json",
            "reflection_consistency_{split}.json",
            "for split in (\"train\", \"test\")",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)
        self.assertNotIn("BooleanOptionalAction", source)

    def test_direct_ablation_launcher_supports_deterministic_seed_output_naming(self):
        launcher = Path("scripts/run_rc_refgs_ablation_direct.py")
        self.assertTrue(launcher.exists(), "scripts/run_rc_refgs_ablation_direct.py is missing")

        source = launcher.read_text()
        required_snippets = [
            "def _model_path(",
            'parser.add_argument("--seeds"',
            'parser.add_argument("--include_seed_in_path"',
            "for seed in args.seeds:",
            'f"{scene}_{variant}_seed{seed}"',
            '"--seed"',
            "str(seed)",
            "include_seed_in_path = args.include_seed_in_path or len(args.seeds) > 1",
            "include_seed_in_path=include_seed_in_path",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_direct_ablation_launcher_supports_manifest_dry_run_orchestration(self):
        launcher = Path("scripts/run_rc_refgs_ablation_direct.py")
        self.assertTrue(launcher.exists(), "scripts/run_rc_refgs_ablation_direct.py is missing")

        source = launcher.read_text()
        required_snippets = [
            "import json",
            "MANIFEST_FIELDS =",
            '"scenes"',
            '"variants"',
            '"iterations"',
            '"seeds"',
            '"output_root"',
            '"pair_list_json"',
            '"metrics"',
            "SUPPORTED_METRICS =",
            '"reflection_consistency"',
            "def _load_manifest(",
            "def _cli_option_names(",
            "def _apply_manifest(",
            "parser.add_argument(\"--manifest_json\"",
            "args = _apply_manifest(args, argv)",
            "Unsupported manifest metrics",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_metric_gt_compositing_is_channel_aware(self):
        metric_script = Path("metrics/reflection_consistency_eval.py")
        self.assertTrue(metric_script.exists(), "metrics/reflection_consistency_eval.py is missing")

        source = metric_script.read_text()
        self.assertNotIn("gt[:3, ...] * gt[3:, ...]", source)
        self.assertIn("def _prepare_gt_image(gt_image, bg):", source)
        self.assertIn("if channels >= 4:", source)
        self.assertIn("alpha = gt_image[3:4, ...]", source)
        self.assertIn("if channels == 3:", source)
        self.assertIn("raise ValueError", source)
        self.assertIn("target = _prepare_gt_image(gt, bg_color)", source)

    def test_metric_prepare_gt_image_handles_rgb_and_rgba(self):
        source = Path("metrics/reflection_consistency_eval.py").read_text()
        module = ast.parse(source)

        func_node = None
        for node in module.body:
            if isinstance(node, ast.FunctionDef) and node.name == "_prepare_gt_image":
                func_node = node
                break
        self.assertIsNotNone(func_node, "metrics/reflection_consistency_eval.py must define _prepare_gt_image")

        compiled = compile(ast.Module(body=[func_node], type_ignores=[]), filename="metrics/reflection_consistency_eval.py", mode="exec")
        scope = {}
        exec(compiled, scope)
        prepare_gt_image = scope["_prepare_gt_image"]

        bg = torch.tensor([0.0, 0.0, 0.0], dtype=torch.float32)
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

    def test_direct_ablation_launcher_writes_expansion_summary_and_checks_missing_artifacts(self):
        launcher = Path("scripts/run_rc_refgs_ablation_direct.py")
        self.assertTrue(launcher.exists(), "scripts/run_rc_refgs_ablation_direct.py is missing")

        source = launcher.read_text()
        required_snippets = [
            "def _expected_artifacts(",
            "def _build_jobs(",
            "def _write_expansion_summary(",
            "def _collect_missing_artifacts(",
            "parser.add_argument(\"--summary_json\"",
            "parser.add_argument(\"--check_missing\"",
            '"summary_json"',
            '"check_missing"',
            '"expected_artifacts"',
            '"missing_artifacts"',
            '"train_command"',
            '"metric_commands"',
            '"include_seed_in_path"',
            "summary[\"missing_count\"]",
            "raise SystemExit(2)",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
