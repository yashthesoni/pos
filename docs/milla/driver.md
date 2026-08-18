# Milla Chunk Handler (Driver)

The Milla Driver (`milla/driver.py`) is the storage bridge between the high-level Milla operating system and the low-level `pos` bit-addressable memory map (`posetem.pos.POS`).

---

## 1. Core Architecture and Indexing

* **1-Based Indexing**: All read, write, and format operations index chunks from `1` to `total_chunks`. The driver natively handles bounds checking, instantly raising an `IndexError` for requests outside this range.
* **Byte Interface**: The `MillaDriver` explicitly deals in standard Python `bytes`. While the underlying `.pos` architecture expects lists of individual bits (0s and 1s), the driver handles all encoding/decoding internally.
* **Chunk Geometry**: The driver enforces a strict 512-byte (4096-bit) boundary for all data interactions.

---

## 2. API Reference

### `read_chunk(chunk_idx: int) -> bytes`
1. Validates the `chunk_idx`.
2. Calculates the physical absolute start bit within the POS container.
3. Requests 4096 bits from the `POS` interface using `smart=True` (which safely offsets the address past the POS system headers and display memory).
4. Converts the bit list into a standard 512-byte `bytes` object and returns it.

### `write_chunk(chunk_idx: int, data: bytes) -> None`
1. Enforces that `data` is exactly 512 bytes long.
2. Converts the 512 bytes into a 4096-length list of bits (0s and 1s).
3. Calculates the correct physical offset for the targeted `chunk_idx`.
4. Dispatches the bit list to the `POS` interface via `smart=True` writing.

### `format_chunk(chunk_idx: int) -> None`
* **Purpose**: Securely deletes the contents of a chunk.
* **Mechanism**: Generates 512 bytes of cryptographically secure pseudo-random noise (`os.urandom(512)`) and uses `write_chunk` to overwrite the specified sector on disk. This establishes a permanent chaff layer when space is freed.
