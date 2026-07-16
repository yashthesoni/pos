"""
This is the Graphics Handler for pos
It has basic functions such as cord, plot, clear, image, and drawline.
Refer to documentation at docs/Utilities/graphics.md
"""

from posetem.pos import POS


class GraphicsHandler:
    def __init__(self, pos: POS, origin=[0, 0]) -> None:
        self.origin = origin
        self.pos = pos

    def cord(self, x: int = 1, y: int = 1) -> int:
        return self.pos.display_width * (y + self.origin[1]) + x + self.origin[0]

    def plot(self, x: int = 1, y: int = 1, inverted: bool = False) -> None:
        self.pos.dwrite("0" if inverted else "1", start=self.cord(x, y))

    def clear(self) -> None:
        self.pos.dwrite("0" * (self.pos.display_width * self.pos.display_height))

    def image(
        self,
        array: str,
        line_length: int,
        cordinates: list = [0, 0],
        margin: int = 0,
        scale: int = 1,
        transparent: bool = False,
        inverted: bool = False,
    ) -> None:

        array = array.replace(" ", "")

        if inverted:
            _table = str.maketrans("01", "10")
            array = array.translate(_table)
        if transparent:
            array = array.replace("0", "2")

        lines = [array[i : i + line_length] for i in range(0, len(array), line_length)]

        lines = list(map(lambda a: "".join(list(map(lambda x: x * scale, a))), lines))
        lines = [x for x in lines for _ in range(scale)]

        st = margin
        point = self.cord(*cordinates)
        for a in lines:
            self.pos.dwrite(a, start=self.pos.display_width * st + point + margin)
            st += 1

    def line(self, x0: int, y0: int, x1: int, y1: int, inverted: bool = False) -> None:

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)

        step_x = 1 if x0 < x1 else -1
        step_y = 1 if y0 < y1 else -1

        x, y = x0, y0

        if dx >= dy:
            p = 2 * dy - dx
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

    def lineH(self, x: int, y: int, length: int, inverted: bool = False) -> None:
        for _ in range(length):
            self.plot(x + _, y, inverted)

    def lineV(self, x: int, y: int, length: int, inverted: bool = False) -> None:
        for _ in range(length):
            self.plot(x, y + _, inverted)
