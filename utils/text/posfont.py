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

    def __init__(self, graphics: GraphicsHandler, font: Any) -> None:
        """
        Initialize the font handler with a graphics context and a font.

        Args:
            graphics: The active GraphicsHandler to blit characters.
            font: The font definition class/object.
        """
        self.graphics: GraphicsHandler = graphics
        self.font: Any = font
        self.poskii: PoskiiHandler = PoskiiHandler(font)

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
        w: int = self.font.properties.get("width", 5)
        ls: int = self.font.properties.get("letter_spacing", 1)

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
