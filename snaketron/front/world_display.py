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

    from back.agents import AbstractSnakeAgent, AbstractAISnakeAgent
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
    ai_explanations: bool

    arena_drawer: ArenaDrawer
    ai_inspection_drawers: list[AiInspectionDrawer]
    food_draw_updater: FoodDrawUpdater
    snake_draw_updaters: dict[int, SnakeDrawUpdater]
    snake_updates: dict[int, AgentUpdated]

    world_colors: WorldColors
    snake_colors: SnakeColors

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
        self.ai_explanations = False

        self.arena_drawer = ArenaDrawer(self, world, world_colors)

        self.ai_inspection_drawers = []
        for snake in ai_snakes:
            self.ai_inspection_drawers.append(AiInspectionDrawer(
                self, snake, snake_colors[snake.get_id()]
            ))

        self.food_draw_updater = FoodDrawUpdater(self, world_colors)

        self.snake_updates = {}
        self.snake_draw_updaters = {}
        for snake in itertools.chain(world.iter_alive_agents(), world.iter_dead_agents()):
            snake_id = snake.get_id()
            self.snake_draw_updaters[snake_id] = SnakeDrawUpdater(
                self, snake, snake_colors[snake_id], n_decay_steps=4
            )

        self.world_colors = world_colors
        self.snake_colors = snake_colors
        self.arena_drawer.erase_and_draw()

    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + pos[0] * self.square_size,
            self.y + (self.world.get_height() - 1 - pos[1]) * self.square_size
        )

    def recompute_square_size(self) -> None:
        self.square_size = min(
            self.height / self.world.get_height(),
            self.width / self.world.get_width()
        )

    def on_square_size(self, instance: Widget, value: float) -> None:
        self.arena_drawer.erase_and_draw()

        if self.ai_explanations:
            for ai_inspection_drawer in self.ai_inspection_drawers:
                ai_inspection_drawer.erase_and_draw()

        self.food_draw_updater.reset()
        for snake_draw_updater in self.snake_draw_updaters.values():
            snake_draw_updater.reset()

    def toggle_ai_explanations(self) -> None:
        self.ai_explanations = not self.ai_explanations
        if self.ai_explanations:
            self.update_draw()
        else:
            for ai_inspection_drawer in self.ai_inspection_drawers:
                ai_inspection_drawer.erase()


    def _draw_arena_events(self) -> None:
        for event in self.event_receiver.recv_arena_events():
            if isinstance(event, FoodCreated):
                self.food_draw_updater.draw_food(event)
            elif isinstance(event, FoodConsumed):
                self.food_draw_updater.erase_food(event)

    def _draw_agent_events(self) -> None:
        for snake_id, event in self.event_receiver.recv_agent_events():
            if isinstance(event, AgentUpdated):
                self.snake_updates[snake_id] = event

        for snake in itertools.chain(
            self.world.iter_alive_agents(),
            self.world.iter_dead_agents()
        ):
            snake_id = snake.get_id()
            event = self.snake_updates.pop(snake_id, None)
            self.snake_draw_updaters[snake_id].update_draw(event)

    def update_draw(self) -> None:
        if self.ai_explanations:
            for ai_inspection_drawer in self.ai_inspection_drawers:
                ai_inspection_drawer.erase_and_draw()

        self._draw_arena_events()
        self._draw_agent_events()


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


class ArenaDrawer:
    def __init__(
        self,
        world_display: WorldDisplay,
        world: SnakeWorld,
        colors: WorldColors
    ) -> None:
        self.display = world_display
        self.world = world

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.color_values = colors

    def erase_and_draw(self) -> None:
        self.instr.clear()
        h, w = self.world.get_height(), self.world.get_width()
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


class SnakeDrawUpdater:
    def __init__(
        self,
        world_display: WorldDisplay,
        snake: AbstractSnakeAgent,
        colors: SnakeColors,
        n_decay_steps: int
    ) -> None:
        self.display = world_display
        self.snake = snake

        self.color_values = colors
        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)

        # snake state
        self.alive = snake.is_alive()

        # head of the snake
        self.head_square: Rectangle = None
        self.head_pos: Position = None
        self.head_color = Color(*colors.head)

        # tail of the snake [end of tail, ..., 1 square before head]
        self.tail_squares: deque[Rectangle] = deque()
        self.tail_pos: deque[Position] = deque()
        self.tail_color = Color(*colors.tail)

        # decay animation at the snake death
        self.n_decay_steps = n_decay_steps
        self.decay_step = -1
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
        decay_in_progress = (0 <= self.decay_step < self.n_decay_steps)
        if decay_in_progress:
            self.head_color.rgb = self.head_decay_rgb_grad[self.decay_step]
            self.tail_color.rgb = self.tail_decay_rgb_grad[self.decay_step]
        else:
            self.head_color.rgb = self.color_values.head
            self.tail_color.rgb = self.color_values.tail

        self.instr.clear()
        self.tail_squares.clear()
        self.tail_pos.clear()

        if self.alive or decay_in_progress:
            # draws the head
            cells = self.snake.iter_cells()
            self.head_pos = next(cells)
            self.head_square = self._square(self.head_pos)
            self.instr.add(self.head_color)
            self.instr.add(self.head_square)

            # draws the tail
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

    def _init_decay(self, decay_step: int) -> None:
        self.decay_step = decay_step
        self.head_color.rgb = self.head_decay_rgb_grad[decay_step]
        self.tail_color.rgb = self.tail_decay_rgb_grad[decay_step]

    def _decay(self) -> None:
        # do not decay
        if self.decay_step < 0:
            return

        # decay in progress
        if self.decay_step < self.n_decay_steps:
            self.head_color.rgb = self.head_decay_rgb_grad[self.decay_step]
            self.tail_color.rgb = self.tail_decay_rgb_grad[self.decay_step]
            self.decay_step += 1

        # decay over: snake disappear
        else:
            self.decay_step = -1
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
                self._init_decay(0)
                self._decay()

            # snake respawns
            elif not self.alive:
                self.alive = True
                self.reset()

            # snake moves and potentialy grows or shrinks
            else:
                self._move_snake(event.new_head_pos, event.growth)
