import unittest

from signaai.api import nqt


class NqtConversionTests(unittest.TestCase):
    def test_decimal_amounts_are_exact(self):
        self.assertEqual(nqt("0.29"), 29_000_000)
        self.assertEqual(nqt("1.00000001"), 100_000_001)
        self.assertEqual(nqt("0.000000019"), 1)

    def test_invalid_amounts_raise(self):
        with self.assertRaises(ValueError):
            nqt("-1")
        with self.assertRaises(ValueError):
            nqt("not-a-number")


if __name__ == "__main__":
    unittest.main()
