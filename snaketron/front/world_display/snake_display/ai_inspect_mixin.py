from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.graphics import Color, InstructionGroup, Rectangle

from snaketron.events.back2front_protocol import AiSnakeInspection
from snaketron.front.world_display.snake_display.base_snake_draw_updater import BaseSnakeDrawUpdater

if TYPE_CHECKING:
    from typing import Iterable, Optional

    from snaketron.back.type_hints import Direction, Position

__all__ = ['AiInspectMixin']


class AiInspectMixin(BaseSnakeDrawUpdater):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.ai_inspection_instr = InstructionGroup()
        self.get_graphical_elements().add(self.ai_inspection_instr)


    # ---- public methods overloaded from base class
    def erase(self) -> None:
        self.erase_ai_inspection()
        super().erase()

    def reset(
        self,
        cell_pos: Optional[Iterable[Position]]=None,
        head_dir: Optional[Direction]=None
    ) -> None:
        super().reset(cell_pos, head_dir)


    # ---- public methods implemented by this mixin
    def erase_ai_inspection(self) -> None:
        self.ai_inspection_instr.clear()

    def update_draw_ai_inspection(self, event: AiSnakeInspection) -> None:
        self.erase_ai_inspection()
        self.ai_inspection_instr.add(Color(*self.get_colors().inspect))
        s = self.get_draw_tool().get_square_size()
        for pos in event.inspection:
            x, y = self.get_draw_tool().pos_to_coord(pos)
            self.ai_inspection_instr.add(Rectangle(pos=(x, y), size=(s, s)))
