from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.graphics import Color, InstructionGroup, Rectangle
from kivy.properties import (ListProperty, NumericProperty,
                             ReferenceListProperty)

if TYPE_CHECKING:
    from back.agents import AbstractSnakeAgent
    from back.events import SnakeMovement
    from back.type_hints import Direction, Position
    from front.type_hints import ColorValue, Coordinate
    from front.world_display import SnakeColors, WorldDisplay
    from kivy.uix.widget import Widget


class SnakeDrawUpdater:
    def __init__(
        self,
        world_display: WorldDisplay,
        snake: AbstractSnakeAgent,
        colors: SnakeColors,
        n_decay_steps: int
    ) -> None:
        self.d = world_display
        self.snake = snake
        self.alive = snake.is_alive()
        self.colors = colors

        # deque([end of tail <----> start of tail (1 cell before the head)])
        self.tail_pos: deque[Position] = deque()
        self.head_pos: Position = None
        self.n_decay_steps = n_decay_steps

        self.tail = SnakeCellDeque(world_display)
        self.head = AnimatedSnakeCell(world_display)
        self.tail_end = AnimatedSnakeCell(world_display)
        self.wrapping_head = AnimatedSnakeCell(world_display)
        self.wrapping_tail_end = AnimatedSnakeCell(world_display)

    def _stop_anim(self) -> None:
        self.tail.stop_anim()
        self.head.stop_anim()
        self.wrapping_head.stop_anim()
        self.tail_end.stop_anim()
        self.wrapping_tail_end.stop_anim()

    def _erase(self) -> None:
        self.tail.erase()
        self.head.erase()
        self.wrapping_head.erase()
        self.tail_end.erase()
        self.wrapping_tail_end.erase()

    def _init_pos(self) -> None:  # TODO: transformer l'attribut self.snake en un argument de la méthode
        assert len(self.snake) >= 1
        self.tail_pos.clear()
        cells = self.snake.iter_cells()
        self.head_pos = next(cells)
        for pos in cells:
            self.tail_pos.appendleft(pos)


    def _init_draw(self) -> None:
        # tail
        self.tail.init(self.colors.tail)
        for pos in self.tail_pos:
            self.tail.append(self.d.pos_to_coord(pos), self.d.square_size)

        # head
        head_coord = self.d.pos_to_coord(self.head_pos)
        self.head.init(head_coord, self.d.square_size, self.colors.head)
        self.wrapping_head.init(head_coord, self.d.square_size, (0., 0., 0., 0.))

        # tail end
        tail_end_pos = self.tail_pos[0] if len(self.tail_pos) > 0 else self.head_pos
        tail_end_coord = self.d.pos_to_coord(tail_end_pos)
        self.tail_end.init(tail_end_coord, self.d.square_size, self.colors.tail)
        self.wrapping_tail_end.init(tail_end_coord, self.d.square_size, (0., 0., 0., 0.))

    def reset(self) -> None:
        self._stop_anim()
        self._erase()
        self._init_pos()
        if self.alive:
            self._init_draw()


    def _update_tail(self, new_head_pos: Position, growth: int) -> None:
        # adds a square at the current head position
        self.tail.append(self.d.pos_to_coord(self.head_pos), self.d.square_size)
        self.tail_pos.append(self.head_pos)
        self.head_pos = new_head_pos

        if growth <= 0:
            # removes squares at the end of the tail
            for _ in range(1-growth):
                self.tail.removeleft()
                self.tail_pos.popleft()

        elif growth >= 2:
            # adds squares at the end of the tail
            for _ in range(growth-1):
                pos = self.tail_pos[0]
                self.tail.appendleft(self.d.pos_to_coord(pos), self.d.square_size)
                self.tail_pos.appendleft(pos)

    def _slide_tail_end(self, time_step: float, growth: int) -> None:
        if growth < 0:
            print(
                f"DEBUG: CUT: {growth=}"
                f"{self.tail_end.get_coord()} -> "
                f"{self.d.pos_to_coord(self.tail_pos[0])}"
            )
            Animation.stop_all(self.tail_end)  #BUG: aucune animation n'est censé être planifiée à ce moment
            self.tail_end.set_coord(self.d.pos_to_coord(self.tail_pos[0]))
        elif len(self.tail_pos) > 1:
            x_src, y_src = self.tail_end.get_coord()
            x_dst, y_dst = self.d.pos_to_coord(self.tail_pos[0])
            dx, dy = x_dst-x_src, y_dst-y_src
            self.tail_end.slide_coord((x_src+1.2*dx, y_src+1.2*dy), time_step)
        else:
            self.tail_end.slide_coord(self.d.pos_to_coord(self.head_pos), time_step)

    def update_draw_snake_move(self, time_step: float, event: SnakeMovement) -> None:
        self._update_tail(event.new_head_pos, event.growth)
        self.head.slide_coord(self.d.pos_to_coord(self.head_pos), time_step)
        self._slide_tail_end(time_step, event.growth)

    def update_draw_snake_wrap(self, time_step: float, event: SnakeMovement) -> None:
        wrap_in_start_pos = self.head_pos
        wrap_in_end_pos = (self.head_pos[0]+event.new_dir[0], self.head_pos[1]+event.new_dir[1])
        wrap_out_start_pos = (event.new_head_pos[0]-event.new_dir[0], event.new_head_pos[1]-event.new_dir[1])
        self._update_tail(event.new_head_pos, event.growth)

        self.head.set_coord(self.d.pos_to_coord(wrap_out_start_pos))
        self.head.slide_coord(self.d.pos_to_coord(event.new_head_pos), time_step)

        self.wrapping_head.set_coord(self.d.pos_to_coord(wrap_in_start_pos))
        self.wrapping_head.set_color(self.head.get_color())
        # self.wrapping_head.set_color((0., 1., 0., 1.))
        anim = self.wrapping_head.slide_coord(self.d.pos_to_coord(wrap_in_end_pos), time_step)
        anim.bind(on_complete=lambda *_: self.wrapping_head.set_color((0., 0., 0., 0.)))

        # TODO: implement the wrapping animation of the tail end
        self._slide_tail_end(time_step, event.growth)

    def update_draw_snake_teleport(self, time_step: float, event: SnakeMovement) -> None:
        raise NotImplementedError
        ...

    def update_draw_spawn(self, time_step: float) -> None:
        self.alive = True
        self.reset()

    def update_draw_die(self, time_step: float) -> None:
        self.alive = False

        duration = self.n_decay_steps * time_step
        anim = self.tail.fade_color(self.colors.tail_decay_final, duration)
        self.head.fade_color(self.colors.head_decay_final, duration)
        self.tail_end.fade_color(self.colors.tail_decay_final, duration)
        anim.bind(on_complete=lambda *_: self._erase())

class SnakeCellDeque(EventDispatcher):
    color_rgba = ListProperty([0., 0., 0., 0.])

    def on_color_rgba(self, _, value):
        self.color.rgba = value

    def __init__(self, canvas_owner: Widget) -> None:
        super().__init__()

        # reference to canvas
        self.instr = InstructionGroup()
        canvas_owner.canvas.add(self.instr)

        # instructions
        self.squares: deque[Rectangle] = deque()
        self.color: Color = None

        # animation
        self.color_anim = Animation()


    def init(self, color_rgba: ColorValue) -> None:
        self.color = Color(*color_rgba)
        self.instr.add(self.color)

    def stop_anim(self) -> None:
        self.color_anim.stop(self)

    def erase(self) -> None:
        self.instr.clear()
        self.squares.clear()


    def append(self, coord: Coordinate, square_size: float) -> None:
        sqr = Rectangle(pos=coord, size=(square_size, square_size))
        self.squares.append(sqr)
        self.instr.add(sqr)

    def appendleft(self, coord: Coordinate, square_size: float) -> None:
        sqr = Rectangle(pos=coord, size=(square_size, square_size))
        self.squares.appendleft(sqr)
        self.instr.add(sqr)

    def removeleft(self) -> None:
        sqr = self.squares.popleft()
        self.instr.remove(sqr)

    def set_color(self, color_rgba: ColorValue) -> None:
        self.color_rgba = color_rgba


    def fade_color(self, color_rgba: ColorValue, duration: float) -> Animation:
        self.color_anim = Animation(color_rgba=color_rgba, duration=duration, t='linear')
        self.color_anim.start(self)
        return self.color_anim


class AnimatedSnakeCell(EventDispatcher):
    square_x = NumericProperty(0.)
    square_y = NumericProperty(0.)
    square_pos = ReferenceListProperty(square_x, square_y)
    color_rgba = ListProperty([0., 0., 0., 0.])

    def on_square_pos(self, _, value):
        self.square.pos = value

    def on_color_rgba(self, _, value):
        self.color.rgba = value

    def __init__(self, canvas_owner: Widget) -> None:
        super().__init__()

        # reference to canvas
        self.instr = InstructionGroup()
        canvas_owner.canvas.add(self.instr)

        # instructions
        self.square: Rectangle = None
        self.color: Color = None

        # animations
        self.pos_anim = Animation()
        self.color_anim = Animation()


    def init(self, coord: Coordinate, square_size: float, color_rgba: ColorValue) -> None:
        self.square = Rectangle(pos=coord, size=(square_size, square_size))
        self.square_pos = self.square.pos
        self.color = Color(*color_rgba)
        self.instr.add(self.color)
        self.instr.add(self.square)

    def stop_anim(self) -> None:
        self.pos_anim.stop(self)
        self.color_anim.stop(self)

    def erase(self) -> None:
        self.instr.clear()


    def get_coord(self) -> Coordinate:
        return self.square_pos

    def get_color(self) -> ColorValue:
        return self.color_rgba

    def set_coord(self, coord: Coordinate) -> None:
        self.square_pos = coord

    def set_color(self, color_rgba: ColorValue) -> None:
        self.color_rgba = color_rgba


    def slide_coord(self, coord: Coordinate, duration: float) -> Animation:
        self.pos_anim = Animation(square_pos=coord, duration=duration, t='linear')
        self.pos_anim.start(self)
        return self.pos_anim

    def fade_color(self, color_rgba: ColorValue, duration: float) -> Animation:
        self.color_anim = Animation(color_rgba=color_rgba, duration=duration, t='linear')
        self.color_anim.start(self)
        return self.color_anim
