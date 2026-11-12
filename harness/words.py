# SPDX-License-Identifier: Apache-2.0
"""Validate Python values before crossing the fixed-width public ABI."""
import operator


def integer_word(value, minimum, maximum):
    if isinstance(value, bool):
        raise ValueError('ABI_WORD_REQUIRES_INTEGER')
    try:
        word = operator.index(value)
    except TypeError:
        raise ValueError('ABI_WORD_REQUIRES_INTEGER') from None
    if not minimum <= word <= maximum:
        raise ValueError('ABI_WORD_OUT_OF_RANGE')
    return word


def int64_word(value):
    return integer_word(value, -(1 << 63), (1 << 63) - 1)


def uint32_word(value):
    return integer_word(value, 0, (1 << 32) - 1)
