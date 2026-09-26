# Milla Custom Chunk Cryptography Module

This document outlines the cryptographic logic and chunk structure used within the Milla storage environment, as implemented in `milla/chunk_crypto.py`. 

*(Note: Accidental phantom chunks are verified at the cryptography layer via `verify_phantom()`).*

---

## 1. Physical Layout (512 Bytes / 4096 Bits)

Every chunk in Milla is exactly 512 bytes, strictly segmented into three components:

| Address Range (Bytes) | Size (Bytes) | Variable | Description |
| :--- | :--- | :--- | :--- |
| `0 – 1` | 2 | $x$ | Random iteration count for Stochastic Proof-of-Work ($1 \le x \le 65535$). |
| `2 – 7` | 6 | $y$ | Secret offset compensation modifier ($y = E \oplus m$). |
| `8 – 511` | 504 | $z_{enc}$ | The encrypted payload and pointer structure. |

### The $z$ Block Geometry
The internal structure of the 504-byte unencrypted $z$ block is mapped as follows:
* **Payload**: 500 bytes (4000 bits) of raw user data.
* **Pointer**: 4 bytes (32 bits) containing the physical address of the next chained chunk (handled by `milla/pointer.py`).

---

## 2. Encryption Algorithm

When a payload and pointer are to be written to a chunk, Milla secures them using the following process:

1. **Phantom Verification**: If `allow_phantom=False` (default), verifies that the payload does not accidentally have a Hamming weight of 2000 set bits (`verify_phantom(payload)`).
2. **Secret Key Generation**: Generate a random 48-bit secret integer $E$. (If $E = 0$, it is bumped to $1$).
3. **Data Concatenation**: Concatenate the payload (500 bytes) and the pointer (4 bytes) to form $z$ (504 bytes).
4. **Keystream Derivation**: 
   * A PRF keystream of 504 bytes is derived from $E$ using BLAKE2b.
5. **Encryption**: 
   * XOR the plaintext $z$ with the keystream to produce $z_{enc}$.
6. **Stochastic Proof-of-Work Calculation**:
   * A random 16-bit integer $x$ is chosen.
   * $m$ is derived by recursively hashing $z_{enc}$ exactly $x$ times via BLAKE2b, taking the first 48 bits of the final digest.
7. **Key Disguise**: 
   * Compute $y = E \oplus m$. This effectively locks $E$ behind the work value $m$.
8. **Finalization**: 
   * Assemble the final chunk in the order: $x \mathbin{\Vert} y \mathbin{\Vert} z_{enc}$.

---

## 3. Decryption Algorithm

To extract data from an encrypted chunk on disk:

1. **Extraction**: Split the 512-byte chunk into $x$ (2 bytes), $y$ (6 bytes), and $z_{enc}$ (504 bytes).
2. **Work Reconstruction**: 
   * Recursively hash $z_{enc}$ exactly $x$ times to recover $m$ (48 bits).
3. **Key Reconstruction**: 
   * Recover the original secret key $E = m \oplus y$.
4. **Decryption**: 
   * Rebuild the keystream from $E$ and XOR it against $z_{enc}$ to recover the plaintext $z$.
5. **Data Unpacking**: 
   * Split $z$ into the 500-byte payload and the 4-byte pointer.

---

## 4. Phantom Node Verification

* **`verify_phantom(data: bytes) -> bool`**: Verifies whether a 500-byte decrypted payload or a 512-byte encrypted chunk is a Phantom Node by evaluating if the Hamming weight (number of set bits) of the payload exactly equals 2000 ($\sum \text{bit\_count} = 2000$).
* **`is_phantom(data: bytes) -> bool`**: Alias for `verify_phantom(data)`.
* **`make_phantom(ptr: bytes | None = None) -> bytes`**: Generates a valid Phantom Node chunk with exactly 2000 set bits and an encrypted next pointer.

