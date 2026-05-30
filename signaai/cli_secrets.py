"""
cli_secrets.py — passphrase resolution for SignaAI CLI tools.

Resolves a passphrase argument to a literal string at runtime:

  -           → interactive getpass prompt (safe for terminals)
  env:VAR     → read from environment variable VAR
  @worker     → read from ~/.openclaw/signaai-worker.json {"passphrase": "..."}
  @file:PATH  → read first line of file at PATH (~ expanded)
  <literal>   → use as-is (fallback for everything else)
"""
import json
import os


_WORKER_JSON = os.path.expanduser("~/.openclaw/signaai-worker.json")


def resolve_passphrase(value: str) -> str:
    """Resolve a passphrase token to a literal passphrase string.

    Raises ValueError if the token cannot be resolved.
    """
    if value == "-":
        import getpass
        return getpass.getpass("Passphrase: ")

    if value.startswith("env:"):
        var = value[4:]
        val = os.environ.get(var)
        if val is None:
            raise ValueError(f"Environment variable {var!r} is not set")
        return val

    if value == "@worker":
        try:
            with open(_WORKER_JSON) as f:
                data = json.load(f)
            passphrase = data.get("passphrase")
            if not passphrase:
                raise ValueError(f"No 'passphrase' key in {_WORKER_JSON}")
            return passphrase
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Could not read worker passphrase from {_WORKER_JSON}: {exc}") from exc

    if value.startswith("@file:"):
        path = os.path.expanduser(value[6:])
        try:
            with open(path) as f:
                return f.readline().strip()
        except OSError as exc:
            raise ValueError(f"Could not read passphrase from {path}: {exc}") from exc

    return value
