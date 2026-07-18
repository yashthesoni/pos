# Graphics Library Documentation

The `GraphicsHandler` class provides high-level 2D drawing functions built on top of the raw 1D bit array display memory of the `pos` OS simulator.

## Class Overview

* **Source File**: `graphics.py`
* **Import Path**: `from utils.graphics import GraphicsHandler`

The class abstracts pixel coordinates, line drawing, and blitting images. It supports coordinate mapping relative to a viewport **origin offset**.

---

## Initialization

```python
def __init__(self, pos: POS, origin: Optional[List[int]] = None) -> None:
```

* **`pos`**: An active connection instance of the `POS` client.
* **`origin`**: An optional list `[x_offset, y_offset]` in pixels. All coordinate values passed to drawing methods will be offset relative to this origin. Defaults to `[0, 0]`.

---

## API Reference

### 1. `cord(x: int = 1, y: int = 1) -> int`
Translates 2D viewport coordinates into a 1D index offset in the display memory, applying the origin offset.
* **Parameters**:
  * `x`: Column coordinate (defaults to `1`).
  * `y`: Row coordinate (defaults to `1`).
* **Returns**: Flat 1D index integer mapping to display memory.

### 2. `plot(x: int = 1, y: int = 1, inverted: bool = False) -> None`
Plots a single pixel at the specified coordinate.
* **Parameters**:
  * `x`: Column coordinate.
  * `y`: Row coordinate.
  * `inverted`: If `False`, writes a white pixel (`1`). If `True`, writes a black pixel (`0`).

### 3. `clear() -> None`
Resets the entire screen display memory, filling it with black pixels (`0`).

### 4. `image(array: str, line_length: int, cordinates: Optional[List[int]] = None, margin: int = 0, scale: int = 1, transparent: bool = False, inverted: bool = False) -> None`
Blits a binary bitmap string (made of `0`s and `1`s) onto the screen.
* **Parameters**:
  * `array`: Pixel data representation (whitespace is automatically stripped).
  * `line_length`: Width of the source image in pixels.
  * `cordinates`: The `[x, y]` start coordinate for the top-left corner. Defaults to `[0, 0]`.
  * `margin`: Horizontal margin added to each line during drawing.
  * `scale`: Scaling factor integer (must be $\ge 1$). Scaling duplicates pixels horizontally and duplicate lines vertically.
  * `transparent`: If `True`, `0` pixels in the image are treated as transparent (ignored, value `2` passed to POS), allowing the background to show through.
  * `inverted`: If `True`, inverts image pixels (`0` becomes `1` and vice versa) before rendering.

### 5. `line(x0: int, y0: int, x1: int, y1: int, inverted: bool = False) -> None`
Draws a line between `(x0, y0)` and `(x1, y1)` using Bresenham's Line Algorithm.
* **Parameters**:
  * `x0`, `y0`: Starting point coordinates.
  * `x1`, `y1`: Ending point coordinates.
  * `inverted`: If `True`, draws the line in black. If `False`, draws the line in white.

### 6. `lineH(x: int, y: int, length: int, inverted: bool = False) -> None`
Draws a horizontal line starting at `(x, y)` going right.
* **Parameters**:
  * `x`, `y`: Start coordinates.
  * `length`: Length of the line in pixels.
  * `inverted`: If `True`, draws in black; otherwise white.

### 7. `lineV(x: int, y: int, length: int, inverted: bool = False) -> None`
Draws a vertical line starting at `(x, y)` going down.
* **Parameters**:
  * `x`, `y`: Start coordinates.
  * `length`: Length of the line in pixels.
  * `inverted`: If `True`, draws in black; otherwise white.

---

## Examples

### Drawing Shapes relative to an Origin
```python
from posetem import POS
from utils.graphics import GraphicsHandler

pos = POS("sys.pos")
# Viewport centered starting at x=10, y=10
g = GraphicsHandler(pos, origin=[10, 10])

# Draw a 10x10 border frame relative to the origin
g.lineH(0, 0, 10)
g.lineH(0, 9, 10)
g.lineV(0, 0, 10)
g.lineV(9, 0, 10)
```