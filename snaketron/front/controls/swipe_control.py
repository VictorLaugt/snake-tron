from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.uix.widget import Widget
from snaketron.back.direction import UP, DOWN, RIGHT, LEFT

if TYPE_CHECKING:
    from typing import Optional

    from kivy.input import MotionEvent

    from snaketron.back.type_hints import Direction
    from snaketron.front.controls.keyboard_control import PlayerController

__all__ = ['SwipeControl']


class SwipeControl(Widget):
    def __init__(
        self,
        controller: PlayerController,
        min_swipe_len: float,
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.controller = controller
        self.min_swipe_sqr_len = min_swipe_len * min_swipe_len

        self.touch_uid: Optional[int] = None
        self.prev_touch_pos = (0., 0.)
        self.direction_filter = SwipeDirectionFilter()

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if self.touch_uid is not None or not self.collide_point(touch.x, touch.y):
            return False

        self.touch_uid = touch.uid
        self.prev_touch_pos = touch.pos
        self.direction_filter.reset(
            self.controller.get_last_direction_input() or self.controller.get_real_direction()
        )
        return True

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if touch.uid != self.touch_uid:
            return False

        x, y = touch.pos
        prev_x, prev_y = self.prev_touch_pos
        dx, dy = x-prev_x, y-prev_y
        if dx*dx + dy*dy < self.min_swipe_sqr_len:
            return True

        if abs(dx) > abs(dy):
            direction = RIGHT if dx > 0 else LEFT
        else:
            direction = UP if dy > 0 else DOWN

        if self.direction_filter.filter(direction):
            self.controller.register_new_input(direction)

        self.prev_touch_pos = touch.pos
        return True

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if touch.uid != self.touch_uid:
            return False

        self.touch_uid = None
        return True


class SwipeDirectionFilter:
    def __init__(self) -> None:
        self.prev_valid_dir: Direction = (0, 0)
        self.prev_rot = 0  # 1 when turning right; -1 when turning left
        self.u_turn = False  # True when turning twice in the same direction; False otherwise

    def reset(self, initial_dir: Direction) -> None:
        self.prev_valid_dir = initial_dir
        self.prev_rot = 0
        self.u_turn = False

    def filter(self, swipe_dir: Direction) -> bool:
        # prevents consecutive swipe in the same direction
        if swipe_dir == self.prev_valid_dir:
            return False

        rot = self.prev_valid_dir[0]*swipe_dir[1] - self.prev_valid_dir[1]*swipe_dir[0]

        # prevents selecting the same or the opposite direction
        if rot == 0:
            return False

        # prevents three consecutive turns in the same direction
        elif rot == self.prev_rot:
            if self.u_turn:
                return False
            self.u_turn = True
        else:
            self.u_turn = False

        # validates the swipe direction
        self.prev_valid_dir = swipe_dir
        self.prev_rot = rot
        return True
