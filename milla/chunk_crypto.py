import hashlib
import os
import random

try:
    from milla.constants import (
        CHUNK_SIZE_BITS,
        X_BITS,
        Y_BITS,
        Z_BITS,
        PAYLOAD_BITS,
        TWEAK_BITS,
        PTR_BITS,
    )
except ImportError:
    from constants import (
        CHUNK_SIZE_BITS,
        X_BITS,
        Y_BITS,
        Z_BITS,
        PAYLOAD_BITS,
        TWEAK_BITS,
        PTR_BITS,
    )
MOD_48 = 1 << 48

def bits_to_bytes(bits: list[int]) -> bytes:
    """Convert a bit list (length multiple of 8) to bytes."""
    byte_arr = bytearray(len(bits) // 8)
    for i in range(len(byte_arr)):
        val = 0
        for j in range(8):
            if bits[i * 8 + j]:
                val |= (1 << (7 - j))
        byte_arr[i] = val
    return bytes(byte_arr)

def bytes_to_bits(b_data: bytes) -> list[int]:
    """Convert bytes to a bit list."""
    bits = []
    for b in b_data:
        for j in range(8):
            bits.append(1 if (b & (1 << (7 - j))) else 0)
    return bits

def derive_m(enc_z_bits: list[int], x: int) -> int:
    """
    Hash enc_z, then iterate x-1 times to establish Stochastic Proof-of-Work.
    Returns the first 48 bits as integer m.
    """
    if x < 1 or x > 65535:
        raise ValueError("Iteration count x must be between 1 and 65535")
        
    enc_z_bytes = bits_to_bytes(enc_z_bits)
    
    # First hash over the full encrypted payload
    h = hashlib.blake2b(enc_z_bytes).digest()
    
    # Stochastic PoW iterations
    for _ in range(x - 1):
        h = hashlib.blake2b(h).digest()
        
    # Take first 6 bytes (48 bits) and convert to 48-bit unsigned integer m
    h_48 = h[:6]
    m = int.from_bytes(h_48, 'big')
    return m

def derive_keystream(e_val: int, length: int = Z_BITS) -> list[int]:
    """
    Expand a 48-bit key integer E into a pseudo-random keystream of specified bit length.
    """
    e_bytes = e_val.to_bytes(6, 'big')
    keystream_bits = []
    counter = 0
    while len(keystream_bits) < length:
        h = hashlib.blake2b(e_bytes + counter.to_bytes(4, 'big')).digest()
        keystream_bits.extend(bytes_to_bits(h))
        counter += 1
        
    return keystream_bits[:length]

def encrypt_chunk(
    payload_bits: list[int],
    ptr_bits: list[int],
    x: int | None = None,
    e_val: int | None = None
) -> list[int]:
    """
    Encrypt payload (3999b) and pointer (32b) into a 4096-bit chunk using the Two-Tier architecture:
    1. Add 1-bit Anti-Phantom Tweak to ensure decrypted payload does not sum to 2016.
    2. E is a random 48-bit positive integer key.
    3. Encrypt z = (payload + tweak + ptr) with E to create enc_z.
    4. Pick uniformly random x (16b). Compute PoW m = derive_m(enc_z, x).
    5. Compute y = (E - m) mod 2^48.
    6. Assemble: x (16b) + y (48b) + enc_z (4032b) = 4096 bits.
    """
    if len(payload_bits) != PAYLOAD_BITS:
        raise ValueError(f"payload_bits must be exactly {PAYLOAD_BITS} bits, got {len(payload_bits)}")
    if len(ptr_bits) != PTR_BITS:
        raise ValueError(f"ptr_bits must be exactly {PTR_BITS} bits, got {len(ptr_bits)}")
        
    for b in payload_bits + ptr_bits:
        if b not in (0, 1):
            raise ValueError("Input bit arrays must contain exclusively 0s and 1s")

    # Anti-Phantom Tweak logic
    S = sum(payload_bits) + sum(ptr_bits)
    if S == 2016:
        tweak_bit = 1 # Total = 2017
    elif S == 2015:
        tweak_bit = 0 # Total = 2015
    else:
        tweak_bit = random.choice([0, 1])

    z_bits = payload_bits + [tweak_bit] + ptr_bits

    # Pick random 48-bit key E
    if e_val is None:
        e_bytes = os.urandom(6)
        e_val = int.from_bytes(e_bytes, 'big')
        if e_val == 0:
            e_val = 1
    elif e_val < 0 or e_val >= MOD_48:
        raise ValueError("E must be a positive 48-bit integer")

    # Encrypt z with E
    keystream = derive_keystream(e_val, Z_BITS)
    enc_z_bits = [z ^ k for z, k in zip(z_bits, keystream)]

    # Pick random x (16-bit integer: 1..65535) uniformly
    if x is None:
        x = random.randint(1, 65535)
    elif x < 1 or x > 65535:
        raise ValueError("x must be between 1 and 65535")

    # Hash enc_z with Stochastic PoW -> 48-bit integer m
    m = derive_m(enc_z_bits, x)

    # Compute y = (E - m) mod 2^48
    y = (e_val - m) % MOD_48

    # Convert x (16 bits) and y (48 bits) into bit arrays
    x_bits = [(x >> i) & 1 for i in range(15, -1, -1)]
    y_bits = [(y >> i) & 1 for i in range(47, -1, -1)]

    # Assemble 4096-bit chunk
    chunk_bits = x_bits + y_bits + enc_z_bits
    return chunk_bits

def decrypt_chunk(chunk_bits: list[int]) -> tuple[list[int], list[int]]:
    """
    Decrypt a 4096-bit chunk using the Two-Tier architecture:
    1. Unpack x (16b), y (48b), enc_z (4032b).
    2. Compute PoW hash m from enc_z iterating x times.
    3. Reconstruct E = (m + y) mod 2^48.
    4. Decrypt enc_z using E to recover payload (3999b), tweak (1b), and pointer (32b).
    """
    if len(chunk_bits) != CHUNK_SIZE_BITS:
        raise ValueError(f"chunk_bits must be exactly {CHUNK_SIZE_BITS} bits, got {len(chunk_bits)}")
    for b in chunk_bits:
        if b not in (0, 1):
            raise ValueError("chunk_bits must contain exclusively 0s and 1s")

    # Unpack x (16 bits)
    x = 0
    for b in chunk_bits[:16]:
        x = (x << 1) | b

    # Unpack y (48 bits)
    y = 0
    for b in chunk_bits[16:64]:
        y = (y << 1) | b

    # Unpack enc_z (4032 bits)
    enc_z_bits = chunk_bits[64:4096]

    # Compute PoW hash m
    m = derive_m(enc_z_bits, x)

    # Reconstruct E = (m + y) mod 2^48
    e_val = (m + y) % MOD_48

    # Derive keystream from E and decrypt enc_z
    keystream = derive_keystream(e_val, Z_BITS)
    z_bits = [ez ^ k for ez, k in zip(enc_z_bits, keystream)]

    payload_bits = z_bits[:PAYLOAD_BITS]
    tweak_bit = z_bits[PAYLOAD_BITS]
    ptr_bits = z_bits[PAYLOAD_BITS + 1:]

    return payload_bits, ptr_bits