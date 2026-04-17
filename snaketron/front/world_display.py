from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import itertools
from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty
from kivy.uix.floatlayout import FloatLayout

from back.events import FoodCreated, FoodConsumed, AgentUpdated
from back.events import FoodCreated, FoodConsumed, SnakeSimpleEvent, SnakeMovement, SnakeWrap

if TYPE_CHECKING:
    from typing import Sequence, Optional

    from back.agents import AbstractSnakeAgent, AbstractAISnakeAgent
    from back.events import EventReceiver
    from back.type_hints import Position
    from back.world import SnakeWorld
    from front.type_hints import ColorValue, Coordinate
    from kivy.uix.widget import Widget


@dataclass
class WorldColors:
    food_outline: ColorValue
    food: ColorValue
    background: ColorValue
    gridline: ColorValue
    gridborder: ColorValue


@dataclass
class SnakeColors:
    head: ColorValue
    tail: ColorValue
    head_decay_first: ColorValue
    head_decay_final: ColorValue
    tail_decay_first: ColorValue
    tail_decay_final: ColorValue
    inspect: ColorValue


class WorldDisplay(FloatLayout):
    square_size = NumericProperty(0.)

    event_receiver: EventReceiver
    world: SnakeWorld
    ai_explanations: bool

    arena_drawer: ArenaDrawer
    ai_inspection_drawers: list[AiInspectionDrawer]
    food_draw_updater: FoodDrawUpdater
    snake_draw_updaters: dict[int, SnakeDrawUpdater]

    world_colors: WorldColors
    snake_colors: SnakeColors

    def init_logic(
        self,
        event_receiver: EventReceiver,
        world: SnakeWorld,
        ai_snakes: Sequence[AbstractAISnakeAgent],
        world_colors: WorldColors,
        snake_colors: dict[int, SnakeColors]
    ) -> None:
        self.event_receiver = event_receiver
        self.world = world
        self.ai_explanations = False

        self.arena_drawer = ArenaDrawer(self, world, world_colors)

        self.ai_inspection_drawers = []
        for snake in ai_snakes:
            self.ai_inspection_drawers.append(AiInspectionDrawer(
                self, snake, snake_colors[snake.get_id()]
            ))

        self.food_draw_updater = FoodDrawUpdater(self, world_colors)

        self.snake_draw_updaters = {}
        for snake in itertools.chain(world.iter_alive_agents(), world.iter_dead_agents()):
            snake_id = snake.get_id()
            self.snake_draw_updaters[snake_id] = SnakeDrawUpdater(
                self, snake, snake_colors[snake_id], n_decay_steps=4
            )

        self.world_colors = world_colors
        self.snake_colors = snake_colors
        self.arena_drawer.erase_and_draw()

    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + float(pos[0]) * self.square_size,
            self.y + (self.world.get_height() - 1 - float(pos[1])) * self.square_size
        )

    def recompute_square_size(self) -> None:
        self.square_size = min(
            self.height / self.world.get_height(),
            self.width / self.world.get_width()
        )

    def on_square_size(self, instance: Widget, value: float) -> None:
        self.arena_drawer.erase_and_draw()

        if self.ai_explanations:
            for ai_inspection_drawer in self.ai_inspection_drawers:
                ai_inspection_drawer.erase_and_draw()

        self.food_draw_updater.reset()
        for updater in self.snake_draw_updaters.values():
            updater.reset()

    def toggle_ai_explanations(self) -> None:
        self.ai_explanations = not self.ai_explanations
        if self.ai_explanations:
            for drawer in self.ai_inspection_drawers:
                drawer.erase_and_draw()

        else:
            for drawer in self.ai_inspection_drawers:
                drawer.erase()


    def _draw_arena_events(self) -> None:
        for event in self.event_receiver.recv_arena_events():
            if isinstance(event, FoodCreated):
                self.food_draw_updater.draw_food(event)
            elif isinstance(event, FoodConsumed):
                self.food_draw_updater.erase_food(event)

    def _draw_agent_events(self, time_step: float) -> None:
        for snake_id, event in self.event_receiver.recv_agent_events():
            updater = self.snake_draw_updaters[snake_id]
            if isinstance(event, SnakeMovement):
                updater.update_draw_snake_move(event, time_step)
            elif isinstance(event, SnakeWrap):  # TODO: backend should send SnakeWrap events
                ...
            elif event == SnakeSimpleEvent.SPAWN:
                updater.update_draw_spawn()
            elif event == SnakeSimpleEvent.DIE:
                updater.update_draw_die(time_step)
            elif event == SnakeSimpleEvent.DASH:
                ...


    def update_draw(self, time_step: float) -> None:
        if self.ai_explanations:
            for ai_inspection_drawer in self.ai_inspection_drawers:
                ai_inspection_drawer.erase_and_draw()

        self._draw_arena_events()
        self._draw_agent_events(time_step)


class AiInspectionDrawer:
    def __init__(
        self,
        world_display: WorldDisplay,
        snake: AbstractAISnakeAgent,
        colors: SnakeColors
    ) -> None:
        self.display = world_display
        self.snake = snake

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.color_values = colors

    def erase(self) -> None:
        self.instr.clear()

    def erase_and_draw(self) -> None:
        self.instr.clear()
        self.instr.add(Color(*self.color_values.inspect))
        s = self.display.square_size
        for pos in self.snake.inspect():
            x, y = self.display.pos_to_coord(pos)
            self.instr.add(Rectangle(pos=(x, y), size=(s, s)))


class ArenaDrawer:
    def __init__(
        self,
        world_display: WorldDisplay,
        world: SnakeWorld,
        colors: WorldColors
    ) -> None:
        self.display = world_display
        self.world = world

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.color_values = colors

    def erase_and_draw(self) -> None:
        self.instr.clear()
        h, w = self.world.get_height(), self.world.get_width()
        display_x, display_y = self.display.pos
        display_s = self.display.square_size

        # background
        self.instr.add(Color(*self.color_values.background))
        self.instr.add(Rectangle(pos=(display_x, display_y), size=(w*display_s, h*display_s)))

        # grid lines every 3 cells
        self.instr.add(Color(*self.color_values.gridline))
        for u in range(3, w, 3):
            x = display_x + u*display_s
            y0 = display_y
            y1 = display_y + h*display_s
            self.instr.add(Line(points=(x, y0, x, y1)))
        for v in range(3, h, 3):
            y = display_y + (h-v)*display_s
            x0 = display_x
            x1 = display_x + w*display_s
            self.instr.add(Line(points=(x0, y, x1, y)))

        # grid border
        self.instr.add(Color(*self.color_values.gridborder))
        self.instr.add(Line(points=(
            display_x, display_y,
            display_x + w*display_s, display_y
        )))
        self.instr.add(Line(points=(
            display_x, display_y + h*display_s,
            display_x + w*display_s, display_y + h*display_s
        )))
        self.instr.add(Line(points=(
            display_x, display_y,
            display_x, display_y + h*display_s
        )))
        self.instr.add(Line(points=(
            display_x + w*display_s, display_y,
            display_x + w*display_s, display_y + h*display_s
        )))


class FoodDrawUpdater:
    def __init__(
        self,
        world_display: WorldDisplay,
        colors: WorldColors
    ) -> None:
        self.display = world_display

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.food_color = Color(*colors.food)

        self.foods: dict[Position, Ellipse] = {}


    def _circle(self, pos: Position) -> None:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        return Ellipse(pos=(x, y), size=(s, s))

    def reset(self) -> None:
        self.instr.clear()
        self.instr.add(self.food_color)
        for pos in self.foods.keys():
            circle = self._circle(pos)
            self.instr.add(circle)
            self.foods[pos] = circle

    def draw_food(self, event: FoodCreated) -> None:
        circle = self._circle(event.pos)
        self.instr.add(circle)
        self.foods[event.pos] = circle

    def erase_food(self, event: FoodConsumed) -> None:
        circle = self.foods.pop(event.pos)
        self.instr.remove(circle)


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
        # TODO: fix the animation when the head or the tail wraps to the other side of the world

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
