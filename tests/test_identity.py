import unittest
from unittest.mock import patch

from signaai import identity


class ProfileApi:
    def get(self, request_type, **params):
        if request_type == "getAccount":
            return {
                "accountRS": "S-WORKER",
                "balanceNQT": "200000000",
            }
        if request_type == "getAccountTransactions":
            return {
                "transactions": [
                    {
                        "transaction": "rating-tx",
                        "timestamp": 0,
                        "senderRS": "S-PAYER",
                        "attachment": {
                            "message": "TASK_RATING:task-1:S-WORKER:hash:4"
                        },
                    },
                    {
                        "transaction": "self-tx",
                        "timestamp": 1,
                        "senderRS": "S-WORKER",
                        "attachment": {
                            "message": "TASK_COMPLETE:task-2:hash2:5"
                        },
                    },
                ]
            }
        return {}


class RatingApi:
    def __init__(self):
        self.last_request = None

    def post(self, request_type, **params):
        self.last_request = (request_type, params)
        return {"transaction": "rating-tx"}


class IdentityTests(unittest.TestCase):
    def test_profile_prefers_counterparty_ratings(self):
        with patch.object(identity, "get_api", return_value=ProfileApi()):
            profile, err = identity.get_agent_profile("S-WORKER")

        self.assertIsNone(err)
        self.assertEqual(profile["tasks_completed"], 1)
        self.assertEqual(profile["counterparty_ratings"], 1)
        self.assertEqual(profile["self_reported_tasks"], 1)
        self.assertEqual(profile["avg_rating"], 4)
        self.assertEqual(profile["task_history"][0]["rated_by"], "S-PAYER")

    def test_record_task_rating_sends_to_worker(self):
        api = RatingApi()
        with patch.object(identity, "get_api", return_value=api), \
             patch.object(identity, "get_my_address", return_value=("S-PAYER", None)):
            result, err = identity.record_task_rating(
                "secret",
                "task-1",
                "S-WORKER",
                "hash",
                rating=5,
            )

        self.assertIsNone(err)
        self.assertEqual(result["tx_id"], "rating-tx")
        request_type, params = api.last_request
        self.assertEqual(request_type, "sendMessage")
        self.assertEqual(params["recipient"], "S-WORKER")
        self.assertEqual(params["message"], "TASK_RATING:task-1:S-WORKER:hash:5")


if __name__ == "__main__":
    unittest.main()
