# SPDX-License-Identifier: Apache-2.0
"""Only public declarations from dm_mhm_abi.h are bound here."""
import ctypes as C
from pathlib import Path
from .words import int64_word, uint32_word
ONE = 1 << 32


class NativeStatusError(RuntimeError):
    def __init__(self, status):
        self.status = int(status)
        super().__init__('NATIVE_INITIALIZATION_FAILED')


class Library:
    def __init__(self, path):
        self.lib = C.CDLL(str(Path(path).resolve()))
        signatures = {
            'dm_mhm_abi_version': (C.c_uint32, []),
            'dm_mhm_create': (C.c_int32, [C.POINTER(C.c_void_p)]),
            'dm_mhm_load_peaks': (C.c_int32, [C.c_void_p, C.POINTER(C.c_int64), C.c_size_t]),
            'dm_mhm_match_batch': (C.c_int32, [C.c_void_p, C.POINTER(C.c_int64), C.c_size_t,
                                             C.c_uint32, C.c_int64, C.POINTER(C.c_int64), C.POINTER(C.c_uint8)]),
            'dm_mhm_destroy': (None, [C.c_void_p]),
        }
        for name, (result, args) in signatures.items():
            fn = getattr(self.lib, name)
            fn.restype, fn.argtypes = result, args
        if self.lib.dm_mhm_abi_version() != 1:
            raise ValueError('ABI_VERSION_MISMATCH')

    def context(self):
        return Context(self.lib)


class Context:
    def __init__(self, lib):
        self.lib = lib
        self.ptr = C.c_void_p()
        status = lib.dm_mhm_create(C.byref(self.ptr))
        if status != 0:
            raise NativeStatusError(status)
        if not self.ptr:
            raise ValueError('CREATE_RETURNED_NULL')

    def load(self, peaks):
        if not self.ptr:
            raise ValueError('CONTEXT_CLOSED')
        if len(peaks) > 4097:
            raise ValueError('RUNNER_INPUT_LIMIT')
        peaks = [int64_word(peak) for peak in peaks]
        return self.lib.dm_mhm_load_peaks(self.ptr, (C.c_int64 * len(peaks))(*peaks), len(peaks))

    def match(self, queries, h=32, tolerance=2 * ONE, flags=True):
        if not self.ptr:
            raise ValueError('CONTEXT_CLOSED')
        if len(queries) > 128:
            raise ValueError('RUNNER_INPUT_LIMIT')
        queries = [int64_word(query) for query in queries]
        h, tolerance = uint32_word(h), int64_word(tolerance)
        n = len(queries)
        output = (C.c_int64 * (n * max(1, min(h, 32))))(*([-123] * (n * max(1, min(h, 32)))))
        restarts = (C.c_uint8 * n)(*([173] * n)) if flags else None
        status = self.lib.dm_mhm_match_batch(self.ptr, (C.c_int64 * n)(*queries), n,
                                            h, tolerance, output, restarts)
        return status, list(output), list(restarts) if flags else None

    def close(self):
        if self.ptr:
            self.lib.dm_mhm_destroy(self.ptr)
            self.ptr = C.c_void_p()
