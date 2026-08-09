# Milla Pointer Math

The Pointer module (`milla/pointer.py`) governs address generation and translation within the volatile file system.

## Core Operations
- **Address Encoding (`encode_address`)**: Given a 1-based target chunk, generates a 32-bit list of bits. The MSB (index 0) is implicitly set to `1` (chained/valid). The remaining 31 bits encode the modulo jitter representation of the target chunk.
- **Garbage Pointers**: If `encode_address(0, total)` or `None` is provided, the MSB is set to `0` (indicating a terminal sequence or no location), and the remaining 31 bits are populated with pure random garbage to thwart cryptanalysis.
- **Address Decoding (`decode_address`)**: Unpacks a 32-bit list of bits. The MSB is rigorously checked *first*. If `0`, it instantly halts calculation and returns `(0, False)`. Otherwise, it recovers the target chunk via modulo math natively supporting the 1-based index (where a remainder of `0` cleanly maps to `total_chunks`).
- **Strict Validation**: Heavily checks bounds (`total_chunks > 0`, exactly 32 bits input containing only `0` and `1`).
