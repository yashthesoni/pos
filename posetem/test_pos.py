"""Minimal self-check — run: python3 posetem/test_pos.py"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from posetem.pos import HEADER_BITS, POS


def test():
    W, H = 8, 4
    # Get a unique temp path (don't keep the empty file).
    fd, fname = tempfile.mkstemp(suffix=".pos")
    os.close(fd)
    os.unlink(fname)

    try:
        pos = POS.create(fname, total_bits=2000, display_width=W, display_height=H)

        # Smart write/read in user memory.
        pos.write([1, 1, 0, 1], start=0)
        assert pos.read(0, 4) == [1, 1, 0, 1], "user memory read/write failed"

        # Raw addressing: first user bit is at HEADER_BITS + W*H.
        raw_start = HEADER_BITS + W * H
        assert pos.read(raw_start, 4, smart=False) == [1, 1, 0, 1], "raw read failed"

        # dwrite / dread.
        pos.dwrite([1, 0, 1, 0])
        assert pos.dread(0, 4) == [1, 0, 1, 0], "dwrite/dread failed"

        # dwrite clips at display boundary.
        big = [1] * 1000
        pos.dwrite(big)  # should not raise
        assert len(pos.dread()) == W * H, "dread length mismatch"

        # user_memory_size.
        expected = pos.total_bits - HEADER_BITS - W * H
        assert pos.user_memory_size == expected, (
            f"user_memory_size: {pos.user_memory_size} != {expected}"
        )

        # Persistence: close + reopen via mmap.
        pos.close()
        pos2 = POS(fname)
        assert pos2.display_width == W, "reloaded width mismatch"
        assert pos2.display_height == H, "reloaded height mismatch"
        assert pos2.total_bits == 2000, "reloaded total_bits mismatch"
        assert pos2.read(0, 4) == [1, 1, 0, 1], "reloaded user data mismatch"
        assert pos2.dread(0, 4) == [1, 1, 1, 1], "reloaded display data mismatch"
        pos2.close()

        print("All checks passed.")
    finally:
        if os.path.exists(fname):
            os.unlink(fname)


if __name__ == "__main__":
    test()
