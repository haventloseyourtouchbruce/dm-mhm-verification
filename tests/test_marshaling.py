import unittest
from harness.words import int64_word, uint32_word


class Marshaling(unittest.TestCase):
    def test_invalid_words(self):
        for value in [True, False, 1.5, -(1<<63)-1, 1<<63]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                int64_word(value)

    def test_endpoints(self):
        for value in [-(1<<63), 0, (1<<63)-1]:
            self.assertEqual(int64_word(value), value)
        self.assertEqual(uint32_word((1<<32)-1), (1<<32)-1)
        for value in [-1, 1<<32, True, 1.5]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                uint32_word(value)
