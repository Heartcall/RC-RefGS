import unittest
from pathlib import Path


class MeshConfidenceStaticTests(unittest.TestCase):
    def test_mesh_utils_does_not_require_image_helpers_or_trimesh_at_import(self):
        source = Path("utils/mesh_utils.py").read_text()

        forbidden_top_level_imports = [
            "from utils.render_utils import save_img_f32, save_img_u8",
            "import trimesh",
        ]

        for snippet in forbidden_top_level_imports:
            with self.subTest(snippet=snippet):
                self.assertNotIn(snippet, source)

        required_snippets = [
            "def _missing_render_utils_helper",
            "save_img_f32 = _missing_render_utils_helper(\"save_img_f32\")",
            "save_img_u8 = _missing_render_utils_helper(\"save_img_u8\")",
        ]

        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_mesh_extractor_has_confidence_map_pipeline(self):
        source = Path("utils/mesh_utils.py").read_text()

        required_snippets = [
            "self.confmaps = []",
            "normal_agree =",
            "conf = alpha * normal_agree",
            "self.confmaps.append(conf.cpu())",
            "conf_threshold=0.0",
            "if hasattr(self, \"confmaps\")",
            "depth[self.confmaps[i] < conf_threshold] = 0",
        ]

        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
