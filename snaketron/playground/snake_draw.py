from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from back.direction import DOWN, LEFT, RIGHT, UP
from back.events import AgentUpdated, FoodConsumed, FoodCreated
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window, WindowBase
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout

if TYPE_CHECKING:
    from typing import Iterable, Optional, Sequence

    from back.agent import PlayerSnakeAgent
    from back.events import EventReceiver
    from back.type_hints import Position
    from back.world import SnakeWorld
    from front.type_hints import ColorValue, Coordinate
    from kivy.uix.widget import Widget


KV = '''
<MinimalistWorldDisplay>:
    orientation: "vertical"
    on_pos: self.recompute_square_size()
    on_size: self.recompute_square_size()
'''

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
    world: SnakeWorld
    player: PlayerSnakeAgent

    def on_kv_post(self, base_widget: Widget) -> None:
        self.instr_arena = InstructionGroup()
        self.canvas.add(self.instr_arena)

        self.food_drawer = FoodDrawer(self)
        self.snake_drawer = SnakeDrawer(self)

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

        # self.snake_drawer.reset(self.player.iter_cells())
        for agent_id, event in self.event_receiver.recv_agent_events():
            if agent_id == player.get_id():
                self.snake_drawer.update_draw(event.new_head_pos, event.growth)

    def redraw(self) -> None:
        self.draw_arena()
        self.food_drawer.reset()
        self.snake_drawer.reset(self.player.iter_cells())

    def game_step(self, dt: float) -> None:
        self.world.simulate()
        self.draw_world()


class FoodDrawer:
    food_color = (0., 1., 0.)

    def __init__(self, world_display: MinimalistWorldDisplay) -> None:
        self.display = world_display
        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)
        self.foods: dict[int, Ellipse] = {}

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


class SnakeDrawer:
    head_color = (1., 1., 1.)
    tail_color = (.7, .7, .7)

    def __init__(self, world_display: MinimalistWorldDisplay) -> None:
        self.display = world_display
        self.instr = InstructionGroup()
        self.display.canvas.add(self.instr)

        self.head_square: Rectangle = None
        self.head_pos: Position = None

        # [bout de queue <----> 1 avant la tête]
        self.tail_squares: deque[Rectangle] = deque()
        self.tail_pos: deque[Position] = deque()

    def _square(self, pos: Position) -> Rectangle:
        x, y = self.display.pos_to_coord(pos)
        s = self.display.square_size
        return Rectangle(pos=(x, y), size=(s, s))

    def reset(self, cells: Iterable[Position]) -> None:
        self.instr.clear()
        self.tail_squares.clear()
        self.tail_pos.clear()

        cells = iter(cells)
        self.head_pos = next(cells)
        self.head_square = self._square(self.head_pos)
        self.instr.add(Color(*self.head_color))
        self.instr.add(self.head_square)

        self.instr.add(Color(*self.tail_color))
        for pos in cells:
            sqr = self._square(pos)
            self.tail_squares.appendleft(sqr)
            self.tail_pos.appendleft(pos)
            self.instr.add(sqr)

    def update_draw(self, new_head_pos: Position, growth: int) -> None:
        # creates a tail square at the previous position of the head
        sqr = self._square(self.head_pos)
        self.tail_pos.append(self.head_pos)
        self.tail_squares.append(sqr)
        self.instr.add(Color(*self.tail_color))
        self.instr.add(sqr)

        # removes the previous head square
        self.head_pos = new_head_pos
        self.instr.remove(self.head_square)

        # creates the head square at the new position of the head
        self.head_square = self._square(self.head_pos)
        self.instr.add(Color(*self.head_color))
        self.instr.add(self.head_square)

        if growth <= 0:  # TODO: handle case where growth >= 2 i.e the snake grows of multiple cells at the same time
            # removes squares at the end of the tail
            for _ in range(1-growth):
                sqr = self.tail_squares.popleft()
                self.instr.remove(sqr)
                self.tail_pos.popleft()


if __name__ == '__main__':
    from back.agent import PlayerSnakeAgent
    from back.events import build_event_pipe
    from back.world import SnakeWorld

    sender, receiver = build_event_pipe()

    init_pos = [(2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7)]
    init_dir = (0, -1)

    world = SnakeWorld(width=10, height=10, n_food=1, event_sender=sender)
    player = PlayerSnakeAgent(world, init_pos, init_dir)
    world.attach_agent(player)

    app = MinimalistSnakeTronApp(receiver, world, player, .25)
    app.run()
