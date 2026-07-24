# Text and POSKII Handler Documentation

The `PoskiiHandler` class translates ASCII text strings into custom POSKII character codes, retrieves pixel array arrays from a font file, and prepares them for rendering onto the display.

## POSKII Character Set

POSKII is a custom 1-indexed character set containing 96 entries:
* **Codes 1–33**: Standard punctuation and space character (e.g. space, `!`, `"`, `#`, `$`, etc.).
* **Codes 34–43**: Alphanumeric digits `0` through `9`.
* **Codes 44–69**: Uppercase English alphabet `A` through `Z`.
* **Codes 70–95**: Lowercase English alphabet `a` through `z`.
* **Code 96**: The Unicode replacement character `\ufffd` (``), used as a fallback for invalid or unmapped characters.

---

## Class Overview

* **Source File**: `poskii.py`
* **Import Path**: `from utils.text.poskii import PoskiiHandler`

---

## Initialization

```python
def __init__(self, font: dict) -> None:
```

* **`font`**: An dict containing `font_file`, mapping POSKII character codes (1–96) to binary image pixel strings.

---

## API Reference

### 1. `pski(character: str) -> int`
Looks up the POSKII integer code corresponding to the given string character.
* **Parameters**:
  * `character`: A single-character string.
* **Returns**: The POSKII code point integer (1–96), or `0` if the character is not supported.

### 2. `char(code: int) -> str`
Looks up the standard character corresponding to the given POSKII code.
* **Parameters**:
  * `code`: A POSKII code point integer (1–96).
* **Returns**: The matching character string, or an empty string `""` if the code point is invalid.

### 3. `get_arr(char_or_code: str | int) -> str`
Retrieves the font bitmap pixel string representation for a given character or POSKII code.
* **Parameters**:
  * `char_or_code`: Either the string character (e.g., `'A'`) or its POSKII integer code (e.g., `44`).
* **Returns**: A string containing the pixel layout (made of `0`s and `1`s).
* **Errors & Fallbacks**: If the lookup fails or throws an exception, it falls back to the replacement character glyph (POSKII `96`).

---

## Font Format Specification

A font dictionary passed to `PoskiiHandler` must contain the following keys:
* `properties`: Dictionary indicating `height`, `width`, `letter_spacing`, and `line_spacing`.
* `font_file`: Dictionary mapping POSKII integers to space-separated binary rows.

### Font Example (5x9 pixels)
```python
MyFont = {
    'properties': {
        "height": 9,
        "width": 5,
        "letter_spacing": 1,
        "word_spacing": 5,
        "line_spacing": 2,
        "paragraph_spacing": 3
    },
    'font_file': {
        34: "00100 11100 00100 00100 00100 00100 00100 00100 11111", # Glyph '1'
        35: "01110 10001 10001 00001 00010 00100 01000 10000 11111", # Glyph '2'
        96: "00100 01110 01010 11011 11011 11111 01010 01110 00100", # Fallback Glyph
    }
}
```

---

## Usage Example

```python
from posetem import POS
from utils.graphics import GraphicsHandler
from utils.text.poskii import PoskiiHandler

# 1. Setup connection and handlers
pos = POS("sys.pos")
g = GraphicsHandler(pos)
t = PoskiiHandler(MyFont)

# 2. Get the pixel array for character '1' (POSKII code 34)
glyph_data = t.get_arr("1")  # equivalent to t.get_arr(34)

# 3. Draw the character to coordinates (0, 0)
g.image(glyph_data, line_length=MyFont['properties']["width"], cordinates=[0, 0])
```
