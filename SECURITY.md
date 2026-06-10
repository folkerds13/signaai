# Security Policy

SignaAI is alpha infrastructure. Use testnet while developing, and handle
mainnet wallets as real funds.

## Passphrases

- Do not paste real wallet passphrases into shared shells, logs, issue reports,
  screenshots, or chat transcripts.
- CLI commands accept `-` where a passphrase is expected, which prompts without
  writing the passphrase to shell history.
- CLI commands also accept `env:VAR_NAME` for agent runtimes that inject secrets
  through environment variables.
- SDK callers are responsible for storing passphrases securely in their runtime.

## Escrow

- `escrow.py` is operator-mediated. It creates an auditable on-chain trail, but
  funds are held by the operator wallet.
- `at_escrow.py` is the trustless path. Validate AT behavior on testnet before
  handling meaningful value.
- On-chain proof records prove content integrity and timestamp. They do not
  prove factual correctness.

## Reporting Issues

Please report security issues privately to the maintainer before public
disclosure. Include affected version, transaction IDs if relevant, and a minimal
reproduction that does not expose wallet secrets.
