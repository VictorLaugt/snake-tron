from __future__ import annotations

from kivy.core.window import Window, Keyboard
from kivy.event import EventDispatcher
from kivy.uix.widget import Widget
from kivy.properties import ListProperty
from kivy.graphics import Color, Line, InstructionGroup
from kivy.utils import get_color_from_hex
from kivy.uix.boxlayout import BoxLayout

from itertools import chain

from direction import UP, DOWN, LEFT, RIGHT


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from agent import PlayerSnakeAgent
    from front.world_display import SnakeColors

    from kivy.core.window import WindowBase
    from kivy.input import MotionEvent

    from typing import Sequence, Iterable, Optional
    from type_hints import Direction
    from front.type_hints import ColorValue


class PlayerSwipeControl(Widget):
    background_color = ListProperty(get_color_from_hex('#FFFFFF00'))
    border_color = ListProperty(get_color_from_hex('#FFFFFF00'))

    draw_instr: InstructionGroup
    touch_starts: dict[int, tuple[float, float]]
    player: PlayerSnakeAgent
    colors: SnakeColors

    def on_kv_post(self, base_widget: Widget) -> None:
        self.draw_instr = InstructionGroup()
        self.canvas.add(self.draw_instr)
        self.touch_starts = {}

    def init_logic(self, player: PlayerSnakeAgent, colors: SnakeColors, background_color: ColorValue) -> None:
        self.player = player
        self.colors = colors
        self.border_color = self.colors.head
        self.background_color = background_color

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if not self.collide_point(touch.x, touch.y):
            return False

        self.touch_starts[touch.uid] = touch.pos
        return True

    def on_touch_up(self, touch: MotionEvent) -> bool:
        start_pos = self.touch_starts.pop(touch.uid, None)
        if start_pos is None:
            return False

        start_x, start_y = start_pos
        dx, dy = touch.x - start_x, touch.y - start_y
        if abs(dx) > abs(dy):
            direction = RIGHT if dx > 0 else LEFT
        else:
            direction = UP if dy > 0 else DOWN
        self.player.add_dir_request(direction)
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


class KeyBoardControls(EventDispatcher):
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
