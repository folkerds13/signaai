import unittest

from signaai import protocol
from signaai.events import EventType, SignaAIEvent, event_from_transaction, events_from_transactions


def _tx(message="", amount=0, sender="S-SENDER", recipient="S-RECV", tx_id="tx1", timestamp=100):
    return {
        "transaction": tx_id,
        "timestamp": timestamp,
        "senderRS": sender,
        "recipientRS": recipient,
        "amountNQT": amount,
        "attachment": {"message": message} if message else {},
    }


class TestEventFromTransaction(unittest.TestCase):
    def test_no_message_is_unknown(self):
        ev = event_from_transaction(_tx())
        self.assertEqual(ev.event_type, EventType.UNKNOWN)

    def test_escrow_created(self):
        msg = protocol.build_escrow_create("esc-1", "S-W", 100000000, "thash", 9999)
        ev = event_from_transaction(_tx(msg, amount=100000000))
        self.assertEqual(ev.event_type, EventType.ESCROW_CREATED)
        self.assertEqual(ev.escrow_id, "esc-1")
        self.assertEqual(ev.worker, "S-W")
        self.assertEqual(ev.amount_nqt, 100000000)

    def test_escrow_funded(self):
        msg = protocol.build_escrow_fund("esc-1")
        ev = event_from_transaction(_tx(msg))
        self.assertEqual(ev.event_type, EventType.ESCROW_FUNDED)
        self.assertEqual(ev.escrow_id, "esc-1")

    def test_task_assigned(self):
        msg = protocol.build_escrow_assign("esc-2", "thash", "do the thing")
        ev = event_from_transaction(_tx(msg))
        self.assertEqual(ev.event_type, EventType.TASK_ASSIGNED)
        self.assertEqual(ev.escrow_id, "esc-2")

    def test_result_submitted(self):
        msg = protocol.build_escrow_submit("esc-3", "resulthash")
        ev = event_from_transaction(_tx(msg))
        self.assertEqual(ev.event_type, EventType.RESULT_SUBMITTED)
        self.assertEqual(ev.escrow_id, "esc-3")
        self.assertEqual(ev.result_hash, "resulthash")

    def test_escrow_released(self):
        msg = protocol.build_escrow_release("esc-4", "S-W")
        ev = event_from_transaction(_tx(msg))
        self.assertEqual(ev.event_type, EventType.ESCROW_RELEASED)
        self.assertEqual(ev.escrow_id, "esc-4")

    def test_escrow_refunded(self):
        msg = protocol.build_escrow_refund("esc-5", "S-P")
        ev = event_from_transaction(_tx(msg))
        self.assertEqual(ev.event_type, EventType.ESCROW_REFUNDED)
        self.assertEqual(ev.escrow_id, "esc-5")

    def test_proof_stamped(self):
        msg = protocol.build_sigproof("chash", "shash", "my-task")
        ev = event_from_transaction(_tx(msg))
        self.assertEqual(ev.event_type, EventType.PROOF_STAMPED)
        self.assertEqual(ev.result_hash, "chash")
        self.assertEqual(ev.label, "my-task")

    def test_task_completed(self):
        msg = protocol.build_task_complete("task-1", "rhash", 4)
        ev = event_from_transaction(_tx(msg))
        self.assertEqual(ev.event_type, EventType.TASK_COMPLETED)
        self.assertEqual(ev.result_hash, "rhash")
        self.assertEqual(ev.rating, 4)

    def test_task_rated(self):
        msg = protocol.build_task_rating("esc-6", "S-W", "rhash", 5)
        ev = event_from_transaction(_tx(msg))
        self.assertEqual(ev.event_type, EventType.TASK_RATED)
        self.assertEqual(ev.escrow_id, "esc-6")
        self.assertEqual(ev.worker, "S-W")
        self.assertEqual(ev.rating, 5)

    def test_arbitration(self):
        msg = protocol.build_arbit_open("esc-7", "S-CLAIMANT", "rhash")
        ev = event_from_transaction(_tx(msg))
        self.assertEqual(ev.event_type, EventType.ARBITRATION)
        self.assertEqual(ev.escrow_id, "esc-7")

    def test_unknown_message_is_unknown(self):
        ev = event_from_transaction(_tx("RANDOM_GARBAGE"))
        self.assertEqual(ev.event_type, EventType.UNKNOWN)

    def test_tx_fields_preserved(self):
        msg = protocol.build_sigproof("h", "", "")
        ev = event_from_transaction(_tx(msg, tx_id="txABC", sender="S-AAA", recipient="S-BBB"))
        self.assertEqual(ev.tx_id, "txABC")
        self.assertEqual(ev.sender, "S-AAA")
        self.assertEqual(ev.recipient, "S-BBB")

    def test_events_from_transactions_list(self):
        txs = [
            _tx(protocol.build_escrow_create("e1", "S-W", 0, "h", 1), tx_id="t1"),
            _tx("GARBAGE", tx_id="t2"),
            _tx(protocol.build_sigproof("ch", "", ""), tx_id="t3"),
        ]
        events = events_from_transactions(txs)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].event_type, EventType.ESCROW_CREATED)
        self.assertEqual(events[1].event_type, EventType.UNKNOWN)
        self.assertEqual(events[2].event_type, EventType.PROOF_STAMPED)

    def test_event_is_dataclass(self):
        ev = event_from_transaction(_tx())
        self.assertIsInstance(ev, SignaAIEvent)


if __name__ == "__main__":
    unittest.main()
