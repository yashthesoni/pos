"""
Main system for pointer creation and decoding.

DEALS EXCLUSIVELY IN BYTES.
"""

# CLEAN LATER, bad code, long additions.

import os

from milla.constants import PTR_BYTES


def encode_address(target_chunk: int | None, total_chunks: int, k: int | None = None) -> bytes:
    """
    Encode a target chunk index into a 4-byte address.
    Bit 31 (MSB): 1 if chained (valid target), 0 if terminal (no target)
    Bits 0-30: encoded address with random modulo jitter

    If target_chunk is 0 or None (meaning no location / terminal), the 31-bit address portion
    becomes purely random jitter and MSB is 0.
    """
    if total_chunks <= 0:
        raise ValueError("total_chunks cannot be negative")

    is_chained = bool(target_chunk)

    if not is_chained:
        raw_addr = int.from_bytes(os.urandom(4), 'big') & ((1 << 31) - 1)   # dirty shit
    else:
        if target_chunk < 1 or target_chunk > total_chunks:
            raise ValueError(f"target_chunk {target_chunk} is out of bounds (1 to {total_chunks})")

        max_val = (1 << 31) - 1
        max_k = (max_val - target_chunk) // total_chunks

        if k is None:
            if max_k < 0:
                raise ValueError("total_chunks is too large for 31-bit address space")
            k = int.from_bytes(os.urandom(4), 'big') % (max_k + 1)
        elif k < 0 or k > max_k:
            raise ValueError("k is out of valid range")

        raw_addr = target_chunk + k * total_chunks

    if is_chained:
        raw_addr |= (1 << 31)

    return raw_addr.to_bytes(PTR_BYTES, 'big')


def decode_address(raw_bytes: bytes, total_chunks: int) -> int:
    """
    Recover the target chunk index and chain flag from a 4-byte address.
    Returns target_chunk, if pointer is chained.
    If not chained, target_chunk is returned as 0 (no location) and the address is considered pure garbage.
    """
    if total_chunks <= 0:
        raise ValueError("total_chunks cannot be negative")

    if len(raw_bytes) != PTR_BYTES:
        raise ValueError(f"raw_bytes must be {PTR_BYTES} bytes long, got {len(raw_bytes)}")

    val = int.from_bytes(raw_bytes, 'big')
    is_chained = bool(val & (1 << 31))

    if not is_chained:
        return 0

    raw_addr = val & ((1 << 31) - 1)
    res = raw_addr % total_chunks
    target_chunk = total_chunks if res == 0 else res

    return target_chunk
