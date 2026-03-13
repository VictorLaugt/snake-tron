from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import numpy as np
import itertools
from typing import TYPE_CHECKING

from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout

from back.events import FoodCreated, FoodConsumed, AgentUpdated

if TYPE_CHECKING:
    from typing import Sequence, Optional

    from back.agent import AbstractAISnakeAgent, AbstractSnakeAgent
    from back.events import EventReceiver
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
    head_decay_first: ColorValue
    head_decay_final: ColorValue
    tail_decay_first: ColorValue
    tail_decay_final: ColorValue
    inspect: ColorValue


class WorldDisplay(FloatLayout):
    square_size = NumericProperty(0.)

    event_receiver: EventReceiver
    world: SnakeWorld
    ai_snakes: Sequence[AbstractAISnakeAgent]
    ai_explanations: bool

    instr_arena: InstructionGroup
    food_drawer: FoodDrawer
    snake_drawers: dict[int, SnakeDrawer]
    snake_updates: dict[int, AgentUpdated]

    world_colors: WorldColors
    snake_colors: SnakeColors

    def on_kv_post(self, base_widget: Widget) -> None:
        self.instr_arena = InstructionGroup()
        self.canvas.add(self.instr_arena)

    def init_logic(
        self,
        event_receiver: EventReceiver,
        world: SnakeWorld,
        ai_snakes: Sequence[AbstractAISnakeAgent],
        world_colors: WorldColors,
        snake_colors: dict[int, SnakeColors]
    ) -> None:
        self.event_receiver = event_receiver
        self.world = world
        self.ai_snakes = ai_snakes
        self.ai_explanations = False

        self.food_drawer = FoodDrawer(self, world_colors)
        self.snake_updates = {}
        self.snake_drawers = {}
        for snake in itertools.chain(world.iter_alive_agents(), world.iter_dead_agents()):
            snake_id = snake.get_id()
            self.snake_drawers[snake_id] = SnakeDrawer(
                self, snake, snake_colors[snake_id], n_decay_steps=4
            )

        self.world_colors = world_colors
        self.snake_colors = snake_colors
        self.draw_arena()

    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + pos[0] * self.square_size,
            self.y + (self.world.get_height() - 1 - pos[1]) * self.square_size
        )

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

    def toggle_ai_explanations(self) -> None:
        self.ai_explanations = not self.ai_explanations

    def recompute_square_size(self) -> None:
        self.square_size = min(
            self.height / self.world.get_height(),
            self.width / self.world.get_width()
        )

    def on_square_size(self, instance: Widget, value: float) -> None:
        self.draw_arena()
        self.food_drawer.reset()
        for snake_drawer in self.snake_drawers.values():
            snake_drawer.reset()

    def update_draw(self) -> None:
        for event in self.event_receiver.recv_arena_events():
            if isinstance(event, FoodCreated):
                self.food_drawer.draw_food(event)
            elif isinstance(event, FoodConsumed):
                self.food_drawer.remove_food(event)

        for snake_id, event in self.event_receiver.recv_agent_events():
            if isinstance(event, AgentUpdated):
                self.snake_updates[snake_id] = event

        for snake in itertools.chain(
            self.world.iter_alive_agents(),
            self.world.iter_dead_agents()
        ):
            snake_id = snake.get_id()
            event = self.snake_updates.pop(snake_id, None)
            self.snake_drawers[snake_id].update_draw(event)


class FoodDrawer:
    def __init__(
        self,
        world_display: WorldDisplay,
        colors: WorldColors
    ) -> None:
        self.display = world_display
        self.instr = InstructionGroup()
        self.food_color = Color(*colors.food)

        self.display.canvas.add(self.instr)
        self.instr.add(self.food_color)

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

    def remove_food(self, event: FoodConsumed) -> None:
        circle = self.foods.pop(event.pos)
        self.instr.remove(circle)


class SnakeDrawer:
    def __init__(
        self,
        world_display: WorldDisplay,
        snake: AbstractSnakeAgent,
        colors: SnakeColors,
        n_decay_steps: int
    ) -> None:
        self.display = world_display
        self.snake = snake

        self.colors = colors
        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)

        # snake state
        self.alive = snake.is_alive()

        # head of the snake
        self.head_square: Rectangle = None
        self.head_pos: Position = None
        self.head_color = Color(colors.head)

        # tail of the snake [end of tail, ..., 1 square before head]
        self.tail_squares: deque[Rectangle] = deque()
        self.tail_pos: deque[Position] = deque()
        self.tail_color = Color(colors.tail)

        # decay animation at the snake death
        self.n_decay_steps = n_decay_steps
        self.decay_step = 0
        self.head_decay_rgb_grad = np.linspace(
            colors.head_decay_first, colors.head_decay_final, n_decay_steps
        )
        self.tail_decay_rgb_grad = np.linspace(
            colors.tail_decay_first, colors.tail_decay_final, n_decay_steps
        )


    def _square(self, pos: Position) -> Rectangle:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        return Rectangle(pos=(x, y), size=(s, s))

    def reset(self) -> None:
        self.instr.clear()
        self.tail_squares.clear()
        self.tail_pos.clear()

        # draws the head
        cells = self.snake.iter_cells()
        self.head_pos = next(cells)
        self.head_square = self._square(self.head_pos)
        self.head_color.rgb = self.colors.head
        self.instr.add(self.head_color)
        self.instr.add(self.head_square)

        # draws the tail
        self.tail_color.rgb = self.colors.tail
        self.instr.add(self.tail_color)
        for pos in cells:
            sqr = self._square(pos)
            self.tail_squares.appendleft(sqr)
            self.tail_pos.appendleft(pos)
            self.instr.add(sqr)

    def _move_snake(self, new_head_pos: Position, growth: int) -> None:
        # creates a tail square at the previous position of the head
        sqr = self._square(self.head_pos)
        self.tail_pos.append(self.head_pos)
        self.tail_squares.append(sqr)
        self.instr.add(self.tail_color)
        self.instr.add(sqr)

        # removes the previous head square
        self.head_pos = new_head_pos
        self.instr.remove(self.head_square)

        # creates the head square at the new position of the head
        self.head_square = self._square(self.head_pos)
        self.instr.add(self.head_color)
        self.instr.add(self.head_square)

        if growth <= 0:
            # removes squares at the end of the tail
            for _ in range(1-growth):
                sqr = self.tail_squares.popleft()
                self.instr.remove(sqr)
                self.tail_pos.popleft()

        elif growth >= 2:
            # adds squares at the end of the tail
            for _ in range(growth-1):
                pos = self.tail_pos[0]
                self.tail_pos.appendleft(pos)
                sqr = self._square(pos)
                self.tail_squares.appendleft(sqr)
                self.instr.add(self.tail_color)
                self.instr.add(sqr)

    def _init_decay(self) -> None:
        self.decay_step = 0
        self.head_color.rgb = self.head_decay_rgb_grad[0]
        self.tail_color.rgb = self.tail_decay_rgb_grad[0]

    def _decay(self) -> None:
        # decay in progress
        if self.decay_step < self.n_decay_steps:
            self.head_color.rgb = self.head_decay_rgb_grad[self.decay_step]
            self.tail_color.rgb = self.tail_decay_rgb_grad[self.decay_step]
            self.decay_step += 1

        # decay over: snake disappear
        else:
            self.instr.clear()

    def update_draw(self, event: Optional[AgentUpdated]=None) -> None:
        if event is None:
            if not self.alive:
                self._decay()

        else:
            # snake dies
            if event.death:
                self.alive = False
                self._move_snake(event.new_head_pos, event.growth)
                self._init_decay()
                self._decay()

            # snake respawns
            elif not self.alive:
                self.alive = True
                self.reset()

            # snake moves and potentialy grows or shrinks
            else:
                self._move_snake(event.new_head_pos, event.growth)
