#!/usr/bin/env python3
"""
SignaAI Listener — monitor a Signum address for SignaAI protocol events.

Framework-agnostic. No OpenClaw, no Hermes, no Telegram, no LLM.
Drop this into any Python agent and register callbacks.

Quick start:
    from signaai import SignaAIListener

    listener = SignaAIListener(address="S-YOUR-ADDRESS", network="mainnet")

    @listener.on_task_assigned
    def handle_task(event):
        print(f"Task: {event.task_description}")
        # do work, submit result...

    listener.run()

State is persisted in SIGNAAI_STATE_DIR (default ~/.signaai/) so the listener
resumes from where it left off across restarts.
"""
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .api import get_api, ok
from .protocol import parse_message, EscrowMessage, SigProof, TaskRating, ProtocolError


# ── State directory ───────────────────────────────────────────────────────────

def _default_state_dir():
    return os.environ.get(
        "SIGNAAI_STATE_DIR",
        os.path.expanduser("~/.signaai")
    )


# ── Event types ───────────────────────────────────────────────────────────────

@dataclass
class TaskEvent:
    """Fired when this address is assigned an escrow task."""
    escrow_id: str
    task_description: str
    payer_address: str
    worker_address: str
    amount_nqt: int
    deadline_block: int
    operator_address: str
    tx_id: str
    timestamp: int
    raw_message: str = ""


@dataclass
class ResultEvent:
    """Fired when a worker submits a result for an escrow."""
    escrow_id: str
    result_hash: str
    worker_address: str
    tx_id: str
    timestamp: int
    raw_message: str = ""


@dataclass
class ReleaseEvent:
    """Fired when an escrow is released."""
    escrow_id: str
    worker_address: str
    tx_id: str
    timestamp: int
    raw_message: str = ""


@dataclass
class ProofEvent:
    """Fired when a SIGPROOF stamp is seen on this address."""
    content_hash: str
    label: str
    sender_address: str
    tx_id: str
    timestamp: int
    raw_message: str = ""


@dataclass
class RatingEvent:
    """Fired when a payer sends a TASK_RATING for completed work."""
    escrow_id: str
    worker_address: str
    result_hash: str
    rating: int
    sender_address: str
    tx_id: str
    timestamp: int
    raw_message: str = ""


@dataclass
class RawEvent:
    """Fired for every incoming transaction with a parseable SignaAI message."""
    parsed: object          # EscrowMessage, SigProof, etc.
    sender_address: str
    tx_id: str
    timestamp: int
    raw_message: str = ""


# ── Listener ──────────────────────────────────────────────────────────────────

class SignaAIListener:
    """
    Monitor a Signum address for SignaAI protocol events.

    Register callbacks with the decorator API, then call run() to start:

        listener = SignaAIListener("S-XXXX-XXXX-XXXX-XXXXX", network="mainnet")

        @listener.on_task_assigned
        def handle(event: TaskEvent):
            ...

        listener.run()

    Or poll manually:

        listener.poll_once()
    """

    def __init__(
        self,
        address: str,
        network: str = "mainnet",
        poll_interval: int = 120,
        state_dir: Optional[str] = None,
        logger: Optional[Callable] = None,
    ):
        self.address       = address
        self.network       = network
        self.poll_interval = poll_interval
        self.state_dir     = state_dir or _default_state_dir()
        self._log          = logger or self._default_log

        self._on_task_assigned:   List[Callable] = []
        self._on_result_received: List[Callable] = []
        self._on_escrow_released: List[Callable] = []
        self._on_proof_stamped:   List[Callable] = []
        self._on_rating_received: List[Callable] = []
        self._on_raw:             List[Callable] = []

        self._state = self._load_state()

    # ── Decorator registration ─────────────────────────────────────────────────

    def on_task_assigned(self, fn: Callable) -> Callable:
        """Register a handler for ESCROW:ASSIGN / ESCROW:CREATE events where
        this address is the worker. Called with a TaskEvent."""
        self._on_task_assigned.append(fn)
        return fn

    def on_result_received(self, fn: Callable) -> Callable:
        """Register a handler for ESCROW:SUBMIT events. Called with a ResultEvent."""
        self._on_result_received.append(fn)
        return fn

    def on_escrow_released(self, fn: Callable) -> Callable:
        """Register a handler for ESCROW:RELEASE events. Called with a ReleaseEvent."""
        self._on_escrow_released.append(fn)
        return fn

    def on_proof_stamped(self, fn: Callable) -> Callable:
        """Register a handler for SIGPROOF messages. Called with a ProofEvent."""
        self._on_proof_stamped.append(fn)
        return fn

    def on_rating_received(self, fn: Callable) -> Callable:
        """Register a handler for TASK_RATING events. Called with a RatingEvent."""
        self._on_rating_received.append(fn)
        return fn

    def on_message(self, fn: Callable) -> Callable:
        """Catch-all handler for every parseable incoming message. Called with a RawEvent."""
        self._on_raw.append(fn)
        return fn

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self, once: bool = False):
        """
        Start the listener loop. Blocks until interrupted.

        Args:
            once: If True, poll once and return (useful for cron/testing).
        """
        self._log(f"SignaAI listener starting — {self.address} on {self.network}")
        self._log(f"State: {self._state_path()}")

        if once:
            self.poll_once()
            return

        while True:
            try:
                self.poll_once()
            except KeyboardInterrupt:
                self._log("Stopped.")
                break
            except Exception as e:
                self._log(f"Poll error: {e}")
            time.sleep(self.poll_interval)

    def poll_once(self):
        """Poll for new transactions and fire any matching callbacks."""
        api = get_api(self.network)
        result = api.get(
            "getAccountTransactions",
            account=self.address,
            timestamp=self._state.get("last_seen_timestamp", 0),
            firstIndex="0",
            lastIndex="49",
        )
        if not ok(result):
            self._log(f"API error: {result.get('error')}")
            return

        txs = result.get("transactions") or []
        seen = set(self._state.get("recent_tx_ids", []))
        newest_ts = self._state.get("last_seen_timestamp", 0)
        fired = 0

        for tx in txs:
            tx_id = str(tx.get("transaction", ""))
            if tx_id in seen:
                continue

            attachment = tx.get("attachment") or {}
            raw = attachment.get("message", "")
            if not raw:
                continue

            sender = tx.get("senderRS") or tx.get("sender", "")
            ts     = tx.get("timestamp", 0)

            try:
                parsed = parse_message(raw)
            except (ProtocolError, Exception):
                continue

            fired += self._dispatch(parsed, sender, tx_id, ts, raw)
            seen.add(tx_id)
            if ts > newest_ts:
                newest_ts = ts

        # Keep recent_tx_ids bounded
        recent = list(seen)[-200:]
        self._state["recent_tx_ids"]       = recent
        self._state["last_seen_timestamp"] = newest_ts
        self._save_state()

        if not fired:
            self._log("No new events")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _dispatch(self, parsed, sender, tx_id, ts, raw) -> int:
        fired = 0

        # Catch-all first
        if self._on_raw:
            ev = RawEvent(parsed=parsed, sender_address=sender,
                          tx_id=tx_id, timestamp=ts, raw_message=raw)
            for fn in self._on_raw:
                self._call(fn, ev)
            fired += 1

        if isinstance(parsed, EscrowMessage):
            action = parsed.action

            if action in ("ASSIGN", "CREATE") and parsed.worker == self.address:
                ev = TaskEvent(
                    escrow_id=parsed.escrow_id,
                    task_description=parsed.task_description,
                    payer_address=sender,
                    worker_address=parsed.worker,
                    amount_nqt=parsed.amount_nqt,
                    deadline_block=parsed.deadline_block,
                    operator_address=parsed.operator,
                    tx_id=tx_id,
                    timestamp=ts,
                    raw_message=raw,
                )
                for fn in self._on_task_assigned:
                    self._call(fn, ev)
                    fired += 1

            elif action == "SUBMIT":
                ev = ResultEvent(
                    escrow_id=parsed.escrow_id,
                    result_hash=parsed.result_hash,
                    worker_address=sender,
                    tx_id=tx_id,
                    timestamp=ts,
                    raw_message=raw,
                )
                for fn in self._on_result_received:
                    self._call(fn, ev)
                    fired += 1

            elif action == "RELEASE":
                ev = ReleaseEvent(
                    escrow_id=parsed.escrow_id,
                    worker_address=parsed.worker,
                    tx_id=tx_id,
                    timestamp=ts,
                    raw_message=raw,
                )
                for fn in self._on_escrow_released:
                    self._call(fn, ev)
                    fired += 1

        elif isinstance(parsed, SigProof):
            ev = ProofEvent(
                content_hash=parsed.content_hash,
                label=parsed.label,
                sender_address=sender,
                tx_id=tx_id,
                timestamp=ts,
                raw_message=raw,
            )
            for fn in self._on_proof_stamped:
                self._call(fn, ev)
                fired += 1

        elif isinstance(parsed, TaskRating):
            ev = RatingEvent(
                escrow_id=parsed.escrow_id,
                worker_address=parsed.worker,
                result_hash=parsed.result_hash,
                rating=parsed.rating,
                sender_address=sender,
                tx_id=tx_id,
                timestamp=ts,
                raw_message=raw,
            )
            for fn in self._on_rating_received:
                self._call(fn, ev)
                fired += 1

        return fired

    def _call(self, fn, event):
        try:
            fn(event)
        except Exception as e:
            self._log(f"Handler {fn.__name__} raised: {e}")

    def _state_path(self) -> str:
        safe_addr = self.address.replace("-", "")
        os.makedirs(os.path.join(self.state_dir, self.network), exist_ok=True)
        return os.path.join(self.state_dir, self.network, f"{safe_addr}.json")

    def _load_state(self) -> dict:
        path = self._state_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"last_seen_timestamp": 0, "recent_tx_ids": []}

    def _save_state(self):
        path = self._state_path()
        tmp  = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self._state, f, indent=2)
        os.replace(tmp, path)

    @staticmethod
    def _default_log(msg: str):
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="SignaAI Listener — monitor address for events")
    parser.add_argument("address",   help="Signum address to monitor (S-XXXX-...)")
    parser.add_argument("--network", default=os.environ.get("SIGNUM_NETWORK", "mainnet"))
    parser.add_argument("--interval", type=int, default=120, help="Poll interval seconds")
    parser.add_argument("--once",    action="store_true", help="Poll once and exit")
    parser.add_argument("--state-dir", default=None, help="State directory (default: ~/.signaai)")
    args = parser.parse_args()

    listener = SignaAIListener(
        address=args.address,
        network=args.network,
        poll_interval=args.interval,
        state_dir=args.state_dir,
    )

    @listener.on_task_assigned
    def log_task(event):
        print(f"  TASK ASSIGNED  escrow={event.escrow_id}")
        print(f"    payer:  {event.payer_address}")
        print(f"    amount: {event.amount_nqt / 100_000_000:.4f} SIGNA")
        print(f"    task:   {event.task_description[:120]}")

    @listener.on_result_received
    def log_result(event):
        print(f"  RESULT RECEIVED  escrow={event.escrow_id}  hash={event.result_hash[:16]}...")

    @listener.on_escrow_released
    def log_release(event):
        print(f"  ESCROW RELEASED  escrow={event.escrow_id}  worker={event.worker_address}")

    @listener.on_proof_stamped
    def log_proof(event):
        print(f"  PROOF STAMPED  label={event.label}  hash={event.content_hash[:16]}...")

    listener.run(once=args.once)


if __name__ == "__main__":
    main()
