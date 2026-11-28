from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.event import EventDispatcher
from kivy.graphics import InstructionGroup, Rectangle

if TYPE_CHECKING:
    from typing import Callable, Iterable, Optional

    from snaketron.back.type_hints import Direction, Position
    from snaketron.front.colors import SnakeColors
    from snaketron.front.type_hints import Coordinate

__all__ = ['BaseSnakeDrawUpdater']


class SnakeDrawTool:
    def __init__(
        self,
        pos_to_coord: Callable[[Position], Coordinate],
        get_square_size: Callable[[], float],
    ) -> None:
        self.pos_to_coord = pos_to_coord
        self.get_square_size = get_square_size


class BaseSnakeDrawUpdater(EventDispatcher):
    def __init__(self, draw_tool: SnakeDrawTool, colors: SnakeColors) -> None:
        super().__init__()
        self.draw_tool = draw_tool
        self.colors = colors
        self.graphical_elements = InstructionGroup()

    # ---- protected
    def get_draw_tool(self) -> SnakeDrawTool:
        return self.draw_tool

    def get_colors(self) -> SnakeColors:
        return self.colors

    def square(self, pos: Position) -> Rectangle:
        x, y = self.draw_tool.pos_to_coord(pos)
        s = self.draw_tool.get_square_size()
        return Rectangle(pos=(x, y), size=(s, s))

    # ---- public
    def get_graphical_elements(self) -> InstructionGroup:
        return self.graphical_elements

    def erase(self) -> None:
        pass

    def reset(
        self,
        cell_pos: Optional[Iterable[Position]]=None,
        head_dir: Optional[Direction]=None
    ) -> None:
        pass
