"""
Example client script — connect to a running pos and draw on it.

Usage:
  1. Terminal 1:  python3 posetem/pos.py system.pos
                  (create with e.g. 2000 bits, 40x20 display)
  2. Terminal 2:  python3 examples/demo.py
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from posetem import POS

POSFILE = os.environ.get("POS_FILE", "sys.pos")

pos = POS(POSFILE)
W, H = pos.display_width, pos.display_height
print(f"Connected to {POSFILE} — {W}×{H} display, {pos.user_memory_size} user bits")

# Draw a border.
border = [0] * (W * H)
for y in range(H):
    for x in range(W):
        if x == 0 or x == W - 1 or y == 0 or y == H - 1:
            border[y * W + x] = 1
pos.dwrite(border)
print("Border drawn.")

time.sleep(0.5)

# Draw a diagonal line inside the border.
for i in range(1, min(W, H) - 1):
    pos.dwrite([1], start=i * W + i)
    time.sleep(0.03)
print("Diagonal drawn.")

# Write + read user memory.
pos.write([1, 0, 1, 0, 1, 0, 1, 0], start=0)
print(f"User memory[0:8] = {pos.read(0, 8)}")

pos.close()
print("Done. Display in server terminal should show the result.")