from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.app import App
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout

if TYPE_CHECKING:
    from back.agent import PlayerSnakeAgent
    from back.events import EventReceiver
    from back.type_hints import Position
    from back.world import SnakeWorld
    from front.type_hints import Coordinate
    from kivy.uix.widget import Widget


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

    def build(self) -> MinimalistWorldDisplay:
        Builder.load_string('''
        ''')

        window = MinimalistWorldDisplay()
        window.init_logic(...)
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
        player: PlayerSnakeAgent
    ) -> None:
        self.world = world
        self.player = player
        self.draw_arena()

    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + pos[0] * self.square_size,
            self.y + (self.world.get_height() - 1 - pos[1]) * self.square_size
        )

    def draw_arena(self) -> None:
        self.instr_arena.clear()
        h, w = self.world.get_height(), self.world.get_width()

        # grid lines every 3 cells
        self.instr_arena.add(Color(1, 1, 1))
        for u in range(3, w, 3):
            x = self.x + u*self.square_size
            y0 = self.y
            y1 = self.y + h*self.square_size
            self.instr_arena.add(Line(points=(x, y0, x, y1)))
        for v in range(3, h, 3):
            y = self.y + (h-v)*self.square_size
            x0 = self.x
            x1 = self.x + w*self.square_size
            self.instr_arena.add(Line(points=(x0, y, x1, y)))


if __name__ == '__main__':
    from back.agent import PlayerSnakeAgent
    from back.world import SnakeWorld
    from back.events import build_event_pipe

    sender, receiver = build_event_pipe()

    init_pos = [(2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7)]
    init_dir = (0, 1)

    world = SnakeWorld(width=10, height=10, n_food=1, event_sender=sender)
    player = PlayerSnakeAgent(world, init_pos, init_dir)
    world.attach_agent(player)

    app = MinimalistSnakeTronApp(receiver, world, player, 0.25)
    app.run()
