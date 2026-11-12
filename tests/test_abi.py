# SPDX-License-Identifier: Apache-2.0
"""Optional owned-buffer boundary checks for a separately supplied binary."""
import ctypes as C
import os
import unittest
from harness.loader import Library
from harness.loader import ONE


@unittest.skipUnless(os.environ.get('DM_MHM_ENGINE_LIBRARY'), 'authorized engine not supplied')
class AbiBoundaries(unittest.TestCase):
    def setUp(self):
        self.library = Library(os.environ['DM_MHM_ENGINE_LIBRARY'])
        self.context = self.library.context()
        self.lib = self.library.lib

    def tearDown(self):
        self.context.close()

    def test_null_boundaries(self):
        self.assertEqual(self.lib.dm_mhm_create(None), 1)
        self.lib.dm_mhm_destroy(None)
        self.assertEqual(self.lib.dm_mhm_load_peaks(None, None, 1), 1)
        self.assertEqual(self.lib.dm_mhm_load_peaks(self.context.ptr, None, 1), 1)
        self.assertEqual(self.lib.dm_mhm_match_batch(None, None, 0, 32, ONE, None, None), 1)
        self.assertEqual(self.lib.dm_mhm_match_batch(self.context.ptr, None, 0, 32, ONE, None, None), 0)
        self.assertEqual(self.context.load([ONE]), 0)
        query, output = C.c_int64(ONE), C.c_int64(-123)
        flag = C.c_uint8(173)
        self.assertEqual(self.lib.dm_mhm_match_batch(self.context.ptr, None, 1, 1, ONE,
                                                   C.byref(output), C.byref(flag)), 1)
        self.assertEqual((output.value, flag.value), (-123, 173))
        self.assertEqual(self.lib.dm_mhm_match_batch(self.context.ptr, C.byref(query), 1, 1, ONE,
                                                   None, C.byref(flag)), 1)
        self.assertEqual(flag.value, 173)

    def test_count_arithmetic_rejected_before_buffer_access(self):
        self.assertEqual(self.context.load([ONE]), 0)
        self.assertEqual(self.context.match([2 * ONE], 1, ONE), (0, [0], [0]))
        query, output = C.c_int64(ONE), C.c_int64(-123)
        flag = C.c_uint8(173)
        maximum = C.c_size_t(-1).value
        # Deliberate arithmetic-overflow calls use valid dummy addresses. No
        # representable batch is submitted with insufficient buffer storage.
        for count, h in [(maximum, 32), (maximum // 32 + 1, 32),
                         (maximum // (32 * 8) + 1, 32), (maximum // 8 + 1, 1)]:
            with self.subTest(count=count, harmonics=h):
                self.assertEqual(self.lib.dm_mhm_match_batch(self.context.ptr, C.byref(query), count,
                                                           h, ONE, C.byref(output), C.byref(flag)), 2)
                self.assertEqual((output.value, flag.value), (-123, 173))
        self.assertEqual(self.context.match([ONE], 1, ONE), (0, [ONE], [1]))

    def test_rejected_prefix_preserves_history_and_output(self):
        self.assertEqual(self.context.load([100 * ONE, 150 * ONE, 200 * ONE]), 0)
        self.assertEqual(self.context.match([200 * ONE], 1, 1), (0, [200 * ONE], [0]))
        self.assertEqual(self.context.match([100 * ONE, -1], 1, 1), (1, [-123, -123], [173, 173]))
        self.assertEqual(self.context.match([150 * ONE], 1, 1), (0, [150 * ONE], [1]))
