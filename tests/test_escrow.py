import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from signaai import escrow


class EscrowTests(unittest.TestCase):
    def test_parse_escrow_state_requires_exact_id(self):
        txs = [
            {
                "transaction": "create-tx",
                "timestamp": 0,
                "senderRS": "S-PAYER",
                "recipientRS": "S-OPERATOR",
                "attachment": {
                    "message": "ESCROW:CREATE:abc123:S-WORKER:100000000:taskhash:500:S-OPERATOR"
                },
            },
            {
                "transaction": "submit-tx",
                "timestamp": 1,
                "senderRS": "S-WORKER",
                "attachment": {
                    "message": "ESCROW:SUBMIT:abc123:resulthash"
                },
            },
            {
                "transaction": "wrong-tx",
                "timestamp": 1,
                "senderRS": "S-WORKER",
                "attachment": {
                    "message": "ESCROW:SUBMIT:abc123-extra:wrong"
                },
            },
        ]

        state, err = escrow._parse_escrow_from_txs("abc123", txs)

        self.assertIsNone(err)
        self.assertEqual(state["state"], escrow.STATE_SUBMITTED)
        self.assertEqual(state["payer"], "S-PAYER")
        self.assertEqual(state["worker"], "S-WORKER")
        self.assertEqual(state["operator"], "S-OPERATOR")
        self.assertEqual(state["submitted_hash"], "resulthash")

    def test_create_requires_operator_address(self):
        result, err = escrow.create_escrow(
            "payer secret",
            "S-WORKER",
            1,
            "task",
            network="testnet",
        )
        self.assertIsNone(result)
        self.assertIn("operator_address is required", err)

    def test_release_requires_hash_or_explicit_approval(self):
        status = {
            "state": escrow.STATE_SUBMITTED,
            "worker": "S-WORKER",
            "amount_signa": 1.0,
            "submitted_hash": "expected",
        }
        with patch.object(escrow, "get_my_address", return_value=("S-OPERATOR", None)), \
             patch.object(escrow, "get_escrow_status", return_value=(status, None)), \
             patch.object(escrow, "send_signa", return_value=("release-tx", None)):
            with redirect_stdout(StringIO()):
                result, err = escrow.release_payment("operator secret", "abc123")
                self.assertIsNone(result)
                self.assertIn("expected_result_hash", err)

                result, err = escrow.release_payment(
                    "operator secret",
                    "abc123",
                    expected_result_hash="wrong",
                )
                self.assertIsNone(result)
                self.assertIn("does not match", err)

                result, err = escrow.release_payment(
                    "operator secret",
                    "abc123",
                    expected_result_hash="expected",
                )
                self.assertIsNone(err)
                self.assertEqual(result["tx_id"], "release-tx")

    def test_release_with_rating_sends_task_rating(self):
        status = {
            "state": escrow.STATE_SUBMITTED,
            "worker": "S-WORKER",
            "amount_signa": 1.0,
            "submitted_hash": "resulthash",
        }
        rating_tx_sent = []

        def fake_post(request_type, **kwargs):
            if request_type == "sendMessage":
                rating_tx_sent.append(kwargs.get("message", ""))
                return {"transaction": "rating-tx"}
            return {}

        with patch.object(escrow, "get_my_address", return_value=("S-OPERATOR", None)), \
             patch.object(escrow, "get_escrow_status", return_value=(status, None)), \
             patch.object(escrow, "send_signa", return_value=("release-tx", None)), \
             patch.object(escrow.get_api("testnet"), "post", side_effect=fake_post):
            with redirect_stdout(StringIO()):
                result, err = escrow.release_payment(
                    "operator secret", "abc123",
                    expected_result_hash="resulthash",
                    rating=4,
                    network="testnet",
                )
            self.assertIsNone(err)
            self.assertEqual(result["rating"], 4)
            self.assertEqual(len(rating_tx_sent), 1)
            self.assertIn("TASK_RATING:v1:abc123:S-WORKER:resulthash:4", rating_tx_sent[0])


if __name__ == "__main__":
    unittest.main()
