"""THIS FILE IS LINKED TO POS
NO VERIFICATION FOR ACCIDENTAL PHANTOM CHUNKS
Main system for chunk R&W capabilities.

DEALS EXCLUSIVELY IN BYTES."""

 # CLEAN LATER, after pos transitions to native byte reader
 
import os

from milla.constants import CHUNK_SIZE_BYTES
from posetem.pos import POS


class MillaDriver:
    """
    (NO VERIFICATION FOR ACCIDENTAL PHANTOM CHUNKS)

    Provides chunk-aligned read/write capabilities for provided POS instance.
    Each chunk is 4096 bits.
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
        """Read a single chunk."""
        start_bit = self._get_bit_offset(chunk_idx)
        bits = self.pos.read(start_bit, self.CHUNK_SIZE_BYTES * 8, smart=True)
        byte_arr = bytearray(self.CHUNK_SIZE_BYTES)
        for i in range(self.CHUNK_SIZE_BYTES):
            val = 0
            for j in range(8):
                if bits[i * 8 + j]:
                    val |= (1 << (7 - j))
            byte_arr[i] = val
        return bytes(byte_arr)

    def write_chunk(self, chunk_idx: int, data: bytes) -> None:
        """Write a single chunk. Provide exactly 512 bytes"""
        if len(data) != self.CHUNK_SIZE_BYTES:
            raise ValueError(f"Data must be of {self.CHUNK_SIZE_BYTES} bytes, got {len(data)}")

        bits: list[int] = []
        for b in data:
            for j in range(8):
                bits.append(1 if (b & (1 << (7 - j))) else 0)

        start_bit = self._get_bit_offset(chunk_idx)
        self.pos.write(bits, start_bit, smart=True)

    def format_chunk(self, chunk_idx: int) -> None:
        """USE WITH CAUTION. 
        Overwrites a specific chunk with random chaff."""
        chaff = os.urandom(self.CHUNK_SIZE_BYTES)
        self.write_chunk(chunk_idx, chaff)

    def check_phantom(self, chunk_idx: int) -> bool:
        """
        Check if the chunk at chunk_idx is a Phantom Node.
        A chunk is a Phantom Node if the Hamming Weight (sum of bits) of its decrypted payload (z) exactly equals 2016.
        """
        from milla.chunk_crypto import decrypt_chunk
        
        chunk = self.read_chunk(chunk_idx)
        payload = decrypt_chunk(chunk)[0]
        z = payload
        
        hamming_weight = sum(b.bit_count() for b in z)
        return hamming_weight == 2016

