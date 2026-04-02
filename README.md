# SignaAI

AI agent infrastructure on the Signum blockchain — payments, identity, verifiable outputs, and trustless escrow.

Built on Signum's self-executing AT (Automated Transaction) contracts, live since 2014. No Ethereum gas wars. No external keepers. Fixed fees around $0.00003 per transaction.

---

## Why Signum?

| Feature | Signum | Ethereum/Solana |
|---|---|---|
| Smart contract execution | Self-executing, no keeper | Requires external keeper or relayer |
| Transaction fee | ~$0.00003 fixed | Variable, often $1–$50+ |
| Energy use | <0.002% of Bitcoin | High (PoW) or validator overhead |
| Agent-to-agent payments | Native, 4-second blocks | Possible but expensive |
| Running since | 2014 (as Burstcoin) | 2015 / 2020 |

Competitors (Coinbase x402, ERC-8004, Fetch.ai/ASI, Olas) are all building on Ethereum or Solana. Signum is greenfield for AI agent infrastructure.

---

## Install

```bash
pip install signaai
```

Or from source (editable):

```bash
git clone https://github.com/your-org/signaai
cd signaai
pip install -e .
```

**No external dependencies** — uses Python stdlib only (urllib, hashlib, struct, secrets).

Requires Python 3.9+.

---

## Quick Start

```python
import signaai

# Set network once at startup
signaai.network("mainnet")  # or "testnet"

# Check a balance
bal, err = signaai.wallet.get_balance("S-YOUR-ADDRESS")
print(f"{bal['confirmed']:.4f} SIGNA")

# Register your agent
signaai.identity.register_agent(
    "your secret passphrase",
    "my-agent",
    capabilities=["research", "summarization"]
)

# Stamp an output on-chain
signaai.verify.stamp(
    "your secret passphrase",
    "The answer to the task is 42.",
    label="task-001"
)
```

---

## Layers

### Layer 1 — Wallet (agent-to-agent payments)

```python
from signaai import wallet

# Check balance
bal, err = wallet.get_balance("S-XXXX-XXXX-XXXX-XXXXX")
# bal = {"confirmed": 10.5, "unconfirmed": 10.5, "address": "S-..."}

# Send SIGNA
result, err = wallet.send_signa(
    "payer passphrase",
    recipient="S-XXXX-XXXX-XXXX-XXXXX",
    amount=5.0
)

# Transaction history
txs, err = wallet.get_transactions("S-XXXX-XXXX-XXXX-XXXXX", limit=10)
```

CLI:
```bash
signaai-wallet --network mainnet balance S-XXXX-XXXX-XXXX-XXXXX
signaai-wallet --network mainnet send "passphrase" S-XXXX-XXXX-XXXX-XXXXX 5.0
signaai-wallet --network mainnet history S-XXXX-XXXX-XXXX-XXXXX
```

---

### Layer 2 — Identity (agent registry and reputation)

Agents register a unique on-chain alias with a JSON profile (name, version, capabilities, endpoint).

```python
from signaai import identity

# Register your agent
result, err = identity.register_agent(
    "your passphrase",
    "my-research-agent",
    capabilities=["research", "web-search"],
    endpoint="https://myagent.example.com",
    version="1.0.0"
)

# Look up an agent by name
agent, err = identity.lookup_agent("my-research-agent")
# agent = {"name": "my-research-agent", "address": "S-...", "capabilities": [...], ...}

# Get reputation score (derived from transaction count and history)
rep, err = identity.get_reputation("S-XXXX-XXXX-XXXX-XXXXX")
```

CLI:
```bash
signaai-identity --network mainnet register "passphrase" my-agent --capabilities research summarization
signaai-identity --network mainnet lookup my-agent
signaai-identity --network mainnet reputation S-XXXX-XXXX-XXXX-XXXXX
```

---

### Layer 3 — Verify (tamper-proof output stamping)

Hash an AI output and record it on-chain before delivery. Anyone can verify the output hasn't been altered.

```python
from signaai import verify

# Stamp output on-chain
result, err = verify.stamp(
    "your passphrase",
    "The quarterly revenue was $4.2M, up 12% YoY.",
    label="report-2026-Q1"
)
# result = {"tx_id": "...", "hash": "sha256:abc123...", "block": 12345}

# Verify output matches on-chain record
ok, err = verify.check(
    "The quarterly revenue was $4.2M, up 12% YoY.",
    tx_id="<stamp tx id>"
)
```

CLI:
```bash
signaai-verify --network mainnet stamp "passphrase" "output text" --label task-001
signaai-verify --network mainnet check "output text" --tx TX_ID
```

---

### Layer 4 — Escrow (Phase 1: operator-mediated)

On-chain audit trail for agent task payments. An operator (trusted third party) releases or refunds.

```python
from signaai import escrow

# Payer creates escrow
result, err = escrow.create_escrow(
    "payer passphrase",
    worker_address="S-WORKER-ADDRESS",
    amount=10.0,
    task_description="Summarize these 5 documents",
    deadline_hours=24
)
escrow_id = result["escrow_id"]

# Check status
status, err = escrow.get_escrow_status(escrow_id, "operator passphrase")

# Operator releases payment after verifying work
result, err = escrow.release_payment(escrow_id, "operator passphrase")

# Or operator refunds payer
result, err = escrow.refund_escrow(escrow_id, "operator passphrase")
```

CLI:
```bash
signaai-escrow --network mainnet create "payer pass" S-WORKER 10.0 "task description" --deadline 24
signaai-escrow --network mainnet status ESCROW_ID "operator pass"
signaai-escrow --network mainnet release ESCROW_ID "operator pass"
signaai-escrow --network mainnet refund ESCROW_ID "operator pass"
```

---

### Layer 4 — AT Escrow (Phase 2: trustless, no operator)

A smart contract holds funds. The worker reveals a preimage → contract auto-pays. Deadline passes → contract auto-refunds. No operator, no trust required.

```python
from signaai import at_escrow

# 1. Generate a secret preimage
preimage, preimage_hash = at_escrow.gen_preimage()
# Store preimage securely — reveal only after verifying the worker's output

# 2. Deploy the escrow contract
result, err = at_escrow.deploy_at(
    "payer passphrase",
    worker_address="S-WORKER-ADDRESS",
    deadline_minutes=1440,  # 24 hours
    preimage_hex=preimage
)
at_address = result["at_address"]

# 3. Fund the contract (send SIGNA to the AT address)
wallet.send_signa("payer passphrase", at_address, amount=10.0)

# 4. Verify worker's output, then reveal the preimage to them
# Worker submits preimage — AT auto-pays, no operator needed
result, err = at_escrow.submit_preimage(
    "worker passphrase",
    at_address=at_address,
    preimage_hex=preimage
)

# Check AT state
info, err = at_escrow.get_at_info(at_address)
```

CLI:
```bash
# Generate preimage
signaai-at gen-preimage

# Deploy contract
signaai-at --network mainnet deploy "payer pass" S-WORKER 1440 PREIMAGE_HEX

# Fund it
signaai-wallet --network mainnet send "payer pass" S-AT-ADDRESS 10.0

# Worker claims payment
signaai-at --network mainnet submit "worker pass" S-AT-ADDRESS PREIMAGE_HEX

# Check status
signaai-at --network mainnet info S-AT-ADDRESS
```

---

## Environment Variables

```bash
export SIGNUM_NETWORK=mainnet  # default all calls to mainnet
```

Or call `signaai.network("mainnet")` once at startup.

---

## How AT Escrow Works (trustless flow)

```
Payer                          AT Contract                    Worker
  |                                |                              |
  |-- gen_preimage() ---------->   |                              |
  |   (preimage, hash)             |                              |
  |                                |                              |
  |-- deploy_at(hash, worker) ->   |                              |
  |   (AT address)                 |                              |
  |                                |                              |
  |-- send SIGNA to AT -------->   |                              |
  |                                |  (funds held trustlessly)   |
  |                                |                              |
  |   [verify worker output]       |                              |
  |-- reveal preimage ----------->  |  <-- submit_preimage() -- |
  |                                |                              |
  |                                |-- SHA256(preimage) match? --|
  |                                |   YES → sendBalance(worker) |
  |                                |   NO + deadline passed      |
  |                                |        → refund(creator)    |
```

The contract runs entirely on-chain. No API key, no server, no operator.

---

## Network Nodes

| Network | Node |
|---|---|
| Mainnet | europe.signum.network, us.signum.network |
| Testnet | europe3.testnet.signum.network |

Testnet SIGNA faucet: https://faucet.signum.network

---

## Architecture

```
signaai/
├── api.py          — HTTP client, NQT conversion, node failover
├── wallet.py       — SIGNA send/receive/history
├── identity.py     — Agent registry, reputation scoring
├── verify.py       — Output stamping and verification
├── escrow.py       — Phase 1 operator-mediated escrow
├── at_escrow.py    — Phase 2 trustless AT smart contract escrow
└── contracts/
    └── signaai_escrow.smart   — AT bytecode source
```

---

## License

MIT
