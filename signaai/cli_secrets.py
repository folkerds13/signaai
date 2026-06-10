"""
cli_secrets.py — passphrase resolution for SignaAI CLI tools.

Resolves a passphrase argument to a literal string at runtime:

  -           → interactive getpass prompt (safe for terminals)
  env:VAR     → read from environment variable VAR
  @worker     → read from the worker config (first match wins):
                  ~/.openclaw/signaai-worker.json
                  ~/.openclaw/workspace/signaai-worker.json
                  ~/.hermes/signaai-worker.json
                The config's "passphrase" value may itself be an env:/@file:
                spec, which is resolved in turn.
  @file:PATH  → read first line of file at PATH (~ expanded)
  <literal>   → use as-is (fallback for everything else)
"""
import json
import os


WORKER_CONFIG_PATHS = [
    "~/.openclaw/signaai-worker.json",
    "~/.openclaw/workspace/signaai-worker.json",
    "~/.hermes/signaai-worker.json",
]


def _read_worker_passphrase():
    errors = []
    for candidate in WORKER_CONFIG_PATHS:
        path = os.path.expanduser(candidate)
        if not os.path.exists(path):
            continue
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        passphrase = data.get("passphrase")
        if passphrase:
            return str(passphrase).strip()
        errors.append(f"{path}: no 'passphrase' key")
    detail = "; ".join(errors) if errors else "no worker config found"
    raise ValueError(f"Could not read worker passphrase ({detail})")


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
        passphrase = _read_worker_passphrase()
        # The config value may itself be a spec (env:VAR, @file:PATH) —
        # resolve it, but never recurse back into @worker.
        if passphrase == "@worker":
            raise ValueError("Worker config 'passphrase' must not be '@worker'")
        return resolve_passphrase(passphrase)

    if value.startswith("@file:"):
        path = os.path.expanduser(value[6:])
        try:
            with open(path) as f:
                return f.readline().strip()
        except OSError as exc:
            raise ValueError(f"Could not read passphrase from {path}: {exc}") from exc

    return value
