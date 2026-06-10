import os
import unittest
from unittest.mock import patch

from signaai.cli_secrets import resolve_passphrase


class SecretTests(unittest.TestCase):
    def test_dash_prompts_for_passphrase(self):
        with patch("getpass.getpass", return_value="prompted") as getpass:
            self.assertEqual(resolve_passphrase("-"), "prompted")
        getpass.assert_called_once()

    def test_env_reference_reads_named_variable(self):
        with patch.dict(os.environ, {"SIGNAAI_TEST_SECRET": "from-env"}):
            self.assertEqual(
                resolve_passphrase("env:SIGNAAI_TEST_SECRET"),
                "from-env",
            )

    def test_explicit_value_still_works_for_compatibility(self):
        self.assertEqual(resolve_passphrase("legacy"), "legacy")


if __name__ == "__main__":
    unittest.main()
