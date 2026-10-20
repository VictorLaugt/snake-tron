from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, cast

from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex

from events.back2front_protocol import *
from events.front2back_protocol import *
from front.colors import *
from front.controls import *
from front.score_board import *
from front.world_display import *

if TYPE_CHECKING:
    from typing import Sequence

    from kivy.uix.widget import Widget

    from back.agents import AbstractAISnakeAgent, AbstractSnakeAgent, PlayerSnakeAgent
    from back.world import SnakeWorld
    from events.pipe import *
    from front.type_hints import *

__all__ = ['SnakeTronWindow']


MINIMAL_TIME_STEP = 0.01


class SnakeTronWindow(BoxLayout):
    app_background_color = ListProperty(get_color_from_hex('#000000'))

    def on_kv_post(self, base_widget: Widget) -> None:
        self.swipe_zones: list[SwipeControlZone] = []
        for child in self.children:
            if isinstance(child, SwipeControlZone):
                self.swipe_zones.append(child)

    def _set_time_step(self, new_time_step: float) -> None:
        self.time_step = new_time_step
        if not self.paused:
            Clock.unschedule(self.clock_event)
            self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            Clock.unschedule(self.clock_event)
        else:
            self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

    def toggle_fullspeed(self) -> None:
        self.full_speed = not self.full_speed
        if self.full_speed:
            self._set_time_step(MINIMAL_TIME_STEP)
        else:
            self._set_time_step(self.regular_time_step)

    def fullspeed_is_enabled(self) -> bool:
        return self.full_speed

    def toggle_ai_explanations(self) -> None:
        cast(WorldDisplay, self.ids.world_display).toggle_ai_explanations()

    def ai_explanations_is_enabled(self) -> bool:
        return cast(WorldDisplay, self.ids.world_display).ai_explanations_is_enabled()


    def init_logic(
        self,
        event_receiver: EventReceiver[BackendEvent],  # receives events from the back
        event_sender: EventSender[FrontendEvent],  # sends events to the back
        world: SnakeWorld,
        time_step: float,
        ai_explanations: bool,
        colors: dict,
        input_sensitivity: float,
    ) -> None:
        # link to the backend
        self.event_receiver = event_receiver
        self.event_sender = event_sender
        self.world = world
        self.world.reset()

        # game speed
        self.paused = False
        self.full_speed = False
        self.regular_time_step = time_step
        self.time_step = time_step
        self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

        # colors
        world_colors = self._create_world_colors(colors)
        ui_colors = self._create_ui_colors(colors)
        self.snake_color_manager = SnakeColorManager(colors)
        self.app_background_color = ui_colors.app_background

        # propagates logic to child widgets
        cast(ScoreBoard, self.ids.score_board).init_logic()
        cast(WorldDisplay, self.ids.world_display).init_logic(
            self, self.ids.score_board, world_colors, input_sensitivity
        )
        self.swipe_control_manager = SwipeControlManager(
            event_sender, self.ids.world_display, self.swipe_zones,
            input_sensitivity, ui_colors
        )
        self.keyboard_control_manager = KeyBoardControlManager(
            event_sender, (
            ('up', 'left', 'down', 'right'),
            ('z', 'q', 's', 'd'),
            ('i', 'j', 'k',  'l')
        ))

        if ai_explanations:
            self.toggle_ai_explanations()

    @staticmethod
    def _create_world_colors(colors: dict) -> WorldColors:
        return WorldColors(
            food_outline=get_color_from_hex(colors['world']['food_outline']),
            food=get_color_from_hex(colors['world']['food']),
            background=get_color_from_hex(colors['world']['background']),
            gridline=get_color_from_hex(colors['world']['gridline']),
            gridborder=get_color_from_hex(colors['world']['gridborder'])
        )

    @staticmethod
    def _create_ui_colors(colors: dict) -> UIColors:
        return UIColors(
            swipe_zone_bg=get_color_from_hex(colors['ui']['swipe_zone_bg_color']),
            app_background=get_color_from_hex(colors['ui']['background'])
        )

    def add_snake(self, snake_id: int, is_player: bool) -> None:
        snake_colors = self.snake_color_manager.add_snake(snake_id)
        cast(WorldDisplay, self.ids.world_display).add_snake(snake_id, snake_colors)
        cast(ScoreBoard, self.ids.score_board).add_snake(snake_id, snake_colors)
        if is_player:
            self.swipe_control_manager.add_player_snake(snake_id, snake_colors)
            self.keyboard_control_manager.add_player_snake(snake_id)

    def remove_snake(self, snake_id: int, is_player: bool) -> None:
        self.snake_color_manager.remove_snake(snake_id)
        cast(WorldDisplay, self.ids.world_display).remove_snake(snake_id)
        cast(ScoreBoard, self.ids.score_board).remove_snake(snake_id)
        if is_player:
            self.swipe_control_manager.remove_player_snake(snake_id)
            self.keyboard_control_manager.remove_player_snake(snake_id)

    def game_step(self, dt: float) -> None:
        self.world.simulate()

        world_display = cast(WorldDisplay, self.ids.world_display)
        score_board = cast(ScoreBoard, self.ids.score_board)

        for event in self.event_receiver.recv():
            match event:
                # world events
                case ArenaUpdateSize(width, height):
                    world_display.arena_update_size(width, height)

                case FoodCreated(food_pos):
                    world_display.arena_spawn_food(food_pos, self.time_step)
                case FoodConsumed(food_pos, by) if by is not None:
                    world_display.arena_eat_food(food_pos, by, self.time_step)
                case FoodConsumed(food_pos):
                    world_display.arena_despawn_food(food_pos, self.time_step)

                # agent events
                case SnakeConnectionUpdate(snake_id, is_player, is_connecting=True):
                    self.add_snake(snake_id, is_player)
                case SnakeConnectionUpdate(snake_id, is_player, is_connecting=False):
                    self.remove_snake(snake_id, is_player)

                case SnakeSpawn(snake_id):
                    world_display.snake_spawn(snake_id, self.time_step, event)
                case SnakeDie(snake_id):
                    world_display.snake_die(snake_id, self.time_step, event)

                case SnakeMovement(snake_id, SnakeMovementType.TELEPORT):
                    raise BackEventHandleNotImplemented(event)  # NotImplemented
                case SnakeMovement(snake_id):
                    world_display.snake_move(snake_id, self.time_step, event)

                case SnakeDash(snake_id):
                    raise BackEventHandleNotImplemented(event)  # NotImplemented
