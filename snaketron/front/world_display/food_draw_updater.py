from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.graphics import Color, Ellipse, InstructionGroup
from kivy.properties import ListProperty, NumericProperty, ReferenceListProperty
from kivy.utils import get_color_from_hex

if TYPE_CHECKING:
    from typing import Callable, Iterator, Optional, Self

    from back.type_hints import *
    from front.type_hints import *
    from front.world_display import *


__all__ = ['FoodDrawUpdater']


__all__ = ['FoodDrawUpdater']

class FoodDrawUpdater:
    def __init__(self, world_display: WorldDisplay, colors: WorldColors) -> None:
        self.display = world_display

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)

        self.pool: Pool[Position, FoodDrawer] = Pool(lambda pool: FoodDrawer(
            pool, world_display, self.instr, colors
        ))

    def reset(self) -> None:
        for pos, drawer in list(self.pool.iter_workers()):
            if drawer.food_consumed():
                drawer.erase()
            else:
                drawer.redraw(pos)

    def spawn_food(self, pos: Position, time_step: float) -> None:
        drawer = self.pool.allocate_worker(pos)
        drawer.spawn(pos, time_step)

    def eat_food(self, food_pos: Position, eater_pos: Position, time_step: float) -> None:
        drawer = self.pool.get_worker(food_pos)
        assert drawer is not None, f"No food at position {food_pos}"
        drawer.eat(eater_pos, time_step)

    def despawn_food(self, food_pos: Position, time_step: float) -> None:
        drawer = self.pool.get_worker(food_pos)
        assert drawer is not None, f"No food at position {food_pos}"
        drawer.despawn(time_step)


class Pool[K, W]:
    def __init__(self, constructor: Callable[[Self], W]) -> None:
        self.constructor = constructor
        self.working: dict[K, W] = {}
        self.free: list[W] = []

    def allocate_worker(self, key: K) -> W:
        if len(self.free) > 0:
            worker = self.free.pop()
        else:
            worker = self.constructor(self)

        self.working[key] = worker
        return worker

    def free_worker(self, key: K) -> None:
        worker = self.working.pop(key)
        self.free.append(worker)

    def get_worker(self, key: K) -> Optional[W]:
        return self.working.get(key)

    def iter_workers(self) -> Iterator[tuple[K, W]]:
        yield from self.working.items()


class FoodDrawer(EventDispatcher):
    invisible: ColorValue = get_color_from_hex('#00000000')

    animated_color = ListProperty([0., 0., 0., 0.])

    animated_pos_x = NumericProperty(0.)
    animated_pos_y = NumericProperty(0.)
    animated_pos = ReferenceListProperty(animated_pos_x, animated_pos_y)

    animated_size_x = NumericProperty(0.)
    animated_size_y = NumericProperty(0.)
    animated_size = ReferenceListProperty(animated_size_x, animated_size_y)

    def __repr__(self):
        return type(self).__name__

    def __init__(
        self,
        pool: Pool[Position, FoodDrawer],
        display: WorldDisplay,
        instr: InstructionGroup,
        color_values: WorldColors
    ) -> None:
        super().__init__()
        self.pool = pool
        self.display = display
        self.color_values = color_values
        self.food_pos = None
        self.food_is_consumed = False

        self.color = Color(*self.invisible)
        self.circle = Ellipse(pos=(0, 0), size=(0, 0))
        instr.add(self.color)
        instr.add(self.circle)

    def on_animated_color(self, _, value):
        self.color.rgba = value

    def on_animated_pos(self, _, value):
        self.circle.pos = value

    def on_animated_size(self, _, value):
        self.circle.size = value

    def food_consumed(self) -> bool:
        return self.food_is_consumed


    def erase(self) -> None:
        assert self.food_pos is not None
        self.animated_color = self.invisible
        if self.pool.get_worker(self.food_pos) is self:
            self.pool.free_worker(self.food_pos)

    def redraw(self, food_pos: Position) -> None:
        self.food_pos = food_pos

        x, y = self.display.pos_to_coord(food_pos)
        s = self.display.square_size
        c = self.color_values.food

        Animation.cancel_all(self)
        self.animated_pos = (x, y)
        self.animated_size = (s, s)
        self.animated_color = c


    def spawn(self, food_pos: Position, duration: float) -> None:
        self.food_is_consumed = False
        self.food_pos = food_pos

        x, y = self.display.pos_to_coord(food_pos)
        s = self.display.square_size
        c = self.color_values.food

        # self.animated_size = (0, 0)
        self.animated_size = (s, s)
        self.animated_pos = (x, y)
        self.animated_color = self.invisible
        anim = (
            # Animation(animated_size=(s, s), d=duration, t='linear') &
            Animation(animated_color=c, d=duration, t='linear')
        )
        anim.start(self)

    def despawn(self, duration: float) -> None:
        self.food_is_consumed = True
        anim = (
            # Animation(animated_size=(0, 0), d=duration, t='linear') &
            Animation(animated_color=self.invisible, d=duration, t='linear')
        )
        anim.bind(on_complete=lambda *_: self.erase())
        anim.start(self)

    def eat(self, eater_pos: Position, duration: float) -> None:
        self.food_is_consumed = True
        anim = (
            Animation(animated_pos=self.display.pos_to_coord(eater_pos), d=duration, t='linear') # &
            # Animation(animated_color=self.invisible, d=duration, t='linear')
        )
        anim.bind(on_complete=lambda *_: self.erase())
        anim.start(self)
