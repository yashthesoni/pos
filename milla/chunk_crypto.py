'''INDEPENDENT FILE.
THIS FILE IS NOT LINKED TO POS.
Main system for single chunk decryption, encryption, and Phantom Node verification.'''

import hashlib
import os

from milla.constants import (
    CHUNK_SIZE_BYTES,
    PAYLOAD_BYTES,
    PTR_BYTES,
    X_BYTES,
    Y_BYTES,
    Z_BYTES,
)


def _derive_m(enc_z: bytes, x: int) -> int:
    if x < 1 or x > 65535:
        raise ValueError("Iteration count x must be between 1 and 65535")

    h = hashlib.blake2b(enc_z).digest()

    for _ in range(x):
        h = hashlib.blake2b(h).digest()

    m = int.from_bytes(h[:6], 'big')
    return m

def _derive_keystream(e_val: int, length: int = Z_BYTES) -> bytes:
    e_bytes = e_val.to_bytes(6, 'big')
    keystream = bytearray()
    counter = 0
    while len(keystream) < length:
        h = hashlib.blake2b(e_bytes + counter.to_bytes(4, 'big')).digest()
        keystream.extend(h)
        counter += 1

    return bytes(keystream[:length])

def _xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))

def verify_phantom(data: bytes) -> bool:
    """
    Verifies if a decrypted payload (500 bytes) or encrypted chunk (512 bytes) is a Phantom Node.
    A chunk is a Phantom Node if the Hamming Weight (sum of set bits) of its 500-byte payload exactly equals 2000.
    """
    if len(data) == CHUNK_SIZE_BYTES:
        payload, _ = decrypt_chunk(data)
    elif len(data) == PAYLOAD_BYTES:
        payload = data
    else:
        raise ValueError(
            f"Expected {PAYLOAD_BYTES} bytes (payload) or {CHUNK_SIZE_BYTES} bytes (chunk), got {len(data)}"
        )
    return sum(b.bit_count() for b in payload) == 2000


def is_phantom(data: bytes) -> bool:
    """Check if a payload or chunk is a Phantom Node."""
    return verify_phantom(data)

def make_chunk(
    payload: bytes,
    ptr: bytes,
    x: int | None = None,
    e_val: int | None = None,
    allow_phantom: bool = False,
) -> bytes:
    """
    1. payload is 4000 bit data (NOT 3999)
    2. ptr is the pointer
    3. x is the hash count
    4. e_val key value (symbol: E)

    If you do not give x or e_val, the system will securely generate them.
    If allow_phantom is False, verifies that the payload does not accidentally
    have a Hamming weight of 2000 bits (Phantom Node condition).
    """
    if len(payload) != PAYLOAD_BYTES:
        raise ValueError(f"payload must be {PAYLOAD_BYTES} bytes, got {len(payload)}")
    if len(ptr) != PTR_BYTES:
        raise ValueError(f"ptr must be {PTR_BYTES} bytes, got {len(ptr)}")

    if not allow_phantom and verify_phantom(payload):
        raise ValueError(
            "Accidental Phantom Node detected: payload has Hamming weight of exactly 2000 bits. "
            "Use allow_phantom=True to create an intentional phantom chunk."
        )

    z = payload + ptr

    # pick E
    if e_val is None:
        e_val = int.from_bytes(os.urandom(6), 'big')
        if e_val == 0:
            e_val = 1
    elif e_val <= 0 or e_val >= (1 << 48):
        raise ValueError("E must be a positive 48-bit integer")

    # Enc_E(z)
    keystream = _derive_keystream(e_val, Z_BYTES)
    enc_z = _xor_bytes(z, keystream)

    # pick x
    if x is None:
        x = int.from_bytes(os.urandom(2), 'big') or 1

    m = _derive_m(enc_z, x)

    y = e_val ^ m    # compute y

    # return chunk
    return x.to_bytes(X_BYTES, 'big') + y.to_bytes(Y_BYTES, 'big') + enc_z

def decrypt_chunk(chunk: bytes) -> tuple[bytes, bytes]:
    """
    Use this function on encrypted chunks.
    This function will return (payload, ptr).
    To verify whether the decrypted chunk is a phantom node, use verify_phantom().
    """
    if len(chunk) != CHUNK_SIZE_BYTES:
        raise ValueError(f"chunk must be {CHUNK_SIZE_BYTES} bytes, got {len(chunk)}")

    x = int.from_bytes(chunk[:X_BYTES], 'big')
    y = int.from_bytes(chunk[X_BYTES:X_BYTES+Y_BYTES], 'big')
    enc_z = chunk[X_BYTES+Y_BYTES:]

    m = _derive_m(enc_z, x)

    e_val = m ^ y     # reconstruct E

    # Derive keystream from E and decrypt enc_z
    keystream = _derive_keystream(e_val, Z_BYTES)
    z = _xor_bytes(enc_z, keystream)

    payload = z[:PAYLOAD_BYTES]
    ptr = z[PAYLOAD_BYTES:]

    return payload, ptr

def make_phantom(ptr: bytes | None = None) -> bytes:
    """
    Creates a Phantom Node chunk by generating a random payload with exactly 2000 set bits.
    """
    import secrets
    
    if ptr is None:
        ptr = os.urandom(PTR_BYTES)
        
    bits = [0] * (PAYLOAD_BYTES * 8)
    for idx in secrets.SystemRandom().sample(range(PAYLOAD_BYTES * 8), 2000):
        bits[idx] = 1
        
    payload_bytearray = bytearray(PAYLOAD_BYTES)
    for i in range(PAYLOAD_BYTES):
        val = 0
        for j in range(8):
            if bits[i * 8 + j]:
                val |= (1 << (7 - j))
        payload_bytearray[i] = val
        
    return make_chunk(bytes(payload_bytearray), ptr, allow_phantom=True)
