# Milla Chunk Handler (Driver)

The Milla Driver (`milla/driver.py`) is the storage bridge between the high-level Milla operating system and the low-level `pos` bit-addressable memory map.

## Core Responsibilities
- **1-Based Chunk Indexing**: Abstraction ensuring all operations index chunks from `1` to `total_chunks`.
- **Pure Bit Arrays**: Translates chunk reads and writes exclusively via lists of bits (`list[int]`), fully eliminating python `bytes` intermediate representation for true bare-metal fidelity.
- **Strict Validation**: Aggressively bounds-checks indices and validates that data buffers are exactly 4096 elements long, containing exclusively `0` and `1`.
- **Secure Deletion**: Instantly overwrites individual chunks with cryptographically secure pseudo-random noise (CSPRNG), establishing the chaff layer dynamically via `format_chunk`.
