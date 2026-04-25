import unittest
from unittest.mock import patch

from signaai import wallet


class FakeApi:
    def __init__(self):
        self.last_request = None

    def post(self, request_type, **params):
        self.last_request = (request_type, params)
        return {"transaction": "123"}


class WalletTests(unittest.TestCase):
    def test_send_accepts_amount_keyword_and_uses_exact_nqt(self):
        api = FakeApi()
        with patch.object(wallet, "get_api", return_value=api):
            tx_id, err = wallet.send_signa("secret", "S-RECIPIENT", amount="0.29")

        self.assertIsNone(err)
        self.assertEqual(tx_id, "123")
        request_type, params = api.last_request
        self.assertEqual(request_type, "sendMoney")
        self.assertEqual(params["amountNQT"], 29_000_000)

    def test_send_rejects_missing_or_zero_amount(self):
        tx_id, err = wallet.send_signa("secret", "S-RECIPIENT")
        self.assertIsNone(tx_id)
        self.assertIn("Amount is required", err)

        tx_id, err = wallet.send_signa("secret", "S-RECIPIENT", amount="0")
        self.assertIsNone(tx_id)
        self.assertIn("greater than zero", err)


if __name__ == "__main__":
    unittest.main()
