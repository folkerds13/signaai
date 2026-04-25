#!/usr/bin/env python3
"""Register an agent identity alias on Signum."""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from signaai import identity


def main():
    parser = argparse.ArgumentParser(description="Register a SignaAI agent")
    parser.add_argument("name")
    parser.add_argument("--capabilities", default="",
                        help="Comma-separated capabilities")
    parser.add_argument("--description", default="")
    parser.add_argument("--endpoint", default="")
    parser.add_argument("--version", default="1.0")
    parser.add_argument("--network", default=os.environ.get("SIGNUM_NETWORK", "testnet"))
    parser.add_argument("--passphrase", default=os.environ.get("SIGNAAI_PASSPHRASE"),
                        help="Defaults to SIGNAAI_PASSPHRASE")
    args = parser.parse_args()

    if not args.passphrase:
        raise SystemExit("Set SIGNAAI_PASSPHRASE or pass --passphrase")

    capabilities = [c.strip() for c in args.capabilities.split(",") if c.strip()]
    result, err = identity.register_agent(
        args.passphrase,
        args.name,
        capabilities=capabilities,
        description=args.description,
        endpoint=args.endpoint,
        version=args.version,
        network=args.network,
    )
    if err:
        raise SystemExit(err)

    print(f"Registered {result['metadata']['name']}")
    print(f"Address: {result['address']}")
    print(f"Alias:   {result['alias']}")
    print(f"TX:      {result['tx_id']}")


if __name__ == "__main__":
    main()
