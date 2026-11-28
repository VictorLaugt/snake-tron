from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional, Sequence

    from snaketron.back.type_hints import Direction
    from snaketron.events.abstract_pipe import AbstractEventSender
    from snaketron.events.front2back_protocol import FrontendEvent
    from snaketron.front.colors import SnakeColors, UIColors
    from snaketron.front.controls.player_controller_group import PlayerControllerGroup
    from snaketron.front.type_hints import KeyboardSet

__all__ = ['PlayerControllerManager']


class PlayerControllerManager:
    """Assigns each player to its controller."""
    def __init__(
        self,
        event_sender: AbstractEventSender[FrontendEvent],
        controller_groups: Iterable[PlayerControllerGroup],
        ui_global_colors: UIColors,
        swipe_sensitivity: float,
        keyboard_control_sets: Sequence[KeyboardSet]
    ) -> None:
        self.available_keyboard_sets = deque(keyboard_control_sets)

        self.controller_groups = list(controller_groups)
        self.controller_group_mapping: dict[int, int] = {}

        for group in self.controller_groups:
            group.init_logic(
                event_sender, ui_global_colors, swipe_sensitivity
            )

    def add_player_snake(self, snake_id: int, colors: SnakeColors) -> None:
        if self.available_keyboard_sets:
            kb_set = self.available_keyboard_sets.popleft()
        else:
            kb_set = None

        group_id = len(self.controller_group_mapping) % len(self.controller_groups)
        self.controller_groups[group_id].add_player_snake(snake_id, colors, kb_set)
        self.controller_group_mapping[snake_id] = group_id

    def remove_player_snake(self, snake_id: int) -> None:
        group_id = self.controller_group_mapping.pop(snake_id)
        group = self.controller_groups[group_id]
        if (kb_set := group.get_kb_set(snake_id)) is not None:
            self.available_keyboard_sets.append(kb_set)
        group.remove_player_snake(snake_id)

    def update_real_direction(self, snake_id: int, d: Optional[Direction]) -> None:
        if (group_id := self.controller_group_mapping.get(snake_id)) is not None:
            self.controller_groups[group_id].update_real_direction(snake_id, d)
