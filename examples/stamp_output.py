#!/usr/bin/env python3
"""Stamp an output hash on-chain and print the proof receipt."""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from signaai import verify


def main():
    parser = argparse.ArgumentParser(description="Stamp a verifiable output")
    parser.add_argument("content")
    parser.add_argument("--label", default="")
    parser.add_argument("--sources", default="",
                        help="Comma-separated source URLs or IDs")
    parser.add_argument("--network", default=os.environ.get("SIGNUM_NETWORK", "testnet"))
    parser.add_argument("--passphrase", default=os.environ.get("SIGNAAI_PASSPHRASE"),
                        help="Defaults to SIGNAAI_PASSPHRASE")
    args = parser.parse_args()

    if not args.passphrase:
        raise SystemExit("Set SIGNAAI_PASSPHRASE or pass --passphrase")

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    result, err = verify.stamp(
        args.passphrase,
        args.content,
        sources=sources,
        label=args.label,
        network=args.network,
    )
    if err:
        raise SystemExit(err)

    print(f"TX:           {result['tx_id']}")
    print(f"Content hash: {result['hash']}")
    print(f"Sources:      {', '.join(result['sources']) or '-'}")


if __name__ == "__main__":
    main()
