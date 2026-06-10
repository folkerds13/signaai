# Changelog

## 0.3.1 — 2026-06-10

Security and packaging fixes found during the Phase 1 skill conversion.

### Security
- **`wallet.get_my_address` no longer sends the passphrase to the node.**
  0.3.0 passed `secretPhrase` as a GET query parameter to public Signum
  nodes. The key pair is now derived locally (`signaai.crypto`) and only the
  public key leaves the process. (POST transactions were already signed
  locally and were never affected.)
- **README examples scrubbed** — no literal passphrases in any Python or CLI
  example; all use `env:WALLET_SECRET` / `os.environ` forms.

### Fixed
- **Removed `sys.path.insert(0, <package dir>)` from five modules**
  (arbitration, at_escrow, escrow, verify, wallet) — a leftover from their
  script origins that put the installed package directory at the front of
  `sys.path` and shadowed any caller's top-level modules named `verify`,
  `escrow`, `wallet`, etc.
- **`cli_secrets` `@worker` now checks all worker config locations**
  (`~/.openclaw/signaai-worker.json`, `~/.openclaw/workspace/…`,
  `~/.hermes/signaai-worker.json`) instead of OpenClaw's only, and the
  config's `passphrase` value may itself be an `env:`/`@file:` spec.
- **`signaai-board` CLI now resolves passphrase specs** (`-`, `env:VAR`,
  `@worker`, `@file:PATH`) like every other CLI; 0.3.0 passed the raw
  argument through.
- `wallet.send_signa` uses the dynamic `fee_message()` for message
  transactions instead of the flat minimum (multi-KB messages underpaid).

### Added
- `identity.verify_agent(name)` + `signaai-identity verify <name>` —
  confirms an agent alias is owned by the address it claims (ported from the
  OpenClaw skill).

## 0.3.0 — 2026-06

- `signaai.board` — task board protocol (open/claim/accept/cancel/list).
- `signaai.events` — canonical event model (ERC-8183/8004-aware naming).
- `signaai.cli_secrets` — passphrase spec resolution for all CLIs.
- Local transaction signing — passphrase never leaves the machine on POST.
- CI switched to pytest.

## 0.2.0 and earlier

- Wallet, identity, verify, escrow, AT escrow, arbitration, protocol,
  listener primitives. Published from Machine 1; see git history.
