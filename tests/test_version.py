import pathlib
import re
import unittest

import signaai


class VersionTests(unittest.TestCase):
    def test_package_version_matches_pyproject(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        pyproject = (root / "pyproject.toml").read_text()
        match = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)

        self.assertIsNotNone(match)
        self.assertEqual(signaai.__version__, match.group(1))


if __name__ == "__main__":
    unittest.main()
