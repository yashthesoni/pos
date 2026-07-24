# Font and Text Layout Handler Documentation

The `FontHandler` class handles text writing and multi-line formatting on the display using Poskii font glyphs.

## Class Overview

* **Source File**: `posfont.py`
* **Import Path**: `from utils.text.posfont import FontHandler`
* The standalone `wrap_text` function can also be imported directly: `from utils.text.posfont import wrap_text`

---

## Standalone Function

### `wrap_text(text, line_width, char_w, letter_sp, word_sp) -> List[List[str]]`

Pure layout function — no graphics dependency. Takes text and pixel dimensions, returns wrapped lines grouped by paragraph.

* **`text`**: Input string (may contain `\n`).
* **`line_width`**: Maximum line width in pixels.
* **`char_w`**: Pixel width of one character.
* **`letter_sp`**: Pixel spacing between characters.
* **`word_sp`**: Pixel spacing between words.
* **Returns**: List of paragraphs, each a list of line strings.

Paragraphs are split by `\n`. Words within each paragraph are greedily grouped onto lines. If a single word exceeds `line_width`, it is split character-by-character and a warning is printed to the terminal.

---

## Initialization

```python
def __init__(self, graphics: GraphicsHandler, font: dict) -> None:
```

* **`graphics`**: The active `GraphicsHandler` instance.
* **`font`**: The font dict containing `font_file` and properties (`width`, `height`, `letter_spacing`, `word_spacing`, `line_spacing`, `paragraph_spacing`).

---

## API Reference

### `window_size` *(property)* → `(width, height)`
Usable pixel dimensions of the graphics window.

### `chars_per_line(scale=1) -> int`
Maximum characters that fit in one horizontal line.

### `max_lines(scale=1) -> int`
Maximum text lines that fit vertically.

### `write_words(text, cordinates=None, margin=0, scale=1, transparent=False, inverted=False) -> None`
Renders a single line of text. Characters are drawn sequentially using `letter_spacing`.

### `dprint(text, cordinates=None, margin=0, scale=1, transparent=False, inverted=False, line_width=None) -> None`
Multi-line text rendering with smart word wrapping.
* **Paragraph breaks** (`\n`): Uses `paragraph_spacing` from the font.
* **Soft wraps** (line overflow): Uses `line_spacing` from the font.
* **Word gaps**: Uses `word_spacing` from the font.
* **Oversized words**: Split character-by-character with a terminal warning.
* **`line_width`**: Maximum line width in pixels. Defaults to the graphics window width.

---

## Usage Example

```python
from posetem import POS
from utils.graphics import GraphicsHandler
from utils.text.posfont import FontHandler, wrap_text

pos = POS("sys.pos")
g = GraphicsHandler(pos, margin=5)
fh = FontHandler(g, MyFont)

# Multi-line text with automatic wrapping
fh.dprint("Hello World!\nThis is a new paragraph.", cordinates=[0, 0])

# Use wrap_text independently for layout calculations
lines = wrap_text("Some long text here", line_width=60, char_w=5, letter_sp=1, word_sp=4)
# lines = [['Some long', 'text here']]  — one paragraph, two lines
```
