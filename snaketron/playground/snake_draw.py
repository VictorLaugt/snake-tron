from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from back.agents.abstract_snake_agent import AbstractSnakeAgent
from back.direction import DOWN, LEFT, RIGHT, UP
from back.events import AgentUpdated, FoodConsumed, FoodCreated

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window, WindowBase
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout

import numpy as np

if TYPE_CHECKING:
    from typing import Optional, Sequence

    from back.agents.player_snake_agent import PlayerSnakeAgent
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

    def build(self) -> MinimalistWorldDisplay:
        Builder.load_string(KV)

        window = MinimalistWorldDisplay()
        window.init_logic(self.event_receiver, self.world, self.player, self.time_step)
        return window


class MinimalistWorldDisplay(FloatLayout):
    square_size = NumericProperty(10.)

    instr_arena: InstructionGroup
    event_receiver: EventReceiver
    world: SnakeWorld
    player: PlayerSnakeAgent
    agents_events: dict[int, AgentUpdated]
    food_drawer: FoodDrawer
    snake_drawer: SnakeDrawer
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
        self.agents_events = {}
        self.player = player
        self.food_drawer = FoodDrawer(self)
        self.snake_drawer = SnakeDrawer(self, self.player, n_decay_steps=4)
        self.time_step = time_step
        self.key_bindings = {
            Keyboard.keycodes['up']: UP,
            Keyboard.keycodes['right']: RIGHT,
            Keyboard.keycodes['down']: DOWN,
            Keyboard.keycodes['left']: LEFT,
        }
        Window.bind(on_key_down=self.on_key_down)

        self.recompute_square_size()
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
        self.redraw()

    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + pos[0] * self.square_size,
            self.y + (self.world.get_height() - 1 - pos[1]) * self.square_size
        )

    def draw_arena(self) -> None:
        self.instr_arena.clear()
        h, w = self.world.get_height(), self.world.get_width()

        self.instr_arena.add(Color(1, 1, 1))
        for u in range(w+1):
            x = self.x + u*self.square_size
            y0 = self.y
            y1 = self.y + h*self.square_size
            self.instr_arena.add(Line(points=(x, y0, x, y1)))
        for v in range(h+1):
            y = self.y + (h-v)*self.square_size
            x0 = self.x
            x1 = self.x + w*self.square_size
            self.instr_arena.add(Line(points=(x0, y, x1, y)))

    def draw_world(self) -> None:
        for event in self.event_receiver.recv_arena_events():
            if isinstance(event, FoodCreated):
                self.food_drawer.draw_food(event.pos)
            elif isinstance(event, FoodConsumed):
                self.food_drawer.remove_food(event.pos)

        for agent_id, event in self.event_receiver.recv_agent_events():
            self.agents_events[agent_id] = event

        for agent in (player,):
            event = self.agents_events.pop(agent.get_id(), None)
            self.snake_drawer.update_draw(event) # should select the correct snake_drawer

        print(f"\nDEBUG:\n{self.world}")

    def redraw(self) -> None:
        self.draw_arena()
        self.food_drawer.reset()
        self.snake_drawer.reset()

    def game_step(self, dt: float) -> None:
        self.world.simulate()
        self.draw_world()


class FoodDrawer:
    food_color = (0., 1., 0.)

    def __init__(self, world_display: MinimalistWorldDisplay) -> None:
        self.display = world_display
        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.foods: dict[Position, Ellipse] = {}

    def reset(self) -> None:
        self.instr.clear()
        for pos in self.foods.keys():
            self.draw_food(pos)

    def draw_food(self, pos: Position) -> None:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        self.instr.add(Color(*self.food_color))
        circle = Ellipse(pos=(x, y), size=(s, s))
        self.instr.add(circle)
        self.foods[pos] = circle

    def remove_food(self, pos: Position) -> None:
        circle = self.foods.pop(pos)
        self.instr.remove(circle)


def color_gradient(
    first_rgb: tuple[int, int, int],
    final_rgb: tuple[int, int, int],
    n_steps: int
) -> list[tuple[int, int, int]]:
    first_r, first_g, first_b = first_rgb
    final_r, final_g, final_b = final_rgb



class SnakeDrawer:
    head_alive_rgb = (1., 1., 1.)
    tail_alive_rgb = (.7, .7, .7)

    head_decay_first_rgb = (.3, .0, .0)
    head_decay_final_rgb = (.1, .0, .0)

    tail_decay_first_rgb = (.7, .0, .0)
    tail_decay_final_rgb = (.1, .0, .0)

    def __init__(
        self,
        world_display: MinimalistWorldDisplay,
        snake: AbstractSnakeAgent,
        n_decay_steps: int
    ) -> None:
        self.display = world_display
        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)

        self.snake = snake
        self.alive = self.snake.is_alive()
        self.head_square: Rectangle = None
        self.head_pos: Position = None
        self.head_color = Color(*self.head_alive_rgb)

        # [bout de queue <----> 1 avant la tête]
        self.tail_squares: deque[Rectangle] = deque()
        self.tail_pos: deque[Position] = deque()
        self.tail_color = Color(*self.tail_alive_rgb)

        self.n_decay_steps = n_decay_steps
        self.decay_step = 0
        self.head_decay_rgb_gradient = np.linspace(self.head_decay_first_rgb, self.head_decay_final_rgb, self.n_decay_steps)
        self.tail_decay_rgb_gradient = np.linspace(self.tail_decay_first_rgb, self.tail_decay_final_rgb, self.n_decay_steps)

    def _square(self, pos: Position) -> Rectangle:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        return Rectangle(pos=(x, y), size=(s, s))

    def reset(self) -> None:
        self.instr.clear()
        self.tail_squares.clear()
        self.tail_pos.clear()

        cells = self.snake.iter_cells()
        self.head_pos = next(cells)
        self.head_square = self._square(self.head_pos)
        self.head_color.rgb = self.head_alive_rgb
        self.instr.add(self.head_color)
        self.instr.add(self.head_square)

        self.tail_color.rgb = self.tail_alive_rgb
        self.instr.add(self.tail_color)
        for pos in cells:
            sqr = self._square(pos)
            self.tail_squares.appendleft(sqr)
            self.tail_pos.appendleft(pos)
            self.instr.add(sqr)

    def _move_snake(self, new_head_pos: Position, growth: int) -> None:
        # creates a tail square at the previous position of the head
        sqr = self._square(self.head_pos)
        self.tail_pos.append(self.head_pos)
        self.tail_squares.append(sqr)
        self.instr.add(self.tail_color)
        self.instr.add(sqr)

        # removes the previous head square
        self.head_pos = new_head_pos
        self.instr.remove(self.head_square)

        # creates the head square at the new position of the head
        self.head_square = self._square(self.head_pos)
        self.instr.add(self.head_color)
        self.instr.add(self.head_square)

        if growth <= 0:
            # removes squares at the end of the tail
            for _ in range(1-growth):
                sqr = self.tail_squares.popleft()
                self.instr.remove(sqr)
                self.tail_pos.popleft()

        elif growth >= 2:
            # adds squares at the end of the tail
            for _ in range(growth-1):
                pos = self.tail_pos[0]
                self.tail_pos.appendleft(pos)
                sqr = self._square(pos)
                self.tail_squares.appendleft(sqr)
                self.instr.add(self.tail_color)
                self.instr.add(sqr)

    def _init_decay(self) -> None:
        self.decay_step = 0
        self.head_color.rgb = self.head_decay_rgb_gradient[self.decay_step]
        self.tail_color.rgb = self.tail_decay_rgb_gradient[self.decay_step]

    def _decay(self) -> None:
        if self.decay_step < self.n_decay_steps:
            self.head_color.rgb = self.head_decay_rgb_gradient[self.decay_step]
            self.tail_color.rgb = self.tail_decay_rgb_gradient[self.decay_step]
            self.decay_step += 1
        else:
            self.instr.clear()

    def update_draw(self, event: Optional[AgentUpdated]=None) -> None:
        if event is None:
            if not self.alive:
                self._decay()
        else:
            if event.death:
                self.alive = False
                self._init_decay()
                self._decay()
            elif not self.alive:
                self.alive = True
                self.reset()
            else:
                self._move_snake(event.new_head_pos, event.growth)


if __name__ == '__main__':
    from back.agents.player_snake_agent import PlayerSnakeAgent
    from back.events import build_event_pipe
    from back.world import SnakeWorld

    sender, receiver = build_event_pipe()

    init_pos = [(2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10)]
    init_dir = (0, -1)

    w = h = 15
    world = SnakeWorld(width=w, height=h, n_food=1, respawn_cooldown=6, event_sender=sender)
    obstacle_pos = []
    for x in range(0, w):
        obstacle_pos.append((x, 0))
        obstacle_pos.append((x, h-1))
    for y in range(1, h-1):
        obstacle_pos.append((0, y))
        obstacle_pos.append((w-1, y))
    world.attach_agent(ObstacleAgent(world, obstacle_pos, True))

    player = PlayerSnakeAgent(world, init_pos, init_dir)
    world.attach_agent(player)

    app = MinimalistSnakeTronApp(receiver, world, player, .5)
    app.run()
