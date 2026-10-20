from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.graphics import Color, InstructionGroup, Line
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import get_color_from_hex

from back.direction import DOWN, LEFT, RIGHT, UP
from events.front2back_protocol import *
from front.colors import UIColors
from front.world_display import WorldDisplay

if TYPE_CHECKING:
    from typing import Iterable

    from kivy.input import MotionEvent
    from kivy.uix.widget import Widget

    from back.type_hints import *
    from events.pipe import EventSender
    from front.colors import SnakeColors
    from front.type_hints import *

__all__ = ['PlayerSwipeControl', 'SwipeControlZone']


class PlayerSnakeState:
    def __init__(
        self,
        event_sender: EventSender[FrontendEvent],
        world_display: WorldDisplay,
        snake_id: int
    ) -> None:
        self.event_sender = event_sender
        self.world_display = world_display
        self.snake_id = snake_id

    def get_direction(self) -> Direction:
        d = self.world_display.get_snake_dir(self.snake_id)
        if d is None:  # FIXME: should not be None
            print(f"DEBUG: None")
            return (0, 0)
        return d

    def send_dir_request(self, dir_request: Direction) -> None:
        self.event_sender.send(PlayerDirRequest(self.snake_id, dir_request))


class SwipeDirectionFilter:
    def __init__(self, initial_dir: Direction):
        self.reset(initial_dir)

    def reset(self, initial_dir: Direction):
        assert initial_dir is not None
        self.prev_valid_dir = initial_dir
        self.prev_rot = 0
        self.u_turn = False

    def filter(self, swipe_dir: Direction) -> bool:
        # prevents consecutive swipe in the same direction
        if swipe_dir == self.prev_valid_dir:
            return False

        # prevents three consecutive turns in the same direction
        rot = self.prev_valid_dir[0]*swipe_dir[1] - self.prev_valid_dir[1]*swipe_dir[0]
        if rot == self.prev_rot:
            if self.u_turn:
                return False
            self.u_turn = True
        else:
            self.u_turn = False

        # validates the swipe direction
        self.prev_valid_dir = swipe_dir
        self.prev_rot = rot
        return True

    def get_prev_valid_dir(self) -> Direction:
        return self.prev_valid_dir


class PlayerSwipeControl(FloatLayout):
    background_color = ListProperty(get_color_from_hex('#FFFFFF00'))
    border_color = ListProperty(get_color_from_hex('#FFFFFF00'))

    def __init__(
        self,
        player_state: PlayerSnakeState,
        snake_colors: SnakeColors,
        background_color: ColorValue,
        min_seg_len: float,
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.player_state = player_state

        self.colors = snake_colors
        self.background_color = background_color
        self.border_color = snake_colors.head

        self.min_seg_sqr_len = min_seg_len**2
        self.touch_uid = None
        self.prev_touch_pos = (0., 0.)
        self.control_filter = SwipeDirectionFilter(player_state.get_direction())

        self.draw_instr = InstructionGroup()
        self.canvas.add(self.draw_instr)


    def on_touch_down(self, touch: MotionEvent) -> bool:
        if self.touch_uid is not None or not self.collide_point(touch.x, touch.y):
            return False

        self.touch_uid = touch.uid
        self.prev_touch_pos = touch.pos
        self.control_filter.reset(self.player_state.get_direction())
        return True

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if touch.uid != self.touch_uid:
            return False

        x, y = touch.pos
        prev_x, prev_y = self.prev_touch_pos
        dx, dy = x-prev_x, y-prev_y
        if dx*dx + dy*dy < self.min_seg_sqr_len:
            return True

        if abs(dx) > abs(dy):
            direction = RIGHT if dx > 0 else LEFT
        else:
            direction = UP if dy > 0 else DOWN

        if self.control_filter.filter(direction):
            self.player_state.send_dir_request(direction)
            self.update_direction_display()

        self.prev_touch_pos = touch.pos
        return True

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if touch.uid != self.touch_uid:
            return False

        self.touch_uid = None
        return True

    def on_size(self, instance: Widget, value: tuple[float, float]) -> None:
        self.update_direction_display()

    def on_pos(self, instance: Widget, value: tuple[float, float]) -> None:
        self.update_direction_display()

    def update_direction_display(self) -> None:
        self.draw_instr.clear()

        cx, cy = self.center
        size = min(self.width, self.height) * 0.2
        direction = self.control_filter.get_prev_valid_dir()
        if direction == UP:
            points = (cx, cy - size, cx, cy + size, cx - size * 0.5, cy + size * 0.5,
                      cx, cy + size, cx + size * 0.5, cy + size * 0.5)
        elif direction == DOWN:
            points = (cx, cy + size, cx, cy - size, cx - size * 0.5, cy - size * 0.5,
                      cx, cy - size, cx + size * 0.5, cy - size * 0.5)
        elif direction == LEFT:
            points = (cx + size, cy, cx - size, cy, cx - size * 0.5, cy + size * 0.5,
                      cx - size, cy, cx - size * 0.5, cy - size * 0.5)
        elif direction == RIGHT:
            points = (cx - size, cy, cx + size, cy, cx + size * 0.5, cy + size * 0.5,
                      cx + size, cy, cx + size * 0.5, cy - size * 0.5)
        else:
            return

        self.draw_instr.add(Color(rgba=self.colors.tail))
        self.draw_instr.add(Line(points=points, width=2, cap='round', joint='round'))


class SwipeControlZone(BoxLayout):
    def init_logic(
        self,
        event_sender: EventSender[FrontendEvent],
        world_display: WorldDisplay,
        input_sensitivity: float,
        ui_colors: UIColors
    ) -> None:
        self.event_sender = event_sender
        self.world_display = world_display
        self.input_sensitivity = input_sensitivity
        self.ui_colors = ui_colors
        self.controllers: dict[int, PlayerSwipeControl] = {}

    def add_player_snake(self, snake_id: int, snake_colors: SnakeColors) -> None:
        controller = PlayerSwipeControl(
            PlayerSnakeState(self.event_sender, self.world_display, snake_id),
            snake_colors, self.ui_colors.swipe_zone_bg,
            1/self.input_sensitivity
        )
        self.controllers[snake_id] = controller
        self.add_widget(controller)

    def remove_player_snake(self, snake_id: int) -> None:
        controller = self.controllers.pop(snake_id)
        self.remove_widget()


class SwipeControlManager:
    def __init__(
        self,
        event_sender: EventSender[FrontendEvent],
        world_display: WorldDisplay,
        swipe_zones: Iterable[SwipeControlZone],
        input_sensitivity: float,
        ui_colors: UIColors
    ) -> None:
        self.swipe_zones = list(swipe_zones)
        self.controller_zone_mapping: dict[int, int] = {}

        for swipe_zone in self.swipe_zones:
            swipe_zone.init_logic(
                event_sender, world_display, input_sensitivity, ui_colors
            )

    def add_player_snake(self, snake_id: int, colors: SnakeColors) -> None:
        swipe_zone_idx = len(self.controller_zone_mapping) % len(self.swipe_zones)
        self.swipe_zones[swipe_zone_idx].add_player_snake(snake_id, colors)
        self.controller_zone_mapping[snake_id] = swipe_zone_idx

    def remove_player_snake(self, snake_id: int) -> None:
        swipe_zone_idx = self.controller_zone_mapping.pop(snake_id)
        self.swipe_zones[swipe_zone_idx].remove_player_snake(snake_id)
