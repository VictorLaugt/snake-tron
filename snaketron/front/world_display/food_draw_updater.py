from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.graphics import InstructionGroup, Color, Ellipse
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty
from kivy.utils import get_color_from_hex

from back.direction import opposite_dir

if TYPE_CHECKING:
    from typing import Optional

    from front.world_display import WorldDisplay, WorldColors
    from front.type_hints import ColorValue

    from back.agents import AbstractSnakeAgent
    from back.type_hints import Position


class FoodDrawUpdater:
    def __init__(self, world_display: WorldDisplay, colors: WorldColors) -> None:
        self.display = world_display

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.food_color = colors.food

        self.working_drawers: dict[Position, FoodDrawer] = {}
        self.free_drawers: list[FoodDrawer] = []

    def reset(self) -> None:
        for pos, drawer in self.working_drawers.items():
            drawer.despawn_without_anim(pos)
            drawer.spawn_without_anim(pos)
        self.free_drawers.clear()

    def spawn_food(self, pos: Position, time_step: float) -> None:
        if len(self.free_drawers) > 0:
            drawer = self.free_drawers.pop()
        else:
            drawer = FoodDrawer(self)
        self.working_drawers[pos] = drawer
        drawer.spawn(pos, time_step)

    def consume_food(
        self,
        pos: Position,
        eater: Optional[AbstractSnakeAgent],
        time_step: float
    ) -> None:
        drawer = self.working_drawers[pos]
        if eater is not None:
            drawer.eat(pos, eater, time_step)
        else:
            drawer.despawn(pos, time_step)


class FoodDrawer(EventDispatcher):
    invisible: ColorValue = get_color_from_hex('#00000000')

    animated_color = ListProperty(invisible)

    animated_pos_x = NumericProperty(0.)
    animated_pos_y = NumericProperty(0.)
    animated_pos = ReferenceListProperty(animated_pos_x, animated_pos_y)

    animated_size_x = NumericProperty(0.)
    animated_size_y = NumericProperty(0.)
    animated_size = ReferenceListProperty(animated_size_x, animated_size_y)

    def __repr__(self):
        return type(self).__name__

    def __init__(self, pool: FoodDrawUpdater) -> None:
        super().__init__()
        self.pool = pool
        self.color = Color(self.invisible)
        self.circle = Ellipse(pos=(0, 0), size=(0, 0))
        self.pool.instr.add(self.color)
        self.pool.instr.add(self.circle)

    def on_animated_color(self, _, value):
        self.color.rgba = value

    def on_animated_pos(self, _, value):
        self.circle.pos = value

    def on_animated_size(self, _, value):
        self.circle.size = value


    def _allocate(self, pos: Position) -> None:
        self.pool.working_drawers[pos] = self

    def _free(self, pos: Position) -> None:
        self.pool.working_drawers.pop(pos)
        self.pool.free_drawers.append(self)


    def spawn_without_anim(self, pos: Position) -> None:
        # self._allocate(pos)

        x, y = self.pool.display.pos_to_coord(pos)
        s = self.pool.display.square_size
        c = self.pool.food_color
        self.animated_pos = (x, y)
        self.animated_size = (s, s)
        self.animated_color = c

    def spawn(self, pos: Position, duration: float) -> None:
        self._allocate(pos)

        x, y = self.pool.display.pos_to_coord(pos)
        s = self.pool.display.square_size
        c = self.pool.food_color
        # self.animated_size = (0, 0)
        self.animated_size = (s, s)
        self.animated_pos = (x, y)
        self.animated_color = self.invisible
        anim = (
            # Animation(animated_size=(s, s), d=duration, t='linear') &
            Animation(animated_color=c, d=duration, t='linear')
        )
        anim.start(self)

    def despawn_without_anim(self, pos: Position) -> None:
        self.animated_color = self.invisible

    def despawn(self, pos: Position, duration: float) -> None:
        anim = (
            # Animation(animated_size=(0, 0), d=duration, t='linear') &
            Animation(animated_color=self.invisible, d=duration, t='linear')
        )
        anim.bind(on_complete=lambda *_: self._free(pos))
        anim.start(self)

    def eat(self, pos: Position, eater: AbstractSnakeAgent, duration: float) -> None:
        mouth_dir = opposite_dir(eater.get_direction())
        food_dst = eater.get_world().get_neighbor(pos, mouth_dir)
        x, y = self.pool.display.pos_to_coord(food_dst)
        anim = (
            Animation(animated_pos=(x, y), d=duration, t='linear') # &
            # Animation(animated_color=self.invisible, d=duration, t='linear')
        )
        anim.bind(on_complete=lambda *_: self._free(pos))
        anim.start(self)
