from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.graphics import InstructionGroup, Color, Rectangle
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty
from collections import deque

if TYPE_CHECKING:
    from typing import Optional

    from front.world_display import WorldDisplay, SnakeColors

    from back.agents import AbstractSnakeAgent
    from back.events import SnakeMovement
    from back.type_hints import Position

class SnakeDrawUpdater(EventDispatcher):
    tail_rgb = ListProperty([0., 0., 0.])

    animated_head_x = NumericProperty(0.)
    animated_head_y = NumericProperty(0.)
    animated_head_pos = ReferenceListProperty(animated_head_x, animated_head_y)
    animated_head_rgb = ListProperty([0., 0., 0.])

    animated_tail_x = NumericProperty(0.)
    animated_tail_y = NumericProperty(0.)
    animated_tail_pos = ReferenceListProperty(animated_tail_x, animated_tail_y)
    animated_tail_rgb = ListProperty([0., 0., 0.])

    def __init__(
        self,
        world_display: WorldDisplay,
        snake: AbstractSnakeAgent,
        colors: SnakeColors,
        n_decay_steps: int
    ) -> None:
        super().__init__()
        self.display = world_display
        self.instr_back = InstructionGroup()
        self.instr_fore = InstructionGroup()
        self.display.canvas.add(self.instr_back)
        self.display.canvas.add(self.instr_fore)

        self.snake = snake
        self.alive = snake.is_alive()

        # [end of tail <----> 1 cell before head]
        self.tail_squares: deque[Rectangle] = deque()
        self.tail_pos: deque[Position] = deque()
        self.head_pos: Position = None

        # movement animation system
        self.animated_tail: Rectangle = None
        self.tail_animation: Optional[Animation] = None
        self.animated_head: Rectangle = None
        self.head_animation: Optional[Animation] = None

        # color system
        self.colors = colors
        self.animated_head_color = Color(*self.colors.head)
        self.animated_tail_color = Color(*self.colors.tail)
        self.tail_color = Color(*self.colors.tail)
        self.n_decay_steps = n_decay_steps
        self.decay_animation: Optional[Animation] = None

    def on_animated_head_pos(self, _, value):
        self.animated_head.pos = value

    def on_animated_tail_pos(self, _, value):
        self.animated_tail.pos = value

    def on_animated_head_rgb(self, _, value):
        self.animated_head_color.rgb = value

    def on_animated_tail_rgb(self, _, value):
        self.animated_tail_color.rgb = value

    def on_tail_rgb(self, _, value):
        self.tail_color.rgb = value

    def _square(self, pos: Position) -> Rectangle:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        return Rectangle(pos=(x, y), size=(s, s))

    def _stop_animations(self) -> None:
        if self.head_animation is not None:
            self.head_animation.stop(self)
        if self.tail_animation is not None:
            self.tail_animation.stop(self)
        if self.decay_animation is not None:
            self.decay_animation.stop(self)

    def _clear_instruction_groups(self) -> None:
        self.instr_back.clear()
        self.instr_fore.clear()

    def _init_color(self) -> None:
        self.animated_head_rgb = self.colors.head
        self.animated_tail_rgb = self.colors.tail
        self.tail_rgb = self.colors.tail

    def _init_body(self) -> None:
        assert len(self.snake) >= 1

        self.tail_squares.clear()
        self.tail_pos.clear()

        cells = self.snake.iter_cells()
        self.head_pos = next(cells)

        self.tail_color = Color(*self.tail_rgb)
        self.instr_back.add(self.tail_color)
        for pos in cells:
            sqr = self._square(pos)
            self.tail_squares.appendleft(sqr)
            self.tail_pos.appendleft(pos)
            self.instr_back.add(sqr)

    def _init_animated_tail(self) -> None:
        end_tail_pos = self.tail_pos[0] if len(self.tail_pos) > 0 else self.head_pos
        self.animated_tail = self._square(end_tail_pos)
        self.animated_tail_pos = self.animated_tail.pos
        self.animated_tail_color = Color(*self.animated_tail_rgb)
        self.instr_fore.add(self.animated_tail_color)
        self.instr_fore.add(self.animated_tail)

    def _init_animated_head(self) -> None:
        self.animated_head = self._square(self.head_pos)
        self.animated_head_pos = self.animated_head.pos
        self.animated_head_color = Color(*self.animated_head_rgb)
        self.instr_fore.add(self.animated_head_color)
        self.instr_fore.add(self.animated_head)

    def reset(self) -> None:
        self._stop_animations()
        self._clear_instruction_groups()
        self._init_color()
        if self.alive:
            self._init_body()
            self._init_animated_tail()
            self._init_animated_head()

    def _update_body(self, new_head_pos: Position, growth: int) -> None:
        # adds a square at the current head position
        self.tail_pos.append(self.head_pos)
        sqr = self._square(self.head_pos)
        self.tail_squares.append(sqr)
        self.instr_back.add(sqr)
        self.head_pos = new_head_pos

        if growth <= 0:
            # removes squares at the end of the tail
            for _ in range(1-growth):
                sqr = self.tail_squares.popleft()
                self.instr_back.remove(sqr)
                self.tail_pos.popleft()

        elif growth >= 2:
            # adds squares at the end of the tail
            for _ in range(growth-1):
                pos = self.tail_pos[0]
                self.tail_pos.appendleft(pos)
                sqr = self._square(pos)
                self.tail_squares.appendleft(sqr)
                self.instr_back.add(sqr)

    def _animate_head(self, time_step: float) -> None:
        # slides the animated head square at the new head position
        self.head_animation = Animation(
            animated_head_pos=self.display.pos_to_coord(self.head_pos),
            duration=time_step,
            t='linear'
        )
        self.head_animation.start(self)

    def _animate_tail(self, time_step: float) -> None:
        # slides the animated tail square at the new tail end position
        tail_end_pos = self.tail_pos[0] if len(self.tail_pos) > 0 else self.head_pos
        x_src, y_src = self.animated_tail_pos
        x_dst, y_dst = self.display.pos_to_coord(tail_end_pos)
        dx, dy = x_dst-x_src, y_dst-y_src

        self.tail_animation = Animation(
            animated_tail_pos=(x_src+1.2*dx, y_src+1.2*dy),
            duration=time_step,
            t='linear'
        )
        self.tail_animation.start(self)

    def _animate_decay(self, time_step: float) -> None:
        d = self.n_decay_steps * time_step
        animation_transition = 'out_circ'
        self.decay_animation = Animation(
            animated_head_rgb=self.colors.head_decay_final, duration=d, t=animation_transition
        ) & Animation(
            animated_tail_rgb=self.colors.tail_decay_final, duration=d, t=animation_transition
        ) & Animation(
            tail_rgb=self.colors.tail_decay_final, duration=d, t=animation_transition
        )
        self.decay_animation.bind(on_complete=(lambda *_: self._clear_instruction_groups()))

        self.animated_head_rgb = self.colors.head_decay_first
        self.animated_tail_rgb = self.colors.tail_decay_first
        self.tail_rgb = self.colors.tail_decay_first
        self.decay_animation.start(self)

    def update_draw_snake_move(self, event: SnakeMovement, time_step: float) -> None:
        self._update_body(event.new_head_pos, event.growth)
        self._animate_head(time_step)
        self._animate_tail(time_step)

    def update_draw_spawn(self) -> None:
        self.alive = True
        self.reset()

    def update_draw_die(self, time_step: float) -> None:
        self.alive = False
        self._animate_decay(time_step)
