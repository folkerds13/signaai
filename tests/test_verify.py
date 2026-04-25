import hashlib
import unittest
from unittest.mock import patch

from signaai import verify


class VerifyTests(unittest.TestCase):
    def test_hash_content_normalizes_sources(self):
        from_string = verify.hash_content("answer", "https://b, https://a")
        from_list = verify.hash_content("answer", ["https://a", "https://b"])
        self.assertEqual(from_string["sources_hash"], from_list["sources_hash"])
        self.assertEqual(from_string["combined_hash"], from_list["combined_hash"])

    def test_stamp_hashes_and_publishes(self):
        content_hash = hashlib.sha256(b"answer").hexdigest()
        with patch.object(verify, "publish_proof") as publish:
            publish.return_value = ({"tx_id": "tx-1"}, None)
            result, err = verify.stamp("secret", "answer", label="task-1")

        self.assertIsNone(err)
        self.assertEqual(result["hash"], content_hash)
        self.assertEqual(result["tx_id"], "tx-1")
        publish.assert_called_once()


if __name__ == "__main__":
    unittest.main()
