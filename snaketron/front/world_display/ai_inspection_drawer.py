from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.graphics import InstructionGroup, Color, Rectangle

if TYPE_CHECKING:
    from back.agents import AbstractAISnakeAgent
    from front.world_display import WorldDisplay, SnakeColors


class AiInspectionDrawer:
    def __init__(
        self,
        world_display: WorldDisplay,
        snake: AbstractAISnakeAgent,
        colors: SnakeColors
    ) -> None:
        self.display = world_display
        self.snake = snake

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.color_values = colors

    def erase(self) -> None:
        self.instr.clear()

    def erase_and_draw(self) -> None:
        self.instr.clear()
        self.instr.add(Color(*self.color_values.inspect))
        s = self.display.square_size
        for pos in self.snake.inspect():
            x, y = self.display.pos_to_coord(pos)
            self.instr.add(Rectangle(pos=(x, y), size=(s, s)))
