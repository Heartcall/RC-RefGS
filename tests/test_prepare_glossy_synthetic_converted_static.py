import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


class PrepareGlossySyntheticConvertedStaticTests(unittest.TestCase):
    def test_script_exists_is_executable_and_has_safe_shell_preamble(self):
        script = Path("scripts/prepare_glossy_synthetic_converted.sh")
        self.assertTrue(script.exists(), "conversion prep script is missing")
        mode = script.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR, "conversion prep script is not user-executable")
        source = script.read_text(encoding="utf-8")
        self.assertIn("#!/usr/bin/env bash", source)
        self.assertIn("set -euo pipefail", source)
        self.assertIn("This script ONLY prepares data. It does NOT start any training.", source)

    def test_help_executes(self):
        script = Path("scripts/prepare_glossy_synthetic_converted.sh")
        result = subprocess.run(
            [str(script), "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--dry_run", result.stdout)
        self.assertIn("--raw_root", result.stdout)
        self.assertIn("--converted_root", result.stdout)

    def test_dry_run_completes_with_mock_scene(self):
        script = Path("scripts/prepare_glossy_synthetic_converted.sh")
        with tempfile.TemporaryDirectory(prefix="rc_refgs_glossy_prep_test_") as tmp:
            raw_root = Path(tmp) / "raw"
            converted_root = Path(tmp) / "converted"
            scene_root = raw_root / "angel"
            scene_root.mkdir(parents=True)
            (scene_root / "000-camera.pkl").write_text("", encoding="utf-8")
            (scene_root / "000-depth.png").write_text("", encoding="utf-8")
            (scene_root / "000.png").write_text("", encoding="utf-8")
            fake_nero2 = Path(tmp) / "fake_nero2blender.py"
            fake_nero2.write_text(
                "#!/usr/bin/env python\nprint('fake nero2blender')\n",
                encoding="utf-8",
            )
            fake_nero2.chmod(0o755)

            result = subprocess.run(
                [
                    str(script),
                    "--raw_root",
                    str(raw_root),
                    "--converted_root",
                    str(converted_root),
                    "--nero2blender",
                    str(fake_nero2),
                    "--dry_run",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DRY-RUN:", result.stdout)
            self.assertIn("converted_ok=", result.stderr)
            self.assertIn("converted_fail=0", result.stderr)


if __name__ == "__main__":
    unittest.main()
