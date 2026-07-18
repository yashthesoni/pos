"""
Graphics Handler for pos.

Provides functions for coordinate translation, pixel plotting, screen clearing,
image rendering (blitting) with scaling, and line drawing.
"""

from typing import List, Optional
from posetem.pos import POS


class GraphicsHandler:
    """
    Utility handler for performing graphics and drawing operations on the pos display.
    Supports a viewport origin offset.
    """

    def __init__(self, pos: POS, origin: Optional[List[int]] = None) -> None:
        """
        Initialize the GraphicsHandler with a POS instance and an optional origin offset.

        Args:
            pos: The active POS client connection.
            origin: The [x, y] coordinates representing the viewport origin.
                All drawing operations are relative to this origin. Defaults to [0, 0] if None.
        """
        self.pos: POS = pos
        self.origin: List[int] = origin if origin is not None else [0, 0]
        if any(coord < 0 for coord in self.origin):
            raise ValueError("Origin coordinates cannot be negative")
        if self.pos is not None:
            if self.origin[0] >= self.pos.display_width or self.origin[1] >= self.pos.display_height:
                raise ValueError("Origin coordinates must be within display bounds")

    def cord(self, x: int = 1, y: int = 1) -> int:
        """
        Convert 2D screen coordinates into a 1D flat display memory address,
        applying the origin offset.

        Args:
            x: The X coordinate (column index). Defaults to 1.
            y: The Y coordinate (row index). Defaults to 1.

        Returns:
            The corresponding 1D index offset in the display memory.

        Raises:
            ValueError: If calculated coordinates are outside the display bounds.
        """
        actual_x = x + self.origin[0]
        actual_y = y + self.origin[1]
        if not (0 <= actual_x < self.pos.display_width and 0 <= actual_y < self.pos.display_height):
            raise ValueError("Coordinates out of display range")
        return self.pos.display_width * actual_y + actual_x

    def plot(self, x: int = 1, y: int = 1, inverted: bool = False, margin: int = 0) -> None:
        """
        Write a single pixel to the screen at the given coordinates.

        Args:
            x: The X coordinate. Defaults to 1.
            y: The Y coordinate. Defaults to 1.
            inverted: If True, writes black (0). Otherwise, writes white (1).
            margin: Margin offset applied to X and Y coordinates. Defaults to 0.
        """
        self.pos.dwrite("0" if inverted else "1", start=self.cord(x + margin, y + margin))

    def clear(self) -> None:
        """
        Clear the entire screen by writing black (0) to all display pixels.
        """
        self.pos.dwrite("0" * (self.pos.display_width * self.pos.display_height))

    def image(
        self,
        array: str,
        line_length: int,
        cordinates: Optional[List[int]] = None,
        margin: int = 0,
        scale: int = 1,
        transparent: bool = False,
        inverted: bool = False,
    ) -> None:
        """
        Render/blit a 2D binary image string onto the display, with scaling support.

        Args:
            array: A string containing the pixel representation (e.g. '0's and '1's).
            line_length: The width of the image in pixels.
            cordinates: The starting [x, y] coordinates to render the image at.
                Defaults to [0, 0] if None.
            margin: Extra horizontal margin added to each line during drawing. Defaults to 0.
            scale: An integer scaling factor. An image is scaled up by duplicating pixels
                both horizontally and vertically. Defaults to 1.
            transparent: If True, '0' pixels are treated as transparent (value '2')
                and will not overwrite background pixels. Defaults to False.
            inverted: If True, '0' and '1' pixels are swapped before rendering. Defaults to False.
        """
        if cordinates is None:
            cordinates = [0, 0]

        array = array.replace(" ", "")

        if inverted:
            _table = str.maketrans("01", "10")
            array = array.translate(_table)
        if transparent:
            array = array.replace("0", "2")

        lines: List[str] = [
            array[i : i + line_length] for i in range(0, len(array), line_length)
        ]

        # Apply scaling if scale is greater than 1
        if scale > 1:
            lines = list(map(lambda a: "".join(list(map(lambda x: x * scale, a))), lines))
            lines = [x for x in lines for _ in range(scale)]

        if not lines:
            self.cord(cordinates[0] + margin, cordinates[1] + margin)
            return

        start_x = cordinates[0] + margin
        start_y = cordinates[1] + margin
        for i, line_str in enumerate(lines):
            if not line_str:
                continue
            line_y = start_y + i
            start_idx = self.cord(start_x, line_y)
            # Check end of row line bounds
            self.cord(start_x + len(line_str) - 1, line_y)
            self.pos.dwrite(line_str, start=start_idx)

    def line(self, x0: int, y0: int, x1: int, y1: int, inverted: bool = False, margin: int = 0) -> None:
        """
        Draw a straight line between two points using Bresenham's Line Algorithm.

        Args:
            x0: Start point X coordinate.
            y0: Start point Y coordinate.
            x1: End point X coordinate.
            y1: End point Y coordinate.
            inverted: If True, draws the line in black (0) instead of white (1).
            margin: Optional margin offset added to coordinates.
        """
        dx: int = abs(x1 - x0)
        dy: int = abs(y1 - y0)

        step_x: int = 1 if x0 < x1 else -1
        step_y: int = 1 if y0 < y1 else -1

        x, y = x0, y0

        if dx >= dy:
            p: int = 2 * dy - dx
            for _ in range(dx + 1):
                self.plot(x, y, inverted, margin=margin)
                if p >= 0:
                    y += step_y
                    p -= 2 * dx
                p += 2 * dy
                x += step_x
        else:
            p = 2 * dx - dy
            for _ in range(dy + 1):
                self.plot(x, y, inverted, margin=margin)
                if p >= 0:
                    x += step_x
                    p -= 2 * dy
                p += 2 * dx
                y += step_y

    def lineH(self, x: int, y: int, length: int, inverted: bool = False, margin: int = 0) -> None:
        """
        Draw a horizontal line of a given length.

        Args:
            x: Starting X coordinate.
            y: Starting Y coordinate.
            length: Length of the line in pixels.
            inverted: If True, draws the line in black (0).
            margin: Optional margin offset added to coordinates.
        """
        for _ in range(length):
            self.plot(x + _, y, inverted, margin=margin)

    def lineV(self, x: int, y: int, length: int, inverted: bool = False, margin: int = 0) -> None:
        """
        Draw a vertical line of a given length.

        Args:
            x: Starting X coordinate.
            y: Starting Y coordinate.
            length: Length of the line in pixels.
            inverted: If True, draws the line in black (0).
            margin: Optional margin offset added to coordinates.
        """
        for _ in range(length):
            self.plot(x, y + _, inverted, margin=margin)
