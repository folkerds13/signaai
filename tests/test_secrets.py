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

    def _with_worker_paths(self, paths):
        import signaai.cli_secrets as cs
        original = cs.WORKER_CONFIG_PATHS
        cs.WORKER_CONFIG_PATHS = paths

        def restore():
            cs.WORKER_CONFIG_PATHS = original
        return restore

    def _temp_config(self, payload):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(payload, f)
            return f.name

    def test_worker_json(self):
        path = self._temp_config({"passphrase": "worker-secret"})
        restore = self._with_worker_paths([path])
        try:
            self.assertEqual(resolve_passphrase("@worker"), "worker-secret")
        finally:
            restore()
            os.unlink(path)

    def test_worker_json_second_path_wins_when_first_missing(self):
        path = self._temp_config({"passphrase": "hermes-secret"})
        restore = self._with_worker_paths(["/nonexistent/worker.json", path])
        try:
            self.assertEqual(resolve_passphrase("@worker"), "hermes-secret")
        finally:
            restore()
            os.unlink(path)

    def test_worker_json_missing_raises(self):
        restore = self._with_worker_paths(["/nonexistent/worker.json"])
        try:
            with self.assertRaises(ValueError):
                resolve_passphrase("@worker")
        finally:
            restore()

    def test_worker_json_missing_key_raises(self):
        path = self._temp_config({"other_key": "val"})
        restore = self._with_worker_paths([path])
        try:
            with self.assertRaises(ValueError):
                resolve_passphrase("@worker")
        finally:
            restore()
            os.unlink(path)

    def test_worker_json_nested_env_spec(self):
        path = self._temp_config({"passphrase": "env:SIGNAAI_NESTED_TEST"})
        restore = self._with_worker_paths([path])
        os.environ["SIGNAAI_NESTED_TEST"] = "resolved-from-env"
        try:
            self.assertEqual(resolve_passphrase("@worker"), "resolved-from-env")
        finally:
            restore()
            del os.environ["SIGNAAI_NESTED_TEST"]
            os.unlink(path)

    def test_worker_json_recursive_worker_spec_raises(self):
        path = self._temp_config({"passphrase": "@worker"})
        restore = self._with_worker_paths([path])
        try:
            with self.assertRaises(ValueError):
                resolve_passphrase("@worker")
        finally:
            restore()
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
