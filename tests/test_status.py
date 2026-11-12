# SPDX-License-Identifier: Apache-2.0
import unittest
from harness.loader import Context, NativeStatusError


class InitializationStatus(unittest.TestCase):
    def test_numeric_initialization_failure_is_retained(self):
        class Refused:
            @staticmethod
            def dm_mhm_create(_):
                return 6
        with self.assertRaises(NativeStatusError) as caught:
            Context(Refused())
        self.assertEqual(caught.exception.status, 6)

    def test_success_with_null_context_is_a_contract_error(self):
        class InvalidSuccess:
            @staticmethod
            def dm_mhm_create(_):
                return 0
        with self.assertRaisesRegex(ValueError, 'CREATE_RETURNED_NULL'):
            Context(InvalidSuccess())


if __name__ == '__main__':
    unittest.main()
