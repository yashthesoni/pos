"""
Font and text rendering layout handler for the pos simulator.
"""

from typing import Any, Optional, List
from utils.graphics import GraphicsHandler
from utils.text.poskii import PoskiiHandler


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
        """
        Usable (width, height) of the graphics window in pixels.
        Useful for calculating how many characters fit on screen.
        """
        return self.graphics.window_size

    def chars_per_line(self, scale: int = 1) -> int:
        """
        Calculate how many characters fit in one line of the current window.

        Args:
            scale: Pixel scaling factor.

        Returns:
            Number of characters that fit horizontally.
        """
        w = self.font['properties']["width"] * scale
        ls = self.font['properties']["letter_spacing"] * scale
        avail = self.graphics.window_width
        if avail <= 0 or w <= 0:
            return 0
        # First char takes w pixels, each subsequent takes w + ls
        return max(0, 1 + (avail - w) // (w + ls)) if avail >= w else 0

    def max_lines(self, scale: int = 1) -> int:
        """
        Calculate how many lines of text fit vertically in the current window.

        Args:
            scale: Pixel scaling factor.

        Returns:
            Number of text lines that fit vertically.
        """
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
            margin: Horizontal offset added to character drawing line.
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
