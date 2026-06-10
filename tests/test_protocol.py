import unittest

from signaai import protocol


class ProtocolTests(unittest.TestCase):
    def test_sigproof_round_trip(self):
        msg = protocol.build_sigproof("abc", "def", "task:one")
        parsed = protocol.parse_message(msg)

        self.assertEqual(msg, "SIGPROOF:v1:abc:def:task-one")
        self.assertEqual(parsed.kind, "sigproof")
        self.assertEqual(parsed.content_hash, "abc")
        self.assertEqual(parsed.sources_hash, "def")
        self.assertEqual(parsed.label, "task-one")
        self.assertEqual(parsed.to_message(), msg)

    def test_escrow_create_round_trip(self):
        msg = protocol.build_escrow_create(
            "escrow-1",
            "S-WORKER",
            100000000,
            "taskhash",
            1234,
            "S-OPERATOR",
        )
        parsed = protocol.parse_message(msg)

        self.assertEqual(parsed.kind, "escrow")
        self.assertEqual(parsed.action, "CREATE")
        self.assertEqual(parsed.escrow_id, "escrow-1")
        self.assertEqual(parsed.worker, "S-WORKER")
        self.assertEqual(parsed.amount_nqt, 100000000)
        self.assertEqual(parsed.deadline_block, 1234)
        self.assertEqual(parsed.operator, "S-OPERATOR")
        self.assertEqual(parsed.to_message(), msg)

    def test_versioned_escrow_assign_parse(self):
        msg = "ESCROW:ASSIGN:v1:escrow-1:taskhash:do the work"
        parsed = protocol.parse_message(msg)

        self.assertEqual(parsed.action, "ASSIGN")
        self.assertEqual(parsed.version, "v1")
        self.assertEqual(parsed.escrow_id, "escrow-1")
        self.assertEqual(parsed.task_hash, "taskhash")
        self.assertEqual(parsed.task_description, "do the work")

    def test_task_complete_rating_validation(self):
        msg = protocol.build_task_complete("task-1", "hash", 5)
        parsed = protocol.parse_message(msg)
        self.assertEqual(parsed.rating, 5)

        with self.assertRaises(protocol.ProtocolError):
            protocol.build_task_complete("task-1", "hash", 6)
        with self.assertRaises(protocol.ProtocolError):
            protocol.parse_message("TASK_COMPLETE:task-1:hash:6")

    def test_task_rating_round_trip(self):
        msg = protocol.build_task_rating("task-1", "S-WORKER", "hash", 4)
        parsed = protocol.parse_message(msg)

        self.assertEqual(msg, "TASK_RATING:task-1:S-WORKER:hash:4")
        self.assertEqual(parsed.kind, "task_rating")
        self.assertEqual(parsed.task_id, "task-1")
        self.assertEqual(parsed.worker, "S-WORKER")
        self.assertEqual(parsed.result_hash, "hash")
        self.assertEqual(parsed.rating, 4)
        self.assertEqual(parsed.to_message(), msg)

        with self.assertRaises(protocol.ProtocolError):
            protocol.build_task_rating("task-1", "S-WORKER", "hash", 0)

    def test_arbitration_round_trip(self):
        msg = protocol.build_arbit_vote("escrow-1", "release", "noteshash")
        parsed = protocol.parse_message(msg)

        self.assertEqual(msg, "ARBIT_VOTE:escrow-1:RELEASE:noteshash")
        self.assertEqual(parsed.kind, "arbitration")
        self.assertEqual(parsed.action, "VOTE")
        self.assertEqual(parsed.decision, "RELEASE")
        self.assertEqual(parsed.to_message(), msg)

    def test_unknown_message(self):
        parsed = protocol.parse_message("HELLO")
        self.assertEqual(parsed.kind, "unknown")
        self.assertEqual(parsed.to_message(), "HELLO")


if __name__ == "__main__":
    unittest.main()
