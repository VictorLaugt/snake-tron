from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.core.window import Keyboard, Window
from kivy.event import EventDispatcher

from back.direction import DOWN, LEFT, RIGHT, UP
from events.front2back_protocol import *

if TYPE_CHECKING:
    from typing import Optional, Sequence

    from kivy.core.window import WindowBase

    from back.type_hints import *
    from events.pipe import EventSender
    from front.type_hints import *

__all__ = ['KeyBoardControlManager']


class PlayerKeyBoardControl(EventDispatcher):
    def __init__(
        self,
        snake_id: int, event_sender: EventSender[FrontendEvent],
        up: str, left: str, down: str, right: str
    ) -> None:
        super().__init__()
        self.snake_id = snake_id
        self.event_sender = event_sender
        self.key_bindings = {
            Keyboard.keycodes[up]: UP,
            Keyboard.keycodes[right]: RIGHT,
            Keyboard.keycodes[down]: DOWN,
            Keyboard.keycodes[left]: LEFT,
        }
        Window.bind(on_key_down=self.on_key_down)

    def unbind(self):
        Window.unbind(on_key_down=self.on_key_down)

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
            self.event_sender.send(PlayerDirRequest(self.snake_id, direction))


class KeyBoardControlManager:
    def __init__(
        self,
        event_sender: EventSender[FrontendEvent],
        keyboard_control_sets: Sequence[tuple[str, str, str, str]]
    ) -> None:
        self.event_sender = event_sender
        self.keyboard_control_sets = keyboard_control_sets
        self.controllers: dict[int, PlayerKeyBoardControl] = {}

    def add_player_snake(self, snake_id: int) -> None:
        if len(self.controllers) >= len(self.keyboard_control_sets):
            return

        self.controllers[snake_id] = PlayerKeyBoardControl(
            snake_id, self.event_sender,
            *self.keyboard_control_sets[len(self.controllers)]
        )

    def remove_player_snake(self, snake_id: int) -> None:
        self.controllers.pop(snake_id).unbind()
