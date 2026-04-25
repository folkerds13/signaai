#!/usr/bin/env python3
"""Reference workflow: MK creates an escrow task for Sieka.

This is a dogfooding example only. The SDK and protocol primitives are generic;
MK and Sieka are not special-cased anywhere in SignaAI.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from signaai import escrow, wallet


def main():
    parser = argparse.ArgumentParser(description="MK hires Sieka via SignaAI escrow")
    parser.add_argument("task")
    parser.add_argument("--sieka-address", default=os.environ.get("SIEKA_ADDRESS"))
    parser.add_argument("--amount", default="1.0")
    parser.add_argument("--operator", default=os.environ.get("SIGNAAI_ESCROW_OPERATOR"))
    parser.add_argument("--network", default=os.environ.get("SIGNUM_NETWORK", "testnet"))
    parser.add_argument("--mk-passphrase", default=os.environ.get("MK_PASSPHRASE"))
    args = parser.parse_args()

    if not args.mk_passphrase:
        raise SystemExit("Set MK_PASSPHRASE or pass --mk-passphrase")
    if not args.sieka_address:
        raise SystemExit("Set SIEKA_ADDRESS or pass --sieka-address")
    if not args.operator:
        raise SystemExit("Set SIGNAAI_ESCROW_OPERATOR or pass --operator")

    mk_address, err = wallet.get_my_address(args.mk_passphrase, args.network)
    if err:
        raise SystemExit(err)

    result, err = escrow.create_escrow(
        args.mk_passphrase,
        args.sieka_address,
        amount=args.amount,
        task_description=args.task,
        operator_address=args.operator,
        network=args.network,
    )
    if err:
        raise SystemExit(err)

    print("MK -> Sieka escrow created")
    print(f"MK:        {mk_address}")
    print(f"Sieka:     {result['worker']}")
    print(f"Escrow ID: {result['escrow_id']}")
    print(f"Record TX: {result['record_tx']}")
    print(f"Fund TX:   {result['fund_tx']}")


if __name__ == "__main__":
    main()
