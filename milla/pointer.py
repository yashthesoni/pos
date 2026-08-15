import random
try:
    from milla.constants import PTR_BITS
except ImportError:
    from constants import PTR_BITS

def encode_address(target_chunk: int | None, total_chunks: int, k: int | None = None) -> list[int]:
    """
    Encode a target chunk index into a 32-bit list of bits (0s and 1s).
    Bits[0] (MSB): 1 if chained (valid target), 0 if terminal (no target)
    Bits[1:32]: encoded address with random modulo jitter

    If target_chunk is 0 or None (meaning no location / terminal), the 31-bit address portion
    becomes purely random jitter and MSB is 0.
    """
    if total_chunks <= 0:
        raise ValueError("total_chunks must be strictly positive")

    is_chained = bool(target_chunk)

    if not is_chained:
        raw_addr = random.randint(0, (1 << 31) - 1)
    else:
        if target_chunk < 1 or target_chunk > total_chunks:
            raise ValueError(f"target_chunk {target_chunk} is out of bounds (1 to {total_chunks})")

        max_val = (1 << 31) - 1
        max_k = (max_val - target_chunk) // total_chunks

        if k is None:
            if max_k < 0:
                raise ValueError("total_chunks is too large for 31-bit address space")
            k = random.randint(0, max_k)
        elif k < 0 or k > max_k:
            raise ValueError("k is out of valid range")

        raw_addr = target_chunk + k * total_chunks

    bits = [1 if is_chained else 0]
    for i in range(30, -1, -1):
        bits.append(1 if (raw_addr & (1 << i)) else 0)

    return bits


def decode_address(raw_bits: list[int], total_chunks: int) -> tuple[int, bool]:
    """
    Recover the target chunk index and chain flag from a 32-bit list of bits.
    Returns (target_chunk, is_chained).
    If not chained, target_chunk is returned as 0 (no location) and the address is considered garbage.
    """
    if total_chunks <= 0:
        raise ValueError("total_chunks must be strictly positive")

    if len(raw_bits) != PTR_BITS:
        raise ValueError(f"raw_bits must be {PTR_BITS} bits long, got {len(raw_bits)}")

    for b in raw_bits:
        if b not in (0, 1):
            raise ValueError("raw_bits must contain only 0s and 1s")

    is_chained = bool(raw_bits[0])

    if not is_chained:
        return 0, False

    raw_addr = 0
    for b in raw_bits[1:]:
        raw_addr = (raw_addr << 1) | b

    res = raw_addr % total_chunks
    target_chunk = total_chunks if res == 0 else res

    return target_chunk, True
