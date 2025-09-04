from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout

if TYPE_CHECKING:
    from typing import Iterable, Sequence

    from back.agent import AbstractAISnakeAgent, AbstractSnakeAgent
    from back.type_hints import Position
    from back.world import SnakeWorld
    from front.type_hints import ColorValue, Coordinate
    from kivy.uix.widget import Widget


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

    instr_arena: InstructionGroup
    instr_objs: InstructionGroup
    world: SnakeWorld
    ai_snakes: Sequence[AbstractAISnakeAgent]
    world_colors: WorldColors
    snake_colors: dict[int, SnakeColors]

    def on_kv_post(self, base_widget: Widget) -> None:
        self.instr_arena = InstructionGroup()
        self.instr_objs = InstructionGroup()
        self.canvas.add(self.instr_arena)
        self.canvas.add(self.instr_objs)

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
        self.draw_arena()

    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + pos[0] * self.square_size,
            self.y + (self.world.get_height() - 1 - pos[1]) * self.square_size
        )

    def draw_square(self, x: float, y: float, c: ColorValue) -> None:
        self.instr_objs.add(Color(*c))
        self.instr_objs.add(Rectangle(pos=(x, y), size=(self.square_size, self.square_size)))

    def draw_circle(self, x: float, y: float, c: ColorValue) -> None:
        self.instr_objs.add(Color(*c))
        self.instr_objs.add(Ellipse(pos=(x, y), size=(self.square_size, self.square_size)))

    def draw_arena(self) -> None:
        self.instr_arena.clear()
        h, w = self.world.get_height(), self.world.get_width()

        # background
        self.instr_arena.add(Color(*self.world_colors.background))
        self.instr_arena.add(Rectangle(pos=self.pos, size=(w*self.square_size, h*self.square_size)))

        # grid lines every 3 cells
        self.instr_arena.add(Color(*self.world_colors.gridline))
        for u in range(3, w, 3):
            x = self.x + u*self.square_size
            y0 = self.y
            y1 = self.y + h*self.square_size
            self.instr_arena.add(Line(points=(x, y0, x, y1)))
        for v in range(3, h, 3):
            y = self.y + (h-v)*self.square_size
            x0 = self.x
            x1 = self.x + w*self.square_size
            self.instr_arena.add(Line(points=(x0, y, x1, y)))

        # grid border
        self.instr_arena.add(Color(*self.world_colors.gridborder))
        self.instr_arena.add(Line(points=(
            self.x, self.y,
            self.x + w*self.square_size, self.y
        )))
        self.instr_arena.add(Line(points=(
            self.x, self.y + h*self.square_size,
            self.x + w*self.square_size, self.y + h*self.square_size
        )))
        self.instr_arena.add(Line(points=(
            self.x, self.y,
            self.x, self.y + h*self.square_size
        )))
        self.instr_arena.add(Line(points=(
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
        self.draw_arena()
        self.update_draw()

    def update_draw(
        self,
        dead_snakes: Iterable[AbstractSnakeAgent]=(),
        ai_explanations: bool=False
    ) -> None:
        self.instr_objs.clear()
        if ai_explanations:
            self.draw_ai_inspection()
        self.draw_alive_snakes()
        self.draw_food()
        self.draw_killed_snakes(dead_snakes)


class FoodDrawer:
    def __init__(
        self,
        world_display: WorldDisplay,
        colors: WorldColors
    ) -> None:
        self.colors = colors
        self.display = world_display
        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)

        self.foods: dict[int, Ellipse] = {}

    def reset(self) -> None:
        self.instr.clear()
        for pos in self.foods.keys():
            self.draw_food(pos)

    def draw_food(self, pos: Position) -> None:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        self.instr.add(Color(*self.colors.food))
        circle = Ellipse(pos=(x, y), size=(s, s))
        self.instr.add(circle)
        self.foods[pos] = circle

    def remove_food(self, pos: Position) -> None:
        circle = self.foods.pop(pos)
        self.instr.remove(circle)


class SnakeDrawer:
    def __init__(
        self,
        world_display: WorldDisplay,
        colors: SnakeColors
    ) -> None:
        self.colors = colors
        self.display = world_display
        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)

        self.head_square: Rectangle = None
        self.tail_squares: deque[Rectangle] = deque()

        self.head_pos: Position = None
        self.tail_pos: deque[Position] = deque()

    def _square(self, pos: Position) -> Rectangle:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        return Rectangle(pos=(x, y), size=(s, s))

    def reset(self, cells: Iterable[Position]) -> None:
        self.instr.clear()
        self.tail_squares.clear()
        self.tail_pos.clear()

        # draws the head
        cells = iter(cells)
        self.head_pos = next(cells)
        self.head_square = self._square(self.head_pos)
        self.instr.add(Color(*self.colors.head))
        self.instr.add(self.head_square)

        # draws the tail
        self.instr.add(Color(*self.colors.tail))
        for pos in cells:
            sqr = self._square(pos)
            self.tail_squares.appendleft(sqr)
            self.tail_pos.appendleft(pos)
            self.instr.add(sqr)

    # TODO: snake death
    def update_draw(self, new_head_pos: Position, growth: int, death: bool) -> None:
        # creates a tail square at the previous position of the head
        sqr = self._square(self.head_pos)
        self.tail_pos.append(self.head_pos)
        self.tail_squares.append(sqr)
        self.instr.add(Color(*self.colors.tail))
        self.instr.add(sqr)

        # removes the previous head square
        self.head_pos = new_head_pos
        self.instr.remove(self.head_square)

        # creates the head square at the new position of the head
        self.head_square = self._square(self.head_pos)
        self.instr.add(Color(*self.colors.head))
        self.instr.add(self.head_square)

        if growth <= 0:  # TODO: handle case where growth >= 2 i.e the snake grows of multiple cells at the same time
            # removes squares at the end of the tail
            for _ in range(1-growth):
                sqr = self.tail_squares.popleft()
                self.instr.remove(sqr)
                self.tail_pos.popleft()
