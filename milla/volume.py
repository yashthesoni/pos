import hashlib
import os
import shutil

from milla.startup import derive_outer_key
from posetem.pos import POS


def _derive_outer_keystream(master_key: bytes, required_bits: int) -> bytearray:
    """
    Derives the outer layer keystream using BLAKE2b in counter mode.
    Returns a bytearray containing enough random bytes to cover required_bits.
    """
    required_bytes = (required_bits + 7) // 8
    keystream = bytearray()
    counter = 0
    while len(keystream) < required_bytes:
        # fuck off
        h = hashlib.blake2b(master_key + counter.to_bytes(8, "big")).digest()
        keystream.extend(h)
        counter += 1

    return keystream


def decrypt_volume(input_pos_path: str, output_pos_path: str, passphrase: str) -> None:
    """Decrypts the outer layer of the Milla volume."""
    _process_volume(input_pos_path, output_pos_path, passphrase)


def encrypt_volume(input_pos_path: str, output_pos_path: str, passphrase: str) -> None:
    """Encrypts the outer layer of the Milla volume."""
    _process_volume(input_pos_path, output_pos_path, passphrase)


def _process_volume(input_pos_path: str, output_pos_path: str, passphrase: str) -> None:
    if not os.path.exists(input_pos_path):
        raise FileNotFoundError(f"POS file not found: {input_pos_path}")

    # copy the file
    shutil.copy2(input_pos_path, output_pos_path)

    with POS(output_pos_path) as pos_instance:
        user_bits = pos_instance.user_memory_size
        total_chunks = user_bits // 4096

        if total_chunks <= 0:
            raise ValueError(
                "Invalid POS file: size is too small to contain any user chunks."
            )

        # get the keystream
        master_key = derive_outer_key(passphrase, total_chunks)
        keystream_bytes = _derive_outer_keystream(master_key, user_bits)

        # read the bit array through the POS
        encrypted_bits = pos_instance.read(0, user_bits, smart=True)
        decrypted_bits = []

        # xor bit by bit
        for i in range(user_bits):
            byte_idx = i // 8
            bit_idx = 7 - (i % 8)
            key_bit = (keystream_bytes[byte_idx] >> bit_idx) & 1

            decrypted_bits.append(encrypted_bits[i] ^ key_bit)

        # write the mutated bits back safely through POS
        pos_instance.write(decrypted_bits, 0, smart=True)
