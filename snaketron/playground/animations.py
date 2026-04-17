from __future__ import annotations

from typing import TYPE_CHECKING
from collections import deque

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window, WindowBase
from kivy.event import EventDispatcher
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.lang import Builder
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty
from kivy.uix.floatlayout import FloatLayout

from back.events import FoodCreated, FoodConsumed
from back.agents import AbstractSnakeAgent, PlayerSnakeAgent
from back.direction import UP, DOWN, LEFT, RIGHT

if TYPE_CHECKING:
    from typing import Optional, Sequence

    from back.agents import AbstractSnakeAgent
    from back.events import EventReceiver, AgentUpdated
    from back.type_hints import Direction, Position
    from back.world import SnakeWorld
    from front.type_hints import Coordinate
    from kivy.uix.widget import Widget


KV = '''
<MinimalistWorldDisplay>:
    orientation: "vertical"
    on_pos: self.recompute_square_size()
    on_size: self.recompute_square_size()
'''


class ObstacleAgent(AbstractSnakeAgent):
    def __init__(self, world: SnakeWorld, pos: Sequence[Position]) -> None:
        super().__init__(world, pos, True)

    def decide_direction(self) -> Direction:
        return UP

    def get_direction(self) -> Direction:
        return UP

    def move(self, d: Direction) -> None:
        pass


class MinimalistSnakeTronApp(App):
    def __init__(
        self,
        event_receiver: EventReceiver,
        world: SnakeWorld,
        player: PlayerSnakeAgent,
        time_step: float,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.event_receiver = event_receiver
        self.world = world
        self.player = player
        self.time_step = time_step
        self.world.reset()
        self.player.reset()

    def build(self) -> MinimalistWorldDisplay:
        Builder.load_string(KV)

        window = MinimalistWorldDisplay()
        window.init_logic(self.event_receiver, self.world, self.player, self.time_step)
        return window


class MinimalistWorldDisplay(FloatLayout):
    square_size = NumericProperty(10.)

    world: SnakeWorld
    player: PlayerSnakeAgent

    arena_drawer: ArenaDrawer
    food_draw_updater: FoodDrawUpdater
    player_draw_updater: SnakeDrawer

    time_step: float
    key_bindings: dict[int, Direction]

    def on_kv_post(self, base_widget: Widget) -> None:
        self.instr_arena = InstructionGroup()
        self.canvas.add(self.instr_arena)

    def init_logic(
        self,
        event_receiver: EventReceiver,
        world: SnakeWorld,
        player: PlayerSnakeAgent,
        time_step: float
    ) -> None:
        self.event_receiver = event_receiver
        self.world = world
        self.player = player
        self.time_step = time_step
        self.key_bindings = {
            Keyboard.keycodes['up']: UP,
            Keyboard.keycodes['right']: RIGHT,
            Keyboard.keycodes['down']: DOWN,
            Keyboard.keycodes['left']: LEFT,
        }
        Window.bind(on_key_down=self.on_key_down)

        self.arena_drawer = ArenaDrawer(self, world)
        self.food_draw_updater = FoodDrawUpdater(self)
        # self.player_draw_updater = DummyPlayerDrawUpdater(self, player)
        self.player_draw_updater = SnakeDrawer(self, player, 6)

        Clock.schedule_interval(self.game_step, self.time_step)

    def on_key_down(
        self,
        window: WindowBase,
        key: int,
        scancode: int,
        codepoint: Optional[str],
        modifiers: Sequence[str]
    ) -> None:
        direction = self.key_bindings.get(key)
        if direction is not None:
            self.player.add_dir_request(direction)

    def recompute_square_size(self) -> None:
        self.square_size = min(
            self.height / self.world.get_height(),
            self.width / self.world.get_width()
        )

    def on_square_size(self, instance: Widget, value: float) -> None:
        self.arena_drawer.erase_and_draw()
        self.food_draw_updater.reset()
        self.player_draw_updater.reset()

    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + pos[0] * self.square_size,
            self.y + (self.world.get_height() - 1 - pos[1]) * self.square_size
        )

    def game_step(self, dt: float) -> None:
        self.world.simulate()

        for event in self.event_receiver.recv_arena_events():
            if isinstance(event, FoodCreated):
                self.food_draw_updater.draw_food(event)
            elif isinstance(event, FoodConsumed):
                self.food_draw_updater.erase_food(event)

        for agent_id, event in self.event_receiver.recv_agent_events():
            if agent_id == self.player.get_id():
                self.player_draw_updater.update_draw(event)

        print(f"\nDEBUG:\n{self.world}")


class ArenaDrawer:
    def __init__(
        self,
        world_display: MinimalistWorldDisplay,
        world: SnakeWorld,
    ) -> None:
        self.display = world_display
        self.world = world

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)

    def erase_and_draw(self) -> None:
        self.instr.clear()
        h, w = self.world.get_height(), self.world.get_width()
        display_x, display_y = self.display.pos
        display_s = self.display.square_size

        # background
        self.instr.add(Color(0, 0, 0))
        self.instr.add(Rectangle(pos=(display_x, display_y), size=(w*display_s, h*display_s)))

        # grid lines
        self.instr.add(Color(.5, .5, .5))
        for u in range(w+1):
            x = display_x + u*display_s
            y0 = display_y
            y1 = display_y + h*display_s
            self.instr.add(Line(points=(x, y0, x, y1)))
        for v in range(h+1):
            y = display_y + (h-v)*display_s
            x0 = display_x
            x1 = display_x + w*display_s
            self.instr.add(Line(points=(x0, y, x1, y)))


class FoodDrawUpdater:
    def __init__(
        self,
        world_display: MinimalistWorldDisplay,
    ) -> None:
        self.display = world_display

        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.food_color = Color(1, 0, 0)

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


class SnakeDrawer(EventDispatcher):
    head_rgb = ListProperty([0., 0., 0.])
    tail_rgb = ListProperty([0., 0., 0.])

    animated_head_x = NumericProperty(0.)
    animated_head_y = NumericProperty(0.)
    animated_head_pos = ReferenceListProperty(animated_head_x, animated_head_y)

    animated_tail_x = NumericProperty(0.)
    animated_tail_y = NumericProperty(0.)
    animated_tail_pos = ReferenceListProperty(animated_tail_x, animated_tail_y)

    def __init__(
        self,
        world_display: MinimalistWorldDisplay,
        snake: AbstractSnakeAgent,
        n_decay_steps: int
    ) -> None:
        super().__init__()
        self.display = world_display
        self.instr_back = InstructionGroup()
        self.instr_fore = InstructionGroup()
        self.display.canvas.add(self.instr_back)
        self.display.canvas.add(self.instr_fore)

        self.head_alive_rgb = (1., 1., 1.)
        self.tail_alive_rgb = (.7, .7, .7)
        self.head_decay_rgb = (.1, .0, .0)
        self.tail_decay_rgb = (.1, .0, .0)

        self.snake = snake
        self.alive = self.snake.is_alive()

        # [bout de queue <----> 1 avant la tête]
        self.tail_squares: deque[Rectangle] = deque()
        self.tail_pos: deque[Position] = deque()
        self.head_pos: Position = None

        # movement animation system
        self.animated_head: Rectangle = None
        self.animated_tail: Rectangle = None
        self.head_animation: Optional[Animation] = None
        self.tail_animation: Optional[Animation] = None

        # color system
        self.head_color = Color(*self.head_alive_rgb)
        self.tail_color = Color(*self.tail_alive_rgb)
        self.n_decay_steps = n_decay_steps
        self.decay_animation: Optional[Animation] = None

    def on_animated_head_pos(self, _, value):
        self.animated_head.pos = value

    def on_animated_tail_pos(self, _, value):
        self.animated_tail.pos = value

    def on_head_rgb(self, _, value):
        self.head_color.rgb = value

    def on_tail_rgb(self, _, value):
        self.tail_color.rgb = value

    def _square(self, pos: Position) -> Rectangle:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        return Rectangle(pos=(x, y), size=(s, s))

    def _clear_all(self) -> None:
        self.instr_back.clear()
        self.instr_fore.clear()
        if self.head_animation is not None:
            self.head_animation.cancel(self)
        if self.tail_animation is not None:
            self.tail_animation.cancel(self)
        if self.decay_animation is not None:
            self.decay_animation.cancel(self)

    def _init_color(self) -> None:
        self.head_rgb = self.head_alive_rgb
        self.tail_rgb = self.tail_alive_rgb

    def _init_body(self) -> None:
        assert len(self.snake) >= 1

        self.tail_squares.clear()
        self.tail_pos.clear()

        cells = self.snake.iter_cells()
        self.head_pos = next(cells)

        self.instr_back.add(self.tail_color)
        for pos in cells:
            sqr = self._square(pos)
            self.tail_squares.appendleft(sqr)
            self.tail_pos.appendleft(pos)
            self.instr_back.add(sqr)

    def _init_animated_head(self) -> None:
        self.animated_head = self._square(self.head_pos)
        self.animated_head_pos = self.animated_head.pos
        self.instr_fore.add(self.head_color)
        self.instr_fore.add(self.animated_head)

    def _init_animated_tail(self) -> None:
        return  # TODO: animate the tail end
        self.animated_tail = ...
        self.animated_tail_pos = self.animated_tail.pos
        self.instr_fore.add(self.tail_color)
        self.instr_fore.add(self.animated_tail)

    def reset(self) -> None:
        self._clear_all()
        self._init_color()
        self._init_body()
        self._init_animated_head()
        self._init_animated_tail()

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

    def _animate_head(self, new_head_pos: Position) -> None:
        # TODO: fix the animation when the head or the tail wraps to the other side of the world

        # slides the animated head square at the new head position
        self.head_animation = Animation(
            animated_head_pos=self.display.pos_to_coord(new_head_pos),
            duration=self.display.time_step,
            t='linear'
        )
        self.head_animation.start(self)

    def _update_snake(self, event: AgentUpdated) -> None:
        self._update_body(event.new_head_pos, event.growth)
        self._animate_head(event.new_head_pos)
        self.head_pos = event.new_head_pos

    def _animate_decay(self) -> None:
        animation_transition = 'out_circ'
        self.decay_animation = Animation(
            head_rgb=self.head_decay_rgb,
            duration=self.n_decay_steps*self.display.time_step,
            t=animation_transition
        ) & Animation(
            tail_rgb=self.tail_decay_rgb,
            duration=self.n_decay_steps*self.display.time_step,
            t=animation_transition
        )
        self.decay_animation.start(self)

    def update_draw(self, event: Optional[AgentUpdated]=None) -> None:
        if event is None:
            return

        # snake dies
        if event.death:
            self.alive = False
            self._animate_decay()

        # snake respawns
        elif not self.alive:
            self.alive = True
            self.reset()

        # snake moves
        else:
            self._update_snake(event)


if __name__ == '__main__':
    from back.world import SnakeWorld
    from back.events import build_event_pipe

    w = h = 15
    sender, receiver = build_event_pipe()
    world = SnakeWorld(width=w, height=h, n_food=2, respawn_cooldown=6, event_sender=sender)

    # init_pos = [(2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10)]
    init_pos = [(2, 5)] * 6
    init_dir = (0, -1)
    player = PlayerSnakeAgent(world, init_pos, init_dir)
    world.attach_agent(player)

    obstacle_pos = [(11, 5), (11, 6), (11, 7), (11, 8)]
    world.attach_agent(ObstacleAgent(world, obstacle_pos))

    time_step = .5

    app = MinimalistSnakeTronApp(receiver, world, player, time_step)
    app.run()
