# Font and Text Layout Handler Documentation

The [PosFontHandler](file:///Users/yashsoni/Codes/pos/utils/text/posfont.py#L9) class handles text writing and single-line formatting on the display using Poskii font glyphs.

## Class Overview

* **Source File**: [posfont.py](file:///Users/yashsoni/Codes/pos/utils/text/posfont.py)
* **Import Path**: `from utils.text.posfont import PosFontHandler`

---

## Initialization

```python
def __init__(self, graphics: GraphicsHandler, font: Any) -> None:
```

* **`graphics`**: The active [GraphicsHandler](file:///Users/yashsoni/Codes/pos/utils/graphics.py#L12) instance.
* **`font`**: The font class or module containing `font_file` and font properties (such as glyph width, height, and spacing).

---

## API Reference

### `write_line(text: str, cordinates: Optional[List[int]] = None, margin: int = 0, scale: int = 1, transparent: bool = False, inverted: bool = False) -> None`
Renders a single line of text onto the screen. Characters are drawn sequentially in a single row.
* **Parameters**:
  * `text`: The single-line text string to render.
  * `cordinates`: The starting `[x, y]` coordinates. Defaults to `[0, 0]`.
  * `margin`: Horizontal margin added to each line.
  * `scale`: Integer scaling factor.
  * `transparent`: If `True`, background pixels of glyphs are transparent.
  * `inverted`: If `True`, swaps foreground/background colors.

---

## Usage Example

```python
from posetem import POS
from utils.graphics import GraphicsHandler
from utils.text.posfont import PosFontHandler

# Setup connection and handlers
pos = POS("sys.pos")
g = GraphicsHandler(pos)
fh = PosFontHandler(g, MyFont)

# Write a single line of text to coordinates (0, 0)
fh.write_line("Hello World", cordinates=[0, 0], scale=2)
```
