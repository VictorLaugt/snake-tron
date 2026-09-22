from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.graphics import Color, InstructionGroup, Rectangle
from kivy.properties import (ListProperty, NumericProperty,
                             ReferenceListProperty)
from kivy.utils import get_color_from_hex

from events.back2front_protocol import SnakeMovementType

if TYPE_CHECKING:
    from typing import Iterable, Optional

    from kivy.graphics import Canvas, Instruction

    from back.type_hints import Direction, Position
    from events.back2front_protocol import *
    from front.type_hints import ColorValue
    from front.world_display import SnakeColors, WorldDisplay


class SnakeDrawUpdater(EventDispatcher):
    invisible: ColorValue = get_color_from_hex('#00000000')

    tail_rgba = ListProperty([0., 0., 0., 0.])
    tailcut_rgba = ListProperty([0., 0., 0., 0.])

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
    def on_tailcut_rgba(self, _, val): self.tailcut_color.rgba = val

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
        colors: SnakeColors,
        n_decay_steps: int
    ) -> None:
        super().__init__()
        self.display = world_display
        self.layer_back = InstructionGroup()
        self.layer_middle = InstructionGroup()
        self.layer_front = InstructionGroup()
        self.display.canvas.add(self.layer_back)
        self.display.canvas.add(self.layer_middle)
        self.display.canvas.add(self.layer_front)

        # back layer: decaying cut cells
        self.tailcut_color: Color = None

        # middle layer: cells which remains stationary: [tail end <----> 1 cell before head]
        self.tail_color: Color = None
        self.tail_cells: deque[Rectangle] = deque()
        self.tail_pos: deque[Position] = deque()
        self.head_pos: Position = None

        # front layer: head cell
        self.head_color: Color = None
        self.head_cell: Rectangle = None

        # front layer: tail end cell
        self.tailend_color: Color = None
        self.tailend_cell: Rectangle = None
        self.tailend_clock = SnakeTailEndClock()

        # front layer: head cell which leaves the world when wrapping
        self.wrapping_head_color: Color = None
        self.wrapping_head_cell: Rectangle = None

        # front layer: tail end cell which leaves the world when wrapping
        self.wrapping_tailend_color: Color = None
        self.wrapping_tailend_cell: Rectangle = None

        # every animation which can possibly occure
        self.anim_head: Optional[Animation] = None
        self.anim_tail: Optional[Animation] = None
        self.anim_death: Optional[Animation] = None

        # constant parameters
        self.alive = False
        self.colors = colors
        self.n_decay_steps = n_decay_steps

    def get_head_pos(self) -> Position:
        return self.head_pos

    def get_tailend_pos(self) -> Position:
        return self.tail_pos[0] if len(self.tail_pos) > 0 else self.head_pos


    def _square(self, pos: Position) -> Rectangle:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        return Rectangle(pos=(x, y), size=(s, s))


    def _stop_animations(self) -> None:
        if self.anim_head is not None:
            self.anim_head.stop(self)
        if self.anim_tail is not None:
            self.anim_tail.stop(self)
        if self.anim_death is not None:
            self.anim_death.stop(self)

    def _clear_instruction_groups(self) -> None:
        self.layer_middle.clear()
        self.layer_front.clear()
        self.layer_back.clear()

    def _init_tail(self, cell_pos: Optional[Iterable[Position]]) -> None:
        self.tail_color = Color(*self.colors.tail)
        self.tail_rgba = self.colors.tail
        self.layer_middle.add(self.tail_color)

        if cell_pos is not None:
            cell_pos = iter(cell_pos)
            self.head_pos = next(cell_pos)
        else:
            self.tail_pos.reverse()
            cell_pos = list(self.tail_pos)

        self.tail_cells.clear()
        self.tail_pos.clear()

        for pos in cell_pos:
            sqr = self._square(pos)
            self.tail_cells.appendleft(sqr)
            self.tail_pos.appendleft(pos)
            self.layer_middle.add(sqr)

    def _init_head(self, pos: Position, rgba: ColorValue) -> None:
        self.head_color = Color(*rgba)
        self.head_rgba = rgba
        self.head_cell = self._square(pos)
        self.head_cell_pos = self.head_cell.pos

        self.layer_front.add(self.head_color)
        self.layer_front.add(self.head_cell)

    def _init_tailend(self, pos: Position, rgba: ColorValue) -> None:
        self.tailend_color = Color(*rgba)
        self.tailend_rgba = rgba
        self.tailend_cell = self._square(pos)
        self.tailend_cell_pos = self.tailend_cell.pos

        self.layer_front.add(self.tailend_color)
        self.layer_front.add(self.tailend_cell)

    def _init_wrapping_head(self, pos: Position, rgba: ColorValue) -> None:
        self.wrapping_head_color = Color(*rgba)
        self.wrapping_head_rgba = rgba
        self.wrapping_head_cell = self._square(pos)
        self.wrapping_head_cell_pos = self.wrapping_head_cell.pos

        self.layer_front.add(self.wrapping_head_color)
        self.layer_front.add(self.wrapping_head_cell)

    def _init_wrapping_tailend(self, pos: Position, rgba: ColorValue) -> None:
        self.wrapping_tailend_color = Color(*rgba)
        self.wrapping_tailend_rgba = rgba
        self.wrapping_tailend_cell = self._square(pos)
        self.wrapping_tailend_cell_pos = self.wrapping_tailend_cell.pos

        self.layer_front.add(self.wrapping_tailend_color)
        self.layer_front.add(self.wrapping_tailend_cell)


    def reset(self, cell_pos: Optional[Iterable[Position]]=None) -> None:
        self.tailend_clock.reset()
        self._stop_animations()
        self._clear_instruction_groups()
        if self.alive:
            self._init_tail(cell_pos)
            self._init_tailend(self.get_tailend_pos(), self.colors.tail)
            self._init_head(self.head_pos, self.colors.head)


    def _update_body(self, new_head_pos: Position, growth: int) -> Optional[list[Position]]:
        # adds a square at the current head position
        self.tail_pos.append(self.head_pos)
        sqr = self._square(self.head_pos)
        self.tail_cells.append(sqr)
        self.layer_middle.add(sqr)
        self.head_pos = new_head_pos

        if growth <= 0:
            # removes squares at the end of the tail
            tailcut_pos = []
            for _ in range(1-growth):
                sqr = self.tail_cells.popleft()
                self.layer_middle.remove(sqr)
                tailcut_pos.append(self.tail_pos.popleft())
            return tailcut_pos

        elif growth >= 2:
            # adds squares at the end of the tail
            for _ in range(growth-1):
                pos = self.tail_pos[0]
                self.tail_pos.appendleft(pos)
                sqr = self._square(pos)
                self.tail_cells.appendleft(sqr)
                self.layer_middle.add(sqr)


    def _anim_slide_head(self, time_step: float, dst: Position) -> Animation:
        return Animation(
            head_cell_pos=self.display.pos_to_coord(dst),
            duration=time_step,
            t='linear'
        )

    def _anim_wrap_head(
        self,
        time_step: float,
        wrap_dir: Direction,
        wrap_in_src: Position,
        wrap_out_dst: Position
    ) -> Animation:
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
        anim.bind(on_complete=InstructionRemover(self.layer_front, self.wrapping_head_cell))
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
    ) -> Animation:
        wrap_in_dst = (wrap_in_src[0]+wrap_dir[0], wrap_in_src[1]+wrap_dir[1])
        wrap_out_src = (wrap_out_dst[0]-wrap_dir[0], wrap_out_dst[1]-wrap_dir[1])

        self.tailend_cell_pos = self.display.pos_to_coord(wrap_out_src)
        self._init_wrapping_tailend(wrap_in_src, self.colors.tail)

        anim = (
            self._anim_slide_tailend(time_step, wrap_out_dst) &
            Animation(
                wrapping_tailend_cell_pos=self.display.pos_to_coord(wrap_in_dst),
                duration=time_step,
                t='linear'
            )
        )
        anim.bind(on_complete=InstructionRemover(self.layer_front, self.wrapping_tailend_cell))
        return anim

    def _anim_cut_tail(
        self,
        time_step: float,
        tailend_pos: Position,
        tailcut_pos: Iterable[Position]
    ) -> Animation:
        self.tailcut_color = Color(*self.colors.tail_decay_first)
        self.tailcut_rgba = self.colors.tail_decay_first

        if self.anim_tail is not None:
            self.anim_tail.stop(self)
        self.tailend_cell_pos = self.display.pos_to_coord(tailend_pos)

        anim = Animation(
            tailcut_rgba=self.colors.tail_decay_final,
            duration=self.n_decay_steps * time_step,
            t='out_circ'
        )

        self.layer_back.add(self.tailcut_color)
        for pos in tailcut_pos:
            sqr = self._square(pos)
            self.layer_back.add(sqr)
            anim.bind(on_complete=InstructionRemover(self.layer_back, sqr))

        return anim


    def _animate_snake_movement(self, time_step: float, event: SnakeMovement) -> None:
        init_head_pos = self.head_pos
        init_tailend_pos = self.get_tailend_pos()

        # update the stationary cells
        tailcut_pos = self._update_body(event.new_head_pos, event.growth)

        # prepare the animation of the head cell
        if event.movement_type == SnakeMovementType.WRAP:
            self.anim_head = self._anim_wrap_head(time_step, event.new_dir, init_head_pos, self.head_pos)
            self.tailend_clock.new_schedule(len(self.tail_pos)+1, event.new_dir)
        else:
            self.anim_head = self._anim_slide_head(time_step, self.head_pos)

        # prepare the animation of the tail end cell
        self.tailend_clock.update_schedules(event.growth-1)
        if event.growth < 0:
            self.anim_tail = self._anim_cut_tail(time_step, self.get_tailend_pos(), tailcut_pos)
        elif (tailend_wrap_dir := self.tailend_clock.next_step()) is not None:
            self.anim_tail = self._anim_wrap_tailend(time_step, tailend_wrap_dir, init_tailend_pos, self.get_tailend_pos())
        else:
            self.anim_tail = self._anim_slide_tailend(time_step, self.get_tailend_pos())

        # start the animation
        (self.anim_head & self.anim_tail).start(self)

    def _animate_decay(self, time_step: float) -> None:
        # prepare the animation
        d = self.n_decay_steps * time_step
        transition = 'out_circ'
        self.anim_death = Animation(
            head_rgba=self.colors.head_decay_final, duration=d, t=transition
        ) & Animation(
            tail_rgba=self.colors.tail_decay_final, duration=d, t=transition
        )
        self.anim_death.bind(on_complete=(lambda *_: self._clear_instruction_groups()))

        # start the animation
        self.head_rgba = self.colors.head_decay_first
        self.tailend_rgba = self.invisible
        self.tail_rgba = self.colors.tail_decay_first
        self.anim_death.start(self)


    def update_draw_snake_move(self, time_step: float, event: SnakeMovement) -> None:
        self._animate_snake_movement(time_step, event)

    def update_draw_snake_teleport(self, time_step: float, event: SnakeMovement) -> None:
        raise NotImplementedError

    def update_draw_snake_spawn(self, time_step: float, event: SnakeSpawn) -> None:
        self.alive = True
        self.reset(event.pos)

    def update_draw_snake_die(self, time_step: float, event: SnakeDie) -> None:
        self.alive = False
        self._animate_decay(time_step)


class SnakeTailEndClock:
    def __init__(self):
        self.countdowns: deque[int] = deque()
        self.directions: deque[Direction] = deque()

    def reset(self) -> None:
        self.countdowns.clear()
        self.directions.clear()

    def new_schedule(self, snake_length: int, head_direction: Direction) -> None:
        self.countdowns.append(snake_length)
        self.directions.append(head_direction)

    def update_schedules(self, n_steps: int) -> None:
        for _ in range(len(self.countdowns)):
            self.countdowns[0] += n_steps
            self.countdowns.rotate()

    def next_step(self) -> Optional[Direction]:
        if len(self.countdowns) > 0 and self.countdowns[0] <= 0:
            n_remaining_steps = self.countdowns.popleft()
            direction = self.directions.popleft()

            if n_remaining_steps == 0:
                return direction


class InstructionRemover:
    def __init__(self, instr: InstructionGroup|Canvas, obj: Instruction) -> None:
        self.instr = instr
        self.obj = obj

    def __call__(self, *_):
        self.instr.remove(self.obj)
