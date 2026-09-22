from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kivy.graphics import Color, InstructionGroup, Line, Rectangle
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout

from events.back2front_protocol import *
from front.pause_menu import PauseMenuInvoker
from front.world_display.food_draw_updater import FoodDrawUpdater
from front.world_display.snake_draw_updater import SnakeDrawUpdater

if TYPE_CHECKING:
    from kivy.uix.widget import Widget

    from back.type_hints import Position
    from events.back2front_protocol import BackendEvent
    from events.pipe import EventReceiver
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

    event_receiver: EventReceiver[BackendEvent]
    arena_drawer: ArenaDrawer
    food_draw_updater: FoodDrawUpdater
    snake_draw_updaters: dict[int, SnakeDrawUpdater]
    pause_invoker: PauseMenuInvoker

    def init_logic(
        self,
        main_window: SnakeTronWindow,
        event_receiver: EventReceiver[BackendEvent],
        # event_sender: EventSender[FrontendEvent],  # TODO: use the event sender to ask the backend for ai inspection info, and receive them in the event receiver
        world_colors: WorldColors,
        snake_colors: dict[int, SnakeColors],
        pause_command_touch_max_length: float
    ) -> None:
        self.event_receiver = event_receiver

        self.arena_drawer = ArenaDrawer(self, world_colors)
        self.food_draw_updater = FoodDrawUpdater(self, world_colors)

        self.snake_draw_updaters = {}
        for snake_id, snake_color in snake_colors.items():
            self.snake_draw_updaters[snake_id] = SnakeDrawUpdater(
                self, snake_color, n_decay_steps=4
            )

        self.pause_invoker = PauseMenuInvoker(
            main_window, pause_command_touch_max_length,
            size_hint=(None, None), size=self.size,
            pos=self.to_window(self.x, self.y)
        )
        self.add_widget(self.pause_invoker)


    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + float(pos[0]) * self.square_size,
            self.y + (self.arena_drawer.get_height() - 1 - float(pos[1])) * self.square_size
        )

    def _recompute_square_size(self) -> None:
        self.square_size = min(
            self.height / self.arena_drawer.get_height(),
            self.width / self.arena_drawer.get_width()
        )

    def on_square_size(self, instance: Widget, value: float) -> None:
        self.arena_drawer.erase_and_draw()
        self.food_draw_updater.reset()
        for updater in self.snake_draw_updaters.values():
            updater.reset()

        self.pause_invoker.size = self.size
        self.pause_invoker.pos = self.to_window(self.x, self.y)

    def on_pos(self, instance: Widget, value: tuple[float, float]) -> None:
        self._recompute_square_size()

    def on_size(self, instance: Widget, value: tuple[float, float]) -> None:
        self._recompute_square_size()


    def toggle_ai_explanations(self) -> None:
        raise NotImplementedError

    def ai_explanations_is_enabled(self) -> bool:
        return False  # MOCK


    def _draw_events(self, time_step: float) -> None:
        for event in self.event_receiver.recv():
            match event:
                # world events
                case ArenaUpdateSize(width, height):
                    self.arena_drawer.update_size(width, height)

                case FoodCreated(food_pos):
                    self.food_draw_updater.spawn_food(food_pos, time_step)
                case FoodConsumed(food_pos, by) if by is not None:
                    consumer_head_pos = self.snake_draw_updaters[by].get_head_pos()
                    self.food_draw_updater.eat_food(food_pos, consumer_head_pos, time_step)
                case FoodConsumed(food_pos):
                    self.food_draw_updater.despawn_food(food_pos, time_step)

                # agent events
                case SnakeSpawn(snake_id, pos):
                    self.snake_draw_updaters[snake_id].update_draw_snake_spawn(time_step, event)
                case SnakeDie(snake_id):
                    self.snake_draw_updaters[snake_id].update_draw_snake_die(time_step, event)

                case SnakeMovement(snake_id, SnakeMovementType.TELEPORT):
                    self.snake_draw_updaters[snake_id].update_draw_snake_teleport(time_step, event)
                case SnakeMovement(snake_id):
                    self.snake_draw_updaters[snake_id].update_draw_snake_move(time_step, event)

                case SnakeDash(snake_id):
                    raise BackEventHandleNotImplemented(event)  # NotImplemented

    def update_draw(self, time_step: float) -> None:
        self._draw_events(time_step)


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

    def update_size(self, width: int, height: int) -> None:
        self.arena_width = width
        self.arena_height = height
        self.erase_and_draw()

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
