#!/usr/bin/env python3
"""
SignaAI Events — parse on-chain transactions into structured SignaAIEvent objects.

Used by the signaai.io dashboard and any indexer that needs human-readable
activity data without reimplementing protocol parsing.

Usage:
  from signaai.events import get_account_events, EventType

  events = get_account_events("S-PS4K-2KE2-8LEV-HD2YE", network="mainnet")
  for ev in events:
      print(ev.event_type, ev.escrow_id, ev.timestamp)

CLI:
  signaai-events <address> [--network mainnet] [--limit 50] [--all]
"""
import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .api import get_api, ok, ts
from .protocol import (
    parse_message,
    EscrowMessage,
    SigProof,
    TaskComplete,
    TaskRating,
    ArbitrationMessage,
    UnknownMessage,
    ProtocolError,
)


class EventType(str, Enum):
    ESCROW_CREATED   = "escrow_created"
    ESCROW_FUNDED    = "escrow_funded"
    TASK_ASSIGNED    = "task_assigned"
    RESULT_SUBMITTED = "result_submitted"
    ESCROW_RELEASED  = "escrow_released"
    ESCROW_REFUNDED  = "escrow_refunded"
    PROOF_STAMPED    = "proof_stamped"
    TASK_COMPLETED   = "task_completed"
    TASK_RATED       = "task_rated"
    ARBITRATION      = "arbitration"
    UNKNOWN          = "unknown"


@dataclass
class SignaAIEvent:
    event_type:  EventType
    tx_id:       str
    timestamp:   str
    sender:      str
    recipient:   str
    amount_nqt:  int = 0
    escrow_id:   str = ""
    result_hash: str = ""
    worker:      str = ""
    rating:      int = 0
    label:       str = ""
    raw_message: str = ""


def event_from_transaction(tx: dict) -> SignaAIEvent:
    """Convert a raw Signum API transaction dict to a SignaAIEvent."""
    attachment  = tx.get("attachment") or {}
    message     = attachment.get("message", "")
    tx_id       = tx.get("transaction", "")
    timestamp   = ts(tx.get("timestamp"))
    sender      = tx.get("senderRS") or tx.get("sender", "")
    recipient   = tx.get("recipientRS") or tx.get("recipient", "")
    amount_nqt  = int(tx.get("amountNQT", 0))

    base = dict(
        tx_id=tx_id,
        timestamp=timestamp,
        sender=sender,
        recipient=recipient,
        amount_nqt=amount_nqt,
        raw_message=message,
    )

    if not message:
        return SignaAIEvent(event_type=EventType.UNKNOWN, **base)

    try:
        parsed = parse_message(message)
    except ProtocolError:
        return SignaAIEvent(event_type=EventType.UNKNOWN, **base)

    if isinstance(parsed, EscrowMessage):
        action = parsed.action.upper()
        if action == "CREATE":
            return SignaAIEvent(
                event_type=EventType.ESCROW_CREATED,
                escrow_id=parsed.escrow_id,
                worker=parsed.worker,
                **base,
            )
        if action == "FUND":
            return SignaAIEvent(
                event_type=EventType.ESCROW_FUNDED,
                escrow_id=parsed.escrow_id,
                **base,
            )
        if action == "ASSIGN":
            return SignaAIEvent(
                event_type=EventType.TASK_ASSIGNED,
                escrow_id=parsed.escrow_id,
                worker=parsed.worker,
                **base,
            )
        if action == "SUBMIT":
            return SignaAIEvent(
                event_type=EventType.RESULT_SUBMITTED,
                escrow_id=parsed.escrow_id,
                result_hash=parsed.result_hash,
                **base,
            )
        if action == "RELEASE":
            return SignaAIEvent(
                event_type=EventType.ESCROW_RELEASED,
                escrow_id=parsed.escrow_id,
                worker=parsed.worker or parsed.participant,
                **base,
            )
        if action == "REFUND":
            return SignaAIEvent(
                event_type=EventType.ESCROW_REFUNDED,
                escrow_id=parsed.escrow_id,
                **base,
            )
        return SignaAIEvent(event_type=EventType.UNKNOWN, **base)

    if isinstance(parsed, SigProof):
        return SignaAIEvent(
            event_type=EventType.PROOF_STAMPED,
            result_hash=parsed.content_hash,
            label=parsed.label,
            **base,
        )

    if isinstance(parsed, TaskComplete):
        return SignaAIEvent(
            event_type=EventType.TASK_COMPLETED,
            result_hash=parsed.result_hash,
            rating=parsed.rating,
            **base,
        )

    if isinstance(parsed, TaskRating):
        return SignaAIEvent(
            event_type=EventType.TASK_RATED,
            escrow_id=parsed.escrow_id,
            worker=parsed.worker,
            result_hash=parsed.result_hash,
            rating=parsed.rating,
            **base,
        )

    if isinstance(parsed, ArbitrationMessage):
        return SignaAIEvent(
            event_type=EventType.ARBITRATION,
            escrow_id=parsed.escrow_id,
            **base,
        )

    return SignaAIEvent(event_type=EventType.UNKNOWN, **base)


def events_from_transactions(txs: list) -> List[SignaAIEvent]:
    """Convert a list of raw Signum transactions to SignaAIEvents."""
    return [event_from_transaction(tx) for tx in txs]


def get_account_events(
    address: str,
    limit: int = 100,
    network: Optional[str] = None,
    protocol_only: bool = True,
) -> List[SignaAIEvent]:
    """Fetch recent transactions for address and return as SignaAIEvents.

    Args:
        address: Signum RS address (S-XXXX-...) or numeric account ID
        limit: max transactions to fetch (capped at 500 by the node)
        network: "mainnet" or "testnet" (defaults to SIGNUM_NETWORK env var)
        protocol_only: if True, filter out UNKNOWN events
    """
    api = get_api(network)
    result = api.get(
        "getAccountTransactions",
        account=address,
        firstIndex=0,
        lastIndex=limit - 1,
        includeIndirect="true",
    )
    if not ok(result):
        return []

    txs = result.get("transactions", [])
    events = events_from_transactions(txs)

    if protocol_only:
        events = [e for e in events if e.event_type != EventType.UNKNOWN]

    return events


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="SignaAI on-chain event log")
    parser.add_argument("address", help="Signum address (S-XXXX-...)")
    parser.add_argument("--network", default=os.environ.get("SIGNUM_NETWORK", "mainnet"),
                        choices=["mainnet", "testnet"])
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--all", dest="all_events", action="store_true",
                        help="Include UNKNOWN events")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    os.environ["SIGNUM_NETWORK"] = args.network

    events = get_account_events(
        args.address,
        limit=args.limit,
        network=args.network,
        protocol_only=not args.all_events,
    )

    if args.as_json:
        import json
        import dataclasses
        print(json.dumps([dataclasses.asdict(e) for e in events], indent=2))
        return

    if not events:
        print("No SignaAI events found.")
        return

    print(f"{'TYPE':<20} {'TIMESTAMP':<18} {'ESCROW / HASH':<20} {'RATING'}")
    print("-" * 75)
    for ev in events:
        detail = ev.escrow_id or ev.result_hash or ev.label or ""
        rating = str(ev.rating) if ev.rating else ""
        print(f"{ev.event_type.value:<20} {ev.timestamp:<18} {detail[:20]:<20} {rating}")


if __name__ == "__main__":
    main()
