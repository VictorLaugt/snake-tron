from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.graphics import InstructionGroup, Color, Ellipse

if TYPE_CHECKING:
    from front.world_display import WorldDisplay, WorldColors

    from back.events import FoodCreated, FoodConsumed
    from back.type_hints import Position


class FoodDrawUpdater:
    def __init__(
        self,
        world_display: WorldDisplay,
        colors: WorldColors
    ) -> None:
        self.display = world_display

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.food_color = Color(*colors.food)

        self.foods: dict[Position, Ellipse] = {}


    def _circle(self, pos: Position) -> None:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        return Ellipse(pos=(x, y), size=(s, s))

    def reset(self) -> None:
        self.instr.clear()
        self.instr.add(self.food_color)
        for pos in self.foods.keys():
            circle = self._circle(pos)
            self.instr.add(circle)
            self.foods[pos] = circle

    def draw_food(self, event: FoodCreated) -> None:
        circle = self._circle(event.pos)
        self.instr.add(circle)
        self.foods[event.pos] = circle

    def erase_food(self, event: FoodConsumed) -> None:
        circle = self.foods.pop(event.pos)
        self.instr.remove(circle)
