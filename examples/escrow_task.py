#!/usr/bin/env python3
"""Create a Phase 1 operator-mediated escrow task."""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from signaai import escrow


def main():
    parser = argparse.ArgumentParser(description="Create a SignaAI escrow task")
    parser.add_argument("worker")
    parser.add_argument("amount", help="Amount in SIGNA")
    parser.add_argument("task")
    parser.add_argument("--operator", default=os.environ.get("SIGNAAI_ESCROW_OPERATOR"),
                        help="Operator address; defaults to SIGNAAI_ESCROW_OPERATOR")
    parser.add_argument("--deadline-hours", type=int, default=24)
    parser.add_argument("--network", default=os.environ.get("SIGNUM_NETWORK", "testnet"))
    parser.add_argument("--passphrase", default=os.environ.get("SIGNAAI_PASSPHRASE"),
                        help="Defaults to SIGNAAI_PASSPHRASE")
    args = parser.parse_args()

    if not args.passphrase:
        raise SystemExit("Set SIGNAAI_PASSPHRASE or pass --passphrase")
    if not args.operator:
        raise SystemExit("Set SIGNAAI_ESCROW_OPERATOR or pass --operator")

    result, err = escrow.create_escrow(
        args.passphrase,
        args.worker,
        amount=args.amount,
        task_description=args.task,
        deadline_hours=args.deadline_hours,
        operator_address=args.operator,
        network=args.network,
    )
    if err:
        raise SystemExit(err)

    print(f"Escrow ID: {result['escrow_id']}")
    print(f"Worker:    {result['worker']}")
    print(f"Operator:  {result['operator']}")
    print(f"Amount:    {result['amount_signa']} SIGNA")
    print(f"Record TX: {result['record_tx']}")
    print(f"Fund TX:   {result['fund_tx']}")


if __name__ == "__main__":
    main()
