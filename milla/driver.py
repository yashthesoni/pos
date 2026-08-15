import os
import sys
try:
    from milla.constants import CHUNK_SIZE_BITS
except ImportError:
    from constants import CHUNK_SIZE_BITS

class MillaDriver:
    """
    Wraps the posetem.pos.POS instance to provide chunk-aligned read/write capabilities.
    Each chunk is exactly 4096 bits.
    Deals exclusively in raw bit arrays (list[int] of 0s and 1s).
    """

    CHUNK_SIZE_BITS = CHUNK_SIZE_BITS

    def __init__(self, pos_instance):
        self.pos = pos_instance
        self.total_chunks = self.pos.user_memory_size // self.CHUNK_SIZE_BITS

    def _get_bit_offset(self, chunk_idx: int) -> int:
        if chunk_idx < 1 or chunk_idx > self.total_chunks:
            raise IndexError(f"Chunk index {chunk_idx} is out of bounds")
        return (chunk_idx - 1) * self.CHUNK_SIZE_BITS

    def read_chunk(self, chunk_idx: int) -> list[int]:
        """Read a single 4096-bit chunk as a list of bits."""
        start_bit = self._get_bit_offset(chunk_idx)
        return self.pos._read(start_bit, self.CHUNK_SIZE_BITS, smart=True)

    def write_chunk(self, chunk_idx: int, data_bits: list[int]) -> None:
        """Write exactly 4096 bits into a single chunk."""
        if len(data_bits) != self.CHUNK_SIZE_BITS:
            raise ValueError(f"Data must be of {self.CHUNK_SIZE_BITS} bits, got {len(data_bits)}")

        for b in data_bits:
            if b not in (0, 1):
                raise ValueError("data_bits must contain exclusively 0s and 1s")

        start_bit = self._get_bit_offset(chunk_idx)
        self.pos._write(data_bits, start_bit, smart=True)

    def format_chunk(self, chunk_idx: int) -> None:
        """Overwrites a specific chunk with CSPRNG chaff (bits)."""
        rand_bytes = os.urandom(self.CHUNK_SIZE_BITS // 8)
        chaff = []
        for b in rand_bytes:
            for j in range(8):
                chaff.append(1 if (b & (1 << (7 - j))) else 0)
        self.write_chunk(chunk_idx, chaff)
