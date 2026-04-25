"""
SignaAI — AI Agent Infrastructure on Signum Blockchain

SDK stack for agent-to-agent payments, identity, verifiable outputs, escrow,
and arbitration.
Built on Signum's self-executing AT contracts (live since 2014).

Layers:
  signaai.wallet    — send/receive SIGNA, check balances
  signaai.identity  — register agents, build on-chain reputation
  signaai.verify    — hash and timestamp AI outputs on-chain
  signaai.escrow    — Phase 1 practical escrow (on-chain audit trail)
  signaai.at_escrow — Phase 2 trustless AT escrow (no operator needed)
  signaai.arbitration — dispute/open-vote records for escrow flows

Quick start:
  import signaai
  signaai.network("mainnet")

  bal = signaai.wallet.get_balance("S-YOUR-ADDRESS")
  signaai.identity.register_agent("passphrase", "my-agent", capabilities=["research"])
  signaai.verify.stamp("passphrase", "my output text", label="task-001")

Environment:
  Set SIGNUM_NETWORK=mainnet to default all calls to mainnet.
  Or call signaai.network("mainnet") at startup.
"""

import os
from . import wallet, identity, verify, escrow, at_escrow, arbitration
from .api import get_api, signa, nqt, ok

__version__ = "0.1.0"
__author__  = "SignaAI"


def network(net):
    """Set the default network for all SignaAI calls. Call once at startup.

    Args:
        net: "mainnet" or "testnet"

    Example:
        import signaai
        signaai.network("mainnet")
    """
    os.environ["SIGNUM_NETWORK"] = net
    get_api(net)  # initialize singleton
