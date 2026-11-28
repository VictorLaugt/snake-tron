from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.core.window import Keyboard, Window
from kivy.event import EventDispatcher

from snaketron.back.direction import DOWN, LEFT, RIGHT, UP

if TYPE_CHECKING:
    from typing import Optional, Sequence

    from kivy.core.window import WindowBase

    from snaketron.front.controls.player_controller import PlayerController
    from snaketron.front.type_hints import KeyboardSet

__all__ = ['KeyBoardControl']


class KeyBoardControl(EventDispatcher):
    def __init__(self, controller: PlayerController, keyboard_set: KeyboardSet) -> None:
        super().__init__()
        self.controller = controller
        self.keyboard_set = up, left, down, right = keyboard_set
        self.key_bindings = {
            Keyboard.keycodes[up]: UP,
            Keyboard.keycodes[right]: RIGHT,
            Keyboard.keycodes[down]: DOWN,
            Keyboard.keycodes[left]: LEFT,
        }
        Window.bind(on_key_down=self.on_key_down)

    def get_keyboard_set(self) -> KeyboardSet:
        return self.keyboard_set

    def disable_control(self) -> None:
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
            self.controller.register_new_input(direction)
