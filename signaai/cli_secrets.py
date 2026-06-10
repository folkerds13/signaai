"""
CLI helpers for handling wallet passphrases.

SDK calls still accept explicit passphrases because agents often hold secrets
in their own runtime. CLI commands can pass "-" to prompt without writing the
passphrase into shell history.
"""
import getpass
import os


def resolve_passphrase(value, env_var="SIGNAAI_PASSPHRASE",
                       prompt="Signum passphrase"):
    """Resolve a passphrase from a CLI value, environment variable, or prompt."""
    if value == "-":
        return getpass.getpass(f"{prompt}: ")

    if isinstance(value, str) and value.startswith("env:"):
        name = value[4:]
        resolved = os.environ.get(name)
        if not resolved:
            raise ValueError(f"Environment variable not set: {name}")
        return resolved

    if value:
        return value

    if env_var:
        resolved = os.environ.get(env_var)
        if resolved:
            return resolved

    return getpass.getpass(f"{prompt}: ")
