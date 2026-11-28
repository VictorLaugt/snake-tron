from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.uix.boxlayout import BoxLayout

from snaketron.front.controls.player_controller import PlayerController

if TYPE_CHECKING:
    from typing import Optional

    from snaketron.back.type_hints import Direction
    from snaketron.events.abstract_pipe import AbstractEventSender
    from snaketron.events.front2back_protocol import FrontendEvent
    from snaketron.front.colors import SnakeColors, UIColors
    from snaketron.front.type_hints import KeyboardSet

__all__ = ['PlayerControllerGroup']


class PlayerControllerGroup(BoxLayout):
    """A group of several player controller widgets."""
    def init_logic(
        self,
        event_sender: AbstractEventSender[FrontendEvent],
        ui_global_colors: UIColors,
        swipe_sensitivity: float,
    ) -> None:
        self.event_sender = event_sender
        self.ui_global_colors = ui_global_colors
        self.swipe_sensitivity = swipe_sensitivity

        self.controllers: dict[int, PlayerController] = {}

    def add_player_snake(self, snake_id: int, colors: SnakeColors, kb_set: Optional[KeyboardSet]) -> None:
        assert snake_id not in self.controllers.keys()

        controller = PlayerController(
            self.event_sender, snake_id,
            colors, self.ui_global_colors.swipe_zone_bg
        )
        if kb_set is not None:
            controller.enable_keyboard_control(kb_set)
        controller.enable_swipe_control(self.swipe_sensitivity)
        self.controllers[snake_id] = controller
        self.add_widget(controller)

    def remove_player_snake(self, snake_id: int) -> None:
        controller = self.controllers.pop(snake_id)
        controller.disable_keyboard_control()
        controller.disable_swipe_control()
        self.remove_widget(controller)

    def get_kb_set(self, snake_id: int) -> Optional[KeyboardSet]:
        controller = self.controllers.get(snake_id)
        if controller is not None:
            return controller.get_keyboard_set()

    def update_real_direction(self, snake_id: int, d: Optional[Direction]) -> None:
        self.controllers[snake_id].update_real_direction(d)
