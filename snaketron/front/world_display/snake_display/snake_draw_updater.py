from __future__ import annotations

from typing import TYPE_CHECKING

from front.colors import SnakeColors
from front.world_display.snake_display.ai_inspect_mixin import AiInspectMixin
from front.world_display.snake_display.snake_draw_mixin import SnakeDrawMixin

if TYPE_CHECKING:
    from typing import Callable

    from back.type_hints import Position
    from front.type_hints import Coordinate

__all__ = ['SnakeDrawUpdater', 'SnakeDrawTool']


class SnakeDrawTool:
    def __init__(
        self,
        pos_to_coord: Callable[[Position], Coordinate],
        get_square_size: Callable[[], float],
    ) -> None:
        self.pos_to_coord = pos_to_coord
        self.get_square_size = get_square_size


class SnakeDrawUpdater(SnakeDrawMixin, AiInspectMixin):
    def __init__(
        self, *,
        draw_tool: SnakeDrawTool,
        colors: SnakeColors,
        n_decay_steps: int
    ) -> None:
        super().__init__(draw_tool=draw_tool, colors=colors, n_decay_steps=n_decay_steps)
