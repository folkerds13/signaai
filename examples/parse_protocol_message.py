#!/usr/bin/env python3
"""Parse a SignaAI protocol message into structured fields."""
import argparse
from dataclasses import asdict, is_dataclass
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from signaai import protocol


def main():
    parser = argparse.ArgumentParser(description="Parse a SignaAI protocol message")
    parser.add_argument("message")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    parsed = protocol.parse_message(args.message, strict=args.strict)
    if is_dataclass(parsed):
        payload = asdict(parsed)
    else:
        payload = {"raw": parsed.to_message()}
    payload["kind"] = parsed.kind
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
