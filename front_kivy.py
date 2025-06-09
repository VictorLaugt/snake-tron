# from kivy config (do this before importing anything Kivy)
from kivy.config import Config
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '800')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Rectangle, Color, Line, Ellipse, InstructionGroup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ObjectProperty

from direction import UP, DOWN, LEFT, RIGHT, away_from_center

from itertools import chain
from dataclasses import dataclass
from typing import Iterable, Sequence

# Position, SnakeWorld, PlayerSnakeAgent, AbstractAISnakeAgent must be imported from the existing backend

TAG_WORLD = 'game'
TAG_INSPECT = 'inspect'

@dataclass
class SnakeColors:
    head_color: list[float]
    tail_color: list[float]
    dead_color: list[float]
    inspect_color: list[float]


class AbstractGameWidget(RelativeLayout):
    HEAD_COLORS = [(0, 0.4, 0.8), (0.82, 0.58, 0), (0.58, 0, 0.82), (0, 0.5, 0)]
    TAIL_COLORS = [(0, 0.53, 0.93), (0.95, 0.71, 0), (0.93, 0.51, 0.93), (0, 0.39, 0)]
    DEAD_COLOR = (0.55, 0, 0)
    INSPECT_COLOR = (0, 0, 0.38)
    FOOD_COLOR = (1, 0, 0)
    FOOD_OUTLINE = (1, 0.2, 0.2)
    GRID_COLOR = (0, 0, 0.56)
    
    '''
    HEAD_COLORS = [(0, 0, 1), (1, 0.5, 0), (0.6, 0, 1), (0, 1, 0)]
    TAIL_COLORS = [(0.2, 0.6, 1), (1, 0.8, 0.2), (1, 0.4, 1), (0, 0.6, 0.2)]
    DEAD_COLOR = (0.7, 0, 0)
    INSPECT_COLOR = (0, 0, 0.5)
    FOOD_COLOR = (1, 0, 0)
    FOOD_OUTLINE = (1, 0.2, 0.2)
    GRID_COLOR = (0.2, 0.4, 1)
    '''

    def __init__(self, snake_world, player_agents, ai_agents, explain_ai, square_size=20, **kwargs):
        super().__init__(**kwargs)
        self.square_size = square_size
        self.world = snake_world
        self.player_snakes = player_agents
        self.ai_snakes = ai_agents
        self.explain_ai = explain_ai
        self.snake_colors = [None] * (len(player_agents) + len(ai_agents))

        for snake in chain(player_agents, ai_agents):
            idx = min(snake.get_id(), len(self.HEAD_COLORS)-1)
            self.snake_colors[snake.get_id()] = SnakeColors(
                self.HEAD_COLORS[idx],
                self.TAIL_COLORS[idx],
                self.DEAD_COLOR,
                self.INSPECT_COLOR
            )

        self.drawing_instructions = InstructionGroup()
        self.canvas.add(self.drawing_instructions)
        self.bind(pos=self.redraw, size=self.redraw)

    def draw_square(self, x, y, color):
        self.drawing_instructions.add(Color(*color))
        self.drawing_instructions.add(Rectangle(pos=(x, y), size=(self.square_size, self.square_size)))

    def draw_circle(self, x, y, color, outline):
        self.drawing_instructions.add(Color(*outline))
        self.drawing_instructions.add(Ellipse(pos=(x, y), size=(self.square_size, self.square_size)))

    def pos_to_coord(self, pos):
        return self.x + pos[0] * self.square_size, self.y + (self.world.get_height() - 1 - pos[1]) * self.square_size

    def redraw(self, *args):
        self.drawing_instructions.clear()
        self.draw_world([])

    def draw_world(self, dead_snakes: Iterable):
        self.drawing_instructions.clear()

        # Draw background
        self.drawing_instructions.add(Color(0, 0, 0.18))
        self.drawing_instructions.add(Rectangle(pos=self.pos, size=self.size))

        # Draw grid lines every 3 cells
        self.drawing_instructions.add(Color(*self.GRID_COLOR))
        for u in range(3, self.world.get_width(), 3):
            x = self.x + u * self.square_size
            y0 = self.y
            y1 = self.y + self.world.get_height() * self.square_size
            self.drawing_instructions.add(Line(points=[x, y0, x, y1]))
        for v in range(3, self.world.get_height(), 3):
            y = self.y + (self.world.get_height() - v) * self.square_size
            x0 = self.x
            x1 = self.x + self.world.get_width() * self.square_size
            self.drawing_instructions.add(Line(points=[x0, y, x1, y]))

        # AI inspection
        if self.explain_ai:
            for snake in self.ai_snakes:
                color = self.snake_colors[snake.get_id()].inspect_color
                for pos in snake.inspect():
                    x, y = self.pos_to_coord(pos)
                    self.draw_square(x, y, color)

        # Draw snakes
        for snake in self.world.iter_alive_agents():
            colors = self.snake_colors[snake.get_id()]
            cells = list(snake.iter_cells())
            for i, pos in enumerate(cells):
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, colors.head_color if i == 0 else colors.tail_color)

        # Draw food
        for food in self.world.iter_food():
            x, y = self.pos_to_coord(food)
            self.draw_circle(x, y, self.FOOD_COLOR, self.FOOD_OUTLINE)

        # Dead snakes
        for snake in dead_snakes:
            color = self.snake_colors[snake.get_id()].dead_color
            for pos in snake.iter_cells():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, color)


class MobileSnakeGameWindow(BoxLayout):
    def __init__(self, snake_world, player_agents, ai_agents, explain_ai, ui_size_coeff, time_step, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.world = snake_world
        self.players = player_agents
        self.ai = ai_agents
        self.explain_ai = explain_ai
        self.ui_size_coeff = ui_size_coeff
        self.time_step = time_step / 1000.
        self.fullspeed = False
        self.regular_time_step = self.time_step
        self.canvas_widget = AbstractGameWidget(
            self.world, self.players, self.ai, self.explain_ai,
            square_size=int(20 * ui_size_coeff),
            size=Window.size,
        )
        self.add_widget(self.canvas_widget)

        # Scoreboard
        self.score_labels = {}
        scoreboard = BoxLayout(size_hint_y=0.05)
        for snake in chain(self.players, self.ai):
            label = Label(text=f"{snake.get_id()}: 0", color=(1,1,1,1), size_hint_x=None, width=100)
            scoreboard.add_widget(label)
            self.score_labels[snake.get_id()] = label
        self.add_widget(scoreboard)

        # Swipe controls
        self.swipe_controls = [SwipeControlWidget(snake) for snake in self.players]
        swipe_container = BoxLayout(size_hint_y=0.2)
        for swipe in self.swipe_controls:
            swipe_container.add_widget(swipe)
        self.add_widget(swipe_container)

        # Control buttons
        button_bar = BoxLayout(size_hint_y=0.1)
        button_bar.add_widget(Button(text='Pause', on_press=self.toggle_pause))
        button_bar.add_widget(Button(text='AI Explain', on_press=self.toggle_ai))
        button_bar.add_widget(Button(text='Full Speed', on_press=self.toggle_fullspeed))
        self.add_widget(button_bar)

        self.paused = False
        self.event = Clock.schedule_interval(self.step, self.time_step)

    def toggle_pause(self, *args):
        self.paused = not self.paused

    def toggle_ai(self, *args):
        self.explain_ai = not self.explain_ai
        self.canvas_widget.explain_ai = self.explain_ai

    def toggle_fullspeed(self, *args):
        self.fullspeed = not self.fullspeed
        Clock.unschedule(self.event)
        new_step = 0.01 if self.fullspeed else self.regular_time_step
        self.event = Clock.schedule_interval(self.step, new_step)

    def update_scores(self):
        for snake in chain(self.players, self.ai):
            self.score_labels[snake.get_id()].text = f"{snake.get_id()}: {len(snake)}"

    def step(self, dt):
        if not self.paused:
            dead = self.world.simulate()
            self.canvas_widget.draw_world(dead)
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
