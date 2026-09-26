# Milla Startup & Runtime Environment

The Startup module (`milla/startup.py`) manages the volatile session lifecycle, outer master key derivation, dynamic root anchor discovery, and user visual passphrase fingerprints.

---

## 1. Volatile Environment Lifecycle

Milla operates under a strict volatile-first model: persistent containers are never manipulated in-place in their encrypted form while mounted. 

The `MillaEnvironment` class provides a context manager to isolate runtime operations:

* **Session Directory**: Generates a temporary directory named `.temp-<filename>-<session_id>` (using an 8-character hex token from `secrets.token_hex(4)`) alongside the target `.pos` file.
* **Working Copy**: Creates `decrypted-<filename>` inside the session directory for active mounting and runtime memory mapping.
* **Runtime Config**: Writes a local `config.json` containing metadata (e.g. `source_file` path).
* **Cryptographic Sanitization (Secure Wipe)**: Upon unmount (or context exit):
  1. Overwrites the entire working file with zero bytes (`b'\x00' * file_size`).
  2. Flushes the buffer and executes `os.fsync()` to ensure dirty blocks are overwritten on physical media.
  3. Deletes `decrypted-<filename>` and `config.json`.
  4. Removes the session directory (`shutil.rmtree`).

---

## 2. Key Derivation & Anchor Resolution

### `derive_outer_key(passphrase: str, total_chunks: int) -> bytes`
Derives the 32-byte master outer key using `scrypt`:
* **Salt**: Dynamic salt composed of `b"Milla Jovovich"` concatenated with `total_chunks` encoded as an 8-byte big-endian integer.
* **Parameters**: $N = 16384$, $r = 8$, $p = 1$, output length = 32 bytes (`dklen=32`).
* **Purpose**: Feeds both the outer envelope keystream and the root chunk pointer math.

### `get_root_chunk_and_fingerprint(passphrase: str, total_chunks: int, word_count: int = 4) -> tuple[int, str]`
Derives the 1-based root directory chunk index and an interactive visual confirmation fingerprint:

1. **Outer Key Derivation**: Computes the 32-byte master key via `derive_outer_key`.
2. **Dynamic Root Anchor**: 
   * Reads the first 16 bytes as an unsigned integer `lcn`.
   * Computes the 1-based chunk location:
     $$\text{res} = \text{lcn} \pmod{\text{total\_chunks}}$$
     $$\text{root\_chunk} = \begin{cases} \text{total\_chunks} & \text{if } \text{res} == 0 \\ \text{res} & \text{otherwise} \end{cases}$$
3. **Phonetic Visual Fingerprint**:
   * Reads the remaining 16 bytes as an unsigned integer `fingerprint_val`.
   * Maps modulo indices across a 26-word NATO phonetic alphabet dictionary (`alfa`, `bravo`, ..., `zulu`).
   * Produces a space-separated visual confirmation phrase (e.g. `"bravo tango echo lima"`).
   * Allows the user to visually confirm correct passphrase input without storing any on-disk verification hash.
