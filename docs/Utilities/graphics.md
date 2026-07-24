# Graphics Library Documentation

The `GraphicsHandler` class provides high-level 2D drawing functions built on top of the raw 1D bit array display memory of the `pos` OS simulator.

## Class Overview

* **Source File**: `graphics.py`
* **Import Path**: `from utils.graphics import GraphicsHandler`

The class abstracts pixel coordinates, line drawing, and blitting images. It supports coordinate mapping relative to a viewport **origin offset** and a **clipping window** that tracks the usable drawing area.

---

## Window System

The **window** is the usable sub-region of the display, defined by four edges (left, top, right, bottom) in absolute display coordinates.

* By default the window spans the entire display.
* When a **margin** is applied (via constructor or `set_margin()`), the window shrinks inward equally from all four sides.
* A custom window can be set via `set_window()`.
* If the window extends beyond the physical display, pixels are **silently clipped** at draw time — the window definition itself is never rejected.

All drawing methods (`plot`, `image`, `line`, `lineH`, `lineV`) route through an intermediary clipping layer. Pixels that fall outside the window or the physical display are silently dropped rather than raising errors.

---

## Initialization

```python
def __init__(self, pos: POS, origin: Optional[List[int]] = None, margin: int = 0) -> None:
```

* **`pos`**: An active connection instance of the `POS` client.
* **`origin`**: An optional list `[x_offset, y_offset]` in pixels. All coordinate values passed to drawing methods will be offset relative to this origin. Defaults to `[0, 0]`.
* **`margin`**: Uniform margin in pixels applied to all four sides of the display, shrinking the usable window inward. Defaults to `0`.

---

## API Reference

### Window Management

#### `set_window(left: int, top: int, right: int, bottom: int) -> None`
Set a custom clipping window in absolute display coordinates.
* `left`, `top`: Inclusive start edges.
* `right`, `bottom`: Exclusive end edges (one past last valid pixel).

#### `set_margin(margin: int) -> None`
Convenience method — sets the window by insetting `margin` pixels from every edge of the display.

#### `window` *(property)* → `(left, top, right, bottom)`
Returns the current window edges as a tuple.

#### `window_width` *(property)* → `int`
Usable width of the window in pixels.

#### `window_height` *(property)* → `int`
Usable height of the window in pixels.

#### `window_size` *(property)* → `(width, height)`
Usable dimensions of the window as a tuple.

---

### Drawing

#### `cord(x: int = 1, y: int = 1) -> int`
Translates 2D viewport coordinates into a 1D index offset in the display memory, applying the origin offset.
* **Returns**: Flat 1D index integer mapping to display memory.

#### `plot(x: int = 1, y: int = 1, inverted: bool = False, margin: int = 0) -> None`
Plots a single pixel at the specified coordinate. Clipped silently if outside the window.

#### `clear() -> None`
Resets the entire screen display memory, filling it with black pixels (`0`).

#### `image(array: str, line_length: int, cordinates: Optional[List[int]] = None, margin: int = 0, scale: int = 1, transparent: bool = False, inverted: bool = False) -> None`
Blits a binary bitmap string onto the screen. Pixels outside the window are silently clipped on a per-row basis.
* **Parameters**:
  * `array`: Pixel data representation (whitespace is automatically stripped).
  * `line_length`: Width of the source image in pixels.
  * `cordinates`: The `[x, y]` start coordinate for the top-left corner. Defaults to `[0, 0]`.
  * `margin`: Margin offset added to coordinates during drawing.
  * `scale`: Scaling factor integer (must be ≥ 1).
  * `transparent`: If `True`, `0` pixels are treated as transparent.
  * `inverted`: If `True`, inverts image pixels before rendering.

#### `line(x0, y0, x1, y1, inverted=False, margin=0) -> None`
Draws a line between two points using Bresenham's algorithm. Pixels outside the window are silently clipped.

#### `lineH(x, y, length, inverted=False, margin=0) -> None`
Draws a horizontal line. Pixels outside the window are silently clipped.

#### `lineV(x, y, length, inverted=False, margin=0) -> None`
Draws a vertical line. Pixels outside the window are silently clipped.

---

## Examples

### Using the Window System
```python
from posetem import POS
from utils.graphics import GraphicsHandler

pos = POS("sys.pos")  # 128x64 display

# Create handler with 5px margin on all sides
g = GraphicsHandler(pos, margin=5)

print(g.window)        # (5, 5, 123, 59)
print(g.window_size)   # (118, 54)

# Anything drawn outside the 118x54 usable area is silently clipped
g.lineH(0, 0, 200)     # only draws within the window, no error
```

### Custom Window
```python
g = GraphicsHandler(pos)
g.set_window(10, 10, 100, 50)  # restrict drawing to a sub-region
print(g.window_width)          # 90
```

### Drawing Shapes relative to an Origin
```python
pos = POS("sys.pos")
# Viewport centered starting at x=10, y=10
g = GraphicsHandler(pos, origin=[10, 10])

# Draw a 10x10 border frame relative to the origin
g.lineH(0, 0, 10)
g.lineH(0, 9, 10)
g.lineV(0, 0, 10)
g.lineV(9, 0, 10)
```