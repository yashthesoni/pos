# pos — Bare-Bones OS Simulator

A minimal, educational operating system simulator designed to help people learn how to build their own systems from the ground up without actually interacting with hardware.

## Philosophy

pos is built as a bare-bones, low-level educational asset rather than a production product. It provides:
1. **Memory Interaction**: A simple, bit-addressable array of memory (stored as `0`s and `1`s).
2. **Memory-Mapped Display**: A display system driven directly by scanning a dedicated region of the memory array.
3. **No Hardware Needed**: A simulated environment runs on top of standard Python memory mapping (`mmap`).

A live pixel display window is rendered natively from this memory using Tkinter with no external package dependencies.

## How It Works

**Server** runs in one terminal. It owns the `.pos` file and renders the display.
**Client** scripts run in another terminal. This connects to the same `.pos` file via mmap. Changes appear on the display instantly.

The OS page cache is the shared memory bus.

## Quick Start

### 1. Start the server

This will start the server. If no arguement is provided, a prompt will ask for location too. If the `.pos` file exists, it will smartly open it.

```bash
python3 posetem/pos.py system.pos
```

### 2. Connect from a script

```python
from posetem import POS

pos = POS("system.pos")  # connect

# Write to the display
pos.dwrite([1, 1, 1, 0, 0, 1, 1, 1], start=0)

# Write to user memory
pos.write([1, 0, 1, 0], start=0)

# Read it back
bits = pos.read(0, 4)  # [1, 0, 1, 0]

pos.close() # not strictly necessary
```

The display window (running from the server terminal) updates live.

## Memory Layout

The `.pos` file is a flat byte array. Each byte is `0x00` or `0x01` (one bit):

| Address (bits) | Size | Purpose |
|---|---|---|
| `0 – 1023` | 1024 | Reserved empty |
| `1024 – 1055` | 32 | Reserved display settings (empty) |
| `1056 – 1071` | 16 | Display width |
| `1072 – 1087` | 16 | Display height |
| `1088 – 1088+W×H-1` | W × H | Display pixels (1 = white, 0 = black) |
| `1088+W×H – end` | remainder | User memory |

**Smart addressing** (on by default) makes `start=0` point to the first *user* bit — after the display region. You never need to calculate header offsets by yourself.

## API Reference

### Creating / Connecting

```python
# Connect to existing .pos file
pos = POS("system.pos")

# Create a new .pos file
pos = POS.create("new.pos", total_bits=20000, display_width=100, display_height=100)
```

### `pos.read(start, length, *, smart=True) → list[int]`

Read `length` bits from `start`. With `smart=True`, `start` is relative to the first user bit.

### `pos.write(data, start, *, smart=True)`

Write `data` (can be a list of `0`/`1` values or a bit-string like `"1010"`) starting at `start`. Smart addressing same as `read`.

Using `2` will ignore the bit (e.g. `121` will write only `1` and `1` but will leave the bit at the place of `2` unchanged)

### `pos.dwrite(data, start=0, *, smart=True)`

Write `data` (can be a list of `0`/`1` values or a bit-string like `"1010"`) to the **display** region. `start=0` = first pixel. Overflow is silently clipped.

Using `2` will ignore the bit (e.g. `121` will write only `1` and `1` but will leave the bit at the place of `2` unchanged)

### `pos.dread(start=0, length=None, *, smart=True) → list[int]`

Read from the display region. `length=None` reads to end.

### `pos.close()`

Flush and close the mmap. Use `with POS("f.pos") as pos:` for auto-close.

### Properties

| Property | Description |
|---|---|
| `pos.display_width` | Display width in pixels |
| `pos.display_height` | Display height in pixels |
| `pos.user_memory_size` | Bits available for user data |
| `pos.total_bits` | Total memory size |

## Display Window Controls

The Tkinter server display includes:
- **Grey backdrop** around the display screen boundary to distinguish it from black pixels.
- **Native Menu Bar** for zooming in and out

## Example

```bash
# Terminal 1 — start server (create 2000-bit pos with 40×20 display)
python3 posetem/pos.py system.pos

# Terminal 2 — run the demo client
python3 examples/demo.py
```

## Running Tests

```bash
python3 posetem/test_pos.py
```

## Requirements

- **Python 3.10+**
- **tkinter** — for the server display only (`brew install python-tk` on macOS if missing)
- No external packages
