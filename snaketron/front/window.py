from __future__ import annotations

from typing import TYPE_CHECKING, cast

from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex

from snaketron.events.back2front_protocol import *
from snaketron.events.front2back_protocol import *
from snaketron.front.colors import SnakeColorManager, UIColors, WorldColors
from snaketron.front.controls import PlayerControllerGroup, PlayerControllerManager
from snaketron.front.score_board import ScoreBoard
from snaketron.front.world_display import WorldDisplay

if TYPE_CHECKING:
    from kivy.uix.widget import Widget

    from snaketron.events.abstract_pipe import AbstractEventSender
    from snaketron.front.type_hints import *

__all__ = ['SnakeTronWindow']


MINIMAL_TIME_STEP = 0.01


class SnakeTronWindow(BoxLayout):
    app_background_color = ListProperty(get_color_from_hex('#000000'))

    def on_kv_post(self, base_widget: Widget) -> None:
        self.controller_groups: list[PlayerControllerGroup] = []
        for child in self.children:
            if isinstance(child, PlayerControllerGroup):
                self.controller_groups.append(child)

    def init_logic(
        self,
        event_sender: AbstractEventSender[FrontendEvent],  # sends events to the back
        time_step: float,
        ai_explanations: bool,
        colors: dict,
        swipe_sensitivity: float,
    ) -> None:
        # link to the backend
        self.event_sender = event_sender

        # game speed
        self.paused = False
        self.full_speed_enabled = False
        self.regular_time_step = time_step
        self.time_step = time_step

        # colors
        world_colors = self._create_world_colors(colors)
        ui_colors = self._create_ui_colors(colors)
        self.snake_color_manager = SnakeColorManager(colors)
        self.app_background_color = ui_colors.app_background

        # propagates logic to child widgets
        cast(ScoreBoard, self.ids.score_board).init_logic()
        cast(WorldDisplay, self.ids.world_display).init_logic(
            self, self.ids.score_board, world_colors, swipe_sensitivity
        )
        keyboard_control_sets = (
            ('up', 'left', 'down', 'right'),
            ('z', 'q', 's', 'd'),
            ('i', 'j', 'k',  'l')
        )
        self.player_controller_manager = PlayerControllerManager(
            event_sender, self.controller_groups, ui_colors,
            swipe_sensitivity, keyboard_control_sets
        )

        # ai inspection
        self.ai_inspection_enabled = False
        self.ai_snakes: set[int] = set()
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

    def toggle_fullspeed(self) -> None:
        self.full_speed_enabled = not self.full_speed_enabled
        self.time_step = MINIMAL_TIME_STEP if self.full_speed_enabled else self.regular_time_step
        self.event_sender.send(SimulationSpeedUpdateRequest(time_step=self.time_step, pause=None))

    def fullspeed_is_enabled(self) -> bool:
        return self.full_speed_enabled

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.event_sender.send(SimulationSpeedUpdateRequest(time_step=None, pause=self.paused))

    def toggle_ai_explanations(self) -> None:
        self.ai_inspection_enabled = not self.ai_inspection_enabled
        if self.ai_inspection_enabled:
            for snake_id in self.ai_snakes:
                self.event_sender.send(AiInspectionRequest(snake_id, True))
        else:
            for snake_id in self.ai_snakes:
                self.event_sender.send(AiInspectionRequest(snake_id, False))
                cast(WorldDisplay, self.ids.world_display).remove_ai_snake_inspection(snake_id)


    def ai_explanations_is_enabled(self) -> bool:
        return self.ai_inspection_enabled

    def add_snake(self, snake_id: int, is_player: bool) -> None:
        snake_colors = self.snake_color_manager.add_snake(snake_id)
        cast(WorldDisplay, self.ids.world_display).add_snake(snake_id, snake_colors)
        cast(ScoreBoard, self.ids.score_board).add_snake(snake_id, snake_colors)
        if is_player:
            self.player_controller_manager.add_player_snake(snake_id, snake_colors)
        else:
            self.ai_snakes.add(snake_id)

    def remove_snake(self, snake_id: int, is_player: bool) -> None:
        self.snake_color_manager.remove_snake(snake_id)
        cast(WorldDisplay, self.ids.world_display).remove_snake(snake_id)
        cast(ScoreBoard, self.ids.score_board).remove_snake(snake_id)
        if is_player:
            self.player_controller_manager.remove_player_snake(snake_id)

    def process_backend_event(self, event: BackendEvent) -> None:
        world_display = cast(WorldDisplay, self.ids.world_display)
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

            case SnakeSpawn():
                world_display.snake_spawn(self.time_step, event)
            case SnakeDie(snake_id):
                world_display.snake_die(self.time_step, event)

            case SnakeMovement(snake_id, SnakeMovementType.TELEPORT, _, new_dir, _):
                raise BackEventHandleNotImplemented(event)  # NotImplemented
                self.player_controller_manager.update_real_direction(snake_id, new_dir)
            case SnakeMovement(snake_id, _, _, new_dir, _):
                world_display.snake_move(self.time_step, event)
                self.player_controller_manager.update_real_direction(snake_id, new_dir)
            case SnakeDash():
                raise BackEventHandleNotImplemented(event)  # NotImplemented

            case AiSnakeInspection():
                world_display.ai_snake_inspect(event)
