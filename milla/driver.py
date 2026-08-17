import os

from milla.constants import CHUNK_SIZE_BYTES
from posetem.pos import POS


class MillaDriver:
    """
    Wraps the posetem.pos.POS instance to provide chunk-aligned read/write capabilities.
    Each chunk is exactly 512 bytes.
    Deals exclusively in bytes.
    """

    CHUNK_SIZE_BYTES: int = CHUNK_SIZE_BYTES

    def __init__(self, pos_instance: POS):
        self.pos: POS = pos_instance
        self.total_chunks: int = self.pos.user_memory_size // (self.CHUNK_SIZE_BYTES * 8)

    def _get_bit_offset(self, chunk_idx: int) -> int:
        if chunk_idx < 1 or chunk_idx > self.total_chunks:
            raise IndexError(f"Chunk index {chunk_idx} is out of bounds")
        return (chunk_idx - 1) * self.CHUNK_SIZE_BYTES * 8

    def read_chunk(self, chunk_idx: int) -> bytes:
        """Read a single 512-byte chunk."""
        start_bit = self._get_bit_offset(chunk_idx)
        bits = self.pos.read(start_bit, self.CHUNK_SIZE_BYTES * 8, smart=True)
        # Convert bits to bytes
        byte_arr = bytearray(self.CHUNK_SIZE_BYTES)
        for i in range(self.CHUNK_SIZE_BYTES):
            val = 0
            for j in range(8):
                if bits[i * 8 + j]:
                    val |= (1 << (7 - j))
            byte_arr[i] = val
        return bytes(byte_arr)

    def write_chunk(self, chunk_idx: int, data: bytes) -> None:
        """Write exactly 512 bytes into a single chunk."""
        if len(data) != self.CHUNK_SIZE_BYTES:
            raise ValueError(f"Data must be of {self.CHUNK_SIZE_BYTES} bytes, got {len(data)}")

        bits: list[int] = []
        for b in data:
            for j in range(8):
                bits.append(1 if (b & (1 << (7 - j))) else 0)

        start_bit = self._get_bit_offset(chunk_idx)
        self.pos.write(bits, start_bit, smart=True)

    def format_chunk(self, chunk_idx: int) -> None:
        """Overwrites a specific chunk with CSPRNG chaff."""
        chaff = os.urandom(self.CHUNK_SIZE_BYTES)
        self.write_chunk(chunk_idx, chaff)
