from __future__ import annotations

from typing import TYPE_CHECKING

from back.direction import DOWN, LEFT, RIGHT, UP
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window, WindowBase
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout

if TYPE_CHECKING:
    from typing import Optional, Sequence

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
        window.init_logic(self.world, self.player, self.time_step)
        return window


class MinimalistWorldDisplay(FloatLayout):
    square_size = NumericProperty(10.)

    instr_arena: InstructionGroup
    instr: InstructionGroup
    world: SnakeWorld
    player: PlayerSnakeAgent

    def on_kv_post(self, base_widget: Widget) -> None:
        self.instr_arena = InstructionGroup()
        self.instr = InstructionGroup()
        self.canvas.add(self.instr_arena)
        self.canvas.add(self.instr)

    def init_logic(
        self,
        world: SnakeWorld,
        player: PlayerSnakeAgent,
        time_step: float
    ) -> None:
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
        self.draw_arena()

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
        self.instr.clear()

        def square(x: float, y: float) -> Rectangle:
            return Rectangle(pos=(x, y), size=(self.square_size, self.square_size))

        def circle(x: float, y: float) -> Ellipse:
            return Ellipse(pos=(x, y), size=(self.square_size, self.square_size))

        for food in self.world.iter_food():
            x, y = self.pos_to_coord(food)
            self.instr.add(Color(0, 1, 0))
            self.instr.add(circle(x, y))

        for snake in self.world.iter_alive_agents():
            self.instr.add(Color(1, 1, 1))
            for cell in snake.iter_cells():
                x, y = self.pos_to_coord(cell)
                self.instr.add(square(x, y))

    def game_step(self, dt: float) -> None:
        self.world.simulate()
        self.draw_world()


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
