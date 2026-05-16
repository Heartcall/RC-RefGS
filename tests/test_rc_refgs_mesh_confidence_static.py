import unittest
from pathlib import Path


class MeshConfidenceStaticTests(unittest.TestCase):
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
