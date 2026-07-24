"""
Font and text rendering layout handler for the pos simulator.
"""

import warnings
from typing import Optional, List
from utils.graphics import GraphicsHandler
from utils.text.poskii import PoskiiHandler


def _word_px(word: str, char_w: int, letter_sp: int) -> int:
    """Pixel width of a word."""
    n = len(word)
    return n * char_w + max(0, n - 1) * letter_sp if n else 0


def _split_long_word(word: str, line_width: int, char_w: int, letter_sp: int) -> List[str]:
    """Break an oversized word into fitting chunks."""
    chunks, chunk, w = [], "", 0
    for ch in word:
        added = char_w if not chunk else letter_sp + char_w
        if chunk and w + added > line_width:
            chunks.append(chunk)
            chunk, w = ch, char_w
        else:
            chunk += ch
            w += added
    if chunk:
        chunks.append(chunk)
    return chunks


def wrap_text(
    text: str, line_width: int, char_w: int, letter_sp: int, word_sp: int
) -> List[List[str]]:
    """
    Lay out text into wrapped lines grouped by paragraph.

    Splits by '\\n' into paragraphs, then wraps each paragraph's words
    into lines that fit within line_width pixels. Words too long for a
    single line are split character-by-character with a terminal warning.

    Args:
        text: Input text with optional '\\n' paragraph breaks.
        line_width: Maximum line width in pixels.
        char_w: Pixel width of a single character.
        letter_sp: Pixel spacing between adjacent characters.
        word_sp: Pixel spacing between words.

    Returns:
        List of paragraphs, each a list of line strings.
    """
    result = []
    for para in text.split('\n'):
        words = para.split()
        if not words:
            result.append([''])
            continue
        lines, cur, cur_w = [], [], 0
        for word in words:
            wpx = _word_px(word, char_w, letter_sp)
            if wpx > line_width:
                warnings.warn(f"Word '{word}' exceeds line width, splitting by character")
                if cur:
                    lines.append(' '.join(cur))
                    cur, cur_w = [], 0
                chunks = _split_long_word(word, line_width, char_w, letter_sp)
                for c in chunks[:-1]:
                    lines.append(c)
                if chunks:
                    cur, cur_w = [chunks[-1]], _word_px(chunks[-1], char_w, letter_sp)
            elif not cur:
                cur, cur_w = [word], wpx
            elif cur_w + word_sp + wpx <= line_width:
                cur.append(word)
                cur_w += word_sp + wpx
            else:
                lines.append(' '.join(cur))
                cur, cur_w = [word], wpx
        if cur:
            lines.append(' '.join(cur))
        result.append(lines if lines else [''])
    return result


class FontHandler:
    """
    Handles text formatting and drawing text on the display using Poskii fonts.
    """

    def __init__(self, graphics: GraphicsHandler, font: dict) -> None:
        """
        Initialize the font handler with a graphics context and a font.

        Args:
            graphics: The active GraphicsHandler to blit characters.
            font: A dict containing font information.
        """
        self.graphics: GraphicsHandler = graphics
        self.font: dict = font
        self.poskii: PoskiiHandler = PoskiiHandler(font)

    @property
    def window_size(self):
        """Usable (width, height) of the graphics window in pixels."""
        return self.graphics.window_size

    def chars_per_line(self, scale: int = 1) -> int:
        """How many characters fit in one line of the current window."""
        w = self.font['properties']["width"] * scale
        ls = self.font['properties']["letter_spacing"] * scale
        avail = self.graphics.window_width
        if avail <= 0 or w <= 0:
            return 0
        return max(0, 1 + (avail - w) // (w + ls)) if avail >= w else 0

    def max_lines(self, scale: int = 1) -> int:
        """How many lines of text fit vertically in the current window."""
        h = self.font['properties']["height"] * scale
        lns = self.font['properties']["line_spacing"] * scale
        avail = self.graphics.window_height
        if avail <= 0 or h <= 0:
            return 0
        return max(0, 1 + (avail - h) // (h + lns)) if avail >= h else 0

    def write_words(
        self,
        text: str,
        cordinates: Optional[List[int]] = None,
        margin: int = 0,
        scale: int = 1,
        transparent: bool = False,
        inverted: bool = False,
    ) -> None:
        """
        Write a single line of text on the display.

        Args:
            text: The single line string to draw.
            cordinates: Starting top-left [x, y] coordinates. Defaults to [0, 0].
            margin: Offset added to character positions.
            scale: Pixel scaling factor.
            transparent: Whether background '0' pixels in glyphs are transparent.
            inverted: Whether to swap black/white pixels.
        """
        if cordinates is None:
            cordinates = [0, 0]

        start_x, start_y = cordinates[0], cordinates[1]
        w: int = self.font['properties']["width"]
        ls: int = self.font['properties']["letter_spacing"]

        current_x: int = start_x
        for char in text:
            glyph = self.poskii.get_arr(char)
            self.graphics.image(
                glyph,
                w,
                cordinates=[current_x, start_y],
                margin=margin,
                scale=scale,
                transparent=transparent,
                inverted=inverted,
            )
            current_x += (w + ls) * scale

    def dprint(
        self,
        text: str,
        cordinates: Optional[List[int]] = None,
        margin: int = 0,
        scale: int = 1,
        transparent: bool = False,
        inverted: bool = False,
        line_width: Optional[int] = None,
    ) -> None:
        """
        Multi-line text rendering with smart word wrapping.

        Splits text by '\\n' for paragraph breaks (using paragraph_spacing),
        and soft-wraps within paragraphs (using line_spacing). Words too long
        for one line are split by character with a terminal warning.

        Args:
            text: The text string to render (may contain '\\n').
            cordinates: Starting top-left [x, y] coordinates. Defaults to [0, 0].
            margin: Offset added to character positions.
            scale: Pixel scaling factor.
            transparent: Whether background '0' pixels in glyphs are transparent.
            inverted: Whether to swap black/white pixels.
            line_width: Maximum line width in pixels. Defaults to the window width.
        """
        if cordinates is None:
            cordinates = [0, 0]

        props = self.font['properties']
        char_w = props['width'] * scale
        letter_sp = props['letter_spacing'] * scale
        word_sp = props.get('word_spacing', props['letter_spacing']) * scale
        line_sp = props['line_spacing'] * scale
        para_sp = props.get('paragraph_spacing', props['line_spacing']) * scale
        font_h = props['height'] * scale

        if line_width is None:
            line_width = self.graphics.window_width - 2 * margin

        wrapped = wrap_text(text, line_width, char_w, letter_sp, word_sp)

        y = cordinates[1]
        for p_idx, para_lines in enumerate(wrapped):
            if p_idx > 0:
                y += para_sp
            for l_idx, line in enumerate(para_lines):
                if l_idx > 0:
                    y += line_sp
                if line:
                    x = cordinates[0]
                    for w_idx, word in enumerate(line.split(' ')):
                        if w_idx > 0:
                            x += word_sp
                        self.write_words(
                            word, cordinates=[x, y], margin=margin,
                            scale=scale, transparent=transparent, inverted=inverted,
                        )
                        x += _word_px(word, char_w, letter_sp)
                y += font_h