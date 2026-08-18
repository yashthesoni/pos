# Milla Pointer Math

The Pointer module (`milla/pointer.py`) governs address generation, chain validation, and modulo jitter translation for linked chunks in the file system.

The system exclusively operates on standard Python `bytes` objects when encoding or reading pointer definitions.

---

## 1. Address Architecture

Every pointer is exactly 4 bytes (32 bits) in size. 

* **Bit 31 (MSB)**: The Chain Flag. 
  * `1`: The pointer is valid and actively chains to another chunk.
  * `0`: The pointer is terminal (end of file/sequence) and the remaining 31 bits are purely random garbage.
* **Bits 0–30**: The Modulo Jitter space. If the chunk is chained, this space holds a deterministically obfuscated representation of the target address.

---

## 2. Pointer Operations

### `encode_address(target_chunk: int | None, total_chunks: int, k: int | None = None) -> bytes`
Converts a literal 1-based index into a secure 4-byte string.

1. **Terminal Generation**: If `target_chunk` is `0` or `None`, the pointer is marked unchained. The MSB is left as `0`, and the lower 31 bits are filled with cryptographically secure random bits (`os.urandom(4)` masked to 31 bits).
2. **Modulo Jitter Routing**: 
   * If a `target_chunk` is given, it verifies the target falls inside the valid `total_chunks` boundary.
   * Calculates a random integer $k$ within the maximum allowable 31-bit address space.
   * Computes the obfuscated address: $\text{raw\_addr} = \text{target\_chunk} + (k \times \text{total\_chunks})$.
   * Explicitly sets the MSB to `1` using a bitwise OR (`raw_addr | (1 << 31)`).
3. **Serialization**: Exports the resulting 32-bit integer as a 4-byte big-endian string.

### `decode_address(raw_bytes: bytes, total_chunks: int) -> int`
Retrieves the exact 1-based target chunk from a 4-byte pointer string.

1. **Validation**: Reads the 4 bytes into a 32-bit integer.
2. **Chain Verification**: Evaluates the MSB. If it is `0`, the pointer is terminal. The function instantly abandons math and returns `0` (not a tuple).
3. **De-Jittering**:
   * Strips the MSB away.
   * Computes the remainder: $\text{res} = \text{raw\_addr} \bmod \text{total\_chunks}$.
   * Since the environment uses 1-based indexing natively, if $\text{res} == 0$, it maps cleanly to the absolute final chunk (`total_chunks`).
4. **Return**: Yields the decoded integer representing the next chunk in the chain.
