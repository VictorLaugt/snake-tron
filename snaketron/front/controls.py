from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING

from back.direction import DOWN, LEFT, RIGHT, UP
from kivy.core.window import Keyboard, Window
from kivy.event import EventDispatcher
from kivy.graphics import Color, InstructionGroup, Line
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

if TYPE_CHECKING:
    from typing import Iterable, Optional, Sequence

    from back.agents import PlayerSnakeAgent
    from back.type_hints import Direction
    from front.type_hints import ColorValue
    from front.world_display import SnakeColors
    from kivy.core.window import WindowBase
    from kivy.input import MotionEvent


class SwipeDirectionFilter:
    def __init__(self, initial_dir: Direction):
        self.reset(initial_dir)

    def reset(self, initial_dir: Direction):
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


class PlayerSwipeControl(Widget):
    background_color = ListProperty(get_color_from_hex('#FFFFFF00'))
    border_color = ListProperty(get_color_from_hex('#FFFFFF00'))

    draw_instr: InstructionGroup
    player: PlayerSnakeAgent
    colors: SnakeColors

    min_seg_sqr_len: float
    touch_uid: Optional[int]
    prev_touch_pos: tuple[float, float]
    control_filter: SwipeDirectionFilter

    def on_kv_post(self, base_widget: Widget) -> None:
        self.draw_instr = InstructionGroup()
        self.canvas.add(self.draw_instr)
        self.touch_starts = {}

    def init_logic(
        self,
        player: PlayerSnakeAgent,
        colors: SnakeColors,
        background_color: ColorValue,
        min_seg_len: float
    ) -> None:
        self.player = player

        self.colors = colors
        self.background_color = background_color
        self.border_color = colors.head

        self.min_seg_sqr_len = min_seg_len**2
        self.touch_uid = None
        self.prev_touch_pos = (0., 0.)
        self.control_filter = SwipeDirectionFilter(player.get_direction())

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if self.touch_uid is not None or not self.collide_point(touch.x, touch.y):
            return False

        self.touch_uid = touch.uid
        self.prev_touch_pos = touch.pos
        self.control_filter.reset(self.player.get_direction())
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
            self.player.add_dir_request(direction)

        self.prev_touch_pos = touch.pos
        return True

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if touch.uid != self.touch_uid:
            return False

        self.touch_uid = None
        return True

    def update_direction_display(self) -> None:
        self.draw_instr.clear()

        if not self.player.is_alive():
            return

        cx, cy = self.center
        size = min(self.width, self.height) * 0.2
        direction = self.player.get_direction()
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
    def init_logic(self, player_controllers: Iterable[PlayerSwipeControl]) -> None:
        for controller in player_controllers:
            self.add_widget(controller)


class PlayerKeyBoardControl(EventDispatcher):
    player: PlayerSnakeAgent
    key_bindings: dict[int, Direction]

    def init_logic(self, player: PlayerSnakeAgent, up: str, left: str, down: str, right: str) -> None:
        self.player = player
        self.key_bindings = {
            Keyboard.keycodes[up]: UP,
            Keyboard.keycodes[right]: RIGHT,
            Keyboard.keycodes[down]: DOWN,
            Keyboard.keycodes[left]: LEFT,
        }
        Window.bind(on_key_down=self.on_key_down)

    def on_key_down(
        self,
        window: WindowBase,
        key: int,
        scancode: int,
        codepoint: Optional[str],
        modifiers: Sequence[str]
    ) -> None:
        direction = self.key_bindings.get(key)
        if direction is not None:
            self.player.add_dir_request(direction)
