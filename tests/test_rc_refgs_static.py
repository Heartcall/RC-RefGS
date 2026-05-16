import unittest
from pathlib import Path


class RenderIntermediateBufferTests(unittest.TestCase):
    def test_render_exposes_rc_refgs_intermediate_buffers(self):
        renderer_source = Path("gaussian_renderer/__init__.py").read_text()

        required_names = [
            "output_spec_rgb",
            "output_diff_rgb",
            "output_roughness",
            "output_wo",
            "output_feature",
            "'spec_light': output_spec_rgb",
            "'diff_light': output_diff_rgb",
            "'roughness_map': output_roughness",
            "'reflection_dir': output_wo",
            "'feature_map': output_feature",
            "'select_index': select_index",
        ]

        for name in required_names:
            with self.subTest(name=name):
                self.assertIn(name, renderer_source)


if __name__ == "__main__":
    unittest.main()
