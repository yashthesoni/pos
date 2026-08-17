"""
pos — bare-bones operating system simulator.

Run this file to start the pos server (display + memory).
Import POS in your scripts to connect to a running pos.

Architecture:
  Terminal 1:  python3 posetem/pos.py system.pos   (server + display)
  Terminal 2:  from posetem import POS              (client)
               pos = POS("system.pos")
               pos.dwrite([1, 0, 1])

Both sides mmap the same .pos file.
"""

import mmap
import os
import sys
from collections.abc import Sequence
from typing import IO, cast, final

# ---------------------------------------------------------------------------
# Memory layout (all sizes in bits, each bit stored as one byte 0x00/0x01):
#   [0..1023]          — reserved empty (1024 bits)
#   [1024..1055]       — reserved display settings (32 bits)
#   [1056..1071]       — display width (16 bits)
#   [1072..1087]       — display height (16 bits)
#   [1088..1088+w*h-1] — display pixel data (1 = white, 0 = black)
#   [1088+w*h .. end]  — user memory (smart addressing starts here)
# ---------------------------------------------------------------------------

RESERVED_BITS = 1024
DISPLAY_SETTINGS_BITS = 32
WIDTH_BITS = 16
HEIGHT_BITS = 16
HEADER_BITS = RESERVED_BITS + DISPLAY_SETTINGS_BITS + WIDTH_BITS + HEIGHT_BITS  # 1088

_DISPLAY_LUT = bytes([0, 255] + [0] * 254)


def _pack_int(value: int, n_bits: int) -> bytes:
    """Pack an integer into `n_bits` bytes of 0/1 (MSB first)."""
    return bytes([(value >> (n_bits - 1 - i)) & 1 for i in range(n_bits)])


def _unpack_int(mem: Sequence[int], offset: int, n_bits: int) -> int:
    """Read `n_bits` bytes of 0/1 starting at `offset`, return integer."""
    v = 0
    for i in range(n_bits):
        v = (v << 1) | mem[offset + i]
    return v


@final
class POS:
    """
    Connection to a pos instance via memory-mapped .pos file.

    Usage:
        pos = POS("system.pos")          # connect to existing
        pos = POS.create("new.pos", ...) # create new
    """

    def __init__(self, filename: str):
        """Connect to an existing .pos file."""
        if not os.path.exists(filename):
            raise FileNotFoundError(
                f"{filename} not found. Start the pos server first, or use POS.create() to make a new one."
            )
        self._filename: str = filename
        with open(filename, "r+b") as fd:
            self._fd: IO[bytes] = os.fdopen(os.dup(fd.fileno()), "r+b")
        self._mem: mmap.mmap = mmap.mmap(self._fd.fileno(), 0)  # map entire file

        self.display_width: int = _unpack_int(
            cast(Sequence[int], cast(object, self._mem)),
            RESERVED_BITS + DISPLAY_SETTINGS_BITS,
            WIDTH_BITS,
        )
        self.display_height: int = _unpack_int(
            cast(Sequence[int], cast(object, self._mem)),
            RESERVED_BITS + DISPLAY_SETTINGS_BITS + WIDTH_BITS,
            HEIGHT_BITS,
        )
        self._display_start: int = HEADER_BITS
        self._display_end: int = HEADER_BITS + self.display_width * self.display_height
        self._user_start: int = self._display_end

    @classmethod
    def create(
        cls,
        filename: str,
        total_bits: int,
        display_width: int,
        display_height: int,
    ) -> "POS":
        """Create a new .pos file and return a POS connected to it."""
        display_pixels = display_width * display_height
        min_required = HEADER_BITS + display_pixels
        if total_bits < min_required:
            raise ValueError(
                f"Need >= {min_required} bits for {display_width}x{display_height} display, got {total_bits}"
            )
        if not 1 <= display_width < (1 << WIDTH_BITS):
            raise ValueError(f"Width must be 1..{(1 << WIDTH_BITS) - 1}")
        if not 1 <= display_height < (1 << HEIGHT_BITS):
            raise ValueError(f"Height must be 1..{(1 << HEIGHT_BITS) - 1}")

        mem = bytearray(total_bits)
        width_offset = RESERVED_BITS + DISPLAY_SETTINGS_BITS
        mem[width_offset : width_offset + WIDTH_BITS] = _pack_int(
            display_width, WIDTH_BITS
        )
        height_offset = width_offset + WIDTH_BITS
        mem[height_offset:HEADER_BITS] = _pack_int(display_height, HEIGHT_BITS)
        with open(filename, "wb") as f:
            _ = f.write(mem)

        return cls(filename)

    @staticmethod
    def _to_bits(data: Sequence[int] | str) -> list[int]:
        """Normalize input: '101' -> [1,0,1], passthrough lists."""
        if isinstance(data, str):
            return [int(c) for c in data]
        return list(data)

    # --- public API ---------------------------------------------------------

    def read(self, start: int, length: int, *, smart: bool = True) -> list[int]:
        """
        Read `length` bits starting from `start`.

        smart=True (default): start is relative to first user bit.
        smart=False: raw memory address.
        """
        if smart:
            start += self._user_start
        if start + length > len(self._mem):
            raise IndexError("read overflows memory")
        return list(self._mem[start : start + length])

    def write(self, data: Sequence[int] | str, start: int, *, smart: bool = True) -> None:
        """
        Write `data` (list of 0/1/2, or string like "1021") starting at `start`.
        A value of 2 is transparent — that bit is left unchanged.

        smart=True (default): start is relative to first user bit.
        smart=False: raw memory address.
        """
        data = self._to_bits(data)
        if smart:
            start += self._user_start
        if start + len(data) > len(self._mem):
            raise IndexError("write overflows memory")
        for i, b in enumerate(data):
            if b == 2:
                continue
            self._mem[start + i] = b & 1

    def dwrite(self, data: Sequence[int] | str, start: int = 0, *, smart: bool = True) -> None:
        """
        Write `data` (list of 0/1/2, or string like "1021") to the display region.
        Overflow is silently clipped. A value of 2 is transparent — that pixel
        is left unchanged. Negative start indices or data values are rejected.

        smart=True (default): start=0 is first display pixel.
        """
        if start < 0:
            raise ValueError("start index cannot be negative")
        data = self._to_bits(data)
        if any(b < 0 for b in data if b != 2):
            raise ValueError("data cannot contain negative numbers")
        if smart:
            start += self._display_start
        cap = max(0, self._display_end - start)
        for i, b in enumerate(data[:cap]):
            if b == 2:
                continue
            self._mem[start + i] = b & 1

    def dread(
        self, start: int = 0, length: int | None = None, *, smart: bool = True
    ) -> list[int]:
        """
        Read from the display region.

        smart=True (default): start=0 is first display pixel.
        length=None reads to end of display.
        """
        if smart:
            start += self._display_start
        if length is None:
            length = self._display_end - start
        length = min(length, self._display_end - start)
        if length <= 0:
            return []
        return list(self._mem[start : start + length])

    @property
    def user_memory_size(self) -> int:
        """Number of bits available for user data (after display region)."""
        return len(self._mem) - self._user_start

    @property
    def total_bits(self) -> int:
        return len(self._mem)

    def close(self) -> None:
        """Flush and close the memory-mapped file."""
        self._mem.flush()
        self._mem.close()
        self._fd.close()

    def __enter__(self) -> "POS":
        return self

    def __exit__(
        self, exc_type: object, exc: object, tb: object
    ) -> None:
        self.close()

    # --- display (server-side only) -----------------------------------------

    def run_display(self) -> None:
        """Start the display window. Blocks until window is closed."""
        import tempfile
        import tkinter as tk

        root = tk.Tk()
        root.title(f"pos — {os.path.basename(self._filename)}")
        _ = root.configure(bg="gray")

        w, h = self.display_width, self.display_height

        SCALES = [0.5, 0.75, 1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]
        SCALE_MAP = {
            0.5: (1, 2),
            0.75: (3, 4),
            1.0: (1, 1),
            1.2: (6, 5),
            1.5: (3, 2),
            2.0: (2, 1),
            3.0: (3, 1),
            4.0: (4, 1),
            5.0: (5, 1),
            6.0: (6, 1),
            8.0: (8, 1),
            10.0: (10, 1),
        }

        # Auto-zoom fits within 400x400 limit initially
        auto_scale = max(0.5, min(400 / max(w, 1), 400 / max(h, 1)))
        current_scale: float = min(SCALES, key=lambda s: abs(s - auto_scale))

        label = tk.Label(root, borderwidth=0, highlightthickness=0, bg="black")
        label.pack(padx=10, pady=10)

        pgm_header = f"P5\n{w} {h}\n255\n".encode()
        tmpfile = os.path.join(tempfile.gettempdir(), f"pos_display_{os.getpid()}.pgm")
        last_snap: list[bytes | None] = [None]
        photo_ref: list[tk.PhotoImage | None] = [None]

        def update():
            snap = bytes(self._mem[self._display_start : self._display_end])
            if snap != last_snap[0]:
                last_snap[0] = snap
                pixels = snap.translate(_DISPLAY_LUT)
                with open(tmpfile, "wb") as f:
                    _ = f.write(pgm_header)
                    _ = f.write(pixels)
                img = tk.PhotoImage(file=tmpfile)
                z, s = SCALE_MAP.get(current_scale, (1, 1))
                if z > 1:
                    img = img.zoom(z)
                if s > 1:
                    img = img.subsample(s)
                _ = label.configure(image=img)
                photo_ref[0] = img
            _ = root.after(33, update)  # ~30 fps

        def trigger_update():
            last_snap[0] = None
            update()

        def set_scale(new_scale: float) -> None:
            nonlocal current_scale
            if new_scale in SCALE_MAP:
                current_scale = new_scale
                trigger_update()

        def zoom_in():
            idx = SCALES.index(current_scale)
            if idx < len(SCALES) - 1:
                set_scale(SCALES[idx + 1])

        def zoom_out():
            idx = SCALES.index(current_scale)
            if idx > 0:
                set_scale(SCALES[idx - 1])

        def set_max_size() -> None:
            max_w, max_h = root.maxsize()
            fits = [s for s in SCALES if w * s <= max_w and h * s <= max_h]
            set_scale(max(fits) if fits else 0.5)

        # menu
        menubar = tk.Menu(root)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=zoom_in)
        view_menu.add_command(label="Zoom Out", command=zoom_out)
        view_menu.add_command(label="Max Size", command=set_max_size)
        _ = menubar.add_cascade(label="View", menu=view_menu)
        _ = root.config(menu=menubar)

        def on_close():
            root.destroy()
            try:
                os.unlink(tmpfile)
            except OSError:
                pass

        _ = root.protocol("WM_DELETE_WINDOW", on_close)
        _ = root.after(1, update)
        root.mainloop()


# ---------------------------------------------------------------------------
# CLI — run this file to start the pos server.
#
#   python3 posetem/pos.py                  # new pos (prompts)
#   python3 posetem/pos.py system.pos       # load existing (no prompts)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        fname = sys.argv[1]
    else:
        fname = input("pos filename (e.g. system.pos): ").strip()

    if os.path.exists(fname):
        pos = POS(fname)
        print(
            f"Loaded {fname} — {pos.total_bits} bits, display {pos.display_width}×{pos.display_height}, user memory {pos.user_memory_size} bits"
        )
    else:
        print(f"Creating new pos: {fname}")
        total = int(input("  Total memory size (bits): "))
        w = int(input("  Display width  (pixels) : "))
        h = int(input("  Display height (pixels) : "))
        pos = POS.create(fname, total, w, h)
        print(
            f"Created — {pos.total_bits} bits, display {pos.display_width}×{pos.display_height}, user memory {pos.user_memory_size} bits"
        )

    print("Display running. Close window to stop.")
    try:
        pos.run_display()
    except KeyboardInterrupt:
        pass
    finally:
        pos.close()
        print("pos stopped.")
