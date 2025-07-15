from __future__ import annotations

from kivy.config import Config
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '800')

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button

from kivy.graphics import Rectangle, Color, Line, Ellipse, InstructionGroup
from kivy.utils import get_color_from_hex

from direction import UP, DOWN, LEFT, RIGHT, away_from_center

from itertools import chain
from dataclasses import dataclass

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import TypeAlias, Sequence, Iterable
    from type_hints import Position
    from world import SnakeWorld
    from agent import AbstractSnakeAgent, PlayerSnakeAgent, AbstractAISnakeAgent
    Coordinate: TypeAlias = tuple[float, float]
    ColorValue: TypeAlias = tuple[float, float, float, float]


TAG_WORLD = 'game'
TAG_INSPECT = 'inspect'

@dataclass
class SnakeColors:
    head_color: list[float]
    tail_color: list[float]
    dead_color: list[float]
    inspect_color: list[float]


class WorldDisplay(FloatLayout):
    HEAD_COLORS = [get_color_from_hex(c) for c in ('#0066CC', '#D19300', '#9400D3', '#008000')]
    TAIL_COLORS = [get_color_from_hex(c) for c in ('#0088EE', '#F3B500', '#EE82EE', '#006400')]

    FOOD_OUTLINE_COLOR = get_color_from_hex('#FF6666')
    FOOD_COLOR = get_color_from_hex('#FF0000')
    DEAD_COLOR = get_color_from_hex('#8B0000')
    INSPECT_COLOR = get_color_from_hex('#000060')
    BACKGROUND_COLOR = get_color_from_hex('#000030')
    GRIDLINE_COLOR = get_color_from_hex('#000090')
    GRIDBORDER_COLOR = get_color_from_hex("#005690")

    def __init__(
        self,
        snake_world: SnakeWorld,
        player_agents: Sequence[PlayerSnakeAgent],
        ai_agents: Sequence[AbstractAISnakeAgent],
        explain_ai: bool,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        # interface with the backend
        self.world = snake_world
        self.player_snakes = player_agents
        self.ai_snakes = ai_agents

        # ai inspection
        self.explain_ai = explain_ai

        # snake colors
        self.square_size = self.compute_square_size()
        self.snake_colors: list[SnakeColors] = [None] * (len(player_agents) + len(ai_agents))
        for snake in chain(player_agents, ai_agents):
            color_idx = min(snake.get_id(), len(self.HEAD_COLORS)-1)
            self.snake_colors[snake.get_id()] = SnakeColors(
                self.HEAD_COLORS[color_idx],
                self.TAIL_COLORS[color_idx],
                self.DEAD_COLOR,
                self.INSPECT_COLOR
            )

        self.draw_instr = InstructionGroup()
        self.canvas.add(self.draw_instr)
        self.bind(pos=self.redraw, size=self.redraw)

    def compute_square_size(self) -> float:
        return min(
            self.width / self.world.get_width(),
            self.height / self.world.get_height()
        )

    def toggle_ai_explanation(self) -> None:
        self.explain_ai = not self.explain_ai

    def draw_square(self, x: float, y: float, c: ColorValue) -> None:
        self.draw_instr.add(Color(*c))
        self.draw_instr.add(Rectangle(pos=(x, y), size=(self.square_size, self.square_size)))

    def draw_circle(self, x: float, y: float, c: ColorValue) -> None:
        self.draw_instr.add(Color(*c))
        self.draw_instr.add(Ellipse(pos=(x, y), size=(self.square_size, self.square_size)))

    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + pos[0] * self.square_size,
            self.y + (self.world.get_height() - 1 - pos[1]) * self.square_size
        )

    def redraw(self, *args) -> None:
        self.square_size = self.compute_square_size()
        self.draw_instr.clear()
        self.draw(())

    def draw(self, dead_snakes: Iterable[AbstractSnakeAgent]) -> None:
        self.draw_instr.clear()
        self.draw_world()
        if self.explain_ai:
            self.draw_ai_inspection()
        self.draw_alive_snakes()
        self.draw_food()
        self.draw_killed_snakes(dead_snakes)

    def draw_world(self) -> None:
        h, w = self.world.get_height(), self.world.get_width()

        # background
        self.draw_instr.add(Color(*self.BACKGROUND_COLOR))
        self.draw_instr.add(Rectangle(pos=self.pos, size=(w*self.square_size, h*self.square_size)))

        # grid lines every 3 cells
        self.draw_instr.add(Color(*self.GRIDLINE_COLOR))
        for u in range(3, w, 3):
            x = self.x + u*self.square_size
            y0 = self.y
            y1 = self.y + h*self.square_size
            self.draw_instr.add(Line(points=(x, y0, x, y1)))
        for v in range(3, h, 3):
            y = self.y + (h-v)*self.square_size
            x0 = self.x
            x1 = self.x + w*self.square_size
            self.draw_instr.add(Line(points=(x0, y, x1, y)))

        # grid border
        self.draw_instr.add(Color(*self.GRIDBORDER_COLOR))
        self.draw_instr.add(Line(points=(
            self.x, self.y,
            self.x + w*self.square_size, self.y
        )))
        self.draw_instr.add(Line(points=(
            self.x, self.y + h*self.square_size,
            self.x + w*self.square_size, self.y + h*self.square_size
        )))
        self.draw_instr.add(Line(points=(
            self.x, self.y,
            self.x, self.y + h*self.square_size
        )))
        self.draw_instr.add(Line(points=(
            self.x + w*self.square_size, self.y,
            self.x + w*self.square_size, self.y + h*self.square_size
        )))

    def draw_ai_inspection(self) -> None:
        for snake in self.ai_snakes:
            color = self.snake_colors[snake.get_id()].inspect_color
            for pos in snake.inspect():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, color)

    def draw_alive_snakes(self) -> None:
        for snake in self.world.iter_alive_agents():
            colors = self.snake_colors[snake.get_id()]
            cells = list(snake.iter_cells())
            for i, pos in enumerate(cells):
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, colors.head_color if i == 0 else colors.tail_color)

    def draw_food(self) -> None:
        for food in self.world.iter_food():
            x, y = self.pos_to_coord(food)
            self.draw_circle(x, y, self.FOOD_COLOR)

    def draw_killed_snakes(self, dead_snakes: Iterable[AbstractSnakeAgent]) -> None:
        for snake in dead_snakes:
            color = self.snake_colors[snake.get_id()].dead_color
            for pos in snake.iter_cells():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, color)


class MobileSnakeGameWindow(BoxLayout):
    def __init__(
        self,
        snake_world: SnakeWorld,
        player_agents: Sequence[PlayerSnakeAgent],
        ai_agents: Sequence[AbstractAISnakeAgent],
        explain_ai: bool,
        ui_size_coeff: float,
        time_step_ms: int,
        **kwargs
    ) -> None:
        super().__init__(orientation='vertical', **kwargs)

        # interface with the backend
        self.world = snake_world
        self.player_snakes = list(player_agents)
        self.ai_snakes = list(ai_agents)

        # game speed
        self.time_step = time_step_ms / 1000.
        self.regular_time_step = self.time_step
        self.fullspeed = False
        self.game_paused = False

        # world display
        self.canvas_widget = WorldDisplay(
            self.world,
            self.player_snakes,
            self.ai_snakes,
            explain_ai,
            size=Window.size,
        )
        self.add_widget(self.canvas_widget)

        # scoreboard
        self.score_labels = {}
        scoreboard = BoxLayout(size_hint_y=0.05)
        for snake in chain(self.player_snakes, self.ai_snakes):
            label = Label(text=f"{snake.get_id()}: 0", color=(1,1,1,1), size_hint_x=None, width=100)
            scoreboard.add_widget(label)
            self.score_labels[snake.get_id()] = label
        self.add_widget(scoreboard)

        # snake controls
        self.swipe_controls = [SwipeControlWidget(snake) for snake in self.player_snakes]
        swipe_container = BoxLayout(size_hint_y=0.2)
        for swipe in self.swipe_controls:
            swipe_container.add_widget(swipe)
        self.add_widget(swipe_container)

        # buttons
        button_bar = BoxLayout(size_hint_y=0.1)
        button_bar.add_widget(Button(text='Pause', on_press=self.toggle_pause))
        button_bar.add_widget(Button(text='AI Explain', on_press=self.toggle_ai))
        button_bar.add_widget(Button(text='Full Speed', on_press=self.toggle_fullspeed))
        self.add_widget(button_bar)

        self.event = Clock.schedule_interval(self.step, self.time_step)

    def toggle_pause(self, *args):
        self.game_paused = not self.game_paused

    def toggle_ai(self, *args):
        self.canvas_widget.toggle_ai_explanation()

    def toggle_fullspeed(self, *args):
        self.fullspeed = not self.fullspeed
        Clock.unschedule(self.event)
        new_step = 0.01 if self.fullspeed else self.regular_time_step
        self.event = Clock.schedule_interval(self.step, new_step)

    def update_scores(self):
        for snake in chain(self.player_snakes, self.ai_snakes):
            self.score_labels[snake.get_id()].text = f"{snake.get_id()}: {len(snake)}"

    def step(self, dt):
        if not self.game_paused:
            dead = self.world.simulate()
            self.canvas_widget.draw(dead)
            self.update_scores()


class SwipeControlWidget(Widget):
    def __init__(self, snake, **kwargs):
        super().__init__(**kwargs)
        self.snake = snake
        self.touch_start = None

    def on_touch_down(self, touch):
        self.touch_start = (touch.x, touch.y)
        return True

    def on_touch_up(self, touch):
        if not self.touch_start:
            return True
        dx = touch.x - self.touch_start[0]
        dy = touch.y - self.touch_start[1]
        if abs(dx) > abs(dy):
            direction = RIGHT if dx > 0 else LEFT
        else:
            direction = UP if dy > 0 else DOWN
        self.snake.add_dir_request(direction)
        self.touch_start = None
        return True


class SnakeApp(App):
    def __init__(self, snake_world, player_agents, ai_agents, explain_ai, ui_size_coeff, time_step, **kwargs):
        self.snake_world = snake_world
        self.players = player_agents
        self.ai_agents = ai_agents
        self.explain_ai = explain_ai
        self.ui_size_coeff = ui_size_coeff
        self.time_step = time_step
        super().__init__(**kwargs)

    def build(self):
        self.snake_world.reset()
        return MobileSnakeGameWindow(
            self.snake_world,
            self.players,
            self.ai_agents,
            self.explain_ai,
            self.ui_size_coeff,
            self.time_step
        )

# Exemple d'utilisation:
# SnakeApp(snake_world, players, ai_agents, explain_ai=False, ui_size_coeff=1.0, time_step=0.1).run()
