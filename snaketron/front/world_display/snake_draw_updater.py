from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.graphics import Color, InstructionGroup, Rectangle
from kivy.properties import (ListProperty, NumericProperty,
                             ReferenceListProperty)


if TYPE_CHECKING:
    from typing import Optional

    from back.agents import AbstractSnakeAgent
    from back.events import SnakeMovement
    from back.type_hints import Direction, Position
    from front.world_display import SnakeColors, WorldDisplay
    from front.type_hints import ColorValue

from debug_tool import DebugSpace
dbg = DebugSpace(name="SnakeDrawUpdater")
class SnakeDrawUpdater(EventDispatcher):
    tail_rgba = ListProperty([0., 0., 0., 0.])

    head_cell_x = NumericProperty(0.)
    head_cell_y = NumericProperty(0.)
    head_cell_pos = ReferenceListProperty(head_cell_x, head_cell_y)
    head_rgba = ListProperty([0., 0., 0., 0.])

    tailend_cell_x = NumericProperty(0.)
    tailend_cell_y = NumericProperty(0.)
    tailend_cell_pos = ReferenceListProperty(tailend_cell_x, tailend_cell_y)
    tailend_rgba = ListProperty([0., 0., 0., 0.])

    wrapping_head_cell_x = NumericProperty(0.)
    wrapping_head_cell_y = NumericProperty(0.)
    wrapping_head_cell_pos = ReferenceListProperty(wrapping_head_cell_x, wrapping_head_cell_y)
    wrapping_head_rgba = ListProperty([0., 0., 0., 0.])

    wrapping_tailend_cell_x = NumericProperty(0.)
    wrapping_tailend_cell_y = NumericProperty(0.)
    wrapping_tailend_cell_pos = ReferenceListProperty(wrapping_tailend_cell_x, wrapping_tailend_cell_y)
    wrapping_tailend_rgba = ListProperty([0., 0., 0., 0.])

    def on_tail_rgba(self, _, val): self.tail_color.rgba = val

    def on_head_cell_pos(self, _, val): self.head_cell.pos = val
    def on_head_rgba(self, _, val): self.head_color.rgba = val

    def on_tailend_cell_pos(self, _, val): self.tailend_cell.pos = val
    def on_tailend_rgba(self, _, val): self.tailend_color.rgba = val

    def on_wrapping_head_cell_pos(self, _, val): self.wrapping_head_cell.pos = val
    def on_wrapping_head_rgba(self, _, val): self.wrapping_head_color.rgba = val

    def on_wrapping_tailend_cell_pos(self, _, val): self.wrapping_tailend_cell.pos = val
    def on_wrapping_tailend_rgba(self, _, val): self.wrapping_tailend_color.rgba = val

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
        self.colors = colors
        self.n_decay_steps = n_decay_steps

        # cells which remains stationary: [tail end <----> 1 cell before head]
        self.tail_color: Color = None
        self.tail_cells: deque[Rectangle] = deque()
        self.tail_pos: deque[Position] = deque()
        self.head_pos: Position = None

        # head cell
        self.head_color: Color = None
        self.head_cell: Rectangle = None

        # tail end cell
        self.tailend_color: Color = None
        self.tailend_cell: Rectangle = None

        # head cell which leaves the world when wrapping
        self.wrapping_head_color: Color = None
        self.wrapping_head_cell: Rectangle = None

        # tail end cell which leaves the world when wrapping
        self.wrapping_tailend_color: Color = None
        self.wrapping_tailend_cell: Rectangle = None

        # every animation which can possibly occure
        self.anim_move_head: Optional[Animation] = None
        self.anim_move_tailend: Optional[Animation] = None
        self.anim_decay: Optional[Animation] = None

    def _tailend_pos(self) -> Position:
        return self.tail_pos[0] if len(self.tail_pos) > 0 else self.head_pos

    def _square(self, pos: Position) -> Rectangle:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        return Rectangle(pos=(x, y), size=(s, s))

    def _stop_animations(self) -> None:
        if self.anim_move_head is not None:
            self.anim_move_head.stop(self)
        if self.anim_move_tailend is not None:
            self.anim_move_tailend.stop(self)
        if self.anim_decay is not None:
            self.anim_decay.stop(self)

    @dbg.trackmethod()
    def _clear_instruction_groups(self) -> None:
        self.instr_back.clear()
        self.instr_fore.clear()

    @dbg.trackmethod()
    def _init_tail(self) -> None:
        assert len(self.snake) >= 1

        self.tail_cells.clear()
        self.tail_pos.clear()

        cells = self.snake.iter_cells()
        self.head_pos = next(cells)

        self.tail_color = Color(*self.colors.tail)
        self.tail_rgba = self.colors.tail
        self.instr_back.add(self.tail_color)
        for pos in cells:
            sqr = self._square(pos)
            self.tail_cells.appendleft(sqr)
            self.tail_pos.appendleft(pos)
            self.instr_back.add(sqr)

    @dbg.trackmethod()
    def _init_head(self, pos: Position, rgba: ColorValue) -> None:
        self.head_color = Color(*rgba)
        self.head_rgba = rgba
        self.head_cell = self._square(pos)
        self.head_cell_pos = self.head_cell.pos

        self.instr_fore.add(self.head_color)
        self.instr_fore.add(self.head_cell)

    @dbg.trackmethod()
    def _init_tailend(self, pos: Position, rgba: ColorValue) -> None:
        self.tailend_color = Color(*rgba)
        self.tailend_rgba = rgba
        self.tailend_cell = self._square(pos)
        self.tailend_cell_pos = self.tailend_cell.pos

        self.instr_fore.add(self.tailend_color)
        self.instr_fore.add(self.tailend_cell)

    @dbg.trackmethod()
    def _init_wrapping_head(self, pos: Position, rgba: ColorValue) -> None:
        self.wrapping_head_color = Color(*rgba)
        self.wrapping_head_rgba = rgba
        self.wrapping_head_cell = self._square(pos)
        self.wrapping_head_cell_pos = self.wrapping_head_cell.pos

        self.instr_fore.add(self.wrapping_head_color)
        self.instr_fore.add(self.wrapping_head_cell)

    @dbg.trackmethod()
    def _init_wrapping_tailend(self, pos: Position, rgba: ColorValue) -> None:
        self.wrapping_tailend_color = Color(*rgba)
        self.wrapping_tailend_rgba = rgba
        self.wrapping_tailend_cell = self._square(pos)
        self.wrapping_tailend_cell_pos = self.wrapping_tailend_cell.pos

        self.instr_fore.add(self.wrapping_tailend_color)
        self.instr_fore.add(self.wrapping_tailend_cell)

    @dbg.trackmethod()
    def reset(self) -> None:
        self._stop_animations()
        self._clear_instruction_groups()
        if self.alive:
            self._init_tail()
            self._init_head(self.head_pos, self.colors.head)
            self._init_tailend(self._tailend_pos(), self.colors.tail)

    def _update_body(self, new_head_pos: Position, growth: int) -> None:
        # adds a square at the current head position
        self.tail_pos.append(self.head_pos)
        sqr = self._square(self.head_pos)
        self.tail_cells.append(sqr)
        self.instr_back.add(sqr)
        self.head_pos = new_head_pos

        if growth <= 0:
            # removes squares at the end of the tail
            for _ in range(1-growth):
                sqr = self.tail_cells.popleft()
                self.instr_back.remove(sqr)
                self.tail_pos.popleft()

        elif growth >= 2:
            # adds squares at the end of the tail
            for _ in range(growth-1):
                pos = self.tail_pos[0]
                self.tail_pos.appendleft(pos)
                sqr = self._square(pos)
                self.tail_cells.appendleft(sqr)
                self.instr_back.add(sqr)

    def _anim_slide_head(self, time_step: float, dst: Position) -> Animation:
        return Animation(
            head_cell_pos=self.display.pos_to_coord(dst),
            duration=time_step,
            t='linear'
        )

    @dbg.trackmethod()
    def _anim_wrap_head(
        self,
        time_step: float,
        wrap_dir: Direction,
        wrap_in_src: Position,
        wrap_out_dst: Position
    ) -> None:
        wrap_in_dst = (wrap_in_src[0]+wrap_dir[0], wrap_in_src[1]+wrap_dir[1])
        wrap_out_src = (wrap_out_dst[0]-wrap_dir[0], wrap_out_dst[1]-wrap_dir[1])

        self.head_cell_pos = self.display.pos_to_coord(wrap_out_src)
        self._init_wrapping_head(wrap_in_src, self.colors.head)

        anim = (
            self._anim_slide_head(time_step, wrap_out_dst) &
            Animation(
                wrapping_head_cell_pos=self.display.pos_to_coord(wrap_in_dst),
                duration=time_step,
                t='linear'
            )
        )
        anim.bind(on_complete=lambda *_: self.instr_fore.remove(self.wrapping_head_cell))
        return anim

    def _anim_slide_tailend(self, time_step: float, dst: Position) -> Animation:
        x_src, y_src = self.tailend_cell_pos
        x_dst, y_dst = self.display.pos_to_coord(dst)
        dx, dy = x_dst-x_src, y_dst-y_src

        return Animation(
            tailend_cell_pos=(x_src+1.2*dx, y_src+1.2*dy),
            duration=time_step,
            t='linear'
        )

    def _anim_wrap_tailend(
        self,
        time_step: float,
        wrap_dir: Direction,
        wrap_in_src: Position,
        wrap_out_dst: Position
    ) -> None:
        ...
        # TODO: implement a multi-countdown mechanism to schedule tail end wrapping
        # animation immediatly after the head wrapped
        return self._anim_slide_tailend(time_step, wrap_out_dst)

    def _animate_decay(self, time_step: float) -> None:
        d = self.n_decay_steps * time_step
        animation_transition = 'out_circ'
        self.anim_decay = Animation(
            head_rgba=self.colors.head_decay_final, duration=d, t=animation_transition
        ) & Animation(
            tailend_rgba=self.colors.tail_decay_final, duration=d, t=animation_transition
        ) & Animation(
            tail_rgba=self.colors.tail_decay_final, duration=d, t=animation_transition
        )
        self.anim_decay.bind(on_complete=(lambda *_: self._clear_instruction_groups()))

        self.head_rgba = self.colors.head_decay_first
        self.tailend_rgba = self.colors.tail_decay_first
        self.tail_rgba = self.colors.tail_decay_first
        self.anim_decay.start(self)

    def update_draw_snake_move(self, time_step: float, event: SnakeMovement) -> None:
        self._update_body(event.new_head_pos, event.growth)

        self.anim_move_head = self._anim_slide_head(time_step, self.head_pos)
        self.anim_move_tailend = self._anim_slide_tailend(time_step, self._tailend_pos())
        (self.anim_move_head & self.anim_move_tailend).start(self)

    def update_draw_snake_wrap(self, time_step: float, event: SnakeMovement) -> None:
        head_initial_pos = self.head_pos
        tailend_initial_pos = self._tailend_pos()
        self._update_body(event.new_head_pos, event.growth)

        self.anim_move_head = self._anim_wrap_head(time_step, event.new_dir, head_initial_pos, self.head_pos)
        self.anim_move_tailend = self._anim_wrap_tailend(time_step, event.new_dir, tailend_initial_pos, self._tailend_pos())
        (self.anim_move_head & self.anim_move_tailend).start(self)

    def update_draw_snake_teleport(self, time_step: float, event: SnakeMovement) -> None:
        raise NotImplementedError

    @dbg.trackmethod()
    def update_draw_spawn(self, time_step: float) -> None:
        self.alive = True
        self.reset()

    def update_draw_die(self, time_step: float) -> None:
        self.alive = False
        self._animate_decay(time_step)
