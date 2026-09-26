# Milla Monolithic Volume Encryption

The Volume module (`milla/volume.py`) governs whole-volume outer encryption and decryption for Milla containers on top of the `pos` shared-memory bus.

---

## 1. Two-Tier Outer Architecture

Milla utilizes a two-tier cryptographic model:
1. **Outer Layer (Global Envelope)**: Encrypts the entire user-memory region monolithically using a stream cipher derived from the user's master passphrase. This ensures that unmounted `.pos` files are statistically indistinguishable from uniform CSPRNG noise.
2. **Inner Layer (Self-Decrypting Chunks)**: Encrypted chunks reside inside the envelope and manage their own block keys ($E = m \oplus y$).

Because encryption is symmetric stream XOR, the encryption and decryption pipelines execute the identical bit-flipping operation (`encrypt_volume` and `decrypt_volume` are interchangeable symmetric operations).

---

## 2. Keystream Generation

### `_derive_outer_keystream(master_key: bytes, required_bits: int) -> bytearray`
Generates a cryptographically secure pseudorandom keystream using BLAKE2b in counter mode:

1. Calculates required byte length: $\lceil \text{required\_bits} / 8 \rceil$.
2. Initializes an 8-byte big-endian counter starting at $0$.
3. In each iteration, computes:
   $$\text{block} = \text{BLAKE2b}(\text{master\_key} \mathbin{\Vert} \text{counter}_{64})$$
4. Appends each 64-byte digest to the keystream and increments the counter until sufficient bytes are generated to cover the entire user memory.

---

## 3. Volume Processing Operations

### `encrypt_volume(input_pos_path: str, output_pos_path: str, passphrase: str) -> None`
### `decrypt_volume(input_pos_path: str, output_pos_path: str, passphrase: str) -> None`
Executes monolithic envelope encryption or decryption:

1. **File Duplication**: Copies `input_pos_path` to `output_pos_path` via `shutil.copy2`.
2. **POS Bus Mount**: Opens `output_pos_path` using the `POS` interface.
3. **Geometry Calculation**: 
   * Reads `user_memory_size` (total bits past the 1088-bit system header and display memory).
   * Computes $\text{total\_chunks} = \lfloor \text{user\_bits} / 4096 \rfloor$.
4. **Keystream Derivation**: 
   * Derives 32-byte `master_key` from `passphrase` and `total_chunks` via `derive_outer_key`.
   * Expands `master_key` into `user_bits` of keystream using `_derive_outer_keystream`.
5. **Bitwise Stream XOR**:
   * Reads all user bits via `pos_instance.read(0, user_bits, smart=True)`.
   * XORs each user bit with the corresponding bit from the keystream byte array:
     $$\text{bit}'_i = \text{bit}_i \oplus \left( \frac{\text{keystream}[i // 8]}{2^{7 - (i \bmod 8)}} \ \& \ 1 \right)$$
6. **In-Place Writeback**: Writes the transformed bits back to user memory via `pos_instance.write(decrypted_bits, 0, smart=True)`.
