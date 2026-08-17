"""
Graphics Handler for pos.

Provides functions for coordinate translation, pixel plotting, screen clearing,
image rendering (blitting) with scaling, and line drawing.

Includes a viewport window system.
"""

from contextlib import contextmanager
from typing import List, Optional, Tuple

from posetem.pos import POS


class GraphicsHandler:
    """
    Utility handler for performing graphics and drawing operations on the pos display.
    Supports a viewport origin offset and a clipping window.

    Drawing operations that fall outside the window are silently clipped.
    """

    def __init__(self, pos: POS, origin: Optional[List[int]] = None, margin: int = 0) -> None:
        """
        Initialize the GraphicsHandler with a POS instance and an optional origin offset.

        Args:
            pos: The active POS client connection.
            origin: The [x, y] coordinates representing the viewport origin.
                All drawing operations are relative to this origin. Defaults to [0, 0] if None.
            margin: Uniform margin applied to all four sides of the display.
                Shrinks the usable window inward. Defaults to 0.
        """
        self.pos: POS = pos
        self.origin: List[int] = origin if origin is not None else [0, 0]
        if any(coord < 0 for coord in self.origin):
            raise ValueError("Origin coordinates cannot be negative")
        if self.pos is not None:
            if self.origin[0] >= self.pos.display_width or self.origin[1] >= self.pos.display_height:
                raise ValueError("Origin coordinates must be within display bounds")

        self._window_left: int = 0
        self._window_top: int = 0
        self._window_right: int = self.pos.display_width
        self._window_bottom: int = self.pos.display_height

        if margin > 0:
            self.set_margin(margin)

    def set_window(self, left: int, top: int, right: int, bottom: int) -> None:
        """
        Set a custom clipping window in absolute display coordinates.

        Pixels drawn outside this region are silently clipped.
        The window is **not** rejected if it exceeds the physical display —
        pixels that fall outside the display are simply clipped at draw time.

        Args:
            left:   Left edge X (inclusive).
            top:    Top edge Y (inclusive).
            right:  Right edge X (exclusive, one past last valid column).
            bottom: Bottom edge Y (exclusive, one past last valid row).

        Raises:
            ValueError: If left >= right or top >= bottom.
        """
        if left >= right or top >= bottom:
            raise ValueError("Invalid window: left must be < right and top must be < bottom")
        self._window_left = left
        self._window_top = top
        self._window_right = right
        self._window_bottom = bottom

    def set_margin(self, margin: int) -> None:
        """
        Set the window by applying a uniform margin from all four sides of the display.

        Args:
            margin: Number of pixels to inset from each edge.

        Raises:
            ValueError: If the margin is too large for the display.
        """
        if margin < 0:
            raise ValueError("Margin cannot be negative")
        left = margin
        top = margin
        right = self.pos.display_width - margin
        bottom = self.pos.display_height - margin
        if left >= right or top >= bottom:
            raise ValueError("Margin too large for the display dimensions")
        self.set_window(left, top, right, bottom)

    @property
    def window(self) -> Tuple[int, int, int, int]:
        """
        The current clipping window as (left, top, right, bottom) in absolute display coordinates.
        """
        return (self._window_left, self._window_top, self._window_right, self._window_bottom)

    @property
    def window_width(self) -> int:
        """Usable width of the current window in pixels."""
        return self._window_right - self._window_left

    @property
    def window_height(self) -> int:
        """Usable height of the current window in pixels."""
        return self._window_bottom - self._window_top

    @property
    def window_size(self) -> Tuple[int, int]:
        """Usable (width, height) of the current window."""
        return (self.window_width, self.window_height)

    def _clip_point(self, abs_x: int, abs_y: int) -> bool:
        """
        Check whether an absolute display coordinate is inside both the
        window and the physical display.

        Returns:
            True if the point is drawable, False if it should be clipped.
        """
        if abs_x < 0 or abs_y < 0:
            return False
        if abs_x >= self.pos.display_width or abs_y >= self.pos.display_height:
            return False
        if abs_x < self._window_left or abs_x >= self._window_right:
            return False
        if abs_y < self._window_top or abs_y >= self._window_bottom:
            return False
        return True

    def _abs_coords(self, x: int, y: int) -> Tuple[int, int]:
        """Translate local coordinates to absolute display coordinates using origin."""
        return (x + self.origin[0], y + self.origin[1])

    @contextmanager
    def _margin_window(self, margin: int):
        """Temporarily shrink the clipping window by margin on all four sides."""
        if margin == 0:
            yield
            return
        old = (self._window_left, self._window_top, self._window_right, self._window_bottom)
        self._window_left += margin
        self._window_top += margin
        self._window_right -= margin
        self._window_bottom -= margin
        try:
            yield
        finally:
            self._window_left, self._window_top, self._window_right, self._window_bottom = old

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
            margin: Temporary inset from all four sides of the window. Defaults to 0.
        """
        with self._margin_window(margin):
            abs_x, abs_y = self._abs_coords(x + margin, y + margin)
            if not self._clip_point(abs_x, abs_y):
                return
            addr = self.pos.display_width * abs_y + abs_x
            self.pos.dwrite("0" if inverted else "1", start=addr)

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
            margin: Temporary inset from all four sides of the window. Defaults to 0.
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

        if scale > 1:
            lines = list(map(lambda a: "".join(list(map(lambda x: x * scale, a))), lines))
            lines = [x for x in lines for _ in range(scale)]

        if not lines:
            return

        with self._margin_window(margin):
            start_x = cordinates[0] + margin
            start_y = cordinates[1] + margin
            for i, line_str in enumerate(lines):
                if not line_str:
                    continue
                line_y = start_y + i
                abs_y = line_y + self.origin[1]

                if abs_y < 0 or abs_y >= self.pos.display_height:
                    continue
                if abs_y < self._window_top or abs_y >= self._window_bottom:
                    continue

                abs_start_x = start_x + self.origin[0]
                abs_end_x = abs_start_x + len(line_str)

                clip_left = max(abs_start_x, self._window_left, 0)
                clip_right = min(abs_end_x, self._window_right, self.pos.display_width)

                if clip_left >= clip_right:
                    continue

                slice_start = clip_left - abs_start_x
                slice_end = clip_right - abs_start_x
                clipped_line = line_str[slice_start:slice_end]

                addr = self.pos.display_width * abs_y + clip_left
                self.pos.dwrite(clipped_line, start=addr)

    def line(self, x0: int, y0: int, x1: int, y1: int, inverted: bool = False, margin: int = 0) -> None:
        """
        Draw a straight line between two points using Bresenham's Line Algorithm.

        Args:
            x0: Start point X coordinate.
            y0: Start point Y coordinate.
            x1: End point X coordinate.
            y1: End point Y coordinate.
            inverted: If True, draws the line in black (0) instead of white (1).
            margin: Temporary inset from all four sides of the window.
        """
        with self._margin_window(margin):
            x0, y0 = x0 + margin, y0 + margin
            x1, y1 = x1 + margin, y1 + margin
            dx: int = abs(x1 - x0)
            dy: int = abs(y1 - y0)

            step_x: int = 1 if x0 < x1 else -1
            step_y: int = 1 if y0 < y1 else -1

            x, y = x0, y0

            if dx >= dy:
                p: int = 2 * dy - dx
                for _ in range(dx + 1):
                    self.plot(x, y, inverted)
                    if p >= 0:
                        y += step_y
                        p -= 2 * dx
                    p += 2 * dy
                    x += step_x
            else:
                p = 2 * dx - dy
                for _ in range(dy + 1):
                    self.plot(x, y, inverted)
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
            margin: Temporary inset from all four sides of the window.
        """
        with self._margin_window(margin):
            for _ in range(length):
                self.plot(x + margin + _, y + margin, inverted)

    def lineV(self, x: int, y: int, length: int, inverted: bool = False, margin: int = 0) -> None:
        """
        Draw a vertical line of a given length.

        Args:
            x: Starting X coordinate.
            y: Starting Y coordinate.
            length: Length of the line in pixels.
            inverted: If True, draws the line in black (0).
            margin: Temporary inset from all four sides of the window.
        """
        with self._margin_window(margin):
            for _ in range(length):
                self.plot(x + margin, y + margin + _, inverted)
