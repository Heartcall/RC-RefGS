import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from lpipsPyTorch.modules import networks


class LpipsNetworkRetryTests(unittest.TestCase):
    def test_load_features_retries_once_after_corrupt_checkpoint_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoints_dir = os.path.join(tmpdir, "checkpoints")
            os.makedirs(checkpoints_dir, exist_ok=True)
            checkpoint_path = os.path.join(checkpoints_dir, "alexnet-test.pth")
            with open(checkpoint_path, "wb") as f:
                f.write(b"corrupt")

            calls = {"count": 0}
            weights = SimpleNamespace(url="https://example.com/alexnet-test.pth")

            class _Model:
                features = "ok"

            def fake_builder(*, weights):
                calls["count"] += 1
                if calls["count"] == 1:
                    raise RuntimeError(
                        "PytorchStreamReader failed reading zip archive: failed finding central directory"
                    )
                return _Model()

            with patch("torch.hub.get_dir", return_value=tmpdir):
                result = networks._load_features_with_retry(fake_builder, weights)

            self.assertEqual(result, "ok")
            self.assertEqual(calls["count"], 2)
            self.assertFalse(os.path.exists(checkpoint_path))

    def test_load_features_does_not_retry_unrelated_runtime_errors(self):
        calls = {"count": 0}
        weights = SimpleNamespace(url="https://example.com/alexnet-test.pth")

        def fake_builder(*, weights):
            calls["count"] += 1
            raise RuntimeError("some unrelated runtime error")

        with self.assertRaisesRegex(RuntimeError, "unrelated"):
            networks._load_features_with_retry(fake_builder, weights)
        self.assertEqual(calls["count"], 1)


if __name__ == "__main__":
    unittest.main()
