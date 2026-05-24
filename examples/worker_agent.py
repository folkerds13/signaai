#!/usr/bin/env python3
"""
Example: autonomous worker agent using SignaAIListener.

Run this on any machine. When a payer creates an escrow targeting your address,
this agent receives the task, does the work, and submits the result on-chain.

No OpenClaw. No Hermes. Just Python.

Usage:
    export SIGNUM_NETWORK=mainnet
    python3 worker_agent.py --address S-YOUR-ADDRESS --passphrase "your words here"
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from signaai import SignaAIListener, TaskEvent
from signaai.escrow import submit_result


def do_work(task_description: str) -> str:
    """
    Replace this with your actual agent logic — LLM call, web search, etc.
    Must return the result as a string.
    """
    return f"Result for: {task_description}\n\n[Replace with real agent logic]"


def main():
    parser = argparse.ArgumentParser(description="SignaAI worker agent")
    parser.add_argument("--address",    required=True, help="Your Signum address")
    parser.add_argument("--passphrase", default=os.environ.get("SIGNAAI_PASSPHRASE"))
    parser.add_argument("--network",    default=os.environ.get("SIGNUM_NETWORK", "mainnet"))
    parser.add_argument("--interval",   type=int, default=120)
    parser.add_argument("--once",       action="store_true")
    args = parser.parse_args()

    if not args.passphrase:
        raise SystemExit("Set SIGNAAI_PASSPHRASE or pass --passphrase")

    listener = SignaAIListener(
        address=args.address,
        network=args.network,
        poll_interval=args.interval,
    )

    @listener.on_task_assigned
    def handle_task(event: TaskEvent):
        print(f"\nTask received: {event.escrow_id}")
        print(f"  From:   {event.payer_address}")
        print(f"  Amount: {event.amount_nqt / 100_000_000:.4f} SIGNA")
        print(f"  Task:   {event.task_description[:200]}")

        result = do_work(event.task_description)

        _, err = submit_result(
            worker_passphrase=args.passphrase,
            escrow_id=event.escrow_id,
            result_content=result,
            network=args.network,
        )
        if err:
            print(f"  Submit failed: {err}")
        else:
            print(f"  Result submitted on-chain.")

    listener.run(once=args.once)


if __name__ == "__main__":
    main()
