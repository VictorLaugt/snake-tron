from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.graphics import Color, InstructionGroup, Line, Rectangle

from debug_tool import dbg

if TYPE_CHECKING:
    from front.world_display.world_display import WorldColors, WorldDisplay

__all__ = ['ArenaDrawer']


class ArenaDrawer:
    def __init__(self, world_display: WorldDisplay, colors: WorldColors) -> None:
        self.display = world_display
        self.arena_width = 1
        self.arena_height = 1

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.color_values = colors

    def get_width(self) -> int:
        return self.arena_width

    def get_height(self) -> int:
        return self.arena_height

    @dbg.trackmethod()
    def update_size(self, width: int, height: int) -> None:
        self.arena_width = width
        self.arena_height = height
        self.erase_and_draw()

    @dbg.trackmethod()
    def erase_and_draw(self) -> None:
        self.instr.clear()
        h, w = self.arena_height, self.arena_width
        display_x, display_y = self.display.pos
        display_s = self.display.square_size

        # background
        self.instr.add(Color(*self.color_values.background))
        self.instr.add(Rectangle(pos=(display_x, display_y), size=(w*display_s, h*display_s)))

        # grid lines every 3 cells
        self.instr.add(Color(*self.color_values.gridline))
        for u in range(3, w, 3):
            x = display_x + u*display_s
            y0 = display_y
            y1 = display_y + h*display_s
            self.instr.add(Line(points=(x, y0, x, y1)))
        for v in range(3, h, 3):
            y = display_y + (h-v)*display_s
            x0 = display_x
            x1 = display_x + w*display_s
            self.instr.add(Line(points=(x0, y, x1, y)))

        # grid border
        self.instr.add(Color(*self.color_values.gridborder))
        self.instr.add(Line(points=(
            display_x, display_y,
            display_x + w*display_s, display_y
        )))
        self.instr.add(Line(points=(
            display_x, display_y + h*display_s,
            display_x + w*display_s, display_y + h*display_s
        )))
        self.instr.add(Line(points=(
            display_x, display_y,
            display_x, display_y + h*display_s
        )))
        self.instr.add(Line(points=(
            display_x + w*display_s, display_y,
            display_x + w*display_s, display_y + h*display_s
        )))
