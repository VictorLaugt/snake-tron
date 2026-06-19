from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import itertools
from typing import TYPE_CHECKING

from kivy.graphics import Color, InstructionGroup, Line, Rectangle
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout

from back.events import FoodCreated, FoodConsumed, SnakeSimpleEvent, SnakeMovement, SnakeWrap

from front.pause_menu import PauseMenu
from front.world_display.ai_inspection_drawer import AiInspectionDrawer
from front.world_display.food_draw_updater import FoodDrawUpdater
from front.world_display.snake_draw_updater import SnakeDrawUpdater

if TYPE_CHECKING:
    from typing import Sequence
    from kivy.uix.widget import Widget
    from kivy.input import MotionEvent

    from back.agents import AbstractAISnakeAgent
    from back.events import EventReceiver
    from back.type_hints import Position
    from back.world import SnakeWorld

    from front.type_hints import ColorValue, Coordinate
    from front.window import SnakeTronWindow



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

    world_colors: WorldColors
    snake_colors: SnakeColors

    def init_logic(
        self,
        main_window: SnakeTronWindow,
        event_receiver: EventReceiver,
        world: SnakeWorld,
        ai_snakes: Sequence[AbstractAISnakeAgent],
        world_colors: WorldColors,
        snake_colors: dict[int, SnakeColors]
    ) -> None:
        self.main_window = main_window
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
            self.x + float(pos[0]) * self.square_size,
            self.y + (self.world.get_height() - 1 - float(pos[1])) * self.square_size
        )

    def _recompute_square_size(self) -> None:
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
        for updater in self.snake_draw_updaters.values():
            updater.reset()

    def on_pos(self, instance: Widget, value: tuple[float, float]) -> None:
        self._recompute_square_size()

    def on_size(self, instance: Widget, value: tuple[float, float]) -> None:
        self._recompute_square_size()

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if super().on_touch_down(touch):
            return True

        if self.collide_point(touch.x, touch.y):
            pause_menu = PauseMenu(
                self.main_window,
                size_hint=(None, None),
                size=self.size,
                pos=self.to_window(self.x, self.y)
            )
            self.add_widget(pause_menu)
            pause_menu.request_pause()
            return True

        return False


    def toggle_ai_explanations(self) -> None:
        self.ai_explanations = not self.ai_explanations
        if self.ai_explanations:
            for drawer in self.ai_inspection_drawers:
                drawer.erase_and_draw()

        else:
            for drawer in self.ai_inspection_drawers:
                drawer.erase()

    def ai_explanations_is_enabled(self) -> bool:
        return self.ai_explanations


    def _draw_arena_events(self) -> None:
        for event in self.event_receiver.recv_arena_events():
            if isinstance(event, FoodCreated):
                self.food_draw_updater.draw_food(event)
            elif isinstance(event, FoodConsumed):
                self.food_draw_updater.erase_food(event)

    def _draw_agent_events(self, time_step: float) -> None:
        for snake_id, event in self.event_receiver.recv_agent_events():
            updater = self.snake_draw_updaters[snake_id]
            if isinstance(event, SnakeMovement):
                updater.update_draw_snake_move(event, time_step)
            elif isinstance(event, SnakeWrap):
                ...  # TODO: use the SnakeWrap event to fix the animation when the head or the tail wraps to the other side of the world
            elif event == SnakeSimpleEvent.SPAWN:
                updater.update_draw_spawn()
            elif event == SnakeSimpleEvent.DIE:
                updater.update_draw_die(time_step)
            elif event == SnakeSimpleEvent.DASH:
                NotImplemented  # Gamelpay feature not implemented yet

    def update_draw(self, time_step: float) -> None:
        if self.ai_explanations:
            for ai_inspection_drawer in self.ai_inspection_drawers:
                ai_inspection_drawer.erase_and_draw()

        self._draw_arena_events()
        self._draw_agent_events(time_step)


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
