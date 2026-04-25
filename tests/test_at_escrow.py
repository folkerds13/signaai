import unittest

from signaai import at_escrow


class AtEscrowTests(unittest.TestCase):
    def test_data_field_matches_contract_layout(self):
        preimage = "00" * 32
        data = at_escrow.build_data_field_for_deadline(
            preimage,
            worker_account_id=42,
            deadline_block=1000,
        )

        self.assertEqual(len(data), 96)
        self.assertTrue(data.startswith(at_escrow.encode_long_le(42)))
        self.assertEqual(data[16:32], at_escrow.encode_long_le(1000))

    def test_preimage_generation_returns_hex_values(self):
        preimage, digest = at_escrow.gen_preimage()
        self.assertEqual(len(preimage), 64)
        self.assertEqual(len(digest), 64)
        int(preimage, 16)
        int(digest, 16)


if __name__ == "__main__":
    unittest.main()
