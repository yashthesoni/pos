# Font and Text Layout Handler Documentation

The `FontHandler` class handles text writing and single-line formatting on the display using Poskii font glyphs.

## Class Overview

* **Source File**: `posfont.py`
* **Import Path**: `from utils.text.posfont import FontHandler`

The FontHandler is aware of the graphics window. Text that overflows the usable area is silently clipped by the underlying graphics clipping layer. Helper properties let you query how much space is available for layout.

---

## Initialization

```python
def __init__(self, graphics: GraphicsHandler, font: dict) -> None:
```

* **`graphics`**: The active `GraphicsHandler` instance.
* **`font`**: The font dict containing `font_file` and font properties (such as glyph width, height, and spacing).

---

## API Reference

### `window_size` *(property)* → `(width, height)`
Returns the usable pixel dimensions of the graphics window. Useful for text layout calculations.

### `chars_per_line(scale: int = 1) -> int`
Returns the maximum number of characters that fit in one horizontal line of the current window at the given scale.

### `max_lines(scale: int = 1) -> int`
Returns the maximum number of text lines that fit vertically in the current window at the given scale.

### `write_words(text: str, cordinates: Optional[List[int]] = None, margin: int = 0, scale: int = 1, transparent: bool = False, inverted: bool = False) -> None`
Renders a single line of text onto the screen. Characters are drawn sequentially in a single row. Overflow is silently clipped.
* **Parameters**:
  * `text`: The single-line text string to render.
  * `cordinates`: The starting `[x, y]` coordinates. Defaults to `[0, 0]`.
  * `margin`: Margin offset added to each character.
  * `scale`: Integer scaling factor.
  * `transparent`: If `True`, background pixels of glyphs are transparent.
  * `inverted`: If `True`, swaps foreground/background colors.

---

## Usage Example

```python
from posetem import POS
from utils.graphics import GraphicsHandler
from utils.text.posfont import FontHandler

# Setup connection and handlers
pos = POS("sys.pos")
g = GraphicsHandler(pos, margin=5)
fh = FontHandler(g, MyFont)

# Query available space
print(fh.window_size)       # (118, 54)
print(fh.chars_per_line())  # e.g. 19 for a 5px-wide font with 1px spacing
print(fh.max_lines())       # e.g. 4 for a 9px-tall font with 2px spacing

# Write text — overflow is silently clipped
fh.write_words("Hello World", cordinates=[0, 0], scale=2)
```
