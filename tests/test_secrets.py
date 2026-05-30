import json
import os
import tempfile
import unittest

from signaai.cli_secrets import resolve_passphrase


class TestResolvePassphrase(unittest.TestCase):
    def test_literal_passphrase(self):
        self.assertEqual(resolve_passphrase("my secret words"), "my secret words")

    def test_env_var(self):
        os.environ["SIGNAAI_TEST_PASS"] = "from-env"
        try:
            self.assertEqual(resolve_passphrase("env:SIGNAAI_TEST_PASS"), "from-env")
        finally:
            del os.environ["SIGNAAI_TEST_PASS"]

    def test_env_var_missing_raises(self):
        os.environ.pop("SIGNAAI_NONEXISTENT_VAR", None)
        with self.assertRaises(ValueError) as ctx:
            resolve_passphrase("env:SIGNAAI_NONEXISTENT_VAR")
        self.assertIn("SIGNAAI_NONEXISTENT_VAR", str(ctx.exception))

    def test_file_passphrase(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("file-passphrase\nextra-line\n")
            path = f.name
        try:
            self.assertEqual(resolve_passphrase(f"@file:{path}"), "file-passphrase")
        finally:
            os.unlink(path)

    def test_file_missing_raises(self):
        with self.assertRaises(ValueError):
            resolve_passphrase("@file:/nonexistent/path/to/pass.txt")

    def test_worker_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"passphrase": "worker-secret"}, f)
            path = f.name
        import signaai.cli_secrets as cs
        original = cs._WORKER_JSON
        cs._WORKER_JSON = path
        try:
            self.assertEqual(resolve_passphrase("@worker"), "worker-secret")
        finally:
            cs._WORKER_JSON = original
            os.unlink(path)

    def test_worker_json_missing_raises(self):
        import signaai.cli_secrets as cs
        original = cs._WORKER_JSON
        cs._WORKER_JSON = "/nonexistent/worker.json"
        try:
            with self.assertRaises(ValueError):
                resolve_passphrase("@worker")
        finally:
            cs._WORKER_JSON = original

    def test_worker_json_missing_key_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"other_key": "val"}, f)
            path = f.name
        import signaai.cli_secrets as cs
        original = cs._WORKER_JSON
        cs._WORKER_JSON = path
        try:
            with self.assertRaises(ValueError):
                resolve_passphrase("@worker")
        finally:
            cs._WORKER_JSON = original
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
