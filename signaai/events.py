#!/usr/bin/env python3
"""
SignaAI event parsing.

This module turns raw Signum transactions into stable event dictionaries for
dashboards, indexers, agent runtimes, and tests. It is intentionally small:
network calls are optional, and protocol parsing is delegated to protocol.py.
"""
from dataclasses import asdict, is_dataclass
import os

from .api import get_api, ok, signa, ts
from .protocol import parse_message


def event_from_transaction(tx):
    """Normalize one Signum transaction into a SignaAI event dictionary."""
    attachment = tx.get("attachment") or {}
    message = attachment.get("message", "")
    amount_signa = signa(tx.get("amountNQT", 0))
    parsed = parse_message(message) if message else None

    protocol_kind = None
    protocol = None
    if parsed and getattr(parsed, "kind", "unknown") != "unknown":
        protocol_kind = parsed.kind
        protocol = _dataclass_dict(parsed)

    event_type = "payment" if amount_signa else "message"
    if protocol_kind:
        event_type = protocol_kind

    return {
        "tx_id": tx.get("transaction"),
        "timestamp": ts(tx.get("timestamp")),
        "sender": tx.get("senderRS", tx.get("sender", "")),
        "recipient": tx.get("recipientRS", tx.get("recipient", "")),
        "amount_signa": amount_signa,
        "fee_signa": signa(tx.get("feeNQT", 0)),
        "confirmations": tx.get("confirmations", 0),
        "message": message,
        "event_type": event_type,
        "protocol_kind": protocol_kind,
        "protocol": protocol,
    }


def events_from_transactions(transactions, protocol_only=False):
    """Normalize a list of raw transactions."""
    events = [event_from_transaction(tx) for tx in transactions]
    if protocol_only:
        return [event for event in events if event["protocol_kind"]]
    return events


def get_account_events(address, limit=100, network=None, protocol_only=False):
    """Fetch and normalize recent events for one account."""
    api = get_api(network)
    result = api.get("getAccountTransactions",
                     account=address,
                     firstIndex=0,
                     lastIndex=max(0, limit - 1))
    if not ok(result):
        return [], result.get("error", "Could not fetch transactions")
    return events_from_transactions(
        result.get("transactions", []),
        protocol_only=protocol_only,
    ), None


def _dataclass_dict(value):
    if is_dataclass(value):
        data = asdict(value)
    else:
        data = dict(value)
    data["kind"] = getattr(value, "kind", data.get("kind"))
    return data


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SignaAI event parser")
    parser.add_argument("--network", default=os.environ.get("SIGNUM_NETWORK", "testnet"),
                        choices=["mainnet", "testnet"])
    parser.add_argument("address")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--protocol-only", action="store_true")
    args = parser.parse_args()

    events, err = get_account_events(
        args.address,
        limit=args.limit,
        network=args.network,
        protocol_only=args.protocol_only,
    )
    if err:
        print(f"Error: {err}")
        return

    for event in events:
        label = event["protocol_kind"] or event["event_type"]
        amount = f" {event['amount_signa']:.4f} SIGNA" if event["amount_signa"] else ""
        print(f"{event['timestamp']} {label:<14} {event['tx_id']}{amount}")


if __name__ == "__main__":
    main()
