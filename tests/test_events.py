import unittest
from unittest.mock import patch

from signaai import events


class FakeApi:
    def get(self, request_type, **params):
        self.last_request = (request_type, params)
        return {
            "transactions": [
                {
                    "transaction": "tx-1",
                    "timestamp": 0,
                    "senderRS": "S-PAYER",
                    "recipientRS": "S-WORKER",
                    "amountNQT": "0",
                    "feeNQT": "10000000",
                    "confirmations": 5,
                    "attachment": {
                        "message": "TASK_RATING:task-1:S-WORKER:hash:5"
                    },
                },
                {
                    "transaction": "tx-2",
                    "timestamp": 1,
                    "senderRS": "S-PAYER",
                    "recipientRS": "S-WORKER",
                    "amountNQT": "100000000",
                    "feeNQT": "735000",
                    "attachment": {},
                },
            ]
        }


class EventTests(unittest.TestCase):
    def test_event_from_transaction_parses_protocol_message(self):
        event = events.event_from_transaction({
            "transaction": "tx-1",
            "timestamp": 0,
            "senderRS": "S-PAYER",
            "recipientRS": "S-WORKER",
            "amountNQT": "0",
            "feeNQT": "10000000",
            "attachment": {
                "message": "TASK_RATING:task-1:S-WORKER:hash:5"
            },
        })

        self.assertEqual(event["event_type"], "task_rating")
        self.assertEqual(event["protocol_kind"], "task_rating")
        self.assertEqual(event["protocol"]["task_id"], "task-1")
        self.assertEqual(event["protocol"]["rating"], 5)

    def test_get_account_events_can_filter_protocol_events(self):
        api = FakeApi()
        with patch.object(events, "get_api", return_value=api):
            result, err = events.get_account_events(
                "S-WORKER",
                limit=10,
                protocol_only=True,
            )

        self.assertIsNone(err)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tx_id"], "tx-1")
        request_type, params = api.last_request
        self.assertEqual(request_type, "getAccountTransactions")
        self.assertEqual(params["lastIndex"], 9)


if __name__ == "__main__":
    unittest.main()
