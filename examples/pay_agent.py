#!/usr/bin/env python3
"""Send SIGNA to another agent."""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from signaai import wallet


def main():
    parser = argparse.ArgumentParser(description="Pay a SignaAI agent")
    parser.add_argument("recipient")
    parser.add_argument("amount", help="Amount in SIGNA")
    parser.add_argument("--message", default="")
    parser.add_argument("--network", default=os.environ.get("SIGNUM_NETWORK", "testnet"))
    parser.add_argument("--passphrase", default=os.environ.get("SIGNAAI_PASSPHRASE"),
                        help="Defaults to SIGNAAI_PASSPHRASE")
    args = parser.parse_args()

    if not args.passphrase:
        raise SystemExit("Set SIGNAAI_PASSPHRASE or pass --passphrase")

    tx_id, err = wallet.send_signa(
        args.passphrase,
        args.recipient,
        amount=args.amount,
        message=args.message or None,
        network=args.network,
    )
    if err:
        raise SystemExit(err)

    print(f"Payment sent: {tx_id}")


if __name__ == "__main__":
    main()
