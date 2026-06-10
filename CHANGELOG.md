# Changelog

## 0.2.1

- Added `TASK_RATING` protocol messages for counterparty-signed reputation.
- Added `identity.record_task_rating()` and profile fields separating
  counterparty ratings from legacy self-reported completions.
- Added `signaai.events` and the `signaai-events` CLI for normalized
  transaction feeds.
- Added CLI passphrase prompting with `-` and `env:VAR_NAME` secret resolution.
- Synced package version metadata between `pyproject.toml` and `signaai.__version__`.

## 0.2.0

- Published Python SDK package with wallet, identity, verify, escrow, AT escrow,
  arbitration, protocol helpers, examples, and unit tests.
