from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from kivy.properties import ListProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import get_color_from_hex

from events.front2back_protocol import PlayerDirRequest
from front.controls.direction_input_drawer import ArrowDrawer, ArrowDrawerTool
from front.controls.keyboard_control import KeyBoardControl
from front.controls.swipe_control import SwipeControl

if TYPE_CHECKING:
    from typing import Optional

    from kivy.uix.widget import Widget

    from back.type_hints import Direction
    from events.abstract_pipe import AbstractEventSender
    from events.front2back_protocol import FrontendEvent
    from front.colors import SnakeColors
    from front.type_hints import ColorValue, KeyboardSet

__all__ = ['PlayerController']


class PlayerController(FloatLayout):
    """Widget providing a controller for an indivudual player."""
    background_color = ListProperty(get_color_from_hex('#FFFFFF00'))
    border_color = ListProperty(get_color_from_hex('#FFFFFF00'))

    def __init__(
        self,
        event_sender: AbstractEventSender[FrontendEvent],
        snake_id: int,
        snake_colors: SnakeColors,
        background_color: ColorValue,
    ) -> None:
        super().__init__()

        # keyboard controls
        self.keyboard_control: Optional[KeyBoardControl] = None

        # swipe controls
        self.swipe_control: Optional[SwipeControl] = None

        # inputs
        self.event_sender = event_sender
        self.snake_id = snake_id
        self.last_direction_input: Optional[Direction] = None
        self.real_direction: Direction = (0, 0)

        # direction display
        self.background_color = background_color
        self.border_color = snake_colors.head
        arrow_drawer_tool = ArrowDrawerTool(
            get_widget_center=(lambda: self.center),
            get_widget_size=(lambda: self.size)
        )
        self.arrow_drawer = ArrowDrawer(arrow_drawer_tool, snake_colors)
        self.canvas.add(self.arrow_drawer.get_graphical_elements())


    # ---- keyboard controls
    def get_keyboard_set(self) -> Optional[KeyboardSet]:
        if self.keyboard_control is not None:
            return self.keyboard_control.get_keyboard_set()

    def enable_keyboard_control(self, keyboard_set: KeyboardSet) -> None:
        self.disable_keyboard_control()
        self.keyboard_control = KeyBoardControl(self, keyboard_set)

    def disable_keyboard_control(self) -> None:
        if self.keyboard_control is not None:
            self.keyboard_control.disable_control()
            self.keyboard_control = None


    # ---- swipe controls
    def enable_swipe_control(self, swipe_sensitivity: float) -> None:
        self.swipe_control = SwipeControl(
            self, 1/swipe_sensitivity,
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(self.swipe_control)

    def disable_swipe_control(self) -> None:
        self.swipe_control = None


    # ---- inputs
    def register_new_input(self, d: Direction) -> None:
        self.last_direction_input = d
        self.event_sender.send(PlayerDirRequest(self.snake_id, d))
        self.arrow_drawer.add_new_segment(d)

    def get_last_direction_input(self) -> Optional[Direction]:
        return self.last_direction_input

    def get_real_direction(self) -> Direction:
        return self.real_direction


    # ---- direction display
    def on_size(self, instance: Widget, value: tuple[float, float]) -> None:
        self.arrow_drawer.draw_arrow()

    def on_pos(self, instance: Widget, value: tuple[float, float]) -> None:
        self.arrow_drawer.draw_arrow()

    def update_real_direction(self, d: Optional[Direction]) -> None:
        if d is None:
            self.arrow_drawer.erase_all_segments()
            return

        self.real_direction = d
        n_segments = self.arrow_drawer.n_segments()
        if n_segments == 0:
            self.arrow_drawer.add_new_segment(d)

        elif n_segments == 1 and self.arrow_drawer.get_segment(0) != d:
            self.arrow_drawer.erase_all_segments()
            self.arrow_drawer.add_new_segment(d)

        elif n_segments > 1:
            if self.arrow_drawer.get_segment(1) == d:
                self.arrow_drawer.pop_first_segment()
            else:
                self.arrow_drawer.erase_all_segments()
                self.arrow_drawer.add_new_segment(d)

