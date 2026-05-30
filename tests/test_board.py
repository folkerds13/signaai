"""Tests for signaai.board protocol primitives (network-free)."""
import pytest
from signaai.protocol import (
    build_task_open, build_task_claim, build_task_accept, build_task_cancel,
    build_task_message, parse_task, parse_message,
    TaskMessage, TASK_PREFIX, ProtocolError,
)
from signaai.board import _resolve_board


# ── Protocol builder / parser round-trips ─────────────────────────────────────

def test_task_open_roundtrip():
    msg = build_task_open(
        task_id="abc12345",
        payer_address="S-AAAA-BBBB-CCCC-DDDDD",
        capability_tag="research",
        amount_nqt=100_000_000,
        deadline_block=5000,
        task_hash="deadbeef" * 8,
        task_summary="Find top blockchains",
    )
    assert msg.startswith("TASK:OPEN:v1:")
    parsed = parse_task(msg)
    assert parsed.action == "OPEN"
    assert parsed.task_id == "abc12345"
    assert parsed.payer_address == "S-AAAA-BBBB-CCCC-DDDDD"
    assert parsed.capability_tag == "research"
    assert parsed.amount_nqt == 100_000_000
    assert parsed.deadline_block == 5000
    assert parsed.task_summary == "Find top blockchains"


def test_task_claim_roundtrip():
    msg = build_task_claim("abc12345", "S-WORK-AAAA-BBBB-CCCCC")
    assert msg.startswith("TASK:CLAIM:v1:")
    parsed = parse_task(msg)
    assert parsed.action == "CLAIM"
    assert parsed.task_id == "abc12345"
    assert parsed.worker_address == "S-WORK-AAAA-BBBB-CCCCC"


def test_task_accept_roundtrip():
    msg = build_task_accept("abc12345", "S-WORK-AAAA-BBBB-CCCCC")
    assert msg.startswith("TASK:ACCEPT:v1:")
    parsed = parse_task(msg)
    assert parsed.action == "ACCEPT"
    assert parsed.task_id == "abc12345"
    assert parsed.worker_address == "S-WORK-AAAA-BBBB-CCCCC"


def test_task_cancel_roundtrip():
    msg = build_task_cancel("abc12345")
    assert msg.startswith("TASK:CANCEL:v1:")
    parsed = parse_task(msg)
    assert parsed.action == "CANCEL"
    assert parsed.task_id == "abc12345"


def test_task_message_dataclass_roundtrip():
    task = TaskMessage(
        action="OPEN",
        task_id="xyz99",
        payer_address="S-PAY-AAAA-BBBB-CCCCC",
        capability_tag="code",
        amount_nqt=200_000_000,
        deadline_block=9999,
        task_hash="cafebabe" * 8,
    )
    msg = task.to_message()
    parsed = parse_task(msg)
    assert parsed.task_id == "xyz99"
    assert parsed.capability_tag == "code"


def test_parse_message_dispatches_task():
    msg = build_task_open("t1", "S-A", "research", 0, 100, "hash")
    parsed = parse_message(msg)
    assert isinstance(parsed, TaskMessage)
    assert parsed.action == "OPEN"


def test_task_open_no_summary():
    msg = build_task_open("t2", "S-B", "", 0, 200, "hash")
    parsed = parse_task(msg)
    assert parsed.task_summary == ""


def test_capability_colon_sanitized():
    msg = build_task_open("t3", "S-C", "re:search", 0, 300, "hash")
    parsed = parse_task(msg)
    assert ":" not in parsed.capability_tag


def test_malformed_task_raises():
    with pytest.raises(ProtocolError):
        parse_task("TASK:OPEN:v1:onlyone")


def test_resolve_board_env(monkeypatch):
    monkeypatch.setenv("SIGNAAI_BOARD", "S-BOARD-TEST")
    assert _resolve_board(None) == "S-BOARD-TEST"


def test_resolve_board_explicit():
    assert _resolve_board("S-EXPLICIT") == "S-EXPLICIT"


def test_resolve_board_missing(monkeypatch):
    monkeypatch.delenv("SIGNAAI_BOARD", raising=False)
    with pytest.raises(ValueError, match="board_address is required"):
        _resolve_board(None)
