from __future__ import annotations

from kivy.graphics import Rectangle, Color, Line, Ellipse, InstructionGroup
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget

from dataclasses import dataclass

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from back.world import SnakeWorld
    from back.agent import AbstractSnakeAgent, AbstractAISnakeAgent

    from typing import Sequence, Iterable
    from back.type_hints import Position
    from front.type_hints import ColorValue, Coordinate


@dataclass
class WorldColors:
    food_outline: ColorValue
    food: ColorValue
    background: ColorValue
    gridline: ColorValue
    gridborder: ColorValue


@dataclass
class SnakeColors:
    head: ColorValue
    tail: ColorValue
    dead: ColorValue
    inspect: ColorValue


class WorldDisplay(FloatLayout):
    square_size = NumericProperty(0.)

    draw_instr: InstructionGroup
    world: SnakeWorld
    ai_snakes: Sequence[AbstractAISnakeAgent]
    world_colors: WorldColors
    snake_colors: dict[int, SnakeColors]

    def on_kv_post(self, base_widget: Widget) -> None:
        self.draw_instr = InstructionGroup()
        self.canvas.add(self.draw_instr)

    def init_logic(
        self,
        world: SnakeWorld,
        ai_snakes: Sequence[AbstractAISnakeAgent],
        world_colors: WorldColors,
        snake_colors: dict[int, SnakeColors]
    ) -> None:
        self.world = world
        self.ai_snakes = ai_snakes
        self.world_colors = world_colors
        self.snake_colors = snake_colors

    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + pos[0] * self.square_size,
            self.y + (self.world.get_height() - 1 - pos[1]) * self.square_size
        )

    def draw_square(self, x: float, y: float, c: ColorValue) -> None:
        self.draw_instr.add(Color(*c))
        self.draw_instr.add(Rectangle(pos=(x, y), size=(self.square_size, self.square_size)))

    def draw_circle(self, x: float, y: float, c: ColorValue) -> None:
        self.draw_instr.add(Color(*c))
        self.draw_instr.add(Ellipse(pos=(x, y), size=(self.square_size, self.square_size)))

    def draw_world(self) -> None:
        h, w = self.world.get_height(), self.world.get_width()

        # background
        self.draw_instr.add(Color(*self.world_colors.background))
        self.draw_instr.add(Rectangle(pos=self.pos, size=(w*self.square_size, h*self.square_size)))

        # grid lines every 3 cells
        self.draw_instr.add(Color(*self.world_colors.gridline))
        for u in range(3, w, 3):
            x = self.x + u*self.square_size
            y0 = self.y
            y1 = self.y + h*self.square_size
            self.draw_instr.add(Line(points=(x, y0, x, y1)))
        for v in range(3, h, 3):
            y = self.y + (h-v)*self.square_size
            x0 = self.x
            x1 = self.x + w*self.square_size
            self.draw_instr.add(Line(points=(x0, y, x1, y)))

        # grid border
        self.draw_instr.add(Color(*self.world_colors.gridborder))
        self.draw_instr.add(Line(points=(
            self.x, self.y,
            self.x + w*self.square_size, self.y
        )))
        self.draw_instr.add(Line(points=(
            self.x, self.y + h*self.square_size,
            self.x + w*self.square_size, self.y + h*self.square_size
        )))
        self.draw_instr.add(Line(points=(
            self.x, self.y,
            self.x, self.y + h*self.square_size
        )))
        self.draw_instr.add(Line(points=(
            self.x + w*self.square_size, self.y,
            self.x + w*self.square_size, self.y + h*self.square_size
        )))

    def draw_ai_inspection(self) -> None:
        for snake in self.ai_snakes:
            color = self.snake_colors[snake.get_id()].inspect
            for pos in snake.inspect():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, color)

    def draw_alive_snakes(self) -> None:
        for snake in self.world.iter_alive_agents():
            colors = self.snake_colors[snake.get_id()]
            cells = list(snake.iter_cells())
            for i, pos in enumerate(cells):
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, colors.head if i == 0 else colors.tail)

    def draw_food(self) -> None:
        for food in self.world.iter_food():
            x, y = self.pos_to_coord(food)
            self.draw_circle(x, y, self.world_colors.food)

    def draw_killed_snakes(self, dead_snakes: Iterable[AbstractSnakeAgent]) -> None:
        for snake in dead_snakes:
            color = self.snake_colors[snake.get_id()].dead
            for pos in snake.iter_cells():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, color)

    def recompute_square_size(self) -> None:
        self.square_size = min(
            self.height / self.world.get_height(),
            self.width / self.world.get_width()
        )

    def on_square_size(self, instance: Widget, value: float) -> None:
        self.draw()

    def draw(
        self,
        dead_snakes: Iterable[AbstractSnakeAgent]=(),
        ai_explanations: bool=False
    ) -> None:
        self.draw_instr.clear()
        self.draw_world()
        if ai_explanations:
            self.draw_ai_inspection()
        self.draw_alive_snakes()
        self.draw_food()
        self.draw_killed_snakes(dead_snakes)
