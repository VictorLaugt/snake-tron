from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from kivy.graphics import Color, InstructionGroup, Line

if TYPE_CHECKING:
    from typing import Callable, Sequence

    from snaketron.back.type_hints import Direction
    from snaketron.front.colors import SnakeColors


__all__ = ['ArrowDrawerTool', 'ArrowDrawer']


class ArrowDrawerTool:
    def __init__(
        self,
        get_widget_center: Callable[[], tuple[float, float]],
        get_widget_size: Callable[[], tuple[float, float]]
    ) -> None:
        self.get_widget_center = get_widget_center
        self.get_widget_size = get_widget_size


class ArrowDrawer:
    def __init__(self, draw_tool: ArrowDrawerTool, colors: SnakeColors) -> None:
        self.draw_tool = draw_tool
        self.colors = colors
        self.graphical_elements = InstructionGroup()

        self.arrow_builder = NormalizedLine()
        self.directions: deque[Direction] = deque()

    def get_graphical_elements(self) -> InstructionGroup:
        return self.graphical_elements

    def n_segments(self) -> int:
        return len(self.directions)

    def get_segment(self, index: int) -> Direction:
        return self.directions[index]

    def draw_arrow(self) -> None:
        widget_width, widget_height = self.draw_tool.get_widget_size()
        self.arrow_builder.normalize(.6*widget_width, .6*widget_height)

        widget_center_x, widget_center_y = self.draw_tool.get_widget_center()
        arrowline = self.arrow_builder.arrowline(widget_center_x, widget_center_y)
        arrowhead = self.arrow_builder.arrowhead(widget_center_x, widget_center_y)

        self.graphical_elements.clear()
        self.graphical_elements.add(Color(rgba=self.colors.tail))
        self.graphical_elements.add(Line(points=arrowline, width=2, cap='round', joint='round'))
        self.graphical_elements.add(Line(points=arrowhead, width=2, cap='round', joint='round'))

    def add_new_segment(self, d: Direction) -> None:
        self.directions.append(d)
        self.arrow_builder.add_new_point(d[0], -d[1])
        self.draw_arrow()

    def pop_first_segment(self) -> Direction:
        d = self.directions.popleft()
        self.arrow_builder.remove_first_point()
        self.draw_arrow()
        return d

    def erase_all_segments(self) -> None:
        self.directions.clear()
        self.arrow_builder.clear()
        self.graphical_elements.clear()


class NormalizedLine:
    def __init__(self) -> None:
        # invariant: len(self.x) > 0 and len(self.x) == len(self.y)
        self.x: deque[float] = deque()
        self.y: deque[float] = deque()
        self.x.append(0.)
        self.y.append(0.)
        self.dx: float = 0.
        self.dy: float = 0.
        self.factor: float = 1.

    def add_new_point(self, direction_x: float, direction_y: float) -> None:
        self.dx = direction_x
        self.dy = direction_y
        self.x.append(self.x[-1] + direction_x)
        self.y.append(self.y[-1] + direction_y)

    def remove_first_point(self) -> None:
        self.x.popleft()
        self.y.popleft()

    def clear(self) -> None:
        self.x.clear()
        self.y.clear()
        self.x.append(0.)
        self.y.append(0.)

    def normalize(self, box_width: float, box_height: float) -> None:
        n = len(self.x)
        x_mean = sum(self.x) / n
        y_mean = sum(self.y) / n

        x_abs_max = 0.
        y_abs_max = 0.
        for i in range(n):
            self.x[i] -= x_mean
            self.y[i] -= y_mean

            x_abs_max = max(abs(self.x[i]), x_abs_max)
            y_abs_max = max(abs(self.y[i]), y_abs_max)

        if (max_abs := max(x_abs_max, y_abs_max)) > 0:
            self.factor = .5 * min(box_width, box_height) / max_abs

    def arrowline(self, center_x: float, center_y: float) -> Sequence[float]:
        n = len(self.x)
        arrowline = []
        for i in range(n):
            arrowline.append(self.x[i]*self.factor + center_x)
            arrowline.append(self.y[i]*self.factor + center_y)

        return arrowline

    def arrowhead(self, center_x: float, center_y: float) -> Sequence[float]:
        x, y = self.x[-1]*self.factor, self.y[-1]*self.factor
        dx, dy = self.dx*self.factor, self.dy*self.factor

        vx, vy = x+center_x, y+center_y
        ux, uy = vx-0.25*(dx+dy), vy-0.25*(dy-dx)
        wx, wy = vx-0.25*(dx-dy), vy-0.25*(dy+dx)

        return (ux,uy, vx,vy, wx,wy)
